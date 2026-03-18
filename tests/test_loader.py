"""Tests for deliberators.loader — YAML loaders and validation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from deliberators.loader import (
    ConfigLoadError,
    ConfigLoader,
    PersonaLoadError,
    PersonaLoader,
    STANDARD_PERSONAS,
)

PERSONAS_DIR = Path("personas")
CONFIG_PATH = Path("config.yaml")


class TestPersonaLoaderLoadAll:
    """Test loading all 15 standard personas."""

    @pytest.fixture(scope="class")
    def all_personas(self):
        return PersonaLoader.load_all(PERSONAS_DIR)

    def test_loads_all_25(self, all_personas):
        assert len(all_personas) == 25

    def test_all_standard_names_present(self, all_personas):
        assert set(all_personas.keys()) == STANDARD_PERSONAS

    @pytest.mark.parametrize("name", sorted(STANDARD_PERSONAS))
    def test_persona_has_valid_role(self, name):
        persona = PersonaLoader.load(PERSONAS_DIR / f"{name}.yaml")
        assert persona.role in ("analyst", "editor"), (
            f"{name}: role must be 'analyst' or 'editor', got '{persona.role}'"
        )

    @pytest.mark.parametrize("name", sorted(STANDARD_PERSONAS))
    def test_persona_has_min_forbidden(self, name):
        persona = PersonaLoader.load(PERSONAS_DIR / f"{name}.yaml")
        assert len(persona.forbidden) >= 2, (
            f"{name}: must have >= 2 forbidden items, got {len(persona.forbidden)}"
        )

    @pytest.mark.parametrize("name", sorted(STANDARD_PERSONAS))
    def test_persona_system_prompt_has_forbidden(self, name):
        persona = PersonaLoader.load(PERSONAS_DIR / f"{name}.yaml")
        assert "FORBIDDEN" in persona.system_prompt, (
            f"{name}: system_prompt must contain 'FORBIDDEN'"
        )

    @pytest.mark.parametrize("name", sorted(STANDARD_PERSONAS))
    def test_persona_system_prompt_has_must_not(self, name):
        persona = PersonaLoader.load(PERSONAS_DIR / f"{name}.yaml")
        assert "MUST NOT" in persona.system_prompt, (
            f"{name}: system_prompt must contain 'MUST NOT'"
        )

    def test_analysts_count(self, all_personas):
        analysts = [p for p in all_personas.values() if p.role == "analyst"]
        assert len(analysts) == 20

    def test_editors_count(self, all_personas):
        editors = [p for p in all_personas.values() if p.role == "editor"]
        assert len(editors) == 5


class TestPersonaLoaderValidation:
    """Test validation rejects invalid personas."""

    def _write_yaml(self, tmpdir: Path, data: dict, name: str = "test.yaml") -> Path:
        path = tmpdir / name
        with open(path, "w") as f:
            yaml.dump(data, f)
        return path

    def test_missing_name_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="missing required fields.*name"):
            PersonaLoader.load(path)

    def test_missing_system_prompt_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "role": "analyst",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="missing required fields.*system_prompt"):
            PersonaLoader.load(path)

    def test_too_few_forbidden_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["only one"],
        })
        with pytest.raises(PersonaLoadError, match="at least 2"):
            PersonaLoader.load(path)

    def test_missing_forbidden_keyword_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "role": "analyst",
            "system_prompt": "You are not allowed to do X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="FORBIDDEN"):
            PersonaLoader.load(path)

    def test_missing_must_not_keyword_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You should not Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="MUST NOT"):
            PersonaLoader.load(path)


class TestPersonaLoaderDiscoverCustom:
    def test_no_custom_in_standard_dir(self):
        custom = PersonaLoader.discover_custom(PERSONAS_DIR)
        assert len(custom) == 0

    def test_discovers_valid_custom(self, tmp_path):
        # Write a valid custom persona
        data = {
            "name": "Custom Thinker",
            "role": "analyst",
            "reasoning_style": "Custom style",
            "forbidden": ["a", "b"],
            "focus": "Custom focus",
            "output_format": {"position": True},
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
        }
        with open(tmp_path / "custom.yaml", "w") as f:
            yaml.dump(data, f)

        custom = PersonaLoader.discover_custom(tmp_path)
        assert len(custom) == 1
        assert custom[0].name == "Custom Thinker"

    def test_rejects_invalid_custom(self, tmp_path):
        # Write an invalid custom persona (missing fields)
        data = {"name": "Bad", "role": "analyst"}
        with open(tmp_path / "bad.yaml", "w") as f:
            yaml.dump(data, f)

        with pytest.raises(PersonaLoadError):
            PersonaLoader.discover_custom(tmp_path)

    def test_ignores_schema_yaml(self, tmp_path):
        # schema.yaml should be skipped
        with open(tmp_path / "schema.yaml", "w") as f:
            yaml.dump({"some": "data"}, f)

        custom = PersonaLoader.discover_custom(tmp_path)
        assert len(custom) == 0


class TestConfigLoader:
    @pytest.fixture(scope="class")
    def config(self):
        return ConfigLoader.load(CONFIG_PATH)

    def test_loads_six_presets(self, config):
        assert len(config.presets) == 6

    def test_preset_names(self, config):
        assert set(config.presets.keys()) == {
            "quick", "balanced", "deep",
            "code_quick", "code_balanced", "code_deep",
        }

    def test_default_preset(self, config):
        assert config.default_preset == "balanced"

    def test_model(self, config):
        assert config.model == "opus"

    def test_quick_preset_analysts(self, config):
        quick = config.presets["quick"]
        assert quick.analysts == ["occam", "holmes", "lupin"]

    def test_quick_preset_has_two_editors(self, config):
        """Regression test: config.yaml has 2 editors for quick (marx + samenvatter).
        This was previously documented as 1 editor — see AC-3."""
        quick = config.presets["quick"]
        assert len(quick.editors) == 2
        assert "marx" in quick.editors
        assert "samenvatter" in quick.editors

    def test_quick_preset_one_round(self, config):
        assert config.presets["quick"].rounds == 1

    def test_balanced_preset(self, config):
        balanced = config.presets["balanced"]
        assert len(balanced.analysts) == 5
        assert len(balanced.editors) == 4  # marx, hegel, arendt, samenvatter
        assert balanced.rounds == 2

    def test_deep_preset(self, config):
        deep = config.presets["deep"]
        assert len(deep.analysts) == 8
        assert len(deep.editors) == 4
        assert deep.rounds == 2

    def test_get_preset_valid(self, config):
        preset = ConfigLoader.get_preset(config, "balanced")
        assert preset.name == "balanced"

    def test_get_preset_invalid_raises(self, config):
        with pytest.raises(ValueError, match="Unknown preset 'nonexistent'"):
            ConfigLoader.get_preset(config, "nonexistent")


class TestConfigLoaderValidation:
    def test_missing_presets_raises(self, tmp_path):
        path = tmp_path / "bad_config.yaml"
        with open(path, "w") as f:
            yaml.dump({"default_preset": "balanced"}, f)

        with pytest.raises(ConfigLoadError, match="missing 'presets'"):
            ConfigLoader.load(path)
