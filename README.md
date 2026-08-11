# APEX Vision AI v2

AI floor detection, room segmentation and tile rendering — a clean rebuild of the
APEX Vision AI project with a config-driven architecture, a pluggable AI provider
stack, and a fully working React frontend.

## Features

- **Scene analysis** — detects the floor, segments it, estimates depth, fits the
  floor plane and extracts a homography so tiles can be projected in perspective.
- **AI provider pattern** — production defaults to the heavy models
  (GroundingDINO + SAM2 + DepthAnythingV2). `auto` may be selected explicitly to
  allow a heuristic fallback; `light` is available for development only.
- **Tile rendering** — grout, straight / brick / herringbone / chevron patterns,
  material enhancement, room lighting, LAB colour matching and shadow
  preservation.
- **Room & tile catalog** — served over a FastAPI JSON API.
- **Frontend** — React 19 + MUI v9 + Vite. Search, category/finish filters,
  room picker, live configuration panel (size, grout, colour, pattern).
- **Tests** — pytest suite covering geometry, rendering, services and the API.

## Layout

```
app/
  main.py                 FastAPI entry point
  core/config.py          environment-driven settings
  api/routes/             rooms, catalog, render
  services/               catalog, room, tile, render services
  ai/
    scene/                SceneResult + SceneAnalyzer orchestrator
    detection/            GroundingDINO (heavy) / heuristic (light)
    segmentation/         SAM2 (heavy) / heuristic (light)
    depth/                DepthAnythingV2 (heavy) / heuristic (light)
    geometry/             polygon, homography, plane fitting
  renderer/               patterns, grout, lighting, shadow, colour, compositor
  cache/scene_cache.py    pickle-based scene cache (keyed by provider)
assets/                   rooms, tiles, scenes cache
catalog/tiles.json        tile catalog
frontend/                 React + MUI frontend
tests/                    pytest suite
```

## Quick start

### Backend

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py            # or: .venv\Scripts\uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 — the `/api/rooms`, `/api/catalog/*` and
`/api/render` endpoints are live.

### Frontend

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173
```

### Tests

```powershell
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest tests
```

## AI providers

| Setting (`APEX_AI_PROVIDER`) | Behaviour                                            |
| ---------------------------- | ---------------------------------------------------- |
| `heavy` (default)            | Force GroundingDINO + SAM2 + DepthAnythingV2         |
| `auto`                       | Use heavy when fully ready, else heuristics           |
| `light`                      | Force the pure-OpenCV heuristic stack                |

`APEX_AI_DEVICE` controls heavy-model execution:

| Setting | Behaviour |
| --- | --- |
| `auto` (default) | CUDA when available, otherwise CPU |
| `cuda` | Require CUDA; fail fast if unavailable |
| `cpu` | Run heavy models on CPU |

Model paths are configurable via environment variables:

- `GROUNDING_DINO_CONFIG`, `GROUNDING_DINO_CKPT`
- `SAM2_CONFIG_DIR`, `SAM2_CONFIG_FILE`, `SAM2_CKPT`
- `DEPTH_ANYTHING_ROOT`, `DEPTH_ANYTHING_CKPT`

The heavy readiness check validates dependencies, configuration files, source
repositories and all three checkpoints before the production provider is
selected.

## Production deployment

The app ships as a **single service**: FastAPI serves both the JSON API and the
built React frontend on one port. `app/main.py` auto-detects `frontend/dist` and
mounts it as the SPA at `/` (the JSON home endpoint is then replaced by the web
UI). Point `APEX_FRONTEND_DIST` elsewhere to override the build location.

### 1. Install Python dependencies

```powershell
.venv\Scripts\pip install -r requirements-prod.txt
# Heavy AI stack (torch must already be installed; needs git + C/C++ toolchain):
.venv\Scripts\pip install -r requirements-ai-source.txt
```

The heavy pipeline also needs the Depth-Anything-V2 source clone and all model
checkpoints. To intentionally use the heuristic fallback, set
`APEX_AI_PROVIDER=auto`; to force the lightweight path, set
`APEX_AI_PROVIDER=light`.

### 2. Build the frontend

```powershell
cd frontend
npm ci
npm run build          # outputs dist/ (Served by the backend automatically)
cd ..
```

The frontend talks to the API through relative URLs by default (same origin).
To point it at a different host, build with `VITE_API_BASE` set, e.g.
`$env:VITE_API_BASE = "https://api.example.com"` before `npm run build`.

### 3. Run

```powershell
.\start.ps1
```

`start.ps1` explicitly selects `APEX_AI_PROVIDER=heavy` and
`APEX_AI_DEVICE=auto` when those variables are not already set. The service
loads the heavy models once and exposes `/api/ready` as the production
readiness probe.

Open http://your-host:8000 — the web UI and `/api/*` endpoints are live.

Notes:

- Use a single worker: the heavy models are large and are loaded once per
  process at startup.
- If the UI is served from a different origin than the API, add
  `APEX_CORS_ORIGINS=https://your-site.example.com` (comma-separated) or set
  `VITE_API_BASE` at build time.
- Rendered images under `/output/*` are served with `Cache-Control: no-store`
  so refreshes always show the latest render.

## Production setup on a fresh Windows machine

`scripts/setup-windows.ps1` installs everything on an empty Windows box
(Python 3.11, Node 20.19+/22.12+ and git must already be installed):

```powershell
git clone https://github.com/tagtech26-chn/APEX-Vision-AI-v2.git
cd APEX-Vision-AI-v2

# Heuristic stack only - works anywhere, runs on CPU, no extra downloads:
.\scripts\setup-windows.ps1 -CpuOnly

# Or the full heavy AI stack (~2.9 GB of model weights; also needs the Visual
# Studio C++ Build Tools to compile GroundingDINO):
.\scripts\setup-windows.ps1 -Heavy -CpuOnly
```

What it does: creates `.venv`, installs `requirements-prod.txt` (and
`requirements-ai-source.txt` + model weights with `-Heavy`), runs
`npm ci && npm run build` in `frontend/`, and writes `models.env` (heavy model
paths, loaded by `start.ps1` — never committed).

Start and test:

```powershell
.\start.ps1
# open http://127.0.0.1:8000
```

Notes:

- The production provider defaults to `heavy`. `auto` uses heavy only when the
  complete stack is ready and otherwise falls back to OpenCV; force one with
  `$env:APEX_AI_PROVIDER = "heavy"`, `"auto"`, or `"light"` before `start.ps1`.
- `-CpuOnly` installs the CPU torch build; heavy AI still runs on CPU when CUDA
  is unavailable, but GPU is recommended for practical render times.
- `-SkipFrontend` skips the npm build; `-SkipModels` skips the weight download
  when `-Heavy` is given (run `.\scripts\download-heavy-models.ps1` later).
- Sanity-check the install with the test suite:
  `.venv\Scripts\pip install -r requirements-dev.txt` then
  `.venv\Scripts\python -m pytest`.

## Other settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `APEX_HOST` / `APEX_PORT` | `0.0.0.0` / `8000` | Server bind address |
| `APEX_DEBUG` | `false` | Verbose logging |
| `APEX_WRITE_DEBUG` | `false` | Write debug images during rendering |
| `APEX_AI_PROVIDER` | `heavy` | AI provider selection |
| `APEX_AI_DEVICE` | `auto` | Heavy-model device selection |
| `APEX_ASSETS` / `APEX_OUTPUT` | `assets/` / `output/` | Data directories |
| `APEX_TILE_MM` / `APEX_GROUT` | `600` / `2` | Default render values |
| `APEX_CORS_ORIGINS` | dev origins only | Extra comma-separated CORS origins |
| `APEX_FRONTEND_DIST` | `frontend/dist` | Built SPA location (served at `/`) |
