# APEX Vision AI v2

AI floor detection, room segmentation and tile rendering — a clean rebuild of the
APEX Vision AI project with a config-driven architecture, a pluggable AI provider
stack, and a fully working React frontend.

## Features

- **Scene analysis** — detects the floor, segments it, estimates depth, fits the
  floor plane and extracts a homography so tiles can be projected in perspective.
- **AI provider pattern** — choose between the heavy models
  (GroundingDINO + SAM2 + DepthAnythingV2) and a lightweight OpenCV heuristic
  stack. `auto` picks whichever is available and falls back gracefully.
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
| `auto` (default)             | Use the heavy stack when importable, else heuristics |
| `heavy`                      | Force GroundingDINO + SAM2 + DepthAnythingV2         |
| `light`                      | Force the pure-OpenCV heuristic stack                |

Model paths are configurable via environment variables:

- `GROUNDING_DINO_CONFIG`, `GROUNDING_DINO_CKPT`
- `SAM2_CONFIG_DIR`, `SAM2_CONFIG_FILE`, `SAM2_CKPT`
- `DEPTH_ANYTHING_ROOT`, `DEPTH_ANYTHING_CKPT`

Defaults point at `D:\Projects\GroundingDINO`, `D:\Projects\sam2` and
`D:\Projects\Depth-Anything-V2`. The heavy dependencies
(`groundingdino`, `sam2`, `depth_anything_v2`) are installed from those source
repositories and are **not** required — the app runs fully on the heuristic
stack if they are missing.

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
checkpoints — see the env vars above. To run without them, set
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
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://your-host:8000 — the web UI and `/api/*` endpoints are live.

Notes:

- Use a single worker: the heavy models are large and are loaded once per
  process at startup.
- If the UI is served from a different origin than the API, add
  `APEX_CORS_ORIGINS=https://your-site.example.com` (comma-separated) or set
  `VITE_API_BASE` at build time.
- Rendered images under `/output/*` are served with `Cache-Control: no-store`
  so refreshes always show the latest render.

## Other settings

| Variable                     | Default            | Purpose                              |
| ---------------------------- | ------------------ | ------------------------------------ |
| `APEX_HOST` / `APEX_PORT`    | `0.0.0.0` / `8000` | Server bind address                  |
| `APEX_DEBUG`                 | `false`            | Verbose logging                      |
| `APEX_WRITE_DEBUG`           | `false`            | Write debug images during rendering  |
| `APEX_ASSETS` / `APEX_OUTPUT`| `assets/` `output/`| Data directories                     |
| `APEX_TILE_MM` / `APEX_GROUT`| `600` / `2`        | Default render values                |
| `APEX_CORS_ORIGINS`          | dev origins only   | Extra comma-separated CORS origins   |
| `APEX_FRONTEND_DIST`         | `frontend/dist`    | Built SPA location (served at `/`)   |
