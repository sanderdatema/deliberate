"""Validate config.yaml and preset definitions."""

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
PERSONAS_DIR = PROJECT_ROOT / "personas"

REQUIRED_PRESET_FIELDS = ["description", "rounds", "analysts", "editors"]


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
    def test_preset_analysts_are_lists(self, preset_name):
        config = load_config()
        preset = config["presets"][preset_name]
        assert isinstance(preset["analysts"], list), f"{preset_name}: analysts must be a list"
        assert len(preset["analysts"]) >= 1, f"{preset_name}: must have at least 1 analyst"

    @pytest.mark.parametrize("preset_name", ["quick", "balanced", "deep"])
    def test_preset_editors_are_lists(self, preset_name):
        config = load_config()
        preset = config["presets"][preset_name]
        assert isinstance(preset["editors"], list), f"{preset_name}: editors must be a list"
        assert len(preset["editors"]) >= 1, f"{preset_name}: must have at least 1 editor"

    @pytest.mark.parametrize("preset_name", ["quick", "balanced", "deep"])
    def test_preset_personas_exist_as_files(self, preset_name):
        config = load_config()
        preset = config["presets"][preset_name]
        available = get_available_personas()
        for persona in preset["analysts"] + preset["editors"]:
            assert persona in available, (
                f"preset '{preset_name}' references '{persona}' but no {persona}.yaml exists"
            )

    def test_quick_is_smaller_than_balanced(self):
        config = load_config()
        quick = config["presets"]["quick"]
        balanced = config["presets"]["balanced"]
        quick_total = len(quick["analysts"]) + len(quick["editors"])
        balanced_total = len(balanced["analysts"]) + len(balanced["editors"])
        assert quick_total < balanced_total, "quick should have fewer personas than balanced"

    def test_deep_is_larger_than_balanced(self):
        config = load_config()
        deep = config["presets"]["deep"]
        balanced = config["presets"]["balanced"]
        deep_total = len(deep["analysts"]) + len(deep["editors"])
        balanced_total = len(balanced["analysts"]) + len(balanced["editors"])
        assert deep_total > balanced_total, "deep should have more personas than balanced"

    def test_quick_has_fewer_rounds(self):
        config = load_config()
        assert config["presets"]["quick"]["rounds"] < config["presets"]["balanced"]["rounds"]
