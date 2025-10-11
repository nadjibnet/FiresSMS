from flask import Flask, request, jsonify
import os
import sqlite3
from datetime import datetime
import logging

app = Flask(__name__)

# -----------------------------
# Configuration
# -----------------------------
DB_PATH = os.getenv("GAMMU_DB_PATH", "/var/lib/gammu/smsd.db")
API_TOKEN = os.getenv("API_TOKEN", "changeme")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

# -----------------------------
# Helper functions
# -----------------------------
def get_db_connection():
    """Return SQLite connection to Gammu DB."""
    if not os.path.exists(DB_PATH):
        app.logger.error("SQLite database does not exist: %s", DB_PATH)
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def validate_token(data):
    token = data.get("token") if isinstance(data, dict) else None
    is_valid = token == API_TOKEN
    if not is_valid:
        app.logger.warning("Unauthorized token: %s", token)
    return is_valid

# -----------------------------
# Endpoint: /send
# -----------------------------
@app.route("/send", methods=["POST"])
def send_sms():
    data = request.get_json(force=True)
    if not data or not validate_token(data):
        return jsonify({"error": "Invalid or missing token"}), 401

    number = data.get("number")
    message = data.get("message")

    if not number or not message:
        return jsonify({"error": "Number and message are required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Support multiple recipients
        if isinstance(number, list):
            for num in number:
                cur.execute("""
                    INSERT INTO outbox (DestinationNumber, TextDecoded, CreatorID, Coding)
                    VALUES (?, ?, 'flask-api', 'Default_No_Compression');
                """, (num, message))
                app.logger.info("Queued SMS for %s", num)
        else:
            cur.execute("""
                INSERT INTO outbox (DestinationNumber, TextDecoded, CreatorID, Coding)
                VALUES (?, ?, 'flask-api', 'Default_No_Compression');
            """, (number, message))
            app.logger.info("Queued SMS for %s", number)

        conn.commit()
        conn.close()

        return jsonify({"status": "Message queued"}), 200

    except Exception as e:
        app.logger.exception("Failed to queue SMS: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Endpoint: /receive
# -----------------------------
@app.route("/receive", methods=["GET"])
def receive_sms():
    token = request.args.get("token")
    if token != API_TOKEN:
        app.logger.warning("Unauthorized receive attempt with token: %s", token)
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1️⃣ Read all messages from inbox
        cur.execute("""
            SELECT * FROM inbox ORDER BY ReceivingDateTime ASC;
        """)
        rows = cur.fetchall()

        messages = []
        for row in rows:
            if row["TextDecoded"] != "":
                msg = {
                    "id": row["ID"],
                    "from": row["SenderNumber"],
                    "message": row["TextDecoded"],
                    "received": row["ReceivingDateTime"]
                }
                messages.append(msg)

            # 2️⃣ Move message to archive
            cur.execute("""
                INSERT INTO archive (
                    UpdatedInDB, ReceivingDateTime, Text, SenderNumber, 
                    Coding, UDH, SMSCNumber, Class, TextDecoded, ID, 
                    RecipientID, Processed
                )
                SELECT UpdatedInDB, ReceivingDateTime, Text, SenderNumber, 
                       Coding, UDH, SMSCNumber, Class, TextDecoded, ID, 
                       RecipientID, Processed
                FROM inbox WHERE ID = ?;
            """, (row["ID"],))

            # 3️⃣ Delete message from inbox
            cur.execute("DELETE FROM inbox WHERE ID = ?;", (row["ID"],))

        # 4️⃣ Commit all changes
        conn.commit()
        conn.close()

        app.logger.info("Moved %d messages from inbox to archive", len(messages))
        return jsonify(messages), 200

    except Exception as e:
        app.logger.exception("Failed to read or archive inbox: %s", e)
        return jsonify({"error": str(e)}), 500



# -----------------------------
# Main entry point
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
