from .model import Notebook, Cell
import re
import json
from typing import Optional

# --
# Notes
# - JavaScript-exported notebooks contain the imported notebooks, which
#   sometimes contain cells with the same names. These should not shadow
#   the current notebook's cells.


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

    def __init__(self):
        self.feedLineToCell = False
        self.source: Optional[str] = None
        self.notebooks: dict[str, Notebook] = {}
        self.notebook: Optional[Notebook] = None
        self.cell: Optional[Cell] = None
        # Used to keep track of the from (source) of a cell
        self.metaFrom: Optional[str] = None
        # Used to keep track of the original (source) name of an imported cell
        self.metaRemote: Optional[str] = None
        # Tells if the cell is defined as a function
        self.isCellFunction = False

    # FIXME: This should really be an event-driven parser `onXXX`. This is
    # super brittle.
    def feed(self, line: str):
        # DEBUG: Leaving this here as it's useful when we get parsing errors
        # print(f"PARSED| {repr(line)}")
        if not self.feedLineToCell and (match := self.NOTEBOOK.match(line)):
            # We have a new notebook, this sets the source of the cell
            # It can be :
            # - @username/notebook
            # - @username/notebook@version
            # - NNNNNNNNNNNNNNN
            # - NNNNNNNNNNNNNNN@version
            self.source = match.group("id") or match.group()
            self.feedLineToCell = False
            self.cell = None
            self.metaFrom = None
            self.metaRemote = None
            self.isCellFunction = False
            # NOTE: The very last notebook of the page will be the aggregation
            # of all the others:
            #
            # ```
            # const notebook = {
            #   id: "9177eee981fcbaee@2256",
            #   modules: [m0,m1,m2,m3]
            # }
            # ```
            self.notebook = self.notebooks.setdefault(
                self.source, Notebook(self.source)
            )
        elif line.startswith(self.NAME):
            # We have the name of the cell, which is going to be a string after the `name:`
            # Note that Observable has "initial NNN" or "viewof NNN" as names
            # of special cells (views, and mutable cells). We normalise the names
            # by replacing spaces with underscore, which may triger some name
            # clashes.
            name = json.loads(line[len(self.NAME) : -2]).replace(" ", "_")
            assert self.notebook, f"Notebook not defined before cell definition: {line}"
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
            assert self.notebook, f"Notebook not defined before cell definition: {line}"
            # FIXME: This is a messy, reptititive section that that
            # should be reworked.
            if not self.cell:
                if inputs == ["md"]:
                    self.cell = self.notebook.addCell(
                        None,
                        source=self.metaFrom or self.source,
                        sourceName=self.metaRemote,
                        type="md",
                    )
                    self.cell.inputs = [_ for _ in inputs if _ != "md"]
                elif inputs == ["html"]:
                    self.cell = self.notebook.addCell(
                        None,
                        source=self.metaFrom or self.source,
                        sourceName=self.metaRemote,
                        type="html",
                    )
                    self.cell.inputs = [_ for _ in inputs if _ != "html"]
                else:
                    self.cell = self.notebook.addCell(
                        None,
                        source=self.metaFrom or self.source,
                        sourceName=self.metaRemote,
                        type=None,
                    )
                    self.cell.inputs = inputs
            elif self.cell:
                # If we already have inputs, this means that we have a new cell,
                # which is likely going to be anonymous
                if self.cell.inputs:
                    self.cell = self.notebook.addCell(
                        None,
                        source=self.metaFrom or self.source,
                        sourceName=self.metaRemote,
                        # FIXME: Why is this HTML?
                        type="html",
                    )
                self.cell.inputs = inputs
        elif line.startswith(self.VALUE):
            rest = line[len(self.VALUE) :]
            # Observable function declarations will start with
            # that prefix. This is a bit awkward, but besically we use
            # the `isCellFunction` flag to disambiguate between a cell
            # that is a function from a cell that is just a value.
            if self.RE_INPUT_FUNCTION.match(rest):
                self.isCellFunction = True
                # If there's no cell defined, it means it's an anonymous cell
                if not self.cell:
                    assert self.notebook
                    self.cell = self.notebook.addCell(
                        None,
                        source=self.metaFrom or self.source,
                        sourceName=self.metaRemote,
                    )

            elif self.cell:
                self.cell.addLine(rest)
                self.isCellFunction = False
            # NOTE: It's important to leave that at the end of the branch,
            # as we may be creating cells.
            self.feedLineToCell = self.cell and self.cell.isEmpty and True
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
        else:
            # print("DEBUG")
            pass


def parse(text: str) -> tuple[Optional[Notebook], dict[str, Notebook]]:
    parser = NotebookParser()
    for line in text.split("\n"):
        parser.feed(line + "\n")
    return parser.notebook, parser.notebooks


# EOF
