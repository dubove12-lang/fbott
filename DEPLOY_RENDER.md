# FatBot Copytrading MVP — proper full-stack deployment

This is the correct deployment package for the current MVP.

Do **not** drag the full backend ZIP into Netlify. Netlify static hosting will not run this FastAPI server.
This app is FastAPI + SQLite + static frontend served by FastAPI, so deploy it as one Python web service.

## Recommended: Render full-stack deployment

### 1) Create a GitHub repository

Create a new private GitHub repo, for example:

`fatbot-copytrading-mvp`

Upload the contents of this folder to the repository root. The repository root must contain:

- `backend/`
- `frontend/`
- `requirements.txt`
- `render.yaml`
- `Dockerfile`

### 2) Deploy on Render

In Render:

1. New +
2. Blueprint
3. Connect your GitHub repo
4. Render reads `render.yaml`
5. Create service

Alternative manual setup:

- Type: Web Service
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

### 3) Environment variables

Set these in Render service settings:

`HYDROMANCER_API_KEY=your_key_here`

Optional:

`HYDROMANCER_LEADERBOARD_WINDOW=30d`
`HYDROMANCER_LEADERBOARD_SORT_BY=totalPnl`
`HYDROMANCER_LEADERBOARD_LIMIT=50`

If Hydromancer still returns 403 for `userPnlLeaderboard`, the app will fall back to SQLite mock leaderboard until Hydromancer enables that endpoint for your key.

### 4) Open the Render URL

The app is served from `/`.

The API is served from `/api/...`.

No Netlify is needed for this MVP.

## Railway option

Railway can deploy this same repository using the Dockerfile.

Start command is already inside Dockerfile:

`python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}`

## Important production note

SQLite on free cloud instances is okay only for MVP testing.
For real production, move DB to PostgreSQL and use persistent storage.
