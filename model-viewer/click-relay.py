#!/usr/bin/env python3
"""Relay: clicks from viewer.html -> a message in an OpenCode session.

Run:  python3 click-relay.py [sessionID] [port]
      no arguments -> delivers to the active session, port 18767

  GET  /ping — health check
  POST /pick — {"model": "...", "picks": [{"n":1,"x":..,"y":..,"z":..}], "total": N}
               -> POST /api/session/{id}/prompt into OpenCode
"""
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PINNED_SESSION = sys.argv[1] if len(sys.argv) > 1 else None
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 18767


def active_session():
    out = subprocess.run(['opencode', 'api', 'get', '/api/session/active'],
                         capture_output=True, text=True, timeout=20).stdout
    data = json.loads(out).get('data') or {}
    return next(iter(data), None)


def send_prompt(text):
    try:
        sid = PINNED_SESSION or active_session()
        if not sid:
            print('! no active session', flush=True)
            return
        payload = json.dumps({'text': text}, ensure_ascii=False)
        r = subprocess.run(['opencode', 'api', 'post', f'/api/session/{sid}/prompt',
                            '--data', payload],
                           capture_output=True, text=True, timeout=60)
        print(f'-> {sid}: {(r.stdout + r.stderr)[:200]}', flush=True)
    except Exception as e:  # noqa: BLE001
        print('! send error:', e, flush=True)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'pong')

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n).decode('utf-8', 'replace')
        try:
            data = json.loads(raw)
        except Exception:  # noqa: BLE001
            self.send_response(400)
            self._cors()
            self.end_headers()
            return
        picks = data.get('picks') or []
        model = data.get('model') or 'model'
        lines = [f'📍 Clicked on model **{model}** (total points: {data.get("total", len(picks))}):']
        for p in picks:
            lines.append(f'- #{p.get("n")}: x={p.get("x")}, y={p.get("y")}, z={p.get("z")}')
        threading.Thread(target=send_prompt, args=('\n'.join(lines),), daemon=True).start()
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    print(f'relay on 127.0.0.1:{PORT}, session: {PINNED_SESSION or "active"}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
