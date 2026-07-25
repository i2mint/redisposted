"""Pytest configuration for redisposted.

Lets the suite stay green **without a live Redis**. redisposted is a Redis
message-broker layer, so its pub/sub tests need a reachable server. When none is
reachable (e.g. a local run with no Redis, or CI without the redis service) the
Redis-dependent tests are *deselected* rather than left to fail; when a server
is available (CI's ``services: redis`` container, or local dev) they run
normally. The signature test needs no server and always runs.

Mirrors the mongodol conftest: *deselection* (not a skip marker) keeps CI green
without a server and is robust across pytest versions.
"""

import os


def _redis_available(*, timeout=0.5):
    """Return ``True`` iff a Redis server answers a ping quickly.

    Probes ``REDISPOSTED_REDIS_HOST``:``REDISPOSTED_REDIS_PORT`` (default
    ``localhost:6379``), matching the test fixture's connection target.
    """
    host = os.environ.get("REDISPOSTED_REDIS_HOST", "localhost")
    port = int(os.environ.get("REDISPOSTED_REDIS_PORT", "6379"))
    try:
        from redis import Redis

        client = Redis(host=host, port=port, socket_connect_timeout=timeout)
        try:
            return bool(client.ping())
        finally:
            client.close()
    except Exception:
        return False


def _requires_redis(item):
    """Whether a collected item needs a live Redis to run.

    Any item that uses the ``broker`` fixture connects to Redis; items that
    don't (e.g. the signature test) run without a server.
    """
    return "broker" in getattr(item, "fixturenames", ())


def pytest_collection_modifyitems(config, items):
    """Drop Redis-dependent items when no server is reachable."""
    if _redis_available():
        return
    kept, deselected = [], []
    for item in items:
        (deselected if _requires_redis(item) else kept).append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = kept
