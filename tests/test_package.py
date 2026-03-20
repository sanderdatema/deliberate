"""Tests for package data bundling and get_data_path()."""

from pathlib import Path

from deliberators import get_data_path
from deliberators.loader import PersonaLoader


class TestGetDataPath:
    """AC-3: get_data_path() returns valid bundled data directory."""

    def test_returns_path(self):
        result = get_data_path()
        assert isinstance(result, Path)

    def test_config_yaml_exists(self):
        p = get_data_path()
        assert (p / "config.yaml").exists()

    def test_personas_dir_exists(self):
        p = get_data_path()
        assert (p / "personas").is_dir()

    def test_bundled_persona_count_matches_root(self):
        """Bundled personas should match root-level personas."""
        root_personas = sorted(
            p.stem for p in Path("personas").glob("*.yaml") if p.stem != "schema"
        )
        bundled_personas = sorted(
            p.stem
            for p in (get_data_path() / "personas").glob("*.yaml")
            if p.stem != "schema"
        )
        assert root_personas == bundled_personas

    def test_bundled_personas_are_loadable(self):
        """All bundled personas pass validation."""
        bundled_dir = get_data_path() / "personas"
        personas = PersonaLoader.load_all(bundled_dir)
        assert len(personas) == 25
