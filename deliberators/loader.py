"""YAML loaders for persona and config files."""

from __future__ import annotations

from pathlib import Path

import yaml

from deliberators.models import Config, Persona, Preset

REQUIRED_PERSONA_FIELDS = {"name", "role", "system_prompt", "forbidden"}
_BUNDLED_DATA_DIR = Path(__file__).parent / "data"
_USER_CONFIG_DIR = Path.home() / ".config" / "deliberators"


def resolve_config_path(explicit: Path | None = None) -> Path:
    """Resolve config.yaml path: explicit → CWD → user config → bundled."""
    if explicit is not None and explicit != Path("config.yaml"):
        return explicit
    cwd_path = Path("config.yaml")
    if cwd_path.exists():
        return cwd_path
    user_path = _USER_CONFIG_DIR / "config.yaml"
    if user_path.exists():
        return user_path
    return _BUNDLED_DATA_DIR / "config.yaml"


def resolve_personas_dir(explicit: Path | None = None) -> Path:
    """Resolve personas directory: explicit → CWD → user config → bundled."""
    if explicit is not None and explicit != Path("personas"):
        return explicit
    cwd_path = Path("personas")
    if cwd_path.is_dir():
        return cwd_path
    user_path = _USER_CONFIG_DIR / "personas"
    if user_path.is_dir():
        return user_path
    return _BUNDLED_DATA_DIR / "personas"
MIN_FORBIDDEN_ITEMS = 2


class PersonaLoadError(Exception):
    """Raised when a persona file cannot be loaded or validated."""


class ConfigLoadError(Exception):
    """Raised when config.yaml cannot be loaded."""


class PersonaLoader:
    """Loads and validates persona YAML files."""

    @staticmethod
    def load(path: Path) -> Persona:
        """Load a single persona from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        missing = REQUIRED_PERSONA_FIELDS - set(data.keys())
        if missing:
            raise PersonaLoadError(
                f"{path.name}: missing required fields: {', '.join(sorted(missing))}"
            )

        forbidden = data.get("forbidden", [])
        if len(forbidden) < MIN_FORBIDDEN_ITEMS:
            raise PersonaLoadError(
                f"{path.name}: forbidden must have at least {MIN_FORBIDDEN_ITEMS} items, "
                f"got {len(forbidden)}"
            )

        system_prompt = data.get("system_prompt", "")
        for keyword in ("FORBIDDEN", "MUST NOT"):
            if keyword not in system_prompt:
                raise PersonaLoadError(
                    f"{path.name}: system_prompt must contain '{keyword}'"
                )

        return Persona(
            name=data["name"],
            role=data["role"],
            reasoning_style=data.get("reasoning_style", ""),
            forbidden=tuple(forbidden),
            focus=data.get("focus", ""),
            output_format=data.get("output_format", {}),
            system_prompt=system_prompt,
        )

    @staticmethod
    def load_all(personas_dir: Path) -> dict[str, Persona]:
        """Load all persona YAML files from a directory (autodiscovery)."""
        personas: dict[str, Persona] = {}
        for path in sorted(personas_dir.glob("*.yaml")):
            if path.stem == "schema":
                continue
            personas[path.stem] = PersonaLoader.load(path)
        return personas


class ConfigLoader:
    """Loads and validates config.yaml."""

    @staticmethod
    def load(path: Path) -> Config:
        """Load config.yaml and return a Config dataclass."""
        with open(path) as f:
            data = yaml.safe_load(f)

        if "presets" not in data:
            raise ConfigLoadError("config.yaml: missing 'presets' section")

        presets: dict[str, Preset] = {}
        for name, preset_data in data["presets"].items():
            presets[name] = Preset(
                name=name,
                description=preset_data.get("description", ""),
                rounds=preset_data.get("rounds", data.get("rounds", 2)),
                analysts=tuple(preset_data.get("analysts", [])),
                editors=tuple(preset_data.get("editors", [])),
                summarizer=preset_data.get("summarizer"),
            )

        return Config(
            default_preset=data.get("default_preset", "balanced"),
            rounds=data.get("rounds", 2),
            model=data.get("model", "opus"),
            presets=presets,
        )

    @staticmethod
    def get_preset(config: Config, name: str) -> Preset:
        """Get a preset by name, raising ValueError if not found."""
        if name not in config.presets:
            raise ValueError(
                f"Unknown preset '{name}'. Available: {', '.join(config.presets.keys())}"
            )
        return config.presets[name]

    @staticmethod
    def validate_preset_personas(config: Config, personas: dict[str, Persona]) -> None:
        """Validate that all persona keys referenced in presets exist in the loaded personas.

        Raises ValueError with a clear message listing which preset references
        which missing persona(s).
        """
        missing: list[str] = []
        for preset_name, preset in config.presets.items():
            for name in preset.analysts + preset.editors:
                if name not in personas:
                    missing.append(f"preset '{preset_name}' references unknown persona '{name}'")
        if missing:
            raise ValueError(
                f"Preset persona validation failed:\n  - " + "\n  - ".join(missing)
            )
