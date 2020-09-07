#urlopen = f"https://api.observablehq.com/${name}
import json

class Cell:

    def __init__( self, name:str ):
        self.name = name
        self.inputs = []
        self.value = []

    @property
    def text( self ):
        return f"// {self.inputs}\nconst {self.name} = " + "".join(self.value)

class NotebookParser:

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
            self.cells.append(Cell(name))
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

parser = NotebookParser()
with open("boilerplate.js") as f:
    for line in f.readlines():
        parser.feed(line)
for cell in parser.cells:
    print (cell.text)
# EOF
