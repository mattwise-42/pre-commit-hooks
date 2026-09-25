import tree_sitter_java

from docs_hooks._tree import declarations, parse


def validate_java(path, source, include_tests=False):
    tree, errors = parse(tree_sitter_java, source)
    if errors:
        return [f"{path}:1: syntax error: {errors[0]}"]
    types = {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration", "annotation_type_declaration"}
    members = {"method_declaration", "constructor_declaration"}
    result = []
    for node, documented in declarations(tree, types, members, include_tests):
        name = node.child_by_field_name("name")
        label = name.text.decode() if name else node.type
        if not documented:
            result.append(f"{path}:{node.start_point.row + 1}: {label} is missing adjacent Javadoc")
    return result
