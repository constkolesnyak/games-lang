"""Per-language interface / full-audio / subtitles flags from IStoreBrowseService/GetItems (batched, ~50 apps per call).
Usage: python3 scripts/fetch_langflags.py appids.txt   -> data/langflags.json {appid: {"de": [ui, audio, subs], "ja": [...]}}
"""
import json, sys, time, pathlib, urllib.request, urllib.parse
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "langflags.json"
DE, JA = 1, 10                                   # ELanguage: 1 German, 10 Japanese
store = json.loads(OUT.read_text()) if OUT.exists() else {}
ids = [a for a in pathlib.Path(sys.argv[1]).read_text().split() if a.isdigit() and a not in store]
print("to fetch:", len(ids), flush=True)
def get(batch, tries=5):
    q = {"ids": [{"appid": int(a)} for a in batch], "context": {"language": "english", "country_code": "US"}, "data_request": {"include_supported_languages": True}}
    url = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1/?input_json=" + urllib.parse.quote(json.dumps(q))
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return json.loads(urllib.request.urlopen(req, timeout=40).read().decode()).get("response", {}).get("store_items", [])
        except Exception as e:
            wait = 60 if getattr(e, "code", None) == 429 else 5 * (t + 1); print("retry", t, e, "sleep", wait, file=sys.stderr, flush=True); time.sleep(wait)
    return []
for i in range(0, len(ids), 50):
    batch = ids[i:i + 50]; items = get(batch); seen = set()
    for it in items:
        a = str(it.get("appid")); seen.add(a); flags = {}
        for l in it.get("supported_languages", []):
            k = "de" if l.get("elanguage") == DE else "ja" if l.get("elanguage") == JA else None
            if k: flags[k] = [bool(l.get("supported")), bool(l.get("full_audio")), bool(l.get("subtitles"))]
        store[a] = flags
    for a in batch:
        if a not in seen: store[a] = None            # unknown / delisted
    if (i // 50) % 10 == 0: OUT.write_text(json.dumps(store)); print(time.strftime("%H:%M:%S"), i + len(batch), "/", len(ids), flush=True)
    time.sleep(0.8)
OUT.write_text(json.dumps(store)); print("DONE", len(store))
