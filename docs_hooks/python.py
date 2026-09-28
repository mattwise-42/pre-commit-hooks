import ast
import re


_SECTION_HEADINGS = {
    "Args:",
    "Arguments:",
    "Attributes:",
    "Class Attributes:",
    "Deprecated:",
    "Example:",
    "Examples:",
    "Inputs:",
    "Keyword Args:",
    "Keyword Arguments:",
    "Methods:",
    "Module Attributes:",
    "Note:",
    "Notes:",
    "Other Parameters:",
    "Parameters:",
    "Properties:",
    "Raises:",
    "References:",
    "Returns:",
    "See Also:",
    "Todo:",
    "Warnings:",
    "Yields:",
}
_INPUT_SECTIONS = ("Args", "Arguments", "Parameters", "Inputs")
_PARAMETER_LINE = re.compile(
    r"^\s*(?P<name>\*{0,2}[A-Za-z_]\w*)(?:\s+\([^)]*\))?:\s*(?P<description>\S.*)$"
)


def _section_lines(docstring, heading):
    lines = docstring.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == f"{heading}:"), None)
    if start is None:
        return None

    section = []
    for line in lines[start + 1 :]:
        if line.strip() in _SECTION_HEADINGS:
            break
        if line.strip():
            section.append(line)
    return section


def _documented_parameters(docstring):
    for heading in _INPUT_SECTIONS:
        section = _section_lines(docstring, heading)
        if section is not None:
            return {
                match.group("name").lstrip("*")
                for line in section
                if (match := _PARAMETER_LINE.match(line))
            }
    return None


def _has_section_content(docstring, heading):
    section = _section_lines(docstring, heading)
    return bool(section)


def _returns_value(node):
    def visit(current):
        for child in ast.iter_child_nodes(current):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if (isinstance(child, ast.Return) and child.value is not None
                    and not (isinstance(child.value, ast.Constant) and child.value.value is None)) or visit(child):
                return True
        return False
    return visit(node)


def _has_yield(node):
    def visit(current):
        for child in ast.iter_child_nodes(current):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if isinstance(child, (ast.Yield, ast.YieldFrom)) or visit(child):
                return True
        return False
    return visit(node)


def _is_static_method(node):
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            decorator = decorator.func
        if isinstance(decorator, ast.Name) and decorator.id == "staticmethod":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "staticmethod":
            return True
    return False


def _no_output_annotation(annotation):
    if isinstance(annotation, ast.Name):
        name = annotation.id
    elif isinstance(annotation, ast.Attribute):
        name = annotation.attr
    elif isinstance(annotation, ast.Constant):
        if annotation.value is None:
            return True
        if isinstance(annotation.value, str):
            name = annotation.value.rsplit(".", 1)[-1]
        else:
            return False
    else:
        return False
    return name in {"None", "NoReturn", "Never"}


def _output_section(node):
    if _has_yield(node):
        return "Yields"
    if node.returns is not None and _no_output_annotation(node.returns):
        return None
    if node.returns is not None or _returns_value(node):
        return "Returns"
    return None


def validate_python(path, source):
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as error:
        return [f"{path}:{error.lineno or 1}: syntax error: {error.msg}"]

    diagnostics = []

    def check(node, kind, is_method=False):
        doc = ast.get_docstring(node)
        line = node.lineno
        name = node.name
        if not doc or not doc.strip():
            diagnostics.append(f"{path}:{line}: {kind} {name!r} is missing docstring")
            return

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            params = [arg.arg for arg in args.posonlyargs + args.args]
            if args.vararg:
                params.append(args.vararg.arg)
            params.extend(arg.arg for arg in args.kwonlyargs)
            if args.kwarg:
                params.append(args.kwarg.arg)
            if is_method and not _is_static_method(node) and params and params[0] in {"self", "cls"}:
                params.pop(0)

            documented = _documented_parameters(doc)
            missing = [param for param in params if documented is None or param not in documented]
            if missing:
                if documented is None:
                    headings = ", ".join(f"{heading}:" for heading in _INPUT_SECTIONS)
                    diagnostics.append(
                        f"{path}:{line}: {kind} {name!r} parameters {', '.join(missing)!r} "
                        f"require documentation in one of these input sections: {headings}"
                    )
                else:
                    diagnostics.append(
                        f"{path}:{line}: {kind} {name!r} parameters {', '.join(missing)!r} "
                        "are undocumented in the selected input section"
                    )

            output = _output_section(node)
            if output and not _has_section_content(doc, output):
                diagnostics.append(
                    f"{path}:{line}: {kind} {name!r} requires a non-empty {output}: section"
                )

    def visit(node, in_class=False):
        if isinstance(node, ast.ClassDef):
            check(node, "class")
            for child in node.body:
                visit(child, True)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            check(node, "function", in_class)
            for child in node.body:
                visit(child)
            return
        for child in ast.iter_child_nodes(node):
            visit(child, in_class)

    visit(tree)
    return diagnostics
