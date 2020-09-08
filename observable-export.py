#!/usr/bin/env python3
import json, sys, requests
from typing import Optional, List, Dict

__doc__ = """
Parses ObservableHQ notebook API `https://api.observablehq.com/{notebook}.js`, returning a JavaScript
module that does not require Observable's runtime. This is a bit of hack that makes it possible use
Observable notebooks as literate definitions for JavaScript modules.
"""

# Cells with these symbols will be skipped
NATIVE_SKIPPED_SYMBOLS = [
    "html"
]
DEFINED_SYMBOLS = [
"md", "html", "document", "window", "Node", "NodeList", "StyleSheetList"
]

class Cell:

    def __init__( self, name:str, source:str, index:int ):
        self.name = name
        self.source = source
        self.inputs = []
        self.value = []
        self.index = index
        self.order = 0
        self.key = 0
        self.isResolved = False

    @property
    def isEmpty( self ):
        return len(self.value) == 0

    @property
    def text( self ):
        return f"// @cell('{self.name}', {self.inputs})\nexport const {self.name} = " + "".join(self.value)

    def addLine( self, line:str ):
        self.value.append(line)
        return self

class Notebook:

    def __init__( self ):
        self._cells    = []
        self.areCellsDirty = False

    @property
    def cell( self ) -> Optional[Cell]:
        return self.cells[0] if self.cells else None

    @property
    def cells( self ):
        if self.areCellsDirty:
            self._cells = self.normaliseCells(self._cells)
            self.areCellsDirty = False
        return self._cells

    @property
    def defined( self ) -> List[Cell]:
        return [_ for _ in self.cells if not _.source and _.isResolved and not _.isEmpty]

    @property
    def imported( self ) -> Dict[str,Cell]:
        cells_by_source = {}
        for cell in self.cells:
            if cell.source:
                cells_by_source.setdefault(cell.source, []).append(cell)
        return cells_by_source

    def addCell( self, name, source=None ) -> Cell:
        self._cells.append(Cell(name, source=source, index=len(self.cells)))
        self.areCellsDirty = True
        return self.cell

    def normaliseCells( self, cells ):
        """Brute force prioritization of cells based on dependencies. This would
        fail with a cycle, but we assume that the Observable notebook contains
        none."""
        has_changed = True
        own_cells = [_ for _ in cells if _.isResolved]
        own_cells_map = dict( (_.name,_) for _ in own_cells)
        # All own cells start at order 1
        for cell in own_cells:
            cell.order += 1
        while has_changed:
            has_changed = False
            for cell in own_cells:
                if cell.inputs:
                    o = max(cell.order, max(own_cells_map[_].order + 1 if _ in own_cells_map and _ != cell.name else 0 for _ in cell.inputs) if cell.inputs else cell.order)
                    has_changed = has_changed or o != cell.order
                    if has_changed:
                        cell.order = o
        # We update the key and the isResolved
        cells_map = dict( (_.name,_) for _ in cells)
        is_skipped = lambda _:_ not in cells_map and _ in NATIVE_SKIPPED_SYMBOLS
        for cell in cells:
            cell.key = len(cells) * cell.order + cell.index
            cell.isResolved = len([_ for _ in cell.inputs if not is_skipped(_) and (cells_map.get(_) or _ in DEFINED_SYMBOLS)]) == len(cell.inputs)
        return sorted(cells, key=lambda _:_.key)


class NotebookParser:
    """A crude line-based cell extractor for Observable. This relies on the
    notebook exports to be formatted the same way, so it might need updates
    along the way."""

    NOTEBOOK = '  id: "@'
    NAME   = "      name: "
    INPUTS = "      inputs: "
    VALUE  = "      value: "
    END    = ")})"

    def __init__( self ):
        self.feedLineToCell = False
        self.source   = None
        self.notebook = Notebook()

    def feed( self, line ):
        if not self.feedLineToCell and line.startswith(self.NOTEBOOK):
            self.source = line[len(self.NOTEBOOK)-1:-3]
        elif line.startswith(self.NAME):
            name = json.loads(line[len(self.NAME):-2])
            self.notebook.addCell(name, source=self.source)
        elif line.startswith(self.INPUTS):
            inputs = json.loads(line[len(self.INPUTS):-2])
            cell   = self.notebook.cell
            if cell:
                cell.inputs = inputs
        elif line.startswith(self.VALUE):
            # We only
            self.feedLineToCell = self.notebook.cell and self.notebook.cell.isEmpty and True
        elif line.startswith(self.END):
            self.feedLineToCell = False
        elif self.feedLineToCell:
            cell   = self.notebook.cell
            if cell:
                self.notebook.cell.addLine(line)

def download(notebook):
    url = f"https://api.observablehq.com/{notebook}.js"
    r = requests.get(url)
    parser = NotebookParser()
    for line in r.text.split("\n"):
        parser.feed(line + "\n")
    notebook = parser.notebook
    for source, cells in notebook.imported.items():
        print ("import {" + ", ".join(_.name for _ in cells) + "} from '../" + source + "'")
    for cell in notebook.defined:
      print (cell.text)
    # for cell in notebook.defined:
    #    print (cell.source, cell.name, cell.inputs, cell.isEmpty, cell.isResolved)

download(sys.argv[1])
# EOF