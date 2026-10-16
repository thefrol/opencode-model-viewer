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

PINNED_SESSION = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] not in ('', '-') else None
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 18767
MAX_PAYLOAD_BYTES = 1024 * 1024  # 1 MB limit


def active_session():
    r = subprocess.run(
        ['opencode', 'api', 'get', '/api/session/active'],
        capture_output=True, text=True, timeout=15, check=False
    )
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        raw = json.loads(r.stdout)
    except Exception:  # noqa: BLE001
        return None
    data = raw.get('data') if isinstance(raw, dict) else raw
    if isinstance(data, dict) and data:
        return next(iter(data), None)
    if isinstance(data, list) and data:
        first = data[0]
        return first.get('id') if isinstance(first, dict) else str(first)
    return None


def send_prompt(sid, text):
    try:
        payload = json.dumps({'text': text}, ensure_ascii=False)
        r = subprocess.run(
            ['opencode', 'api', 'post', f'/api/session/{sid}/prompt', '--data', payload],
            capture_output=True, text=True, timeout=60, check=False
        )
        print(f'-> {sid} (exit {r.returncode}): {(r.stdout + r.stderr)[:200]}', flush=True)
    except Exception as e:  # noqa: BLE001
        print('! send error:', e, flush=True)


class RelayServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type='text/plain; charset=utf-8'):
        encoded = body.encode('utf-8') if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        if encoded:
            self.wfile.write(encoded)

    def do_OPTIONS(self):
        self._send(204, b'')

    def do_GET(self):
        if self.path.split('?')[0] not in ('/', '/ping'):
            self._send(404, 'not found')
            return
        self._send(200, 'pong')

    def do_POST(self):
        if self.path.split('?')[0] != '/pick':
            self._send(404, 'not found')
            return
        try:
            n = int(self.headers.get('Content-Length') or 0)
        except ValueError:
            self._send(400, 'invalid Content-Length')
            return
        if n <= 0 or n > MAX_PAYLOAD_BYTES:
            self._send(413 if n > MAX_PAYLOAD_BYTES else 400, 'payload size out of range')
            return

        raw = self.rfile.read(n).decode('utf-8', 'replace')
        try:
            data = json.loads(raw)
        except Exception:  # noqa: BLE001
            self._send(400, 'invalid JSON')
            return

        if not isinstance(data, dict):
            self._send(400, 'JSON object expected')
            return

        picks = data.get('picks') or []
        if not isinstance(picks, list) or not picks:
            self._send(400, 'no picks provided')
            return

        try:
            sid = PINNED_SESSION or active_session()
        except Exception as e:  # noqa: BLE001
            self._send(502, f'failed to query active session: {e}')
            return

        if not sid:
            print('! no active session', flush=True)
            self._send(503, 'no active OpenCode session found')
            return

        model = data.get('model') or 'model'
        total = data.get('total', len(picks))
        lines = [f'📍 Clicked on model **{model}** (total points: {total}):']
        for p in picks:
            if not isinstance(p, dict):
                continue
            line = f'- #{p.get("n")}: x={p.get("x")}, y={p.get("y")}, z={p.get("z")}'
            nx, ny, nz = p.get('nx'), p.get('ny'), p.get('nz')
            if nx is not None and ny is not None and nz is not None:
                line += f' (normal: {nx}, {ny}, {nz})'
            lines.append(line)

        threading.Thread(target=send_prompt, args=(sid, '\n'.join(lines)), daemon=True).start()
        self._send(200, 'ok')

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    print(f'relay on 127.0.0.1:{PORT}, session: {PINNED_SESSION or "active"}', flush=True)
    RelayServer(('127.0.0.1', PORT), Handler).serve_forever()

