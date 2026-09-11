# Ultra KI V2

Kompakter Flask-Prototyp für eine KI-Chat-Anwendung mit Benutzerkonto und SQLite-Chatverlauf.

## Status
Der ursprüngliche Quelltext verwendet Flask, SQLite, OpenAI, dotenv und Passwort-Hashing. Die alte Datei bleibt als historische Quelle erhalten. Die Web-Templates waren im Repository jedoch nicht vorhanden; deshalb wird die nächste Bereinigung eine vollständige, reproduzierbare App-Struktur ergänzen.

## Start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=...
python app.py
```
