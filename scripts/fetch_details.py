"""NOTE: never run two instances against the same output file - each process rewrites the whole JSON.
For a list of appids fetch (a) Steam Deck / SteamOS / Steam Machine compatibility report and
(b) SteamSpy appdetails (full user tag list with votes, owners, ccu, playtime).
Usage: python3 scripts/fetch_details.py appids.txt
Output: data/details.json {appid: {"compat": {...}, "spy": {...}}} — resumable, only fetches missing keys.
"""
import json, os, sys, time, pathlib, threading, urllib.request

OUT = pathlib.Path(os.environ.get("DETAILS_OUT") or (pathlib.Path(__file__).resolve().parent.parent / "data" / "details.json"))
lock = threading.Lock()
store = json.loads(OUT.read_text()) if OUT.exists() else {}

def get(url, tries=8):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            code = getattr(e, "code", None)
            wait = 60 if code == 429 else 5 * (i + 1)
            print("retry", i, url, e, "sleep", wait, file=sys.stderr, flush=True); time.sleep(wait)
    return None

def save():
    with lock: OUT.write_text(json.dumps(store))

def worker(kind, appids, delay):
    done = 0
    for a in appids:
        rec = store.setdefault(str(a), {})
        if kind in rec: continue
        if kind == "compat":
            j = get(f"https://store.steampowered.com/saleaction/ajaxgetdeckappcompatibilityreport?nAppID={a}&l=english")
            r = (j or {}).get("results") or {}
            val = {"deck": r.get("resolved_category"), "os": r.get("steamos_resolved_category"),
                   "machine": r.get("machine_resolved_category"),
                   "deck_items": [x["loc_token"].split("_TestResult_")[-1] for x in r.get("resolved_items") or []],
                   "machine_items": [x["loc_token"].split("_TestResult_")[-1] for x in r.get("machine_resolved_items") or []]} if j else None
        else:
            j = get(f"https://steamspy.com/api.php?request=appdetails&appid={a}")
            val = {k: j.get(k) for k in ("name", "owners", "ccu", "average_2weeks", "median_forever", "positive", "negative", "languages", "developer", "publisher", "genre")} if j else None
            if j: val["tags"] = j.get("tags") if isinstance(j.get("tags"), dict) else {}
        with lock: rec[kind] = val
        done += 1
        if done % 25 == 0: save(); print(time.strftime("%H:%M:%S"), kind, done, "/", len(appids), flush=True)
        time.sleep(delay)
    save(); print(kind, "DONE", done, flush=True)

if __name__ == "__main__":
    appids = [int(x) for x in pathlib.Path(sys.argv[1]).read_text().split()]
    kinds = sys.argv[2].split(",") if len(sys.argv) > 2 else ["compat", "spy"]
    ts = []
    for k in kinds:
        if k == "spy":   # SteamSpy is fast; 3 shards ~ 1 req/s total
            ts += [threading.Thread(target=worker, args=(k, appids[i::3], 1.0)) for i in range(3)]
        else:            # store.steampowered.com: 2 shards, backs off 60s on 429
            ts += [threading.Thread(target=worker, args=(k, appids[i::2], 0.8)) for i in range(2)]
    [t.start() for t in ts]; [t.join() for t in ts]
    print("ALL DONE", len(store))
