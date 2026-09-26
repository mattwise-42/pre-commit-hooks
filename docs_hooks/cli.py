import sys
from pathlib import Path


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
    diagnostics = []
    for name in argv if argv is not None else sys.argv[1:]:
        path = Path(name)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            diagnostics.append(f"{name}: cannot read file: {error}")
            continue
        diagnostics.extend(validator(name, source))
    for diagnostic in diagnostics:
        print(diagnostic, file=sys.stderr)
    return int(bool(diagnostics))


def python_docstrings():
    return main("python-docstrings")


def java_javadocs():
    return main("java-javadocs")


def csharp_xml_docs():
    return main("csharp-xml-docs")
