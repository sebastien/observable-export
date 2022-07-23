from observableexport.parser2 import parse, process
from pathlib import Path

pnb = parse((Path(__file__).parent / "data-notebook-raw-problematic.js").read_text())
nb = process(pnb)
