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


def declarations(tree, types, members):
    found = []

    def walk(node):
        for index, child in enumerate(node.children):
            if child.type in types or child.type in members:
                found.append((child, _has_adjacent_doc(node.children, index)))
            walk(child)

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
