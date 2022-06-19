from .model import Notebook, Cell
from .parser import NotebookParser
from typing import Optional, Iterator, Union, Generic, TypeVar, cast
import requests
import os
import json
from dataclasses import dataclass

# TODO: Support caching
# TODO: Support request ETag
# TODO: Support listing notebooks (including private)
# TODO: Support listing notebook revisions(including private)

T = TypeVar("T")
OBSERVABLE_API_KEY = "OBSERVABLE_API_KEY"


@dataclass
class NotebookRef:
    """An unambiguous reference to a notebook"""

    id: str
    version: int
    username: Optional[str] = None
    name: Optional[str] = None


@dataclass
class NotebookHeader:
    """The parse result of a JavaScript header
    for an observable notebook"""

    id: Optional[str]
    version: int
    username: str
    name: Optional[str]


class Singleton(Generic[T]):
    """Utility singleton"""

    Instance: Optional[T] = None

    @classmethod
    def Get(cls):
        if not cls.Instance:
            cls.Instance = cls()
        return cls.Instance

    def __init__(self):
        if not self.__class__.Instance:
            self.__class__.Instance = self


class ObservableAPI(Singleton["ObservableAPI"]):
    """The baseline Observable API"""

    def __init__(self, key: Optional[str] = None):
        super().__init__
        self.apikey: Optional[str] = key
        self.cache: dict[str, str] = {}

    def key(self, variable=OBSERVABLE_API_KEY) -> str:
        return (os.getenv(variable) or "").strip("\n").strip()

    def url(self, path: str) -> str:
        return f"https://api.observablehq.com/{path}"

    def request(self, url: str, key: Optional[str] = None) -> str:
        if url in self.cache:
            return self.cache[url]
        api_key: str = key or self.key()
        abs_url = self.url(url)
        headers = {"Authorization": f"ApiKey {api_key}"} if api_key else {}
        r = requests.get(abs_url, headers=headers)
        if r.status_code >= 200 and r.status_code < 300:
            self.cache[url] = r.text
            return r.text
        else:
            raise RuntimeError(
                f"Request to {url} failed with {r.status_code}: {r.text}"
            )

    def list(
        self, path: str, key: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        res: dict[str, dict] = {}
        before: Optional[str] = None
        added: int = 1
        # There's a limit of 30 results per page, so we use the "before" query
        # parameter to iterate through the results.
        while added != 0 and len(res) < limit:
            added = 0
            for item in json.loads(
                self.request(
                    (f"{path}?before={before}" if before else path),
                    key or self.key(),
                )
            ):
                nid = item["id"]
                update_time = item["update_time"]
                before = (
                    update_time if before is None or update_time < before else before
                )
                if nid not in res:
                    res[nid] = item
                    added += 1
        return [_ for _ in res.values()]


class NotebookAPI(Singleton["NotebookAPI"]):
    """Wraps the notebook/document Observable API"""

    def __init__(self, api: Optional[ObservableAPI] = None):
        super().__init__()
        self.api: ObservableAPI = api or ObservableAPI.Get()
        self.names: dict[str, str] = {}
        self.latest: dict[str, int] = {}
        self.ids: dict[str, str] = {}
        self.resolved: dict[str, NotebookRef] = {}

    def parseJSHeader(self, source: str) -> NotebookHeader:
        meta = {
            (k[3:].lower().strip().split()[0]): v.strip()
            for k, v in (l.split(":", 1) for l in source.split("\n")[0:5])
        }
        # {'url': 'https://observablehq.com/d/XXXXXXXXXXXXXXXX', 'title':
        # '000-Sitemap', 'author': 'Sébastien Pierre (@sebastien)', 'version':
        # '38', 'runtime': ' 1'}
        # -or-
        # {'url': 'https://observablehq.com/@sebastien/boilerplate', 'title':
        # 'Boilerplate', 'author': 'Sébastien Pierre (@sebastien)', 'version':
        # '2234', 'runtime versi
        return NotebookHeader(
            id=meta["url"].rsplit("/d/", 1)[-1] if "/d/" in meta["url"] else None,
            version=int(meta["version"]),
            name=meta["url"].rsplit("/", 1)[-1] if "/@" in meta["url"] else None,
            username=meta["author"].rsplit("(@", 1)[1].split(")")[0],
        )

    def resolve(
        self, notebook: Union[NotebookRef, str], key: Optional[str] = None
    ) -> NotebookRef:
        """Resolves the given notebook name"""
        # We reuse the resolution cache
        if isinstance(notebook, NotebookRef):
            return notebook
        elif notebook in self.resolved:
            return self.resolved[notebook]
        name = Notebook.ParseName(notebook)
        if not name:
            raise ValueError(
                f"Could not parse 'notebook', should be like '@user/notebook' or 'hexhash', got: {notebook}"
            )
        api_key = key or self.api.key()
        rev = f"@{name.rev}" if name.rev is not None else ""
        if Notebook.IsPrivate(name):
            if not api_key:
                raise RuntimeError(
                    f"Missing Observable API key variable {OBSERVABLE_API_KEY}, visit https://observablehq.com/settings/api-keys to create one"
                )
            ref = f"d/{name.id}{rev}"
            # https://api.observablehq.com/d/[NOTEBOOK_ID][@VERSION].[FORMAT]?v=3&api_key=xxxx
            header = self.parseJSHeader(observable_request(f"{ref}.js", key))
            assert name.id
            document_id: str = header.id or name.id
            document_latest: int = header.version
            document_name: Optional[str] = header.name
            document_user: str = header.username
        elif resolved := self.resolved.get(f"@{name.username}/{name.name}"):
            # In case the name was already resolved, we can return it right away
            # and save a request.
            document_id = resolved.id
            document_latest = name.rev or resolved.version
            document_name = name.name
            assert name.username
            document_user = name.username
        else:
            data = json.loads(
                observable_request(f"document/@{name.username}/{name.name}{rev}", key),
            )
            # SEE: https://api.observablehq.com/document/@sebastien/boilerplate
            document_id = str(data["id"])
            document_latest = int(data["latest_version"])
            document_name = str(data["slug"])
            document_user = data["owner"]["login"]
        assert document_id
        self.latest[document_id] = document_latest
        if document_name:
            self.ids[document_name] = document_id
            self.names[document_id] = document_name
        res = NotebookRef(
            id=document_id,
            version=int(name.rev) if name.rev else document_latest,
            username=document_user,
            name=document_name,
        )
        self.resolved[notebook] = res
        return res

    # FIXME: We should add a resolver. And also the actual resolved ID may
    # be different from the  ID that we requested. The Observable API returns
    # the notebook AND its revision number.
    def dependencies(
        self, *notebook: Union[NotebookRef, str], key: Optional[str] = None
    ) -> list[str]:
        """Returns the list of all the dependencies, including transitive
        dependencies from this notebook."""
        loaded: dict[str, list[str]] = {}
        to_process: list[NotebookRef] = [self.resolve(_, key) for _ in notebook]
        while to_process:
            nref = to_process.pop()
            if nref.id in loaded:
                continue
            n = self.load(nref, key=key)
            if n:
                loaded[nref.id] = [_ for _ in n.imported]
                to_process += [
                    self.resolve(_) for _ in loaded[nref.id] if _ not in loaded
                ]
        return [_ for _ in loaded]

    def get(
        self,
        notebook: Union[NotebookRef, str],
        key: Optional[str] = None,
    ) -> str:
        """Downloads the given notebook, optionally using the given API key"""
        ref = self.resolve(notebook)
        api_key = key or self.api.key()
        if not ref.name:
            if not api_key:
                raise RuntimeError(
                    f"Missing Observable API key variable {OBSERVABLE_API_KEY}, visit https://observablehq.com/settings/api-keys to create one"
                )
            # https://api.observablehq.com/d/[NOTEBOOK_ID][@VERSION].[FORMAT]?v=3&api_key=xxxx
            url = f"d/{ref.id}@{ref.version}.js"
        else:
            url = f"@{ref.username}/{ref.name}@{ref.version}.js"
        return self.api.request(url, api_key)

    def load(
        self, notebook: Union[NotebookRef, str], key: Optional[str] = None
    ) -> Optional[Notebook]:
        """Gets and parses the given notebook"""
        return self.parse(self.get(notebook, key=key))

    def parse(self, content: str) -> Optional[Notebook]:
        """Parses the given notebook text into a Notebook object"""
        parser = NotebookParser()
        for line in content.split("\n"):
            parser.feed(f"{line}\n")
        return parser.notebook


# --
# ## High-Level API


def observable_key(variable=OBSERVABLE_API_KEY) -> str:
    return ObservableAPI.Get().key(variable)


def observable_url(path: str) -> str:
    return ObservableAPI.Get().url(path)


def observable_request(url: str, key: Optional[str] = None) -> str:
    return ObservableAPI.Get().request(url, key=key)


def observable_list(
    path: str, key: Optional[str] = None, limit: int = 100
) -> list[dict]:
    return ObservableAPI.Get().list(path, key=key, limit=limit)


def user_information(username: str):
    pass


def user_collections(username: str, key: Optional[str] = None):
    return json.loads(observable_request(f"collections/@{username}", key))


def user_notebooks(username: str, key: Optional[str] = None, limit: int = 100):
    """Lists the public notebooks of the given user, up to `limit` documents."""
    return observable_list(f"documents/@{username}", key, limit)


def user_collection_notebooks(
    username: str, collection: str, key: Optional[str] = None
):
    return json.loads(
        observable_request(
            f"collection/@{username}/{collection}", key or observable_key()
        )
    )


def notebook_resolve(notebook: str, key: Optional[str] = None) -> NotebookRef:
    return NotebookAPI.Get().resolve(notebook, key)


def notebook_get(
    notebook: str,
    key: Optional[str] = None,
) -> str:
    return NotebookAPI.Get().get(notebook, key)


def notebook_parse(content: str) -> Optional[Notebook]:
    return NotebookAPI.Get().parse(content)


def notebook_load(notebook: str, key: Optional[str] = None) -> Optional[Notebook]:
    return NotebookAPI.Get().load(notebook, key)


def notebook_dependencies(*notebook: str, key: Optional[str] = None) -> list[str]:
    return NotebookAPI.Get().dependencies(*notebook, key=key)


def notebook_json(notebook: Notebook) -> str:
    return json.dumps(
        {_.name: _.asDict() for _ in notebook.cells},
    )


def notebook_md(notebook: Notebook) -> Iterator[str]:
    """Converts the Observable notebook as a Markdown document."""
    for cell in notebook.cells:
        if cell.type == "md":
            yield cell.text
            yield "\n\n"
        else:
            yield f"```{cell.type}\n"
            if cell.name:
                yield f"const {cell.name} = "
            for line in cell.value:
                yield line
            yield "```\n\n"


def notebook_js(
    notebook: Notebook,
    transitiveExports=False,
    withPreprocessed=True,
    withAnonymous=True,
    importParameters: Optional[str] = None,
) -> Iterator[str]:
    """Converts the Observable notebook as a JavaScript module."""

    # --
    # We start with the imported cells, which are found in the
    # notebook dependencies.
    imported_cells: dict[str, Cell] = {}
    cells_defined: dict[str, Cell] = {_.name: _ for _ in notebook.defined}
    # The dependencies are a list of cells grouped by source (notebook)
    # name.
    for source, cells in notebook.dependencies.items():
        # NOTE: We will skip any cell that is imported but then
        # shadowed by a defined cell.
        import_cells: dict[str, Cell] = {
            _.name: _
            for _ in cells
            if (_.name not in imported_cells) and (_.name not in cells_defined)
        }

        if import_cells:
            imported_cells.update(import_cells)
            prefix = "./" if notebook.isPrivate else "../"
            notebook_name = Notebook.ParseName(source)
            assert notebook_name, f"Could not parse source as a notebook: {source}"
            # NOTE: We renamed the cells with `__` as a prefix so that they
            # don't clash when we export them.
            import_names = (
                f"{cell.sourceName or cell.name} as __{name}"
                if transitiveExports
                else (f"{cell.sourceName} as {name}" if cell.sourceName else name)
                for name, cell in import_cells.items()
            )
            yield "import {" + ", ".join(import_names) + "} from '" + prefix + (
                source
            ) + f".js{importParameters or ''}'\n"

    if transitiveExports:
        # --
        # We transitively export the imported cells, which is what is
        # expected in Observable.
        for name in imported_cells:
            yield f"export const {name} = __{name};\n"

    # --
    # We output the defined notebook cells, skipping the views and the
    # mutable ones.
    for cell in notebook.defined:
        # We filter out ObservableHQ specific viewof and initial (mutable)
        # variables. We should probably tag the cells.
        if cell.name.startswith("viewof_"):
            continue
        elif cell.name.startswith("initial_"):
            continue
        elif cell.name.startswith("mutable_"):
            continue
        elif (not cell.isPreprocessed or withPreprocessed) and (
            not cell.isAnonymous or withAnonymous
        ):

            yield f"\n// @cell('{cell.name}', {cell.inputs})\nexport const {cell.name} = (\n"
            yield json.dumps(
                {"type": cell.type, "value": cell.text}
            ) if cell.isPreprocessed else "".join(cell.value)
            yield ");\n"

    yield "// EOF\n"


# EOF
