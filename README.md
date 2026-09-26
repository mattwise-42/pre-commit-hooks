# API documentation pre-commit hooks

Three opt-in hooks require public API documentation in Python, Java, and C#.
Python 3.10 or newer is required for the hook environments. Install pre-commit
in your project, then add this repository to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/mattwise-42/pre-commit-hooks
    rev: v0.1.0
    hooks:
      - id: python-docstrings
      - id: java-javadocs
      - id: csharp-xml-docs
```

Use a published version tag for `rev` and update it deliberately when upgrading. The initial `v0.1.0` example is illustrative until that tag is published; choose an existing release tag for a live consumer.
All hooks are opt-in; select only the languages used by your project. The
manifest targets `.py`, `.java`, and `.cs` via pre-commit's language file types.
Use pre-commit's native `files` and `exclude` filters to choose the source
folders and generated/test files for each hook. For example, to check Python
files under `src` and skip generated service clients:

```yaml
repos:
  - repo: https://github.com/mattwise-42/pre-commit-hooks
    rev: v0.1.0
    hooks:
      - id: python-docstrings
        files: ^src/.*[.]py$
        exclude: ^(api-clients/(openlink_token_service_client|person_matching_service_client))/
      - id: java-javadocs
        files: ^src/main/java/.*\.java$
        exclude: ^(api-clients/(openlink_token_service_client|person_matching_service_client))/
      - id: csharp-xml-docs
        files: ^src/.*\.cs$
        exclude: ^(api-clients/(openlink_token_service_client|person_matching_service_client))/
```

Use `files` to narrow the normal language filter and `exclude` to remove paths
from that selection. Test files are treated like any other files: include or
exclude their directories/names in these regular expressions. The hooks only
inspect filenames passed by pre-commit; they do not recursively scan folders.
For example, `files: ^(src|tests)/.*[.]py$` checks both source and tests, while
`exclude: ^tests/` checks only source; add generated paths to `exclude` as needed.

## Rules

* `python-docstrings` uses only Python's standard-library AST. It requires
  docstrings for classes, functions, and methods; an `Args:` or `Inputs:`
  section documenting every non-`self`/`cls` parameter; and non-empty
  `Returns:` sections for functions that return a value or `Yields:` sections
  for generators. Syntax errors are reported as diagnostics.
* `java-javadocs` requires an adjacent `/** ... */` comment on types, methods,
  and constructors, including private declarations. Nested declarations are
  checked. Syntax errors are reported.
* `csharp-xml-docs` requires adjacent `///` comments on types, methods,
  and constructors, including private declarations. Nested declarations are
  checked. Syntax errors are reported.

Java and C# hooks install the pinned Tree-sitter runtime and their own pinned
language grammar in their isolated pre-commit environments. The Python hook
has no parser runtime dependencies; parser packages are not downloaded on its
first run. Tree-sitter validates syntax but does not interpret whether comment
content is semantically complete beyond presence.

## Development

```sh
python -m pip install build pytest pre-commit
python -m pytest -q
python -m build
pre-commit run --all-files
```
