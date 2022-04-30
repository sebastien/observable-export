from .model import Notebook, Cell
from .parser import NotebookParser
from typing import Optional, Iterator, Union
import requests
import os
import json

# TODO: Support caching
# TODO: Support request ETag
# TODO: Support listing notebooks (including private)
# TODO: Support listing notebook revisions(including private)

OBSERVABLE_API_KEY = "OBSERVABLE_API_KEY"
CACHE: dict[str, str] = {}


def observable_key(variable=OBSERVABLE_API_KEY) -> str:
    return (os.getenv(variable) or "").strip("\n").strip()


def observable_url(path: str) -> str:
    return f"https://api.observablehq.com/{path}"


def observable_request(url: str, apiKey: Optional[Union[bool, str]] = True) -> str:
    if url in CACHE:
        return CACHE[url]
    api_key = observable_key if apiKey is True else apiKey or ""
    headers = {"Authorization": f"ApiKey {api_key}"} if api_key else {}
    r = requests.get(observable_url(url), headers=headers)
    if r.status_code >= 200 and r.status_code < 300:
        CACHE[url] = r.text
        return r.text
    else:
        raise RuntimeError(f"Request to {url} failed with {r.status_code}: {r.text}")


def observable_list(
    path: str, apiKey: Optional[Union[bool, str]] = True, limit: int = 100
) -> list[dict]:
    res: dict[str, dict] = {}
    before: Optional[str] = None
    added: int = 1
    # There's a limit of 30 results per page, so we use the "before" query
    # parameter to iterate through the results.
    while added != 0 and len(res) < limit:
        added = 0
        for item in json.loads(
            observable_request(
                (f"{path}?before={before}" if before else path),
                apiKey or observable_key(),
            )
        ):
            nid = item["id"]
            update_time = item["update_time"]
            before = update_time if before is None or update_time < before else before
            if nid not in res:
                res[nid] = item
                added += 1
    return [_ for _ in res.values()]


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


def notebook_get(
    notebook: str,
    key: Optional[str] = None,
) -> str:
    """Downloads the given notebook, optionally using the given API key"""
    name = Notebook.ParseName(notebook)
    if not name:
        raise ValueError(
            f"Could not parse 'notebook', should be like '@user/notebook' or 'hexhash', got: {notebook}"
        )
    api_key = key or observable_key()
    rev = f"@{name.rev}" if name.rev is not None else ""
    if Notebook.IsPrivate(name):
        if not api_key:
            raise RuntimeError(
                f"Missing Observable API key variable {OBSERVABLE_API_KEY}, visit https://observablehq.com/settings/api-keys to create one"
            )
        # https://api.observablehq.com/d/[NOTEBOOK_ID][@VERSION].[FORMAT]?v=3&api_key=xxxx
        url = f"d/{name.id}{rev}.js"
    else:
        url = f"@{name.username}/{name.name}{rev}.js?"
    return observable_request(url, api_key)


def notebook_parse(content: str) -> Notebook:
    """Parses the given notebook text into a Notebook object"""
    parser = NotebookParser()
    for line in content.split("\n"):
        parser.feed(f"{line}\n")
    return parser.notebook


def notebook_dependencies(*notebook: str) -> list[str]:
    """Returns the list of all the dependencies, including transitive
    dependencies from this notebook."""
    loaded: dict[str, list[str]] = {}
    to_process: list[str] = [_ for _ in notebook]
    while to_process:
        n = notebook_parse(notebook_get(nid := to_process.pop()))
        assert nid not in loaded
        loaded[nid] = [_ for _ in n.imported]
        to_process += [_ for _ in loaded[nid] if _ not in loaded]
    return [_ for _ in loaded]


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


def notebook_js(notebook: Notebook, transitiveExports=False) -> Iterator[str]:
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
            ) + ".js'\n"

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
        elif not cell.isPreprocessed:
            yield cell.text

    yield "// EOF"


# EOF
