"""Join everything into data/games_scored.csv + data/games_scored.json.

Inputs:
  data/steam_lang.parquet        — FronkonGames Steam dataset (languages, reviews, owners ...)
  data/steam_deck_search.json    — Steam search crawl: Deck Verified/Playable games + top-7 tag ids
  data/details.json              — compat report (deck/os/machine) + SteamSpy tags per candidate
  data/steam_tags.json           — tag id -> name
Filter:
  * game has voice-over  -> German or Japanese must be among full-audio languages
  * game has no voice    -> German or Japanese must be among interface/subtitle languages
  * runs on Steam Machine: Deck Verified / Playable, or Steam Machine Verified / Playable, or SteamOS compatible
  * ranked by language intensity (tags) x popularity
  * explicitly adult games (tagscore.EXCLUDE_TAGS) are dropped from every output
"""
import json, pathlib, re, sys
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tagscore as T

D = pathlib.Path(__file__).resolve().parent.parent / "data"
df = pd.read_parquet(D / "steam_lang.parquet")
search = {int(k): v for k, v in json.loads((D / "steam_deck_search.json").read_text()).items()}
details = {}
for f in ("details.json", "details_extra.json", "details_spy2.json", "details_picked.json", "details_account.json"):
    if (D / f).exists():
        for k, v in json.loads((D / f).read_text()).items():
            details.setdefault(k, {}).update({kk: vv for kk, vv in v.items() if vv is not None})

verified = json.loads((D / "verified_langs.json").read_text()) if (D / "verified_langs.json").exists() else {}
verified = {k: v for k, v in verified.items() if v}
LANGFLAGS = json.loads((D / "langflags.json").read_text()) if (D / "langflags.json").exists() else {}   # appid -> {"de": [ui, audio, subs], "ja": [...]}
ACCT = json.loads((D / "steam_account.json").read_text()) if (D / "steam_account.json").exists() else {}
MINE = {}                                             # appid -> "owned" | "wishlist" | "followed" | "ignored" (comma-joined)
for kind in ("owned", "wishlist", "followed", "ignored"):
    for a in ACCT.get(kind, []): MINE[str(a)] = (MINE[str(a)] + "," + kind) if str(a) in MINE else kind
PICKED_ALL = json.loads((D / "picked.json").read_text()) if (D / "picked.json").exists() else {}
PICKED = {k: v for k, v in PICKED_ALL.items() if k.isdigit()}
EXTERNAL = {k: v for k, v in PICKED_ALL.items() if k.startswith("x-")}      # not on Steam: pseudo appids -1, -2, …
EXT_ID = {k: -(i + 1) for i, k in enumerate(EXTERNAL)}
for k, v in EXTERNAL.items(): PICKED[str(EXT_ID[k])] = v
# picked games missing from the dataset snapshot (brand-new releases): synthesize a row from the live store data
missing = [a for a in list(PICKED) + [m for m in MINE if m not in PICKED] if int(a) not in set(df.appid) and (a in verified or int(a) < 0)]
if missing:
    rows_new = []
    for a in missing:
        if int(a) < 0:                                   # external (non-Steam) entry, data straight from picked.json
            e = PICKED[a]
            rows_new.append({"appid": int(a), "name": e["name"], "release_date": str(e.get("year", "")), "year": int(e.get("year") or 0),
                "owners_min": 0, "estimated_owners": "", "peak_ccu": 0, "price": 0.0, "positive": 0, "negative": 0, "reviews_total": 0, "review_pct": 0.0,
                "metacritic_score": 0, "recommendations": 0, "average_playtime_forever": 0, "average_playtime_2weeks": 0, "median_playtime_forever": 0,
                "has_voice": bool(e.get("langs_audio")), "de_text": "German" in e.get("langs_text", []), "ja_text": "Japanese" in e.get("langs_text", []),
                "de_audio": "German" in e.get("langs_audio", []), "ja_audio": "Japanese" in e.get("langs_audio", []),
                "n_langs": len(e.get("langs_text", [])), "n_audio": len(e.get("langs_audio", [])), "genres": [], "categories": [],
                "developers": e.get("developers", []), "publishers": e.get("publishers", []), "short_description": e.get("note", ""), "header_image": "",
                "windows": True, "linux": False, "required_age": 0, "langs": e.get("langs_text", []), "audio": e.get("langs_audio", [])})
            continue
        v = verified[a]; year = pd.to_datetime(v.get("release") or "", errors="coerce")
        if v.get("type") not in (None, "game"): continue
        rows_new.append({"appid": int(a), "name": v["name"], "release_date": v.get("release") or "", "year": year.year if pd.notna(year) else 0,
            "owners_min": 0, "estimated_owners": "", "peak_ccu": 0, "price": 0.0, "positive": 0, "negative": 0, "reviews_total": 0, "review_pct": 0.0,
            "metacritic_score": 0, "recommendations": 0, "average_playtime_forever": 0, "average_playtime_2weeks": 0, "median_playtime_forever": 0,
            "has_voice": bool(v["audio"]), "de_text": "German" in v["text"], "ja_text": "Japanese" in v["text"], "de_audio": "German" in v["audio"],
            "ja_audio": "Japanese" in v["audio"], "n_langs": len(v["text"]), "n_audio": len(v["audio"]), "genres": [], "categories": [], "developers": [],
            "publishers": [], "short_description": "", "header_image": "", "windows": True, "linux": False, "required_age": 0,
            "langs": v["text"], "audio": v["audio"]})
    df = pd.concat([df, pd.DataFrame(rows_new)], ignore_index=True)
df["verified"] = False
if verified:   # live Steam store data beats the dataset snapshot
    key = df.appid.astype(str); m = key.isin(verified.keys())
    vt = key[m].map(lambda k: verified[k]["text"]); va = key[m].map(lambda k: verified[k]["audio"])
    df.loc[m, "langs"] = vt; df.loc[m, "audio"] = va
    df.loc[m, "has_voice"] = va.map(bool).values
    df.loc[m, "de_text"] = vt.map(lambda t: "German" in t).values; df.loc[m, "ja_text"] = vt.map(lambda t: "Japanese" in t).values
    df.loc[m, "de_audio"] = va.map(lambda t: "German" in t).values; df.loc[m, "ja_audio"] = va.map(lambda t: "Japanese" in t).values
    df.loc[m, "n_audio"] = va.map(len).values; df.loc[m, "n_langs"] = vt.map(len).values
    df.loc[m, "verified"] = True
lang_ok = ((df.has_voice & (df.de_audio | df.ja_audio)) | (~df.has_voice & (df.de_text | df.ja_text)))
text_only = df.has_voice & ~(df.de_audio | df.ja_audio) & (df.de_text | df.ja_text)   # appendix: DE/JA subtitles, voice in other languages
picked = df.appid.astype(str).isin(PICKED.keys()); mine = df.appid.astype(str).isin(MINE.keys())
df = df[lang_ok | text_only | picked | mine].copy()
df["lang_ok"] = lang_ok[df.index]; df["picked"] = picked[df.index]; df["mine"] = mine[df.index]

JP_PUBS = re.compile(r"sega|atlus|square enix|capcom|bandai namco|falcom|spike chunsoft|koei tecmo|fromsoftware|level-5|nippon ichi|nis america|idea factory|compile heart|kadokawa|arc system|marvelous|xseed|d3 publisher|aquaplus|shiravune|nekonyan|mangagamer|sekai project|jast|frontwing|key\b|visual arts|nitroplus|type-moon|aniplex|konami|platinum|cygames|gust|inti creates|granzella|kemco|cyberconnect|dmm|g-mode|entergram|mages|5pb|cave\b|taito|arc system works|acquire|tose|clouded leopard|playism|degica|dangen|room6|kakehashi|japan|tokyo|osaka|kyoto|nihon|kojima|team ninja|omega force|ryu ga gotoku|tri-ace|imageepoch|experience inc|orange_juice|fruitbat|edelweiss|hakama|toydea|nintendo|vanillaware|grasshopper|toybox|bushiroad|furyu|sting\b|h\.a\.n\.d\.|ruminant|jupiter|zap\b|arc system|dear villagers|liar-soft|minori|purple software|sprite\b|yuzusoft|saga planets|smee|hooksoft|asa project|palette|silky|moonstone|august\b|navel|alicesoft|eushully|light\b|innocent grey|propeller|giga\b|circus\b|akabeisoft|lump of sugar|whirlpool|windmill|parasol|cabbit|azurite|pulltop|will\b|nexton|studio ryokucha|monobeno|lose\b|kamikaze\b", re.I)
DE_PUBS = re.compile(r"daedalic|piranha bytes|king art|deck13|blue byte|ubisoft blue byte|ubisoft mainz|ubisoft düsseldorf|thq nordic|nordic games|deep silver|koch media|plaion|kalypso|crytek|yager|mimimi|megagon|application systems|headup|assemble entertainment|rockfish|limbic|realmforge|gaming minds|ravenscourt|wild river|astragon|aerosoft|giants software|mad head|sunlight games|studio fizbin|independent arts|pixel maniacs|toplitz|jumpgate|paintbucket|klabater|pow wow|the games company|black forest games|bit composer|chimera|jowood|radon labs|ascaron|eipix|wolpertinger|spellbound|keen games|kalypso media|bigpoint|innogames|goodgame|travian|upjers|gameforge|dreamhaven|rokapublish|byterockers|bavaria|berlin|hamburg|münchen|munich|köln|cologne|frankfurt|stuttgart|leipzig|dresden|nürnberg|wien|vienna|zürich|zurich|austria|switzerland|germany|deutschland", re.I)

DE_SELFPUB = re.compile(r"daedalic|application systems|headup|assemble entertainment|astragon|aerosoft|rokapublish|mimimi|piranha bytes|king art|deck13|studio fizbin", re.I)

# Valve's compat-report tokens -> short English notes (games.csv "compat_notes"; index.html carries the raw tokens)
NOTE = {"DefaultControllerConfigFullyFunctional": "controller: fully functional", "ControllerGlyphsMatchDevice": "button glyphs match the device",
    "ControllerGlyphsDoNotMatchDevice": "button glyphs from another controller", "DefaultConfigurationIsPerformant": "performance OK",
    "DefaultConfigurationNotPerformant": "performance below par", "InterfaceTextIsLegible": "text legible", "TextIsNotLegible": "small text",
    "LauncherInteractionIssues": "launcher needs manual interaction", "FirstTimeSetupRequiresActiveInternetConnection": "first launch needs internet",
    "ExternalControllersNotSupportedPrimaryPlayer": "external controllers not supported for player 1", "CrossPlatformCloudSavesNotSupported": "no cross-platform cloud saves",
    "UnsupportedAntiCheatConfiguration": "anti-cheat unsupported on SteamOS", "UnsupportedAntiCheat_Other": "anti-cheat unsupported",
    "NativeResolutionNotSupported": "native resolution unsupported", "DisplaysCompatibilityWarnings": "shows compatibility warnings",
    "GameOrLauncherDoesntRunOnLinux": "game or launcher does not run on Linux", "UnsupportedGraphicsPerformance": "weak graphics performance",
    "SteamOSDoesNotSupport": "unsupported by SteamOS", "GameStartupFunctional": "starts up", "VideoPlaybackHasNonblockingIssues": "non-blocking video playback issues",
    "RequiresInternetForSetup": "first launch needs internet", "SteamDeckVerified": "", "ResolutionWarning": "resolution warning",
    "DefaultControllerConfigNotFullyFunctional": "controller: not fully functional", "LauncherNotFunctional": "launcher not functional", "AuxFunctionalityNotAccessible": "some functionality inaccessible"}
def tokens(a):
    c = (details.get(str(a)) or {}).get("compat") or {}
    return ";".join(dict.fromkeys(c.get("machine_items") or c.get("deck_items") or []))
def notes(a):
    return "; ".join(dict.fromkeys(NOTE.get(t, t.replace("_", " ")) for t in tokens(a).split(";") if t and NOTE.get(t, t)))

def lf(a, r, lang, i):
    """interface(0) / subtitles(2) flag; falls back to the plain language list when the store API had no data."""
    f = (LANGFLAGS.get(str(a)) or {}).get(lang) if a > 0 else None
    if f: return bool(f[i])
    has = (r.de_text if lang == "de" else r.ja_text)
    return bool(has) if i == 0 else bool(has and r.has_voice)

def spy_tags(a):
    d = details.get(str(a), {}).get("spy") or {}
    tags = d.get("tags") or {}
    return [t for t, _ in sorted(tags.items(), key=lambda kv: -kv[1])]

rows = []; n_adult = 0
for r in df.itertuples():
    a = int(r.appid)
    s = search.get(a); det = details.get(str(a), {}); comp = det.get("compat") or {}
    deck = comp.get("deck") if comp.get("deck") not in (None, 0) else (s or {}).get("deck")
    machine = comp.get("machine"); os_ = comp.get("os")
    if not s and not comp:      # compat unknown -> keep row but mark; filtered later
        deck = deck or 0
    tag_names = spy_tags(a) if a > 0 else list(PICKED.get(str(a), {}).get("tags", []))
    if tag_names:
        ids = [T.NAME2ID.get(t) for t in tag_names]; ids = [i for i in ids if i]
        tag_src = "spy"
    elif s and s.get("tagids"):
        ids = s["tagids"]; tag_names = [T.TAGS.get(i, str(i)) for i in ids]; tag_src = "search"
    else:
        ids, tag_src = [], "none"
    if T.is_adult(tag_names): n_adult += 1; continue     # explicit adult games: out of every list
    sc, top, t5, t4 = T.score(ids)
    devs = " ".join(list(r.developers)); pubs = " ".join(list(r.publishers))
    spy = det.get("spy") or {}
    rv = det.get("reviews") or {}          # live appreviews summary (fetched for hand-picked games)
    reviews = max(int(r.reviews_total), int((s or {}).get("review_count") or 0), int((spy.get("positive") or 0) + (spy.get("negative") or 0)), int(rv.get("total") or 0))
    review_pct = float(r.review_pct) if r.reviews_total >= 50 else (float((s or {}).get("review_pct") or 0) if s and s.get("review_pct") else (float(rv["pct"]) if rv.get("total") else float(r.review_pct)))
    ccu = max(int(r.peak_ccu), int(spy.get("ccu") or 0))
    de_mode = "audio" if r.de_audio else ("text" if r.de_text else "")
    ja_mode = "audio" if r.ja_audio else ("text" if r.ja_text else "")
    rows.append(dict(appid=a, name=r.name, year=r.year, release_date=r.release_date,
        deck=deck, machine=machine, steamos=os_, compat_src=("api" if comp else ("search" if s else "")),
        has_voice=bool(r.has_voice), de=de_mode, ja=ja_mode, de_audio=bool(r.de_audio), ja_audio=bool(r.ja_audio),
        de_text=bool(r.de_text), ja_text=bool(r.ja_text), n_audio=int(r.n_audio),
        jp_origin=bool(JP_PUBS.search(devs)),
        de_origin=bool(DE_PUBS.search(devs)), de_publisher=bool(DE_SELFPUB.search(pubs)), verified=bool(r.verified), lang_ok=bool(r.lang_ok),
        picked=bool(r.picked), picked_source=PICKED.get(str(a), {}).get("source", "") if r.picked else "",
        mine=MINE.get(str(a), ""),
        compat_notes=notes(a), compat_tokens=tokens(a), de_ui=lf(a, r, "de", 0), ja_ui=lf(a, r, "ja", 0), de_sub=lf(a, r, "de", 2), ja_sub=lf(a, r, "ja", 2),
        reviews=reviews, review_pct=review_pct, review_summary=(s or {}).get("review_summary") or "", owners_min=int(r.owners_min), peak_ccu=ccu,
        playtime_2w=int(r.average_playtime_2weeks), metacritic=int(r.metacritic_score), price=float(r.price),
        score=sc, top_tier=top, bucket=T.bucket(top, sc), tags=", ".join(tag_names[:12]), tag_src=tag_src,
        tier5=", ".join(t5), tier4=", ".join(t4),
        genres=", ".join(r.genres), developers=", ".join(r.developers), publishers=", ".join(r.publishers),
        langs_audio=", ".join(r.audio), langs_text=", ".join(r.langs), desc=r.short_description, header=r.header_image,
        url=PICKED[str(a)]["url"] if a < 0 else f"https://store.steampowered.com/app/{a}/"))
out = pd.DataFrame(rows)
out["popularity"] = (out.reviews.clip(lower=1)).map(lambda x: __import__("math").log10(x))
out["rank_score"] = out.score + out.popularity * 3 + (out.review_pct - 80).clip(lower=-40) / 5
out = out.sort_values("rank_score", ascending=False)
out.to_csv(D / "games_scored.csv", index=False)          # everything incl. text-only appendix (git-ignored, big)
runs = out[(out.deck >= 2) | (out.machine.fillna(0) >= 2) | (out.steamos.fillna(0) >= 2)]
ok = out[((out.deck >= 2) | (out.machine.fillna(0) >= 2) | (out.steamos.fillna(0) >= 2)) & out.lang_ok | out.picked | (out.mine != "")]
cols = ["appid","name","year","de","ja","has_voice","deck","machine","steamos","bucket","score","reviews","review_pct","review_summary","peak_ccu",
        "metacritic","jp_origin","de_origin","verified","lang_ok","picked","picked_source","mine","de_ui","de_sub","ja_ui","ja_sub","compat_notes","tags","developers","publishers","langs_audio","langs_text","url"]
ok[cols].to_csv(D / "games.csv", index=False)               # the deliverable: runs on Machine/Deck/SteamOS
runs[~runs.lang_ok & runs.bucket.isin(["S", "A", "B"]) & (runs.reviews >= 2000)][cols].to_csv(D / "games_text_only.csv", index=False)
print("picked:", int(out.picked.sum()), "of", len(PICKED), "| mine:", int((out.mine != "").sum()), "of", len(MINE), "| adult excluded:", n_adult)
out = out[out.lang_ok]
print("lang_ok:", len(out), "| runs on Machine/Deck:", len(ok), "| with tags:", (out.tag_src != "none").sum(), "| spy tags:", (out.tag_src == "spy").sum())
print("by bucket (runs):", ok.bucket.value_counts().to_dict())
print("bucket S/A with >=1000 reviews:", len(ok[(ok.bucket.isin(["S", "A"])) & (ok.reviews >= 1000)]))
