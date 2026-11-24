"""The only module that touches boto3. It is imported lazily so tests run without it."""

from . import TOOL_NAME, __version__


class MissingDependency(RuntimeError):
    pass


def make_client_factory(profile=None):
    """Return (client_factory, default_region, library_versions) for a boto3 session."""
    try:
        import boto3
        import botocore
        from botocore.config import Config
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise MissingDependency("boto3 is required: pip install boto3 (%s)" % exc)

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    config = Config(
        retries={"max_attempts": 10, "mode": "adaptive"},
        user_agent_extra="%s/%s" % (TOOL_NAME, __version__),
        connect_timeout=10,
        read_timeout=60,
    )

    def factory(service, region):
        return session.client(service, region_name=region, config=config)

    versions = {"boto3": boto3.__version__, "botocore": botocore.__version__}
    return factory, session.region_name, versions
