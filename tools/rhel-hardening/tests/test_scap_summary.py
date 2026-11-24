"""Unit tests for tools/scap_summary.py and tools/patch_report.py.

Run from the repository root:
    python3 -m unittest discover -s tools/rhel-hardening/tests
"""

import contextlib
import datetime as dt
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))

import patch_report  # noqa: E402
import scap_summary as ss  # noqa: E402

ARF = os.path.join(FIXTURES, "arf-sample.xml")
XCCDF = os.path.join(FIXTURES, "xccdf-results-sample.xml")
EXC_YAML = os.path.join(FIXTURES, "exceptions.yml")
EXC_JSON = os.path.join(FIXTURES, "exceptions.json")
TODAY = dt.date(2026, 11, 24)


def by_rule(findings):
    return {f["rule"]: f for f in findings}


class StatusMappingTest(unittest.TestCase):
    def test_mapping_table(self):
        cases = [
            ("fail", "high", ss.FAIL),
            ("fail", "medium", ss.FAIL),
            ("fail", "low", ss.WARN),
            ("fail", "unknown", ss.WARN),
            ("fail", "info", ss.WARN),
            ("error", "high", ss.WARN),
            ("unknown", "medium", ss.WARN),
            ("pass", "high", ss.PASS),
            ("fixed", "low", ss.PASS),
            ("notapplicable", "high", None),
            ("notselected", "medium", None),
            ("notchecked", "low", None),
            ("informational", "low", None),
        ]
        for result, severity, expected in cases:
            with self.subTest(result=result, severity=severity):
                self.assertEqual(ss.map_status(result, severity)[0], expected)

    def test_could_not_evaluate_note(self):
        self.assertEqual(ss.map_status("error", "high"), (ss.WARN, "could not evaluate"))

    def test_severity_falls_back_to_unknown(self):
        parsed = {"rules": {}, "results": [
            {"rule_id": "xccdf_org.ssgproject.content_rule_mystery", "result": "fail", "severity": "", "idents": []}],
            "scan": {}}
        out = ss.build_findings(parsed, [], "h", TODAY)
        self.assertEqual(out["findings"][0]["status"], ss.WARN)
        self.assertEqual(out["findings"][0]["severity"], "unknown")
        self.assertEqual(out["findings"][0]["title"], "mystery")


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.parsed = ss.parse_results(ARF)

    def test_rules_from_benchmark(self):
        rule = self.parsed["rules"]["xccdf_org.ssgproject.content_rule_sshd_disable_root_login"]
        self.assertEqual(rule["title"], "Disable SSH Root Login")
        self.assertEqual(rule["severity"], "medium")
        self.assertEqual(rule["nist_800_53"], ["AC-6(2)", "AC-17(a)", "IA-2"])
        self.assertEqual(rule["cis"], ["5.2.10"])

    def test_title_with_markup(self):
        rule = self.parsed["rules"]["xccdf_org.ssgproject.content_rule_service_auditd_enabled"]
        self.assertEqual(rule["title"], "Enable auditd Service")

    def test_scan_metadata(self):
        scan = self.parsed["scan"]
        self.assertEqual(scan["profile"], "xccdf_org.ssgproject.content_profile_cis_server_l1")
        self.assertEqual(scan["target"], "canary-01.example.test")
        self.assertEqual(scan["benchmark"]["version"], "0.1.72")
        self.assertEqual(scan["benchmark"]["id"], "xccdf_org.ssgproject.content_benchmark_RHEL-9")
        self.assertEqual(scan["scores"][0]["value"], "61.250000")
        self.assertIn("192.0.2.10", scan["target_addresses"])
        self.assertEqual(len(self.parsed["results"]), 11)

    def test_plain_xccdf_results(self):
        parsed = ss.parse_results(XCCDF)
        out = ss.build_findings(parsed, [], "web-01", TODAY)
        rows = by_rule(out["findings"])
        self.assertEqual(rows["ensure_gpgcheck_globally_activated"]["status"], ss.FAIL)
        self.assertEqual(rows["ensure_gpgcheck_globally_activated"]["area"], "Patching")
        self.assertEqual(rows["sshd_set_max_auth_tries"]["status"], ss.PASS)
        self.assertEqual(parsed["scan"]["benchmark"]["version"], "0.1.72")

    def test_not_xml(self):
        with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as handle:
            handle.write("this is not xml")
        try:
            with self.assertRaises(ss.SummaryError):
                ss.parse_results(handle.name)
        finally:
            os.unlink(handle.name)

    def test_xml_without_test_result(self):
        with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as handle:
            handle.write('<Benchmark xmlns="http://checklists.nist.gov/xccdf/1.2" id="b"/>')
        try:
            with self.assertRaisesRegex(ss.SummaryError, "no XCCDF TestResult"):
                ss.parse_results(handle.name)
        finally:
            os.unlink(handle.name)


class FindingsTest(unittest.TestCase):
    def setUp(self):
        self.parsed = ss.parse_results(ARF)
        self.exceptions = ss.load_exceptions(EXC_YAML)

    def test_canary_statuses(self):
        out = ss.build_findings(self.parsed, self.exceptions, "canary-01", TODAY)
        rows = by_rule(out["findings"])
        self.assertEqual(rows["sshd_disable_root_login"]["status"], ss.FAIL)
        self.assertEqual(rows["sshd_disable_root_login"]["area"], "SSH")
        self.assertEqual(rows["sshd_disable_root_login"]["idents"], ["CCE-90799-3"])
        self.assertEqual(rows["grub2_password"]["status"], ss.FAIL)
        self.assertEqual(rows["grub2_password"]["exception_expired"]["expires"], "2026-10-31")
        self.assertEqual(rows["partition_for_var_log_audit"]["status"], ss.ACCEPTED)
        self.assertEqual(rows["partition_for_var_log_audit"]["original_status"], ss.WARN)
        self.assertEqual(rows["partition_for_var_log_audit"]["exception"]["reference"], "CHG0012347")
        self.assertEqual(rows["rsyslog_remote_loghost"]["status"], ss.ACCEPTED)
        self.assertEqual(rows["rsyslog_remote_loghost"]["original_status"], ss.FAIL)
        self.assertEqual(rows["service_auditd_enabled"]["status"], ss.WARN)
        self.assertEqual(rows["service_auditd_enabled"]["note"], "could not evaluate")
        self.assertEqual(rows["kernel_module_usb-storage_disabled"]["status"], ss.WARN)
        # accounts_tmout has no severity on the rule-result: the rule's medium is used.
        self.assertEqual(rows["accounts_tmout"]["severity"], "medium")
        self.assertEqual(rows["accounts_tmout"]["status"], ss.FAIL)
        self.assertEqual(rows["package_aide_installed"]["status"], ss.PASS)
        self.assertEqual(rows["selinux_state"]["status"], ss.PASS)
        self.assertNotIn("sysctl_net_ipv6_conf_all_accept_ra", rows)

        counts = out["counts"]
        self.assertEqual((counts["FAIL"], counts["WARN"], counts["ACCEPTED"], counts["PASS"]), (3, 2, 2, 2))
        self.assertEqual(counts["notapplicable"], 1)
        self.assertEqual(counts["notselected"], 1)
        self.assertEqual(counts["high_fail_without_exception"], 1)
        self.assertEqual(counts["rules_evaluated"], 11)
        self.assertEqual([e["rule"] for e in out["expired_exceptions"]], ["grub2_password"])
        self.assertEqual([e["rule"] for e in out["unused_exceptions"]], ["package_aide_installed"])

    def test_order_fail_first(self):
        out = ss.build_findings(self.parsed, self.exceptions, "canary-01", TODAY)
        statuses = [f["status"] for f in out["findings"]]
        self.assertEqual(statuses, sorted(statuses, key=ss.STATUS_ORDER.get))
        self.assertEqual(out["findings"][0]["severity"], "high")

    def test_host_scoped_exception(self):
        out = ss.build_findings(self.parsed, self.exceptions, "web-01", TODAY)
        rows = by_rule(out["findings"])
        self.assertEqual(rows["accounts_tmout"]["status"], ss.ACCEPTED)
        self.assertEqual(rows["rsyslog_remote_loghost"]["status"], ss.ACCEPTED)
        out = ss.build_findings(self.parsed, self.exceptions, "db-01", TODAY)
        rows = by_rule(out["findings"])
        self.assertEqual(rows["accounts_tmout"]["status"], ss.FAIL)
        self.assertEqual(rows["rsyslog_remote_loghost"]["status"], ss.FAIL)

    def test_exception_valid_on_expiry_day_and_not_after(self):
        exc = [{"rule": "sshd_disable_root_login", "reason": "r", "owner": "o",
                "expires": dt.date(2026, 11, 24), "hosts": [], "reference": ""}]
        on_day = by_rule(ss.build_findings(self.parsed, exc, "h", TODAY)["findings"])
        self.assertEqual(on_day["sshd_disable_root_login"]["status"], ss.ACCEPTED)
        after = by_rule(ss.build_findings(self.parsed, exc, "h", TODAY + dt.timedelta(days=1))["findings"])
        self.assertEqual(after["sshd_disable_root_login"]["status"], ss.FAIL)

    def test_json_exceptions_match_yaml(self):
        exc = ss.load_exceptions(EXC_JSON)
        rows = by_rule(ss.build_findings(self.parsed, exc, "canary-01", TODAY)["findings"])
        self.assertEqual(rows["partition_for_var_log_audit"]["status"], ss.ACCEPTED)
        self.assertEqual(rows["grub2_password"]["status"], ss.FAIL)
        self.assertIn("exception_expired", rows["grub2_password"])


class ExceptionFileTest(unittest.TestCase):
    def _load(self, text, suffix=".yml"):
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as handle:
            handle.write(text)
        self.addCleanup(os.unlink, handle.name)
        return ss.load_exceptions(handle.name)

    def test_yaml_fixture(self):
        exc = ss.load_exceptions(EXC_YAML)
        self.assertEqual(len(exc), 5)
        self.assertEqual(exc[1]["rule"], "rsyslog_remote_loghost")
        self.assertEqual(exc[1]["owner"], "Security operations")
        self.assertEqual(exc[1]["hosts"], ["canary-*", "web-01"])
        self.assertEqual(exc[1]["expires"], dt.date(2027, 1, 15))
        self.assertEqual(exc[3]["hosts"], ["web-*"])
        self.assertEqual(exc[0]["reason"], "Disk layout is fixed at install; next build image adds the partition")

    def test_top_level_list_and_comments(self):
        exc = self._load("---\n# comment\n- rule: a_rule  # trailing comment\n  reason: 'it''s # not a comment'\n"
                         "  owner: team\n  expires: 2027-01-01\n")
        self.assertEqual(exc[0]["reason"], "it's # not a comment")

    def test_missing_field(self):
        with self.assertRaisesRegex(ss.SummaryError, "missing owner"):
            self._load("- rule: a\n  reason: b\n  expires: 2027-01-01\n")

    def test_bad_date(self):
        with self.assertRaisesRegex(ss.SummaryError, "YYYY-MM-DD"):
            self._load("- rule: a\n  reason: b\n  owner: c\n  expires: next year\n")

    def test_empty_file(self):
        self.assertEqual(self._load("# nothing yet\n"), [])

    def test_json_object_form(self):
        exc = self._load(json.dumps({"exceptions": [
            {"rule_id": "a", "reason": "b", "owner": "c", "expires": "2027-01-01", "hosts": "web-01"}]}), ".json")
        self.assertEqual(exc[0]["rule"], "a")
        self.assertEqual(exc[0]["hosts"], ["web-01"])


class OutputTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = self.tmp.name

    def test_files_and_report(self):
        summary = ss.summarise(ARF, self.out, "canary-01", EXC_YAML, TODAY, sha256sums=True)
        for name in ("report.md", "summary.json", "findings.json", "SHA256SUMS"):
            self.assertTrue(os.path.exists(os.path.join(self.out, name)), name)
        self.assertEqual(summary["counts"]["FAIL"], 3)

        with open(os.path.join(self.out, "report.md"), encoding="utf-8") as handle:
            report = handle.read()
        self.assertIn("# OpenSCAP findings: canary-01", report)
        self.assertIn("| Profile | cis_server_l1 |", report)
        self.assertIn("## Expired exceptions", report)
        self.assertIn("AC-6(2), AC-17(a), IA-2", report)
        self.assertIn("Driver \\| usb-storage", report)          # pipe escaped
        self.assertNotIn("Install AIDE", report)                  # PASS rows are not listed
        self.assertNotIn("Ensure SELinux State is Enforcing", report)
        self.assertLess(report.index("## FAIL"), report.index("## WARN"))
        self.assertLess(report.index("## WARN"), report.index("## ACCEPTED"))
        self.assertIn("1 high-severity rule(s) fail without an exception", report)

        with open(os.path.join(self.out, "findings.json"), encoding="utf-8") as handle:
            findings = json.load(handle)
        self.assertIn("package_aide_installed", [f["rule"] for f in findings])

        with open(os.path.join(self.out, "summary.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["host"], "canary-01")
        self.assertEqual(data["expired_exceptions"][0]["rule"], "grub2_password")

    def test_sha256sums_are_correct(self):
        with open(os.path.join(self.out, "arf.xml"), "wb") as handle, open(ARF, "rb") as src:
            handle.write(src.read())
        ss.summarise(os.path.join(self.out, "arf.xml"), self.out, "canary-01", None, TODAY, sha256sums=True)
        with open(os.path.join(self.out, "SHA256SUMS"), encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        names = [line.split("  ", 1)[1] for line in lines]
        self.assertEqual(names, sorted(["arf.xml", "findings.json", "report.md", "summary.json"]))
        for line in lines:
            digest, name = line.split("  ", 1)
            with open(os.path.join(self.out, name), "rb") as handle:
                self.assertEqual(hashlib.sha256(handle.read()).hexdigest(), digest)

    def _cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = ss.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_exit_codes(self):
        common = [ARF, "--out-dir", self.out, "--host", "canary-01", "--today", "2026-11-24"]
        code, out, _ = self._cli(*common, "--exceptions", EXC_YAML)
        self.assertEqual(code, 0)
        self.assertIn("canary-01: FAIL 3, WARN 2, ACCEPTED 2, PASS 2", out)
        self.assertIn("exception for grub2_password expired on 2026-10-31", out)
        self.assertEqual(self._cli(*common, "--fail-on", "high")[0], ss.EXIT_THRESHOLD)
        self.assertEqual(self._cli(*common, "--fail-on", "fail")[0], ss.EXIT_THRESHOLD)
        exc = os.path.join(self.out, "all.json")
        with open(exc, "w", encoding="utf-8") as handle:
            json.dump([{"rule": r, "reason": "x", "owner": "y", "expires": "2027-12-31"}
                       for r in ("grub2_password",)], handle)
        self.assertEqual(self._cli(*common, "--fail-on", "high", "--exceptions", exc)[0], 0)
        code, _, err = self._cli(os.path.join(self.out, "missing.xml"), "--out-dir", self.out)
        self.assertEqual(code, ss.EXIT_ERROR)
        self.assertIn("cannot read", err)


class PatchReportTest(unittest.TestCase):
    REPORT = os.path.join(FIXTURES, "patch-report")

    def _read(self, *parts):
        with open(os.path.join(self.REPORT, *parts), encoding="utf-8") as handle:
            return handle.read()

    def test_parse_list(self):
        adv = patch_report.parse_list(self._read("web-01", "updateinfo-list.txt"))
        self.assertEqual(sorted(adv), ["RHSA-2026:0001", "RHSA-2026:0002", "RHSA-2026:0003", "RHSA-2026:0004"])
        self.assertEqual(len(adv["RHSA-2026:0001"]["packages"]), 2)
        self.assertEqual(adv["RHSA-2026:0002"]["severity"], "Critical")

    def test_parse_info(self):
        info = patch_report.parse_info(self._read("web-01", "updateinfo-info.txt"))
        self.assertEqual(info["RHSA-2026:0001"]["title"], "Important: kernel security update")
        self.assertEqual(info["RHSA-2026:0001"]["cves"], ["CVE-2026-10001", "CVE-2026-10002"])
        self.assertEqual(info["RHSA-2026:0001"]["updated"], "2026-10-01")
        self.assertEqual(info["RHSA-2026:0003"]["issued"], "2026-09-15")

    def test_score(self):
        report = patch_report.build_report(self.REPORT, patch_report.DEFAULT_SLA, set(), TODAY)
        hosts = {h["host"]: h for h in report["hosts"]}
        web = {a["advisory"]: a for a in hosts["web-01"]["advisories"]}
        self.assertTrue(web["RHSA-2026:0001"]["overdue"])          # Important, 54 days
        self.assertEqual(web["RHSA-2026:0001"]["age_days"], 54)
        self.assertFalse(web["RHSA-2026:0002"]["overdue"])         # Critical, 3 days, SLA 7
        self.assertTrue(web["RHSA-2026:0003"]["overdue"])          # issued date wins over updated
        self.assertEqual(web["RHSA-2026:0003"]["due"], "2026-10-16")
        self.assertIsNone(web["RHSA-2026:0004"]["issued"])         # no detail, not scored
        self.assertEqual(hosts["web-01"]["status"], "OVERDUE")
        self.assertEqual(hosts["web-01"]["rings"], ["ring2", "ring2_web"])
        self.assertEqual(hosts["lab-01"]["status"], "WITHIN SLA")
        self.assertEqual(report["totals"]["hosts_overdue"], 1)

    def test_kev_shortens_sla(self):
        kev = patch_report.load_kev(os.path.join(FIXTURES, "kev-sample.txt"))
        report = patch_report.build_report(self.REPORT, patch_report.DEFAULT_SLA, kev, TODAY)
        web = {a["advisory"]: a for h in report["hosts"] if h["host"] == "web-01" for a in h["advisories"]}
        self.assertEqual(web["RHSA-2026:0002"]["sla_days"], 2)
        self.assertTrue(web["RHSA-2026:0002"]["overdue"])

    def test_cli_writes_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            for host in ("web-01", "lab-01"):
                os.makedirs(os.path.join(tmp, host))
                for name in os.listdir(os.path.join(self.REPORT, host)):
                    with open(os.path.join(self.REPORT, host, name), encoding="utf-8") as src, \
                            open(os.path.join(tmp, host, name), "w", encoding="utf-8") as dst:
                        dst.write(src.read())
            with contextlib.redirect_stdout(io.StringIO()):
                code = patch_report.main([tmp, "--today", "2026-11-24", "--fail-on-overdue"])
            self.assertEqual(code, 3)
            with open(os.path.join(tmp, "compliance.md"), encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("**1 of 2 hosts are outside the SLA", text)
            self.assertIn("| web-01 | ring2, ring2_web | OVERDUE |", text)
            self.assertTrue(os.path.exists(os.path.join(tmp, "compliance.json")))


if __name__ == "__main__":
    unittest.main()
