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
    assert main(hook, [str(ROOT / language / invalid)]) == 1
    output = capsys.readouterr().err
    assert output


def test_pre_commit_files_and_exclude_select_source_files_without_args(tmp_path):
    root = tmp_path / "repo"
    source = root / "src" / "app.py"
    generated = root / "api-clients" / "openlink_token_service_client" / "client.py"
    tests = root / "tests" / "test_app.py"
    for path in (source, generated, tests):
        path.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("def process(value):\n    return value\n")
    generated.write_text("class Client:\n    pass\n")
    tests.write_text("class TestApp:\n    pass\n")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    config = root / ".pre-commit-config.yaml"
    config.write_text(f"""repos:\n  - repo: local\n    hooks:\n      - id: python-docstrings\n        name: Python docs\n        entry: {sys.executable} -c \"import sys; from docs_hooks.cli import main; sys.exit(main('python-docstrings', sys.argv[1:]))\"\n        language: system\n        types: [python]\n        files: \".*[.]py$\"\n        exclude: ^(api-clients/(openlink_token_service_client|person_matching_service_client))/|^tests/\n""")
    def run_precommit(path):
        return subprocess.run([sys.executable, "-m", "pre_commit", "run", "--config", str(config), "python-docstrings", "--files", path.relative_to(root).as_posix()], cwd=root, text=True, capture_output=True)

    assert run_precommit(generated).returncode == 0
    assert run_precommit(tests).returncode == 0
    result = run_precommit(source)
    assert result.returncode == 1, result.stdout + result.stderr



def test_python_only_hook_module_has_no_parser_dependencies():
    code = "import docs_hooks.cli as cli; cli.python_docstrings(); import sys; assert not any(n.startswith('tree_sitter') for n in sys.modules)"
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)


