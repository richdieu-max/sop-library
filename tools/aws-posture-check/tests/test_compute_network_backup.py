import unittest
from datetime import timedelta

from fakes import NOW, FakeClient, make_ctx, run, statuses

REGION = "eu-central-1"
CMK = "arn:aws:kms:eu-central-1:111122223333:key/1111aaaa-0000-0000-0000-000000000001"
AWS_EBS = "arn:aws:kms:eu-central-1:111122223333:key/2222bbbb-0000-0000-0000-000000000002"


def instance(iid, name, tokens="required", public_ip=None, profile=True, state="running", vols=("vol-1",)):
    inst = {
        "InstanceId": iid,
        "State": {"Name": state},
        "Tags": [{"Key": "Name", "Value": name}],
        "MetadataOptions": {"HttpTokens": tokens, "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"},
        "BlockDeviceMappings": [{"DeviceName": "/dev/xvda", "Ebs": {"VolumeId": v}} for v in vols],
        "NetworkInterfaces": [],
    }
    if public_ip:
        inst["PublicIpAddress"] = public_ip
    if profile:
        inst["IamInstanceProfile"] = {"Arn": "arn:aws:iam::111122223333:instance-profile/ec2-ssm-cw"}
    return inst


def ec2(instances=(), volumes=(), sgs=(), vpcs=(), flow_logs=()):
    return FakeClient(
        describe_instances={"Reservations": [{"Instances": list(instances)}]},
        describe_volumes={"Volumes": list(volumes)},
        describe_security_groups={"SecurityGroups": list(sgs)},
        describe_vpcs={"Vpcs": list(vpcs)},
        describe_flow_logs={"FlowLogs": list(flow_logs)},
    )


KMS = FakeClient(list_aliases={"Aliases": [{"AliasName": "alias/aws/ebs", "TargetKeyId": AWS_EBS.split("/")[-1]}]})


def ctx_for(**clients):
    return make_ctx(clients, regions=[REGION])


class ComputeTests(unittest.TestCase):
    def test_hardened_instance_passes_everything(self):
        good = instance("i-0a1b2c3d4e5f60001", "web-prd-euc1-01")
        ctx = ctx_for(ec2=ec2([good], [{"VolumeId": "vol-1", "Encrypted": True, "KmsKeyId": CMK}]), kms=KMS,
                      ssm=FakeClient(describe_instance_information={"InstanceInformationList": [
                          {"InstanceId": "i-0a1b2c3d4e5f60001", "PingStatus": "Online"}]}))
        for cid in ("EC2-01", "EC2-02", "EC2-03", "EC2-04", "EC2-05"):
            r = run(ctx, cid, REGION)
            self.assertEqual(statuses(r), ["PASS"], (cid, r[0].detail))
            self.assertEqual(r[0].region, REGION)
            self.assertEqual(r[0].resource_id, "i-0a1b2c3d4e5f60001")

    def test_wizard_default_instance_fails(self):
        bad = instance("i-0bad", "test", tokens="optional", public_ip="203.0.113.10", profile=False)
        ctx = ctx_for(ec2=ec2([bad], [{"VolumeId": "vol-1", "Encrypted": False}]), kms=KMS,
                      ssm=FakeClient(describe_instance_information={"InstanceInformationList": []}))
        self.assertEqual(statuses(run(ctx, "EC2-01", REGION)), ["FAIL"])
        self.assertEqual(statuses(run(ctx, "EC2-02", REGION)), ["FAIL"])
        r = run(ctx, "EC2-03", REGION)
        self.assertEqual(statuses(r), ["FAIL"])
        self.assertIn("203.0.113.10", r[0].detail)
        self.assertEqual(statuses(run(ctx, "EC2-04", REGION)), ["FAIL"])
        self.assertEqual(statuses(run(ctx, "EC2-05", REGION)), ["WARN"])

    def test_aws_managed_key_warns_and_unattached_volume_reported(self):
        inst = instance("i-1", "app")
        vols = [{"VolumeId": "vol-1", "Encrypted": True, "KmsKeyId": AWS_EBS},
                {"VolumeId": "vol-9", "Encrypted": False, "State": "available"}]
        r = run(ctx_for(ec2=ec2([inst], vols), kms=KMS), "EC2-02", REGION)
        self.assertEqual([(x.resource_id, x.status) for x in r], [("i-1", "WARN"), ("vol-9", "FAIL")])

    def test_no_instances(self):
        r = run(ctx_for(ec2=ec2()), "EC2-01", REGION)
        self.assertEqual(statuses(r), ["PASS"])
        self.assertIn("No EC2 instances", r[0].detail)

    def test_terminated_instances_ignored(self):
        gone = instance("i-gone", "old", tokens="optional", state="terminated")
        self.assertEqual(statuses(run(ctx_for(ec2=ec2([gone])), "EC2-01", REGION)), ["PASS"])

    def test_stopped_instance_not_in_ssm_warns(self):
        inst = instance("i-2", "batch", state="stopped")
        ctx = ctx_for(ec2=ec2([inst]), ssm=FakeClient(describe_instance_information={"InstanceInformationList": []}))
        self.assertEqual(statuses(run(ctx, "EC2-04", REGION)), ["WARN"])


def sg(gid, name, perms, egress=()):
    return {"GroupId": gid, "GroupName": name, "VpcId": "vpc-1", "IpPermissions": list(perms),
            "IpPermissionsEgress": list(egress)}


class NetworkTests(unittest.TestCase):
    def test_open_ssh_and_rdp_fail(self):
        groups = [
            sg("sg-ssh", "launch-wizard-1", [{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                                              "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]),
            sg("sg-rdp6", "rdp", [{"IpProtocol": "tcp", "FromPort": 3000, "ToPort": 4000,
                                   "Ipv6Ranges": [{"CidrIpv6": "::/0"}]}]),
            sg("sg-all", "all", [{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]),
            sg("sg-web", "web", [{"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443,
                                  "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]),
            sg("sg-int", "internal", [{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                                       "IpRanges": [{"CidrIp": "10.0.0.0/8"}]}]),
        ]
        r = run(ctx_for(ec2=ec2(sgs=groups)), "NET-01", REGION)
        self.assertEqual(sorted(x.resource_id for x in r if x.status == "FAIL"), ["sg-all", "sg-rdp6", "sg-ssh"])
        self.assertEqual(statuses(r).count("PASS"), 0)

    def test_no_open_ports_passes(self):
        r = run(ctx_for(ec2=ec2(sgs=[sg("sg-web", "web", [])])), "NET-01", REGION)
        self.assertEqual(statuses(r), ["PASS"])

    def test_default_sg(self):
        groups = [sg("sg-d1", "default", [{"IpProtocol": "-1", "UserIdGroupPairs": [{"GroupId": "sg-d1"}]}]),
                  sg("sg-d2", "default", [])]
        r = run(ctx_for(ec2=ec2(sgs=groups)), "NET-02", REGION)
        self.assertEqual([(x.resource_id, x.status) for x in r], [("sg-d1", "WARN"), ("sg-d2", "PASS")])

    def test_default_vpc_and_flow_logs(self):
        vpcs = [{"VpcId": "vpc-def", "IsDefault": True, "CidrBlock": "172.31.0.0/16"},
                {"VpcId": "vpc-prd", "IsDefault": False}]
        logs = [{"ResourceId": "vpc-prd", "FlowLogStatus": "ACTIVE", "TrafficType": "ALL"}]
        ctx = ctx_for(ec2=ec2(vpcs=vpcs, flow_logs=logs))
        self.assertEqual(statuses(run(ctx, "NET-03", REGION)), ["WARN"])
        r = run(ctx, "NET-04", REGION)
        self.assertEqual([(x.resource_id, x.status) for x in r], [("vpc-def", "FAIL"), ("vpc-prd", "PASS")])
        ctx = ctx_for(ec2=ec2(vpcs=[vpcs[1]]))
        self.assertEqual(statuses(run(ctx, "NET-03", REGION)), ["PASS"])


def backup(plans=(), protected=(), vaults=(), plan_detail=None):
    return FakeClient(
        list_backup_plans={"BackupPlansList": list(plans)},
        list_protected_resources={"Results": list(protected)},
        list_backup_vaults={"BackupVaultList": list(vaults)},
        get_backup_plan=plan_detail or {"BackupPlan": {"Rules": []}},
    )


PLAN = {"BackupPlanId": "p1", "BackupPlanName": "plan-prd",
        "BackupPlanArn": "arn:aws:backup:eu-central-1:111122223333:backup-plan:p1"}


class BackupTests(unittest.TestCase):
    def test_no_plan_fails(self):
        ctx = ctx_for(backup=backup())
        self.assertEqual(statuses(run(ctx, "BKP-01", REGION)), ["FAIL"])
        self.assertEqual(statuses(run(ctx, "BKP-04", REGION)), ["FAIL"])

    def test_plan_with_cross_region_copy_passes(self):
        detail = {"BackupPlan": {"Rules": [{"RuleName": "daily", "CopyActions": [
            {"DestinationBackupVaultArn": "arn:aws:backup:eu-west-1:111122223333:backup-vault:vault-dr-euw1"}]}]}}
        ctx = ctx_for(backup=backup(plans=[PLAN], plan_detail=detail))
        self.assertEqual(statuses(run(ctx, "BKP-01", REGION)), ["PASS"])
        r = run(ctx, "BKP-04", REGION)
        self.assertEqual(statuses(r), ["PASS"])
        self.assertIn("eu-west-1", r[0].detail)

    def test_same_region_copy_fails(self):
        detail = {"BackupPlan": {"Rules": [{"CopyActions": [
            {"DestinationBackupVaultArn": "arn:aws:backup:eu-central-1:111122223333:backup-vault:other"}]}]}}
        ctx = ctx_for(backup=backup(plans=[PLAN], plan_detail=detail))
        self.assertEqual(statuses(run(ctx, "BKP-04", REGION)), ["FAIL"])

    def test_protected_instances(self):
        insts = [instance("i-new", "a"), instance("i-old", "b"), instance("i-none", "c")]
        protected = [
            {"ResourceArn": "arn:aws:ec2:eu-central-1:111122223333:instance/i-new", "ResourceType": "EC2",
             "LastBackupTime": NOW - timedelta(hours=5)},
            {"ResourceArn": "arn:aws:ec2:eu-central-1:111122223333:instance/i-old", "ResourceType": "EC2",
             "LastBackupTime": NOW - timedelta(days=5)},
        ]
        r = run(ctx_for(ec2=ec2(insts), backup=backup(protected=protected)), "BKP-02", REGION)
        self.assertEqual([(x.resource_id, x.status) for x in r],
                         [("i-new", "PASS"), ("i-old", "WARN"), ("i-none", "FAIL")])

    def test_vault_lock(self):
        vaults = [
            {"BackupVaultName": "vault-prd-euc1", "Locked": True, "MinRetentionDays": 7, "MaxRetentionDays": 400,
             "NumberOfRecoveryPoints": 10},
            {"BackupVaultName": "Default", "Locked": False, "NumberOfRecoveryPoints": 3},
            {"BackupVaultName": "empty", "Locked": False, "NumberOfRecoveryPoints": 0},
        ]
        r = run(ctx_for(backup=backup(vaults=vaults)), "BKP-03", REGION)
        self.assertEqual(statuses(r), ["PASS", "FAIL", "WARN"])
        self.assertIn("governance", r[0].detail)


if __name__ == "__main__":
    unittest.main()
