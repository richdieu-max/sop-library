"""Evidence bundle: results.json, results.csv, report.md and SHA256SUMS; plus the stdout summary."""

import csv
import hashlib
import io
import json
import os

from .core import AREAS, ERROR, FAIL, PASS, STATUSES, WARN, Result

BUNDLE_FILES = ("results.json", "results.csv", "report.md")
CSV_COLUMNS = ("check_id", "area", "title", "status", "region", "resource_id",
               "detail", "remediation", "nist_800_53", "cis")


def default_out_dir(account_id, when):
    return os.path.join("evidence", "aws-posture-%s-%s" % (account_id, when.strftime("%Y%m%dT%H%M%SZ")))


def to_json(metadata, summary, results):
    doc = {"run": metadata, "summary": summary, "results": [r.to_dict() for r in results]}
    return json.dumps(doc, indent=2, sort_keys=False, default=str) + "\n"


def to_csv(results):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for r in results:
        writer.writerow([r.check_id, r.area, r.title, r.status, r.region, r.resource_id,
                         r.detail, r.remediation, "; ".join(r.nist), r.cis])
    return buf.getvalue()


def _cell(value):
    return " ".join(str(value).split()).replace("|", "\\|")


def _rows_table(rows, with_fix=True):
    head = "| Check | Region | Resource | Detail |"
    sep = "|---|---|---|---|"
    if with_fix:
        head += " Remediation | NIST 800-53 | CIS |"
        sep += "---|---|---|"
    lines = [head, sep]
    for r in rows:
        line = "| %s | %s | `%s` | %s |" % (_cell(r.check_id), _cell(r.region), _cell(r.resource_id), _cell(r.detail))
        if with_fix:
            line += " %s | %s | %s |" % (_cell(r.remediation), _cell(", ".join(r.nist)), _cell(r.cis or "-"))
        lines.append(line)
    return lines


def to_markdown(metadata, summary, results):
    lines = ["# AWS posture check report", ""]
    lines += ["| Item | Value |", "|---|---|"]
    meta_rows = (
        ("Account", metadata.get("account_id")),
        ("Caller", metadata.get("caller_arn")),
        ("Regions", ", ".join(metadata.get("regions", []))),
        ("Home region", metadata.get("home_region")),
        ("Areas", ", ".join(metadata.get("areas", []))),
        ("Tool", "%s %s" % (metadata.get("tool"), metadata.get("tool_version"))),
        ("Started (UTC)", metadata.get("started_utc")),
        ("Finished (UTC)", metadata.get("finished_utc")),
        ("Fail on", "%s (exit code %s)" % (metadata.get("fail_on"), metadata.get("exit_code"))),
    )
    for k, v in meta_rows:
        lines.append("| %s | %s |" % (k, _cell("`%s`" % v if k in ("Account", "Caller") else v)))
    lines += ["", "This run made no changes: it used only Describe, Get and List calls and "
              "iam:GenerateCredentialReport.", ""]

    lines += ["## Summary", "", "| Area | PASS | WARN | FAIL | ERROR |", "|---|---|---|---|---|"]
    for area, counts in summary["by_area"].items():
        lines.append("| %s | %s |" % (area, " | ".join(str(counts[s]) for s in STATUSES)))
    total = summary["total"]
    lines.append("| **Total** | %s |" % " | ".join("**%d**" % total[s] for s in STATUSES))
    lines.append("")

    sections = ((FAIL, ""), (WARN, ""), (ERROR, ", not verified"), (PASS, ""))
    for status, note in sections:
        rows = [r for r in results if r.status == status]
        lines += ["## %s (%d%s)" % (status, len(rows), note), ""]
        if rows:
            lines += _rows_table(rows, with_fix=status != PASS)
        else:
            lines.append("None.")
        lines.append("")
    lines += ["Full results, including titles, are in `results.json` and `results.csv`. "
              "Verify the bundle with `sha256sum -c SHA256SUMS`.", ""]
    return "\n".join(lines)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_bundle(out_dir, metadata, summary, results):
    """Write the evidence files and SHA256SUMS. Returns the list of paths written."""
    os.makedirs(out_dir, exist_ok=True)
    contents = {
        "results.json": to_json(metadata, summary, results),
        "results.csv": to_csv(results),
        "report.md": to_markdown(metadata, summary, results),
    }
    paths = []
    for name in BUNDLE_FILES:
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(contents[name])
        paths.append(path)
    sums = "".join("%s  %s\n" % (sha256_file(p), os.path.basename(p)) for p in paths)
    sums_path = os.path.join(out_dir, "SHA256SUMS")
    with open(sums_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(sums)
    paths.append(sums_path)
    return paths


def to_text(metadata, summary, results, out_dir=None):
    """Short human summary for stdout."""
    lines = [
        "%s %s  account %s  regions %s" % (metadata.get("tool"), metadata.get("tool_version"),
                                           metadata.get("account_id"), ",".join(metadata.get("regions", []))),
        "",
        "%-18s %5s %5s %5s %6s" % ("Area", "PASS", "WARN", "FAIL", "ERROR"),
    ]
    for area in AREAS:
        if area in summary["by_area"]:
            c = summary["by_area"][area]
            lines.append("%-18s %5d %5d %5d %6d" % (area, c[PASS], c[WARN], c[FAIL], c[ERROR]))
    t = summary["total"]
    lines.append("%-18s %5d %5d %5d %6d" % ("Total", t[PASS], t[WARN], t[FAIL], t[ERROR]))
    flagged = [r for r in results if r.status in (FAIL, WARN, ERROR)]
    order = {FAIL: 0, WARN: 1, ERROR: 2}
    if flagged:
        lines.append("")
        for r in sorted(flagged, key=lambda r: order[r.status]):
            lines.append("%-5s %-7s %-14s %s: %s" % (r.status, r.check_id, r.region, r.resource_id, r.detail))
    if out_dir:
        lines += ["", "Evidence: %s" % out_dir]
    lines.append("Exit code: %s (fail on %s)" % (metadata.get("exit_code"), metadata.get("fail_on")))
    return "\n".join(lines) + "\n"


def results_from_json(text):
    """Rebuild Result objects from results.json (used by tests and for re-rendering)."""
    doc = json.loads(text)
    return [Result(**r) for r in doc["results"]]
