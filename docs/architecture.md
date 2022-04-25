# ObservableExport Architecture

## Design Principles

-   High level: the API is designed to abstract over the ObservableHQ
    API format, giving it more independence in case the underlying
    format changes.

-   Decoupled: the implementation itself is separated in distinct,
    clearly separated modules that take care of the different tasks

-   Reusable: while the primary use case is the `observable-export`
    tool, the OO model and its API can be embedded and reused in other
    tools.

## Components

-   `model`: defines the object-oriented API to represent *cells* and
    *notebooks*.
-   `parser`: defines the parser that take a string and returns a
    collection of *notebooks* and *cells*.
-   `api`: defines the key operations that can be performed with the
    ObservableHQ API.
-   `cli`: the command-line interface implemented as the `command`
    module and the `observable-export`CLI tool.

## Implementation

I hesitated to implement this tool/API in Observable itself (ie.
JavaScript), but at the time I started, [Deno](https://deno.land) was
still very new, and it was easier to get a prototype running with
Python.

The main challenge with the ObservableHQ API is that it is not very well
documented, and that it doesn't output JSON, hence the brittle ad-hoc
parsing. However, there's no reason to complain as having the API
enables many new use cases.
