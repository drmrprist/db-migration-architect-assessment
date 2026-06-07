#!/bin/bash
# =============================================
# SQL Server Migration Script
# Source: On-Prem SQL Server (Docker container)
# Target: Azure SQL Database (or local target)
# Database: AdventureWorks2022
# =============================================

set -e

# --- Configuration ---
SRC_HOST="localhost"
SRC_PORT="1433"
SRC_USER="sa"
SRC_PASSWORD="SourceDB@12345"
SRC_DB="AdventureWorks2022"

TGT_HOST="localhost"
TGT_PORT="1434"
TGT_USER="sa"
TGT_PASSWORD="TargetDB@12345"
TGT_DB="AdventureWorks2022"

BACKUP_DIR="$HOME/db-migration-assessment/migration/sqlserver"
BACKUP_FILE="AdventureWorks2022_migration.bak"
LOG_FILE="$BACKUP_DIR/migration_log.txt"

echo "=======================================" | tee -a $LOG_FILE
echo "Migration started: $(date)" | tee -a $LOG_FILE
echo "=======================================" | tee -a $LOG_FILE

# --- Step 1: Pre-migration row count on source ---
echo "" | tee -a $LOG_FILE
echo "STEP 1: Capturing source row counts..." | tee -a $LOG_FILE

sqlcmd -S $SRC_HOST,$SRC_PORT -U $SRC_USER -P "$SRC_PASSWORD" -C -d $SRC_DB -Q "
SELECT 
    SCHEMA_NAME(schema_id) AS schema_name,
    name AS table_name,
    SUM(p.rows) AS row_count
FROM sys.tables t
JOIN sys.partitions p ON t.object_id = p.object_id
WHERE p.index_id IN (0,1)
GROUP BY schema_id, name
ORDER BY schema_name, table_name
" -o "$BACKUP_DIR/source_rowcounts.txt" 2>&1 | tee -a $LOG_FILE

echo "Source row counts saved." | tee -a $LOG_FILE

# --- Step 2: Backup source database ---
echo "" | tee -a $LOG_FILE
echo "STEP 2: Taking backup of source database..." | tee -a $LOG_FILE

sqlcmd -S $SRC_HOST,$SRC_PORT -U $SRC_USER -P "$SRC_PASSWORD" -C -Q "
BACKUP DATABASE [$SRC_DB]
TO DISK = '/var/opt/mssql/data/$BACKUP_FILE'
WITH FORMAT, INIT, COMPRESSION,
NAME = 'AdventureWorks2022 Migration Backup',
STATS = 10
" 2>&1 | tee -a $LOG_FILE

echo "Backup completed." | tee -a $LOG_FILE

# --- Step 3: Copy backup to target container ---
echo "" | tee -a $LOG_FILE
echo "STEP 3: Copying backup to target container..." | tee -a $LOG_FILE

docker cp sqlserver-source:/var/opt/mssql/data/$BACKUP_FILE \
    $BACKUP_DIR/$BACKUP_FILE 2>&1 | tee -a $LOG_FILE

docker cp $BACKUP_DIR/$BACKUP_FILE \
    sqlserver-target:/var/opt/mssql/data/$BACKUP_FILE 2>&1 | tee -a $LOG_FILE

echo "Backup copied to target container." | tee -a $LOG_FILE

# --- Step 4: Restore on target ---
echo "" | tee -a $LOG_FILE
echo "STEP 4: Restoring database on target..." | tee -a $LOG_FILE

sqlcmd -S $TGT_HOST,$TGT_PORT -U $TGT_USER -P "$TGT_PASSWORD" -C -Q "
RESTORE DATABASE [$TGT_DB]
FROM DISK = '/var/opt/mssql/data/$BACKUP_FILE'
WITH MOVE '$SRC_DB' TO '/var/opt/mssql/data/${TGT_DB}.mdf',
MOVE '${SRC_DB}_log' TO '/var/opt/mssql/data/${TGT_DB}_log.ldf',
NOUNLOAD, REPLACE, STATS = 10
" 2>&1 | tee -a $LOG_FILE

echo "Restore completed." | tee -a $LOG_FILE

# --- Step 5: Verify target database is online ---
echo "" | tee -a $LOG_FILE
echo "STEP 5: Verifying target database..." | tee -a $LOG_FILE

sqlcmd -S $TGT_HOST,$TGT_PORT -U $TGT_USER -P "$TGT_PASSWORD" -C -Q "
SELECT name, state_desc, recovery_model_desc
FROM sys.databases
WHERE name = '$TGT_DB'
" 2>&1 | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "=======================================" | tee -a $LOG_FILE
echo "Migration completed: $(date)" | tee -a $LOG_FILE
echo "=======================================" | tee -a $LOG_FILE