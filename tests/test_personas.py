"""Validate all persona YAML files against the schema."""

import os
from pathlib import Path

import pytest
import yaml

PERSONAS_DIR = Path(__file__).parent.parent / "personas"
SCHEMA_PATH = PERSONAS_DIR / "schema.yaml"

REQUIRED_FIELDS = [
    "name",
    "role",
    "reasoning_style",
    "forbidden",
    "focus",
    "output_format",
    "system_prompt",
]

ANALYST_OUTPUT_FIELDS = ["position", "confidence", "evidence", "challenges", "questions"]
EDITOR_OUTPUT_FIELDS = ["blind_spots", "synthesis", "question_shifts", "mechanisms"]


def load_schema():
    with open(SCHEMA_PATH) as f:
        return yaml.safe_load(f)


def load_all_personas():
    personas = []
    for path in sorted(PERSONAS_DIR.glob("*.yaml")):
        if path.name == "schema.yaml":
            continue
        with open(path) as f:
            data = yaml.safe_load(f)
        data["_file"] = path.name
        personas.append(data)
    return personas


PERSONAS = load_all_personas()
PERSONA_IDS = [p["_file"] for p in PERSONAS]


@pytest.fixture
def schema():
    return load_schema()


class TestSchemaExists:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), "personas/schema.yaml must exist"

    def test_schema_is_valid_yaml(self):
        schema = load_schema()
        assert isinstance(schema, dict)
        assert "required_fields" in schema


class TestPersonaCount:
    def test_thirteen_personas_exist(self):
        assert len(PERSONAS) == 13, f"Expected 13 personas, found {len(PERSONAS)}"

    def test_ten_analysts(self):
        analysts = [p for p in PERSONAS if p.get("role") == "analyst"]
        assert len(analysts) == 10, f"Expected 10 analysts, found {len(analysts)}"

    def test_three_editors(self):
        editors = [p for p in PERSONAS if p.get("role") == "editor"]
        assert len(editors) == 3, f"Expected 3 editors, found {len(editors)}"

    def test_unique_names(self):
        names = [p["name"] for p in PERSONAS]
        assert len(names) == len(set(names)), f"Duplicate names found: {names}"


@pytest.mark.parametrize("persona", PERSONAS, ids=PERSONA_IDS)
class TestPersonaFormat:
    def test_valid_yaml(self, persona):
        assert isinstance(persona, dict), f"{persona['_file']} is not a valid YAML dict"

    def test_required_fields_present(self, persona):
        for field in REQUIRED_FIELDS:
            assert field in persona, f"{persona['_file']}: missing required field '{field}'"

    def test_role_is_valid(self, persona):
        assert persona["role"] in (
            "analyst",
            "editor",
        ), f"{persona['_file']}: role must be 'analyst' or 'editor', got '{persona['role']}'"

    def test_forbidden_is_nonempty_list(self, persona):
        forbidden = persona.get("forbidden", [])
        assert isinstance(forbidden, list), f"{persona['_file']}: forbidden must be a list"
        assert (
            len(forbidden) >= 2
        ), f"{persona['_file']}: forbidden must have >= 2 items, has {len(forbidden)}"

    def test_system_prompt_contains_constraints(self, persona):
        sp = persona.get("system_prompt", "")
        has_forbidden = "FORBIDDEN" in sp
        has_must_not = "MUST NOT" in sp
        assert (
            has_forbidden or has_must_not
        ), f"{persona['_file']}: system_prompt must contain 'FORBIDDEN' or 'MUST NOT'"

    def test_output_format_keys_match_role(self, persona):
        fmt = persona.get("output_format", {})
        if persona["role"] == "analyst":
            for key in ANALYST_OUTPUT_FIELDS:
                assert (
                    key in fmt
                ), f"{persona['_file']}: analyst output_format missing '{key}'"
        elif persona["role"] == "editor":
            for key in EDITOR_OUTPUT_FIELDS:
                assert (
                    key in fmt
                ), f"{persona['_file']}: editor output_format missing '{key}'"

    def test_reasoning_style_is_nonempty(self, persona):
        style = persona.get("reasoning_style", "")
        assert len(str(style).strip()) > 10, f"{persona['_file']}: reasoning_style too short"

    def test_system_prompt_is_substantial(self, persona):
        sp = persona.get("system_prompt", "")
        word_count = len(sp.split())
        assert (
            word_count >= 50
        ), f"{persona['_file']}: system_prompt too short ({word_count} words, need >= 50)"

    def test_system_prompt_has_structured_output_format(self, persona):
        sp = persona.get("system_prompt", "")
        assert (
            "FORMAT YOUR RESPONSE" in sp
        ), f"{persona['_file']}: system_prompt must contain 'FORMAT YOUR RESPONSE' section"

    def test_analyst_format_has_confidence(self, persona):
        if persona["role"] != "analyst":
            pytest.skip("Editor persona")
        sp = persona.get("system_prompt", "")
        # Socrates is special — no confidence score
        if persona["name"] == "Socrates":
            assert "**Challenges:**" in sp, f"{persona['_file']}: Socrates format must have Challenges"
            assert "**Questions:**" in sp, f"{persona['_file']}: Socrates format must have Questions"
        else:
            assert "**Confidence:**" in sp, f"{persona['_file']}: analyst format must have Confidence"
            assert "**Position:**" in sp, f"{persona['_file']}: analyst format must have Position"
            assert "**Evidence:**" in sp, f"{persona['_file']}: analyst format must have Evidence"

    def test_editor_format_has_blind_spots(self, persona):
        if persona["role"] != "editor":
            pytest.skip("Analyst persona")
        sp = persona.get("system_prompt", "")
        assert "**Blind Spots:**" in sp, f"{persona['_file']}: editor format must have Blind Spots"
        assert "**Synthesis:**" in sp, f"{persona['_file']}: editor format must have Synthesis"
        assert "**Question Shifts:**" in sp, f"{persona['_file']}: editor format must have Question Shifts"
        assert "**Mechanisms:**" in sp, f"{persona['_file']}: editor format must have Mechanisms"
