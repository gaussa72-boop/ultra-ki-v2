import os
from collections import defaultdict, deque
from time import monotonic
from flask import Flask, jsonify, request, send_from_directory
from openai import OpenAI

app = Flask(__name__)
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")
WEB = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"
MAX_INPUT = max(1000, min(int(os.getenv("MAX_INPUT_CHARS", "12000")), 30000))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
SYSTEM = """Du bist Ultra KI V2, ein leistungsfähiger Forschungs-, Coding- und Projektassistent.
Antworte in der Sprache des Nutzers. Arbeite strukturiert, präzise und lösungsorientiert.
Trenne Fakten, Annahmen und Unsicherheit. Nutze Web-Recherche für aktuelle Informationen, wenn aktiviert.
Erfinde keine Quellen, Daten, Aktionen oder Ergebnisse. Bei Code: Sicherheit, Wartbarkeit, Tests und Deployment beachten."""
RATE = defaultdict(lambda: deque(maxlen=30))

def allow(ip):
    now = monotonic()
    q = RATE[ip]
    while q and now - q[0] > 60: q.popleft()
    if len(q) >= 20: return False
    q.append(now)
    return True

def clean_history(history):
    if not isinstance(history, list): return []
    result = []
    for item in history[-12:]:
        if not isinstance(item, dict): continue
        role, content = item.get("role"), item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            result.append({"role": role, "content": content[:MAX_INPUT]})
    return result

def ask(message, history):
    if not AI_ENABLED: return "Die KI ist derzeit deaktiviert."
    if not client: return "OPENAI_API_KEY ist in Render nicht gesetzt."
    try:
        kwargs = {
            "model": MODEL,
            "store": False,
            "input": [{"role":"system","content":SYSTEM}, *clean_history(history), {"role":"user","content":message}],
        }
        if WEB:
            kwargs["tools"] = [{"type":"web_search","search_context_size":"medium"}]
            kwargs["tool_choice"] = "auto"
        response = client.responses.create(**kwargs)
        return response.output_text or "Keine Antwort erhalten."
    except Exception:
        app.logger.exception("AI API failure")
        return "Die KI-Schnittstelle ist momentan nicht erreichbar. Prüfe API-Key, Guthaben und Render-Logs."

@app.get("/")
def home(): return send_from_directory("templates", "index.html")

@app.get("/engine")
def engine(): return send_from_directory(".", "game_engine.html")

@app.get("/game_engine.js")
def engine_js(): return send_from_directory(".", "game_engine.js")

@app.get("/health")
@app.get("/api/health")
def health():
    return jsonify({"status":"ok","project":"ULTRA KI V2","model":MODEL,"ai_enabled":AI_ENABLED,"web_search":WEB,"openai_configured":bool(client)})

@app.post("/api/chat")
@app.post("/chat")
def chat():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    if not allow(ip): return jsonify({"error":"Zu viele Anfragen. Bitte kurz warten."}), 429
    data = request.get_json(silent=True) or {}
    message = str(data.get("message") or "").strip()
    if not message: return jsonify({"error":"message is required"}), 400
    if len(message) > MAX_INPUT: return jsonify({"error":f"message is too long (max {MAX_INPUT} characters)"}), 413
    reply = ask(message, data.get("history"))
    return jsonify({"ok":True,"reply":reply,"response":reply,"model":MODEL,"web_search":WEB})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
