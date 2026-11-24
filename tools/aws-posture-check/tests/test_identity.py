import unittest

from fakes import FakeClient, FakeClientError, make_ctx, run, statuses

HEADER = ("user,arn,password_enabled,password_last_used,mfa_active,access_key_1_active,"
          "access_key_1_last_rotated,access_key_1_last_used_date,access_key_2_active,"
          "access_key_2_last_rotated,access_key_2_last_used_date")


def report(*rows):
    root = "<root_account>,arn:aws:iam::111122223333:root,not_supported,2025-06-01T00:00:00+00:00,true,false,N/A,N/A,false,N/A,N/A"
    return ("\n".join((HEADER, root) + rows) + "\n").encode()


def iam(summary=None, content=None, policy=None, virtual=None, **extra):
    ops = dict(
        get_account_summary={"SummaryMap": summary or {"AccountMFAEnabled": 1, "AccountAccessKeysPresent": 0}},
        generate_credential_report={"State": "COMPLETE"},
        get_credential_report={"Content": content if content is not None else report()},
        get_account_password_policy=policy if policy is not None else
        {"PasswordPolicy": {"MinimumPasswordLength": 14, "PasswordReusePrevention": 24}},
        list_virtual_mfa_devices={"VirtualMFADevices": virtual or []},
    )
    ops.update(extra)
    return FakeClient(**ops)


class RootTests(unittest.TestCase):
    def test_root_mfa_pass_and_fail(self):
        self.assertEqual(statuses(run(make_ctx({"iam": iam()}), "IAM-01")), ["PASS"])
        ctx = make_ctx({"iam": iam(summary={"AccountMFAEnabled": 0})})
        self.assertEqual(statuses(run(ctx, "IAM-01")), ["FAIL"])

    def test_root_access_keys(self):
        self.assertEqual(statuses(run(make_ctx({"iam": iam()}), "IAM-03")), ["PASS"])
        ctx = make_ctx({"iam": iam(summary={"AccountMFAEnabled": 1, "AccountAccessKeysPresent": 1})})
        r = run(ctx, "IAM-03")
        self.assertEqual(statuses(r), ["FAIL"])
        self.assertEqual(r[0].region, "global")
        self.assertEqual(r[0].cis, "1.4")

    def test_root_virtual_mfa_warns(self):
        virtual = [{"SerialNumber": "arn:aws:iam::111122223333:mfa/root-account-mfa-device",
                    "User": {"Arn": "arn:aws:iam::111122223333:root"}}]
        self.assertEqual(statuses(run(make_ctx({"iam": iam(virtual=virtual)}), "IAM-02")), ["WARN"])
        self.assertEqual(statuses(run(make_ctx({"iam": iam()}), "IAM-02")), ["PASS"])

    def test_root_recent_use(self):
        # Root last used 2025-06-01, NOW is 2026-01-15: old use passes.
        self.assertEqual(statuses(run(make_ctx({"iam": iam()}), "IAM-04")), ["PASS"])
        recent = report().decode().replace("2025-06-01", "2026-01-10").encode()
        self.assertEqual(statuses(run(make_ctx({"iam": iam(content=recent)}), "IAM-04")), ["WARN"])

    def test_access_denied_is_error_not_crash(self):
        ctx = make_ctx({"iam": iam(get_account_summary=FakeClientError("AccessDenied", "GetAccountSummary"))})
        r = run(ctx, "IAM-01")
        self.assertEqual(statuses(r), ["ERROR"])
        self.assertIn("Access denied calling GetAccountSummary", r[0].detail)


class PasswordPolicyTests(unittest.TestCase):
    def test_strong_policy_passes(self):
        self.assertEqual(statuses(run(make_ctx({"iam": iam()}), "IAM-05")), ["PASS"])

    def test_weak_policy_fails(self):
        weak = {"PasswordPolicy": {"MinimumPasswordLength": 8, "PasswordReusePrevention": 24}}
        r = run(make_ctx({"iam": iam(policy=weak)}), "IAM-05")
        self.assertEqual(statuses(r), ["FAIL"])
        self.assertIn("minimum length 8", r[0].detail)

    def test_missing_policy_with_and_without_console_users(self):
        none = FakeClientError("NoSuchEntity", "GetAccountPasswordPolicy")
        self.assertEqual(statuses(run(make_ctx({"iam": iam(policy=none)}), "IAM-05")), ["WARN"])
        user = "alice,arn:aws:iam::111122223333:user/alice,true,N/A,true,false,N/A,N/A,false,N/A,N/A"
        ctx = make_ctx({"iam": iam(policy=none, content=report(user))})
        self.assertEqual(statuses(run(ctx, "IAM-05")), ["FAIL"])


class UserTests(unittest.TestCase):
    def test_console_user_without_mfa_fails(self):
        rows = ("ann,arn:aws:iam::111122223333:user/ann,true,N/A,false,false,N/A,N/A,false,N/A,N/A",
                "bob,arn:aws:iam::111122223333:user/bob,true,N/A,true,false,N/A,N/A,false,N/A,N/A",
                "svc,arn:aws:iam::111122223333:user/svc,false,N/A,false,false,N/A,N/A,false,N/A,N/A")
        r = run(make_ctx({"iam": iam(content=report(*rows))}), "IAM-07")
        self.assertEqual(sorted((x.resource_id.split("/")[-1], x.status) for x in r),
                         [("ann", "FAIL"), ("bob", "PASS")])

    def test_no_console_users_passes(self):
        self.assertEqual(statuses(run(make_ctx({"iam": iam()}), "IAM-07")), ["PASS"])

    def test_access_key_age(self):
        rows = (
            "old,arn:aws:iam::111122223333:user/old,false,N/A,false,true,2025-01-01T00:00:00+00:00,2026-01-14T00:00:00+00:00,false,N/A,N/A",
            "idle,arn:aws:iam::111122223333:user/idle,false,N/A,false,true,2025-11-01T00:00:00+00:00,N/A,false,N/A,N/A",
            "ok,arn:aws:iam::111122223333:user/ok,false,N/A,false,true,2026-01-01T00:00:00+00:00,2026-01-14T00:00:00+00:00,false,N/A,N/A",
        )
        r = run(make_ctx({"iam": iam(content=report(*rows))}), "IAM-08")
        got = {x.resource_id.split("/")[-1].split(" ")[0]: x.status for x in r}
        self.assertEqual(got, {"old": "FAIL", "idle": "WARN", "ok": "PASS"})

    def test_credential_report_waits_until_complete(self):
        states = iter([{"State": "STARTED"}, {"State": "INPROGRESS"}, {"State": "COMPLETE"}])
        client = iam(generate_credential_report=lambda: next(states))
        ctx = make_ctx({"iam": client})
        self.assertEqual(statuses(run(ctx, "IAM-07")), ["PASS"])
        self.assertEqual(sum(1 for c in client.calls if c[0] == "generate_credential_report"), 3)
        # Cached: a second check does not generate the report again.
        run(ctx, "IAM-08")
        self.assertEqual(sum(1 for c in client.calls if c[0] == "generate_credential_report"), 3)


class IdentityCenterTests(unittest.TestCase):
    def test_instance_present(self):
        sso = FakeClient(list_instances={"Instances": [{"InstanceArn": "arn:aws:sso:::instance/ssoins-1", "Status": "ACTIVE"}]})
        r = run(make_ctx({"iam": iam(), "sso-admin": sso}, regions=["eu-central-1"]), "IAM-06")
        self.assertEqual(statuses(r), ["PASS"])
        self.assertEqual(r[0].region, "eu-central-1")

    def test_no_instance_warns(self):
        sso = FakeClient(list_instances={"Instances": []})
        self.assertEqual(statuses(run(make_ctx({"sso-admin": sso}), "IAM-06")), ["WARN"])


if __name__ == "__main__":
    unittest.main()
