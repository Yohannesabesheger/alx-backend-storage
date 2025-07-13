#!/usr/bin/env python3
"""Redis-based Cache system with logging and history"""

import redis
import uuid
from typing import Union, Callable, Optional, Any
from functools import wraps





class Cache:
    def __init__(self):
        """Initialize Redis client and flush the DB"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store the data in Redis with a generated UUID key
        Args:
            data: str, bytes, int, or float
        Returns:
            The key under which the data is stored
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key


def count_calls(method: Callable) -> Callable:
    """Decorator to count how many times a method is called"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """Decorator to store the history of inputs and outputs for a function"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        inputs_key = f"{key}:inputs"
        outputs_key = f"{key}:outputs"
        self._redis.rpush(inputs_key, str(args))
        output = method(self, *args, **kwargs)
        self._redis.rpush(outputs_key, str(output))
        return output
    return wrapper


def replay(method: Callable) -> None:
    """Display the history of calls of a particular function"""
    r = redis.Redis()
    key = method.__qualname__
    inputs = r.lrange(f"{key}:inputs", 0, -1)
    outputs = r.lrange(f"{key}:outputs", 0, -1)
    call_count = r.get(key)
    print(f"{key} was called {int(call_count or 0)} times:")
    for input_args, output in zip(inputs, outputs):
        print(f"{key}(*{input_args.decode()}) -> {output.decode()}")


class Cache:
    """Cache class to interact with Redis"""

    def __init__(self):
        """Initialize Redis client and flush the DB"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis with a randomly generated key
        Args:
            data: str, bytes, int or float
        Returns:
            key as a string
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable[[bytes], Any]] = None) -> Any:
        """
        Get data from Redis and optionally apply a conversion function
        Args:
            key: Redis key
            fn: Callable to convert the data
        Returns:
            Raw or transformed data, or None if key not found
        """
        value = self._redis.get(key)
        if value is None:
            return None
        return fn(value) if fn else value

    def get_str(self, key: str) -> Optional[str]:
        """Retrieve data from Redis and decode it as UTF-8 string"""
        return self.get(key, lambda d: d.decode("utf-8"))

    def get_int(self, key: str) -> Optional[int]:
        """Retrieve data from Redis and convert it to integer"""
        return self.get(key, lambda d: int(d))
