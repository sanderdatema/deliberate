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
    resolve_config_path,
    resolve_personas_dir,
)

PERSONAS_DIR = Path("personas")
CONFIG_PATH = Path("config.yaml")

# Autodiscover expected persona names from the directory (same logic as load_all)
EXPECTED_PERSONA_NAMES = sorted(
    p.stem for p in PERSONAS_DIR.glob("*.yaml") if p.stem != "schema"
)


class TestPersonaLoaderLoadAll:
    """Test loading all 15 standard personas."""

    @pytest.fixture(scope="class")
    def all_personas(self):
        return PersonaLoader.load_all(PERSONAS_DIR)

    def test_loads_all_25(self, all_personas):
        assert len(all_personas) == 25

    def test_all_persona_names_present(self, all_personas):
        assert set(all_personas.keys()) == set(EXPECTED_PERSONA_NAMES)

    @pytest.mark.parametrize("name", EXPECTED_PERSONA_NAMES)
    def test_persona_has_valid_role(self, name):
        persona = PersonaLoader.load(PERSONAS_DIR / f"{name}.yaml")
        assert persona.role in ("analyst", "editor"), (
            f"{name}: role must be 'analyst' or 'editor', got '{persona.role}'"
        )

    @pytest.mark.parametrize("name", EXPECTED_PERSONA_NAMES)
    def test_persona_has_min_forbidden(self, name):
        persona = PersonaLoader.load(PERSONAS_DIR / f"{name}.yaml")
        assert len(persona.forbidden) >= 2, (
            f"{name}: must have >= 2 forbidden items, got {len(persona.forbidden)}"
        )

    @pytest.mark.parametrize("name", EXPECTED_PERSONA_NAMES)
    def test_persona_system_prompt_has_forbidden(self, name):
        persona = PersonaLoader.load(PERSONAS_DIR / f"{name}.yaml")
        assert "FORBIDDEN" in persona.system_prompt, (
            f"{name}: system_prompt must contain 'FORBIDDEN'"
        )

    @pytest.mark.parametrize("name", EXPECTED_PERSONA_NAMES)
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
            "model": "opus",
            "domains": ["testing"],
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="missing required fields.*name"):
            PersonaLoader.load(path)

    def test_missing_system_prompt_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "model": "opus",
            "domains": ["testing"],
            "role": "analyst",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="missing required fields.*system_prompt"):
            PersonaLoader.load(path)

    def test_missing_model_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "domains": ["testing"],
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="missing required fields.*model"):
            PersonaLoader.load(path)

    def test_invalid_model_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "model": "haiku",
            "domains": ["testing"],
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="model must be one of"):
            PersonaLoader.load(path)

    def test_too_few_forbidden_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "model": "opus",
            "domains": ["testing"],
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["only one"],
        })
        with pytest.raises(PersonaLoadError, match="at least 2"):
            PersonaLoader.load(path)

    def test_missing_forbidden_keyword_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "model": "opus",
            "domains": ["testing"],
            "role": "analyst",
            "system_prompt": "You are not allowed to do X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="FORBIDDEN"):
            PersonaLoader.load(path)

    def test_missing_must_not_keyword_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "model": "opus",
            "domains": ["testing"],
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You should not Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="MUST NOT"):
            PersonaLoader.load(path)

    def test_missing_domains_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "model": "opus",
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="missing required fields.*domains"):
            PersonaLoader.load(path)

    def test_empty_domains_raises(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "model": "opus",
            "domains": [],
            "role": "analyst",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
        })
        with pytest.raises(PersonaLoadError, match="domains must be a non-empty list"):
            PersonaLoader.load(path)

    def test_domains_loaded_as_tuple(self, tmp_path):
        path = self._write_yaml(tmp_path, {
            "name": "Test",
            "model": "opus",
            "domains": ["security", "cryptography"],
            "role": "analyst",
            "reasoning_style": "Test style for validation",
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
            "forbidden": ["a", "b"],
            "focus": "testing",
            "output_format": {},
        })
        persona = PersonaLoader.load(path)
        assert persona.domains == ("security", "cryptography")
        assert isinstance(persona.domains, tuple)


class TestPersonaLoaderAutodiscovery:
    """AC-4 (Phase 11): load_all autodiscovers all YAML files."""

    def test_load_all_discovers_all_yaml(self, tmp_path):
        """load_all finds all .yaml files except schema.yaml."""
        valid_data = {
            "name": "Test Persona",
            "model": "opus",
            "domains": ["testing"],
            "role": "analyst",
            "reasoning_style": "testing",
            "forbidden": ["a", "b"],
            "focus": "testing",
            "output_format": {"position": True},
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
        }
        with open(tmp_path / "alpha.yaml", "w") as f:
            yaml.dump({**valid_data, "name": "Alpha"}, f)
        with open(tmp_path / "beta.yaml", "w") as f:
            yaml.dump({**valid_data, "name": "Beta"}, f)

        result = PersonaLoader.load_all(tmp_path)
        assert set(result.keys()) == {"alpha", "beta"}

    def test_load_all_skips_schema_yaml(self, tmp_path):
        """schema.yaml is excluded from autodiscovery."""
        with open(tmp_path / "schema.yaml", "w") as f:
            yaml.dump({"some": "data"}, f)

        result = PersonaLoader.load_all(tmp_path)
        assert "schema" not in result

    def test_adding_yaml_is_autodiscovered(self, tmp_path):
        """Adding a new .yaml file makes it appear in load_all."""
        valid_data = {
            "name": "New Persona",
            "model": "sonnet",
            "domains": ["testing"],
            "role": "analyst",
            "reasoning_style": "new",
            "forbidden": ["a", "b"],
            "focus": "new",
            "output_format": {},
            "system_prompt": "You are FORBIDDEN from X. You MUST NOT Y.",
        }
        with open(tmp_path / "new-persona.yaml", "w") as f:
            yaml.dump(valid_data, f)

        result = PersonaLoader.load_all(tmp_path)
        assert "new-persona" in result
        assert result["new-persona"].name == "New Persona"

    def test_load_all_rejects_invalid_persona(self, tmp_path):
        """Invalid YAML persona raises PersonaLoadError during load_all."""
        data = {"name": "Bad", "role": "analyst"}
        with open(tmp_path / "bad.yaml", "w") as f:
            yaml.dump(data, f)

        with pytest.raises(PersonaLoadError):
            PersonaLoader.load_all(tmp_path)


class TestImmutableFields:
    """AC-3 (Phase 12): Frozen dataclass fields use tuple, not list."""

    def test_persona_forbidden_is_tuple(self):
        """Persona.forbidden is a tuple after loading from YAML."""
        persona = PersonaLoader.load(PERSONAS_DIR / "socrates.yaml")
        assert isinstance(persona.forbidden, tuple)

    def test_preset_analysts_is_tuple(self):
        """Preset.analysts is a tuple after loading from config."""
        config = ConfigLoader.load(CONFIG_PATH)
        preset = config.presets["quick"]
        assert isinstance(preset.analysts, tuple)

    def test_preset_editors_is_tuple(self):
        """Preset.editors is a tuple after loading from config."""
        config = ConfigLoader.load(CONFIG_PATH)
        preset = config.presets["quick"]
        assert isinstance(preset.editors, tuple)


class TestConfigLoader:
    @pytest.fixture(scope="class")
    def config(self):
        return ConfigLoader.load(CONFIG_PATH)

    def test_loads_three_presets(self, config):
        assert len(config.presets) == 3

    def test_preset_names(self, config):
        assert set(config.presets.keys()) == {"quick", "balanced", "deep"}

    def test_no_code_presets(self, config):
        for name in config.presets:
            assert not name.startswith("code_"), f"code_* preset '{name}' should not exist"

    def test_default_preset(self, config):
        assert config.default_preset == "balanced"

    def test_model(self, config):
        assert config.model == "opus"

    def test_quick_preset_team_size(self, config):
        quick = config.presets["quick"]
        assert quick.team_size == 3
        assert quick.editor_count == 1

    def test_quick_preset_one_round(self, config):
        assert config.presets["quick"].max_rounds == 1
        assert config.presets["quick"].min_rounds == 1

    def test_balanced_preset(self, config):
        balanced = config.presets["balanced"]
        assert balanced.team_size == 5
        assert balanced.editor_count == 2
        assert balanced.max_rounds == 2
        assert balanced.min_rounds == 2

    def test_deep_preset(self, config):
        deep = config.presets["deep"]
        assert deep.team_size == 8
        assert deep.editor_count == 3
        assert deep.max_rounds == 3
        assert deep.min_rounds == 2

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




class TestResolvePathFallback:
    """AC-1..AC-4 (Phase 14): Fallback chain for config and personas paths."""

    def test_resolve_config_cwd_exists(self, tmp_path, monkeypatch):
        """CWD config.yaml takes priority."""
        (tmp_path / "config.yaml").write_text("presets: {}")
        monkeypatch.chdir(tmp_path)
        result = resolve_config_path()
        assert result == Path("config.yaml")

    def test_resolve_config_user_dir(self, tmp_path, monkeypatch):
        """~/.config/deliberators/config.yaml is used when CWD has none."""
        user_dir = tmp_path / "user_config"
        user_dir.mkdir()
        (user_dir / "config.yaml").write_text("presets: {}")
        monkeypatch.setattr("deliberators.loader._USER_CONFIG_DIR", user_dir)
        empty_cwd = tmp_path / "empty_cwd"
        empty_cwd.mkdir()
        monkeypatch.chdir(empty_cwd)
        result = resolve_config_path()
        assert result == user_dir / "config.yaml"

    def test_resolve_config_bundled_fallback(self, tmp_path, monkeypatch):
        """Bundled config is used when no CWD or user config exists."""
        monkeypatch.setattr("deliberators.loader._USER_CONFIG_DIR", tmp_path / "nonexistent")
        monkeypatch.chdir(tmp_path)
        result = resolve_config_path()
        assert "deliberators/data/config.yaml" in str(result)
        assert result.exists()

    def test_resolve_config_explicit_override(self):
        """Explicit non-default path is returned directly."""
        custom = Path("/custom/config.yaml")
        result = resolve_config_path(custom)
        assert result == custom

    def test_resolve_personas_cwd_exists(self, tmp_path, monkeypatch):
        """CWD personas/ takes priority."""
        (tmp_path / "personas").mkdir()
        monkeypatch.chdir(tmp_path)
        result = resolve_personas_dir()
        assert result == Path("personas")

    def test_resolve_personas_bundled_fallback(self, tmp_path, monkeypatch):
        """Bundled personas dir is used when no CWD or user dir exists."""
        monkeypatch.setattr("deliberators.loader._USER_CONFIG_DIR", tmp_path / "nonexistent")
        monkeypatch.chdir(tmp_path)
        result = resolve_personas_dir()
        assert "deliberators/data/personas" in str(result)
        assert result.is_dir()
