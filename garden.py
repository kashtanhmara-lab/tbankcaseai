import json

GARDEN_FILE = "garden.json"

def load_garden():
    try:
        with open(GARDEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"saved":0,"saved_count":0}

def save_garden(state):
    try:
        with open(GARDEN_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except:
        pass
