"""Fake AWS clients for unit tests. No boto3, no network."""

import os
import sys
from datetime import datetime, timezone

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from aws_posture_check.core import Context, select_checks, run_check  # noqa: E402

ACCOUNT = "111122223333"
NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


class FakeClientError(Exception):
    """Looks like botocore.exceptions.ClientError to the code under test."""

    def __init__(self, code, operation="FakeOperation", message=""):
        super().__init__("%s: %s" % (code, message))
        self.response = {"Error": {"Code": code, "Message": message or code}}
        self.operation_name = operation


class FakeClient(object):
    """Each keyword is an operation: a dict response, an exception, or a callable(**kwargs)."""

    def __init__(self, **operations):
        self._ops = operations
        self.calls = []

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._ops:
            raise AttributeError("fake client has no operation %s" % name)
        value = self._ops[name]

        def call(**kwargs):
            self.calls.append((name, kwargs))
            result = value(**kwargs) if callable(value) else value
            if isinstance(result, Exception):
                raise result
            return result

        return call


def make_ctx(clients, regions=("us-east-1",), home_region=None):
    """clients maps service or (service, region) to a FakeClient."""

    def factory(service, region):
        if (service, region) in clients:
            return clients[(service, region)]
        if service in clients:
            return clients[service]
        raise FakeClientError("AccessDeniedException", "Fake%s" % service)

    return Context(factory, ACCOUNT, list(regions), home_region=home_region, caller_arn=
                   "arn:aws:sts::%s:assumed-role/auditor/test" % ACCOUNT, now=NOW, sleep=lambda s: None)


def run(ctx, check_id, region=None):
    check = select_checks(check_ids=[check_id])[0]
    return run_check(ctx, check, region or ctx.home_region)


def statuses(results):
    return [r.status for r in results]
