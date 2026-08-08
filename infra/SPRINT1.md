# Sprint 1 Production Hardening

## Current baseline

- Production container definition under `infra/docker/`.
- Dedicated non-root runtime user.
- Explicit `/api/health` endpoint smoke check.
- GitHub Actions container build and smoke-test workflow.
- Runtime output/uploads remain externalized from source control.

## Validation status

The workflow is configured to run on pushes and pull requests targeting
`feature/v2.1-production-hardening`. A successful GitHub Actions run is required
before the branch is considered CI-validated.
