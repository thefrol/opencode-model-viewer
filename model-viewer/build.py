#!/usr/bin/env python3
"""Build viewer.html: embed a model for auto-load and/or set the relay port.

Usage:
  python3 build.py                                  # blank viewer (drag & drop)
  python3 build.py --model path/to/part.stl         # auto-load this STL/OBJ/PLY on open
  python3 build.py --port 9000                      # relay port baked into the page
  python3 build.py --model part.stl --out my.html   # custom output name
"""
import argparse
import base64
import html as html_lib
import pathlib
import sys

LIBS = {
    '__THREE__': 'three.min.js',
    '__ORBIT__': 'OrbitControls.js',
    '__STL__': 'STLLoader.js',
    '__OBJ__': 'OBJLoader.js',
    '__PLY__': 'PLYLoader.js',
}
SUPPORTED_EXTS = {'.stl', '.obj', '.ply'}


def main():
    base = pathlib.Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--model', help='STL/OBJ/PLY file to embed for auto-load (or leave blank for drag & drop)')
    ap.add_argument('--port', type=int, default=18767, help='relay port baked into the page (default 18767)')
    ap.add_argument('--out', default=str(base / 'viewer.html'), help='output file (default: viewer.html next to build.py)')
    ap.add_argument('--template', default=str(base / 'template.html'))
    args = ap.parse_args()

    if not (1 <= args.port <= 65535):
        sys.exit(f'Invalid port: {args.port} (must be 1..65535)')

    html = pathlib.Path(args.template).read_text(encoding='utf-8')

    for token, name in LIBS.items():
        code = (base / 'lib' / name).read_text(encoding='utf-8')
        assert '</script>' not in code, f'{name} contains </script>'
        assert token in html, f'Template token {token} not found'
        html = html.replace(token, code, 1)

    if args.model:
        model = pathlib.Path(args.model)
        if not model.is_file():
            sys.exit(f'Model file not found: {model}')
        if model.suffix.lower() not in SUPPORTED_EXTS:
            sys.exit(f'Auto-load supports STL, OBJ, and PLY (got {model.suffix}).')
        b64 = base64.b64encode(model.read_bytes()).decode('ascii')
        safe_name = html_lib.escape(model.name, quote=True)
        html = html.replace('__MODEL_B64__', b64, 1)
        html = html.replace('__MODEL_NAME__', safe_name, 1)
    else:
        # __MODEL_B64__ stays a token: the page detects it and starts empty
        html = html.replace('__MODEL_NAME__', '', 1)

    html = html.replace('__RELAY_PORT__', str(args.port), 1)
    out = pathlib.Path(args.out)
    out.write_text(html, encoding='utf-8')
    print(f'OK: {out} ({out.stat().st_size / 1024 / 1024:.2f} MB, relay port {args.port})')


if __name__ == '__main__':
    main()

