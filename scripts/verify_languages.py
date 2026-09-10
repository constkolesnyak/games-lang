"""Re-check language support for the top games against the live Steam store API
(store.steampowered.com/api/appdetails). Rate limit ~200 req / 5 min -> 1 req / 1.6 s.
Usage: python3 scripts/verify_languages.py appids.txt
Output: data/verified_langs.json {appid: {"text": [...], "audio": [...], "name": ..., "type": ...}}
"""
import json, re, sys, time, pathlib, html, urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "verified_langs.json"
store = json.loads(OUT.read_text()) if OUT.exists() else {}
appids = [a for a in pathlib.Path(sys.argv[1]).read_text().split() if a not in store]
print("to fetch:", len(appids), flush=True)
for i, a in enumerate(appids, 1):
    url = f"https://store.steampowered.com/api/appdetails?appids={a}&l=english&cc=de"
    for t in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r: j = json.loads(r.read().decode())
            break
        except Exception as e:
            code = getattr(e, "code", None); wait = 120 if code == 429 else 10
            print("retry", a, e, "sleep", wait, file=sys.stderr, flush=True); time.sleep(wait); j = None
    d = (j or {}).get(str(a), {}).get("data") if j else None
    if not d:
        store[a] = None
    else:
        raw = d.get("supported_languages", "")
        raw = re.sub(r"<br\s*/?>.*$", "", raw, flags=re.S)           # drop the "*languages with full audio support" footnote
        parts = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in raw.split(",")]
        text = [p.rstrip("*").strip() for p in parts if p]
        audio = [p.rstrip("*").strip() for p in parts if p.endswith("*")]
        store[a] = {"name": d.get("name"), "type": d.get("type"), "text": text, "audio": audio,
                    "release": (d.get("release_date") or {}).get("date"), "controller": d.get("controller_support")}
    if i % 20 == 0:
        OUT.write_text(json.dumps(store, ensure_ascii=False)); print(time.strftime("%H:%M:%S"), i, "/", len(appids), flush=True)
    time.sleep(1.6)
OUT.write_text(json.dumps(store, ensure_ascii=False)); print("DONE", len(store))
