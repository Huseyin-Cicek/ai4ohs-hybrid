"""Fuzz-style tests for regex and parser helpers.

These tests generate pseudo-random inputs to ensure the deterministic
validation helpers tolerate unexpected content without raising exceptions.
"""

import random
import re
import string

from src.utils import compliance  # Fixed import path


def _make_rng() -> random.Random:
    """Create a deterministic random generator for repeatability."""
    return random.Random(0xC0FFEE)


def _random_word(rng: random.Random, min_len: int = 1, max_len: int = 12) -> str:
    length = rng.randint(min_len, max_len)
    alphabet = string.ascii_letters
    return "".join(rng.choice(alphabet) for _ in range(length))


def _random_text(rng: random.Random, min_len: int = 0, max_len: int = 256) -> str:
    length = rng.randint(min_len, max_len)
    alphabet = string.ascii_letters + string.digits + string.punctuation + " \n\t"
    return "".join(rng.choice(alphabet) for _ in range(length))


def test_has_keywords_handles_random_inputs() -> None:
    rng = _make_rng()

    for _ in range(100):
        text = _random_text(rng)
        keyword_count = rng.randint(0, 6)
        keywords = [_random_word(rng) for _ in range(keyword_count)]

        missing = compliance.has_keywords(text, keywords)

        assert isinstance(missing, list)
        assert all(kw in keywords for kw in missing)


def test_has_section_header_handles_random_patterns() -> None:
    rng = _make_rng()

    for _ in range(100):
        text = _random_text(rng)
        header = _random_word(rng)
        # Anchored pattern keeps regex compilation safe for fuzz data.
        pattern = rf"^{re.escape(header)}"

        result = compliance.has_section_header(text, pattern)

        assert isinstance(result, bool)


def test_extract_numeric_values_returns_floats() -> None:
    rng = _make_rng()
    pattern = re.compile(r"(\d+(?:\.\d+)?)")

    for _ in range(100):
        # Inject a few numeric fragments to ensure matches occur.
        numeric_bits = " ".join(str(rng.uniform(-1000, 1000)) for _ in range(3))
        text = f"{_random_text(rng)} {numeric_bits} {_random_text(rng)}"

        values = compliance.extract_numeric_values(text, pattern)

        assert isinstance(values, list)
        assert all(isinstance(v, float) for v in values)


def test_validate_confined_space_entry_permit_fuzzed_text() -> None:
    rng = _make_rng()
    context = {"activity": "confined_space"}

    for _ in range(50):
        fragments = [
            _random_text(rng),
            "Atmospheric Testing:",
            str(rng.uniform(0, 100)),
            _random_text(rng),
            "Entry Supervisor:",
            _random_word(rng),
            _random_text(rng),
        ]
        text = " ".join(fragments)

        is_compliant, violations = compliance.validate_confined_space_entry_permit(text, context)

        assert isinstance(is_compliant, bool)
        assert isinstance(violations, list)


def test_validate_ppe_requirements_fuzzed_activity_text() -> None:
    rng = _make_rng()
    activities = ["general", "excavation", "confined_space", "hot_work"]

    for _ in range(50):
        context = {"activity": rng.choice(activities)}
        text = _random_text(rng) + " " + _random_word(rng)

        is_compliant, violations = compliance.validate_ppe_requirements(text, context)

        assert isinstance(is_compliant, bool)
        assert isinstance(violations, list)
        # Every listed violation should relate to the generated keywords.
        assert all(isinstance(v, str) for v in violations)
