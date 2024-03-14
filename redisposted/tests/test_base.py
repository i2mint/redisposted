"""
Test cases for the redisBroker class.

The tests are run against a redis broker running in a Docker container. If the container
is not running, it will be started before the running the test and stopped after the 
tests are done.
"""

import os
import pytest
from pathlib import Path
from time import sleep
from posted import NoMsg
from posted.tests.utils import service_is_running, start_service, stop_service
from posted.tests.common import (
    EXISTING_CHANNEL,
    gen_test_mk_msg_broker_args,
    base_test_on_demand_consumption,
    base_test_reactive_consumption,
)

from redisposted.base import RedisBroker

SERVICE_CONTAINER_NAME = 'redisposted_test'
DOCKER_COMPOSE_FILEPATH = Path(
    os.path.dirname(os.path.abspath(__file__)), 'docker-compose.yml'
)


@pytest.fixture(scope='session', autouse=True)
def ensure_service_is_running():
    if service_is_running(SERVICE_CONTAINER_NAME):
        yield
    else:
        start_service(SERVICE_CONTAINER_NAME, DOCKER_COMPOSE_FILEPATH)
        try:
            yield
        finally:
            stop_service(SERVICE_CONTAINER_NAME, DOCKER_COMPOSE_FILEPATH)


@pytest.fixture(scope='module')
def broker():
    return RedisBroker(host='localhost', port=6379, db=0)


@pytest.fixture(autouse=True)
def init_testing_data(broker: RedisBroker):
    broker._redis.flushdb()
    # broker.write(EXISTING_CHANNEL, '')
    # broker.read(EXISTING_CHANNEL)
    # sleep(0.5)


@pytest.mark.parametrize(
    'message, channel', list(gen_test_mk_msg_broker_args()),
)
def test_on_demand_consumption(broker: RedisBroker, message, channel):
    base_test_on_demand_consumption(broker, message, channel)


@pytest.mark.parametrize(
    'message, channel', list(gen_test_mk_msg_broker_args()),
)
def test_reactive_consumption(broker: RedisBroker, message, channel):
    base_test_reactive_consumption(broker, message, channel)
