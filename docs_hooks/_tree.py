from tree_sitter import Language, Parser


def parse(grammar, source):
    parser = Parser(Language(grammar.language()))
    tree = parser.parse(source.encode())
    if tree.root_node.has_error:
        errors = []

        def visit(node):
            if node.type == "ERROR" or node.is_missing:
                errors.append(node.start_point.row + 1)
            for child in node.children:
                visit(child)

        visit(tree.root_node)
        return tree, [f"syntax error at line {min(errors, default=1)}"]
    return tree, []


def declarations(tree, types, members, include_tests=False):
    found = []

    def walk(node, in_test_type=False):
        for index, child in enumerate(node.children):
            name_node = child.child_by_field_name("name") if child.type in types or child.type in members else None
            name = name_node.text.decode() if name_node else ""
            is_test_type = child.type in types and (name.startswith("Test") or name.endswith(("Test", "Tests", "TestCase", "TestSuite")))
            is_test_member = child.type in members and (name.lower().startswith("test") or name.startswith("Test"))
            in_test = in_test_type or is_test_type or is_test_member
            if child.type in types | members and (include_tests or not in_test):
                found.append((child, _has_adjacent_doc(node.children, index)))
            walk(child, in_test_type or is_test_type or is_test_member)

    walk(tree.root_node)
    return found


def _has_adjacent_doc(children, index):
    previous = index - 1
    while previous >= 0 and children[previous].type in {"modifiers", "modifier", "attribute_list"}:
        previous -= 1
    if previous < 0:
        return False
    candidate = children[previous]
    if candidate.type not in {"comment", "block_comment"}:
        return False
    text = candidate.text.decode().lstrip()
    return text.startswith("///") if candidate.type == "comment" else candidate.type == "block_comment" and text.startswith("/**")
