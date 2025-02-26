from flask import Flask, jsonify, request
import requests
import sqlite3

app = Flask(__name__)

# Initialize SQLite database
DB_FILE = "study_scheduler.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                due_date TEXT,
                hours_needed INTEGER
            )
        ''')
        conn.commit()

init_db()

# Fetch assignments from Canvas API
def get_canvas_assignments(canvas_url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{canvas_url}/api/v1/users/self/todo", headers=headers)
    if response.status_code != 200:
        return []
    assignments = response.json()
    formatted_assignments = []
    for item in assignments:
        formatted_assignments.append({
            "name": item["assignment"].get("name", "Unnamed Assignment"),
            "due_date": item["assignment"].get("due_at", "Unknown Date")[:10],
            "hours_needed": 3  # Default estimate, can be modified later
        })
    return formatted_assignments

@app.route("/fetch_assignments", methods=["POST"])
def fetch_assignments():
    data = request.json
    canvas_url = data.get("canvas_url")
    token = data.get("token")
    assignments = get_canvas_assignments(canvas_url, token)
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        for assignment in assignments:
            cursor.execute("""
                INSERT INTO assignments (name, due_date, hours_needed)
                VALUES (?, ?, ?)""", (assignment["name"], assignment["due_date"], assignment["hours_needed"]))
        conn.commit()
    return jsonify({"message": "Assignments fetched and stored.", "assignments": assignments})

@app.route("/get_schedule", methods=["GET"])
def get_schedule():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, due_date, hours_needed FROM assignments")
        assignments = cursor.fetchall()
    return jsonify({"schedule": assignments})

if __name__ == "__main__":
    app.run(debug=True)

