#!/usr/bin/env python
import json, sys, requests, argparse, re, os
from typing import Optional, Iterator
from fnmatch import fnmatch

__doc__ = """
Parses ObservableHQ notebook API `https://api.observablehq.com/{notebook}.js`, returning a JavaScript
module that does not require Observable's runtime. This is a bit of hack that makes it possible use
Observable notebooks as literate definitions for JavaScript modules.
"""

RE_NOTEBOOK_NAMED = re.compile(
    r"^@?(?P<user>[a-zA-Z0-9_\-]+)/(?P<notebook>[a-zA-Z0-9_\-]+)(@(?P<rev>\d+))?$"
)
RE_NOTEBOOK_PRIVATE = re.compile(r"^(?P<id>[0-9a-f]+)(@(?P<ref>\d+))?$")
RE_PREPROCESSED = re.compile(r"^\w+`")

# Cells with these symbols will be skipped
NATIVE_SKIPPED_SYMBOLS = ["html"]

# The list of symbols already defined in the documment.
DEFINED_SYMBOLS = [
    "md",
    "html",
    "document",
    "window",
    "Node",
    "NodeList",
    "StyleSheetList",
]


class Cell:
    """A cell defines an element of a notebook (its source). A cell might have a name,
    a text value (as text lines) and a list of inputs (other cells, referenced by name).
    The index is the original index of the cell, its order is the depth in the dependency
    tree and the key can be used to sort the cells by dependency."""

    def __init__(self, name: str, source: str, index: int):
        self.name: str = name
        self.source: str = source
        self.inputs: list[str] = []
        self.value: list[str] = []
        self.index: int = index
        self.order: int = 0
        self.key: int = 0
        self.isResolved: bool = False

    @property
    def isPreprocessed(self) -> bool:
        return self.value and RE_PREPROCESSED.match(self.value[0])

    @property
    def isEmpty(self) -> bool:
        return len(self.value) == 0

    @property
    def text(self) -> str:
        return (
            f"// @cell('{self.name}', {self.inputs})\nexport const {self.name} = "
            + "".join(self.value)
        )

    def addLine(self, line: str) -> "Cell":
        self.value.append(line)
        return self


class Notebook:
    """A notebook is a collection of cells. Notebooks provide a variety of accessors
    to retrieve the cells."""

    def __init__(self, cells=None):
        self._cells = cells or []
        self.areCellsDirty = True

    @property
    def cell(self) -> Optional[Cell]:
        return self._cells[-1] if self._cells else None

    @property
    def cells(self):
        if self.areCellsDirty:
            self._cells = self.normaliseCells(self._cells)
            self.areCellsDirty = False
        return self._cells

    @property
    def defined(self) -> list[Cell]:
        return [
            _ for _ in self.cells if not _.source and _.isResolved and not _.isEmpty
        ]

    @property
    def dependencies(self) -> dict[str, Cell]:
        depends = set()
        for cell in self.defined:
            for _ in cell.inputs:
                depends.add(_)
        return dict(
            (k, list(set(_ for _ in v if _.name in depends)))
            for (k, v) in self.imported.items()
        )

    @property
    def imported(self) -> dict[str, Cell]:
        cells_by_source = {}
        for cell in self.cells:
            if cell.source:
                cells = cells_by_source.setdefault(cell.source, [])
                if cell not in cells:
                    cells.append(cell)
        return cells_by_source

    def addCell(self, name, source=None) -> Cell:
        self._cells.append(Cell(name, source=source, index=len(self._cells)))
        self.areCellsDirty = True
        return self.cell

    def normaliseCells(self, cells):
        """Brute force prioritization of cells based on dependencies. This would
        fail with a cycle, but we assume that the Observable notebook contains
        none."""
        has_changed = True
        own_cells = [_ for _ in cells if _.isResolved]
        own_cells_map = dict((_.name, _) for _ in own_cells)
        # All own cells start at order 1
        for cell in own_cells:
            cell.order += 1
        while has_changed:
            has_changed = False
            for cell in own_cells:
                if cell.inputs:
                    o = max(
                        cell.order,
                        max(
                            own_cells_map[_].order + 1
                            if _ in own_cells_map and _ != cell.name
                            else 0
                            for _ in cell.inputs
                        )
                        if cell.inputs
                        else cell.order,
                    )
                    has_changed = has_changed or o != cell.order
                    if has_changed:
                        cell.order = o
        # We update the key and the isResolved
        cells_map = dict((_.name, _) for _ in cells)
        is_skipped = lambda _: _ not in cells_map and _ in NATIVE_SKIPPED_SYMBOLS
        for cell in cells:
            cell.key = len(cells) * cell.order + cell.index
            cell.isResolved = len(
                [
                    _
                    for _ in cell.inputs
                    if not is_skipped(_) and (cells_map.get(_) or _ in DEFINED_SYMBOLS)
                ]
            ) == len(cell.inputs)
        return sorted(cells, key=lambda _: _.key)


class NotebookParser:
    """A crude line-based cell extractor for Observable. This relies on the
    notebook exports to be formatted the same way, so it might need updates
    along the way."""

    NOTEBOOK = '  id: "@'
    NAME = "      name: "
    INPUTS = "      inputs: "
    FROM = "      from: "
    VALUE = "      value: "
    END = ")})"

    def __init__(self):
        self.feedLineToCell = False
        self.source = None
        self.notebook = Notebook()
        self.cell: Optional[Cell] = None
        self.metaFrom = None

    def feed(self, line):
        # print ("PARSED|", repr(line))
        if not self.feedLineToCell and line.startswith(self.NOTEBOOK):
            self.source = line[len(self.NOTEBOOK) - 1 : -3]
        elif line.startswith(self.NAME):
            name = json.loads(line[len(self.NAME) : -2])
            self.cell = self.notebook.addCell(name, source=self.metaFrom or self.source)
        elif line.startswith(self.FROM):
            self.metaFrom = json.loads(line[len(self.FROM) : -2])
        elif line.startswith(self.INPUTS):
            inputs = json.loads(line[len(self.INPUTS) : -2])
            if self.cell:
                assert (
                    not self.cell.inputs
                ), "Possible parsing error, cell inputs already defined"
                self.cell.inputs = inputs
        elif line.startswith(self.VALUE):
            self.feedLineToCell = self.cell and self.cell.isEmpty and True
        elif line.startswith(self.END):
            self.feedLineToCell = False
            self.cell = None
            self.metaFrom = None
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

    nid, rev, user, notebook = groups(name, "id", "rev", "username", "notebook")
    if nid:
        key_var = "OBSERVABLE_API_KEY"
        api_key = key or os.getenv(key_var)
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
        raise RuntimeError(f"Request failed with {r.status_code}: {r.text}")


def convert(notebook: Notebook) -> Iterator[str]:
    imported = []
    debug = False
    if debug:
        for cell in notebook.cells:
            print(cell.source, cell.name, cell.inputs, cell.isEmpty, cell.isResolved)
    else:
        for source, cells in notebook.dependencies.items():
            imports = sorted(list(set(_.name for _ in cells if _.name not in imported)))
            imported += imports
            yield "import {" + ", ".join(imports) + "} from '../" + source + "'\n"
        for cell in notebook.defined:
            if not cell.isPreprocessed:
                yield cell.text


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
    parser.add_argument("-o", "--output", help="Outputs to the given file")
    parser.add_argument("-k", "--api-key", help="Sets the API key to use")
    args = parser.parse_args()
    try:
        notebook = download(args.notebook, key=args.api_key)
    except RuntimeError as e:
        sys.stderr.write("!!! ERR {e}\n")
        sys.stderr.flush()
        return 1

    if args.ignore:
        notebook = Notebook([_ for _ in notebook.cells if matches(_.name, args.ignore)])

    def write(out) -> int:
        for line in convert(notebook):
            out.write(line)
        out.flush()

    if args.output:
        with open(args.output, "w") as f:
            return write(f)
    else:
        return write(sys.stdout)


if __name__ == "__main__":
    sys.exit(run())

# EOF
