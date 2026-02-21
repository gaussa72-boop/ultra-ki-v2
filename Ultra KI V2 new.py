from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import sqlite3
import os
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash

# Laden der Umgebungsvariablen (.env Datei)
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ein-sehr-sicherer-schluessel-123")


# -----------------------
# Datenbank Setup
# -----------------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        role TEXT,
        message TEXT
    )""")
    conn.commit()
    conn.close()


init_db()


# -----------------------
# Routen & Logik
# -----------------------

@app.route("/")
def index():
    # Leitet den Nutzer direkt zum Login weiter, wenn er die Seite aufruft
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        # Passwörter werden nun sicher gehasht gespeichert
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Benutzername existiert bereits!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        # Abgleich des gehashten Passworts
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        return "Ungültige Anmeldedaten!"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"error": "Nicht eingeloggt"})

    user_input = request.json.get("message")
    user_id = session["user_id"]

    conn = get_db_connection()
    c = conn.cursor()

    # Chat-Historie für den Kontext laden
    c.execute("SELECT role, message FROM chats WHERE user_id=? ORDER BY id DESC LIMIT 10", (user_id,))
    history = c.fetchall()

    # Historie für die OpenAI API formatieren
    messages = [{"role": "system", "content": "Du bist die UltraKI Pro V2, ein hilfreicher Assistent."}]
    for row in reversed(history):
        messages.append({"role": row["role"], "content": row["message"]})

    messages.append({"role": "user", "content": user_input})

    # OpenAI API Aufruf
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    ai_reply = response.choices[0].message.content

    # Speichern in der Datenbank
    c.execute("INSERT INTO chats (user_id, role, message) VALUES (?, ?, ?)", (user_id, "user", user_input))
    c.execute("INSERT INTO chats (user_id, role, message) VALUES (?, ?, ?)", (user_id, "assistant", ai_reply))
    conn.commit()
    conn.close()

    return jsonify({"reply": ai_reply})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
