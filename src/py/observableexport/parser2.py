from .model import Notebook, Cell
from typing import Optional
import re
import json
from dataclasses import dataclass, field


# --
# These classes define the exact same model as in the Observable
# notebook JS. This data model is then remapped to our internal
# Notebook and Cell model.


@dataclass
class ParsedCell:
    name: Optional[str] = None
    inputs: Optional[list[str]] = None
    remote: Optional[str] = None
    remoteFrom: Optional[str] = None
    value: list[str] = field(default_factory=list)


@dataclass
class ParsedModule:
    id: Optional[str] = None
    cells: list[ParsedCell] = field(default_factory=list)


@dataclass
class ParsedNotebook:
    id: Optional[str] = None
    meta: dict[str, str] = field(default_factory=dict)
    modules: list[ParsedModule] = field(default_factory=list)


# SEE: https://api.observablehq.com/@sebastien/boilerplate.js
class NotebookParser:
    """A line-based cell extractor for Observable. This relies on the
    notebook exports to be formatted the same way, so it might need updates
    along the way. This is a rewrite of the original version that brings
    a bit more safety and resilience."""

    # Blocks
    RE_START_DECLARATION = re.compile("^const (\w+\d*) = \{$")
    RE_END_DECLARATION = re.compile("^\};$")
    RE_START_BLOCK = re.compile(r"^    \{$")
    RE_END_BLOCK = re.compile(r"^    \},?$")
    RE_START_VARIABLES = re.compile(r"^  variables: \[$")
    RE_END_VARIABLES = re.compile(r"^  \]$")

    # Inlines
    RE_MODULE = re.compile(r"m(\d+)")
    RE_EXPORT = re.compile(r"^export default \w+\d*;$")
    RE_ENTRY_ID = re.compile(r"^  id: \"([0-9a-f]+@\d+|@[\w\d\-_]+/[\w\d\-_]+)\",$")
    RE_ENTRY_MODULES = re.compile(r"^  modules: \[([^\]]+)\],?$")
    RE_ENTRY_INPUTS = re.compile(r"^      inputs: \[([^\]]+)\],?$")
    RE_ENTRY_NAME = re.compile(r'^      name: "([^"]+)",?$')
    RE_ENTRY_VALUE = re.compile(r"^      value: (.*)")
    RE_ENTRY_REMOTE = re.compile(r'^      remote: "([^"]+)",?$')
    RE_ENTRY_FROM = re.compile(r'^      from: "([^"]+)",?$')
    RE_META = re.compile(r"// ([\w ]+): (.*)$")

    def __init__(self):
        # self.notebooks: dict[str, Notebook] = {}
        # self.notebook: Optional[Notebook] = None
        self.lineNumber: int = 0
        # --
        # Maintains the current _declaration_, which is expected to
        # be either a module `(module,<modulenum>)` or a notebook `(notebook, None)`.
        self.blockStartLine: Optional[int] = None
        self.blockEndLine: int = 0
        # --
        self.modules: dict[str, ParsedModule] = {}
        self.module: Optional[ParsedModule] = None
        self.notebook: Optional[ParsedNotebook] = None
        self.cell: Optional[ParsedCell] = None
        self.blockLines: list[tuple[int, str]] = []

    def flush(self) -> ParsedNotebook:
        res = self.notebook
        self.lineNumber = 0
        self.blockStartLine = None
        self.blockEndLine = 0
        self.modules = {}
        self.module = None
        self.cell = None
        self.blockLines = []
        assert res
        return res

    def feed(self, line: str):
        # NOTE: We dont't expect the line to end with `\n`, but
        # it doesn't matter if it does.
        line = line.rstrip("\n")
        if self.blockStartLine is not None:
            self.blockLines.append((self.lineNumber, line))
        # ## Blocks
        if match := self.RE_START_DECLARATION.match(line):
            self.onStartDeclaration(match.group(1))
        elif match := self.RE_END_DECLARATION.match(line):
            self.onEndDeclaration()
        elif match := self.RE_START_VARIABLES.match(line):
            self.onStartModuleVariables()
        elif match := self.RE_END_VARIABLES.match(line):
            self.onEndModuleVariables()
        elif match := self.RE_START_BLOCK.match(line):
            self.onStartBlock()
        elif match := self.RE_END_BLOCK.match(line):
            self.onEndBlock()
        elif match := self.RE_EXPORT.match(line):
            self.onEnd()
        # ## Inlines
        elif match := self.RE_META.match(line):
            self.onMeta(match.group(1), match.group(2))
        elif match := self.RE_ENTRY_ID.match(line):
            self.onEntryId(match.group(1))
        elif match := self.RE_ENTRY_NAME.match(line):
            self.onEntryName(match.group(1))
        elif match := self.RE_ENTRY_VALUE.match(line):
            self.onEntryValue(match.group(1))
        elif match := self.RE_ENTRY_REMOTE.match(line):
            self.onEntryRemote(match.group(1))
        elif match := self.RE_ENTRY_FROM.match(line):
            self.onEntryFrom(match.group(1))
        elif match := self.RE_ENTRY_MODULES.match(line):
            self.onEntryModules([_.strip() for _ in match.group(1).split(",")])
        elif match := self.RE_ENTRY_INPUTS.match(line):
            self.onEntryInputs(
                [_.strip().strip('"') for _ in match.group(1).split(",")]
            )
        else:
            self.onLine(line)
        self.lineNumber += 1

    def onEnd(self):
        pass

    def onStartDeclaration(self, name: str):
        if match := self.RE_MODULE.match(name):
            self.module = ParsedModule()
            self.modules[name] = self.module
        elif name == "notebook":
            if not self.notebook:
                self.notebook = ParsedNotebook()
        else:
            raise RuntimeError(f"Unknown declaration: {name}")

    def onEndDeclaration(self):
        self.doEndCell()
        self.module = None

    def onStartModuleVariables(self):
        # We end any outstanding cell
        self.doEndCell()

    def onEndModuleVariables(self):
        self.doEndCell()

    # --
    # We need to be super careful around the block start and end, as they
    # can often trigger false positives when starting, and the alternative
    # would be to have to do full JavaScript parsing. Here we the strategy
    # is that we mark the last end of the block.
    def onStartBlock(self):
        if not self.cell:
            self.cell = ParsedCell()
        else:
            assert self.cell, "A cell should have been created"
            # This is false positive, ie. a cell content that looks
            # like the opening of a new cell

    def onEndBlock(self):
        self.blockEndLine = self.lineNumber

    def onMeta(self, key: str, value: str):
        if not self.notebook:
            self.notebook = ParsedNotebook()
        self.notebook.meta[key.lower()] = value.strip()

    def onEntryId(self, id: str):
        if self.module:
            assert (
                not self.module.id
            ), f"Module should not have duplicate id: '{id}' in {self.module} at {self.lineNumber}"
            self.module.id = id
        elif self.notebook:
            self.notebook.meta["id"] = id
        else:
            raise RuntimeError("Entry id should have a module or a notebook")

    def onEntryName(self, name: str):
        assert self.cell, "Name entry should only occur in cells"
        if not self.cell.name:
            self.cell.name = name
        else:
            # This is a false positive, like here, where "The name of the function"
            # will be considered part of the name.
            #
            # ```
            #                 {
            #       inputs: ["doc"],
            #       value: (function(doc){return(
            # doc(
            #   {
            #     name: "doc",
            #     desc: "Documents JavaScript values, including functions and objects",
            #     args: {
            #       name: "The name of the function.",
            #       desc: "The description of the function."
            #     }
            #   },
            #   doc
            # )
            # ```
            pass

    def doEndCell(self):
        # This gets the values from the cells
        if self.cell and self.blockStartLine is not None:
            for i, line in self.blockLines:
                if i >= self.blockStartLine and i <= self.blockEndLine:
                    self.cell.value.append(line)
        self.blockLines = []
        self.blockStartLine = None
        self.cell = None

    def doStartCell(self):
        if self.cell:
            self.doEndCell()
        self.cell = ParsedCell()
        assert self.module, "Cells should be defined within a module: {self.lineNumber}"
        self.module.cells.append(self.cell)
        self.blockStartLine = None

    def onEntryInputs(self, inputs: list[str]):
        if not self.cell or self.cell.inputs is not None:
            self.doStartCell()
        assert self.cell
        assert (
            not self.cell.inputs
        ), f"Inputs entry should not override an existing inputs: '{inputs}' overrides {self.cell} at line {self.lineNumber}"
        self.cell.inputs = inputs

    def onEntryRemote(self, name: str):
        if not self.cell or self.cell.remote is not None:
            self.doStartCell()
        assert self.cell
        self.cell.remote = name

    def onEntryFrom(self, name: str):
        if not self.cell or self.cell.remoteFrom is not None:
            self.doStartCell()
        assert self.cell
        self.cell.remoteFrom = name

    def onEntryValue(self, value: str):
        if self.cell and self.cell.value is not None:
            self.doStartCell()
        assert self.cell
        assert (
            not self.cell.value
        ), f"Value entry should not override an existing value: '{value}' overrides {self.cell} at line {self.lineNumber}"
        self.cell.value.append(value)
        # We reset the block start line
        self.blockStartLine = None

    def onEntryModules(self, modules: list[str]):
        assert self.notebook
        for m in modules:
            assert m in self.modules
            self.notebook.modules.append(self.modules[m])

    def onLine(self, line):
        if self.cell:
            if self.blockStartLine is None:
                self.blockStartLine = self.lineNumber
        elif line:
            # A stray non-empty line should not appear outside a cell,
            # or that means we're not parsing that line properly. This
            # ensure resilience to changes.
            raise RuntimeError(f"Could not parse line: {line}")


def process(notebook: ParsedNotebook) -> Notebook:
    res = Notebook()
    i: int = 0
    for module in notebook.modules:
        for parsed_cell in module.cells:
            res.addCell(
                name=parsed_cell.name,
                source=parsed_cell.remoteFrom,
                sourceName=parsed_cell.remote,
                # TODO: Not sure about the type
            )
            i += 1
            pass
    return res


def parse(text: str) -> ParsedNotebook:
    parser = NotebookParser()
    for line in text.split("\n"):
        parser.feed(line)
    return parser.flush()


# EOF
