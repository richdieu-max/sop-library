"""Command line interface for aws-posture-check."""

import argparse
import platform
import re
import sys
from datetime import datetime, timezone

from . import TOOL_NAME, __version__
from .core import (
    AREAS, FAIL_ON_CHOICES, Context, exit_code_for, normalise_area, run_checks, select_checks,
    summarise,
)
from .output import default_out_dir, to_json, to_text, write_bundle

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

REGION_RE = re.compile(r"^[a-z]{2}(-[a-z]+)+-\d{1,2}$")


def _area(value):
    try:
        return normalise_area(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc))


def _region(value):
    if not REGION_RE.match(value):
        raise argparse.ArgumentTypeError("not a region name: %r (for example us-east-1)" % value)
    return value


def build_parser():
    p = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Read-only AWS security posture check. Makes no changes; writes a hashed evidence bundle.",
    )
    p.add_argument("--profile", help="AWS CLI profile to use (default: the standard credential chain)")
    p.add_argument("--regions", nargs="+", type=_region, metavar="REGION",
                   help="regions for regional checks (default: the profile's region, else us-east-1)")
    p.add_argument("--home-region", type=_region, metavar="REGION",
                   help="region for account-wide checks and IAM Identity Center (default: first of --regions)")
    p.add_argument("--areas", nargs="+", type=_area, metavar="AREA",
                   help="areas to check (default: all): %s" % ", ".join('"%s"' % a for a in AREAS))
    p.add_argument("--checks", nargs="+", metavar="ID", help="run only these check ids, for example IAM-01 EC2-01")
    p.add_argument("--fail-on", choices=FAIL_ON_CHOICES, default="fail",
                   help="exit 1 on: fail = any FAIL (default); warn = any FAIL, WARN or ERROR; never = always 0")
    p.add_argument("--out", metavar="DIR",
                   help="evidence folder (default: ./evidence/aws-posture-<account>-<UTC timestamp>)")
    p.add_argument("--format", choices=("text", "json"), default="text",
                   help="what to print to stdout: text summary (default) or the full JSON results")
    p.add_argument("--list-checks", action="store_true", help="list the checks and exit (no AWS calls)")
    p.add_argument("-q", "--quiet", action="store_true", help="no progress messages on stderr")
    p.add_argument("--version", action="version", version="%s %s" % (TOOL_NAME, __version__))
    return p


def _list_checks(stream):
    stream.write("%-7s %-18s %-9s %-26s %-10s %s\n" % ("ID", "Area", "Scope", "NIST 800-53", "CIS", "Title"))
    for c in select_checks():
        stream.write("%-7s %-18s %-9s %-26s %-10s %s\n"
                     % (c.check_id, c.area, c.scope, ", ".join(c.nist), c.cis or "-", c.title))


def _utc(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None, client_factory=None, default_region=None, stdout=None, stderr=None, now=None):
    """Entry point. ``client_factory`` and ``default_region`` are injected by tests."""
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    args = build_parser().parse_args(argv)

    if args.list_checks:
        _list_checks(stdout)
        return EXIT_OK

    try:
        checks = select_checks(args.areas, args.checks)
    except ValueError as exc:
        stderr.write("%s: %s\n" % (TOOL_NAME, exc))
        return EXIT_USAGE
    if not checks:
        stderr.write("%s: no checks match the selected areas and check ids\n" % TOOL_NAME)
        return EXIT_USAGE

    versions = {}
    if client_factory is None:
        try:
            from .aws import make_client_factory
            client_factory, default_region, versions = make_client_factory(args.profile)
        except Exception as exc:
            stderr.write("%s: cannot start an AWS session: %s\n" % (TOOL_NAME, exc))
            return EXIT_USAGE

    regions = list(dict.fromkeys(args.regions or [default_region or "us-east-1"]))
    home = args.home_region or regions[0]

    try:
        ident = client_factory("sts", home).get_caller_identity()
    except Exception as exc:
        stderr.write("%s: cannot identify the caller (check credentials and --profile): %s\n" % (TOOL_NAME, exc))
        return EXIT_USAGE
    account, caller = ident.get("Account", "unknown"), ident.get("Arn", "unknown")

    started = now or datetime.now(timezone.utc)
    ctx = Context(client_factory, account, regions, home_region=home, caller_arn=caller, now=started)

    def progress(check, region):
        if not args.quiet:
            stderr.write("  %-7s %-14s %s\n" % (check.check_id, region, check.title))

    if not args.quiet:
        stderr.write("%s %s: account %s, %d check(s), region(s) %s\n"
                     % (TOOL_NAME, __version__, account, len(checks), ", ".join(regions)))
    results = run_checks(ctx, checks, progress=progress)
    finished = datetime.now(timezone.utc) if now is None else now
    summary = summarise(results)
    code = exit_code_for(results, args.fail_on)

    metadata = {
        "tool": TOOL_NAME,
        "tool_version": __version__,
        "account_id": account,
        "caller_arn": caller,
        "regions": regions,
        "home_region": home,
        "areas": sorted({c.area for c in checks}, key=AREAS.index),
        "checks": [c.check_id for c in checks],
        "fail_on": args.fail_on,
        "exit_code": code,
        "started_utc": _utc(started),
        "finished_utc": _utc(finished),
        "python_version": platform.python_version(),
        "libraries": versions,
        "read_only": True,
    }

    out_dir = args.out or default_out_dir(account, started)
    try:
        write_bundle(out_dir, metadata, summary, results)
    except OSError as exc:
        stderr.write("%s: cannot write evidence to %s: %s\n" % (TOOL_NAME, out_dir, exc))
        return EXIT_USAGE

    if args.format == "json":
        stdout.write(to_json(metadata, summary, results))
    else:
        stdout.write(to_text(metadata, summary, results, out_dir))
    return code


def run():  # console script entry point
    sys.exit(main())


if __name__ == "__main__":
    run()
