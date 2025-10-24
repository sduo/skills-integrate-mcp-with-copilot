import sqlite3
from pathlib import Path
import json
from typing import Dict, Any

DB_PATH = Path(__file__).parent / "data.sqlite3"


def init_db(seed_activities: Dict[str, Any]):
    """Create tables if they don't exist and seed activities if empty."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            name TEXT PRIMARY KEY,
            description TEXT,
            schedule TEXT,
            max_participants INTEGER,
            participants TEXT
        )
        """
    )
    # if table empty, insert seed activities
    cur.execute("SELECT COUNT(1) FROM activities")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        for name, v in seed_activities.items():
            participants_json = json.dumps(v.get("participants", []))
            cur.execute(
                "INSERT INTO activities (name, description, schedule, max_participants, participants) VALUES (?, ?, ?, ?, ?)",
                (name, v.get("description"), v.get("schedule"), v.get("max_participants", 0), participants_json),
            )
    conn.commit()
    conn.close()


def _connect():
    conn = sqlite3.connect(DB_PATH)
    return conn


def get_activities():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT name, description, schedule, max_participants, participants FROM activities")
    rows = cur.fetchall()
    conn.close()
    activities = {}
    for name, description, schedule, max_participants, participants in rows:
        try:
            parts = json.loads(participants) if participants else []
        except Exception:
            parts = []
        activities[name] = {
            "description": description,
            "schedule": schedule,
            "max_participants": max_participants,
            "participants": parts,
        }
    return activities


def signup(activity_name: str, email: str):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT participants, max_participants FROM activities WHERE name = ?", (activity_name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Activity not found"
    participants_json, max_participants = row
    participants = json.loads(participants_json) if participants_json else []
    if email in participants:
        conn.close()
        return False, "Student is already signed up"
    if max_participants and len(participants) >= max_participants:
        conn.close()
        return False, "No spots left"
    participants.append(email)
    cur.execute("UPDATE activities SET participants = ? WHERE name = ?", (json.dumps(participants), activity_name))
    conn.commit()
    conn.close()
    return True, f"Signed up {email} for {activity_name}"


def unregister(activity_name: str, email: str):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT participants FROM activities WHERE name = ?", (activity_name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Activity not found"
    participants_json = row[0]
    participants = json.loads(participants_json) if participants_json else []
    if email not in participants:
        conn.close()
        return False, "Student is not signed up for this activity"
    participants.remove(email)
    cur.execute("UPDATE activities SET participants = ? WHERE name = ?", (json.dumps(participants), activity_name))
    conn.commit()
    conn.close()
    return True, f"Unregistered {email} from {activity_name}"
