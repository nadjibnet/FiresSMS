"""SMS business logic: queueing, receiving, and reporting on the Gammu DB.

Each function works directly against the Gammu SMSD tables and returns plain
Python data; the Flask routes in app.py stay thin and only deal with HTTP.
"""
import logging

from services.db import get_db_connection

logger = logging.getLogger(__name__)


def queue_messages(number, message, ack=False):
    """Insert one or more outbound messages into the outbox (the send queue).

    `number` may be a single string or a list of strings. When `ack` is truthy
    a network delivery report is requested for each message.

    Returns (queued, ack_requested) where `queued` is a list of
    {"id", "number"} dicts and `ack_requested` is the effective bool.
    """
    delivery_report = "yes" if ack else "default"
    numbers = number if isinstance(number, list) else [number]

    conn = get_db_connection()
    cur = conn.cursor()
    queued = []
    for num in numbers:
        cur.execute("""
            INSERT INTO outbox (DestinationNumber, TextDecoded, CreatorID, Coding, DeliveryReport)
            VALUES (?, ?, 'flask-api', 'Default_No_Compression', ?);
        """, (num, message, delivery_report))
        queued.append({"id": cur.lastrowid, "number": num})
        logger.info("Queued SMS id=%s for %s (ack=%s)", cur.lastrowid, num, delivery_report)

    conn.commit()
    conn.close()
    return queued, delivery_report == "yes"


def receive_and_archive():
    """Read all inbox messages, move them to the archive, and return them.

    Returns a list of {"id", "from", "message", "received"} dicts.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM inbox ORDER BY ReceivingDateTime ASC;")
    rows = cur.fetchall()

    messages = []
    for row in rows:
        if row["TextDecoded"] != "":
            messages.append({
                "id": row["ID"],
                "from": row["SenderNumber"],
                "message": row["TextDecoded"],
                "received": row["ReceivingDateTime"],
            })

        # Move message to archive, then remove it from the inbox.
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
        cur.execute("DELETE FROM inbox WHERE ID = ?;", (row["ID"],))

    conn.commit()
    conn.close()

    logger.info("Moved %d messages from inbox to archive", len(messages))
    return messages


def get_pending():
    """List SMS currently waiting in the outbox (the send queue)."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT ID, DestinationNumber, TextDecoded, Status, StatusCode,
               Retries, InsertIntoDB, SendingDateTime, DeliveryReport
        FROM outbox
        ORDER BY InsertIntoDB ASC;
    """)
    rows = cur.fetchall()
    conn.close()

    queue = [{
        "id": row["ID"],
        "to": row["DestinationNumber"],
        "message": row["TextDecoded"],
        "status": row["Status"],
        "status_code": row["StatusCode"],
        "retries": row["Retries"],
        "queued_at": row["InsertIntoDB"],
        "send_after": row["SendingDateTime"],
        "ack_requested": row["DeliveryReport"] == "yes",
    } for row in rows]

    logger.info("Queue holds %d pending message(s)", len(queue))
    return queue


def get_status_overview():
    """Return a global snapshot of the SMS database.

    Counts across every table plus what is pending and a delivery (ACK)
    breakdown of sent messages.
    """
    def count(cur, table):
        cur.execute("SELECT COUNT(*) FROM %s;" % table)
        return cur.fetchone()[0]

    def by_status(cur, table):
        cur.execute("SELECT Status, COUNT(*) AS c FROM %s GROUP BY Status;" % table)
        return {row["Status"]: row["c"] for row in cur.fetchall()}

    conn = get_db_connection()
    cur = conn.cursor()

    pending_count = count(cur, "outbox")
    sent_count = count(cur, "sentitems")
    inbox_count = count(cur, "inbox")
    archive_count = count(cur, "archive")

    cur.execute("""
        SELECT ID, DestinationNumber, Status, Retries, InsertIntoDB, DeliveryReport
        FROM outbox ORDER BY InsertIntoDB ASC;
    """)
    pending_items = [{
        "id": row["ID"],
        "to": row["DestinationNumber"],
        "status": row["Status"],
        "retries": row["Retries"],
        "queued_at": row["InsertIntoDB"],
        "ack_requested": row["DeliveryReport"] == "yes",
    } for row in cur.fetchall()]

    cur.execute("""
        SELECT ID, Client, Signal, Battery, Send, Receive, Sent, Received
        FROM phones;
    """)
    modems = [{
        "id": row["ID"],
        "client": row["Client"],
        "signal": row["Signal"],
        "battery": row["Battery"],
        "can_send": row["Send"] == "yes",
        "can_receive": row["Receive"] == "yes",
        "sent": row["Sent"],
        "received": row["Received"],
    } for row in cur.fetchall()]

    pending_by_status = by_status(cur, "outbox")
    sent_by_status = by_status(cur, "sentitems")
    conn.close()

    return {
        "totals": {
            "pending": pending_count,        # outbox: waiting to send
            "sent": sent_count,              # sentitems: handed to network
            "inbox": inbox_count,            # received, not yet read
            "archive": archive_count,        # received and processed
        },
        "pending": {
            "count": pending_count,
            "by_status": pending_by_status,
            "items": pending_items,
        },
        "sent": {
            "count": sent_count,
            "by_status": sent_by_status,     # incl. DeliveryOK/Failed/Pending (ACK)
        },
        "modems": modems,
    }
