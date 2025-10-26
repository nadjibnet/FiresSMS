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
