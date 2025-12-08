from pathlib import Path

from src.cag.validator import RulepackManifest, validate_ruleset


def test_validate_ruleset_manifest() -> None:
    manifest: RulepackManifest = validate_ruleset()

    assert manifest.ruleset_version == "1.0.0"
    assert len(manifest.files) == 1
    rule_file = manifest.files[0]
    assert rule_file.path.as_posix() == "src/cag/rules/rules_example.json"
    assert len(rule_file.sha256) == 64
    # Manifest hash should be 64 hex chars as well
    assert len(manifest.ruleset_sha256) == 64
