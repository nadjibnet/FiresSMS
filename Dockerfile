# All-in-one image: Gammu SMSD daemon + Flask API in a single container.
#
# The two-container docker-compose.yaml remains the canonical setup; this image
# is a self-contained alternative whose runtime config is driven by env vars.
# Build context must be the repository root.
FROM python:3.11-slim

# --- System packages: Gammu SMSD + helpers ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gammu gammu-smsd sqlite3 libdbi1 libdbd-sqlite3 usbutils busybox && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python API ---
COPY dockers/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY dockers/api/app.py /app/app.py
COPY dockers/api/services /app/services

# --- Default configuration (overridable at runtime via env vars) ---
COPY configs/gammurc /etc/gammurc
COPY configs/smsdrc /etc/smsd/smsdrc
# Init script lives outside the DB volume so it survives a mounted volume.
COPY database/database_init.sql /app/database_init.sql

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Empty GAMMU_* means "use the value already in the config file".
# Set any of these at run time to override the bundled defaults.
ENV GAMMU_DEVICE="" \
    GAMMU_CONNECTION="" \
    API_TOKEN="changeme" \
    API_PORT="8080" \
    GAMMU_DB_PATH="/var/lib/gammu/smsd.db"

# Persist the SQLite database across container restarts. GAMMU_DB_PATH (and
# the smsdrc DBDir) live under this path; mount a host dir or named volume here.
VOLUME ["/var/lib/gammu"]

# Documents the default API port; change API_PORT at run time and publish with
# -p <host>:<API_PORT>.
EXPOSE ${API_PORT}

ENTRYPOINT ["/entrypoint.sh"]
