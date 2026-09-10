"""Crawl Steam store search for all Steam Deck Verified (3) and Playable (2) games.

Output: data/steam_deck_search.json  {appid: {name, deck, tagids, review_pct, review_count, released, page}}
Each search row exposes the game's top-7 tag ids (data-ds-tagids), review summary and release date.
"""
import json, re, sys, time, html, pathlib
import urllib.request, urllib.parse

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "steam_deck_search.json"
# placeholder birthday: passes the store age gate so mature-rated games appear in the results
COOKIES = "birthtime=628470001; lastagecheckage=1-0-1990; wants_mature_content=1; Steam_Language=english"
ROW = re.compile(r'data-ds-appid="(\d+)".*?data-ds-tagids="\[([\d,]*)\]".*?<span class="title">(.*?)</span>.*?search_released responsive_secondrow">\s*(.*?)\s*</div>(.*?)</a>', re.S)
REV = re.compile(r'search_review_summary (\w+)" data-tooltip-html="(.*?)&lt;br&gt;(\d+)% of the ([\d,]+) user reviews')

def fetch(url, tries=12):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cookie": COOKIES, "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            wait = 90 if e.code == 429 else 5 * (i + 1)
            print("retry", i, url, e, "sleep", wait, file=sys.stderr, flush=True); time.sleep(wait)
        except Exception as e:
            print("retry", i, url, e, file=sys.stderr, flush=True); time.sleep(5 * (i + 1))
    return None

STATE = OUT.with_suffix(".state.json")
def crawl(deck, store):
    st = json.loads(STATE.read_text()) if STATE.exists() else {}
    if deck in st.get("done", []) and not RANGE: return store
    start, total = (st.get("start", 0) if st.get("deck") == deck else 0), None
    if RANGE: start = RANGE[0]
    while True:
        url = f"https://store.steampowered.com/search/results/?query&start={start}&count=50&deck_compatibility={deck}&infinite=1&json=1&ndl=1"
        j = fetch(url)
        if not j or not j.get("success"):
            print("FAIL", url, file=sys.stderr); break
        total = j["total_count"]; h = j["results_html"]
        n = 0
        for m in ROW.finditer(h):
            appid, tagids, name, released, rest = m.groups()
            appid = int(appid)
            rv = REV.search(rest)
            rec = store.get(appid, {})
            rec.update({"name": html.unescape(name), "deck": max(deck, rec.get("deck", 0)),
                        "tagids": [int(t) for t in tagids.split(",") if t],
                        "released": released.strip(),
                        "review_pct": int(rv.group(3)) if rv else None,
                        "review_count": int(rv.group(4).replace(",", "")) if rv else None,
                        "review_summary": html.unescape(rv.group(2)) if rv else None})
            store[appid] = rec; n += 1
        print(f"deck={deck} start={start}/{total} rows={n} total_store={len(store)}", flush=True)
        if n == 0 or start + 50 >= total or (RANGE and start + 50 >= RANGE[1]): break
        start += 50
        time.sleep(2.0)
        if start % 500 == 0:
            OUT.write_text(json.dumps(store))
            if not RANGE: STATE.write_text(json.dumps({**st, "deck": deck, "start": start}))
    if not RANGE: STATE.write_text(json.dumps({"done": sorted(set(st.get("done", []) + [deck]))}))
    return store

RANGE = None
if __name__ == "__main__":
    # optional: python3 crawl_steam_search.py <deck> <start> <end>  -> re-crawl just that page range
    DECKS = (3, 2)
    if len(sys.argv) == 4:
        DECKS = (int(sys.argv[1]),); RANGE = (int(sys.argv[2]), int(sys.argv[3]))
    store = {}
    if OUT.exists():
        store = {int(k): v for k, v in json.loads(OUT.read_text()).items()}
    for deck in DECKS:
        crawl(deck, store)
        OUT.write_text(json.dumps(store))
    print("DONE", len(store))
