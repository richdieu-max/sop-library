import unittest

from fakes import FakeClient, FakeClientError, make_ctx, run, statuses

from aws_posture_check.checks.logging_checks import management_coverage

TRAIL = {
    "Name": "account-trail",
    "TrailARN": "arn:aws:cloudtrail:us-east-1:111122223333:trail/account-trail",
    "HomeRegion": "us-east-1",
    "IsMultiRegionTrail": True,
    "LogFileValidationEnabled": True,
    "KmsKeyId": "arn:aws:kms:us-east-1:111122223333:key/abcd",
}


def cloudtrail(trails=None, logging=True, selectors=None):
    return FakeClient(
        describe_trails={"trailList": [TRAIL] if trails is None else trails},
        get_trail_status={"IsLogging": logging},
        get_event_selectors=selectors or {"EventSelectors": [{"ReadWriteType": "All", "IncludeManagementEvents": True}]},
    )


class CloudTrailTests(unittest.TestCase):
    def test_good_trail_passes_all(self):
        ctx = make_ctx({"cloudtrail": cloudtrail()})
        for cid in ("LOG-01", "LOG-02", "LOG-03"):
            self.assertEqual(statuses(run(ctx, cid)), ["PASS"], cid)

    def test_no_multi_region_trail_fails(self):
        single = dict(TRAIL, IsMultiRegionTrail=False)
        ctx = make_ctx({"cloudtrail": cloudtrail(trails=[single])})
        for cid in ("LOG-01", "LOG-02", "LOG-03"):
            self.assertEqual(statuses(run(ctx, cid)), ["FAIL"], cid)

    def test_stopped_trail_fails(self):
        self.assertEqual(statuses(run(make_ctx({"cloudtrail": cloudtrail(logging=False)}), "LOG-01")), ["FAIL"])

    def test_write_only_trail_warns(self):
        sel = {"EventSelectors": [{"ReadWriteType": "WriteOnly", "IncludeManagementEvents": True}]}
        self.assertEqual(statuses(run(make_ctx({"cloudtrail": cloudtrail(selectors=sel)}), "LOG-01")), ["WARN"])

    def test_validation_off_and_no_kms(self):
        t = dict(TRAIL, LogFileValidationEnabled=False, KmsKeyId=None)
        ctx = make_ctx({"cloudtrail": cloudtrail(trails=[t])})
        self.assertEqual(statuses(run(ctx, "LOG-02")), ["FAIL"])
        self.assertEqual(statuses(run(ctx, "LOG-03")), ["WARN"])

    def test_status_error_is_per_trail(self):
        ct = FakeClient(describe_trails={"trailList": [TRAIL]},
                        get_trail_status=FakeClientError("AccessDeniedException", "GetTrailStatus"),
                        get_event_selectors={})
        r = run(make_ctx({"cloudtrail": ct}), "LOG-01")
        self.assertEqual(statuses(r), ["ERROR"])
        self.assertEqual(r[0].resource_id, TRAIL["TrailARN"])

    def test_management_coverage_advanced_selectors(self):
        adv = {"AdvancedEventSelectors": [{"FieldSelectors": [{"Field": "eventCategory", "Equals": ["Management"]}]}]}
        self.assertEqual(management_coverage(adv), "all")
        ro = {"AdvancedEventSelectors": [{"FieldSelectors": [
            {"Field": "eventCategory", "Equals": ["Management"]}, {"Field": "readOnly", "Equals": ["true"]}]}]}
        self.assertEqual(management_coverage(ro), "partial")
        self.assertEqual(management_coverage({}), "none")


class ConfigTests(unittest.TestCase):
    def cfg(self, recorders, status):
        return FakeClient(describe_configuration_recorders={"ConfigurationRecorders": recorders},
                          describe_configuration_recorder_status={"ConfigurationRecordersStatus": status})

    def test_recording_all_passes(self):
        c = self.cfg([{"name": "default", "recordingGroup": {"allSupported": True}}],
                     [{"name": "default", "recording": True, "lastStatus": "SUCCESS"}])
        self.assertEqual(statuses(run(make_ctx({"config": c}), "LOG-04")), ["PASS"])

    def test_not_recording_fails_and_missing_fails(self):
        c = self.cfg([{"name": "default"}], [{"name": "default", "recording": False}])
        self.assertEqual(statuses(run(make_ctx({"config": c}), "LOG-04")), ["FAIL"])
        self.assertEqual(statuses(run(make_ctx({"config": self.cfg([], [])}), "LOG-04")), ["FAIL"])

    def test_partial_recording_warns(self):
        c = self.cfg([{"name": "default", "recordingGroup": {"allSupported": False, "resourceTypes": ["AWS::EC2::Instance"]}}],
                     [{"name": "default", "recording": True}])
        self.assertEqual(statuses(run(make_ctx({"config": c}), "LOG-04")), ["WARN"])

    def test_runs_per_region(self):
        from aws_posture_check.core import run_checks, select_checks
        good = self.cfg([{"name": "default"}], [{"name": "default", "recording": True}])
        ctx = make_ctx({("config", "eu-central-1"): good, ("config", "eu-west-1"): self.cfg([], [])},
                       regions=["eu-central-1", "eu-west-1"])
        r = run_checks(ctx, select_checks(check_ids=["LOG-04"]))
        self.assertEqual([(x.region, x.status) for x in r], [("eu-central-1", "PASS"), ("eu-west-1", "FAIL")])


class ThreatTests(unittest.TestCase):
    def test_guardduty(self):
        gd = FakeClient(list_detectors={"DetectorIds": ["d1"]}, get_detector={"Status": "ENABLED"})
        self.assertEqual(statuses(run(make_ctx({"guardduty": gd}), "THR-01")), ["PASS"])
        gd = FakeClient(list_detectors={"DetectorIds": []})
        self.assertEqual(statuses(run(make_ctx({"guardduty": gd}), "THR-01")), ["FAIL"])
        gd = FakeClient(list_detectors={"DetectorIds": ["d1"]}, get_detector={"Status": "DISABLED"})
        self.assertEqual(statuses(run(make_ctx({"guardduty": gd}), "THR-01")), ["FAIL"])

    def test_security_hub(self):
        arn = "arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0"
        sh = FakeClient(describe_hub={"HubArn": "arn:aws:securityhub:us-east-1:111122223333:hub/default"},
                        get_enabled_standards={"StandardsSubscriptions": [{"StandardsArn": arn, "StandardsStatus": "READY"}]})
        self.assertEqual(statuses(run(make_ctx({"securityhub": sh}), "THR-02")), ["PASS"])
        sh = FakeClient(describe_hub=FakeClientError("InvalidAccessException", "DescribeHub"))
        self.assertEqual(statuses(run(make_ctx({"securityhub": sh}), "THR-02")), ["FAIL"])
        sh = FakeClient(describe_hub=FakeClientError("AccessDeniedException", "DescribeHub"))
        self.assertEqual(statuses(run(make_ctx({"securityhub": sh}), "THR-02")), ["ERROR"])
        sh = FakeClient(describe_hub={"HubArn": "h"}, get_enabled_standards={"StandardsSubscriptions": []})
        self.assertEqual(statuses(run(make_ctx({"securityhub": sh}), "THR-02")), ["WARN"])

    def test_access_analyzer(self):
        aa = FakeClient(list_analyzers={"analyzers": [{"arn": "a1", "type": "ACCOUNT", "status": "ACTIVE"}]})
        self.assertEqual(statuses(run(make_ctx({"accessanalyzer": aa}), "THR-03")), ["PASS"])
        aa = FakeClient(list_analyzers={"analyzers": [{"arn": "u1", "type": "ACCOUNT_UNUSED_ACCESS", "status": "ACTIVE"}]})
        self.assertEqual(statuses(run(make_ctx({"accessanalyzer": aa}), "THR-03")), ["FAIL"])


class StorageTests(unittest.TestCase):
    def test_bpa(self):
        on = {k: True for k in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")}
        s3c = FakeClient(get_public_access_block={"PublicAccessBlockConfiguration": on})
        self.assertEqual(statuses(run(make_ctx({"s3control": s3c}), "STO-01")), ["PASS"])
        self.assertEqual(s3c.calls[0][1], {"AccountId": "111122223333"})
        s3c = FakeClient(get_public_access_block={"PublicAccessBlockConfiguration": dict(on, BlockPublicPolicy=False)})
        r = run(make_ctx({"s3control": s3c}), "STO-01")
        self.assertEqual(statuses(r), ["FAIL"])
        self.assertIn("BlockPublicPolicy", r[0].detail)
        s3c = FakeClient(get_public_access_block=FakeClientError("NoSuchPublicAccessBlockConfiguration"))
        self.assertEqual(statuses(run(make_ctx({"s3control": s3c}), "STO-01")), ["FAIL"])

    def test_ebs_default(self):
        ec2 = FakeClient(get_ebs_encryption_by_default={"EbsEncryptionByDefault": True})
        self.assertEqual(statuses(run(make_ctx({"ec2": ec2}), "STO-02")), ["PASS"])
        ec2 = FakeClient(get_ebs_encryption_by_default={"EbsEncryptionByDefault": False})
        self.assertEqual(statuses(run(make_ctx({"ec2": ec2}), "STO-02")), ["FAIL"])


if __name__ == "__main__":
    unittest.main()
