#!/usr/bin/env bash
# Entrypoint for the all-in-one image: applies env-var overrides to the bundled
# config files, then runs gammu-smsd and the Flask API side by side.
set -e

GAMMURC=/etc/gammurc
SMSDRC=/etc/smsd/smsdrc

# --- Config overrides: only touch a line when its env var is set, otherwise
#     the value shipped in the config file is used unchanged. ---
if [ -n "$GAMMU_DEVICE" ]; then
    echo "Overriding device port -> $GAMMU_DEVICE"
    sed -i "s|^port *=.*|port = ${GAMMU_DEVICE}|" "$GAMMURC" "$SMSDRC"
fi

if [ -n "$GAMMU_CONNECTION" ]; then
    echo "Overriding connection -> $GAMMU_CONNECTION"
    sed -i "s|^connection *=.*|connection = ${GAMMU_CONNECTION}|" "$GAMMURC" "$SMSDRC"
fi

# --- Show the effective configuration. Device/connection are read back from
#     the config file so they reflect overrides as well as the bundled
#     defaults; the token is masked so the secret never lands in the logs. ---
if [ "$API_TOKEN" = "changeme" ]; then
    TOKEN_INFO="changeme (default - CHANGE ME!)"
else
    TOKEN_INFO="******** (custom, ${#API_TOKEN} chars)"
fi
echo "==================== FiresSMS configuration ===================="
echo "  Modem device   : $(grep -m1 '^port'       "$GAMMURC" | cut -d= -f2- | xargs)"
echo "  Connection     : $(grep -m1 '^connection' "$GAMMURC" | cut -d= -f2- | xargs)"
echo "  API port       : ${API_PORT:-8080}"
echo "  API token      : ${TOKEN_INFO}"
echo "  Database path  : ${GAMMU_DB_PATH}"
echo "================================================================"

# Forward syslog (where gammu-smsd logs) to the container's stdout.
busybox syslogd -n -O /dev/stdout &

# Initialise the SQLite database on first run. The DB lives on a mounted volume
# (/var/lib/gammu), so it persists; the init script ships in the image at /app.
if [ ! -f "$GAMMU_DB_PATH" ]; then
    echo "Database not found, initialising $GAMMU_DB_PATH"
    mkdir -p "$(dirname "$GAMMU_DB_PATH")"
    sqlite3 "$GAMMU_DB_PATH" < /app/database_init.sql
else
    echo "Database found at $GAMMU_DB_PATH"
fi

# Start both processes; if either exits, stop the container so Docker can
# restart it (a single dead process should not leave a half-running gateway).
echo "Starting gammu-smsd..."
gammu-smsd -c "$SMSDRC" &

echo "Starting Flask API on :${API_PORT:-8080}..."
python /app/app.py &

wait -n
echo "A process exited; shutting down container."
exit 1
