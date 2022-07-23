from observableexport.parser2 import parse
from pathlib import Path

nb, deps = parse(
    (Path(__file__).parent / "data-notebook-raw-problematic.js").read_text()
)
print(nb)
