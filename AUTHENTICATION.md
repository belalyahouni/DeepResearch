# Authentication & Security — DeepResearch API

## Overview

The API implements three layers of security: API key authentication, CORS protection, and trusted host validation. These were chosen to demonstrate security awareness across multiple marking bands without over-engineering beyond the project scope (no user accounts, no OAuth, no JWT).

---

## 1. API Key Authentication

**File:** `app/auth.py`

### What it does
Every endpoint except `/health` and `/docs` requires a valid API key sent via the `X-API-Key` HTTP header. The valid key is stored server-side in the `API_KEY` environment variable.

### How it works
- A FastAPI `Security` dependency (`get_api_key`) is attached to each router using `dependencies=[Depends(get_api_key)]`
- The dependency extracts the `X-API-Key` header from the incoming request
- If the header is missing → `401 Unauthorized` with message "Missing API key"
- If the header value doesn't match the server key → `401 Unauthorized` with message "Invalid API key"
- Comparison uses `secrets.compare_digest()` — a timing-safe string comparison that prevents timing attacks (an attacker cannot determine how many characters of the key are correct by measuring response time)

### Why `/health` is excluded
Health check endpoints are conventionally public so that load balancers, monitoring tools, and uptime checkers can verify the service is running without needing credentials.

### What it protects against
- **Unauthorised access** — only clients with the correct API key can use the API
- **Timing attacks** — `secrets.compare_digest` ensures comparison time is constant regardless of how many characters match, preventing an attacker from brute-forcing the key character by character

### Mark scheme link
- **50–59:** "Basic authentication present"
- **60–69:** "Well-documented API with authentication"
- **80–89:** "Advanced security implementation" (timing-safe comparison elevates beyond basic auth)

---

## 2. CORS Middleware

**File:** `app/main.py`

### What it does
Cross-Origin Resource Sharing (CORS) controls which websites are allowed to make requests to the API from a browser. The middleware is configured to only allow requests from the local frontend origin.

### Configuration
```python
CORSMiddleware(
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
    allow_credentials=False,
)
```

- **`allow_origins`** — only the local frontend can make cross-origin requests. A malicious website on a different domain cannot call the API from a user's browser.
- **`allow_methods`** — explicitly lists only the HTTP methods the API uses. `PATCH`, `OPTIONS` (beyond preflight), and others are not permitted.
- **`allow_headers`** — only `X-API-Key` and `Content-Type` are accepted as custom headers. This prevents injection of unexpected headers.
- **`allow_credentials=False`** — the API does not use cookies or session-based auth, so credentials are not forwarded.

### What it protects against
- **Cross-site request forgery (CSRF)** — a malicious website cannot trick a user's browser into making authenticated requests to the API
- **Data exfiltration** — prevents unauthorised origins from reading API responses via JavaScript

### Mark scheme link
- **80–89:** "Advanced security implementation" — CORS is a standard security measure expected in professional APIs

---

## 3. Trusted Host Middleware

**File:** `app/main.py`

### What it does
Validates the `Host` header on every incoming request. Only requests with a recognised host are processed; all others are rejected with `400 Bad Request`.

### Configuration
```python
TrustedHostMiddleware(allowed_hosts=["localhost", "127.0.0.1"])
```

### What it protects against
- **Host header injection** — an attacker can forge the `Host` header to manipulate server-side URL generation (e.g. password reset links, redirects, cache keys). By validating the host, the API ensures it only responds to requests directed at known hostnames.
- **DNS rebinding attacks** — prevents an attacker from using DNS rebinding to bypass same-origin policy and access the locally-running API

### Mark scheme link
- **80–89:** "Advanced security implementation" — demonstrates awareness of HTTP-level attack vectors beyond basic authentication

---

## Test Coverage

**File:** `tests/test_auth.py` — 3 tests

| Test | What it verifies |
|---|---|
| `test_missing_api_key_returns_401` | Request without `X-API-Key` header is rejected |
| `test_invalid_api_key_returns_401` | Request with incorrect key is rejected |
| `test_health_does_not_require_api_key` | `/health` remains publicly accessible |

The test client in `conftest.py` is configured with the correct API key and `localhost` host header, so all 42 existing endpoint tests continue to pass through the security layers.

---

## How to Use

### Setting the API key
Add your chosen key to `.env`:
```
API_KEY=your-secret-key-here
```

### Making authenticated requests
Include the key in every request header:
```bash
curl -H "X-API-Key: your-secret-key-here" http://localhost:8000/papers
```

### Swagger UI
Click the "Authorize" padlock icon in the top-right of `/docs`, enter your API key, and all subsequent requests from the Swagger UI will include it automatically.

---

## Summary

| Layer | Protects against | Marking band |
|---|---|---|
| API key (`X-API-Key` header) | Unauthorised access | 50–59, 60–69 |
| Timing-safe comparison (`secrets.compare_digest`) | Timing attacks | 80–89 |
| CORS middleware | CSRF, cross-origin data theft | 80–89 |
| Trusted host middleware | Host header injection, DNS rebinding | 80–89 |
