"""Preview the dashboard on http://localhost:8000 while you edit it.

    python -m dashboard.serve              # build, serve docs/, rebuild + reload the browser on changes
    python -m dashboard.serve --port 8080

Opens the same pages GitHub Pages publishes (docs/dashboard/index.html and executive.html).
It watches dashboard/*.html|css|js|py and data/serve/daily_panel.csv; when one changes it rebuilds
and the open browser tab reloads itself. The reload script is added only to what this server
sends, never to the files on disk. Stop with Ctrl+C. Standard library only.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import threading
import time
import webbrowser
from pathlib import Path

from . import build

ROOT = build.HERE.parent
DOCS = ROOT / "docs"
WATCH = [*build.HERE.glob("*.html"), *build.HERE.glob("*.css"), *build.HERE.glob("*.js"), *build.HERE.glob("*.py"), build.SERVE]
RELOAD = (b"<script>(function(){let s=null;setInterval(async()=>{try{const t=await (await fetch('/__build',{cache:'no-store'})).text();"
          b"if(s&&t!==s)location.reload();s=t;}catch(e){}},1000);})();</script>")
stamp = {"value": str(time.time())}


def _mtimes() -> dict:
    return {p: p.stat().st_mtime for p in WATCH if p.exists()}


def _rebuild() -> None:
    try:
        build.main([])
        stamp["value"] = str(time.time())
    except Exception as e:  # keep serving the last good build
        print(f"Build failed, still serving the previous pages: {e}")


def _watch(interval: float = 1.0) -> None:
    seen = _mtimes()
    while True:
        time.sleep(interval)
        now = _mtimes()
        if now != seen:
            seen = now
            print("Change detected, rebuilding ...")
            _rebuild()


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/__build":
            body = stamp["value"].encode()
        elif self.path.split("?")[0].endswith((".html", "/")):
            path = Path(self.translate_path(self.path))
            path = path / "index.html" if path.is_dir() else path
            if not path.exists():
                return super().do_GET()
            body = path.read_bytes().replace(b"</body>", RELOAD + b"</body>")
        else:
            return super().do_GET()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain" if self.path == "/__build" else "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # quiet: the build prints what matters
        pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    args = ap.parse_args(argv)
    _rebuild()
    threading.Thread(target=_watch, daemon=True).start()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), functools.partial(Handler, directory=str(DOCS)))
    url = f"http://localhost:{args.port}/dashboard/"
    print(f"Detailed view   {url}\nExecutive view  {url}executive.html\nCtrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
