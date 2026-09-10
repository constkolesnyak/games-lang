"""Language-intensity scoring from Steam tags.

The goal: rank games by how much language (dialogue / narration / text) the player has to process.
Tags are Steam's user tags (data/steam_tags.json maps id -> name).
"""
import json, pathlib
TAGS = {t["tagid"]: t["name"] for t in json.loads((pathlib.Path(__file__).resolve().parent.parent / "data" / "steam_tags.json").read_text())}
NAME2ID = {v: k for k, v in TAGS.items()}

# tier -> tags. Higher tier = more language per minute of play.
TIERS = {
    5: ["Visual Novel", "Interactive Fiction", "Text-Based", "Choose Your Own Adventure", "Dialogue Heavy", "Otome", "Word Game"],
    4: ["Story Rich", "JRPG", "CRPG", "Party-Based RPG", "Point & Click", "Detective", "Investigation", "Narration",
        "Dynamic Narration", "Narrative", "Choices Matter", "Multiple Endings", "Lore-Rich", "Episodic", "Dating Sim", "RPG",
        "Walking Simulator"],
    3: ["Adventure", "Mystery", "Turn-Based RPG", "Tactical RPG", "Strategy RPG", "Psychological", "Romance", "Drama",
        "Philosophical", "Noir", "Emotional", "Comedy", "Dark Comedy", "Psychological Horror", "Crime", "Thriller", "Political",
        "Conversation", "Life Sim", "Cinematic"],
    2: ["Action RPG", "Action-Adventure", "Open World", "Grand Strategy", "Management", "Colony Sim", "Turn-Based Strategy",
        "Turn-Based Tactics", "Turn-Based Combat", "Horror", "Survival Horror", "Hidden Object", "Historical", "Mythology",
        "Time Travel", "Anime", "Education", "Typing"],
}
NEGATIVE = {"Multiplayer": -2, "Massively Multiplayer": -3, "PvP": -2, "Online Co-Op": -1, "Co-op": -1, "MMORPG": -2, "Sports": -3,
            "Racing": -3, "Rhythm": -3, "Arcade": -2, "Shooter": -2, "FPS": -2, "Third-Person Shooter": -1, "Platformer": -2, "2D Platformer": -2,
            "Precision Platformer": -3, "Roguelike": -2, "Roguelite": -2, "Action Roguelike": -2, "Sandbox": -2, "Survival": -2,
            "Battle Royale": -4, "eSports": -4, "Tower Defense": -2, "Card Game": -1, "Casual": -1, "Clicker": -3, "Idler": -3,
            "Fighting": -2, "Hack and Slash": -2, "Bullet Hell": -3, "Shoot 'Em Up": -3, "Twin Stick Shooter": -3, "Free to Play": -1,
            "Building": -1, "Automation": -2, "Puzzle": -1, "Escape Room": -2, "Farming Sim": -1, "Loot": -1, "Logic": -2, "Puzzle Platformer": -2, "Physics": -2, "Driving": -2, "Flight": -2, "Music": -2, "Beat 'em up": -1,
            "Souls-like": 0, "Competitive": -2, "Team-Based": -2, "Hero Shooter": -4, "Extraction Shooter": -4, "Looter Shooter": -2,
            "Open World Survival Craft": -3, "Vehicular Combat": -3, "Tactical": 0, "Utilities": -5, "Software": -5, "Design & Illustration": -5,
            "Animation & Modeling": -5, "Video Production": -5, "Photo Editing": -5, "Game Development": -3, "Wargame": -1, "Match 3": -3,
            "Trading Card Game": -1, "Party Game": -3, "Local Multiplayer": -1, "4 Player Local": -1, "Minigames": -1, "Board Game": -1,
            "Football (Soccer)": -4, "Basketball": -4, "Golf": -4, "Sokoban": -3, "Programming": -3, "Hex Grid": 0, "Mining": -1}
# Explicitly adult games are dropped from every output (see build_list.py). Only these two tags
# are used: the broader mature-content tags also sit on mainstream titles (The Witcher 3,
# Cyberpunk 2077, Bayonetta) and would throw them out too.
EXCLUDE_TAGS = {"Hentai", "NSFW"}
def is_adult(tag_names):
    return bool(EXCLUDE_TAGS.intersection(tag_names))

TIER_OF = {NAME2ID[n]: t for t, names in TIERS.items() for n in names if n in NAME2ID}
NEG_OF = {NAME2ID[n]: v for n, v in NEGATIVE.items() if n in NAME2ID}
missing = [n for names in TIERS.values() for n in names if n not in NAME2ID] + [n for n in NEGATIVE if n not in NAME2ID]

def score(tagids, weights=None):
    """tagids: iterable of tag ids in rank order (most-voted first). weights optional dict id->votes.
    Returns (score, top_tier, tier5_hits, tier4_hits)."""
    tagids = list(tagids)
    if not tagids: return 0.0, 0, [], []
    s, top = 0.0, 0
    t5, t4 = [], []
    for rank, t in enumerate(tagids):
        pos = 1.0 / (1 + rank / 6)             # rank 0 -> 1.0, rank 6 -> 0.5, rank 18 -> 0.25
        tier = TIER_OF.get(t, 0)
        if tier:
            s += tier * pos; top = max(top, tier)
            if tier == 5: t5.append(TAGS[t])
            if tier == 4: t4.append(TAGS[t])
        s += NEG_OF.get(t, 0) * pos
    return round(s, 2), top, t5, t4

def bucket(top_tier, s):
    if top_tier == 5 and s >= 6: return "S"     # novel-like: reading/listening is the game
    if top_tier >= 4 and s >= 6: return "A"     # story-rich RPG / adventure
    if s >= 4 and top_tier >= 3: return "B"      # story-driven but action/strategy-heavy
    return "C"

if __name__ == "__main__":
    print("unknown tag names:", missing)
    print(len(TIER_OF), "positive tags,", len(NEG_OF), "negative tags")
