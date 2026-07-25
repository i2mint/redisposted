"""
Test cases for the ``RedisBroker`` class.

These tests run against a live Redis server reachable at
``REDISPOSTED_REDIS_HOST``:``REDISPOSTED_REDIS_PORT`` (default
``localhost:6379``, db ``REDISPOSTED_REDIS_DB`` = ``0``). In CI the server is
provided by a ``services: redis`` container; locally, any reachable Redis works
(e.g. ``docker run -p 6379:6379 redis:7`` or a native install). When no Redis is
reachable, the Redis-dependent tests are *deselected* by ``conftest.py`` so the
suite stays green; the signature test, which needs no server, always runs.
"""

import os
import pytest

from redisposted.base import RedisBroker
from posted.tests.common import (
    gen_test_mk_msg_broker_args,
    base_test_on_demand_consumption,
    base_test_reactive_consumption,
)

REDIS_HOST = os.environ.get("REDISPOSTED_REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDISPOSTED_REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDISPOSTED_REDIS_DB", "0"))


@pytest.fixture(scope="module")
def broker():
    return RedisBroker(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


@pytest.fixture(autouse=True)
def init_testing_data(request):
    # Only touch Redis for tests that actually use the ``broker`` fixture, so
    # server-free tests (e.g. the signature test) don't require a live Redis.
    if "broker" in request.fixturenames:
        request.getfixturevalue("broker")._redis.flushdb()


@pytest.mark.parametrize(
    "message, channel",
    list(gen_test_mk_msg_broker_args()),
)
def test_on_demand_consumption(broker: RedisBroker, message, channel):
    base_test_on_demand_consumption(broker, message, channel)


@pytest.mark.parametrize(
    "message, channel",
    list(gen_test_mk_msg_broker_args()),
)
def test_reactive_consumption(broker: RedisBroker, message, channel):
    base_test_reactive_consumption(broker, message, channel)


def test_redis_broker_signature():
    from i2 import Sig
    from redisposted.base import MsgBrokerBase, Redis

    # The signature of the `RedisBroker` class should be the signature of the base
    # broker class, with the `Redis` arguments added to it.
    assert set(Sig(RedisBroker)) == (set(Sig(MsgBrokerBase)) | set(Sig(Redis)))
