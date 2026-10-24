# Hallway Electron App

Hallway packaged as a standalone desktop app for non-developers. Built at Patch the Conference Hackathon (Oct 24, 2026).

## What it does

Launching `Hallway.app` (or running `npm start` inside `electron/`) runs the entire Hallway stack automatically with a visual loading screen and step-by-step status checklist:

1. **Settings**: Creates `.env` in the user data folder (`~/Library/Application Support/Hallway/.env`) if missing.
2. **Python & Virtualenv**: Locates Python 3.11+ and creates an isolated virtualenv with `requirements.txt` installed on first launch.
3. **Graph Database**: Checks if FalkorDB is reachable on `127.0.0.1:6379` and runs `docker compose up -d` if needed. If Docker is not running, shows a plain-English notice with a **Try again** button and **Show logs** button.
4. **Seed & Initial Plan**: Seeds the 18-person, 19-talk sample conference and builds the clash-free schedule for `rene` only when the graph is empty (so meetings and plan edits survive restarts).
5. **Board Server**: Starts `uvicorn app.main:app` on `127.0.0.1:8000`, waits for `/api/health`, and opens the Hallway board inside the native window. On quit, it cleanly stops the backend process while keeping your Docker graph volume intact.

## Running

### Launch the packaged macOS app

```bash
open electron/dist/mac-arm64/Hallway.app
```

### Run from source (development)

```bash
cd electron
npm install
npm start
```

### Rebuild the macOS `.app` bundle

```bash
cd electron
npm run pack       # Unpacked .app in electron/dist/mac-arm64/Hallway.app
npm run dist       # Full DMG + .app build
```

## Requirement

Docker Desktop or Colima (`colima start`) must be running so FalkorDB can run on port `6379`. Everything else is self-contained.
