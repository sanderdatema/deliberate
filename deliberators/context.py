"""Code context builder — reads files and formats them for agent prompts."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_FILE_SIZE: int = 1_048_576  # 1 MB

EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".rb": "ruby",
    ".toml": "toml",
    ".xml": "xml",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}


def _detect_language(path: Path) -> str:
    """Detect programming language from file extension."""
    return EXTENSION_MAP.get(path.suffix.lower(), "text")


def _is_binary(path: Path) -> bool:
    """Check if a file is binary by looking for null bytes."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except OSError:
        return True


def build_code_context(paths: list[Path]) -> str | None:
    """Build a code context string from a list of file paths.

    Returns None if no valid files could be read.
    Skips files with path traversal components (..) and files exceeding MAX_FILE_SIZE.
    """
    sections: list[str] = []

    for path in paths:
        if ".." in path.parts:
            logger.warning("Path traversal detected, skipping: %s", path)
            continue

        if not path.exists():
            logger.warning("File not found, skipping: %s", path)
            continue

        if not path.is_file():
            logger.warning("Not a file, skipping: %s", path)
            continue

        if path.stat().st_size > MAX_FILE_SIZE:
            logger.warning("File exceeds %d bytes, skipping: %s", MAX_FILE_SIZE, path)
            continue

        if _is_binary(path):
            logger.warning("Binary file, skipping: %s", path)
            continue

        language = _detect_language(path)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Could not read %s: %s", path, e)
            continue

        sections.append(f"## File: {path} ({language})\n```{language}\n{content}\n```")

    if not sections:
        return None

    return "\n\n".join(sections)
