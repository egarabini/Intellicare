"""Testes para SimpleCache do Zilda."""

import time

from zilda.engine.cache import SimpleCache


class TestSimpleCache:
    def test_set_and_get(self) -> None:
        cache = SimpleCache()
        cache.set("key1", "value1", ttl=60)
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self) -> None:
        cache = SimpleCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self) -> None:
        cache = SimpleCache()
        cache.set("key1", "value1", ttl=0)
        # TTL=0 means already expired
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_delete(self) -> None:
        cache = SimpleCache()
        cache.set("key1", "value1", ttl=60)
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_nonexistent(self) -> None:
        cache = SimpleCache()
        cache.delete("nonexistent")  # no error

    def test_clear(self) -> None:
        cache = SimpleCache()
        cache.set("a", 1, ttl=60)
        cache.set("b", 2, ttl=60)
        assert cache.size() == 2
        cache.clear()
        assert cache.size() == 0

    def test_has(self) -> None:
        cache = SimpleCache()
        cache.set("key1", "value1", ttl=60)
        assert cache.has("key1") is True
        assert cache.has("key2") is False

    def test_size(self) -> None:
        cache = SimpleCache()
        assert cache.size() == 0
        cache.set("a", 1, ttl=60)
        cache.set("b", 2, ttl=60)
        assert cache.size() == 2

    def test_cleanup(self) -> None:
        cache = SimpleCache()
        cache.set("live", "yes", ttl=60)
        cache.set("dead", "no", ttl=0)
        time.sleep(0.01)
        cache.cleanup()
        assert cache.has("live") is True
        assert cache.has("dead") is False

    def test_overwrite(self) -> None:
        cache = SimpleCache()
        cache.set("key", "v1", ttl=60)
        cache.set("key", "v2", ttl=60)
        assert cache.get("key") == "v2"
