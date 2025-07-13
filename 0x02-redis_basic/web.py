#!/usr/bin/env python3
"""Web caching and access counting"""

import redis
import requests
from typing import Callable
from functools import wraps

r = redis.Redis()


def count_access(method: Callable) -> Callable:
    """Decorator to count accesses to a URL"""
    @wraps(method)
    def wrapper(url: str) -> str:
        count_key = f"count:{url}"
        r.incr(count_key)
        return method(url)
    return wrapper


def cache_result(expire: int = 10) -> Callable:
    """Decorator to cache the result of a function with expiration (default 10s)"""
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(url: str) -> str:
            cached = r.get(url)
            if cached:
                return cached.decode('utf-8')
            result = method(url)
            r.setex(url, expire, result)
            return result
        return wrapper
    return decorator


@count_access
@cache_result(expire=10)
def get_page(url: str) -> str:
    """Fetch and cache the HTML content of a URL"""
    response = requests.get(url)
    return response.text
