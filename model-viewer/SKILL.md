---
name: Model Viewer (3D)
description: Show the user an interactive 3D model viewer (STL/OBJ/PLY) in the built-in browser pane — rotate, zoom, click points on the model; clicked coordinates are delivered to the agent chat via a local relay and the OpenCode HTTP API. Use when the user wants to view or discuss a 3D model, mark places on a part, or check geometry before printing (triggers: "show the model", "open STL", "let me point at the model", «покажи модель», «открой STL», «посмотри деталь», «отметь места на модели»).
---

# 3D Model Viewer with point picking

All files live next to this SKILL.md (OpenCode provides the skill base directory):

- `viewer.html` — self-contained viewer (~0.67 MB, three.js inlined, no network
  needed). Starts empty: the user drags & drops an STL/OBJ/PLY file or uses
  "Choose file". LMB rotate, wheel zoom, RMB pan, click on the model = numbered
  marker with coordinates and surface normal (`nx, ny, nz`) in file units (usually mm).
  Includes procedural scale-reference objects (`lighter`, `banana`, `aa`, `card`).
  Points survive page reloads (localStorage, per model). `Backspace` undoes the last
  point, `Esc` clears all.
- `click-relay.py` — relay: points from the viewer → a message into the active
  agent session via the OpenCode HTTP API (`POST /api/session/{id}/prompt`).
  Default port `127.0.0.1:18767`.
- `build.py` — rebuild `viewer.html` with a model pre-embedded (auto-load on
  open) and/or a custom relay port:
  `python3 build.py --model path/to/part.stl [--port 18767] [--out viewer.html]`.
  Only STL can be pre-embedded; other formats work via drag & drop.
- `template.html` + `lib/` — sources used by `build.py`.

## Startup protocol

1. Check the relay: `curl -s http://127.0.0.1:18767/ping` → must return `pong`.
   If not, start it in the background: `python3 click-relay.py` (no arguments —
   it resolves the active session on every send).
2. Show the viewer to the user: `browser.preview({path: '<skill dir>/viewer.html'})`,
   take the tabID from `browser.tabs.list()`.
3. Confirm a model is loaded: evaluate `window.__modelInfo` (name/tris/size).
   If `null`, ask the user to drop a file into the window.

## Reading the points

- Main channel: the user presses "📤 Send to agent" (or Enter) — a message with
  the not-yet-sent points arrives in the chat (duplicates are avoided).
- Direct read at any time: evaluate `JSON.stringify(window.__picks)`;
  the latest point is `window.__lastPick`.
- Duty mode (real time, while the agent is waiting inside its turn):
  evaluate `window.__waitPick(25000).then(r => JSON.stringify(r))` — resolves
  right after the user clicks, or `null` on timeout.
- Do not wake the agent per click: one batch of points = one send / one turn.

## Gotchas

- The relay is a background process: after a machine reboot it is gone —
  always check `/ping` first.
- If the button says "relay unreachable", the viewer itself still works —
  only the delivery is down.
- Changing the relay port requires a rebuild (`build.py --port N`) and running
  `python3 click-relay.py [sessionID] N`.
- `window.__debugAddPick(x, y, z)` — programmatic marker in file coordinates (testing).
- `window.__viewer.clearPicks()` — clear points; Esc in the viewer does the same.
