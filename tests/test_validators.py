from docs_hooks.csharp import validate_csharp
from docs_hooks.java import validate_java
from docs_hooks.python import validate_python


def test_python_accepts_documented_declarations_and_sections():
    source = '''
"""module."""

def fetch(item, *, limit=1):
    """Fetch values.\n\n    Args:\n        item: Value to fetch.\n        limit: Maximum count.\n\n    Returns:\n        The fetched values.\n    """
    return [item][:limit]

class Outer:
    """Outer type."""

    class Inner:
        """Inner type."""

        def values(self, item):
            """Yield values.\n\n            Inputs:\n                item: Value to yield.\n\n            Yields:\n                Each value.\n            """
            yield item
'''
    assert validate_python("sample.py", source) == []


def test_python_reports_missing_docstrings_parameters_and_returns():
    source = '''
def missing(value):
    return value
'''
    diagnostics = validate_python("sample.py", source)
    assert any("missing docstring" in item for item in diagnostics)
    assert any("value" in item and "Args:" in item for item in diagnostics)
    assert any("Returns:" in item for item in diagnostics)


def test_python_checks_declarations_nested_in_control_flow():
    source = '''
def outer():
    """Outer function."""
    if True:
        def nested(value):
            return value
'''
    diagnostics = validate_python("sample.py", source)
    assert any("function 'nested' is missing docstring" in item for item in diagnostics)


def test_python_requires_nonempty_yields_section():
    source = '''
def values():
    """Yield values.\n\n    Yields:\n    """
    yield 1
'''
    assert any("non-empty Yields:" in item for item in validate_python("sample.py", source))


def test_python_syntax_error_is_diagnostic():
    assert any("syntax error" in item for item in validate_python("broken.py", "def broken(:\n"))


def test_python_validator_has_no_test_path_exceptions():
    source = "def helper():\n    return None\n"
    test_result = validate_python("tests/fixtures/Test.py", source)
    source_result = validate_python("src/Test.py", source)
    assert [item.split(": ", 1)[1] for item in test_result] == [item.split(": ", 1)[1] for item in source_result]


def test_python_skips_test_classes_unless_included():
    source = 'class TestWidget:\n    """Test type."""\nclass WidgetTests:\n    pass\n'
    assert validate_python("src/widgets.py", source) == []
    assert len(validate_python("src/widgets.py", source, include_tests=True)) == 1


def test_python_skips_test_methods_unless_included():
    source = 'class Helper:\n    """Helper."""\n    def test_helper(self):\n        pass\n'
    assert validate_python("src/helper.py", source) == []
    assert validate_python("src/helper.py", source, include_tests=True)


def test_java_accepts_adjacent_docs_for_nested_private_declarations():
    source = '''/** Public type. */
class Outer {
    /** Private method. */
    private void run() {}

    /** Nested type. */
    class Inner {
        /** Private constructor. */
        private Inner() {}
    }
}
'''
    assert validate_java("Example.java", source) == []


def test_java_reports_undocumented_nested_and_private_declarations():
    source = '''class Outer {
    private void run() {}
    class Inner { Inner() {} }
}
'''
    diagnostics = validate_java("Example.java", source)
    assert sum("missing adjacent Javadoc" in item for item in diagnostics) == 4


def test_java_syntax_error_is_diagnostic():
    assert any("syntax error" in item for item in validate_java("Broken.java", "class {"))


def test_java_validator_has_no_test_path_exceptions():
    source = "class Example { void run() {} }"
    test_result = validate_java("tests/Test.java", source)
    source_result = validate_java("src/Test.java", source)
    assert [item.split(": ", 1)[1] for item in test_result] == [item.split(": ", 1)[1] for item in source_result]


def test_java_skips_test_classes_unless_included():
    source = "/** Test type. */ class TestWidget { void helper() {} }"
    assert validate_java("src/Widget.java", source) == []
    assert validate_java("src/Widget.java", source, include_tests=True)




def test_csharp_accepts_adjacent_docs_for_nested_private_declarations():
    source = '''/// <summary>Outer type.</summary>
class Outer {
    /// <summary>Private method.</summary>
    private void Run() {}

    /// <summary>Nested type.</summary>
    class Inner {
        /// <summary>Private constructor.</summary>
        private Inner() {}
    }
}
'''
    assert validate_csharp("Example.cs", source) == []


def test_csharp_reports_undocumented_nested_and_private_declarations():
    source = '''class Outer {
    private void Run() {}
    class Inner { Inner() {} }
}
'''
    diagnostics = validate_csharp("Example.cs", source)
    assert sum("missing adjacent XML documentation" in item for item in diagnostics) == 4


def test_csharp_syntax_error_is_diagnostic():
    assert any("syntax error" in item for item in validate_csharp("Broken.cs", "class {"))


def test_csharp_validator_has_no_test_path_exceptions():
    source = "class Example { void Run() {} }"
    test_result = validate_csharp("tests/Test.cs", source)
    source_result = validate_csharp("src/Test.cs", source)
    assert [item.split(": ", 1)[1] for item in test_result] == [item.split(": ", 1)[1] for item in source_result]


def test_csharp_skips_test_classes_unless_included():
    source = "class TestWidget { void Helper() {} }"
    assert validate_csharp("src/Widget.cs", source) == []
    assert validate_csharp("src/Widget.cs", source, include_tests=True)
