#!/usr/bin/env python3
"""Build viewer.html: embed a model for auto-load and/or set the relay port.

Usage:
  python3 build.py                                  # blank viewer (drag & drop)
  python3 build.py --model path/to/part.stl         # auto-load this STL on open
  python3 build.py --port 9000                      # relay port baked into the page
  python3 build.py --model part.stl --out my.html   # custom output name
"""
import argparse
import base64
import pathlib
import sys

LIBS = {
    '__THREE__': 'three.min.js',
    '__ORBIT__': 'OrbitControls.js',
    '__STL__': 'STLLoader.js',
    '__OBJ__': 'OBJLoader.js',
    '__PLY__': 'PLYLoader.js',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--model', help='STL file to embed for auto-load (other formats: drag & drop)')
    ap.add_argument('--port', type=int, default=18767, help='relay port baked into the page (default 18767)')
    ap.add_argument('--out', default='viewer.html', help='output file (default viewer.html)')
    ap.add_argument('--template', default=str(pathlib.Path(__file__).parent / 'template.html'))
    args = ap.parse_args()

    base = pathlib.Path(__file__).parent
    html = pathlib.Path(args.template).read_text()

    for token, name in LIBS.items():
        code = (base / 'lib' / name).read_text()
        assert '</script>' not in code, f'{name} contains </script>'
        html = html.replace(token, code, 1)

    if args.model:
        model = pathlib.Path(args.model)
        if model.suffix.lower() != '.stl':
            sys.exit('Auto-load supports STL only; other formats work via drag & drop.')
        html = html.replace('__MODEL_B64__', base64.b64encode(model.read_bytes()).decode(), 1)
        html = html.replace('__MODEL_NAME__', model.name, 1)
    else:
        # __MODEL_B64__ stays a token: the page detects it and starts empty
        html = html.replace('__MODEL_NAME__', '', 1)

    html = html.replace('__RELAY_PORT__', str(args.port), 1)
    out = pathlib.Path(args.out)
    out.write_text(html)
    print(f'OK: {out} ({out.stat().st_size / 1024 / 1024:.2f} MB, relay port {args.port})')


if __name__ == '__main__':
    main()
