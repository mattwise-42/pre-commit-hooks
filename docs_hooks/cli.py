import argparse
import sys
from pathlib import Path


_EXTENSIONS = {
    "python-docstrings": ".py",
    "java-javadocs": ".java",
    "csharp-xml-docs": ".cs",
}


def main(hook_id, argv=None):
    if hook_id == "python-docstrings":
        from docs_hooks.python import validate_python
        validator = validate_python
    elif hook_id == "java-javadocs":
        from docs_hooks.java import validate_java
        validator = validate_java
    elif hook_id == "csharp-xml-docs":
        from docs_hooks.csharp import validate_csharp
        validator = validate_csharp
    else:
        print(f"unknown documentation hook: {hook_id}", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(prog=hook_id)
    parser.add_argument("--include-tests", action="store_true", help="include conventional test files and classes")
    parser.add_argument("--include-folder", action="append", default=[], metavar="PATH", help="recursively include source files under PATH (repeatable)")
    parser.add_argument("filenames", nargs="*")
    options = parser.parse_args(argv if argv is not None else sys.argv[1:])
    extension = _EXTENSIONS[hook_id]
    explicit_paths = {Path(name) for name in options.filenames}
    paths = set(explicit_paths)
    for folder in options.include_folder:
        root = Path(folder)
        if not root.is_dir():
            print(f"{root}: include folder does not exist or is not a directory", file=sys.stderr)
            return 2
        paths.update(path for path in root.rglob(f"*{extension}") if path.is_file())

    diagnostics = []
    for path in sorted(paths):
        name = str(path)
        if not path.is_file():
            print(f"{name}: include path is not a file", file=sys.stderr)
            return 2
        if not options.include_tests and path not in explicit_paths and _is_test_path(path):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            diagnostics.append(f"{name}: cannot read file: {error}")
            continue
        diagnostics.extend(validator(name, source, include_tests=options.include_tests or path in explicit_paths))
    for diagnostic in diagnostics:
        print(diagnostic, file=sys.stderr)
    return int(bool(diagnostics))


def _is_test_path(path):
    stem = path.stem.lower()
    return any(part.lower() in {"test", "tests", "testing"} for part in path.parts) or path.name.lower().startswith("test_") or stem.endswith(("_test", "_tests", "_testcase", "_testsuite")) or (path.suffix.lower() in {".java", ".cs"} and (stem.startswith("test") or stem.endswith(("test", "tests", "testcase", "testsuite"))))


def python_docstrings():
    return main("python-docstrings")


def java_javadocs():
    return main("java-javadocs")


def csharp_xml_docs():
    return main("csharp-xml-docs")
