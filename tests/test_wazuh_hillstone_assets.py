from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DECODERS = ROOT / "deploy" / "wazuh" / "hillstone-stoneos-decoders.xml"
RULES = ROOT / "deploy" / "wazuh" / "hillstone-stoneos-rules.xml"


def _fragments(path: Path) -> ET.Element:
    return ET.fromstring(f"<root>{path.read_text(encoding='utf-8')}</root>")


def test_hillstone_threat_decoder_exposes_only_stable_fields() -> None:
    root = _fragments(DECODERS)
    threat = next(
        decoder
        for decoder in root.findall("decoder")
        if decoder.attrib["name"] == "hillstone-stoneos-threat"
    )
    order = (threat.findtext("order") or "").split(",")

    assert order == [
        "id",
        "hillstone.log_type",
        "hillstone.module",
        "hillstone.threat_name",
        "hillstone.threat_type",
        "hillstone.threat_subtype",
        "hillstone.app_protocol",
        "hillstone.action",
        "hillstone.defender",
        "hillstone.error_id",
        "hillstone.profile",
        "hillstone.threat_severity",
        "hillstone.policy_id",
        "hillstone.aggregation_count",
    ]
    assert not any("src" in field or "dst" in field or "user" in field for field in order)


def test_hillstone_threat_rules_are_bounded_to_observed_log_only_protocol_errors() -> None:
    root = _fragments(RULES)
    rules = {rule.attrib["id"]: rule for rule in root.findall(".//rule")}

    assert len(rules) == len(root.findall(".//rule"))
    assert rules["100203"].attrib["level"] == "7"
    assert rules["100203"].findtext("field") == "^Threat$"
    assert rules["100204"].attrib["level"] == "5"
    assert [field.attrib["name"] for field in rules["100204"].findall("field")] == [
        "hillstone.threat_subtype",
        "hillstone.action",
    ]
    assert [field.text for field in rules["100204"].findall("field")] == [
        "^Protocol Exception$",
        "^log-only$",
    ]
