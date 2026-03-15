FROM debian:stable-slim

# Install required packages
RUN apt-get update && \
    apt-get install -y gammu gammu-smsd usbutils minicom busybox sqlite3 libdbi1 libdbd-sqlite3 && \
    rm -rf /var/lib/apt/lists/*

# Copy config files
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
#CMD ["tail", "-f", "/dev/null"]

#HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
#  CMD find /var/spool/gammu/outbox -type f -mmin +2 | grep -q . && exit 1 || exit 0
