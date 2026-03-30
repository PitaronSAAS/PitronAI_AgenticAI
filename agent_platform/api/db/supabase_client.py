from supabase import create_client, Client
from api.config import get_settings
from cachetools import TTLCache
from threading import Lock

_client: Client | None = None

# In-memory tenant cache: api_key → tenant+config dict
_tenant_cache: TTLCache = TTLCache(maxsize=500, ttl=60)
_cache_lock = Lock()


def get_db() -> Client:
    global _client
    if _client is None:
        s = get_settings()
        _client = create_client(s.supabase_url, s.supabase_service_key)
    return _client


def get_tenant_cache() -> TTLCache:
    return _tenant_cache


def get_cache_lock() -> Lock:
    return _cache_lock
