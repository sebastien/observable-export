```
     _                       _   _                            _   
 ___| |_ ___ ___ ___ _ _ ___| |_| |___    ___ _ _ ___ ___ ___| |_ 
| . | . |_ -| -_|  _| | | .'| . | | -_|  | -_|_'_| . | . |  _|  _|
|___|___|___|___|_|  \_/|__,|___|_|___|  |___|_,_|  _|___|_| |_|  
                                                 |_|
```

A self-contained Python script that exports ObservableHQ notebooks to a
variety of formats including:

- A standalone JavaScript file that does not require the Observable runtime,
  assuming your notebook doesn't contain too much Observable-specific syntax.

- A standalone Markdown file that you can use to render your notebook in your
  website.

- A JSON file if you want to be able to do some other stuff with the notebook.

## Quickstart

```
curl -o observableexport.py https://raw.githubusercontent.com/sebastien/observable-export/main/src/py/observableexport.py 
python ./observableexport.py @sebastien/boilerplate
```

or using PIP:

```
python -m pip install --user observable-export
```

## Examples


Checking out a named notebook

    observable-export @sebastien/boilerplate

Saving it as a module

    observable-export @sebastien/boilerplate -o boilerplate.js

Checking out a specific revision

    observable-export @sebastien/boilerplate@2089

Checking out a private notebook

    observable-export -k $YOUR_API_KEY 623731e9e1fcb1ac

Alternatively you can set `OBSERVABLE_API_KEY` with your key.

## References

- Observable API Keys [ObsHQ](https://observablehq.com/@observablehq/api-keys),
  although this article seems a bit outdated.

