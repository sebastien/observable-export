         _                       _   _                            _   
     ___| |_ ___ ___ ___ _ _ ___| |_| |___    ___ _ _ ___ ___ ___| |_ 
    | . | . |_ -| -_|  _| | | .'| . | | -_|  | -_|_'_| . | . |  _|  _|
    |___|___|___|___|_|  \_/|__,|___|_|___|  |___|_,_|  _|___|_| |_|  
                                                     |_|

A self-contained Python script that exports ObservableHQ notebooks to a
variety of formats including:

-   A standalone JavaScript file that does not require the Observable
    runtime, assuming your notebook doesn't contain too much
    Observable-specific syntax.

-   A standalone Markdown file that you can use to render your notebook
    in your website.

-   A JSON file if you want to be able to do some other stuff with the
    notebook.

## Quickstart

By downloading the script directly:

    curl -o observableexport.py https://raw.githubusercontent.com/sebastien/observable-export/main/src/py/observableexport.py 
    python ./observableexport.py @sebastien/boilerplate

or by using PIP

    python -m pip install --user observable-export

Note that *observable-export* required *Python 3.9+*.

## Examples

Checking out a named notebook

    observable-export @sebastien/boilerplate

Saving it as a module

    observable-export @sebastien/boilerplate -o boilerplate.js

Saving it as a markdown file

    observable-export @sebastien/boilerplate -o boilerplate.md

Saving it as JSON data structure

    observable-export @sebastien/boilerplate -o boilerplate.json

Checking out a specific revision

    observable-export @sebastien/boilerplate@2089

Checking out a private notebook

    observable-export -k $YOUR_API_KEY 623731e9e1fcb1ac

Alternatively you can set `OBSERVABLE_API_KEY` with your Observable API
key (you can get it [here](https://observablehq.com/settings/api-keys)).

## Limitations

-   The parsing of the notebook is using an ad-hoc, brittle parsing
    method that relies on specific formatting of the JavaScript file. It
    works alright, but may break if the underlying format changes. This
    could be improved by using a more structured cherry-picking parser.

-   The cell ordering algorithm is very basic and therefore not super
    fast.

## References

-   Observable API Keys
    [ObsHQ](https://observablehq.com/@observablehq/api-keys), although
    this article seems a bit outdated.
