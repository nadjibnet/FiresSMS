#!/usr/bin/bash
# Start syslogd to forward logs to stdout
busybox syslogd -n -O /dev/stdout &

# Initialize the database if it doesn't exist
if [ ! -f /var/lib/gammu/smsd.db ]; then
    echo "Database file not found! Initializing new database."
    touch /var/lib/gammu/smsd.db
    sqlite3 /var/lib/gammu/smsd.db < /var/lib/gammu/database_init.sql
    sleep 5
else
    echo "Database file found."
fi  

# Start Gammu SMSD
gammu-smsd -c /etc/smsd/smsdrc
