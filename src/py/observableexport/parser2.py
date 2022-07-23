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
    id: int
    cells: list[ParsedCell] = field(default_factory=list)


@dataclass
class ParsedNotebook:
    id: Optional[str] = None
    meta: dict[str, str] = field(default_factory=dict)
    modules: list[ParsedModule] = field(default_factory=list)


class NotebookParser:

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
        self.inDeclaration: Optional[tuple[str, Optional[int]]] = None
        self.inVariables: bool = False
        self.blockStartLine: Optional[int] = None
        self.blockEndLine: int = 0
        # --
        self.modules: list[ParsedModule] = []
        self.module: Optional[ParsedModule] = None
        self.notebook: Optional[ParsedNotebook] = None
        self.cell: Optional[ParsedCell] = None

    def flush(text: str) -> tuple[Optional[Notebook], dict[str, Notebook]]:
        return None, None

    def feed(self, line: str):
        # NOTE: We dont't expect the line to end with `\n`, but
        # it doesn't matter if it does.
        line = line.rstrip("\n")
        # ## Blocks
        if match := self.RE_START_DECLARATION.match(line):
            print(f"{self.lineNumber:04d} START_DECLARTION")
            self.onStartDeclaration(match.group(1))
        elif match := self.RE_END_DECLARATION.match(line):
            print(f"{self.lineNumber:04d} END_DECLARTION")
            self.onEndDeclaration()
        elif match := self.RE_START_VARIABLES.match(line):
            print(f"{self.lineNumber:04d} START_VARIABLES")
            self.onStartModuleVariables()
        elif match := self.RE_END_VARIABLES.match(line):
            print(f"{self.lineNumber:04d} END_VARIABLES")
            self.onEndModuleVariables()
        elif match := self.RE_START_BLOCK.match(line):
            print(f"{self.lineNumber:04d} START_BLOCK")
            self.onStartBlock()
        elif match := self.RE_END_BLOCK.match(line):
            print(f"{self.lineNumber:04d} END_BLOCK")
            self.onEndBlock()
        elif match := self.RE_EXPORT.match(line):
            print(f"{self.lineNumber:04d} EXPORT")
            self.onEnd()
        # ## Inlines
        elif match := self.RE_META.match(line):
            self.onMeta(match.group(1), match.group(2))
        elif match := self.RE_ENTRY_ID.match(line):
            id = match.group(1)
            print(f"{self.lineNumber:04d} XXX{id=}")
            self.onEntryId(id)
        elif match := self.RE_ENTRY_NAME.match(line):
            self.onEntryName(match.group(1))
        elif match := self.RE_ENTRY_VALUE.match(line):
            self.onEntryValue(match.group(1))
        elif match := self.RE_ENTRY_REMOTE.match(line):
            remote = match.group(1)
            print(f"{self.lineNumber:04d} XXX{remote=}")
        elif match := self.RE_ENTRY_FROM.match(line):
            remote_from = match.group(1)
            print(f"{self.lineNumber:04d} XXX{remote_from=}")
        elif match := self.RE_ENTRY_MODULES.match(line):
            self.onEntryModules([_.strip() for _ in match.group(1).split(",")])
        elif match := self.RE_ENTRY_INPUTS.match(line):
            inputs = [_.strip().strip('"') for _ in match.group(1).split(",")]
            print(f"{self.lineNumber:04d} XXX{inputs=} {line=}")
        else:
            self.onLine(line)
        self.lineNumber += 1

    def onEnd(self):
        pass

    def onStartDeclaration(self, name: str):
        if match := self.RE_MODULE.match(name):
            self.inDeclaration = ("module", mid := int(name[1:]))
            self.module = ParsedModule(mid)
            self.modules.append(self.module)
        elif name == "notebook":
            self.inDeclaration = ("notebook", None)
        else:
            raise RuntimeError(f"Unknown declaration: {name}")

    def onEndDeclaration(self):
        self.inDeclaration = None
        self.cell = None
        self.module = None

    def onStartModuleVariables(self):
        assert (
            not self.inVariables
        ), f"Start module variables without previous end: {self.lineNumber}"
        self.inVariables = True

    def onEndModuleVariables(self):
        assert (
            self.inVariables
        ), f"End variables without previous start at line: {self.lineNumber}"
        self.inVariables = False

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
        self.notebook.meta[key] = value.strip()

    def onEntryId(self, id: str):
        if self.module:
            print("XXX MODULE ID=", id)
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

    def onEntryValue(self, value: str):
        assert self.cell, "Value entry should only occur in cells"
        assert (
            not self.cell.value
        ), f"Value entry should not override an existing value: '{value}' overrides {self.cell} at line {self.lineNumber}"
        self.cell.value.append(value)
        # We reset the block start line
        self.blockStartLine = None

    def onEntryModules(self, modules: list[str]):
        assert self.notebook
        print("XXX MODULES", modules)

    def onLine(self, line):
        if self.cell:
            if self.blockStartLine is None:
                self.blockStartLine = self.lineNumber
        elif line:
            # A stray non-empty line should not appear outside a cell,
            # or that means we're not parsing that line properly. This
            # ensure resilience to changes.
            raise RuntimeError(f"Could not parse line: {line}")


def parse(text: str) -> tuple[Optional[Notebook], dict[str, Notebook]]:
    parser = NotebookParser()
    for line in text.split("\n"):
        parser.feed(line)
    return parser.flush()


# EOF
