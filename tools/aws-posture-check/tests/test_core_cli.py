import contextlib
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

from fakes import ACCOUNT, NOW, FakeClient, FakeClientError, make_ctx

from aws_posture_check import cli
from aws_posture_check.core import (
    AREAS, FAIL, PASS, ReadOnlyClient, ReadOnlyViolation, Result, exit_code_for, normalise_area,
    run_check, select_checks,
)

TOOL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(TOOL_DIR, "src", "aws_posture_check")


class RegistryTests(unittest.TestCase):
    def test_every_area_has_checks_and_ids_are_unique(self):
        checks = select_checks()
        self.assertEqual({c.area for c in checks}, set(AREAS))
        ids = [c.check_id for c in checks]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(checks), 27)

    def test_every_check_has_nist_mapping_and_remediation(self):
        for c in select_checks():
            self.assertTrue(c.nist, c.check_id)
            self.assertTrue(all(re.match(r"^[A-Z]{2}-\d+(\(\d+\))?$", n) for n in c.nist), c.nist)
            self.assertTrue(c.remediation, c.check_id)

    def test_area_names_from_the_sops(self):
        self.assertEqual(normalise_area("Threat protection"), "Threat protection")
        self.assertEqual(normalise_area("threat-protection"), "Threat protection")
        self.assertEqual(normalise_area("compute"), "Compute")
        with self.assertRaises(ValueError):
            normalise_area("Databases")

    def test_select_by_area_and_id(self):
        self.assertTrue(all(c.area == "Backup" for c in select_checks(["Backup"])))
        self.assertEqual([c.check_id for c in select_checks(check_ids=["iam-01"])], ["IAM-01"])
        with self.assertRaises(ValueError):
            select_checks(check_ids=["NOPE-99"])


class ReadOnlyTests(unittest.TestCase):
    def test_guard_blocks_mutating_calls(self):
        fake = FakeClient(describe_instances={}, create_trail={}, put_public_access_block={})
        guarded = ReadOnlyClient(fake, "ec2")
        guarded.describe_instances()
        for name in ("create_trail", "put_public_access_block", "delete_detector", "start_logging",
                     "update_trail", "modify_instance_metadata_options", "enable_security_hub", "get_waiter"):
            with self.assertRaises(ReadOnlyViolation, msg=name):
                getattr(guarded, name)
        with self.assertRaises(ReadOnlyViolation):
            guarded.get_paginator("delete_flow_logs")
        self.assertEqual([c[0] for c in fake.calls], ["describe_instances"])

    def test_generate_credential_report_is_the_only_extra(self):
        guarded = ReadOnlyClient(FakeClient(generate_credential_report={"State": "COMPLETE"}), "iam")
        self.assertEqual(guarded.generate_credential_report(), {"State": "COMPLETE"})

    def test_source_calls_only_read_operations(self):
        # Every API operation named in the checks is Describe, Get, List or generate_credential_report.
        call_re = re.compile(r"\.\s*([a-z][a-z0-9_]+)\(")
        string_op_re = re.compile(r"\"((?:describe|get|list|create|put|delete|update|start|stop|enable|disable|modify|"
                                  r"associate|revoke|authorize|tag|untag|attach|detach|run|terminate)_[a-z0-9_]+)\"")
        bad = re.compile(r"^(create|put|delete|update|start|stop|enable|disable|modify|associate|revoke|authorize|"
                         r"tag|untag|attach|detach|run|terminate|copy|restore|import|export|register|deregister)_")
        allowed_python = {"run_check", "run_checks", "register"}
        checks_dir = os.path.join(SRC_DIR, "checks")
        for name in os.listdir(checks_dir):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(checks_dir, name), encoding="utf-8") as fh:
                text = fh.read()
            ops = set(call_re.findall(text)) | set(string_op_re.findall(text))
            offenders = sorted(o for o in ops if bad.match(o) and o not in allowed_python)
            self.assertEqual(offenders, [], name)

    def test_unexpected_exception_becomes_error(self):
        check = select_checks(check_ids=["STO-02"])[0]
        ctx = make_ctx({"ec2": FakeClient(get_ebs_encryption_by_default=lambda: 1 / 0)})
        r = run_check(ctx, check, "us-east-1")
        self.assertEqual([x.status for x in r], ["ERROR"])
        self.assertIn("ZeroDivisionError", r[0].detail)

    def test_missing_client_permission_is_error(self):
        r = run_check(make_ctx({}), select_checks(check_ids=["THR-01"])[0], "us-east-1")
        self.assertEqual(r[0].status, "ERROR")


def _r(status):
    return Result("X-01", "Identity", "t", status, "global", "r", "d", "fix", ("AC-2",), "")


class ExitCodeTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(exit_code_for([_r(PASS)], "fail"), 0)
        self.assertEqual(exit_code_for([_r(PASS), _r(FAIL)], "fail"), 1)
        self.assertEqual(exit_code_for([_r("WARN")], "fail"), 0)
        self.assertEqual(exit_code_for([_r("WARN")], "warn"), 1)
        self.assertEqual(exit_code_for([_r("ERROR")], "warn"), 1)
        self.assertEqual(exit_code_for([_r(FAIL)], "never"), 0)


def full_account(region="us-east-1"):
    """A fake account that passes the SOP-AWS-001 baseline, with one bad security group."""
    report = ("user,arn,password_enabled,password_last_used,mfa_active,access_key_1_active,access_key_1_last_rotated,"
              "access_key_1_last_used_date,access_key_2_active,access_key_2_last_rotated,access_key_2_last_used_date\n"
              "<root_account>,arn:aws:iam::%s:root,not_supported,N/A,true,false,N/A,N/A,false,N/A,N/A\n" % ACCOUNT)
    on = {k: True for k in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")}
    return {
        "sts": FakeClient(get_caller_identity={"Account": ACCOUNT,
                                               "Arn": "arn:aws:sts::%s:assumed-role/auditor/session" % ACCOUNT}),
        "iam": FakeClient(get_account_summary={"SummaryMap": {"AccountMFAEnabled": 1, "AccountAccessKeysPresent": 0}},
                          list_virtual_mfa_devices={"VirtualMFADevices": []},
                          generate_credential_report={"State": "COMPLETE"},
                          get_credential_report={"Content": report.encode()},
                          get_account_password_policy=FakeClientError("NoSuchEntity")),
        "sso-admin": FakeClient(list_instances={"Instances": [{"InstanceArn": "arn:aws:sso:::instance/ssoins-1"}]}),
        "cloudtrail": FakeClient(
            describe_trails={"trailList": [{"Name": "account-trail", "HomeRegion": region, "IsMultiRegionTrail": True,
                                            "LogFileValidationEnabled": True,
                                            "TrailARN": "arn:aws:cloudtrail:%s:%s:trail/account-trail" % (region, ACCOUNT)}]},
            get_trail_status={"IsLogging": True},
            get_event_selectors={"EventSelectors": [{"ReadWriteType": "All", "IncludeManagementEvents": True}]}),
        "config": FakeClient(describe_configuration_recorders={"ConfigurationRecorders": [{"name": "default"}]},
                             describe_configuration_recorder_status={"ConfigurationRecordersStatus": [
                                 {"name": "default", "recording": True}]}),
        "guardduty": FakeClient(list_detectors={"DetectorIds": ["d1"]}, get_detector={"Status": "ENABLED"}),
        "securityhub": FakeClient(describe_hub={"HubArn": "hub"}, get_enabled_standards={"StandardsSubscriptions": [
            {"StandardsArn": "arn:aws:securityhub:::standards/cis", "StandardsStatus": "READY"}]}),
        "accessanalyzer": FakeClient(list_analyzers={"analyzers": [{"arn": "a", "type": "ACCOUNT", "status": "ACTIVE"}]}),
        "s3control": FakeClient(get_public_access_block={"PublicAccessBlockConfiguration": on}),
        "ec2": FakeClient(get_ebs_encryption_by_default={"EbsEncryptionByDefault": True},
                          describe_instances={"Reservations": []}, describe_volumes={"Volumes": []},
                          describe_vpcs={"Vpcs": [{"VpcId": "vpc-1", "IsDefault": False}]},
                          describe_flow_logs={"FlowLogs": [{"ResourceId": "vpc-1", "FlowLogStatus": "ACTIVE"}]},
                          describe_security_groups={"SecurityGroups": [
                              {"GroupId": "sg-0bbbbbbbbbbbbbbb1", "GroupName": "launch-wizard-1", "VpcId": "vpc-1",
                               "IpPermissions": [{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                                                  "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]}]}),
        "backup": FakeClient(list_backup_plans={"BackupPlansList": []}, list_backup_vaults={"BackupVaultList": []},
                             list_protected_resources={"Results": []}),
    }


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def invoke(self, argv, clients=None):
        clients = clients or full_account()
        out, err = io.StringIO(), io.StringIO()

        def factory(service, region):
            if service not in clients:
                raise FakeClientError("AccessDenied", service)
            return clients[service]

        code = cli.main(argv, client_factory=factory, default_region="us-east-1", stdout=out, stderr=err, now=NOW)
        return code, out.getvalue(), err.getvalue()

    def test_sop_aws_001_verify_command(self):
        out_dir = os.path.join(self.tmp, "ev")
        code, out, _ = self.invoke(["--profile", "auditor", "--regions", "us-east-1", "--areas", "Identity", "Logging",
                                    "Threat protection", "Storage", "--fail-on", "fail", "--out", out_dir, "-q"])
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(os.listdir(out_dir)), ["SHA256SUMS", "report.md", "results.csv", "results.json"])
        doc = json.loads(read(os.path.join(out_dir, "results.json")))
        self.assertEqual(doc["run"]["account_id"], ACCOUNT)
        self.assertIn("assumed-role/auditor", doc["run"]["caller_arn"])
        self.assertEqual(doc["run"]["regions"], ["us-east-1"])
        self.assertEqual(doc["run"]["areas"], ["Identity", "Logging", "Threat protection", "Storage"])
        self.assertEqual(doc["run"]["started_utc"], "2026-01-15T12:00:00Z")
        self.assertTrue(doc["run"]["tool_version"])
        by_id = {}
        for r in doc["results"]:
            by_id.setdefault(r["check_id"], set()).add(r["status"])
        for cid in ("IAM-01", "IAM-03", "LOG-01", "THR-01", "STO-01"):
            self.assertEqual(by_id[cid], {"PASS"}, cid)
        self.assertNotIn("NET-01", by_id)

    def test_sop_aws_002_verify_command_and_fail_exit(self):
        out_dir = os.path.join(self.tmp, "ev2")
        code, out, _ = self.invoke(["--regions", "eu-central-1", "--areas", "Compute", "Network", "Backup",
                                    "--out", out_dir, "-q"])
        self.assertEqual(code, 1)  # the open SSH security group and the missing backup plan
        self.assertIn("FAIL  NET-01", out)
        report = read(os.path.join(out_dir, "report.md"))
        self.assertLess(report.index("## FAIL"), report.index("## WARN"))
        self.assertIn("| Network |", report)
        rows = list(csv.DictReader(io.StringIO(read(os.path.join(out_dir, "results.csv")))))
        self.assertTrue(all(r["region"] == "eu-central-1" for r in rows))
        self.assertIn("SC-7", [r for r in rows if r["check_id"] == "NET-01"][0]["nist_800_53"])
        code, _, _ = self.invoke(["--regions", "eu-central-1", "--areas", "Network", "--fail-on", "never",
                                  "--out", out_dir, "-q"])
        self.assertEqual(code, 0)

    def test_sha256sums_match(self):
        out_dir = os.path.join(self.tmp, "ev3")
        self.invoke(["--areas", "Storage", "--out", out_dir, "-q"])
        lines = read(os.path.join(out_dir, "SHA256SUMS")).splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines:
            digest, name = line.split("  ")
            with open(os.path.join(out_dir, name), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), digest)

    def test_default_out_dir_and_json_format(self):
        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            code, out, _ = self.invoke(["--areas", "Storage", "--format", "json", "-q"])
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["run"]["account_id"], ACCOUNT)
        self.assertEqual(os.listdir(os.path.join(self.tmp, "evidence")),
                         ["aws-posture-%s-20260115T120000Z" % ACCOUNT])

    def test_access_denied_everywhere_never_crashes(self):
        clients = {"sts": full_account()["sts"]}
        out_dir = os.path.join(self.tmp, "ev4")
        code, out, _ = self.invoke(["--out", out_dir, "-q"], clients=clients)
        self.assertEqual(code, 0)  # ERROR does not trip --fail-on fail
        doc = json.loads(read(os.path.join(out_dir, "results.json")))
        self.assertTrue(doc["results"])
        self.assertEqual({r["status"] for r in doc["results"]}, {"ERROR"})
        code, _, _ = self.invoke(["--out", out_dir, "-q", "--fail-on", "warn"], clients=clients)
        self.assertEqual(code, 1)

    def test_bad_credentials_exit_2(self):
        clients = {"sts": FakeClient(get_caller_identity=FakeClientError("InvalidClientTokenId"))}
        code, _, err = self.invoke(["--out", os.path.join(self.tmp, "x"), "-q"], clients=clients)
        self.assertEqual(code, 2)
        self.assertIn("cannot identify the caller", err)

    def test_bad_area_and_region_exit_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                cli.build_parser().parse_args(["--areas", "Databases"])
            self.assertEqual(cm.exception.code, 2)
            with self.assertRaises(SystemExit):
                cli.build_parser().parse_args(["--regions", "frankfurt"])
        self.assertIn("not a region name", err.getvalue())

    def test_list_checks_needs_no_aws(self):
        out = io.StringIO()
        self.assertEqual(cli.main(["--list-checks"], stdout=out), 0)
        self.assertIn("EC2-01", out.getvalue())

    def test_boto3_not_imported(self):
        self.assertNotIn("boto3", sys.modules)


class StyleTests(unittest.TestCase):
    def test_no_em_or_en_dashes(self):
        for root, _, files in os.walk(TOOL_DIR):
            if "__pycache__" in root or "egg-info" in root:
                continue
            for name in files:
                if name.endswith((".py", ".md", ".toml", ".json", ".txt")) or name == "LICENSE":
                    with open(os.path.join(root, name), encoding="utf-8") as fh:
                        text = fh.read()
                    self.assertNotIn(chr(0x2014), text, name)
                    self.assertNotIn(chr(0x2013), text, name)


if __name__ == "__main__":
    unittest.main()
