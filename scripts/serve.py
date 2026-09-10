#!/usr/bin/env python3
"""Local site for the games list. Serves index.html and keeps statuses in data/status.json inside this repo.

  python3 scripts/serve.py            # http://localhost:8777/  (also reachable on the LAN: http://<mac>.local:8777/)
  PORT=9000 python3 scripts/serve.py

API (same origin, used by index.html):
  GET  /api/status            -> {"<appid>": {"status": "Next", "updated": "..."}, ...}
  GET/POST /api/prefs         -> data/prefs.json (UI preferences, e.g. {"statusOrder": [...]}); POST merges keys
  POST /api/status            <- {"<appid>": "Next" | null, ...}   partial update; null removes
Every change is written to data/status.json and committed to git ("status: <game> → <status>").
Set AUTO_PUSH=1 to also push to origin in the background.
"""
import json, os, subprocess, sys, threading, time, socket
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = os.path.join(ROOT, "data", "status.json")
PREFS = os.path.join(ROOT, "data", "prefs.json")
PORT = int(os.environ.get("PORT", "8777"))
LOCK = threading.Lock()

def load():
    try:
        with open(STATUS, encoding="utf-8") as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return {}

def load_prefs():
    try:
        with open(PREFS, encoding="utf-8") as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return {}

def names():
    try:
        import csv
        with open(os.path.join(ROOT, "data", "games.csv"), encoding="utf-8") as f:
            return {r["appid"]: r["name"] for r in csv.DictReader(f)}
    except Exception: return {}
NAMES = names()

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)

def push_bg():
    """Best-effort push in the background; a failed push is retried after the next commit."""
    def run():
        r = git("push", "-q")
        if r.returncode: sys.stderr.write("%s push failed: %s\n" % (time.strftime("%H:%M:%S"), r.stderr.strip()[-200:]))
    threading.Thread(target=run, daemon=True).start()

def commit(msg, path="data/status.json"):
    git("add", path)
    r = git("-c", "user.name=games-site", "-c", "user.email=games-site@local", "commit", "-q", "-m", msg)
    if r.returncode == 0 and os.environ.get("AUTO_PUSH") == "1": push_bg()
    return r.returncode == 0

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw): super().__init__(*a, directory=ROOT, **kw)
    def log_message(self, fmt, *args):
        if "/api/" in str(args[0] if args else ""): sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path.split("?")[0] == "/api/status":
            with LOCK: return self._json(200, load())
        if self.path.split("?")[0] == "/api/prefs":
            with LOCK: return self._json(200, load_prefs())
        if self.path.split("?")[0] in ("/", "/index.html"):
            self.path = "/index.html"
        return super().do_GET()
    def end_headers(self):
        if self.path.endswith((".json", ".html")): self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def do_POST(self):
        if self.path.split("?")[0] == "/api/prefs":
            try: changes = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")) or b"{}"))
            except Exception: return self._json(400, {"error": "bad json"})
            if not isinstance(changes, dict): return self._json(400, {"error": "object expected"})
            with LOCK:
                prefs = load_prefs(); prefs.update(changes)
                with open(PREFS, "w", encoding="utf-8") as f: json.dump(prefs, f, ensure_ascii=False, indent=1); f.write("\n")
                committed = commit("prefs: " + ", ".join(changes.keys()), "data/prefs.json")
            return self._json(200, {"ok": True, "committed": committed, "data": prefs})
        if self.path.split("?")[0] != "/api/status": return self._json(404, {"error": "not found"})
        try: changes = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")) or b"{}"))
        except Exception: return self._json(400, {"error": "bad json"})
        if not isinstance(changes, dict): return self._json(400, {"error": "object expected"})
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with LOCK:
            data = load(); lines = []
            for k, v in changes.items():
                k = str(k)
                if not k.lstrip("-").isdigit(): continue
                st = v.get("status") if isinstance(v, dict) else v
                if st: data[k] = {"status": str(st), "updated": now}; lines.append(f"{NAMES.get(k, k)} → {st}")
                else: data.pop(k, None); lines.append(f"{NAMES.get(k, k)} → —")
            data = dict(sorted(data.items(), key=lambda kv: int(kv[0])))
            with open(STATUS, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")
            committed = commit("status: " + (lines[0] if len(lines) == 1 else f"{len(lines)} changes")) if lines else False
        return self._json(200, {"ok": True, "committed": committed, "data": data})

if __name__ == "__main__":
    if os.environ.get("AUTO_PUSH") == "1": push_bg()          # flush anything committed while offline
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    host = socket.gethostname()
    print(f"games site: http://localhost:{PORT}/  |  LAN: http://{host if host.endswith('.local') else host + '.local'}:{PORT}/", flush=True)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
