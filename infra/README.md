# APEX Vision AI v2 — Production Infrastructure

This directory contains deployment infrastructure for Sprint 1 production hardening.

## Container

Build from the repository root:

```powershell
docker build -f infra/docker/Dockerfile -t apex-vision-ai:v2.1 .
```

Run a local production smoke test:

```powershell
docker run --rm -p 8000:8000 apex-vision-ai:v2.1
```

Then verify `GET /api/health` returns HTTP 200.

The default container uses the lightweight OpenCV provider. Heavy AI models should
be supplied separately through deployment configuration and must not be committed
to the repository.

## Security baseline

- Container runs as the unprivileged `apex` user.
- Model weights and runtime-generated output are excluded from source control.
- Production deployments should inject secrets and model paths through the runtime
environment or a secret manager.
- Keep the API and frontend on the same origin where possible to reduce CORS exposure.
