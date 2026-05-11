# Redis Security - Quick Start Guide

**TL;DR:** Use `await cache.set()` and `await cache.get()` like before, but:
1. Password now required (set `REDIS_PASSWORD` in `.env`)
2. All keys are service-prefixed (can't cross-pollinate)
3. TTL is enforced (cache misses are safe)
4. JSON only (no pickle = no RCE risk)

---

## 30-Second Setup

### 1. Set Environment Variables

```bash
# Generate secure password
openssl rand -hex 32  # e.g., a1b2c3d4...

# Add to .env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=a1b2c3d4...  # Your secure password
REDIS_CACHE_ENABLED=true
```

### 2. Start Redis

```bash
docker-compose up redis
```

### 3. Use in Your Service

```python
from services.dev1_genomics_variant_api.src.cache.redis_cache import get_cache

# In your route handler or async function:
async def classify_variant(rsid: str):
    cache = await get_cache()
    
    # Try cache first
    cached = await cache.get("variant", rsid, "GRCh38")
    if cached:
        return cached
    
    # Compute if not cached
    result = compute_classification(rsid)
    
    # Store for 1 hour
    await cache.set(
        "variant", rsid, "GRCh38",
        value=result,
        ttl=3600
    )
    
    return result
```

Done! ✅

---

## Common Patterns

### Pattern 1: Get or Compute with Cache

```python
async def get_variant_info(rsid: str):
    cache = await get_cache()
    
    # Try cache
    result = await cache.get("variant", rsid)
    if result:
        logger.info(f"Cache hit: {rsid}")
        return result
    
    # Compute (cache miss)
    logger.info(f"Cache miss, computing: {rsid}")
    result = expensive_computation(rsid)
    
    # Store for later (failures are safe)
    await cache.set("variant", rsid, value=result, ttl=3600)
    
    return result
```

### Pattern 2: Invalidate on Update

```python
async def update_gene_info(gene_id: str, new_data: dict):
    # Update database
    db.update_gene(gene_id, new_data)
    
    # Invalidate cache
    cache = await get_cache()
    await cache.delete("gene", gene_id)
    logger.info(f"Invalidated cache for gene {gene_id}")
```

### Pattern 3: Batch Invalidation

```python
async def clear_all_variants(version: str):
    cache = await get_cache()
    
    # Delete all variant cache for a specific genome version
    count = await cache.delete_pattern(f"variant:*:{version}")
    logger.info(f"Cleared {count} variant cache entries")
```

### Pattern 4: Safe Caching (No Crashes if Redis Down)

```python
async def get_with_cached_fallback(patient_id: str):
    cache = await get_cache()
    
    try:
        # Try to get from cache
        cached = await cache.get("patient_data", patient_id)
        if cached:
            return cached
    except Exception as e:
        # Cache error (Redis down?) - log and continue
        logger.warning(f"Cache error: {e}, continuing without cache")
    
    # Compute fresh (with or without cache)
    result = compute_patient_data(patient_id)
    
    try:
        # Try to cache (failures are safe)
        await cache.set("patient_data", patient_id, value=result, ttl=1800)
    except Exception as e:
        logger.warning(f"Failed to cache result: {e}")
    
    return result
```

---

## TTL Reference

**What's a reasonable TTL?**

| Data Type | How Often Changes | Suggested TTL | Example |
|-----------|-------------------|---------------|---------|
| Gene annotations | Rarely (stable) | 24 hours | `ttl=86400` |
| Clinical guidelines | Occasionally | 6 hours | `ttl=21600` |
| Prediction results | Often | 1 hour | `ttl=3600` |
| Session state | Always | 30 minutes | `ttl=1800` |
| User uploads | Always | 5 minutes | `ttl=300` |

**NOT cached:**
- Authentication tokens ❌
- Patient names/addresses ❌  
- Full patient objects ❌
- File contents ❌

---

## Dev vs Prod Differences

### Development (.env)

```env
DEBUG=true  # Enables PII validation in cache
REDIS_PASSWORD=dev-password
REDIS_CACHE_ENABLED=true  # Can disable for testing
```

### Production (.env)

```env
DEBUG=false  # Disables validation for performance
REDIS_PASSWORD=<strong-random-32-byte-hex>  # Must change!
REDIS_CACHE_ENABLED=true
```

---

## Troubleshooting

### Error: "REDIS_PASSWORD not set"

```python
RuntimeError: REDIS_PASSWORD must be set in environment
```

**Fix:**
```bash
# Add to .env
REDIS_PASSWORD=your-secure-password

# Or set in shell
export REDIS_PASSWORD=$(openssl rand -hex 32)
```

### Error: "Cache value contains PII keyword"

```python
AssertionError: Cache value contains suspicious PII keyword: name
```

**Fix:** Don't cache full patient objects, cache only results.

```python
# ❌ WRONG
await cache.set("patient", patient_id, value=patient_obj, ttl=3600)

# ✅ RIGHT
result = {"classification": "high_risk", "confidence": 0.95}
await cache.set("prediction", patient_id, value=result, ttl=3600)
```

### Error: "Invalid TTL"

```python
False  # Returns False, doesn't raise
```

**Fix:** TTL must be > 0 seconds

```python
# ❌ WRONG
await cache.set("key", value=data, ttl=0)  # Returns False

# ✅ RIGHT  
await cache.set("key", value=data, ttl=300)  # 5 minutes
```

### Redis Connection Not Available

```python
None  # Cache miss, returns None (safe)
False  # Set fails, returns False (safe)
```

**Service continues working!** No exceptions raised.

Check logs:
```
logger.warning(f"Cache get error: Connection refused")
```

---

## Security Rules (TL;DR)

1. **Passwords:** Always from environment (`REDIS_PASSWORD`), never hardcoded ✅
2. **Keys:** Service-prefixed (`dev1:`, `dev2:`, etc.) so services can't interfere ✅
3. **TTL:** Required on every `set()` (no forever-cached keys) ✅
4. **Serialization:** JSON only (no pickle) ✅
5. **PII:** Never cache patient names, tokens, or full objects ✅
6. **Errors:** All caught gracefully (service continues even if Redis down) ✅

---

## Performance Tips

- **Longer TTL** (24h) for reference data that changes rarely
- **Shorter TTL** (1-5m) for session state and user uploads
- **Monitor** cache hit/miss ratio (should be 60%+ for stable queries)
- **Invalidate** when underlying data changes (don't wait for TTL)
- **Test** with Redis disabled in CI/CD (verify graceful degradation)

---

## Testing

```bash
# Run security tests
pytest shared/tests/test_redis_security.py -v

# Test with Redis disabled
export REDIS_CACHE_ENABLED=false
pytest services/*/tests/  # Should still pass

# Test with wrong password
export REDIS_PASSWORD=wrong-password
pytest  # Should get warnings, not crashes
```

---

## FAQ

**Q: Can I cache a patient name?**
A: No. Use dev mode (`DEBUG=true`) to catch this in testing.

**Q: What if Redis goes down?**
A: Service continues working without cache. Cache.get() returns None, cache.set() returns False.

**Q: How often should I rotate the password?**
A: Every 90 days in production.

**Q: Can Dev1 read Dev2's cache?**
A: No. All keys are service-prefixed (`dev1:`, `dev2:`, etc.). Attempting to read another service's key returns None.

**Q: What's the max TTL?**
A: Any value works, but values > 1 year are probably mistakes (triggers warning).

**Q: Do I have to use the cache?**
A: No, but cache=None/False failures are safe. If Redis is down, the cache either returns None (get) or False (set), and your service continues.

---

## Related Docs

- [Full Implementation Guide](REDIS_SECURITY_IMPLEMENTATION.md)
- [Security Tests](shared/tests/test_redis_security.py)
- [Configuration](infrastructure/redis/redis.conf)

---

✅ **You're ready!** Start caching securely.
