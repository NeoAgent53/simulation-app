from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client
from collections import defaultdict
from datetime import datetime, date


import json
import random
import os
from datetime import datetime

# Supabase setup
SUPABASE_URL = "https://cwfpdxefylagzrpnxett.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3ZnBkeGVmeWxhZ3pycG54ZXR0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg0MDQxMjEsImV4cCI6MjA2Mzk4MDEyMX0.FcuKc1WOE0JF3_YkoEDyNH1_uHF52d9Q99uKLnhL2j4"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


app = Flask(__name__)

def get_user():
    user_id = "00000000-0000-0000-0000-000000000001"  # UUID format
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    if response.data:
        return response.data[0]
    else:
        supabase.table("users").insert({
            "id": user_id,
            "xp": 0,
            "level": 1
        }).execute()
        return {"id": user_id, "xp": 0, "level": 1}

def update_user_xp(new_xp):
    user_id = "00000000-0000-0000-0000-000000000001"
    level = new_xp // 1000 + 1
    supabase.table("users").update({
        "xp": new_xp,
        "level": level
    }).eq("id", user_id).execute()

def load_missions():
    with open("missions.json", "r") as f:
        return json.load(f)

def group_missions(missions):
    grouped = defaultdict(list)
    for mission in missions:
        category = mission.get("category", "Uncategorized")
        grouped[category].append((mission["name"], mission))
    return grouped

def load_daily_missions():
    today_str = str(date.today())
    try:
        with open("daily_missions.json", "r") as f:
            daily_data = json.load(f)
            if daily_data.get("date") == today_str:
                return daily_data
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Load from full mission list
    missions = load_missions()
    selected = random.sample(missions, 3)
    new_data = {
        "date": today_str,
        "missions": [{"text": m["name"], "completed": False} for m in selected]
    }

    with open("daily_missions.json", "w") as f:
        json.dump(new_data, f, indent=2)

    return new_data


def save_daily_missions(data):
    with open("daily_missions.json", "w") as f:
        json.dump(data, f, indent=2)

@app.route("/", methods=["GET", "POST"])
def index():
    user = get_user()
    missions = load_missions()
    daily_missions = load_daily_missions()
    grouped_missions = group_missions(missions)
    daily_data = load_daily_missions()

    if request.method == "POST":
        mission_name = request.form.get("mission")
        for mission in missions:
            if mission["name"] == mission_name:
                user["xp"] += mission["xp"]
                update_user_xp(user["xp"])
                break
        return redirect(url_for("index"))

    return render_template("index.html",
                           level=user["level"],
                           xp=user["xp"],
                           grouped_missions=grouped_missions,
                           daily_missions=daily_data["missions"])

@app.route("/lag", methods=["POST"])
def handle_lag():
    user = get_user()
    user["xp"] += 25
    update_user_xp(user["xp"])
    return redirect(url_for("index"))


@app.route("/complete_daily/<int:index>", methods=["POST"])
def complete_daily(index):
    user = get_user()
    daily_data = load_daily_missions()

    if 0 <= index < len(daily_data["missions"]):
        if not daily_data["missions"][index]["completed"]:
            daily_data["missions"][index]["completed"] = True
            user["xp"] += 10  # XP reward per daily mission
            update_user_xp(user["xp"])
            save_daily_missions(daily_data)

    return redirect(url_for("index"))

@app.route("/complete_daily", methods=["POST"])
def complete_daily_mission():
    mission_text = request.form.get("mission_text")
    data = load_daily_missions()

    # Mark the mission as completed
    for mission in data["missions"]:
        if mission["text"] == mission_text:
            mission["completed"] = True
            break

    # Save mission state
    with open("daily_missions.json", "w") as f:
        json.dump(data, f, indent=2)

    # Check if all missions are completed
    all_completed = all(m["completed"] for m in data["missions"])

    # Track if XP has already been awarded for the day
    if all_completed and not data.get("xp_awarded", False):
        user = get_user()
        xp_gain = 30  # or whatever XP value you want for full completion
        user["xp"] += xp_gain
        update_user_xp(user["xp"])
        data["xp_awarded"] = True  # Prevent awarding XP multiple times
        with open("daily_missions.json", "w") as f:
            json.dump(data, f, indent=2)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)