#!/usr/bin/env python3
"""Score outstanding RHEL security errata against the patch SLA.

Reads the folder written by playbooks/patch_report.yml:

  <report dir>/<host>/updateinfo-list.txt   dnf -q updateinfo list --security
  <report dir>/<host>/updateinfo-info.txt   dnf -q updateinfo info --security
  <report dir>/<host>/host.json             {"host": ..., "rings": [...]}

and writes compliance.md and compliance.json in the report folder.

The SLA clock runs from the advisory issue date. Default SLA (days):
Critical 7, Important 30, Moderate 31, Low 31 (next monthly window).
An advisory that fixes a CVE listed in the --kev file gets 2 days.

Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys

__version__ = "1.0.0"

DEFAULT_SLA = {"Critical": 7, "Important": 30, "Moderate": 31, "Low": 31}
KEV_SLA_DAYS = 2
SEVERITIES = ("Critical", "Important", "Moderate", "Low")

LIST_RE = re.compile(r"^(?P<id>RH[SBE]A-\d{4}:\d+)\s+(?P<sev>[A-Za-z]+)/Sec\.\s+(?P<pkg>\S+)")
FIELD_RE = re.compile(r"^\s*(?P<key>[A-Za-z][A-Za-z ]*?)\s*:\s?(?P<value>.*)$")
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def parse_list(text: str) -> dict[str, dict]:
    """Advisory id -> {severity, packages} from 'dnf updateinfo list --security'."""
    advisories: dict[str, dict] = {}
    for line in text.splitlines():
        match = LIST_RE.match(line.strip())
        if not match:
            continue
        entry = advisories.setdefault(match["id"], {"severity": match["sev"].capitalize(), "packages": []})
        if match["pkg"] not in entry["packages"]:
            entry["packages"].append(match["pkg"])
    return advisories


def parse_info(text: str) -> dict[str, dict]:
    """Advisory id -> {title, severity, issued, updated, cves} from 'dnf updateinfo info'."""
    advisories: dict[str, dict] = {}
    current: dict | None = None
    last_key = ""
    lines = text.splitlines()
    pending_title = ""
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("====="):
            # The title sits between two separator lines.
            if index + 2 < len(lines) and lines[index + 2].strip().startswith("====="):
                pending_title = lines[index + 1].strip()
            continue
        match = FIELD_RE.match(line)
        if match and match["key"].strip():
            key, value = match["key"].strip(), match["value"].strip()
            last_key = key
            if key == "Update ID":
                current = {"title": pending_title, "severity": "", "issued": "", "updated": "", "cves": []}
                advisories[value] = current
                pending_title = ""
                continue
            if current is None:
                continue
            if key == "Severity":
                current["severity"] = value.capitalize()
            elif key in ("Issued", "Updated"):
                date = DATE_RE.search(value)
                if date:
                    current[key.lower()] = date.group(0)
            elif key == "CVEs":
                current["cves"].extend(CVE_RE.findall(value))
        elif current is not None and last_key == "CVEs":
            # Continuation lines of the CVE list start with ":".
            current["cves"].extend(CVE_RE.findall(stripped))
    for entry in advisories.values():
        entry["cves"] = sorted(set(entry["cves"]))
    return advisories


def score_host(host: str, rings: list, list_text: str, info_text: str, sla: dict, kev: set,
               today: _dt.date) -> dict:
    outstanding = parse_list(list_text)
    details = parse_info(info_text)
    rows = []
    for adv_id in sorted(outstanding):
        info = details.get(adv_id, {})
        severity = info.get("severity") or outstanding[adv_id]["severity"]
        issued_text = info.get("issued") or info.get("updated") or ""
        kev_cves = sorted(set(info.get("cves", [])) & kev)
        sla_days = KEV_SLA_DAYS if kev_cves else sla.get(severity)
        row = {
            "advisory": adv_id,
            "severity": severity,
            "title": info.get("title", ""),
            "packages": outstanding[adv_id]["packages"],
            "issued": issued_text or None,
            "cves": info.get("cves", []),
            "kev_cves": kev_cves,
            "sla_days": sla_days,
            "age_days": None,
            "due": None,
            "overdue": False,
        }
        if issued_text and sla_days is not None:
            issued = _dt.date.fromisoformat(issued_text)
            due = issued + _dt.timedelta(days=sla_days)
            row.update(age_days=(today - issued).days, due=due.isoformat(), overdue=today > due)
        rows.append(row)

    counts = {sev: sum(1 for r in rows if r["severity"] == sev) for sev in SEVERITIES}
    overdue = [r for r in rows if r["overdue"]]
    undated = [r for r in rows if r["issued"] is None]
    return {
        "host": host,
        "rings": rings,
        "status": "OVERDUE" if overdue else ("UNKNOWN" if undated else "WITHIN SLA"),
        "outstanding": len(rows),
        "counts": counts,
        "overdue": len(overdue),
        "oldest_overdue_days": max((r["age_days"] for r in overdue), default=None),
        "advisories": rows,
    }


def load_kev(path: str | None) -> set:
    if not path:
        return set()
    with open(path, encoding="utf-8") as handle:
        return set(CVE_RE.findall(handle.read()))


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        return ""


def build_report(report_dir: str, sla: dict, kev: set, today: _dt.date) -> dict:
    hosts = []
    for name in sorted(os.listdir(report_dir)):
        host_dir = os.path.join(report_dir, name)
        if not os.path.isdir(host_dir):
            continue
        meta = {}
        meta_text = _read(os.path.join(host_dir, "host.json"))
        if meta_text.strip():
            meta = json.loads(meta_text)
        hosts.append(score_host(
            meta.get("host", name), meta.get("rings", []),
            _read(os.path.join(host_dir, "updateinfo-list.txt")),
            _read(os.path.join(host_dir, "updateinfo-info.txt")),
            sla, kev, today))
    return {
        "tool": "patch_report.py",
        "tool_version": __version__,
        "generated": today.isoformat(),
        "sla_days": sla,
        "kev_sla_days": KEV_SLA_DAYS,
        "hosts": hosts,
        "totals": {
            "hosts": len(hosts),
            "hosts_overdue": sum(1 for h in hosts if h["status"] == "OVERDUE"),
            "advisories_overdue": sum(h["overdue"] for h in hosts),
        },
    }


def render_markdown(report: dict) -> str:
    t = report["totals"]
    sla = report["sla_days"]
    lines = [
        "# Patch compliance against the SLA",
        "",
        f"Generated {report['generated']} by patch_report.py {report['tool_version']}. "
        f"SLA in days from the advisory issue date: "
        + ", ".join(f"{sev} {sla[sev]}" for sev in SEVERITIES if sev in sla)
        + f"; {report['kev_sla_days']} for a CVE in the KEV list.",
        "",
        f"**{t['hosts_overdue']} of {t['hosts']} hosts are outside the SLA, "
        f"{t['advisories_overdue']} overdue advisories in total.**",
        "",
        "| Host | Ring | Status | Critical | Important | Moderate | Low | Overdue | Oldest overdue (days) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for h in report["hosts"]:
        c = h["counts"]
        lines.append(f"| {h['host']} | {', '.join(h['rings']) or '-'} | {h['status']} | {c['Critical']} | "
                     f"{c['Important']} | {c['Moderate']} | {c['Low']} | {h['overdue']} | "
                     f"{h['oldest_overdue_days'] if h['oldest_overdue_days'] is not None else '-'} |")
    overdue_rows = [(h["host"], a) for h in report["hosts"] for a in h["advisories"] if a["overdue"]]
    lines += ["", "## Overdue advisories", ""]
    if overdue_rows:
        lines += ["| Host | Advisory | Severity | Issued | Due | Age (days) | KEV | Title |",
                  "|---|---|---|---|---|---|---|---|"]
        for host, a in sorted(overdue_rows, key=lambda r: (-(r[1]["age_days"] or 0), r[0])):
            title = a["title"].replace("|", "\\|")
            lines.append(f"| {host} | {a['advisory']} | {a['severity']} | {a['issued']} | {a['due']} | "
                         f"{a['age_days']} | {'yes' if a['kev_cves'] else ''} | {title} |")
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score outstanding security errata against the patch SLA.")
    parser.add_argument("report_dir", help="folder written by playbooks/patch_report.yml")
    parser.add_argument("--sla", default=None, help='JSON, for example {"Critical": 7, "Important": 30}')
    parser.add_argument("--kev", default=None, help="file listing CVE ids known to be exploited (CISA KEV)")
    parser.add_argument("--today", default=None, help="YYYY-MM-DD (default: today)")
    parser.add_argument("--fail-on-overdue", action="store_true", help="exit 3 when any host is outside the SLA")
    args = parser.parse_args(argv)

    sla = dict(DEFAULT_SLA)
    if args.sla:
        try:
            sla.update({k.capitalize(): int(v) for k, v in json.loads(args.sla).items()})
        except (ValueError, AttributeError) as exc:
            parser.error(f"--sla: {exc}")
    try:
        today = _dt.date.fromisoformat(args.today) if args.today else _dt.date.today()
    except ValueError:
        parser.error("--today must be YYYY-MM-DD")
    if not os.path.isdir(args.report_dir):
        print(f"patch_report: error: {args.report_dir} is not a folder", file=sys.stderr)
        return 1

    report = build_report(args.report_dir, sla, load_kev(args.kev), today)
    with open(os.path.join(args.report_dir, "compliance.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    with open(os.path.join(args.report_dir, "compliance.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(report))

    t = report["totals"]
    print(f"{t['hosts_overdue']} of {t['hosts']} hosts outside the SLA, {t['advisories_overdue']} overdue advisories")
    print(f"written to {args.report_dir}")
    if args.fail_on_overdue and t["hosts_overdue"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
