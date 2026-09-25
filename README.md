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
By default, files discovered under conventional test paths (`test`, `tests`,
`testing`) and conventionally named test files/classes are skipped. Files passed
directly to the hook by pre-commit are always checked, including test declarations
in those files; use repeatable `--include-folder PATH` args to recursively
scan additional roots; these files are checked alongside files selected by
pre-commit's filters:

```yaml
hooks:
  - id: python-docstrings
    args: [--include-tests, --include-folder, src, --include-folder, tests]
```

All hooks still honor pre-commit `files` and `exclude` filters for filenames
that pre-commit passes to them. Included folders are explicit scan roots; their
files are not subject to consumer-side file filters. The CLI flags may also be
set directly in a hook's `args` list.

## Rules

* Test files are recognized by path components `test`, `tests`, or `testing`, Python-style `test_*.py` / `*_test.py` names, and Java/C# `Test*.java` / `*Test.java` names. Test declarations are recognized by class names prefixed by `Test` or suffixed by `Test`, `Tests`, `TestCase`, or `TestSuite`; test methods by `test`/`Test` prefix. Pass `--include-tests` to disable these exclusions.
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
