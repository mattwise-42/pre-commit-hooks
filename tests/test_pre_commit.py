import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def run(*args, check=True):
    result = subprocess.run([sys.executable, "-m", "pre_commit", *args[1:]], cwd=ROOT, text=True, capture_output=True, check=check)
    print(result.stdout, end="")
    print(result.stderr, end="")
    return result


def test_pre_commit_consumer_smoke_success():
    for hook, paths in (
        ("python-docstrings", ["tests/fixtures/python/valid.py"]),
        ("java-javadocs", ["tests/fixtures/java/Valid.java"]),
        ("csharp-xml-docs", ["tests/fixtures/csharp/Valid.cs"]),
    ):
        result = run("pre-commit", "try-repo", ".", hook, "--files", *paths, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
