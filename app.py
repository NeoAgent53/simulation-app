# app.py (Updated Version with Daily Resistance Missions)

from flask import Flask, render_template, request, redirect, url_for
import json, os
from datetime import datetime
from collections import defaultdict
import random

app = Flask(__name__)

DATA_FILE = 'data.json'
LOG_FILE = 'log.json'
DAILY_FILE = 'daily_missions.json'

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


# Master mission list
resistance_missions = [
    "Post an imperfect creation publicly.",
    "Sit in silence with discomfort for 5 minutes.",
    "Tell a personal truth to someone.",
    "Write down and reframe 3 negative thoughts.",
    "Create something without comparing it.",
    "Ask someone for something and accept the response.",
    "Let a task remain unfinished for 24 hours.",
    "Make a fast decision without overthinking.",
    "Share a raw journal thought online.",
    "Do something outside your usual identity."
]

TRUTH_QUOTE = "The Divine is showing me this resistance to clear."
XP_REWARD = 50

# Utilities
def group_missions_by_type(missions):
    grouped = defaultdict(list)
    for name, info in missions.items():
        grouped[info["type"]].append((name, info))
    return grouped


def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, 'r') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# Load/save data

def load_data():
    return load_json(DATA_FILE, {"xp": 0})

def save_data(data):
    save_json(DATA_FILE, data)

def load_daily():
    return load_json(DAILY_FILE, {"date": "", "missions": []})

def save_daily(data):
    save_json(DAILY_FILE, data)

# Routes
@app.route("/", methods=["GET", "POST"])

def index():
    today = datetime.now().strftime("%Y-%m-%d")
    data = load_data()
    daily = load_daily()

    if request.method == "POST" and "mission" in request.form:
        mission = request.form["mission"]
        mission_info = xp_values.get(mission, {})
        earned_xp = mission_info.get("xp", 0)
        data["xp"] += earned_xp
        save_data(data)
        return redirect(url_for("index"))

    if daily.get("date") != today:
        # New day: pick 3 random missions
        missions = random.sample(resistance_missions, 3)
        daily = {
            "date": today,
            "missions": [{"text": m, "completed": False} for m in missions]
        }
        save_daily(daily)

    all_completed = all(m["completed"] for m in daily["missions"])
    grouped_missions = group_missions_by_type(xp_values)

    return render_template(
        "index.html",
        missions=daily["missions"],
        truth=TRUTH_QUOTE,
        xp=data["xp"],
        all_completed=all(m["completed"] for m in daily["missions"]),
        grouped_missions=grouped_missions
    )


@app.route("/complete/<int:mission_id>", methods=["POST"])
def complete(mission_id):
    daily = load_daily()
    data = load_data()

    if not daily["missions"][mission_id]["completed"]:
        daily["missions"][mission_id]["completed"] = True
        save_daily(daily)

    if all(m["completed"] for m in daily["missions"]):
        data["xp"] += XP_REWARD
        save_data(data)

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)