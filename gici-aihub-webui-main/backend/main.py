from flask import Flask, request, jsonify
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Path to the users JSON file
USERS_FILE = Path(__file__).parent / "users.json"


def load_users():
    if not USERS_FILE.exists():
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    users = load_users()
    if any(u["username"] == username for u in users):
        return jsonify({"error": "用户名已存在"}), 400

    users.append({"username": username, "password": password})
    save_users(users)
    return jsonify({"success": True, "username": username})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    user = next(
        (u for u in users if u["username"] == username and u["password"] == password),
        None,
    )

    if not user:
        return jsonify({"error": "用户名或密码错误"}), 401

    return jsonify({"success": True, "username": username})


@app.route("/add_session", methods=["POST"])
def add_session():
    data = request.json
    username = data.get("username")
    session_id = data.get("sessionId")

    if not username or not session_id:
        return jsonify({"error": "缺少参数"}), 400

    users = load_users()
    user = next((u for u in users if u["username"] == username), None)
    if user:
        if "sessions" not in user:
            user["sessions"] = []
        if session_id not in user["sessions"]:
            user["sessions"].append(session_id)
        save_users(users)
        return jsonify({"success": True})
    return jsonify({"error": "用户不存在"}), 404


@app.route("/user_sessions", methods=["GET"])
def get_user_sessions():
    username = request.args.get("username")
    if not username:
        return jsonify([]), 400

    users = load_users()
    user = next((u for u in users if u["username"] == username), None)
    if user:
        return jsonify(user.get("sessions", []))
    return jsonify([])


@app.route("/remove_session", methods=["POST"])
def remove_session():
    data = request.json
    username = data.get("username")
    session_id = data.get("sessionId")

    users = load_users()
    user = next((u for u in users if u["username"] == username), None)
    if user and "sessions" in user:
        if session_id in user["sessions"]:
            user["sessions"].remove(session_id)
            save_users(users)
        return jsonify({"success": True})
    return jsonify({"error": "用户或会话不存在"}), 404


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    app.run(host=host, port=port, debug=debug)
