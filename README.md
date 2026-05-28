# FiresSMS

**FireSMS** is a Dockerized SMS Gateway built using [Gammu SMSD](https://wammu.eu/docs/manual/smsd/) and a custom API interface. It allows sending and receiving SMS messages using a GSM/USB modem connected to your server. FiresSMS is ideal for IoT devices, alerting systems, or SMS-based applications.

---

## 📦 Features
- 📨 Send and receive SMS messages via a web API
- 🐳 Containerised using Docker and Docker Compose
- ⚙️ Configurable Gammu integration for different modem types
- 🔧 Simple, portable deployment
- 💽 Use the SQLite database

---

## 🧱 Project Structure
```
FiresSMS/
├── configs/
│ ├── gammurc # Gammu configuration (device, connection)
│ └── smsdrc # SMS Daemon configuration
├── dockers/
│ ├── api/ # REST API for SMS interaction
│ │ ├── app.py # Flask routes (thin layer)
│ │ └── services/ # Business logic called by the routes
│ │ ├── db.py # SQLite connection to the Gammu DB
│ │ ├── auth.py # API token validation
│ │ └── sms.py # send / receive / pending / status logic
│ └── gammu-smsd/ # Gammu SMSD container
├── database # folder for database
├── docker-compose.yaml
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Fires04/FiresSMS.git
cd FiresSMS
```

### 2. Configure Gammu

Edit the configuration files under configs/:
gammurc – Set device path (e.g., /dev/ttyUSB0)

docker-compose.yml

Rename .env-example to .env and setup your API token

### 3. Start Services

```bash
docker compose up --build
```
This will start:
gammu-smsd: the SMS daemon container
api: the REST API for sending and managing messages

#### 📡 Usage

Sending an SMS

POST to the API:
URL is http://yourserver:8080 (if you need to change the port, then you can edit the Docker compose file to change the port routing to the Docker container or edit the Python app under /dockers/api/app.py

```http
POST /send
Content-Type: application/json
{
  "token": "my-secret-token",
  "number": "+420123456789",
  "message": "Hello from Flask SMS gateway!"
}
```
or send message to multiple numbers

```http
POST /send
Content-Type: application/json
{
  "token": "my-secret-token",
  "number": ["+420123456789","+420987654321"],
  "message": "Hello from Flask SMS gateway!"
}
```

The response returns the queue ID(s) so each message can be tracked:

```json
{
  "status": "Message queued",
  "ack": false,
  "queued": [
    { "id": 42, "number": "+420123456789" }
  ]
}
```

**Requesting a delivery report (ACK)** — add `"ack": true` to ask the network
for a delivery receipt for that message. The result can then be polled via
`/status` (see below). Note: not all modems/operators support delivery reports,
and some bill extra for them.

```http
POST /send
Content-Type: application/json
{
  "token": "my-secret-token",
  "number": "+420123456789",
  "message": "Hello from Flask SMS gateway!",
  "ack": true
}
```

#### Viewing the send queue

List the SMS currently waiting to be sent (the `outbox`). A message only
appears here while it is pending or retrying; once handed to the network it
leaves the queue and can be tracked via `/status`.

```http://yoururl.url:8080/pending?token=my-secret-token```
The response:
```json
{
  "count": 1,
  "queue": [
    {
      "id": 42,
      "to": "+420123456789",
      "message": "Hello from Flask SMS gateway!",
      "status": "Reserved",
      "status_code": -1,
      "retries": 0,
      "queued_at": "2025-10-26 08:51:22",
      "send_after": "2025-10-26 08:51:22",
      "ack_requested": true
    }
  ]
}
```

#### Gateway status (global overview)

Returns a snapshot of the whole database: message counts per table, what is
currently pending, the delivery (ACK) breakdown of sent messages, and modem
state.

```http://yoururl.url:8080/status?token=my-secret-token```
The response:
```json
{
  "totals": {
    "pending": 1,
    "sent": 12,
    "inbox": 0,
    "archive": 34
  },
  "pending": {
    "count": 1,
    "by_status": { "Reserved": 1 },
    "items": [
      {
        "id": 42,
        "to": "+420123456789",
        "status": "Reserved",
        "retries": 0,
        "queued_at": "2025-10-26 08:51:22",
        "ack_requested": true
      }
    ]
  },
  "sent": {
    "count": 12,
    "by_status": { "SendingOKNoReport": 2, "DeliveryOK": 9, "DeliveryFailed": 1 }
  },
  "modems": [
    {
      "id": "modem1",
      "client": "Gammu 1.x",
      "signal": 67,
      "battery": -1,
      "can_send": true,
      "can_receive": true,
      "sent": 12,
      "received": 34
    }
  ]
}
```

The `sent.by_status` breakdown is where ACKs surface: `DeliveryOK` /
`DeliveryFailed` / `DeliveryPending` only appear for messages sent with
`"ack": true`; others stay at `SendingOK` / `SendingOKNoReport`.


#### Receiving SMS
The API will also allow read the sms by GET request.

```http://yoururl.url:8080/receive?token=my-secret-token```
The response:
```json
[
    {
        "from": "+420123456789",
        "id": 1,
        "message": "Thanks for info",
        "received": "2025-10-26 08:51:22"
    },
    {
        "from": "+420234567891",
        "id": 2,
        "message": "Thanks info 2",
        "received": "2025-10-26 08:51:31"
    }
]
```

#### 🛠️ Configuration

You may need to adjust:
- USB modem device path in gammurc
- Volume mounts in docker-compose.yaml
- Port exposure for the API
- Permissions to access serial devices (/dev/ttyUSB*)
- unicode support in configs


### Unicode UTF-8 support

App now support sending and receiving in UTF-8 / UTF-16 format. Keep in mind the UTF8/16 messages are shorter so you can be billed for more messages.

## Responsibility
I am NOT responsible for any charges for mobile operators. Test your configuration fully and accordingly.
