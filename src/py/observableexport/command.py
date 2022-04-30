from .model import Notebook
from typing import Union
from .api import (
    notebook_get,
    notebook_parse,
    notebook_md,
    notebook_js,
    notebook_json,
    notebook_parse,
    notebook_dependencies,
)
import sys
import argparse
import json
from fnmatch import fnmatch


def matches(name: str, excludes: list[str]) -> bool:
    """Returns `False` if the `name` matches any of the `excludes` glob pattern"""
    for f in excludes:
        if f == name or fnmatch(name, f):
            return False
    return True


def run(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Extracts JavaScript modules from ObservableHQ notebooks."
    )
    parser.add_argument(
        "notebook",
        help="The name or ID of the notebook, for instance @sebastien/boilerplate or ",
        nargs="+",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        action="append",
        help="Excludes the given cell names",
    )
    parser.add_argument("-o", "--output", help="Outputs to the given file", default="")
    parser.add_argument(
        "-a",
        "--append",
        action="store_true",
        help="Appends to the output file",
        default=False,
    )
    parser.add_argument("-k", "--api-key", help="Sets the API key to use")
    parser.add_argument(
        "-m", "--manifest", action="store_true", help="Adds a manifest at the end"
    )
    parser.add_argument(
        "-d",
        "--dependencies",
        action="store_true",
        help="Outputs the notebook dependencies  for the given set of notebook",
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Supports the output type: 'js', 'json' or 'raw'",
    )
    parser.add_argument(
        "--transitive-exports",
        action="store_true",
        help="Notebooks re-export their imported symbols (js only)",
        default=False,
    )

    args = parser.parse_args()

    # We get the format type from the args or the output format
    output_ext = args.output.rsplit(".")[-1].lower() if "." in args.output else None
    output_format = args.type or output_ext or "js"
    output_format = ({"ojs": "raw"}).get(output_format, output_format)

    notebooks: list[Union[str, Notebook]] = []
    # NOTE: This is a bit awkward, but we do not need to parse the notebooks
    # just yet if we're using the dependencies.
    if not args.dependencies:
        for name in args.notebook:
            try:
                notebook_source = notebook_get(name, key=args.api_key)
            except RuntimeError as e:
                sys.stderr.write(f"!!! ERR {e}\n")
                sys.stderr.flush()
                return 1

            notebook = (
                notebook_parse(notebook_source) if output_format != "raw" else None
            )
            if args.ignore and isinstance(notebook, Notebook):
                notebook = Notebook(
                    id=notebook.id,
                    cells=[_ for _ in notebook.cells if matches(_.name, args.ignore)],
                )
            notebooks.append(notebook)

    def write(out) -> int:
        if args.dependencies:
            deps = notebook_dependencies(*args.notebook)
            if output_format == "raw":
                out.write("\n".join(deps))
            elif output_format == "md":
                out.write(
                    "\n".join(
                        [f" - [{_}](https://observablehq.com/d/{_})" for _ in deps]
                    )
                )
            else:
                out.write(json.dumps(deps))
        elif output_format == "raw":
            for notebook in notebooks:
                out.write(notebook)
        elif output_format == "json":
            if len(notebooks) == 1:
                out.write(notebook_json(notebooks[0]))
            else:
                out.write([notebook_json(_) for _ in notebooks])
        elif output_format == "md":
            for notebook in notebooks:
                assert notebook and isinstance(notebook, Notebook)
                for line in notebook_md(notebook):
                    out.write(line)
            out.flush()
        elif output_format == "js":
            manifest = {}
            for notebook in notebooks:
                assert notebook and isinstance(notebook, Notebook)
                for line in notebook_js(
                    notebook, transitiveExports=args.transitive_exports
                ):
                    out.write(line)
                    # FIXME: This may not make a lot of sense when multiple notebooks
                    manifest.update(
                        {
                            _.name: _.asDict(source=False, value=False)
                            for _ in notebook.cells
                        }
                    )
            if args.manifest:
                out.write(f"export const __manifest__ = (")
                json.dump(manifest, out)
                out.write(");\n")
        else:
            raise ValueError(
                "Supported types are json, js or md, got: {output_format} "
            )
        out.flush()
        return 0

    if args.output:
        with open(args.output, "a" if args.append else "w") as f:
            return write(f)
    else:
        return write(sys.stdout)


# EOF
