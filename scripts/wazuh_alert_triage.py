#!/usr/bin/env python3
"""Summarize Wazuh alerts (JSONL, the format of alerts.json) into a daily triage report.

Usage:
    python wazuh_alert_triage.py alerts.json [--min-level 7] [--format md|csv]

Each line of the input file is expected to be one JSON alert object, matching
the structure Wazuh writes to /var/ossec/logs/alerts/alerts.json, e.g.:

    {"timestamp": "...", "rule": {"level": 10, "description": "...", "id": "...",
     "mitre": {"id": ["T1110"], "tactic": ["Credential Access"]}},
     "agent": {"name": "web01", "id": "003"}}
"""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Alert:
    timestamp: str
    level: int
    description: str
    rule_id: str
    agent_name: str
    mitre_ids: List[str] = field(default_factory=list)
    mitre_tactics: List[str] = field(default_factory=list)


def parse_alerts_file(path: str) -> List[Alert]:
    alerts: List[Alert] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            rule = raw.get("rule", {}) or {}
            agent = raw.get("agent", {}) or {}
            mitre = rule.get("mitre", {}) or {}

            alerts.append(
                Alert(
                    timestamp=raw.get("timestamp", ""),
                    level=int(rule.get("level", 0)),
                    description=rule.get("description", "Unknown rule"),
                    rule_id=str(rule.get("id", "")),
                    agent_name=agent.get("name", "unknown-agent"),
                    mitre_ids=list(mitre.get("id", []) or []),
                    mitre_tactics=list(mitre.get("tactic", []) or []),
                )
            )
    return alerts


def filter_by_level(alerts: List[Alert], min_level: int) -> List[Alert]:
    return [a for a in alerts if a.level >= min_level]


def group_by_agent(alerts: List[Alert]) -> Dict[str, List[Alert]]:
    grouped: Dict[str, List[Alert]] = defaultdict(list)
    for a in alerts:
        grouped[a.agent_name].append(a)
    return dict(grouped)


def group_by_rule(alerts: List[Alert]) -> Dict[str, List[Alert]]:
    grouped: Dict[str, List[Alert]] = defaultdict(list)
    for a in alerts:
        key = f"{a.rule_id}: {a.description}"
        grouped[key].append(a)
    return dict(grouped)


def top_mitre_techniques(alerts: List[Alert], top_n: int = 10) -> List[tuple]:
    counter: Counter = Counter()
    for a in alerts:
        for mid in a.mitre_ids:
            counter[mid] += 1
    return counter.most_common(top_n)


def to_markdown(alerts: List[Alert], min_level: int) -> str:
    if not alerts:
        return f"# Wazuh Daily Triage Report\n\nNo alerts at or above level {min_level}.\n"

    lines = ["# Wazuh Daily Triage Report", ""]
    lines.append(f"**Total alerts (level >= {min_level}):** {len(alerts)}")

    by_agent = group_by_agent(alerts)
    lines.append(f"**Affected agents:** {len(by_agent)}")
    lines.append("")

    lines.append("## Top Rules Triggered")
    by_rule = group_by_rule(alerts)
    ranked_rules = sorted(by_rule.items(), key=lambda kv: -len(kv[1]))
    lines.append("| Rule | Count | Max Level |")
    lines.append("|---|---|---|")
    for rule_key, rule_alerts in ranked_rules[:15]:
        max_level = max(a.level for a in rule_alerts)
        lines.append(f"| {rule_key} | {len(rule_alerts)} | {max_level} |")
    lines.append("")

    lines.append("## Alerts by Agent")
    lines.append("| Agent | Alert Count | Highest Severity |")
    lines.append("|---|---|---|")
    for agent, agent_alerts in sorted(by_agent.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"| {agent} | {len(agent_alerts)} | {max(a.level for a in agent_alerts)} |")
    lines.append("")

    techniques = top_mitre_techniques(alerts)
    if techniques:
        lines.append("## Top MITRE ATT&CK Techniques")
        lines.append("| Technique ID | Occurrences |")
        lines.append("|---|---|")
        for tid, count in techniques:
            lines.append(f"| {tid} | {count} |")

    return "\n".join(lines) + "\n"


def to_csv(alerts: List[Alert], out) -> None:
    writer = csv.writer(out)
    writer.writerow(["timestamp", "level", "agent", "rule_id", "description", "mitre_ids"])
    for a in alerts:
        writer.writerow([a.timestamp, a.level, a.agent_name, a.rule_id, a.description, ";".join(a.mitre_ids)])


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Wazuh alerts into a daily triage report.")
    parser.add_argument("alerts_file", help="Path to a Wazuh alerts.json (JSONL) file")
    parser.add_argument("--min-level", type=int, default=7, help="Minimum rule level to include")
    parser.add_argument("--format", choices=["md", "csv"], default="md")
    args = parser.parse_args()

    alerts = parse_alerts_file(args.alerts_file)
    filtered = filter_by_level(alerts, args.min_level)

    if args.format == "md":
        sys.stdout.write(to_markdown(filtered, args.min_level))
    else:
        to_csv(filtered, sys.stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
