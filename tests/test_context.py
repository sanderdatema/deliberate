"""Tests for deliberators.context — build_code_context and helpers."""

from pathlib import Path

import pytest

from deliberators.context import MAX_FILE_SIZE, build_code_context, _detect_language, _is_binary


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


class TestBuildCodeContext:
    def test_single_python_file(self, tmp_path):
        f = tmp_path / "main.py"
        f.write_text("def hello():\n    pass\n")

        result = build_code_context([f])
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

        result = build_code_context([py, ts])
        assert result is not None
        assert "(python)" in result
        assert "(typescript)" in result
        assert "x = 1" in result
        assert "const y = 2;" in result

    def test_nonexistent_file_skipped(self, tmp_path):
        good = tmp_path / "ok.py"
        good.write_text("pass")
        bad = tmp_path / "nope.py"

        result = build_code_context([bad, good])
        assert result is not None
        assert "pass" in result
        assert "nope" not in result

    def test_all_nonexistent_returns_none(self, tmp_path):
        result = build_code_context([tmp_path / "a.py", tmp_path / "b.py"])
        assert result is None

    def test_empty_list_returns_none(self):
        result = build_code_context([])
        assert result is None

    def test_binary_file_skipped(self, tmp_path):
        txt = tmp_path / "ok.py"
        txt.write_text("good")
        binary = tmp_path / "bad.bin"
        binary.write_bytes(b"\x00\x01\x02")

        result = build_code_context([binary, txt])
        assert result is not None
        assert "good" in result
        assert "bad.bin" not in result

    def test_directory_skipped(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        f = tmp_path / "ok.py"
        f.write_text("fine")

        result = build_code_context([subdir, f])
        assert result is not None
        assert "fine" in result


class TestPathSanitization:
    """AC-1: Path traversal components (..) are rejected."""

    def test_dotdot_in_path_skipped(self, tmp_path):
        """A path containing '..' is skipped even if the file exists."""
        # Create a valid file via a clean path
        subdir = tmp_path / "sub"
        subdir.mkdir()
        f = subdir / "ok.py"
        f.write_text("clean")

        # Reference it via a path with ".."
        traversal_path = tmp_path / "sub" / ".." / "sub" / "ok.py"

        result = build_code_context([traversal_path])
        assert result is None  # skipped — no valid files

    def test_dotdot_skipped_but_clean_files_kept(self, tmp_path):
        """Traversal path is skipped while clean paths are kept."""
        good = tmp_path / "ok.py"
        good.write_text("clean code")

        bad = tmp_path / ".." / "etc" / "passwd"

        result = build_code_context([bad, good])
        assert result is not None
        assert "clean code" in result
        assert "passwd" not in result


class TestSymlinkDetection:
    """Symlinks are rejected to prevent reading unintended files."""

    def test_symlink_skipped(self, tmp_path):
        """A symlink to a file is skipped."""
        real = tmp_path / "real.py"
        real.write_text("real content")
        link = tmp_path / "link.py"
        link.symlink_to(real)

        result = build_code_context([link])
        assert result is None

    def test_symlink_skipped_but_real_files_kept(self, tmp_path):
        """Symlinks are skipped while real files are kept."""
        real = tmp_path / "real.py"
        real.write_text("good content")
        link = tmp_path / "link.py"
        link.symlink_to(real)

        result = build_code_context([link, real])
        assert result is not None
        assert "good content" in result
        # Only one file section (the real file)
        assert result.count("## File:") == 1

    def test_symlink_to_outside_skipped(self, tmp_path):
        """A symlink pointing outside the directory is skipped."""
        import os
        target = tmp_path / "outside" / "secret.txt"
        target.parent.mkdir()
        target.write_text("secret data")
        link = tmp_path / "project" / "innocent.py"
        link.parent.mkdir()
        link.symlink_to(target)

        result = build_code_context([link])
        assert result is None


class TestFilesizeLimit:
    """AC-2: Files exceeding MAX_FILE_SIZE are skipped."""

    def test_oversized_file_skipped(self, tmp_path):
        """A file larger than MAX_FILE_SIZE is excluded."""
        big = tmp_path / "huge.py"
        big.write_text("x" * (MAX_FILE_SIZE + 1))

        result = build_code_context([big])
        assert result is None

    def test_oversized_skipped_but_small_kept(self, tmp_path):
        """Oversized file is skipped, normal file is kept."""
        big = tmp_path / "huge.py"
        big.write_text("x" * (MAX_FILE_SIZE + 1))
        small = tmp_path / "ok.py"
        small.write_text("small code")

        result = build_code_context([big, small])
        assert result is not None
        assert "small code" in result
        assert "huge.py" not in result

    def test_file_at_exact_limit_is_kept(self, tmp_path):
        """A file exactly at MAX_FILE_SIZE is NOT skipped."""
        exact = tmp_path / "exact.py"
        exact.write_text("x" * MAX_FILE_SIZE)

        result = build_code_context([exact])
        assert result is not None
        assert "exact.py" in result
