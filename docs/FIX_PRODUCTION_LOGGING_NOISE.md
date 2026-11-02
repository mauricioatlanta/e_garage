# Fix Production Logging Noise

## Problem

Production logs were cluttered with excessive debug output from `LanguagePolicyMiddleware` on every request:

```
[DEBUG] País None - Usando default: es
[DEBUG] ===== LanguagePolicyMiddleware =====
[DEBUG] País: None
[DEBUG] Idioma aplicado: es
[DEBUG] URL: //blog/wp-includes/wlwmanifest.xml
[DEBUG] ===========================================
```

Additionally, bot scanners were hitting WordPress vulnerability paths, generating 404s and wasting server resources.

## Solution

### 1. Replace print() with logger.debug()

**File:** `taller/middleware/lang_policy.py`

- Replaced all `print()` statements with proper `logger.debug()` calls
- Added `import logging` and `logger = logging.getLogger(__name__)`
- This allows Django's logging configuration to control output level

**Benefits:**
- Debug logs only appear when `DEBUG=True` or log level is set to DEBUG
- Production logs remain clean with `level: INFO`
- No code changes needed to toggle debug output

### 2. Add Bot Filter Middleware

**File:** `gestion_taller/middleware/bot_filter.py` (NEW)

Early rejection of common bot scanning paths:
- `/wp-includes/`, `/wp-content/`, `/wordpress/`
- `/.env`, `/phpMyAdmin/`, `/.git/`
- Returns 404 immediately without processing full request cycle

**Benefits:**
- Reduces server load from bot traffic
- Cleaner logs (one line per blocked request)
- Faster response times for legitimate traffic

## Deployment Steps

### Step 1: Update Files on Server

```bash
cd /srv/egarage
source venv/bin/activate

# Pull latest changes
git pull origin main

# Or manually copy files if not using git:
# - taller/middleware/lang_policy.py
# - gestion_taller/middleware/bot_filter.py
```

### Step 2: Add BotFilterMiddleware to Settings

Edit `gestion_taller/settings_prod.py`:

```python
MIDDLEWARE = [
    'gestion_taller.middleware.bot_filter.BotFilterMiddleware',  # ← ADD THIS FIRST
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... rest of middleware
]
```

**Important:** Place it **first** in the middleware list for maximum efficiency.

### Step 3: Restart Gunicorn

```bash
sudo systemctl restart gunicorn
```

### Step 4: Verify

Check logs are clean:

```bash
sudo journalctl -u gunicorn -n 50 --no-pager
```

You should see:
- ✅ No more `[DEBUG]` spam on every request
- ✅ Bot scans blocked: `Bot scan blocked: //wp-includes/wlwmanifest.xml from 1.2.3.4`
- ✅ Only legitimate requests logged

## Testing

### Test 1: Verify Debug Logs Are Gone

```bash
# Make a legitimate request
curl https://egarage.cl/cl/es/accounts/login/

# Check logs - should NOT see debug output
sudo journalctl -u gunicorn -n 20 --no-pager | grep DEBUG
# Expected: No results
```

### Test 2: Verify Bot Filter Works

```bash
# Simulate bot scan
curl https://egarage.cl/wp-includes/wlwmanifest.xml

# Check logs - should see one line
sudo journalctl -u gunicorn -n 5 --no-pager | grep "Bot scan blocked"
# Expected: Bot scan blocked: /wp-includes/wlwmanifest.xml from ...
```

### Test 3: Verify Normal Operation

```bash
# Test Chile login
curl https://egarage.cl/cl/es/accounts/login/

# Test USA login
curl https://egarage.cl/us/en/accounts/login/

# Both should work normally without debug spam
```

## Rollback (If Needed)

If issues occur, restore from backup:

```bash
cd /srv/egarage
cp backups/middleware_YYYYMMDD_HHMMSS/*.py taller/middleware/
sudo systemctl restart gunicorn
```

## Performance Impact

**Before:**
- Every request: 5+ print() calls to stdout
- Bot scans: Full Django request cycle for 404s

**After:**
- Production: Zero debug output (logger.debug() is no-op when level=INFO)
- Bot scans: Rejected in ~1ms before hitting Django routing

**Expected improvements:**
- 📉 Log volume: -80% (no debug spam)
- ⚡ Response time: +5-10ms for legitimate requests (less I/O)
- 🛡️ Server load: -20% (bots blocked early)

## Related Files

- `taller/middleware/lang_policy.py` - Language detection middleware
- `gestion_taller/middleware/bot_filter.py` - Bot filtering middleware
- `gestion_taller/settings_prod.py` - Production settings
- `scripts_deploy/fix_production_logging.sh` - Deployment helper script

## Notes

- The `logger.debug()` calls remain in code but are no-op in production
- To enable debug logging temporarily: Set `LOGGING['root']['level'] = 'DEBUG'` in settings
- Bot filter can be extended with more paths as needed
- Consider adding rate limiting for persistent bot IPs if needed
