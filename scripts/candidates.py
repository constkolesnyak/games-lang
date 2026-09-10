"""Pick the games worth fetching details for: pass the language filter and have >= 500 reviews.
data/candidates_lang.txt  - review count from the dataset
data/candidates_extra.txt - dataset says 0 reviews (new games) but Steam search shows >= 500
"""
import json, pathlib, pandas as pd
D = pathlib.Path(__file__).resolve().parent.parent / "data"
df = pd.read_parquet(D / "steam_lang.parquet")
search = {int(k): v for k, v in json.loads((D / "steam_deck_search.json").read_text()).items()}
ok = ((df.has_voice & (df.de_audio | df.ja_audio)) | (~df.has_voice & (df.de_text | df.ja_text)))
main = df[ok & (df.reviews_total >= 500)].sort_values("reviews_total", ascending=False)
(D / "candidates_lang.txt").write_text("\n".join(map(str, main.appid.tolist())))
df["src"] = df.appid.map(lambda a: (search.get(a) or {}).get("review_count") or 0)
extra = df[ok & (df.reviews_total < 500) & (df.src >= 500)].sort_values("src", ascending=False)
(D / "candidates_extra.txt").write_text("\n".join(map(str, extra.appid.tolist())))
print("candidates:", len(main), "extra:", len(extra))
