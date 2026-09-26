import ast
import re


def _section(docstring, name):
    match = re.search(rf"(?ms)^\s*{name}:\s*\n(.*?)(?=^\s*\w+:\s*$|\Z)", docstring)
    return match.group(1) if match else ""


def _nonempty_section(docstring, name):
    return bool(_section(docstring, name).strip())


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


def validate_python(path, source):
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as error:
        return [f"{path}:{error.lineno or 1}: syntax error: {error.msg}"]

    diagnostics = []

    def check(node, kind):
        doc = ast.get_docstring(node)
        line = node.lineno
        name = node.name
        if not doc:
            diagnostics.append(f"{path}:{line}: {kind} {name!r} is missing docstring")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [arg.arg for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
                if node.args.vararg:
                    params.append(node.args.vararg.arg)
                if node.args.kwarg:
                    params.append(node.args.kwarg.arg)
                missing = [param for param in params if param not in {"self", "cls"}]
                if missing:
                    diagnostics.append(f"{path}:{line}: {kind} {name!r} parameters {', '.join(missing)!r} require documentation in an Args: or Inputs: section")
                if _has_yield(node):
                    diagnostics.append(f"{path}:{line}: {kind} {name!r} requires a non-empty Yields: section")
                elif _returns_value(node):
                    diagnostics.append(f"{path}:{line}: {kind} {name!r} requires a non-empty Returns: section")
            return
        params = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            params = [arg.arg for arg in args.posonlyargs + args.args + args.kwonlyargs]
            if args.vararg:
                params.append(args.vararg.arg)
            if args.kwarg:
                params.append(args.kwarg.arg)
        section = _section(doc, "Args") or _section(doc, "Inputs")
        documented_params = set(re.findall(r"(?m)^\s*([A-Za-z_]\w*)\s*:", section))
        missing = [param for param in params if param not in {"self", "cls"} and param not in documented_params]
        if missing and not any(re.search(rf"(?m)^\s*{section}:\s*$", doc) for section in ("Args", "Inputs")):
            diagnostics.append(f"{path}:{line}: {kind} {name!r} parameters {', '.join(missing)!r} require documentation in an Args: or Inputs: section")
        else:
            for param in missing:
                diagnostics.append(f"{path}:{line}: {kind} {name!r} parameter {param!r} is undocumented in Args: or Inputs:")
        if _has_yield(node):
            if not _nonempty_section(doc, "Yields"):
                diagnostics.append(f"{path}:{line}: {kind} {name!r} requires a non-empty Yields: section")
        elif _returns_value(node) and not _nonempty_section(doc, "Returns"):
            diagnostics.append(f"{path}:{line}: {kind} {name!r} requires a non-empty Returns: section")

    def visit(node):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            check(node, kind)
            for child in node.body:
                visit(child)
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return diagnostics
