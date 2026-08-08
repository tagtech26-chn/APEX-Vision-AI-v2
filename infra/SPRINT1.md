# APEX Vision AI v2.1 — Sprint 1 Production Hardening

## Scope

APEX Vision AI only. No dependency on other APEX products or modules.

## Backend

- [x] Exception middleware with safe 500 responses.
- [x] Centralized structured application logging.
- [x] Configuration validation and environment-driven model paths.
- [x] Health and readiness endpoints.
- [x] Production CORS defaults restricted to explicit origins.
- [x] Signed scene cache with atomic writes and unsafe-name rejection.
- [x] Render output `no-store` cache headers.

## AI / rendering observability

- [x] AI provider diagnostics without exposing model paths or secrets.
- [x] Render duration metrics.
- [x] Cache hit/miss/error metrics.
- [x] Render progress and failure instrumentation.
- [x] Runtime diagnostics endpoint.

## Frontend

- [x] API timeout and retry handling for safe GET requests.
- [x] Render polling retries and bounded timeout.
- [x] Catalog loading state and retry UI.
- [x] Responsive gallery sizing improvements.
- [x] Render progress remains visible through the existing progress model.

## Testing / CI

- [x] Configuration validation tests.
- [x] Health/readiness/diagnostics contract tests.
- [x] Render metrics endpoint test.
- [x] Render service/cache regression tests.
- [x] Backend pytest job in CI.
- [x] Frontend lint/build job in CI.
- [x] Production container smoke test.

## Release gate

Sprint 1 is implementation-complete when all checklist items are committed and
CI reports green for backend tests, frontend validation, container build, and
production smoke checks. A successful GitHub Actions run remains the final
external validation gate.
