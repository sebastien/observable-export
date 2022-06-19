#!/usr/bin/env python
import re
from typing import Optional, NamedTuple, Union
from graphlib import TopologicalSorter
from dataclasses import dataclass

__doc__ = """
Parses ObservableHQ notebook API `https://api.observablehq.com/{notebook}.js`,
creating an object model of the notebook and its cells, and allowing to convert
it to various formats, including to JavaScript module that does not require
Observable's runtime. This is a bit of hack that makes it possible use
Observable notebooks as literate definitions for JavaScript modules.
"""

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

NOTEBOOK_NAME = r"@?(?P<username>[a-zA-Z0-9_\-]+)/(?P<name>[a-zA-Z0-9_\-]+)"
NOTEBOOK_HASH = f"(?P<id>{'[0-9a-f]' * 16})"
NOTEBOOK_REV = r"(@(?P<rev>\d+))?"
RE_NOTEBOOK_PUBLIC = re.compile(f"^{NOTEBOOK_NAME}{NOTEBOOK_REV}$")
RE_NOTEBOOK_PRIVATE = re.compile(f"^{NOTEBOOK_HASH}{NOTEBOOK_REV}$")
RE_NOTEBOOK = re.compile(
    f"^(?P<notebookname>{NOTEBOOK_HASH}|{NOTEBOOK_NAME}){NOTEBOOK_REV}$"
)


@dataclass
class NotebookRef:
    """An unambiguous reference to a notebook"""

    id: str
    version: int
    username: Optional[str] = None
    name: Optional[str] = None

    @property
    def key(self) -> str:
        return f"{self.id}@{self.version}"


@dataclass
class NotebookHeader:
    """The parse result of a JavaScript header
    for an observable notebook"""

    id: Optional[str]
    version: int
    username: str
    name: Optional[str]


class NotebookName(NamedTuple):
    username: Optional[str] = None
    name: Optional[str] = None
    id: Optional[str] = None
    rev: Optional[int] = None


class Cell:
    """A cell defines an element of a notebook (its source). A cell might have a name,
    a text value (as text lines) and a list of inputs (other cells, referenced by name).
    The index is the original index of the cell, its order is the depth in the dependency
    tree and the key can be used to sort the cells by dependency."""

    RE_PREPROCESSED = re.compile(r"^\w+`")
    RE_ANONYMOUS = re.compile(r"^__CELL_\d+__$")

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
        self.isAnonymous = bool(self.RE_ANONYMOUS.match(name))

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
        """A preprocessed cell has content passed through a
        template string, like `md` or `html`."""
        return bool(
            self.type in ("html", "md")
            or self.value
            and self.RE_PREPROCESSED.match(self.value[0])
        )

    @property
    def isEmpty(self) -> bool:
        """And empty cell has no value"""
        return len(self.value) == 0

    @property
    def text(self) -> str:
        """Returns the cell's text as a single string"""
        if self.type in ("md", "html"):
            return (
                "".join(self.value)
                .rstrip("`\n")
                .lstrip(f"{self.type}`")
                .replace("\\`", "`")
            )
        else:
            return (
                f"// @cell('{self.name}', {self.inputs})\nexport const {self.name} = "
                + "".join(self.value)
            )

    def addLine(self, line: str) -> "Cell":
        self.value.append(line)
        return self

    def __repr__(self):
        return f"(Cell#{id(self)} {self.name}@{self.source}{':' + self.sourceName if self.sourceName else ''} {self.type} {self.inputs})"


class Notebook:
    """A notebook is a collection of cells. Notebooks provide a variety of accessors
    to retrieve the cells."""

    @staticmethod
    def IsPrivate(notebook: Union[NotebookName, "Notebook", str]) -> bool:
        if isinstance(notebook, NotebookName):
            return bool(notebook.id)
        else:
            name = notebook.id or "" if isinstance(notebook, Notebook) else notebook
            return bool(RE_NOTEBOOK_PRIVATE.match(name))

    @staticmethod
    def IsPublic(notebook: Union[NotebookName, "Notebook", str]) -> bool:
        if isinstance(notebook, NotebookName):
            return bool(notebook.name)
        else:
            name = notebook.id or "" if isinstance(notebook, Notebook) else notebook
            return bool(RE_NOTEBOOK_PUBLIC.match(name))

    @staticmethod
    def ParseName(name: str) -> Optional[NotebookName]:
        """Parses the  noteboook nname"""
        matched = RE_NOTEBOOK_PUBLIC.match(name) or RE_NOTEBOOK_PRIVATE.match(name)
        if not matched:
            return None

        def groups(matched, *name):
            for n in name:
                try:
                    yield matched.group(n)
                except IndexError:
                    yield None

        return NotebookName(*groups(matched, "username", "name", "id", "rev"))

    def __init__(self, id: Optional[str] = None, cells: Optional[list[Cell]] = None):
        self.id: Optional[str] = id
        self._cells: list[Cell] = cells or []
        self.areCellsDirty: bool = True

    @property
    def isPrivate(self) -> bool:
        return bool(RE_NOTEBOOK_PRIVATE.match(self.id)) if self.id else False

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
        self._cells = self.normaliseCells(self._cells)
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
        assert self.cell, f"Should not leave with a None cell"
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
            # If the name is not in cells_map, it's part of the Web API
            # or default symbols.
            if name in cells_map:
                cells_map[name].order = order

        # We update the isResolved status
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
        return [cells_map[_] for _ in cells_order if _ in cells_map]


# EOF
