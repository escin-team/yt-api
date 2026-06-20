#!/usr/bin/env python
"""Test Redis connection with full diagnostic output."""

from youtube_search.services.cache import CacheService
from youtube_search.utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

print("\n" + "=" * 60)
print("Redis Connection Diagnostic Test")
print("=" * 60 + "\n")

# Test 1: Direct Redis connection
print("Test 1: Creating CacheService instance...")
cache = CacheService()

if cache.client:
    print("✓ Redis client created successfully")

    # Test 2: Ping Redis
    print("\nTest 2: Testing Redis ping...")
    try:
        response = cache.client.ping()
        print(f"✓ Redis ping successful: {response}")
    except Exception as e:
        print(f"✗ Redis ping failed: {e}")

    # Test 3: Get Redis info
    print("\nTest 3: Getting Redis server info...")
    try:
        info = cache.client.info("server")
        print(f"✓ Redis version: {info.get('redis_version')}")
        print(f"✓ Redis mode: {info.get('redis_mode')}")
        print(f"✓ OS: {info.get('os')}")
    except Exception as e:
        print(f"✗ Failed to get Redis info: {e}")

    # Test 4: Test set/get
    print("\nTest 4: Testing cache set/get...")
    try:
        test_key = "test:connection"
        cache.client.setex(test_key, 10, "test_value")
        value = cache.client.get(test_key)
        if value == "test_value":
            print("✓ Cache set/get successful")
            cache.client.delete(test_key)
        else:
            print(f"✗ Cache set/get failed: expected 'test_value', got '{value}'")
    except Exception as e:
        print(f"✗ Cache set/get failed: {e}")
else:
    print("✗ Redis client is None - connection failed")
    print("\nCheck the logs above for detailed error information")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60 + "\n")
