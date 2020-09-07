import sys, json, requests

class Cell:

    def __init__( self, name:str, index:int ):
        self.name = name
        self.inputs = []
        self.value = []
        self.index = 0
        self.order = 0
        self.key = 0

    @property
    def isEmpty( self ):
        return len(self.value) == 0

    @property
    def text( self ):
        return f"// {self.inputs}\nexport const {self.name} = " + "".join(self.value)

class NotebookParser:
    """A crude line-based cell extractor for Observable. This relies on the
    notebook exports to be formatted the same way, so it might need updates
    along the way."""

    NAME   = "      name: "
    INPUTS = "      inputs: "
    VALUE  = "      value: "
    END    = ")})"

    def __init__( self ):
        self.feedLineToCell = False
        self.cells    = []
        self.cell     = None

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
            # We only
            self.feedLineToCell = self.cells and self.cells[-1].isEmpty and True
        elif line.startswith(self.END):
            self.feedLineToCell = False
        elif self.feedLineToCell:
            if not self.cells:
                pass
            else:
                self.cells[-1].value.append(line)

    def post( self ):
        # has_md_only = lambda _:len(_.inputs) == 1 and _.inputs[0] == "md"
        # self.cells = sorted(prioritize([_ for _ in self.cells if not has_md_only(_)]), key=lambda _:_.key)
        return self.cells

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

def download(notebook):
    url = f"https://api.observablehq.com/{notebook}.js"
    r = requests.get(url)
    parser = NotebookParser()
    for line in r.text.split("\n"):
        parser.feed(line + "\n")
    for cell in parser.post():
        print (cell.text)

download(sys.argv[1])
# EOF