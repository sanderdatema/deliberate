"""Tests for deliberators.context — CodeContextBuilder."""

from pathlib import Path

import pytest

from deliberators.context import CodeContextBuilder, _detect_language, _is_binary


class TestDetectLanguage:
    def test_python(self):
        assert _detect_language(Path("foo.py")) == "python"

    def test_typescript(self):
        assert _detect_language(Path("bar.ts")) == "typescript"

    def test_yaml(self):
        assert _detect_language(Path("config.yaml")) == "yaml"

    def test_yml(self):
        assert _detect_language(Path("config.yml")) == "yaml"

    def test_unknown_extension(self):
        assert _detect_language(Path("file.xyz")) == "text"

    def test_go(self):
        assert _detect_language(Path("main.go")) == "go"

    def test_rust(self):
        assert _detect_language(Path("lib.rs")) == "rust"


class TestIsBinary:
    def test_text_file(self, tmp_path):
        f = tmp_path / "text.py"
        f.write_text("print('hello')")
        assert _is_binary(f) is False

    def test_binary_file(self, tmp_path):
        f = tmp_path / "binary.bin"
        f.write_bytes(b"hello\x00world")
        assert _is_binary(f) is True

    def test_nonexistent_file(self, tmp_path):
        f = tmp_path / "nope.txt"
        assert _is_binary(f) is True


class TestCodeContextBuilder:
    def test_single_python_file(self, tmp_path):
        f = tmp_path / "main.py"
        f.write_text("def hello():\n    pass\n")

        result = CodeContextBuilder.build([f])
        assert result is not None
        assert "## File:" in result
        assert "(python)" in result
        assert "```python" in result
        assert "def hello():" in result

    def test_multiple_files(self, tmp_path):
        py = tmp_path / "a.py"
        py.write_text("x = 1")
        ts = tmp_path / "b.ts"
        ts.write_text("const y = 2;")

        result = CodeContextBuilder.build([py, ts])
        assert result is not None
        assert "(python)" in result
        assert "(typescript)" in result
        assert "x = 1" in result
        assert "const y = 2;" in result

    def test_nonexistent_file_skipped(self, tmp_path):
        good = tmp_path / "ok.py"
        good.write_text("pass")
        bad = tmp_path / "nope.py"

        result = CodeContextBuilder.build([bad, good])
        assert result is not None
        assert "pass" in result
        assert "nope" not in result

    def test_all_nonexistent_returns_none(self, tmp_path):
        result = CodeContextBuilder.build([tmp_path / "a.py", tmp_path / "b.py"])
        assert result is None

    def test_empty_list_returns_none(self):
        result = CodeContextBuilder.build([])
        assert result is None

    def test_binary_file_skipped(self, tmp_path):
        txt = tmp_path / "ok.py"
        txt.write_text("good")
        binary = tmp_path / "bad.bin"
        binary.write_bytes(b"\x00\x01\x02")

        result = CodeContextBuilder.build([binary, txt])
        assert result is not None
        assert "good" in result
        assert "bad.bin" not in result

    def test_directory_skipped(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        f = tmp_path / "ok.py"
        f.write_text("fine")

        result = CodeContextBuilder.build([subdir, f])
        assert result is not None
        assert "fine" in result
