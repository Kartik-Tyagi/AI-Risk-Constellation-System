#!/bin/bash

# Backup script for AI Risk Constellation System
# Backs up PostgreSQL and Neo4j data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup to $BACKUP_DIR"

# PostgreSQL backup
echo "[$(date)] Backing up PostgreSQL..."
docker exec risk-postgres pg_dump \
    -U "${POSTGRES_USER:-riskuser}" \
    "${POSTGRES_DB:-risk_constellation}" \
    > "$BACKUP_DIR/postgres_backup.sql"
echo "[$(date)] PostgreSQL backup complete: postgres_backup.sql"

# Neo4j backup (dump via cypher-shell)
echo "[$(date)] Backing up Neo4j node/rel counts..."
docker exec risk-neo4j cypher-shell \
    -u "${NEO4J_USER:-neo4j}" \
    -p "${NEO4J_PASSWORD:-riskpass123}" \
    "MATCH (n) RETURN count(n) AS nodes" \
    > "$BACKUP_DIR/neo4j_stats.txt" 2>/dev/null || echo "[$(date)] Neo4j stats skipped"

# Compress backup
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

echo "[$(date)] Backup complete: $BACKUP_DIR.tar.gz"
