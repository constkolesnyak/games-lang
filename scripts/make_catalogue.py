"""Render CATALOGUE.md from data/games_scored.csv (index.html is rendered by make_html.py).

CATALOGUE.md is generated — it is the full listing that README.md links to. Do not hand-edit it.
"""
import math, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "data"
g = pd.read_csv(D / "games_scored.csv", low_memory=False)
for c in ("de", "ja", "tags", "tier5", "tier4", "developers", "publishers", "genres", "langs_audio", "langs_text", "desc", "review_summary"):
    g[c] = g[c].fillna("")
for c in ("de_ui", "de_sub", "ja_ui", "ja_sub"):
    g[c] = g[c].fillna(False).astype(bool)
g["machine"] = g["machine"].fillna(0).astype(int); g["steamos"] = g["steamos"].fillna(0).astype(int); g["deck"] = g["deck"].fillna(0).astype(int)
g["picked"] = g["picked"].fillna(False).astype(bool); g["picked_source"] = g["picked_source"].fillna("")
allruns = g[(g.deck >= 2) | (g.machine >= 2) | (g.steamos >= 2)].copy()
runs = allruns[allruns.lang_ok].copy(); textonly = allruns[~allruns.lang_ok & ~allruns.picked].copy()
pickedrows = g[g.picked].copy()
g["mine"] = g["mine"].fillna(""); minerows = g[g.mine != ""].copy()

def lang_cell3(r, lang):
    audio = getattr(r, lang) == "audio"; ui = bool(getattr(r, lang + "_ui")); sub = bool(getattr(r, lang + "_sub"))
    if not (audio or ui or sub): return "—"
    return ("🔊" if audio else "") + ("🖥" if ui else "") + ("💬" if sub else "")
def compat_cell(r):
    if r.appid < 0: return "🚫 not on Steam"
    m = {3: "✅ Verified", 2: "🟡 Playable", 1: "❌", 0: "❔"}
    best = max(r.deck, r.machine)
    s = m.get(best, "❔")
    if r.machine == 0 and r.deck == 0 and r.steamos >= 2: s = "🟢 SteamOS"
    return s
def fmt_reviews(n): return f"{n/1000:.0f}k" if n >= 1000 else str(n)
def rating_cell(r):
    mc = f" · MC {int(r.metacritic)}" if r.metacritic and r.metacritic > 0 else ""
    return f"**{r.review_pct:.0f}%**{mc}"

def table(df, n=None):
    df = df if n is None else df.head(n)
    out = ["| # | Game | Year | 🇩🇪 | 🇯🇵 | Steam Machine | Rating | Reviews | Tags |", "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(df.itertuples(), 1):
        tags = ", ".join(r.tags.split(", ")[:6])
        warn = "" if getattr(r, "lang_ok", True) else "⚠️ "
        kind = f" `{r.kind}`" if hasattr(r, "kind") else ""
        out.append(f"| {i} | {warn}[{r.name}]({r.url}){kind} | {int(r.year) if not math.isnan(r.year) else ''} | {lang_cell3(r, "de")} | {lang_cell3(r, "ja")} | {compat_cell(r)} | {rating_cell(r)} | {fmt_reviews(r.reviews)} | {tags} |")
    return "\n".join(out)

SA = runs[runs.bucket.isin(["S", "A"])]
sections = []
def sec(title, blurb, df, n):
    sections.append(f"\n## {title}\n\n{blurb}\n\n" + table(df, n=n) + "\n")

sec("⭐ Top 150 (language density × popularity)", "Combined ranking: tag score plus the number and share of positive reviews. Buckets S and A only, ≥ 2,000 reviews.",
    runs[runs.bucket.isin(["S", "A"]) & (runs.reviews >= 2000)].sort_values("rank_score", ascending=False), 150)
sec("🔥 Popular right now", "Story-driven games with the most concurrent players (peak CCU) among those that pass the filter.",
    runs[runs.bucket.isin(["S", "A", "B"]) & (runs.reviews >= 2000)].sort_values("peak_ccu", ascending=False), 40)
sec("🏛 Classics", "Released 2016 or earlier, ≥ 88 % positive, ≥ 5,000 reviews.",
    runs[runs.bucket.isin(["S", "A", "B"]) & (runs.year <= 2016) & (runs.review_pct >= 88) & (runs.reviews >= 5000)].sort_values("reviews", ascending=False), 50)
sec("🏆 Critically acclaimed (Metacritic ≥ 85)", "Story-driven games with a Metacritic score of 85 or more — proven writing and direction.",
    runs[runs.bucket.isin(["S", "A", "B"]) & (runs.metacritic >= 85)].sort_values(["metacritic", "reviews"], ascending=False), 60)
sec("📖 Visual novels, interactive fiction and dialogue-driven games", "Bucket S: reading or listening *is* the game. The most language per minute of play.",
    runs[(runs.bucket == "S") & (runs.reviews >= 500)].sort_values("rank_score", ascending=False), 120)
sec("🎭 Story-rich RPGs (JRPG / CRPG / party-based)", "Bucket A with RPG tags: dialogue, quest text and lore in bulk.",
    runs[(runs.bucket == "A") & runs.tags.str.contains("RPG") & (runs.reviews >= 1000)].sort_values("rank_score", ascending=False), 120)
sec("🕵️ Adventures, point-and-click, detective and walking sims", "Bucket A without the RPG slant.",
    runs[(runs.bucket == "A") & ~runs.tags.str.contains("RPG") & (runs.reviews >= 1000)].sort_values("rank_score", ascending=False), 100)
sec("🎥 Narrative action and big fully-dubbed games", "Bucket B: action, open world or strategy, but with a full dub or a lot of text. Less language per minute, more motivation to keep playing.",
    runs[(runs.bucket == "B") & (runs.reviews >= 10000)].sort_values("rank_score", ascending=False), 100)
sec("🇩🇪 German studios with a German voice track", "Developer from Germany, Austria or Switzerland (Daedalic, Piranha Bytes, KING Art, Deck13, Mimimi, Black Forest…) — here the German voice track is the original, not a dub. Plus German publishers (Daedalic, Application Systems, Headup, astragon) that dub everything into German.",
    runs[(runs.de_origin | runs.de_publisher) & runs.de_audio & (runs.reviews >= 300)].sort_values("rank_score", ascending=False), 80)
sec("🇯🇵 Japanese games with a Japanese voice track", "Japanese developer or publisher, Japanese voice track — the original.",
    runs[runs.jp_origin & runs.ja_audio & (runs.reviews >= 1000)].sort_values("rank_score", ascending=False), 120)

n_all = len(runs); n_sa = len(SA); n_verified = int(runs["verified"].fillna(False).astype(bool).sum()) if "verified" in runs else 0
head = f"""# Catalogue: Steam games for learning German and Japanese on a Steam Machine / Steam Deck

> This file is generated (`make CATALOGUE.md`) from `data/games_scored.csv` on {pd.Timestamp.today():%Y-%m-%d}; edit `scripts/make_catalogue.py`, not this file.
> What the project is and how the pipeline works: [README](README.md).

Steam's catalogue, filtered: {int(g.lang_ok.sum()):,} games pass the language filter, {n_all:,} of them are confirmed to run on a Steam Machine / Steam Deck / SteamOS.
The full table is [`data/games.csv`](data/games.csv) (every game that passes the filter, with its language-density score); the interactive version is `make serve` → **<http://localhost:8777/>** (also on the LAN, e.g. from a Steam Machine or a tablet: `http://<host>.local:8777/`).

Per-game statuses live in [`data/status.json`](data/status.json): the local server `scripts/serve.py` writes the file and commits every change (`AUTO_PUSH=1` also pushes). Hand-picked additions go in [`data/picked.json`](data/picked.json). Rebuild with `make all`.

## Criteria

1. **Language.** If the game has a voice track, German or Japanese must be among the *full-audio* languages.
   If it has no voice track at all, German or Japanese must be among the interface / subtitle languages.
   (Games with an English-only voice track and German subtitles do **not** pass: they are flagged in the dataset but kept out of the lists.)
2. **Steam Machine.** Steam Machine Verified / Playable, or Steam Deck Verified / Playable (Valve counts every Deck Verified game as Steam Machine Verified), or SteamOS Compatible.
3. **Language density.** Scored from Steam user tags (`scripts/tagscore.py`):
   `S` — visual novels, interactive fiction, dialogue-heavy; `A` — story-rich RPGs and adventures; `B` — narrative action / strategy with a lot of text or a full dub; `C` — language barely needed (never listed).
4. **Popularity.** Number and share of positive reviews, owners, concurrent players (peak CCU).

Explicitly adult games (see `EXCLUDE_TAGS` in `scripts/tagscore.py`) are excluded from every list.

Language columns: 🔊 full voice track, 🖥 interface, 💬 subtitles; only what the game has is shown, "—" means the language is absent. For example "🔊🖥💬" — everything; "🖥" — interface only (a game without voice); "🖥💬" — text and subtitles, voice track in other languages.
Rating — share of positive Steam reviews and the Metacritic score (MC) when there is one.
✅ Verified / 🟡 Playable — the Steam Machine rating (or the Deck rating while Machine has none); 🟢 SteamOS — only the SteamOS Compatible flag.

Data caveat: for some older games Steam does not mark voice languages with an asterisk, so they count as "no voice" and pass on text alone although they may only have an English voice track. For {n_verified:,} top games the languages were re-checked against the live Steam API (`verified` column in the CSV).

Sources: [FronkonGames Steam Games Dataset](https://huggingface.co/datasets/FronkonGames/steam-games-dataset) (languages, reviews, owners), Steam search (Deck Verified / Playable, top tags), `ajaxgetdeckappcompatibilityreport` (Deck / SteamOS / Steam Machine), SteamSpy (full tag lists).
Rebuild: `make all` (see `Makefile`); local site: `make serve`.
"""
sec("🎬 Hand-picked (from videos and recommendations)", "Games from `data/picked.json`, shown regardless of the language filter (those that fail it are marked ⚠️ in the language column). On the site this is the 🎬 chip.",
    pickedrows.sort_values("rank_score", ascending=False), 100)
KIND = {"owned": "library", "wishlist": "wishlist", "followed": "following", "ignored": "ignored"}
minerows["kind"] = minerows.mine.map(lambda m: ", ".join(KIND.get(k, k) for k in m.split(",")))
sec("👤 Owner's Steam account (library + wishlist)", "Everything in the owner's Steam account (`data/steam_account.json`, a snapshot of store.steampowered.com/dynamicstore/userdata). Shown regardless of the language filter; games that fail it are marked ⚠️. On the site this is the 👤 chip.",
    minerows.sort_values(["kind", "rank_score"], ascending=[True, False]), 200)
sec("📝 Appendix: subtitles only (voice track in other languages)", "Fail the main filter — English or other voice, but German or Japanese text. Buckets S/A, ≥ 5,000 reviews. Full list: `data/games_text_only.csv`.",
    textonly[textonly.bucket.isin(["S", "A"]) & (textonly.reviews >= 5000)].sort_values("rank_score", ascending=False), 60)
(ROOT / "CATALOGUE.md").write_text(head + "".join(sections))
print("CATALOGUE:", len(runs), "runs;", {k: int(v) for k, v in runs.bucket.value_counts().items()})
