from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

DATA_FILE = 'data.json'
LOG_FILE = 'log.json'

# Mission definitions with XP, repeat flag, and category type
xp_values = {
    "Drink Water": {"xp": 10, "repeatable": True, "type": "Body"},
    "Meditate 10 Min": {"xp": 20, "repeatable": True, "type": "Mind"},
    "Strength Training": {"xp": 30, "repeatable": False, "type": "Body"},
    "Observe Without Reacting": {"xp": 25, "repeatable": False, "type": "Mind"},
    "Eat Nutritious Meal": {"xp": 15, "repeatable": False, "type": "Body"},
    "Skill Practice": {"xp": 20, "repeatable": True, "type": "Mind"},
    "Digital Detox 1 Hour": {"xp": 15, "repeatable": False, "type": "Routine"},
    "Go for a Walk": {"xp": 10, "repeatable": True, "type": "Body"},
    "Journal Entry": {"xp": 15, "repeatable": True, "type": "Mind"}
}

# XP per level: 100 XP per level
def calculate_level(xp):
    return xp // 100 + 1

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"xp": 0, "last_reset": "2000-01-01"}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE) as f:
        return json.load(f)

def save_log(log):
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def group_missions_by_type(missions):
    grouped = defaultdict(list)
    for name, info in missions.items():
        grouped[info["type"]].append((name, info))
    return grouped

@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()
    log = load_log()
    today = datetime.now().strftime("%Y-%m-%d")

    # Auto-reset daily missions
    if data.get("last_reset") != today:
        log = []
        save_log(log)
        data["last_reset"] = today
        save_data(data)

    if request.method == "POST":
        mission = request.form["mission"]
        mission_info = xp_values.get(mission, {})
        earned_xp = mission_info.get("xp", 0)
        repeatable = mission_info.get("repeatable", False)

        if not repeatable:
            for entry in log:
                if entry["mission"] == mission and entry["timestamp"].startswith(today):
                    return redirect(url_for("index"))  # Already done today

        data["xp"] += earned_xp
        save_data(data)

        log.append({
            "mission": mission,
            "xp": earned_xp,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_log(log)

        return redirect(url_for("index"))

    level = calculate_level(data["xp"])
    badge_image = f"badge_{level}.png"
    grouped_missions = group_missions_by_type(xp_values)

    return render_template(
        "index.html",
        xp=data["xp"],
        level=level,
        badge_image=badge_image,
        grouped_missions=grouped_missions,
        log=log[::-1]
    )

if __name__ == "__main__":
    app.run(debug=True)
