"""Opens the project board: serves the project folder on this computer only and opens
http://localhost:<port>/board/ in the browser. Stop it with Ctrl+C.

    python board/serve.py                          # in a project: the folder above board/, port 8790 (or the next free)
    python board/serve.py 9000                     # another port
    python path/to/board/serve.py --root my-app    # any project folder, with this board

The board reads ROADMAP.md from the project folder, so browsers need it served over http (opened as a file it
can't read it). /board/ always comes from this script's own folder. Only this computer can reach it (127.0.0.1).
"""
import argparse
import functools
import http.server
import os
import socket
import webbrowser

BOARD = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".md": "text/markdown; charset=utf-8", ".js": "text/javascript", ".html": "text/html"}

    def translate_path(self, path):
        # /board/... is this folder; everything else is the project folder
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean == "/board" or clean.startswith("/board/"):
            rel = clean[len("/board"):].lstrip("/") or "index.html"
            target = os.path.realpath(os.path.join(BOARD, rel))
            if target == BOARD or target.startswith(BOARD + os.sep):
                return target
        return super().translate_path(path)

    def end_headers(self):
        # Always the latest roadmap
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def free_port(start):
    for port in range(start, start + 50):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise SystemExit("No free port found.")


def main():
    ap = argparse.ArgumentParser(description="Open the project board.")
    ap.add_argument("port", nargs="?", type=int, default=8790)
    ap.add_argument("--root", help="the project folder (default: the folder above board/)")
    ap.add_argument("--no-browser", action="store_true", help="don't open the browser")
    args = ap.parse_args()
    root = os.path.abspath(args.root or os.path.dirname(BOARD))
    port = free_port(args.port)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=root))
    url = f"http://localhost:{port}/board/"
    print(f"Project board: {url}  (Ctrl+C to stop)")
    if not os.path.exists(os.path.join(root, "ROADMAP.md")):
        print("Note: there is no ROADMAP.md in", root)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
