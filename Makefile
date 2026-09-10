# Rebuild the list from scratch. Takes ~2 h because of Steam / SteamSpy rate limits.
SCRATCH ?= /tmp/games-scratch
PY = uv run --with pandas --with pyarrow python

all: CATALOGUE.md index.html

$(SCRATCH)/games.parquet:
	mkdir -p $(SCRATCH)
	curl -L -o $@ https://huggingface.co/datasets/FronkonGames/steam-games-dataset/resolve/main/data/train-00000-of-00001.parquet

# 1. dataset -> languages / reviews / owners per game
data/steam_lang.parquet: $(SCRATCH)/games.parquet scripts/slim_dataset.py
	$(PY) scripts/slim_dataset.py $<

# 2. Steam search: every Deck Verified + Playable game, with top-7 tags and review counts (~25 min)
data/steam_deck_search.json: scripts/crawl_steam_search.py
	python3 scripts/crawl_steam_search.py

# 3. candidates = pass the language filter and have >= 500 reviews (dataset, or Steam search for new games)
data/candidates_lang.txt data/candidates_extra.txt: data/steam_lang.parquet data/steam_deck_search.json scripts/candidates.py
	$(PY) scripts/candidates.py

# 4. Deck / SteamOS / Steam Machine compat + SteamSpy tags per candidate (~1 h)
#    data/details_spy2.json is a second SteamSpy pass for candidates whose first fetch came back empty; build_list.py merges it
data/details.json: data/candidates_lang.txt scripts/fetch_details.py
	python3 scripts/fetch_details.py data/candidates_lang.txt
data/details_extra.json: data/candidates_extra.txt scripts/fetch_details.py
	DETAILS_OUT=$@ python3 scripts/fetch_details.py data/candidates_extra.txt
# hand-picked games (data/picked.json): live languages + compat + tags
data/picked_ids.txt: data/picked.json
	python3 -c "import json; d=json.load(open('data/picked.json')); open('$@','w').write('\n'.join(k for k in d if k.isdigit()))"
data/details_picked.json: data/picked_ids.txt scripts/fetch_details.py
	python3 scripts/verify_languages.py data/picked_ids.txt
	DETAILS_OUT=$@ python3 scripts/fetch_details.py data/picked_ids.txt

# the owner's Steam account lists (data/steam_account.json, exported from a logged-in store session): live languages + compat + tags
data/account_ids.txt: data/steam_account.json
	python3 -c "import json; a=json.load(open('data/steam_account.json')); open('$@','w').write('\n'.join(map(str,sorted(set(a['owned']+a['wishlist']+a['followed']+a['ignored'])))))"
data/details_account.json: data/account_ids.txt scripts/fetch_details.py
	python3 scripts/verify_languages.py data/account_ids.txt
	DETAILS_OUT=$@ python3 scripts/fetch_details.py data/account_ids.txt

# interface / audio / subtitles flags per language (IStoreBrowseService, 50 apps per call, ~5 min)
# Not part of `all`: it needs a first data/games.csv. Run `make data/langflags.json` after a build, then rebuild once.
data/langflag_ids.txt: data/games.csv
	python3 -c "import csv; open('$@','w').write('\n'.join(r['appid'] for r in csv.DictReader(open('data/games.csv')) if int(r['appid'])>0))"
data/langflags.json: data/langflag_ids.txt scripts/fetch_langflags.py
	python3 scripts/fetch_langflags.py data/langflag_ids.txt

# 5. join + score
data/games_scored.csv: data/steam_lang.parquet data/steam_deck_search.json data/details.json data/details_extra.json data/details_picked.json data/details_account.json data/picked.json data/steam_account.json scripts/build_list.py scripts/tagscore.py
	$(PY) scripts/build_list.py

# 6. re-check languages of the top games against the live Steam store API (~15 min)
data/verified_langs.json: data/games_scored.csv scripts/verify_languages.py
	$(PY) -c "import pandas as pd; g=pd.read_csv('data/games_scored.csv',low_memory=False); g=g[(g.bucket.isin(['S','A','B']))&(g.reviews>=1000)&((g.deck>=2)|(g.machine.fillna(0)>=2)|(g.steamos.fillna(0)>=2))]; open('data/verify_ids.txt','w').write('\n'.join(map(str,g.appid)))"
	python3 scripts/verify_languages.py data/verify_ids.txt

# 7. render (README.md is hand-written and is NOT generated)
CATALOGUE.md index.html: data/games_scored.csv data/verified_langs.json scripts/make_catalogue.py scripts/make_html.py
	$(PY) scripts/make_catalogue.py
	$(PY) scripts/make_html.py

# local site: serves index.html on http://localhost:8777/ and commits statuses to data/status.json
serve: index.html
	AUTO_PUSH=1 python3 scripts/serve.py

.PHONY: all serve
