from flask import Flask, request, jsonify
import os
import logging

from services.auth import validate_token
from services import sms

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)


# -----------------------------
# Endpoint: /send
# -----------------------------
@app.route("/send", methods=["POST"])
def send_sms():
    data = request.get_json(force=True)
    if not data or not validate_token(data.get("token") if isinstance(data, dict) else None):
        return jsonify({"error": "Invalid or missing token"}), 401

    number = data.get("number")
    message = data.get("message")
    if not number or not message:
        return jsonify({"error": "Number and message are required"}), 400

    try:
        queued, ack = sms.queue_messages(number, message, ack=data.get("ack"))
        return jsonify({"status": "Message queued", "ack": ack, "queued": queued}), 200
    except Exception as e:
        app.logger.exception("Failed to queue SMS: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Endpoint: /receive
# -----------------------------
@app.route("/receive", methods=["GET"])
def receive_sms():
    if not validate_token(request.args.get("token")):
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        return jsonify(sms.receive_and_archive()), 200
    except Exception as e:
        app.logger.exception("Failed to read or archive inbox: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Endpoint: /pending
# -----------------------------
@app.route("/pending", methods=["GET"])
def pending_sms():
    if not validate_token(request.args.get("token")):
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        queue = sms.get_pending()
        return jsonify({"count": len(queue), "queue": queue}), 200
    except Exception as e:
        app.logger.exception("Failed to read queue: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Endpoint: /status
# -----------------------------
@app.route("/status", methods=["GET"])
def status_sms():
    if not validate_token(request.args.get("token")):
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        return jsonify(sms.get_status_overview()), 200
    except Exception as e:
        app.logger.exception("Failed to read status: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Main entry point
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("API_PORT", "8080")))
