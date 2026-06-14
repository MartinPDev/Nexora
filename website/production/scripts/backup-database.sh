#!/bin/bash

BACKUP_DIR="/var/backups/nexora"
DB_FILE="/var/www/nexora/website_backend/early_access.db"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")

mkdir -p "$BACKUP_DIR"

cp "$DB_FILE" "$BACKUP_DIR/early_access_$DATE.db"

find "$BACKUP_DIR" -type f -name "*.db" -mtime +30 -delete
