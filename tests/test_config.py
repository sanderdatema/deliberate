"""Validate config.yaml and preset definitions."""

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
PERSONAS_DIR = PROJECT_ROOT / "personas"

REQUIRED_PRESET_FIELDS = ["description", "max_rounds", "team_size", "editor_count"]


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_available_personas():
    return {
        p.stem for p in PERSONAS_DIR.glob("*.yaml") if p.name != "schema.yaml"
    }


class TestConfigExists:
    def test_config_file_exists(self):
        assert CONFIG_PATH.exists(), "config.yaml must exist in project root"

    def test_config_is_valid_yaml(self):
        config = load_config()
        assert isinstance(config, dict)


class TestConfigStructure:
    def test_has_default_preset(self):
        config = load_config()
        assert "default_preset" in config, "config must have default_preset"

    def test_has_rounds(self):
        config = load_config()
        assert "rounds" in config, "config must have rounds"
        assert isinstance(config["rounds"], int)

    def test_has_model(self):
        config = load_config()
        assert "model" in config, "config must have model"

    def test_has_presets(self):
        config = load_config()
        assert "presets" in config, "config must have presets"
        assert isinstance(config["presets"], dict)


class TestPresets:
    def test_three_presets_exist(self):
        config = load_config()
        presets = config["presets"]
        assert "quick" in presets, "missing 'quick' preset"
        assert "balanced" in presets, "missing 'balanced' preset"
        assert "deep" in presets, "missing 'deep' preset"
        assert len(presets) == 3, f"Expected 3 presets, got {len(presets)}"

    def test_no_code_presets(self):
        config = load_config()
        presets = config["presets"]
        for name in presets:
            assert not name.startswith("code_"), f"code_* preset '{name}' should not exist"

    def test_default_preset_is_valid(self):
        config = load_config()
        assert config["default_preset"] in config["presets"], (
            f"default_preset '{config['default_preset']}' not in presets"
        )

    @pytest.mark.parametrize("preset_name", ["quick", "balanced", "deep"])
    def test_preset_has_required_fields(self, preset_name):
        config = load_config()
        preset = config["presets"][preset_name]
        for field in REQUIRED_PRESET_FIELDS:
            assert field in preset, f"preset '{preset_name}' missing field '{field}'"

    @pytest.mark.parametrize("preset_name", ["quick", "balanced", "deep"])
    def test_preset_team_size_positive(self, preset_name):
        config = load_config()
        preset = config["presets"][preset_name]
        assert preset["team_size"] >= 1, f"{preset_name}: team_size must be >= 1"

    @pytest.mark.parametrize("preset_name", ["quick", "balanced", "deep"])
    def test_preset_editor_count_positive(self, preset_name):
        config = load_config()
        preset = config["presets"][preset_name]
        assert preset["editor_count"] >= 1, f"{preset_name}: editor_count must be >= 1"

    def test_quick_is_smaller_than_balanced(self):
        config = load_config()
        quick = config["presets"]["quick"]
        balanced = config["presets"]["balanced"]
        assert quick["team_size"] < balanced["team_size"], (
            "quick should have smaller team_size than balanced"
        )

    def test_deep_is_larger_than_balanced(self):
        config = load_config()
        deep = config["presets"]["deep"]
        balanced = config["presets"]["balanced"]
        assert deep["team_size"] > balanced["team_size"], (
            "deep should have larger team_size than balanced"
        )

    def test_quick_has_fewer_rounds(self):
        config = load_config()
        assert config["presets"]["quick"]["max_rounds"] < config["presets"]["balanced"]["max_rounds"]

    def test_all_presets_have_summarizer(self):
        config = load_config()
        for name, preset in config["presets"].items():
            assert "summarizer" in preset, f"preset '{name}' missing summarizer"
            assert preset["summarizer"] == "samenvatter"
