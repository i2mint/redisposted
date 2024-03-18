"""
Base module for Redis message broker.

This module provides an implementation of the `MsgBrokerBase` interface for Redis. It
uses the `redis` package to interact with a Redis server.
"""

from functools import cached_property
import threading
from time import sleep
from typing import Any, Callable
from posted import MsgBrokerBase, NoMsg
from redis import Redis
from i2 import Sig

# ----------------------------------------------------------------------------
# Signature for the `RedisBroker` class

broker_sig = Sig(MsgBrokerBase.__init__)  # signature of __init__ includes the self
redis_sig = Sig(Redis)
redis_posted_sig = broker_sig + redis_sig
redis_posted_sig = redis_posted_sig.ch_kinds(
    **{  # here, we change all arguments (but self and kwargs) to be keyword-only
        name: Sig.KEYWORD_ONLY
        for name in redis_posted_sig.names
        if name not in {'self', 'kwargs'}
    }
)

# ----------------------------------------------------------------------------
# Redis message broker


class RedisBroker(MsgBrokerBase):
    """
    Message broker for Redis.
    """

    @redis_posted_sig
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def write(self, channel: str, message: Any):
        encoded_msg = self._encoder(message)
        if not self._redis.publish(channel, encoded_msg):
            self._redis.rpush(channel, encoded_msg)

    def read(self, channel: str):
        if not self._redis.exists(channel) or not self._redis.llen(channel):
            return NoMsg
        msg = self._redis.lpop(channel)
        return self._decoder(msg)

    def subscribe(self, channel: str, callback: Callable[[Any], None]):
        def consume(stop_event):
            pubsub = self._redis.pubsub()
            pubsub.subscribe(channel)
            while not stop_event.is_set():
                msg = pubsub.get_message()
                if msg and msg['type'] == 'message':
                    decoded_msg = self._decoder(msg['data'])
                    callback(decoded_msg)
                sleep(0.01)
            pubsub.unsubscribe(channel)

        msg = self.read(channel)
        while msg != NoMsg:
            callback(msg)
            msg = self.read(channel)

        stop_event = threading.Event()
        self._subscriptions.setdefault(channel, []).append(stop_event)
        self._executor.submit(consume, stop_event)

    def unsubscribe(self, channel: str):
        for sub in self._subscriptions.get(channel, []):
            sub.set()
        self._subscriptions.pop(channel, None)

    @cached_property
    def _redis(self):
        return Redis(**self._config)
