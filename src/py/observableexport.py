#!/usr/bin/env python
import json, sys, requests, argparse, re, os
from typing import Optional, Iterator
from fnmatch import fnmatch
from graphlib import TopologicalSorter

__doc__ = """
Parses ObservableHQ notebook API `https://api.observablehq.com/{notebook}.js`,
creating an object model of the notebook and its cells, and allowing to convert
it to various formats, including to JavaScript module that does not require
Observable's runtime. This is a bit of hack that makes it possible use
Observable notebooks as literate definitions for JavaScript modules.
"""

NOTEBOOK_NAME = r"@?(?P<username>[a-zA-Z0-9_\-]+)/(?P<notebook>[a-zA-Z0-9_\-]+)"
NOTEBOOK_HASH = f"(?P<id>{'[0-9a-f]' * 16})"
NOTEBOOK_REV = r"(@(?P<rev>\d+))?"
RE_NOTEBOOK_NAMED = re.compile(f"^{NOTEBOOK_NAME}{NOTEBOOK_REV}$")
RE_NOTEBOOK_PRIVATE = re.compile(f"^{NOTEBOOK_HASH}{NOTEBOOK_REV}$")
RE_NOTEBOOK = re.compile(f"^(?P<name>{NOTEBOOK_HASH}|{NOTEBOOK_NAME}){NOTEBOOK_REV}$")
RE_PREPROCESSED = re.compile(r"^\w+`")

# Cells with these symbols will be skipped
NATIVE_SKIPPED_SYMBOLS = ["html"]

# The list of symbols already defined in the document.
DEFINED_SYMBOLS = [
    "md",
    "html",
    "document",
    "window",
    "Node",
    "NodeList",
    "StyleSheetList",
]

# The preamble can be used to define symbols that may not be already defined.
PREAMBLE = []
for s in DEFINED_SYMBOLS:
    if s[0].lower() != s[0]:
        PREAMBLE.append(f'const {s} = typeof {s} !== "undefined" ? {s} : Object;\n')
    else:
        PREAMBLE.append(f'const {s} = typeof {s} !== "undefined" ? {s} : _ => _;\n')


class Cell:
    """A cell defines an element of a notebook (its source). A cell might have a name,
    a text value (as text lines) and a list of inputs (other cells, referenced by name).
    The index is the original index of the cell, its order is the depth in the dependency
    tree and the key can be used to sort the cells by dependency."""

    def __init__(
        self,
        name: str,
        source: str,
        index: int,
        type: Optional[str] = None,
        sourceName: Optional[str] = None,
    ):
        self.name: str = name
        self.sourceName: Optional[str] = sourceName
        self.type: str = type if type else "js"
        self.source: str = source
        self.inputs: list[str] = []
        self.value: list[str] = []
        self.index: int = index
        self.order: int = 0
        self.key: int = 0
        self.isResolved: bool = False

    def asDict(self, source=True, value=True) -> dict:
        return {
            k: v
            for k, v in dict(
                name=self.name,
                type=self.type,
                source=self.source if source else None,
                sourceName=self.sourceName,
                inputs=self.inputs,
                value=self.value if value else None,
                index=self.index,
                order=self.order,
                key=self.key,
            ).items()
            if v is not None
        }

    @property
    def isPreprocessed(self) -> bool:
        return (
            self.type in ("html", "md")
            or self.value
            and RE_PREPROCESSED.match(self.value[0])
        )

    @property
    def isEmpty(self) -> bool:
        return len(self.value) == 0

    @property
    def text(self) -> str:
        if self.type == "md":
            return "".join(self.value).rstrip("`\n").lstrip("md`").replace("\\`", "`")
        else:
            return (
                f"// @cell('{self.name}', {self.inputs})\nexport const {self.name} = "
                + "".join(self.value)
            )

    def addLine(self, line: str) -> "Cell":
        self.value.append(line)
        return self

    def __repr__(self):
        return f"(Cell {self.name}{':' + self.sourceName if self.sourceName else ''} {self.type} {self.inputs})"


class Notebook:
    """A notebook is a collection of cells. Notebooks provide a variety of accessors
    to retrieve the cells."""

    def __init__(self, id: Optional[str] = None, cells: Optional[list[Cell]] = None):
        self.id: Optional[str] = id
        self._cells: list[Cell] = cells or []
        self.areCellsDirty: bool = True

    @property
    def isPrivate(self) -> bool:
        return self.id and RE_NOTEBOOK_PRIVATE.match(self.id)

    @property
    def cell(self) -> Optional[Cell]:
        """Returns the last cell defined in this notebook"""
        return self._cells[-1] if self._cells else None

    @property
    def cells(self):
        """Returns the cells in this notebook. This takes care of normalising
        the cells when necessary."""
        if self.areCellsDirty:
            self._cells = self.normaliseCells(self._cells)
            self.areCellsDirty = False
        return self._cells

    @property
    def cellsByName(self) -> dict[str, Cell]:
        """Returns the cells by name."""
        return {_.name: _ for _ in self.cells}

    @property
    def defined(self) -> list[Cell]:
        """Returns the list of cells that are *defined* in this notebook."""
        return [
            _
            for _ in self.cells
            if _.source in (None, self.id) and _.isResolved and not _.isEmpty
        ]

    @property
    def dependencies(self) -> dict[str, list[Cell]]:
        """Returns a map of cell names to their list of dependencies."""
        depends = set()
        for cell in self.defined:
            for _ in cell.inputs:
                depends.add(_)
        return {
            k: list(set(_ for _ in v if _.name in depends))
            for (k, v) in self.imported.items()
        }

    @property
    def imported(self) -> dict[str, list[Cell]]:
        """Returns the list of imported cells, grouped by source."""
        cells_by_source: dict[str, list[Cell]] = {}
        for cell in self.cells:
            if cell.source and cell.source != self.id:
                cells = cells_by_source.setdefault(cell.source, [])
                if cell not in cells:
                    cells.append(cell)
        return cells_by_source

    def addCell(
        self,
        name: Optional[str],
        source=None,
        sourceName: Optional[str] = None,
        type: Optional[str] = None,
    ) -> Cell:
        """Adds the cell with the given name and source. This will not check
        if there is already a cell with the given name defined."""
        self._cells.append(
            Cell(
                name if name else f"__CELL_{len(self._cells)}__",
                source=source,
                sourceName=sourceName,
                type=type,
                index=len(self._cells),
            )
        )
        self.areCellsDirty = True
        return self.cell

    def normaliseCells(self, cells: list[Cell]) -> list[Cell]:
        """Brute force prioritization of cells based on dependencies. This would
        fail with a cycle, but we assume that the Observable notebook contains
        none."""
        # We apply the topological sort to get the order of each cell
        cells_map = {_.name: _ for _ in cells}
        cells_graph = {_.name: _.inputs for _ in cells}
        cells_order = [_ for _ in TopologicalSorter(cells_graph).static_order()]
        for order, name in enumerate(cells_order):
            if name in cells_map:
                cells_map[name].order = order

        # We update the isResolved status
        cells_map = dict((_.name, _) for _ in cells)
        is_skipped = lambda _: _ not in cells_map and _ in NATIVE_SKIPPED_SYMBOLS
        for cell in cells:
            # A resolved cells means that all its inputs are in the cells map
            # or are DEFINED_SYMBOLS
            cell.isResolved = len(
                [
                    _
                    for _ in cell.inputs
                    if not is_skipped(_) and (cells_map.get(_) or _ in DEFINED_SYMBOLS)
                ]
            ) == len(cell.inputs)
        return sorted(cells, key=lambda _: _.order)


class NotebookParser:
    """A crude line-based cell extractor for Observable. This relies on the
    notebook exports to be formatted the same way, so it might need updates
    along the way."""

    # SEE: https://api.observablehq.com/@sebastien/boilerplate.js
    # NOTE: We use hardcoded spaces so that we don't match the body by accident.
    NOTEBOOK = re.compile(r'  id: "(?P<id>[^"]+)",')
    NAME = "      name: "
    INPUTS = "      inputs: "
    FROM = "      from: "
    REMOTE = re.compile('^      remote: "(?P<name>[^"]+)"')
    VALUE = "      value: "
    # This is the end of aregular
    END_FUNCTION = ")})"
    # This is the end of special cells (mutable view, etc)
    END_VALUE = "    },"
    RE_INPUT_FUNCTION = re.compile(r"\(function\([^\)]*\)\{return\(")

    def __init__(self, id: Optional[str] = None):
        self.feedLineToCell = False
        self.source: Optional[str] = None
        self.notebook = Notebook(id=id)
        self.cell: Optional[Cell] = None
        # Used to keep track of the from (source) of a cell
        self.metaFrom: Optional[str] = None
        # Used to keep track of the original (source) name of an imported cell
        self.metaRemote: Optional[str] = None
        # Tells if the cell is defined as a function
        self.isCellFunction = False

    def feed(self, line):
        # DEBUG: Leaving this here as it's useful when we get parsing errors
        # print(f"PARSED| {repr(line)}")
        if not self.feedLineToCell and (match := self.NOTEBOOK.match(line)):
            # We have a new notebook, this sets the source of the cell
            # It can be :
            # - @username/notebook
            # - @username/notebook@version
            # - XXXXXXXXXXXXXXX
            # - XXXXXXXXXXXXXXX@version
            self.source = match.group("id") or match.group()
            if not self.notebook.id:
                self.notebook.id = self.source
        elif line.startswith(self.NAME):
            # We have the name of the cell, which is going to be a string after the `name:`
            # Note that Observable has "initial XXX" or "viewof XXX" as names
            # of special cells (views, and mutable cells). We normalise the names
            # by replacing spaces with underscore, which may triger some name
            # clashes.
            name = json.loads(line[len(self.NAME) : -2]).replace(" ", "_")
            self.cell = self.notebook.addCell(
                name, source=self.metaFrom or self.source, sourceName=self.metaRemote
            )
        elif line.startswith(self.FROM):
            # If we have a from, then it means the cell is imported from
            # another notebook.
            self.metaFrom = json.loads(line[len(self.FROM) : -2])
        elif match := self.REMOTE.match(line):
            # Symbols imported like "import {X as Y}" will have a
            # `remote:` attribute.
            self.metaRemote = remote = match.group("name")
            # This may not work in all cases, if "remote:" comes
            # before the name, this will break.
            if self.cell and self.cell.name and self.cell.name != remote:
                self.cell.sourceName = self.metaRemote
        elif line.startswith(self.INPUTS):
            # We capture the inputs of the cell
            inputs = [
                _.replace(" ", "_") for _ in json.loads(line[len(self.INPUTS) : -2])
            ]
            if not self.cell:
                if inputs == ["md"]:
                    self.cell = self.notebook.addCell(
                        None,
                        source=self.metaFrom or self.source,
                        sourceName=self.metaRemote,
                        type="md",
                    )
                elif inputs == ["html"]:
                    self.cell = self.notebook.addCell(
                        None,
                        source=self.metaFrom or self.source,
                        sourceName=self.metaRemote,
                        type="html",
                    )
                else:
                    pass
            elif self.cell:
                # If we already have inputs, this means that we have a new cell,
                # which is likely going to be anonymous
                if self.cell.inputs:
                    self.cell = self.notebook.addCell(
                        None,
                        source=self.metaFrom or self.source,
                        sourceName=self.metaRemote,
                        type="html",
                    )
                self.cell.inputs = inputs
        elif line.startswith(self.VALUE):
            self.feedLineToCell = self.cell and self.cell.isEmpty and True
            rest = line[len(self.VALUE) :]
            # Observable function declarations will start with
            # that prefix. This is a bit awkward, but besically we use
            # the `isCellFunction` flag to disambiguate between a cell
            # that is a function from a cell that is just a value.
            if self.RE_INPUT_FUNCTION.match(rest):
                self.isCellFunction = True
            elif self.cell:
                self.cell.addLine(rest)
                self.isCellFunction = False
        elif (self.isCellFunction and line.startswith(self.END_FUNCTION)) or (
            (not self.isCellFunction) and line.startswith(self.END_VALUE)
        ):
            # We've reached the end of a cell declaration, so we reset
            # our state.
            # TODO: I suspect we need to rewrite the VALUE/END to work in all cases
            self.feedLineToCell = False
            self.cell = None
            self.metaFrom = None
            self.metaRemote = None
            self.isCellFunction = False
        elif self.feedLineToCell:
            if self.cell:
                self.cell.addLine(line)


def download(notebook: str, key: Optional[str] = None):
    """Downloads the given notebook, optionally using the given API key"""
    name = RE_NOTEBOOK_NAMED.match(notebook) or RE_NOTEBOOK_PRIVATE.match(notebook)
    if not name:
        raise ValueError(
            f"Could not parse 'notebook', should be like '@user/notebook' or 'hexhash', got: {notebook}"
        )
    api_key: Optional[str] = None

    def groups(match, *name):
        for n in name:
            try:
                yield match.group(n)
            except IndexError:
                yield None

    nid, rev, username, notebook = groups(name, "id", "rev", "username", "notebook")
    if nid:
        key_var = "OBSERVABLE_API_KEY"
        api_key = (key or os.getenv(key_var) or "").strip("\n").strip()
        if not api_key:
            raise RuntimeError(
                f"Missing Observable API key variable {key_var}, visit https://observablehq.com/settings/api-keys to create one"
            )
        # https://api.observablehq.com/d/[NOTEBOOK_ID][@VERSION].[FORMAT]?v=3&api_key=xxxx
        url = f"https://api.observablehq.com/d/{nid}{'@'+rev if rev else ''}.js"
        headers = {"Authorization": f"ApiKey {api_key}"}
    else:
        url = f"https://api.observablehq.com/@{username}/{notebook}{'@'+rev if rev else ''}.js?"
        headers = {}
    r = requests.get(url, headers=headers)
    if r.status_code >= 200 and r.status_code < 300:
        parser = NotebookParser()
        for line in r.text.split("\n"):
            parser.feed(line + "\n")
        return parser.notebook
    else:
        raise RuntimeError(f"Request to {url} failed with {r.status_code}: {r.text}")


def asJSON(notebook: Notebook) -> str:
    return json.dumps(
        {_.name: _.asDict() for _ in notebook.cells},
    )


def asMarkdown(notebook: Notebook) -> Iterator[str]:
    """Converts the Observable notebook as a Markdown document."""
    for cell in notebook.cells:
        if cell.type == "md":
            yield cell.text
            yield "\n\n"
        else:
            yield f"```{cell.type}\n"
            if cell.name:
                yield f"const {cell.name} = "
            for line in cell.value:
                yield line
            yield "```\n\n"


def asModule(notebook: Notebook, transitiveExports=False) -> Iterator[str]:
    """Converts the Observable notebook as a JavaScript module."""

    # --
    # We start with the imported cells, which are found in the
    # notebook dependencies.
    imported_cells: dict[str, Cell] = {}
    cells_defined: dict[str, Cell] = {_.name: _ for _ in notebook.defined}
    # The dependencies are a list of cells grouped by source (notebook)
    # name.
    for source, cells in notebook.dependencies.items():
        # NOTE: We will skip any cell that is imported but then
        # shadowed by a defined cell.
        import_cells: dict[str, Cell] = {
            _.name: _
            for _ in cells
            if (_.name not in imported_cells) and (_.name not in cells_defined)
        }

        if import_cells:
            imported_cells.update(import_cells)
            prefix = "./" if notebook.isPrivate else "../"
            matched = RE_NOTEBOOK.match(source)
            assert matched, f"Could not parse source as a notebook: {source}"
            # NOTE: We renamed the cells with `__` as a prefix so that they
            # don't clash when we export them.
            import_names = (
                f"{cell.sourceName or cell.name} as __{name}"
                if transitiveExports
                else (f"{cell.sourceName} as {name}" if cell.sourceName else name)
                for name, cell in import_cells.items()
            )
            yield "import {" + ", ".join(import_names) + "} from '" + prefix + (
                matched.group("name")
            ) + ".js'\n"

    if transitiveExports:
        # --
        # We transitively export the imported cells, which is what is
        # expected in Observable.
        for name in imported_cells:
            yield f"export const {name} = __{name};\n"

    # --
    # We output the defined notebook cells, skipping the views and the
    # mutable ones.
    for cell in notebook.defined:
        # We filter out ObservableHQ specific viewof and initial (mutable)
        # variables. We should probably tag the cells.
        if cell.name.startswith("viewof_"):
            continue
        elif cell.name.startswith("initial_"):
            continue
        elif cell.name.startswith("mutable_"):
            continue
        elif not cell.isPreprocessed:
            yield cell.text

    yield "// EOF"


def matches(name: str, excludes: list[str]) -> bool:
    """Returns `False` if the `name` matches any of the `excludes` glob pattern"""
    for f in excludes:
        if f == name or fnmatch(name, f):
            return False
    return True


def run(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Extracts JavaScript modules from ObservableHQ notebooks."
    )
    parser.add_argument(
        "notebook",
        help="The name or ID of the notebook, for instance @sebastien/boilerplate or ",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        action="append",
        help="Excludes the given cell names",
    )
    parser.add_argument("-o", "--output", help="Outputs to the given file", default="")
    parser.add_argument(
        "-a",
        "--append",
        action="store_true",
        help="Appends to the output file",
        default=False,
    )
    parser.add_argument("-k", "--api-key", help="Sets the API key to use")
    parser.add_argument(
        "-m", "--manifest", action="store_true", help="Adds a manifest at the end"
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Supports the output type: 'js' or 'json'",
    )
    parser.add_argument(
        "--transitive-exports",
        action="store_true",
        help="Notebooks re-export their imported symbols (js only)",
        default=False,
    )

    args = parser.parse_args()

    # We get the format type from the args or the output format
    output_ext = args.output.rsplit(".")[-1].lower() if "." in args.output else None
    output_format = args.type or output_ext or "js"

    try:
        notebook = download(args.notebook, key=args.api_key)
    except RuntimeError as e:
        sys.stderr.write(f"!!! ERR {e}\n")
        sys.stderr.flush()
        return 1

    if args.ignore:
        notebook = Notebook(
            id=notebook.id,
            cells=[_ for _ in notebook.cells if matches(_.name, args.ignore)],
        )

    def write(out) -> int:
        if output_format == "json":
            json.dump(
                {_.name: _.asDict() for _ in notebook.cells},
                out,
            )
        elif output_format == "md":
            for line in asMarkdown(notebook):
                out.write(line)
            out.flush()
        elif output_format == "js":
            for line in asModule(notebook, transitiveExports=args.transitive_exports):
                out.write(line)
            if args.manifest:
                manifest = (
                    {
                        _.name: _.asDict(source=False, value=False)
                        for _ in notebook.cells
                    },
                )
                out.write(f"export const __manifest__ = (")
                json.dump(manifest, out)
                out.write(");\n")
        else:
            raise ValueError(
                "Supported types are json, js or md, got: {output_format} "
            )
        out.flush()
        return 0

    if args.output:
        with open(args.output, "a" if args.append else "w") as f:
            return write(f)
    else:
        return write(sys.stdout)


if __name__ == "__main__":
    sys.exit(run())

# EOF
