"""Slim the FronkonGames Steam dataset parquet down to the columns we need + DE/JA language flags.
Input : scratchpad/games.parquet (HuggingFace FronkonGames/steam-games-dataset)
Output: data/steam_lang.parquet  (all games) — used by build_list.py
"""
import sys, pathlib, pandas as pd

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "steam_lang.parquet"
df = pd.read_parquet(SRC)
df["appid"] = df["appID"].astype(int)
L = lambda s: set(s.tolist())
df["langs"] = df["supported_languages"].map(L)
df["audio"] = df["full_audio_languages"].map(L)
df["has_voice"] = df["audio"].map(bool)
df["de_text"] = df["langs"].map(lambda s: "German" in s)
df["ja_text"] = df["langs"].map(lambda s: "Japanese" in s)
df["de_audio"] = df["audio"].map(lambda s: "German" in s)
df["ja_audio"] = df["audio"].map(lambda s: "Japanese" in s)
df["owners_min"] = df["estimated_owners"].str.split(" - ").str[0].str.replace(",", "").astype(int)
df["reviews_total"] = df["positive"] + df["negative"]
df["review_pct"] = (100 * df["positive"] / df["reviews_total"].clip(lower=1)).round(1)
df["year"] = pd.to_datetime(df["release_date"], errors="coerce", format="mixed").dt.year
for c in ("genres", "categories", "developers", "publishers"):
    df[c] = df[c].map(lambda a: list(a))
df["n_langs"] = df["langs"].map(len); df["n_audio"] = df["audio"].map(len)
keep = ["appid","name","release_date","year","owners_min","estimated_owners","peak_ccu","price","positive","negative",
        "reviews_total","review_pct","metacritic_score","recommendations","average_playtime_forever","average_playtime_2weeks",
        "median_playtime_forever","has_voice","de_text","ja_text","de_audio","ja_audio","n_langs","n_audio",
        "genres","categories","developers","publishers","short_description","header_image","windows","linux","required_age"]
out = df[keep].copy()
out["langs"] = df["langs"].map(sorted); out["audio"] = df["audio"].map(sorted)
out.to_parquet(OUT, index=False)
print(out.shape, "->", OUT)
print("has_voice:", out.has_voice.sum(), "de_audio:", out.de_audio.sum(), "ja_audio:", out.ja_audio.sum(), "de_text:", out.de_text.sum(), "ja_text:", out.ja_text.sum())
