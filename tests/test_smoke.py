import subprocess
import sys
from pathlib import Path

import pytest

from docs_hooks.cli import main

ROOT = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(("hook", "language", "valid", "invalid"), [
    ("python-docstrings", "python", "valid.py", "invalid.py"),
    ("java-javadocs", "java", "Valid.java", "Invalid.java"),
    ("csharp-xml-docs", "csharp", "Valid.cs", "Invalid.cs"),
])
def test_consumer_hook_accepts_documented_and_rejects_undocumented(hook, language, valid, invalid, capsys):
    assert main(hook, [str(ROOT / language / valid)]) == 0
    assert main(hook, ["--include-tests", str(ROOT / language / invalid)]) == 1
    output = capsys.readouterr().err
    assert output


def test_hook_include_folder_skips_test_named_files_by_default(tmp_path):
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "TestSupport.cs").write_text("class Helper { }\n")
    assert main("csharp-xml-docs", ["--include-folder", str(folder)]) == 0
    assert main("csharp-xml-docs", ["--include-tests", "--include-folder", str(folder)]) == 1


def test_hook_include_folder_scans_files_and_honors_test_option(tmp_path):
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "Widget.py").write_text("class Widget:\n    pass\n")
    (folder / "tests_placeholder.py").write_text("class TestWidget:\n    pass\n")

    assert main("python-docstrings", ["--include-folder", str(folder)]) == 1
    (folder / "tests_placeholder.py").unlink()
    (folder / "Widget.py").write_text('"""Widget module."""\nclass Widget:\n    """Widget type."""\n')
    (folder / "WidgetTests.py").write_text("class WidgetTests:\n    pass\n")
    assert main("python-docstrings", ["--include-folder", str(folder)]) == 0
    assert main("python-docstrings", ["--include-tests", "--include-folder", str(folder)]) == 1


def test_python_only_hook_module_has_no_parser_dependencies():
    code = "import docs_hooks.cli as cli; cli.python_docstrings(); import sys; assert not any(n.startswith('tree_sitter') for n in sys.modules)"
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)


def test_hook_inclusion_flags_work_through_pre_commit(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(f"""repos:\n  - repo: local\n    hooks:\n      - id: python-docstrings\n        name: Python docs\n        entry: {sys.executable} -m docs_hooks.cli python-docstrings\n        language: system\n        types: [python]\n""")
    source = tmp_path / "TestWidget.py"
    source.write_text("class TestWidget:\n    pass\n")

    result = subprocess.run([sys.executable, "-m", "pre_commit", "run", "--config", str(config), "python-docstrings", "--files", str(source)], cwd=ROOT.parent, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr

    config.write_text(config.read_text().replace("name: Python docs", "name: Python docs\\n        args: [--include-tests, --include-folder, " + str(ROOT / "python") + "]"))
    result = subprocess.run([sys.executable, "-m", "pre_commit", "run", "--config", str(config), "python-docstrings", "--files", str(source)], cwd=ROOT.parent, text=True, capture_output=True)
    assert result.returncode == 1, result.stdout + result.stderr


def test_explicit_hook_file_is_not_skipped_only_because_of_its_name(tmp_path):
    source = tmp_path / "src" / "TestSupport.cs"
    source.parent.mkdir()
    source.write_text("class Helper { }\n")
    assert main("csharp-xml-docs", [str(source)]) == 1
    source.write_text("class TestSupport { }\n")
    assert main("csharp-xml-docs", ["--include-tests", str(source)]) == 1


def test_hook_reports_files_excluded_by_consumer_filters_not_validator_paths():
    assert main("python-docstrings", ["--include-tests", str(ROOT / "python" / "invalid.py")]) == 1
