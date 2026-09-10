"""Render index.html — a self-contained, filterable table of the scored games.
Per-game statuses go through scripts/serve.py (data/status.json) when the page is served locally,
and stay in localStorage when it is opened as a plain file."""
import json, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
g = pd.read_csv(ROOT / "data" / "games_scored.csv", low_memory=False)
for c in ("de", "ja", "tags", "developers", "publishers", "langs_audio", "langs_text", "desc", "genres", "review_summary", "compat_tokens"):
    g[c] = g[c].fillna("")
for c in ("machine", "steamos", "deck", "year", "metacritic"):
    g[c] = g[c].fillna(0).astype(int)
g["picked"] = g["picked"].fillna(False).astype(bool); g["picked_source"] = g["picked_source"].fillna(""); g["mine"] = g["mine"].fillna("")
# every game that runs on Machine/Deck and has DE or JA in any form; the default view hides lang_ok=False rows,
# an explicit language chip or a status brings them back
runs = g[(((g.deck >= 2) | (g.machine >= 2) | (g.steamos >= 2)) & (g.reviews >= 100)) | g.picked | (g.mine != "")].copy()
rows = []
for r in runs.itertuples():
    rows.append([int(r.appid), r.name, int(r.year), r.de, r.ja, int(r.has_voice), int(r.deck), int(r.machine), int(r.steamos),
                 int(r.reviews), round(float(r.review_pct)), int(r.peak_ccu), r.bucket, float(r.score), r.tags,
                 int(bool(r.de_origin)), int(bool(r.jp_origin)), r.developers[:60], r.desc[:300], r.langs_audio, float(r.rank_score),
                 int(r.metacritic), int(bool(r.verified)), int(bool(r.picked)), r.picked_source, int(bool(r.lang_ok)), r.url, r.mine,
                 int(bool(r.de_ui)), int(bool(r.de_sub)), int(bool(r.ja_ui)), int(bool(r.ja_sub)), r.compat_tokens])
data = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
stamp = pd.Timestamp.today().strftime("%Y-%m-%d %H:%M")
n_picked = int(runs.picked.sum()); n_mine = int((runs.mine != "").sum())

page = r"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="darkreader-lock">
<meta name="color-scheme" content="dark light">
<title>Sprachspiele · 言語ゲーム</title>
<meta name="description" content="Steam games with a German or Japanese voice track or text that run on a Steam Machine or Steam Deck, sorted by language density.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --bg:#EEF1F5; --surface:#FFFFFF; --surface-2:#F7F9FB; --line:#D5DCE4; --ink:#151E28; --muted:#5A6A7B; --faint:#8C99A8;
  --accent:#0E6F7B; --accent-ink:#FFFFFF; --accent-soft:#D9EEF0;
  --de:#B8901E; --de-soft:#F6EBC7; --ja:#C0392B; --ja-soft:#F9DCD8;
  --ok:#2E7D4F; --ok-soft:#DCEFE3; --warn:#B26A00; --warn-soft:#FBE8C8; --bad:#B3261E; --bad-soft:#F8DCDA; --os:#3A6FB0; --os-soft:#DCE7F6;
  --s:#5B3FA6; --s-soft:#E7DFF7; --a:#0E6F7B; --a-soft:#D9EEF0; --b:#6B7A8A; --b-soft:#E4E9EE; --c:#9AA6B2; --c-soft:#EEF1F4;
  --n-gray:#787774; --n-gray-bg:#E3E2E0; --n-brown:#9F6B53; --n-brown-bg:#EEE0DA; --n-orange:#D9730D; --n-orange-bg:#FADEC9;
  --n-yellow:#CB912F; --n-yellow-bg:#FDECC8; --n-green:#448361; --n-green-bg:#DBEDDB; --n-blue:#337EA9; --n-blue-bg:#D3E5EF;
  --n-purple:#9065B0; --n-purple-bg:#E8DEEE; --n-pink:#C14C8A; --n-pink-bg:#F5E0E9; --n-red:#D44C47; --n-red-bg:#FFE2DD;
  --shadow:0 1px 2px rgba(21,30,40,.06),0 8px 24px -12px rgba(21,30,40,.18);
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#0F1620; --surface:#171F2B; --surface-2:#1D2735; --line:#2C3847; --ink:#E7EDF3; --muted:#9AAABB; --faint:#6E7E90;
  --accent:#43B5C2; --accent-ink:#0B1218; --accent-soft:#163B42;
  --de:#E2B93B; --de-soft:#3D3416; --ja:#F0665A; --ja-soft:#4A1F1B;
  --ok:#5CC48A; --ok-soft:#173327; --warn:#E8A33C; --warn-soft:#3F2C10; --bad:#F07A73; --bad-soft:#47201E; --os:#7EA9E6; --os-soft:#1C2E48;
  --s:#B49BF0; --s-soft:#2B2144; --a:#43B5C2; --a-soft:#163B42; --b:#9AAABB; --b-soft:#26313E; --c:#6E7E90; --c-soft:#1D2735;
  --n-gray:#9B9B9B; --n-gray-bg:#373737; --n-brown:#BA856F; --n-brown-bg:#4A3228; --n-orange:#F0A05A; --n-orange-bg:#5C3B23;
  --n-yellow:#E6C04E; --n-yellow-bg:#56452A; --n-green:#6BC48E; --n-green-bg:#243D30; --n-blue:#6BB0DD; --n-blue-bg:#1F3A4D;
  --n-purple:#B58DD8; --n-purple-bg:#3C2E4E; --n-pink:#E27DB3; --n-pink-bg:#4E2A3E; --n-red:#F0776F; --n-red-bg:#5C2A27;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
}}
:root[data-theme="dark"]{
  --bg:#0F1620; --surface:#171F2B; --surface-2:#1D2735; --line:#2C3847; --ink:#E7EDF3; --muted:#9AAABB; --faint:#6E7E90;
  --accent:#43B5C2; --accent-ink:#0B1218; --accent-soft:#163B42;
  --de:#E2B93B; --de-soft:#3D3416; --ja:#F0665A; --ja-soft:#4A1F1B;
  --ok:#5CC48A; --ok-soft:#173327; --warn:#E8A33C; --warn-soft:#3F2C10; --bad:#F07A73; --bad-soft:#47201E; --os:#7EA9E6; --os-soft:#1C2E48;
  --s:#B49BF0; --s-soft:#2B2144; --a:#43B5C2; --a-soft:#163B42; --b:#9AAABB; --b-soft:#26313E; --c:#6E7E90; --c-soft:#1D2735;
  --n-gray:#9B9B9B; --n-gray-bg:#373737; --n-brown:#BA856F; --n-brown-bg:#4A3228; --n-orange:#F0A05A; --n-orange-bg:#5C3B23;
  --n-yellow:#E6C04E; --n-yellow-bg:#56452A; --n-green:#6BC48E; --n-green-bg:#243D30; --n-blue:#6BB0DD; --n-blue-bg:#1F3A4D;
  --n-purple:#B58DD8; --n-purple-bg:#3C2E4E; --n-pink:#E27DB3; --n-pink-bg:#4E2A3E; --n-red:#F0776F; --n-red-bg:#5C2A27;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
}
*{box-sizing:border-box}
[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1480px;margin:0 auto;padding:28px 24px 45vh}   /* room at the bottom so the last rows' menus can be scrolled into view */
header{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px 32px;margin-bottom:22px}
h1{font:700 30px/1.1 "Unbounded","IBM Plex Sans",sans-serif;letter-spacing:-.01em;margin:0;text-wrap:balance}
h1 small{display:block;font:500 12px/1.4 "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.lede{max-width:62ch;color:var(--muted);margin:10px 0 0;font-size:14px}
.stats{display:flex;gap:22px;font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--muted)}
.stats b{display:block;font-size:26px;font-weight:500;color:var(--ink);line-height:1.1;font-variant-numeric:tabular-nums}
.panel{position:sticky;top:0;z-index:5;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:7px 10px;box-shadow:var(--shadow);display:flex;flex-wrap:wrap;gap:5px 12px;align-items:center;margin-bottom:10px}
.grp{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.grp>span{font:500 10px/1 "IBM Plex Mono",monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);margin-right:1px}
.chip{border:1px solid var(--line);background:var(--surface-2);color:var(--ink);border-radius:999px;padding:2px 9px;font-size:12.5px;cursor:pointer;line-height:1.3;user-select:none}
.chip:hover{border-color:var(--accent)}
.chip[aria-pressed="true"]{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.chip[data-state="-1"]{background:var(--bad-soft);color:var(--bad);border-color:var(--bad);text-decoration:line-through}
.chip .x{display:inline-block;margin-right:6px;font-weight:700;opacity:.75;cursor:pointer;padding:0 2px;border-radius:4px}.chip .x:hover{opacity:1;background:rgba(0,0,0,.15)}
.chip[data-state="-1"] .n,.chip[data-state="-1"] .pct{text-decoration:none}
.chip.st{padding-left:8px}.chip.st i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:1px}
.chip:focus-visible,input:focus-visible,select:focus-visible,th:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
input[type=search]{border:1px solid var(--line);background:var(--surface-2);color:var(--ink);border-radius:8px;padding:4px 9px;font:inherit;font-size:13px;min-width:180px}
select{border:1px solid var(--line);background:var(--surface-2);color:var(--ink);border-radius:8px;padding:3px 6px;font:inherit;font-size:12.5px}
.count{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;text-align:right;line-height:1.25}
.count small{display:inline;font-size:10.5px;color:var(--faint);margin-left:8px}
.count .delta{display:inline;font-size:11px;color:var(--accent);font-weight:500;margin-left:8px}
.chip .n{opacity:.7;font-size:11px;margin-left:4px;font-family:"IBM Plex Mono",monospace}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--surface)}
table{border-collapse:collapse;width:100%;min-width:1260px;font-size:14px}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{position:sticky;top:0;background:var(--surface-2);font:500 11px/1.2 "IBM Plex Mono",monospace;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);cursor:pointer;white-space:nowrap;user-select:none;z-index:1}
th.sorted{color:var(--accent)}th .arr{opacity:.6;margin-left:3px}
td.num{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;white-space:nowrap;text-align:right}
th.num{text-align:right}
tr:hover td{background:var(--surface-2)}
td.name{min-width:240px}td.name a{color:var(--ink);font-weight:500}td.name a:hover{color:var(--accent)}
.dev{display:block;color:var(--faint);font-size:12px;margin-top:1px}
.tags{color:var(--muted);font-size:12.5px;max-width:380px}
.tag{cursor:pointer;border-bottom:1px dotted transparent;user-select:none}.tag:hover{color:var(--accent);border-bottom-color:var(--accent)}
.tag.inc{color:var(--accent);background:var(--accent-soft);border-radius:4px;padding:0 4px;font-weight:600;border-bottom:0}
.tag.exc{color:var(--bad);background:var(--bad-soft);border-radius:4px;padding:0 4px;text-decoration:line-through;border-bottom:0}
.chip.texc{background:var(--bad-soft);color:var(--bad);border-color:var(--bad);text-decoration:line-through}.chip.texc:hover{border-color:var(--bad)}
.chip.tclear{border-style:dashed;color:var(--muted)}
.lang{display:inline-flex;gap:4px;justify-content:flex-start;align-items:center;width:70px;box-sizing:border-box;border-radius:6px;padding:2px 6px;font:500 12px/1.4 "IBM Plex Mono",monospace;white-space:nowrap}
.lang.none{width:70px;justify-content:center}
.lang i{font-style:normal}
.lang.audio.de{background:var(--de);color:#fff}.lang.audio.ja{background:var(--ja);color:#fff}
.lang.text.de{background:var(--de-soft);color:var(--de)}.lang.text.ja{background:var(--ja-soft);color:var(--ja)}
.lang.sub{opacity:.75}.lang.none{color:var(--faint)}
.pill{display:inline-block;border-radius:6px;padding:2px 7px;font:500 12px/1.4 "IBM Plex Mono",monospace;white-space:nowrap}
.pill.v{background:var(--ok-soft);color:var(--ok)}.pill.p{background:var(--warn-soft);color:var(--warn)}.pill.o{background:var(--os-soft);color:var(--os)}
.pill.S{background:var(--s-soft);color:var(--s)}.pill.A{background:var(--a-soft);color:var(--a)}.pill.B{background:var(--b-soft);color:var(--b)}.pill.C{background:var(--c-soft);color:var(--c)}
.rate{white-space:nowrap}.rate b{font:500 15px/1.2 "IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
.rate.r4 b{color:var(--ok)}.rate.r3 b{color:var(--accent)}.rate.r2 b{color:var(--warn)}.rate.r1 b{color:var(--bad)}
.rate small{display:block;font-size:11px;color:var(--faint);line-height:1.3}
.mc{display:inline-block;margin-left:6px;border:1px solid var(--line);border-radius:4px;padding:0 5px;font:500 11px/1.5 "IBM Plex Mono",monospace;color:var(--muted);vertical-align:2px}
.orig{font-size:11px;color:var(--faint);margin-left:4px}
.pct{color:var(--muted);font-size:12px}
.vrf{font-size:10px;color:var(--faint);margin-left:4px;vertical-align:1px}
/* Notion-style status: pill button + popover menu */
.stp{display:inline-flex;align-items:center;gap:6px;border:0;border-radius:6px;padding:3px 9px;font:500 12.5px/1.4 "IBM Plex Sans",sans-serif;cursor:pointer;background:var(--n-gray-bg);color:var(--n-gray);white-space:nowrap}
.stp i,.stm i{display:inline-block;width:8px;height:8px;border-radius:50%;background:currentColor;opacity:.85}
.stp.none{background:transparent;border:1px dashed var(--line);color:var(--faint);font-weight:400}.stp.none:hover{border-color:var(--accent);color:var(--accent)}
.stp.gray{background:var(--n-gray-bg);color:var(--n-gray)}.stp.brown{background:var(--n-brown-bg);color:var(--n-brown)}
.stp.orange{background:var(--n-orange-bg);color:var(--n-orange)}.stp.yellow{background:var(--n-yellow-bg);color:var(--n-yellow)}
.stp.green{background:var(--n-green-bg);color:var(--n-green)}.stp.blue{background:var(--n-blue-bg);color:var(--n-blue)}
.stp.purple{background:var(--n-purple-bg);color:var(--n-purple)}.stp.pink{background:var(--n-pink-bg);color:var(--n-pink)}
.stp.red{background:var(--n-red-bg);color:var(--n-red)}
.stm{position:fixed;z-index:20;min-width:170px;max-height:calc(100vh - 16px);overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch;touch-action:pan-y;background:var(--surface);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);padding:6px;display:flex;flex-direction:column;gap:2px}
.stm button{flex:0 0 auto}
.stm button{display:flex;align-items:center;gap:8px;width:100%;border:0;background:transparent;color:var(--ink);text-align:left;border-radius:6px;padding:6px 8px;font:inherit;font-size:13px;cursor:pointer}
.stm button:hover,.stm button:focus-visible{background:var(--surface-2);outline:none}
.stm button span{border-radius:5px;padding:1px 7px;font-weight:500;font-size:12.5px}
.stm button.clear{color:var(--muted);border-top:1px solid var(--line);border-radius:0 0 6px 6px;margin-top:2px;padding-top:8px}
.stm button[aria-checked="true"]::after{content:"✓";margin-left:auto;color:var(--muted)}
.stm button .grip{margin-left:auto;padding-left:10px;color:var(--faint);font:500 12px/1 "IBM Plex Mono",monospace;cursor:grab;touch-action:none;user-select:none}
.stm button[aria-checked="true"] .grip{margin-left:6px}.stm button[aria-checked="true"]::after{margin-left:auto}
.stm button.dragging{background:var(--accent-soft);opacity:.9;cursor:grabbing}
.stm button{cursor:grab}
.pill.u{background:var(--bad-soft);color:var(--bad)}
.pick{font-size:12px;margin-left:5px;cursor:help}
.warn{font-size:11px;margin-left:3px;cursor:help}
.gear{margin-left:6px}
.pop{position:fixed;z-index:30;width:min(440px,calc(100vw - 24px));background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);padding:16px 18px;font-size:13.5px}
.pop h3{margin:0 0 6px;font:600 14px/1.3 "IBM Plex Sans",sans-serif}.pop p{margin:6px 0;color:var(--muted)}.pop code{font:12px "IBM Plex Mono",monospace;background:var(--surface-2);padding:1px 5px;border-radius:4px}
.pop input{width:100%;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);border-radius:8px;padding:8px 10px;font:13px "IBM Plex Mono",monospace;margin:8px 0}
.pop .row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{border:1px solid var(--line);background:var(--surface-2);color:var(--ink);border-radius:8px;padding:6px 12px;font:inherit;font-size:13px;cursor:pointer}.btn.pri{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}.btn:hover{border-color:var(--accent)}
.store{font:500 11px/1 "IBM Plex Mono",monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--faint)}
.store i{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--faint);margin-right:5px;vertical-align:0}.store.on i{background:var(--ok)}.store.err i{background:var(--bad)}.store.busy i{background:var(--warn)}
.store{cursor:pointer}
details.legend{margin:18px 0 0;color:var(--muted);font-size:13px}details.legend summary{cursor:pointer;color:var(--ink);font-weight:500}
details.legend ul{margin:8px 0 0;padding-left:18px;max-width:80ch}
.more{display:block;width:100%;margin:12px 0 0;padding:10px;border:1px dashed var(--line);border-radius:8px;background:transparent;color:var(--accent);font:inherit;cursor:pointer}
.more:hover{background:var(--surface)}
@media (max-width:640px){.wrap{padding:18px 12px 48px}h1{font-size:22px}.stats{gap:14px}.stats b{font-size:20px}}
@media (prefers-reduced-motion:no-preference){.chip{transition:background .12s,color .12s,border-color .12s}}
</style>
<div class="wrap">
<header>
  <div>
    <h1><small>Steam · Deck / Machine · DE + JA · build __STAMP__</small>Sprachspiele · 言語ゲーム</h1>
    <p class="lede">Every Steam game that runs on a Steam Machine / Steam Deck / SteamOS and has German or Japanese in any form: voice track, interface or subtitles. No hidden rules: only the chips and selects in the panel narrow the list. Sorted by "language density": how much language per minute of play. </p>
  </div>
  <div class="stats"><div><b id="st-total">0</b>games in the base</div><div><b id="st-sa">0</b>in buckets S/A</div><div><b id="st-status">0</b>with a status</div><div><b id="st-shown">0</b>shown</div></div>
</header>
<div class="panel" role="region" aria-label="Filters">
  <input id="q" type="search" placeholder="Search, Enter" aria-label="Search" title="Searches name, developer and tags on Enter">
  <button class="chip" id="qall" aria-pressed="true" title="On: search the whole base, filters do not apply. Off: search within the current filters">whole base</button>
  <div class="grp"><span>Language</span>
    <button class="chip de" data-f="de_audio" aria-pressed="false" title="full German voice track">🇩🇪 🔊 voice</button>
    <button class="chip de" data-f="de_ui" aria-pressed="false" title="German interface (menus, HUD, in-game text)">🇩🇪 🖥 interface</button>
    <button class="chip de" data-f="de_sub" aria-pressed="false" title="German subtitles for the voice track">🇩🇪 💬 subtitles</button>
    <button class="chip ja" data-f="ja_audio" aria-pressed="false" title="full Japanese voice track">🇯🇵 🔊 voice</button>
    <button class="chip ja" data-f="ja_ui" aria-pressed="false" title="Japanese interface (menus, HUD, in-game text)">🇯🇵 🖥 interface</button>
    <button class="chip ja" data-f="ja_sub" aria-pressed="false" title="Japanese subtitles for the voice track">🇯🇵 💬 subtitles</button>
  </div>
  <div class="grp"><span>Density</span>
    <button class="chip" data-b="S" aria-pressed="true">S novels</button>
    <button class="chip" data-b="A" aria-pressed="true">A story-rich</button>
    <button class="chip" data-b="B" aria-pressed="true">B action/strategy</button>
    <button class="chip" data-b="C" aria-pressed="true">C the rest</button>
  </div>
  <div class="grp"><span>Machine</span>
    <select id="compat" aria-label="Compatibility"><option value="2">Verified + Playable + SteamOS</option><option value="3">Verified only</option></select>
  </div>
  <div class="grp"><span>Reviews ≥</span>
    <select id="minrev" aria-label="Minimum reviews"><option value="100" selected>100</option><option value="500">500</option><option value="2000">2,000</option><option value="10000">10,000</option><option value="50000">50,000</option></select>
  </div>
  <div class="grp"><span>Rating ≥</span>
    <select id="minpct" aria-label="Minimum rating"><option value="0">any</option><option value="70">70%</option><option value="80">80%</option><option value="90">90%</option><option value="95">95%</option></select>
  </div>
  <div class="grp"><span>Origin</span>
    <button class="chip" data-o="de" aria-pressed="false">🇩🇪 German studio</button>
    <button class="chip" data-o="jp" aria-pressed="false">🇯🇵 Japanese studio</button>
  </div>
  <div class="grp"><span>Collections</span>
    <button class="chip" id="pickchip" aria-pressed="false" title="Hand-picked games from videos and recommendations (data/picked.json), shown regardless of the filters">🎬 hand-picked <span class="pct">{n_picked}</span></button>
    <button class="chip" id="minechip" aria-pressed="false" title="Everything in my Steam account: library, wishlist, follows (data/steam_account.json), regardless of the filters">👤 my Steam <span class="pct">{n_mine}</span></button>
    <select id="minekind" aria-label="Which Steam list"><option value="">all lists</option><option value="owned">library</option><option value="wishlist">wishlist</option><option value="followed">following</option><option value="ignored">ignored</option></select>
  </div>
  <div class="grp" id="taggrp" hidden><span>Tags</span></div>
  <div class="grp" id="stgrp"><span>Status</span></div>
  <div class="count"><div id="count"></div><small class="store" id="store" title="Re-read statuses from the repo"><i></i>statuses: loading…</small></div>
</div>
<div class="tablewrap"><table id="t">
<thead><tr>
<th data-k="1">Game</th><th data-k="status">Status</th><th data-k="2" class="num">Year</th><th>🇩🇪</th><th>🇯🇵</th><th>Machine</th>
<th data-k="12">Density</th><th data-k="10">Rating</th><th data-k="9" class="num">Reviews</th><th data-k="11" class="num">Players</th><th>Tags</th>
</tr></thead><tbody id="tb"></tbody></table></div>
<button class="more" id="more" hidden>Show more</button>
<details class="legend"><summary>Legend and criteria</summary><ul>
<li><b>Tri-state chips.</b> Click a chip: off → <b>only this</b> (coloured); further clicks toggle between "only" and "everything except" (red, struck through). The ✕ on the left of an active chip clears the filter. Language, origin, collections and statuses all work this way. Several "only" chips in one group combine with "or"; "except" always excludes.</li>
<li><b>Language.</b> No implicit language rules: with no chips active you see everything in the base. A cell shows only the icons the game has according to its Steam page: 🔊 full voice track, 🖥 interface (menus, HUD, text), 💬 subtitles. A dark plaque means a voice track in that language, a light one means text only. The "voice / interface / subtitles" chips filter on the same flags. The base filter passes a game only if DE/JA is among its voice languages, or the game has no voice track at all.</li>
<li><b>Machine.</b> Verified / Playable / Unsupported — Valve's official rating for the Steam Machine, or for the Steam Deck while the Machine has none. Hover the plaque: the tooltip lists what Valve flagged (launcher, anti-cheat, internet on first launch, performance). Playable = starts and plays, with the caveats from the tooltip. SteamOS — only the SteamOS Compatible flag.</li>
<li><b>Density.</b> Scored from Steam tags: S — visual novels, interactive fiction, dialogue-heavy; A — story-rich RPGs and adventures; B — narrative action, open world, strategy with a lot of text; C — language barely needed.</li>
<li><b>Rating.</b> Share of positive Steam reviews and its verbal summary by Steam's rules (Overwhelmingly Positive = ≥95% with ≥500 reviews, and so on); MC — Metacritic score.</li>
<li><b>Status.</b> A game with a status counts as yours: the base filters (language, compatibility, reviews, density) no longer hide it, only the chips apply. Click the pill to open the menu (always downwards; if space is tight it scrolls inside). Items can be reordered by dragging (on touch screens, by the ⋮⋮ handle); the order is saved to <code>data/prefs.json</code> in the repo and drives the status chips and the sort. Statuses are stored in <code>data/status.json</code> of this repo: the local server <code>scripts/serve.py</code> writes the file and commits it. When the page is opened as a file without the server, only the browser's localStorage is used.</li>
<li><b>Tags.</b> Click a tag in a row to show only games with that tag (several combine with "and"). Double-click does the opposite: hides games with that tag. Active tags are highlighted in the rows and shown as chips in the panel: click a chip to clear the filter, double-click to invert it.</li>
<li><b>👤 my Steam.</b> Library, wishlist, follows and ignores from the Steam account (<code>data/steam_account.json</code>, a snapshot from a logged-in store.steampowered.com session). Shown regardless of the filters; pick the list in the dropdown next to it.</li>
<li><b>🎬 hand-picked.</b> Games from <code>data/picked.json</code> (video recommendations, tips). Shown via the chip.</li>
<li><b>Origin.</b> A studio from Germany / Austria / Switzerland or Japan: the voice track in that language is the original, not a dub.</li>
<li>Data: FronkonGames Steam dataset, Steam search, Steam compatibility report, SteamSpy. Snapshot __STAMP__.</li>
</ul></details>
</div>
<script>
const ROWS=__DATA__;
const I={id:0,name:1,year:2,de:3,ja:4,voice:5,deck:6,machine:7,os:8,rev:9,pct:10,ccu:11,b:12,score:13,tags:14,deo:15,jpo:16,dev:17,desc:18,laudio:19,rank:20,mc:21,vrf:22,pick:23,src:24,lok:25,url:26,mine:27,deui:28,desub:29,jaui:30,jasub:31,notes:32};
const KIND={owned:"library",wishlist:"wishlist",followed:"following",ignored:"ignored"};
const NOTE={DefaultControllerConfigFullyFunctional:"controller: fully functional",ControllerGlyphsMatchDevice:"button glyphs match the device",ControllerGlyphsDoNotMatchDevice:"button glyphs from another controller",DefaultConfigurationIsPerformant:"performance OK",DefaultConfigurationNotPerformant:"performance below par",InterfaceTextIsLegible:"text legible",TextIsNotLegible:"small text",LauncherInteractionIssues:"launcher needs manual interaction",FirstTimeSetupRequiresActiveInternetConnection:"first launch needs internet",ExternalControllersNotSupportedPrimaryPlayer:"external controllers not supported for player 1",CrossPlatformCloudSavesNotSupported:"no cross-platform cloud saves",UnsupportedAntiCheatConfiguration:"anti-cheat unsupported on SteamOS",UnsupportedAntiCheat_Other:"anti-cheat unsupported",NativeResolutionNotSupported:"native resolution unsupported",DisplaysCompatibilityWarnings:"shows compatibility warnings",GameOrLauncherDoesntRunOnLinux:"game or launcher does not run on Linux",UnsupportedGraphicsPerformance:"weak graphics performance",SteamOSDoesNotSupport:"unsupported by SteamOS",GameStartupFunctional:"starts up",VideoPlaybackHasNonblockingIssues:"non-blocking video playback issues",DefaultControllerConfigNotFullyFunctional:"controller: not fully functional",LauncherNotFunctional:"launcher not functional",AuxFunctionalityNotAccessible:"some functionality inaccessible"};
const API="api/status";   // served by scripts/serve.py from this repo; statuses are committed to data/status.json
// status options and their colours
const STATUSES=[["Inbox","gray"],["Checking","yellow"],["To See","blue"],["Next","pink"],["Soon","orange"],["Later","brown"],["Seeing","green"],["On Hold","yellow"],["Completed","purple"],["Dropped","red"],["Skip","gray"],["Permanent","gray"]];
const SCOLOR=Object.fromEntries(STATUSES);
let STATUS_ORDER=STATUSES.map(([n])=>n);
const orderedStatuses=()=>STATUS_ORDER.map(n=>STATUSES.find(x=>x[0]===n)).filter(Boolean).concat(STATUSES.filter(x=>!STATUS_ORDER.includes(x[0])));
const LS_ORDER="sprachspiele.statusOrder";
try{const o=JSON.parse(localStorage.getItem(LS_ORDER)||"null");if(Array.isArray(o)&&o.length)STATUS_ORDER=o}catch(e){}
async function saveOrder(){try{localStorage.setItem(LS_ORDER,JSON.stringify(STATUS_ORDER))}catch(e){}
  try{await fetch("api/prefs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({statusOrder:STATUS_ORDER})})}catch(e){}}
(async()=>{try{const r=await fetch("api/prefs?t="+Date.now(),{cache:"no-store"});if(r.ok){const j=await r.json();if(Array.isArray(j.statusOrder)&&j.statusOrder.length){STATUS_ORDER=j.statusOrder;try{localStorage.setItem(LS_ORDER,JSON.stringify(STATUS_ORDER))}catch(e){}render()}}}catch(e){}})();
// tri-state chips: 0 = off, 1 = only this, -1 = everything except this
const st={q:"",qall:true,de_audio:0,de_ui:0,de_sub:0,ja_audio:0,ja_ui:0,ja_sub:0,b:{S:true,A:true,B:true,C:true},compat:2,minrev:100,minpct:0,o:{de:0,jp:0},status:new Set(),statusExc:new Set(),pick:0,mine:0,minekind:"",tagsInc:[],tagsExc:[],sortK:I.rank,sortD:-1,limit:200};
const tri=v=>v===true?1:v===false||v==null?0:+v;          // old saved booleans → numbers
const cyc=v=>v===0?1:v===1?-1:1;                          // click: off → only → except → only …; the ✕ on the chip clears it
function chipState(el,v){el.dataset.state=v;el.setAttribute("aria-pressed",v===1);
  let x=el.querySelector(".x");
  if(v&&!x){x=document.createElement("i");x.className="x";x.textContent="✕";x.title="clear filter";x.onclick=e=>{e.stopPropagation();if(el._reset)el._reset()};el.prepend(x)}
  else if(!v&&x)x.remove()}
const FLT="sprachspiele.filters";
let lastSaved=null,suppressSave=false;
function serializeFilters(){const o={...st,status:[...st.status].sort(),statusExc:[...st.statusExc].sort()};delete o.limit;return JSON.stringify(o,Object.keys(o).sort())}
function saveFilters(){if(suppressSave)return;try{const v=serializeFilters();if(v===lastSaved)return;lastSaved=v;localStorage.setItem(FLT,v)}catch(e){}}
function loadFilters(){try{const j=JSON.parse(localStorage.getItem(FLT)||"null");if(!j)return;const keep=st.limit;Object.assign(st,j);st.status=new Set(j.status||[]);st.statusExc=new Set(j.statusExc||[]);st.limit=keep;
for(const f of ["de_audio","de_ui","de_sub","ja_audio","ja_ui","ja_sub","pick","mine"])st[f]=tri(st[f]);if(!st.o)st.o={de:0,jp:0};st.o.de=tri(st.o.de);st.o.jp=tri(st.o.jp);if(!st.b)st.b={S:true,A:true,B:true,C:false};if(!st.o)st.o={de:false,jp:false};if(!Array.isArray(st.tagsInc))st.tagsInc=[];if(!Array.isArray(st.tagsExc))st.tagsExc=[]}catch(e){}}
function syncUI(){
  $("#q").value=st.q;$("#qall").setAttribute("aria-pressed",st.qall!==false);
  document.querySelectorAll(".chip[data-f]").forEach(c=>chipState(c,st[c.dataset.f]));
  document.querySelectorAll(".chip[data-b]").forEach(c=>c.setAttribute("aria-pressed",!!st.b[c.dataset.b]));
  document.querySelectorAll(".chip[data-o]").forEach(c=>chipState(c,st.o[c.dataset.o]));
  $("#compat").value=String(st.compat);$("#minrev").value=String(st.minrev);$("#minpct").value=String(st.minpct);
  chipState($("#pickchip"),st.pick);chipState($("#minechip"),st.mine);$("#minekind").value=st.minekind||"";
}
const STATUS={};                       // appid -> status name (merged view)
const LS="sprachspiele.status";
const $=s=>document.querySelector(s);
const fmt=n=>n>=1e6?(n/1e6).toFixed(1)+"M":n>=1e3?Math.round(n/1e3)+"k":String(n);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function lang(r,cls){
  const audio=r[cls==="de"?I.de:I.ja]==="audio", ui=!!r[cls==="de"?I.deui:I.jaui], sub=!!r[cls==="de"?I.desub:I.jasub];
  if(!audio&&!ui&&!sub)return `<span class="lang none">—</span>`;
  const t=[audio?"voice":null,ui?"interface":null,sub?"subtitles":null].filter(Boolean).join(" + ")+(r[I.voice]&&!audio?" · voice track in other languages":"");
  return `<span class="lang ${audio?"audio":"text"} ${cls}" title="${t}">${audio?"<i>🔊</i>":""}${ui?"<i>🖥</i>":""}${sub?"<i>💬</i>":""}</span>`}
function compat(r){if(r[I.id]<0)return `<span class="pill u" title="not on Steam">not Steam</span>`;const best=Math.max(r[I.deck],r[I.machine]);
  const src=r[I.machine]?"Steam Machine":"Steam Deck",notes=r[I.notes]?r[I.notes].split(";").map(k=>NOTE[k]||k.replace(/([a-z])([A-Z])/g,"$1 $2")).filter(Boolean).join("; "):"";const t=esc((notes?notes+" · ":"")+"per Valve's report for "+src);
  if(best>=3)return `<span class="pill v" title="${t}">Verified</span>`;if(best===2)return `<span class="pill p" title="${t}">Playable</span>`;if(r[I.os]>=2)return `<span class="pill o" title="${t}">SteamOS</span>`;if(best===1)return `<span class="pill u" title="${t}">Unsupported</span>`;return `<span class="pct" title="not tested by Valve">—</span>`}
function summary(p,n){if(n<10)return "";if(p>=95&&n>=500)return "Overwhelmingly Positive";if(p>=80&&n>=50)return "Very Positive";if(p>=80)return "Positive";if(p>=70)return "Mostly Positive";if(p>=40)return "Mixed";if(p>=20)return "Mostly Negative";if(n>=500)return "Overwhelmingly Negative";if(n>=50)return "Very Negative";return "Negative"}
function rating(r){const p=r[I.pct],cls=p>=95?"r4":p>=80?"r3":p>=70?"r2":"r1";const mc=r[I.mc]>0?`<span class="mc" title="Metacritic">MC ${r[I.mc]}</span>`:"";return `<div class="rate ${cls}"><b>${p}%</b>${mc}<small>${summary(p,r[I.rev])}</small></div>`}
function statusSel(id){const cur=STATUS[id]||"";const col=cur?SCOLOR[cur]:"none";return `<button class="stp ${col}" data-id="${id}" aria-haspopup="menu" aria-label="Status: ${cur||"none"}">${cur?"<i></i>"+cur:"+ status"}</button>`}
let menu=null;
function closeMenu(){if(menu){menu.remove();menu=null}}
function enableDrag(m){
  let drag=null;
  m.addEventListener("pointerdown",e=>{
    const b=e.target.closest('button[role="menuitemradio"]');if(!b||e.button!==0)return;
    if(e.pointerType!=="mouse"&&!e.target.closest(".grip"))return;      // touch: only via the handle, so the list still scrolls
    drag={b,y0:e.clientY,moved:false,id:e.pointerId};b.setPointerCapture(e.pointerId);
  });
  m.addEventListener("pointermove",e=>{
    if(!drag||e.pointerId!==drag.id)return;const dy=e.clientY-drag.y0;
    if(!drag.moved){if(Math.abs(dy)<4)return;drag.moved=true;m._dragged=true;drag.b.classList.add("dragging")}
    const items=[...m.querySelectorAll('button[role="menuitemradio"]')];
    for(const o of items){if(o===drag.b)continue;const r=o.getBoundingClientRect();const mid=r.top+r.height/2;
      if(e.clientY<mid&&o.compareDocumentPosition(drag.b)&Node.DOCUMENT_POSITION_FOLLOWING){m.insertBefore(drag.b,o);break}
      if(e.clientY>mid&&o.compareDocumentPosition(drag.b)&Node.DOCUMENT_POSITION_PRECEDING){m.insertBefore(drag.b,o.nextSibling);break}}
  });
  const end=e=>{if(!drag||e.pointerId!==drag.id)return;drag.b.classList.remove("dragging");
    if(drag.moved){STATUS_ORDER=[...m.querySelectorAll('button[role="menuitemradio"]')].map(b=>b.dataset.v);saveOrder();render();setTimeout(()=>{if(m)m._dragged=false},0)}
    drag=null};
  m.addEventListener("pointerup",end);m.addEventListener("pointercancel",end);
}
function openMenu(btn){
  closeMenu();const id=+btn.dataset.id,cur=STATUS[id]||"";
  menu=document.createElement("div");menu.className="stm";menu.setAttribute("role","menu");
  menu.innerHTML=orderedStatuses().map(([n,c])=>`<button role="menuitemradio" aria-checked="${n===cur}" data-v="${n}"><span class="stp ${c}"><i></i>${n}</span><b class="grip" title="drag to reorder">⋮⋮</b></button>`).join("")+(cur?`<button class="clear" data-v="">Clear status</button>`:"");
  enableDrag(menu);
  document.body.appendChild(menu);menu._anchor=btn;placeMenu();
  (function track(){if(!menu)return;placeMenu();requestAnimationFrame(track)})();   // follow the pill while scrolling (any scroller, touch momentum too)
  menu.addEventListener("click",e=>{const b=e.target.closest("button[data-v]");if(!b||menu._dragged)return;setStatus(id,b.dataset.v);closeMenu()});
  menu.dataset.for=id; menu.querySelector("button").focus({preventScroll:true});
}
document.addEventListener("click",e=>{const b=e.target.closest("button.stp[data-id]");if(b){e.preventDefault();if(menu&&menu.dataset.for===b.dataset.id)closeMenu();else openMenu(b);return}if(menu&&!menu.contains(e.target))closeMenu()});
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeMenu()});
function placeMenu(){
  if(!menu||!menu._anchor)return;
  if(!menu._anchor.isConnected){const again=document.querySelector(`button.stp[data-id="${menu.dataset.for}"]`);if(!again){closeMenu();return}menu._anchor=again}   // table re-rendered under the menu
  const r=menu._anchor.getBoundingClientRect();
  if(r.bottom<0||r.top>innerHeight){closeMenu();return}          // anchor scrolled away
  const full=menu.scrollHeight+2;                       // full content height, valid even while max-height clips it (never reset it: that kills the menu's own scroll)
  const below=innerHeight-r.bottom-12;                  // always below the pill; scroll the page yourself if it is tight
  const h=Math.min(full,Math.max(60,below));
  const set=(k,v)=>{if(menu.style[k]!==v)menu.style[k]=v};
  set("maxHeight",h+"px");set("top",(r.bottom+4)+"px");
  set("left",Math.max(8,Math.min(r.left,innerWidth-menu.offsetWidth-8))+"px");
}
document.addEventListener("scroll",placeMenu,{passive:true,capture:true});addEventListener("resize",placeMenu);
document.addEventListener("keydown",e=>{if(!menu)return;const items=[...menu.querySelectorAll("button")];const i=items.indexOf(document.activeElement);
  if(e.key==="ArrowDown"){e.preventDefault();(items[i+1]||items[0]).focus()}else if(e.key==="ArrowUp"){e.preventDefault();(items[i-1]||items[items.length-1]).focus()}});
const inMine=r=>!!r[I.mine]&&(!st.minekind||r[I.mine].split(",").includes(st.minekind));
const LANGM={de_audio:r=>r[I.de]==="audio",de_ui:r=>!!r[I.deui],de_sub:r=>!!r[I.desub],ja_audio:r=>r[I.ja]==="audio",ja_ui:r=>!!r[I.jaui],ja_sub:r=>!!r[I.jasub]};
const SEARCH=ROWS.map(r=>(r[I.name]+"\n"+r[I.dev]+"\n"+r[I.tags]).toLowerCase());   // precomputed once: search text per row
const ROWIDX=new Map(ROWS.map((r,i)=>[r,i]));
function matchQ(r){return SEARCH[ROWIDX.get(r)].includes(st.q)}
function ok(r){
  if(st.q){if(st.qall)return matchQ(r);if(!matchQ(r))return false}   // "whole base": search ignores every filter; otherwise it narrows them
  if(st.pick===-1&&r[I.pick])return false;
  if(st.mine===-1&&inMine(r))return false;
  const cur=STATUS[r[I.id]]||"";
  if(st.pick===1||st.mine===1){
    if(!((st.pick===1&&r[I.pick])||(st.mine===1&&inMine(r))))return false;
  }
  else if(!cur){                                          // a game with a status is yours: the selects below never hide it
    if(r[I.rev]<st.minrev||r[I.pct]<st.minpct)return false;
    const best=Math.max(r[I.deck],r[I.machine]);
    if(st.compat===3?best<3:!(best>=2||r[I.os]>=2))return false;
    if(!st.b[r[I.b]])return false;
  }
  let nInc=0,hit=false;
  for(const f in LANGM){const v=st[f];if(!v)continue;const m=LANGM[f](r);if(v===-1&&m)return false;if(v===1){nInc++;if(m)hit=true}}
  if(nInc&&!hit)return false;
  if(st.o.de===1&&!r[I.deo])return false;if(st.o.de===-1&&r[I.deo])return false;
  if(st.o.jp===1&&!r[I.jpo])return false;if(st.o.jp===-1&&r[I.jpo])return false;
  if(st.status.size&&!st.status.has(cur))return false;if(st.statusExc.has(cur))return false;
  if(st.tagsInc.length||st.tagsExc.length){const tl=r[I.tags].split(", ");if(st.tagsInc.some(t=>!tl.includes(t)))return false;if(st.tagsExc.some(t=>tl.includes(t)))return false}
  return true}
function sortVal(r,k){if(k!=="status")return r[k];const s_=STATUS[r[I.id]];if(!s_)return 99;const i=STATUS_ORDER.indexOf(s_);return i<0?98:i}
let lastCount=null,userAct=false;
document.addEventListener("click",e=>{if(e.target.closest(".panel, #tb .tag, th"))userAct=true},true);
document.addEventListener("change",e=>{if(e.target.closest(".panel"))userAct=true},true);
document.addEventListener("input",e=>{if(e.target.closest(".panel"))userAct=true},true);
function langCounts(){   // how many of the otherwise-filtered rows each language chip would keep
  if(st.q&&st.qall){for(const f in LANGM){const c=document.querySelector(`.chip[data-f="${f}"] .n`);if(c)c.textContent=""}return}   // whole-base search ignores chips anyway
  const save={};for(const f in LANGM){save[f]=st[f];st[f]=0}
  const base=ROWS.filter(ok);Object.assign(st,save);
  const n={};for(const f in LANGM)n[f]=0;
  for(const r of base)for(const f in LANGM)if(LANGM[f](r))n[f]++;
  for(const f in n){const c=document.querySelector(`.chip[data-f="${f}"]`);let e=c.querySelector(".n");if(!e){e=document.createElement("span");e.className="n";c.appendChild(e)}e.textContent=n[f]}
}
function render(){
  langCounts();
  const rows=ROWS.filter(ok);const k=st.sortK,d=st.sortD;
  rows.sort((a,b)=>{const x=sortVal(a,k),y=sortVal(b,k);if(x===y)return b[I.rank]-a[I.rank];return (typeof x==="string"?x.localeCompare(y):x-y)*d});
  const show=rows.slice(0,st.limit);
  $("#tb").innerHTML=show.map(r=>`<tr><td class="name"><a href="${esc(r[I.url])}" target="_blank" rel="noopener" title="${esc(r[I.desc])}">${esc(r[I.name])}</a><span class="dev">${esc(r[I.dev])}</span></td><td>${statusSel(r[I.id])}</td><td class="num">${r[I.year]||""}</td><td>${lang(r,"de")}</td><td>${lang(r,"ja")}</td><td>${compat(r)}</td><td><span class="pill ${r[I.b]}">${r[I.b]}</span> <span class="pct">${r[I.score].toFixed(1)}</span></td><td>${rating(r)}</td><td class="num">${fmt(r[I.rev])}</td><td class="num">${r[I.ccu]?fmt(r[I.ccu]):"<span class=pct>—</span>"}</td><td class="tags">${r[I.tags]?r[I.tags].split(", ").slice(0,7).map(t=>`<span class="tag ${tagState(t)}" data-t="${esc(t)}" title="click: only this tag · double-click: exclude it">${esc(t)}</span>`).join(", "):""}</td></tr>`).join("");
  const delta=!userAct?"":lastCount!==rows.length?`<span class="delta">${lastCount} → ${rows.length}</span>`:`<span class="delta" style="color:var(--warn)">list unchanged</span>`;
  $("#count").innerHTML=`${rows.length} games${delta}`;lastCount=rows.length;userAct=false;$("#st-shown").textContent=show.length;saveFilters();
  $("#st-status").textContent=Object.keys(STATUS).length;
  $("#more").hidden=rows.length<=show.length;
  document.querySelectorAll("th").forEach(th=>{const kk=th.dataset.k==="status"?"status":+th.dataset.k;th.classList.toggle("sorted",kk===k);const a=th.querySelector(".arr");if(a)a.remove();if(kk===k)th.insertAdjacentHTML("beforeend",`<span class="arr">${d<0?"↓":"↑"}</span>`)});
  renderStatusChips();renderTagChips();
}
function tagState(t){return st.tagsInc.includes(t)?"inc":st.tagsExc.includes(t)?"exc":""}
function setTag(t,mode){st.tagsInc=st.tagsInc.filter(x=>x!==t);st.tagsExc=st.tagsExc.filter(x=>x!==t);if(mode==="inc")st.tagsInc.push(t);if(mode==="exc")st.tagsExc.push(t);st.limit=200;render()}
function renderTagChips(){
  const g=$("#taggrp");g.querySelectorAll(".chip").forEach(c=>c.remove());
  const items=st.tagsInc.map(t=>[t,"inc"]).concat(st.tagsExc.map(t=>[t,"exc"]));g.hidden=!items.length;
  for(const [t,m] of items){const b=document.createElement("button");b.className="chip "+(m==="inc"?"tinc":"texc");b.setAttribute("aria-pressed",m==="inc");b.textContent=(m==="inc"?"+ ":"− ")+t;b.title=m==="inc"?"only with this tag · click to clear, double-click to invert":"without this tag · click to clear, double-click to invert";
    b.onclick=()=>{clearTimeout(b._t);b._t=setTimeout(()=>setTag(t,""),220)};b.ondblclick=()=>{clearTimeout(b._t);setTag(t,m==="inc"?"exc":"inc")};g.appendChild(b)}
  if(items.length>1){const c=document.createElement("button");c.className="chip tclear";c.textContent="clear tags";c.onclick=()=>{st.tagsInc=[];st.tagsExc=[];render()};g.appendChild(c)}
}
let tagClickTimer=null;
$("#tb").addEventListener("click",e=>{const el=e.target.closest(".tag");if(!el)return;const t=el.dataset.t;clearTimeout(tagClickTimer);tagClickTimer=setTimeout(()=>setTag(t,tagState(t)==="inc"?"":"inc"),220)});
$("#tb").addEventListener("dblclick",e=>{const el=e.target.closest(".tag");if(!el)return;clearTimeout(tagClickTimer);const t=el.dataset.t;setTag(t,tagState(t)==="exc"?"":"exc")});
function renderStatusChips(){
  const counts={};for(const v of Object.values(STATUS))counts[v]=(counts[v]||0)+1;
  const g=$("#stgrp");g.querySelectorAll(".chip").forEach(c=>c.remove());
  const items=[["","none",""]].concat(orderedStatuses().filter(([n])=>counts[n]).map(([n,c])=>[n,c,counts[n]]));
  for(const [n,c,cnt] of items){const b=document.createElement("button");b.className="chip st";b.innerHTML=`<i style="background:var(--n-${c==="none"?"gray":c})"></i>${n||"no status"}${cnt?` <span class="pct">${cnt}</span>`:""}`;chipState(b,st.status.has(n)?1:st.statusExc.has(n)?-1:0);
    b.onclick=()=>{const v=cyc(st.status.has(n)?1:st.statusExc.has(n)?-1:0);st.status.delete(n);st.statusExc.delete(n);if(v===1)st.status.add(n);if(v===-1)st.statusExc.add(n);st.limit=200;render()};
    b._reset=()=>{st.status.delete(n);st.statusExc.delete(n);st.limit=200;render()};g.appendChild(b)}
}
function saveLocal(){try{localStorage.setItem(LS,JSON.stringify(STATUS))}catch(e){}}
const dirty=new Set();let saveTimer=null,saving=false;
function setStatus(id,v){
  if(v)STATUS[id]=v;else delete STATUS[id];
  dirty.add(String(id));saveLocal();render();
  clearTimeout(saveTimer);saveTimer=setTimeout(pushToRepo,1500);
}
// ---- storage: local server (scripts/serve.py) writes data/status.json in the repo and commits it
const NAMES=Object.fromEntries(ROWS.map(r=>[String(r[I.id]),r[I.name]]));
function setStore(cls,text){const el=$("#store");el.className="store "+cls;el.innerHTML=`<i></i>${text}`}
function applyRemote(data){
  for(const k of Object.keys(STATUS))if(!dirty.has(k))delete STATUS[k];
  for(const [k,v] of Object.entries(data)){if(dirty.has(k))continue;const st_=typeof v==="string"?v:v&&v.status;if(st_)STATUS[k]=st_}
  saveLocal();render();
}
let lastPull=0,serverOk=null;
const stamp=()=>new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});
async function pullFromRepo(force){
  if(!force&&Date.now()-lastPull<30000)return;
  if(location.protocol==="file:"){setStore("","statuses: this browser only (open via scripts/serve.py)");return}
  try{const r=await fetch(API+"?t="+Date.now(),{cache:"no-store"});if(!r.ok)throw new Error("HTTP "+r.status);applyRemote(await r.json());lastPull=Date.now();serverOk=true;setStore("on",`statuses: repo ✓ ${stamp()}`)}
  catch(e){serverOk=false;setStore("err","statuses: this browser only (server not responding)")}
}
async function pushToRepo(){
  if(!dirty.size||saving||serverOk===false&&location.protocol==="file:")return;
  saving=true;const ids=[...dirty];
  try{
    setStore("busy","statuses: committing…");
    const body=Object.fromEntries(ids.map(id=>[id,STATUS[id]||null]));
    const r=await fetch(API,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    if(!r.ok)throw new Error("HTTP "+r.status);
    const j=await r.json();ids.forEach(i=>dirty.delete(i));applyRemote(j.data||{});lastPull=Date.now();serverOk=true;
    setStore("on",`statuses: repo ✓ ${stamp()}${j.committed?"":" (not committed)"}`);
  }catch(e){console.warn(e);serverOk=false;setStore("err","statuses: not saved to the repo — server not responding (scripts/serve.py)")}
  finally{saving=false;if(dirty.size&&serverOk)saveTimer=setTimeout(pushToRepo,5000)}
}
$("#store").onclick=()=>pullFromRepo(true);
try{const j=JSON.parse(localStorage.getItem(LS)||"{}");Object.assign(STATUS,j)}catch(e){}
$("#st-total").textContent=ROWS.length;$("#st-sa").textContent=ROWS.filter(r=>r[I.b]==="S"||r[I.b]==="A").length;
document.querySelectorAll(".chip[data-f]").forEach(c=>{c.onclick=()=>{st[c.dataset.f]=cyc(st[c.dataset.f]);chipState(c,st[c.dataset.f]);st.limit=200;render()};c._reset=()=>{st[c.dataset.f]=0;chipState(c,0);st.limit=200;render()}});
document.querySelectorAll(".chip[data-b]").forEach(c=>c.onclick=()=>{st.b[c.dataset.b]=!st.b[c.dataset.b];c.setAttribute("aria-pressed",st.b[c.dataset.b]);st.limit=200;render()});
document.querySelectorAll(".chip[data-o]").forEach(c=>{c.onclick=()=>{st.o[c.dataset.o]=cyc(st.o[c.dataset.o]);chipState(c,st.o[c.dataset.o]);st.limit=200;render()};c._reset=()=>{st.o[c.dataset.o]=0;chipState(c,0);st.limit=200;render()}});
function applyQ(){const v=$("#q").value.trim().toLowerCase();if(v===st.q)return;st.q=v;st.limit=200;render()}
$("#q").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();applyQ()}};          // search runs on Enter only
$("#q").addEventListener("search",applyQ);                                        // the ✕ in the field
$("#q").oninput=e=>{if(!e.target.value.trim())applyQ()};                          // emptied by hand → reset
$("#qall").onclick=()=>{st.qall=!st.qall;$("#qall").setAttribute("aria-pressed",st.qall);st.limit=200;render()};
$("#compat").onchange=e=>{st.compat=+e.target.value;render()};$("#minrev").onchange=e=>{st.minrev=+e.target.value;render()};$("#minpct").onchange=e=>{st.minpct=+e.target.value;render()};
$("#more").onclick=()=>{st.limit+=300;render()};
$("#pickchip").onclick=()=>{st.pick=cyc(st.pick);chipState($("#pickchip"),st.pick);st.limit=200;render()};$("#pickchip")._reset=()=>{st.pick=0;chipState($("#pickchip"),0);st.limit=200;render()};
$("#minechip").onclick=()=>{st.mine=cyc(st.mine);chipState($("#minechip"),st.mine);st.limit=200;render()};$("#minechip")._reset=()=>{st.mine=0;chipState($("#minechip"),0);st.limit=200;render()};
$("#minekind").onchange=e=>{st.minekind=e.target.value;if(st.minekind&&!st.mine){st.mine=1;chipState($("#minechip"),1)}st.limit=200;render()};
document.querySelectorAll("th[data-k]").forEach(th=>{th.tabIndex=0;const go=()=>{const k=th.dataset.k==="status"?"status":+th.dataset.k;if(st.sortK===k)st.sortD*=-1;else{st.sortK=k;st.sortD=(k===I.name||k==="status")?1:-1}render()};th.onclick=go;th.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();go()}}});
loadFilters();try{lastSaved=localStorage.getItem(FLT)}catch(e){}syncUI();render();
pullFromRepo(true);
let syncTimer=null;
function adoptSaved(){try{const v=localStorage.getItem(FLT);if(!v||v===lastSaved)return;loadFilters();lastSaved=v;syncUI();suppressSave=true;try{render()}finally{suppressSave=false}}catch(e){}}   // another tab changed the filters: adopt silently, never write back
addEventListener("storage",e=>{if(e.key===FLT){clearTimeout(syncTimer);syncTimer=setTimeout(adoptSaved,150)}else if(e.key===LS_ORDER){try{STATUS_ORDER=JSON.parse(e.newValue)||STATUS_ORDER}catch(x){}render()}});
addEventListener("focus",adoptSaved);
addEventListener("focus",()=>pullFromRepo(false));
</script>
"""
(ROOT / "index.html").write_text(page.replace("__DATA__", data).replace("__STAMP__", stamp).replace("{n_picked}", str(n_picked)).replace("{n_mine}", str(n_mine)))
print("index.html:", len(rows), "rows,", round((ROOT / "index.html").stat().st_size / 1e6, 2), "MB")
