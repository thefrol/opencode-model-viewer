# opencode-model-viewer

An [OpenCode](https://opencode.ai) skill that lets the **agent show the user a 3D
model** (STL / OBJ / PLY) in an interactive viewer — and lets the user **click
points on it**, with the coordinates delivered straight **into the agent chat**.

```
┌────────────────────────┐   fetch POST    ┌───────────────┐   opencode api    ┌────────────────────────────┐
│ viewer.html (browser)  │ ──────────────▶ │ click-relay   │ ────────────────▶ │ POST /api/session/{id}/    │
│ rotate · zoom · click  │  127.0.0.1:18767│ (python)      │                   │ prompt  → agent wakes up   │
└────────────────────────┘                 └───────────────┘                   └────────────────────────────┘
```

Two channels:

- **Batch**: the user clicks points, then presses **📤 Send to agent** (or Enter)
  → one message with the new points arrives in the chat.
- **Duty mode**: the agent long-polls the page (`window.__waitPick`) while waiting
  inside its turn → sees every click in real time.

Everything runs locally: the viewer is a single self-contained HTML file
(three.js inlined), models never leave the machine.

## Install

**Option A — clone into the global skills directory:**

```sh
git clone https://github.com/thefrol/opencode-model-viewer \
  ~/.config/opencode/skills/opencode-model-viewer
```

**Option B — add the HTTP catalog** to `opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["https://raw.githubusercontent.com/thefrol/opencode-model-viewer/main/"]
}
```

**Option C — project-only:** copy/symlink the `model-viewer/` directory into
`.opencode/skills/` of your project.

Then just ask the agent: *"show the model"* / *"открой STL"*.

## Use

1. The agent opens `viewer.html` in the built-in browser pane and starts the relay.
2. Drop any STL / OBJ / PLY into the window (or it is pre-loaded, see below).
3. Rotate (LMB), zoom (wheel), pan (RMB). Click the model to drop numbered
   markers — coordinates and surface normals (`nx, ny, nz`) are recorded in file
   units (usually mm), and the distance between the last two points is measured
   automatically.
4. Pick a **Scale reference** (`🔥 BIC Lighter`, `🍌 Banana`, `🔋 AA Battery`,
   `💳 Credit Card`) to place a real-world object next to the part for size intuition.
5. Press **📤 Send to agent** (or `Enter`) — the coordinates land in the chat as a message.
6. Points survive page reloads (localStorage, per model). `Backspace` removes the
   last point, `Esc` clears all.

## Pre-load your own model

```sh
cd model-viewer
python3 build.py --model path/to/part.stl        # writes viewer.html
python3 build.py --port 9000                     # custom relay port
```

`viewer.html` stays a single self-contained file — open it in any browser even
without OpenCode (delivery needs the relay, viewing does not).

## Requirements

- [OpenCode](https://opencode.ai) V2 with browser tools (desktop app or TUI with the browser connected)
- `python3` for the relay (stdlib only), `opencode` CLI on PATH
- The relay port defaults to `18767` (configurable — see the skill)

## How it works (for the curious)

The viewer keeps picked points on the page (`window.__picks`). The relay is a
tiny `http.server` that forwards a batch as a prompt into your OpenCode session
via its HTTP API — the agent literally receives a chat message with the
coordinates. The viewer and the relay never touch the network beyond localhost.

MIT licensed. Built around [three.js](https://threejs.org) (MIT).
