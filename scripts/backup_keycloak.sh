#!/bin/bash
# scripts/backup_keycloak.sh
# Automates Keycloak PostgreSQL Database backup and Realm Export
# Recommended to run via Cron daily.

set -e

BACKUP_DIR="/opt/intellicare/backups/keycloak"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="keycloak-db"
KC_CONTAINER="keycloak-intellicare"
DB_USER="keycloak_admin"
DB_NAME="keycloak_db"

mkdir -p "$BACKUP_DIR"

echo "Starting Keycloak Backup Process - $TIMESTAMP"

# 1. Backup PostgreSQL Database
echo "  -> Dumping PostgreSQL database..."
docker exec -t $DB_CONTAINER pg_dump -U $DB_USER -d $DB_NAME -F c > "$BACKUP_DIR/kc_db_$TIMESTAMP.dump"

# 2. Export Realm Configuration (bemcuidar)
echo "  -> Exporting 'bemcuidar' realm from Keycloak..."
# Must use the standalone export tool shipped with Keycloak 24+
# Using `/opt/keycloak/bin/kc.sh export`
docker exec -t $KC_CONTAINER /opt/keycloak/bin/kc.sh export \
  --realm bemcuidar \
  --users skip \
  --file /tmp/bemcuidar-realm-backup.json

# Copy to host
docker cp $KC_CONTAINER:/tmp/bemcuidar-realm-backup.json "$BACKUP_DIR/bemcuidar-realm-$TIMESTAMP.json"

# Cleanup from container
docker exec -t $KC_CONTAINER rm /tmp/bemcuidar-realm-backup.json

# 3. Compress and Retain (Keep last 7 days)
echo "  -> Compressing artifacts..."
tar -czvf "$BACKUP_DIR/keycloak_backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "kc_db_$TIMESTAMP.dump" "bemcuidar-realm-$TIMESTAMP.json"
rm "$BACKUP_DIR/kc_db_$TIMESTAMP.dump" "$BACKUP_DIR/bemcuidar-realm-$TIMESTAMP.json"

echo "  -> Cleaning up old backups (older than 7 days)..."
find "$BACKUP_DIR" -type f -name "keycloak_backup_*.tar.gz" -mtime +7 -delete

echo "Backup Keycloak completed successfully: $BACKUP_DIR/keycloak_backup_$TIMESTAMP.tar.gz"
