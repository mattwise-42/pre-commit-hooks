import subprocess
import sys
from pathlib import Path

import pytest

from docs_hooks.cli import main

ROOT = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(("hook", "language", "extension"), [
    ("python-docstrings", "python", ".py"),
    ("java-javadocs", "java", ".java"),
    ("csharp-xml-docs", "csharp", ".cs"),
])
def test_consumer_hook_accepts_documented_and_rejects_undocumented(hook, language, extension, capsys):
    assert main(hook, [str(ROOT / language / f"Valid{extension}")]) == 0
    assert main(hook, [str(ROOT / language / f"Invalid{extension}")]) == 1
    output = capsys.readouterr().err
    assert output


def test_python_only_hook_module_has_no_parser_dependencies():
    code = "import docs_hooks.cli as cli; cli.python_docstrings(); import sys; assert not any(n.startswith('tree_sitter') for n in sys.modules)"
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)


def test_hook_reports_files_excluded_by_consumer_filters_not_validator_paths():
    assert main("python-docstrings", [str(ROOT / "python" / "invalid.py")]) == 1
