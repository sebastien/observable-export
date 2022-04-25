from .model import Notebook
from .api import (
    notebook_download,
    notebook_parse,
    notebook_md,
    notebook_js,
    notebook_json,
    notebook_parse,
)
import sys
import argparse
import json
import fnmatch


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

    try:
        notebook_source = notebook_download(args.notebook, key=args.api_key)
    except RuntimeError as e:
        sys.stderr.write(f"!!! ERR {e}\n")
        sys.stderr.flush()
        return 1

    notebook = notebook_parse(notebook_source) if output_format != "raw" else None
    if args.ignore and isinstance(notebook, Notebook):
        notebook = Notebook(
            id=notebook.id,
            cells=[_ for _ in notebook.cells if matches(_.name, args.ignore)],
        )

    def write(out) -> int:
        if output_format == "raw":
            out.write(notebook)
        elif output_format == "json":
            assert notebook and isinstance(notebook, Notebook)
            json.dump(
                {_.name: _.asDict() for _ in notebook.cells},
                out,
            )
        elif output_format == "md":
            assert notebook and isinstance(notebook, Notebook)
            for line in notebook_md(notebook):
                out.write(line)
            out.flush()
        elif output_format == "js":
            assert notebook and isinstance(notebook, Notebook)
            for line in notebook_js(
                notebook, transitiveExports=args.transitive_exports
            ):
                out.write(line)
            if args.manifest:
                manifest = (
                    {
                        _.name: _.asDict(source=False, value=False)
                        for _ in notebook.cells
                    },
                )
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
