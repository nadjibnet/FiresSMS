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
# Auth helper
# -----------------------------
def authorized():
    """Validate the API token from the 'Authorization: Bearer <token>' header."""
    header = request.headers.get("Authorization", "")
    token = header[7:].strip() if header.startswith("Bearer ") else None
    return validate_token(token)


# -----------------------------
# Endpoint: /send
# -----------------------------
@app.route("/send", methods=["POST"])
def send_sms():
    if not authorized():
        return jsonify({"error": "Invalid or missing token"}), 401

    data = request.get_json(force=True) or {}
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
    if not authorized():
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        return jsonify(sms.receive_and_archive()), 200
    except Exception as e:
        app.logger.exception("Failed to read or archive inbox: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Endpoint: /archive
# -----------------------------
@app.route("/archive", methods=["GET"])
def archive_sms():
    if not authorized():
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        return jsonify(sms.get_archive()), 200
    except Exception as e:
        app.logger.exception("Failed to read archive: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/archive", methods=["DELETE"])
def delete_archive_sms():
    if not authorized():
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        deleted = sms.delete_archive()
        return jsonify({"status": "Archived messages removed", "deleted": deleted}), 200
    except Exception as e:
        app.logger.exception("Failed to delete archive: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Endpoint: /pending
# -----------------------------
@app.route("/pending", methods=["GET"])
def pending_sms():
    if not authorized():
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        return jsonify(sms.get_pending()), 200
    except Exception as e:
        app.logger.exception("Failed to read queue: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Endpoint: /sent
# -----------------------------
@app.route("/sent", methods=["GET"])
def sent_sms():
    if not authorized():
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        return jsonify(sms.get_sent()), 200
    except Exception as e:
        app.logger.exception("Failed to read sent items: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/sent", methods=["DELETE"])
def delete_sent_sms():
    if not authorized():
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        deleted = sms.delete_sent()
        return jsonify({"status": "Sent messages removed", "deleted": deleted}), 200
    except Exception as e:
        app.logger.exception("Failed to delete sent items: %s", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Endpoint: /status
# -----------------------------
@app.route("/status", methods=["GET"])
def status_sms():
    if not authorized():
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
