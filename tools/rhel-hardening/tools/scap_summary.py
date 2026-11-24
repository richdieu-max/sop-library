#!/usr/bin/env python3
"""Summarise an OpenSCAP result file into findings an auditor can read.

Reads an ARF file (oscap xccdf eval --results-arf) or a plain XCCDF result
file (--results), and writes:

  report.md      FAIL, WARN and ACCEPTED findings, counts in the header
  summary.json   scan metadata and counts
  findings.json  every finding, PASS included
  SHA256SUMS     with --sha256sums, a manifest of every file in the folder

Status mapping:

  oscap result                             severity        finding
  fail                                     high, medium    FAIL
  fail                                     low, other      WARN
  error, unknown                           any             WARN (could not evaluate)
  pass, fixed                              any             PASS
  notapplicable, notselected, notchecked,  any             counted only
  informational

A FAIL or WARN that matches an exception that has not expired becomes
ACCEPTED. An exception past its expiry date no longer applies: the finding
keeps its status and the exception is listed as expired.

Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

__version__ = "1.0.0"

RULE_PREFIX = "xccdf_org.ssgproject.content_rule_"
PROFILE_PREFIX = "xccdf_org.ssgproject.content_profile_"

FAIL, WARN, PASS, ACCEPTED = "FAIL", "WARN", "PASS", "ACCEPTED"
COUNTED_ONLY = ("notapplicable", "notselected", "notchecked", "informational")
STATUS_ORDER = {FAIL: 0, WARN: 1, ACCEPTED: 2, PASS: 3}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "unknown": 3, "info": 4}

EXIT_OK, EXIT_ERROR, EXIT_THRESHOLD = 0, 1, 3

# Rule id fragments to role area, first match wins. The area names match
# the tags of the rhel_baseline role where the role owns the setting.
AREA_PATTERNS = [
    ("partition_|mount_option_", "Partitions"),
    ("sshd_|_ssh_|ssh_", "SSH"),
    ("selinux", "SELinux"),
    ("aide_|package_aide", "AIDE"),
    ("audit|auditd", "Audit"),
    ("journald|rsyslog|logrotate|_log_", "Logging"),
    ("firewalld|nftables|iptables|firewall", "Firewall"),
    ("crypto|fips", "Crypto"),
    ("sysctl_|kernel_module_|coredump|core_dump", "Kernel"),
    ("grub2_|bootloader", "Boot"),
    ("accounts_|pam_|faillock|password|passwd|sudo|login_defs|umask|tmout|_su_|authselect", "Auth"),
    ("gpgcheck|gpgkey|dnf|yum|security_patches", "Patching"),
    ("service_|package_|_disabled$|_removed$|chronyd|ntp|cron|at_", "Services"),
    ("file_|dir_|permissions|owner|groupowner", "Files"),
    ("banner|motd|issue", "Banner"),
]


class SummaryError(Exception):
    """A problem with the input that stops the summary."""


# --------------------------------------------------------------- helpers

def local(tag: str) -> str:
    """Element name without its namespace."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text_of(elem) -> str:
    """All text inside an element (titles can hold XHTML), squeezed."""
    if elem is None:
        return ""
    return " ".join("".join(elem.itertext()).split())


def short_rule_id(rule_id: str) -> str:
    return rule_id[len(RULE_PREFIX):] if rule_id.startswith(RULE_PREFIX) else rule_id


def area_for(rule_id: str) -> str:
    short = short_rule_id(rule_id)
    for pattern, area in AREA_PATTERNS:
        if re.search(pattern, short):
            return area
    return "Other"


def md_cell(value) -> str:
    """Make a value safe for a Markdown table cell."""
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


# ------------------------------------------------------------ XML parsing

def parse_results(path: str) -> dict:
    """Read rules and rule results from an ARF or XCCDF result file.

    Uses iterparse and clears what it has read, so a large ARF with OVAL
    results does not have to sit in memory as a whole tree.
    """
    rules: dict[str, dict] = {}
    results: list[dict] = []
    scan: dict = {}
    benchmark: dict = {}
    test_results_seen = 0
    stack: list[str] = []

    try:
        context = ET.iterparse(path, events=("start", "end"))
        for event, elem in context:
            name = local(elem.tag)
            if event == "start":
                stack.append(name)
                if name == "Benchmark" and not benchmark:
                    benchmark["id"] = elem.get("id", "")
                    benchmark["resolved"] = elem.get("resolved", "")
                elif name == "TestResult":
                    test_results_seen += 1
                    scan = {
                        "test_result_id": elem.get("id", ""),
                        "start_time": elem.get("start-time", ""),
                        "end_time": elem.get("end-time", ""),
                    }
                continue

            # end events
            stack.pop()
            parent = stack[-1] if stack else ""
            if name == "Rule":
                rules[elem.get("id", "")] = _rule_details(elem)
                elem.clear()
            elif name == "rule-result":
                results.append(_rule_result(elem))
                elem.clear()
            elif name == "version" and parent == "Benchmark" and "version" not in benchmark:
                benchmark["version"] = (elem.text or "").strip()
            elif name == "title" and parent == "Benchmark" and "title" not in benchmark:
                benchmark["title"] = text_of(elem)
            elif name == "TestResult":
                _test_result_details(elem, scan)
                elem.clear()
            elif name in ("component", "report", "oval_results", "results"):
                elem.clear()
    except ET.ParseError as exc:
        raise SummaryError(f"{path} is not well-formed XML: {exc}") from exc
    except OSError as exc:
        raise SummaryError(f"cannot read {path}: {exc}") from exc

    if test_results_seen == 0:
        raise SummaryError(f"{path} has no XCCDF TestResult: is it an oscap result file?")
    if test_results_seen > 1:
        scan["note"] = f"{test_results_seen} TestResult elements found, the last one is used"
    scan["benchmark"] = benchmark
    return {"rules": rules, "results": results, "scan": scan}


def _rule_details(elem) -> dict:
    title, nist, cis = "", [], []
    for child in elem:
        cname = local(child.tag)
        if cname == "title" and not title:
            title = text_of(child)
        elif cname == "reference":
            href = (child.get("href") or "").lower()
            values = [v.strip() for v in (child.text or "").split(",") if v.strip()]
            if "800-53" in href:
                nist.extend(values)
            elif "cisecurity" in href:
                cis.extend(values)
    return {
        "title": title,
        "severity": (elem.get("severity") or "").lower(),
        "nist_800_53": _unique(nist),
        "cis": _unique(cis),
    }


def _rule_result(elem) -> dict:
    result, idents = "", []
    for child in elem:
        cname = local(child.tag)
        if cname == "result":
            result = (child.text or "").strip().lower()
        elif cname == "ident":
            if child.text and child.text.strip():
                idents.append(child.text.strip())
    return {
        "rule_id": elem.get("idref", ""),
        "result": result,
        "severity": (elem.get("severity") or "").lower(),
        "idents": idents,
    }


def _test_result_details(elem, scan: dict) -> None:
    for child in elem:
        cname = local(child.tag)
        if cname == "profile":
            scan["profile"] = child.get("idref", "")
        elif cname == "target":
            scan["target"] = (child.text or "").strip()
        elif cname == "target-address":
            scan.setdefault("target_addresses", []).append((child.text or "").strip())
        elif cname == "score":
            scan.setdefault("scores", []).append({
                "system": child.get("system", ""),
                "value": (child.text or "").strip(),
                "maximum": child.get("maximum", ""),
            })
        elif cname == "identity":
            scan["identity"] = (child.text or "").strip()
        elif cname == "benchmark" and not scan.get("benchmark_href"):
            scan["benchmark_href"] = child.get("href", "")


def _unique(values: list) -> list:
    seen, out = set(), []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


# -------------------------------------------------------------- exceptions

def _scalar(raw: str):
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        if value[0] == "'":
            return value[1:-1].replace("''", "'")
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_scalar(v) for v in _split_flow(inner)] if inner else []
    if value in ("", "~", "null", "Null", "NULL"):
        return None
    return value


def _split_flow(inner: str) -> list:
    parts, buf, quote = [], "", ""
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return [p.strip() for p in parts]


def _strip_comment(line: str) -> str:
    out, quote = "", ""
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out += ch
    return out.rstrip()


def parse_simple_yaml(text: str):
    """Parse the small YAML subset used by exception files.

    Supports a top-level list of mappings, or a mapping with one key
    ("exceptions") holding that list. Values are scalars, quoted strings,
    flow lists ([a, b]) or block lists of scalars. This keeps the tool on
    the standard library; use JSON for anything more complex.
    """
    lines = []
    for number, raw in enumerate(text.splitlines(), 1):
        if raw.strip() in ("---", "..."):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise SummaryError(f"line {number}: tabs are not allowed for indentation")
        stripped = _strip_comment(raw)
        if stripped.strip():
            lines.append((number, len(stripped) - len(stripped.lstrip()), stripped.strip()))

    if not lines:
        return []

    root_key = None
    if not lines[0][2].startswith("-"):
        number, _indent, content = lines[0]
        if not content.endswith(":"):
            raise SummaryError(f"line {number}: expected a list of exceptions or 'exceptions:'")
        root_key = content[:-1].strip()
        lines = lines[1:]

    items: list[dict] = []
    current: dict | None = None
    item_indent = None
    list_key = None
    for number, indent, content in lines:
        if content.startswith("- ") or content == "-":
            if item_indent is None:
                item_indent = indent
            if indent == item_indent:
                current = {}
                items.append(current)
                list_key = None
                content = content[1:].strip()
                if not content:
                    continue
                indent = indent + 2
            elif list_key is not None and indent > item_indent and current is not None:
                current[list_key].append(_scalar(content[1:].strip()))
                continue
            else:
                raise SummaryError(f"line {number}: unexpected list item")
        if current is None:
            raise SummaryError(f"line {number}: expected '- ' to start an exception")
        if ":" not in content:
            raise SummaryError(f"line {number}: expected 'key: value'")
        key, _, value = content.partition(":")
        key = key.strip()
        if value.strip() == "":
            current[key] = []
            list_key = key
        else:
            current[key] = _scalar(value)
            list_key = None
    if root_key is not None:
        return {root_key: items}
    return items


def _parse_date(value, field: str, where: str) -> _dt.date:
    if isinstance(value, _dt.date):
        return value
    try:
        return _dt.date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise SummaryError(f"{where}: {field} must be a date as YYYY-MM-DD, got {value!r}") from exc


def load_exceptions(path: str) -> list[dict]:
    """Load exceptions from a YAML (subset) or JSON file and validate them."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        raise SummaryError(f"cannot read exceptions file {path}: {exc}") from exc

    if path.lower().endswith(".json") or text.lstrip().startswith(("{", "[")):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SummaryError(f"{path} is not valid JSON: {exc}") from exc
    else:
        data = parse_simple_yaml(text)

    if isinstance(data, dict):
        data = data.get("exceptions", [])
    if data is None:
        data = []
    if not isinstance(data, list):
        raise SummaryError(f"{path}: expected a list of exceptions")

    out = []
    for index, entry in enumerate(data, 1):
        where = f"{path} exception {index}"
        if not isinstance(entry, dict):
            raise SummaryError(f"{where}: expected a mapping")
        rule = entry.get("rule") or entry.get("rule_id")
        missing = [f for f, v in (("rule", rule), ("reason", entry.get("reason")),
                                  ("owner", entry.get("owner")), ("expires", entry.get("expires")))
                   if v in (None, "", [])]
        if missing:
            raise SummaryError(f"{where}: missing {', '.join(missing)}")
        hosts = entry.get("hosts") or []
        if isinstance(hosts, str):
            hosts = [hosts]
        out.append({
            "rule": short_rule_id(str(rule).strip()),
            "reason": str(entry["reason"]).strip(),
            "owner": str(entry["owner"]).strip(),
            "expires": _parse_date(entry["expires"], "expires", where),
            "hosts": [str(h) for h in hosts],
            "reference": str(entry.get("reference") or entry.get("change") or "").strip(),
        })
    return out


def _exception_applies(exc: dict, rule_id: str, host: str) -> bool:
    if exc["rule"] != short_rule_id(rule_id):
        return False
    if not exc["hosts"]:
        return True
    return any(fnmatch.fnmatchcase(host, pattern) for pattern in exc["hosts"])


# ---------------------------------------------------------------- mapping

def map_status(result: str, severity: str) -> tuple[str | None, str]:
    """Return (status, note) for one rule result. status None = counted only."""
    if result == "fail":
        if severity in ("high", "medium"):
            return FAIL, ""
        return WARN, ""
    if result in ("error", "unknown"):
        return WARN, "could not evaluate"
    if result in ("pass", "fixed"):
        return PASS, ""
    if result in COUNTED_ONLY:
        return None, ""
    return WARN, f"unexpected result {result!r}"


def build_findings(parsed: dict, exceptions: list[dict], host: str, today: _dt.date) -> dict:
    rules = parsed["rules"]
    findings, counted = [], {}
    used_exceptions: set[int] = set()
    expired_hits: list[dict] = []

    for res in parsed["results"]:
        rule = rules.get(res["rule_id"], {})
        severity = res["severity"] or rule.get("severity") or "unknown"
        status, note = map_status(res["result"], severity)
        if status is None:
            counted[res["result"]] = counted.get(res["result"], 0) + 1
            continue

        finding = {
            "status": status,
            "rule_id": res["rule_id"],
            "rule": short_rule_id(res["rule_id"]),
            "title": rule.get("title") or short_rule_id(res["rule_id"]),
            "severity": severity,
            "result": res["result"],
            "area": area_for(res["rule_id"]),
            "nist_800_53": rule.get("nist_800_53", []),
            "cis": rule.get("cis", []),
            "idents": res["idents"],
            "note": note,
        }

        if status in (FAIL, WARN):
            for index, exc in enumerate(exceptions):
                if not _exception_applies(exc, res["rule_id"], host):
                    continue
                used_exceptions.add(index)
                exc_view = {
                    "reason": exc["reason"],
                    "owner": exc["owner"],
                    "expires": exc["expires"].isoformat(),
                    "reference": exc["reference"],
                }
                if today <= exc["expires"]:
                    finding["original_status"] = status
                    finding["status"] = ACCEPTED
                    finding["exception"] = exc_view
                    break
                finding["exception_expired"] = exc_view
                expired_hits.append({"rule": finding["rule"], "status": status, **exc_view})
        findings.append(finding)

    findings.sort(key=lambda f: (STATUS_ORDER[f["status"]], SEVERITY_ORDER.get(f["severity"], 9),
                                 f["area"], f["rule"]))

    unused = [
        {"rule": e["rule"], "owner": e["owner"], "expires": e["expires"].isoformat()}
        for i, e in enumerate(exceptions)
        if i not in used_exceptions and (not e["hosts"] or any(fnmatch.fnmatchcase(host, p) for p in e["hosts"]))
    ]
    counts = {s: sum(1 for f in findings if f["status"] == s) for s in (FAIL, WARN, ACCEPTED, PASS)}
    for key in COUNTED_ONLY:
        counts[key] = counted.get(key, 0)
    counts["high_fail_without_exception"] = sum(
        1 for f in findings if f["status"] == FAIL and f["severity"] == "high")
    counts["rules_evaluated"] = len(parsed["results"])
    return {"findings": findings, "counts": counts, "expired_exceptions": expired_hits,
            "unused_exceptions": unused}


# ----------------------------------------------------------------- output

def render_markdown(host: str, source: str, scan: dict, result: dict, today: _dt.date) -> str:
    c = result["counts"]
    profile = scan.get("profile", "")
    lines = [
        f"# OpenSCAP findings: {host}",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Host | {md_cell(host)} |",
        f"| Target | {md_cell(scan.get('target', ''))} |",
        f"| Profile | {md_cell(profile[len(PROFILE_PREFIX):] if profile.startswith(PROFILE_PREFIX) else profile)} |",
        f"| Benchmark | {md_cell(scan.get('benchmark', {}).get('id', ''))} {md_cell(scan.get('benchmark', {}).get('version', ''))} |",
        f"| Scan started | {md_cell(scan.get('start_time', ''))} |",
        f"| Scan finished | {md_cell(scan.get('end_time', ''))} |",
        f"| Source file | {md_cell(os.path.basename(source))} |",
        f"| Summarised | {today.isoformat()} by scap_summary.py {__version__} |",
    ]
    for score in scan.get("scores", []):
        lines.append(f"| Score ({md_cell(score['system'].rsplit(':', 1)[-1])}) | "
                     f"{md_cell(score['value'])} of {md_cell(score['maximum'])} |")
    lines += [
        "",
        "| FAIL | WARN | ACCEPTED | PASS | Not applicable | Not selected | Not checked | Informational |",
        "|---|---|---|---|---|---|---|---|",
        f"| {c[FAIL]} | {c[WARN]} | {c[ACCEPTED]} | {c[PASS]} | {c['notapplicable']} | "
        f"{c['notselected']} | {c['notchecked']} | {c['informational']} |",
        "",
    ]
    if c["high_fail_without_exception"]:
        lines += [f"**{c['high_fail_without_exception']} high-severity rule(s) fail without an exception.** "
                  "Fix and re-scan, or record a dated exception.", ""]

    if result["expired_exceptions"]:
        lines += ["## Expired exceptions", "",
                  "These exceptions are past their expiry date and no longer apply. Renew them or fix the finding.", "",
                  "| Rule | Status | Owner | Expired | Reason |", "|---|---|---|---|---|"]
        for e in result["expired_exceptions"]:
            lines.append(f"| `{md_cell(e['rule'])}` | {e['status']} | {md_cell(e['owner'])} | "
                         f"{e['expires']} | {md_cell(e['reason'])} |")
        lines.append("")

    sections = [
        (FAIL, "FAIL: high or medium severity rules that failed"),
        (WARN, "WARN: low severity failures and rules that could not be evaluated"),
    ]
    for status, heading in sections:
        rows = [f for f in result["findings"] if f["status"] == status]
        lines += [f"## {heading}", ""]
        if not rows:
            lines += ["None.", ""]
            continue
        lines += ["| Status | Area | Severity | Rule | Title | NIST SP 800-53 | Note |",
                  "|---|---|---|---|---|---|---|"]
        for f in rows:
            note = f["note"]
            if "exception_expired" in f:
                note = (note + "; " if note else "") + f"exception expired {f['exception_expired']['expires']}"
            lines.append(f"| {f['status']} | {f['area']} | {f['severity']} | `{md_cell(f['rule'])}` | "
                         f"{md_cell(f['title'])} | {md_cell(', '.join(f['nist_800_53']))} | {md_cell(note)} |")
        lines.append("")

    rows = [f for f in result["findings"] if f["status"] == ACCEPTED]
    lines += ["## ACCEPTED: findings covered by a current exception", ""]
    if rows:
        lines += ["| Was | Area | Severity | Rule | Title | NIST SP 800-53 | Owner | Expires | Reason |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for f in rows:
            e = f["exception"]
            lines.append(f"| {f['original_status']} | {f['area']} | {f['severity']} | `{md_cell(f['rule'])}` | "
                         f"{md_cell(f['title'])} | {md_cell(', '.join(f['nist_800_53']))} | {md_cell(e['owner'])} | "
                         f"{e['expires']} | {md_cell(e['reason'])} |")
    else:
        lines.append("None.")
    lines.append("")

    if result["unused_exceptions"]:
        lines += ["## Exceptions not used on this host", "",
                  "The rule passed or was not evaluated. Close the exception if the fix is permanent.", ""]
        for e in result["unused_exceptions"]:
            lines.append(f"- `{md_cell(e['rule'])}` (owner {md_cell(e['owner'])}, expires {e['expires']})")
        lines.append("")

    lines += ["PASS rules are listed in findings.json only.", ""]
    return "\n".join(lines)


def write_sha256sums(out_dir: str) -> str:
    """Write a sha256sum -c compatible manifest of every file in out_dir."""
    manifest = os.path.join(out_dir, "SHA256SUMS")
    entries = []
    for root, _dirs, files in os.walk(out_dir):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, out_dir).replace(os.sep, "/")
            if rel == "SHA256SUMS":
                continue
            digest = hashlib.sha256()
            with open(full, "rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            entries.append(f"{digest.hexdigest()}  {rel}")
    entries.sort(key=lambda line: line.split("  ", 1)[1])
    with open(manifest, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(entries) + "\n")
    return manifest


def summarise(source: str, out_dir: str, host: str | None = None, exceptions_file: str | None = None,
              today: _dt.date | None = None, sha256sums: bool = False) -> dict:
    today = today or _dt.date.today()
    parsed = parse_results(source)
    exceptions = load_exceptions(exceptions_file) if exceptions_file else []
    host = host or parsed["scan"].get("target") or "unknown-host"
    result = build_findings(parsed, exceptions, host, today)

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(host, source, parsed["scan"], result, today))

    summary = {
        "tool": "scap_summary.py",
        "tool_version": __version__,
        "host": host,
        "source": os.path.basename(source),
        "summarised": today.isoformat(),
        "scan": parsed["scan"],
        "exceptions_file": os.path.basename(exceptions_file) if exceptions_file else None,
        "counts": result["counts"],
        "expired_exceptions": result["expired_exceptions"],
        "unused_exceptions": result["unused_exceptions"],
    }
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    with open(os.path.join(out_dir, "findings.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result["findings"], handle, indent=2, sort_keys=True)
        handle.write("\n")
    if sha256sums:
        write_sha256sums(out_dir)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarise an OpenSCAP ARF or XCCDF result file into report.md, summary.json and findings.json.")
    parser.add_argument("results", help="ARF (--results-arf) or XCCDF (--results) file from oscap xccdf eval")
    parser.add_argument("--out-dir", default=None, help="output folder (default: the folder of the results file)")
    parser.add_argument("--host", default=None, help="host name for the report (default: the scan target)")
    parser.add_argument("--exceptions", default=None, help="exceptions file, YAML or JSON")
    parser.add_argument("--today", default=None, help="date used to judge expiry, YYYY-MM-DD (default: today)")
    parser.add_argument("--sha256sums", action="store_true", help="write SHA256SUMS for every file in the output folder")
    parser.add_argument("--fail-on", choices=("none", "high", "fail"), default="none",
                        help="exit 3 when a high-severity FAIL (high) or any FAIL (fail) has no exception")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        today = _dt.date.fromisoformat(args.today) if args.today else None
    except ValueError:
        parser.error("--today must be YYYY-MM-DD")

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.results))
    try:
        summary = summarise(args.results, out_dir, args.host, args.exceptions, today, args.sha256sums)
    except SummaryError as exc:
        print(f"scap_summary: error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    c = summary["counts"]
    print(f"{summary['host']}: FAIL {c[FAIL]}, WARN {c[WARN]}, ACCEPTED {c[ACCEPTED]}, PASS {c[PASS]}, "
          f"not applicable {c['notapplicable']}")
    for e in summary["expired_exceptions"]:
        print(f"{summary['host']}: exception for {e['rule']} expired on {e['expires']} (owner {e['owner']})")
    print(f"written to {out_dir}")

    if args.fail_on == "high" and c["high_fail_without_exception"]:
        print(f"{summary['host']}: {c['high_fail_without_exception']} high-severity FAIL without an exception",
              file=sys.stderr)
        return EXIT_THRESHOLD
    if args.fail_on == "fail" and c[FAIL]:
        print(f"{summary['host']}: {c[FAIL]} FAIL without an exception", file=sys.stderr)
        return EXIT_THRESHOLD
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
