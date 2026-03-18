"""YAML loaders for persona and config files."""

from __future__ import annotations

from pathlib import Path

import yaml

from deliberators.models import Config, Persona, Preset

STANDARD_PERSONAS = frozenset({
    "socrates", "occam", "da-vinci", "holmes", "lupin",
    "templar", "tubman", "weil", "marple", "noether",
    "ibn-khaldun",
    "marx", "hegel", "arendt", "samenvatter",
    "linus", "kent-beck", "fowler", "schneier", "jobs",
    "don-norman", "jony-ive", "christensen", "hopper",
    "code-synthesizer",
})

REQUIRED_PERSONA_FIELDS = {"name", "role", "system_prompt", "forbidden"}
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
            forbidden=forbidden,
            focus=data.get("focus", ""),
            output_format=data.get("output_format", {}),
            system_prompt=system_prompt,
        )

    @staticmethod
    def load_all(personas_dir: Path) -> dict[str, Persona]:
        """Load all standard personas from a directory."""
        personas: dict[str, Persona] = {}
        for name in STANDARD_PERSONAS:
            path = personas_dir / f"{name}.yaml"
            if path.exists():
                personas[name] = PersonaLoader.load(path)
        return personas

    @staticmethod
    def discover_custom(personas_dir: Path) -> list[Persona]:
        """Find and load non-standard persona files."""
        custom: list[Persona] = []
        for path in sorted(personas_dir.glob("*.yaml")):
            stem = path.stem
            if stem in STANDARD_PERSONAS or stem == "schema":
                continue
            custom.append(PersonaLoader.load(path))
        return custom


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
                analysts=preset_data.get("analysts", []),
                editors=preset_data.get("editors", []),
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
