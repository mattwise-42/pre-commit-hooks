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


def test_python_stops_checking_inputs_and_outputs_when_docstring_is_missing():
    source = '''
def missing(value) -> int:
    return value
'''
    diagnostics = validate_python("sample.py", source)
    assert len(diagnostics) == 1
    assert "missing docstring" in diagnostics[0]


def test_python_reports_missing_class_and_method_docstrings():
    source = '''
class Example:
    def run(self):
        return 1
'''
    diagnostics = validate_python("sample.py", source)
    assert len(diagnostics) == 2
    assert any("class 'Example' is missing docstring" in item for item in diagnostics)
    assert any("function 'run' is missing docstring" in item for item in diagnostics)


def test_python_reports_missing_parameters_and_annotated_return_documentation():
    source = '''
def missing(value, extra) -> int:
    """Calculate a value.

    Args:
        value: Input value.
    """
    pass
'''
    diagnostics = validate_python("sample.py", source)
    assert any("extra" in item and "undocumented" in item for item in diagnostics)
    assert any("Returns:" in item for item in diagnostics)


def test_python_accepts_legacy_input_headings_and_typed_variadic_parameters():
    source = '''
def parse(positional, /, value, *args, named, **kwargs):
    """Parse values.

    Parameters:
        positional: Positional-only value.
        value (str): Main value.
        *args: Additional positional values.
        named (int): Named value.
        **kwargs: Additional keyword values.
    """
    pass
'''
    assert validate_python("sample.py", source) == []


def test_python_requires_a_nonempty_description_for_each_parameter():
    source = '''
def parse(value):
    """Parse a value.

    Args:
        value:
    """
    pass
'''
    diagnostics = validate_python("sample.py", source)
    assert any("value" in item and "undocumented" in item for item in diagnostics)


def test_python_uses_only_the_first_present_input_section():
    source = '''
def parse(first, second):
    """Parse values.

    Arguments:
        first: First value.

    Parameters:
        second: Second value.
    """
    pass
'''
    diagnostics = validate_python("sample.py", source)
    assert any("second" in item and "undocumented" in item for item in diagnostics)


def test_python_only_omits_first_self_or_cls_parameter_on_nonstatic_methods():
    source = '''
def module_function(self, cls):
    """Module function.

    Args:
        self: First input.
        cls: Second input.
    """

class Example:
    """Example class."""

    def method(self, value) -> None:
        """Instance method.

        Args:
            value: Method input.
        """

    @classmethod
    def class_method(cls, value) -> None:
        """Class method.

        Args:
            value: Method input.
        """

    @staticmethod
    def static_method(self, cls) -> None:
        """Static method.

        Args:
            self: First input.
            cls: Second input.
        """
'''
    assert validate_python("sample.py", source) == []


def test_python_requires_self_and_cls_inputs_outside_the_implicit_receiver():
    source = '''
def module_function(self, cls):
    """Module function.

    Args:
        cls: Second input.
    """

class Example:
    """Example class."""

    @staticmethod
    def static_method(self, cls) -> None:
        """Static method.

        Args:
            cls: Second input.
        """

    def method(cls, self) -> None:
        """Instance method.

        Args:
            self: Second input.
        """
'''
    diagnostics = validate_python("sample.py", source)
    assert len(diagnostics) == 2
    assert any("module_function" in item and "self" in item for item in diagnostics)
    assert any("static_method" in item and "self" in item for item in diagnostics)


def test_python_treats_whitespace_only_docstrings_as_missing():
    source = '''
class Example:
    """   """

    def run(value) -> int:
        """
        """
'''
    diagnostics = validate_python("sample.py", source)
    assert len(diagnostics) == 2
    assert all("missing docstring" in item for item in diagnostics)


def test_python_skips_returns_for_none_and_no_return_annotations():
    source = '''
def returns_none() -> None:
    """Update state."""

def returns_quoted_none() -> "None":
    """Update state."""

def never_returns() -> typing.NoReturn:
    """Stop execution."""

def never_returns_by_name() -> NoReturn:
    """Stop execution."""

def never_returns_with_never() -> Never:
    """Stop execution."""

def quoted_never_returns() -> "typing_extensions.Never":
    """Stop execution."""

def quoted_no_return_name() -> "NoReturn":
    """Stop execution."""

def quoted_never_name() -> "Never":
    """Stop execution."""
'''
    assert validate_python("sample.py", source) == []


def test_python_none_annotation_suppresses_returns_even_for_a_return_call():
    source = '''
def update() -> None:
    """Update stored state."""
    return write_state()
'''
    assert validate_python("sample.py", source) == []


def test_python_requires_returns_for_unannotated_non_none_return_values():
    source = '''
def transform(value):
    """Transform a value."""
    return value
'''
    assert any("Returns:" in item for item in validate_python("sample.py", source))


def test_python_requires_returns_for_annotations_without_return_statements():
    source = '''
def annotated() -> int:
    """Calculate a value."""
    pass

async def async_annotated() -> str:
    """Calculate a value asynchronously."""
    pass
'''
    diagnostics = validate_python("sample.py", source)
    assert sum("Returns:" in item for item in diagnostics) == 2


def test_python_return_sections_end_at_known_headings_only():
    source = '''
def results() -> dict:
    """Build results.

    Returns:
        Result:
        - count: Number of matches.

    Raises:
        ValueError: If the source is invalid.
    """
    pass
'''
    assert validate_python("sample.py", source) == []


def test_python_nested_declarations_do_not_supply_outer_outputs():
    source = '''
def outer():
    """Run local helpers."""

    def inner() -> int:
        """Calculate a value.

        Returns:
            The helper result.
        """
        return 1

    async def async_inner() -> str:
        """Calculate asynchronously.

        Returns:
            The helper result.
        """
        return "value"

    class Nested:
        """Nested class."""

        def values(self):
            """Yield values.

            Yields:
                Each value.
            """
            yield 1

    transform = lambda: 1
'''
    assert validate_python("sample.py", source) == []


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
