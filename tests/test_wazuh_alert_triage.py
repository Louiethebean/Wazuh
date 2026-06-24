import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from wazuh_alert_triage import (  # noqa: E402
    filter_by_level,
    group_by_agent,
    group_by_rule,
    parse_alerts_file,
    to_markdown,
    top_mitre_techniques,
)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_alerts.json")


def test_parse_alerts_file_reads_all_lines():
    alerts = parse_alerts_file(FIXTURE)
    assert len(alerts) == 5


def test_filter_by_level():
    alerts = parse_alerts_file(FIXTURE)
    filtered = filter_by_level(alerts, min_level=7)
    assert len(filtered) == 4
    assert all(a.level >= 7 for a in filtered)


def test_group_by_agent():
    alerts = parse_alerts_file(FIXTURE)
    grouped = group_by_agent(alerts)
    assert set(grouped.keys()) == {"web01", "db01"}
    assert len(grouped["web01"]) == 2
    assert len(grouped["db01"]) == 3


def test_group_by_rule_collapses_repeated_rule():
    alerts = parse_alerts_file(FIXTURE)
    grouped = group_by_rule(alerts)
    auth_failures = grouped["5710: Multiple authentication failures"]
    assert len(auth_failures) == 2


def test_top_mitre_techniques_counts_correctly():
    alerts = parse_alerts_file(FIXTURE)
    top = top_mitre_techniques(alerts)
    top_dict = dict(top)
    assert top_dict["T1110"] == 3


def test_to_markdown_includes_agent_table():
    alerts = parse_alerts_file(FIXTURE)
    filtered = filter_by_level(alerts, min_level=7)
    md = to_markdown(filtered, min_level=7)
    assert "web01" in md
    assert "db01" in md
    assert "Top MITRE ATT&CK Techniques" in md


def test_to_markdown_no_alerts():
    md = to_markdown([], min_level=10)
    assert "No alerts" in md
