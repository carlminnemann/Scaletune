#!/usr/bin/env python3
"""Tiny one-shot receiver so the browser can hand back rendered icons.

The monogram is drawn on a canvas (the only text renderer available here), and
shipping a 512px PNG back as base64 through a tool call is wasteful. The page
POSTs it instead, and this writes the file.

    python3 tools/icon-receiver.py 8795
"""
import base64, json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icons')


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        payload = json.loads(self.rfile.read(n).decode())
        os.makedirs(OUT, exist_ok=True)
        written = []
        for name, b64 in payload.items():
            path = os.path.join(OUT, name)
            with open(path, 'wb') as f:
                f.write(base64.b64decode(b64))
            written.append('%s (%d bytes)' % (name, os.path.getsize(path)))
        body = json.dumps({'written': written}).encode()
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)
        print('\n'.join(written), flush=True)

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8795
    HTTPServer(('127.0.0.1', port), Handler).serve_forever()
