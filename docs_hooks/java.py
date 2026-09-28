import re

import tree_sitter_java

from docs_hooks._tree import declarations, parse


def _has_own_javadoc(comment):
    body = comment.removeprefix("/**")
    if body.endswith("*/"):
        body = body[:-2]
    body = re.sub(r"(?m)^[ \t]*\*[ \t]?", "", body).strip()
    return body != "{@inheritDoc}"


def validate_java(path, source, require_own_docs=False):
    tree, errors = parse(tree_sitter_java, source)
    if errors:
        return [f"{path}:1: syntax error: {errors[0]}"]
    types = {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration", "annotation_type_declaration"}
    members = {"method_declaration", "constructor_declaration"}
    result = []
    for node, comment in declarations(tree, types, members):
        name = node.child_by_field_name("name")
        label = name.text.decode() if name else node.type
        if comment is None:
            result.append(f"{path}:{node.start_point.row + 1}: {label} is missing adjacent Javadoc")
        elif require_own_docs and not _has_own_javadoc(comment):
            result.append(f"{path}:{node.start_point.row + 1}: {label} uses only inherited docs; own Javadoc content is required")
    return result
