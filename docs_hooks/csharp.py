import re

import tree_sitter_c_sharp

from docs_hooks._tree import declarations, parse


def _has_own_xml_docs(comment):
    if comment.startswith("///"):
        body = re.sub(r"(?m)^[ \t]*/// ?", "", comment)
    else:
        body = comment.removeprefix("/**")
        if body.endswith("*/"):
            body = body[:-2]
    body = body.strip()
    return re.fullmatch(r"<inheritdoc(?:\s+[^>]*)?\s*/>", body) is None


def validate_csharp(path, source, require_own_docs=False):
    tree, errors = parse(tree_sitter_c_sharp, source)
    if errors:
        return [f"{path}:1: syntax error: {errors[0]}"]
    types = {"class_declaration", "interface_declaration", "struct_declaration", "enum_declaration", "record_declaration"}
    members = {"method_declaration", "constructor_declaration", "destructor_declaration", "operator_declaration", "conversion_operator_declaration"}
    result = []
    for node, comment in declarations(tree, types, members):
        name = node.child_by_field_name("name")
        label = name.text.decode() if name else node.type
        if comment is None:
            result.append(f"{path}:{node.start_point.row + 1}: {label} is missing adjacent XML documentation")
        elif require_own_docs and not _has_own_xml_docs(comment):
            result.append(f"{path}:{node.start_point.row + 1}: {label} uses only inherited docs; own XML documentation content is required")
    return result
