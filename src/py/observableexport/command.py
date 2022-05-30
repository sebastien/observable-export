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

    parser.add_argument("-k", "--api-key", help="Sets the API key to use")
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Adds an __all__ definition with all cell values",
    )
    parser.add_argument(
        "-m", "--manifest", action="store_true", help="Adds a manifest at the end"
    )
    parser.add_argument(
        "-n", "--named", action="store_true", help="Only includes named cells"
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
        "-e",
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

    notebooks: list[Notebook] = []
    # NOTE: This is a bit awkward, but we do not need to parse the notebooks
    # just yet if we're using the dependencies.
    notebook_sources: list[str] = []
    if not args.dependencies:
        for name in args.notebook:
            try:
                notebook_source = notebook_get(name, key=args.api_key)
            except RuntimeError as e:
                sys.stderr.write(f"!!! ERR {e}\n")
                sys.stderr.flush()
                return 1

            notebook_sources.append(notebook_source)
            notebook = (
                notebook_parse(notebook_source) if output_format != "raw" else None
            )
            if args.ignore and isinstance(notebook, Notebook):
                notebook = Notebook(
                    id=notebook.id,
                    cells=[_ for _ in notebook.cells if matches(_.name, args.ignore)],
                )
            if notebook:
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
            for _ in notebook_sources:
                out.write(_)
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
                    notebook,
                    transitiveExports=args.transitive_exports,
                    withAnonymous=False if args.named else True,
                    withPreprocessed=False if args.named else True,
                ):
                    out.write(line)
                    # FIXME: This may not make a lot of sense when multiple notebooks
                    manifest.update(
                        {
                            _.name: _.asDict(source=False, value=False)
                            for _ in notebook.cells
                            if not args.named or not (_.isAnonymous or _.isPreprocessed)
                        }
                    )
            if args.manifest:
                out.write(f"\nexport const __manifest__ = (")
                json.dump(manifest, out)
                out.write(");\n")
            if args.all:
                out.write("\nexport const __all__ = {")
                out.write(", ".join(_ for _ in manifest))
                out.write("};\n")

        else:
            raise ValueError(
                "Supported types are json, js or md, got: {output_format} "
            )
        out.flush()
        return 0

    if args.output:
        with open(args.output, "w") as f:
            return write(f)
    else:
        return write(sys.stdout)


# EOF
