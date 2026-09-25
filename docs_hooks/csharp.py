import tree_sitter_c_sharp

from docs_hooks._tree import declarations, parse


def validate_csharp(path, source, include_tests=False):
    tree, errors = parse(tree_sitter_c_sharp, source)
    if errors:
        return [f"{path}:1: syntax error: {errors[0]}"]
    types = {"class_declaration", "interface_declaration", "struct_declaration", "enum_declaration", "record_declaration"}
    members = {"method_declaration", "constructor_declaration", "destructor_declaration", "operator_declaration", "conversion_operator_declaration"}
    result = []
    for node, documented in declarations(tree, types, members, include_tests):
        name = node.child_by_field_name("name")
        label = name.text.decode() if name else node.type
        if not documented:
            result.append(f"{path}:{node.start_point.row + 1}: {label} is missing adjacent XML documentation")
    return result
