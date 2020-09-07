#urlopen = f"https://api.observablehq.com/${name}
import json

class Cell:

    def __init__( self, name:str, index:int ):
        self.name = name
        self.inputs = []
        self.value = []
        self.index = 0
        self.order = 0
        self.key = 0

    @property
    def text( self ):
        return f"// {self.inputs}\nconst {self.name} = " + "".join(self.value)

class NotebookParser:
    """A crude line-based cell extractor for Observable. This relies on the
    notebook exports to be formatted the same way, so it might need updates
    along the way."""

    NAME   = "      name: "
    INPUTS = "      inputs: "
    VALUE  = "      value: "
    END = ")})"

    def __init__( self ):
        self.hasValue = False
        self.cells    = []
        self.cell = None

    def feed( self, line ):
        if line.startswith(self.NAME):
            name = json.loads(line[len(self.NAME):-2])
            self.cells.append(Cell(name, index=len(self.cells)))
        elif line.startswith(self.INPUTS):
            inputs = json.loads(line[len(self.INPUTS):-2])
            if not self.cells:
                pass
            else:
                self.cells[-1].inputs = inputs
        elif line.startswith(self.VALUE):
            self.hasValue = True
        elif line.startswith(self.END):
            self.hasValue = False
        elif self.hasValue:
            if not self.cells:
                pass
            else:
                self.cells[-1].value.append(line)

def prioritize(cells):
    """Brute force prioritization of cells based on dependencies. This would
    fail with a cycle, but we assume that the Observable notebook contains
    none."""
    has_changed = True
    cells_map = dict( (_.name,_) for _ in cells)
    while has_changed:
        has_changed = False
        for k, cell in cells_map.items():
            if cell.inputs:
                o = max(cell.order, max(cells_map[_].order + 1 if _ in cells_map and _ != cell.name else 0 for _ in cell.inputs) if cell.inputs else cell.order)
                has_changed = has_changed or o != cell.order
                if has_changed:
                    cell.order = o
    for cell in cells:
        cell.key = len(cells) * cell.order + cell.index
    return cells

parser = NotebookParser()
with open("boilerplate.js") as f:
    for line in f.readlines():
        parser.feed(line)
for cell in sorted(prioritize(parser.cells), key=lambda _:_.order * 1000 + _.index):
    print (cell.text)
# EOF
