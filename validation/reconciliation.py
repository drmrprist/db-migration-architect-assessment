#!/usr/bin/env python3
"""
=============================================
Database Migration Validation Script
Assessment: DB Migration Architect
Source: SQL Server on-prem (port 1433)
Target: SQL Server Azure target (port 1434)
Database: AdventureWorks2022
=============================================
"""

import pymssql
import json
import csv
import sys
from datetime import datetime

# --- Configuration ---
SOURCE = {
    "host": "localhost",
    "port": 1433,
    "user": "sa",
    "password": "SourceDB@12345",
    "database": "AdventureWorks2022"
}

TARGET = {
    "host": "localhost",
    "port": 1434,
    "user": "sa",
    "password": "TargetDB@12345",
    "database": "AdventureWorks2022"
}

OUTPUT_FILE = "validation_report.json"
PASSED = []
FAILED = []
WARNINGS = []

def get_connection(config):
    return pymssql.connect(
        server=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"]
    )

def run_query(conn, sql):
    cursor = conn.cursor(as_dict=True)
    cursor.execute(sql)
    return cursor.fetchall()

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# =============================================
# TEST 1: Row Count Validation
# =============================================
def test_row_counts(src_conn, tgt_conn):
    log("TEST 1: Row count validation...")
    sql = """
        SELECT 
            SCHEMA_NAME(schema_id) AS schema_name,
            name AS table_name,
            SUM(p.rows) AS row_count
        FROM sys.tables t
        JOIN sys.partitions p ON t.object_id = p.object_id
        WHERE p.index_id IN (0,1)
        GROUP BY schema_id, name
        ORDER BY schema_name, table_name
    """
    src_rows = {f"{r['schema_name']}.{r['table_name']}": r['row_count'] 
                for r in run_query(src_conn, sql)}
    tgt_rows = {f"{r['schema_name']}.{r['table_name']}": r['row_count'] 
                for r in run_query(tgt_conn, sql)}

    mismatches = []
    for table, src_count in src_rows.items():
        tgt_count = tgt_rows.get(table, 0)
        if src_count != tgt_count:
            mismatches.append({
                "table": table,
                "source_rows": src_count,
                "target_rows": tgt_count,
                "difference": src_count - tgt_count
            })

    if not mismatches:
        PASSED.append(f"ROW COUNTS: All {len(src_rows)} tables match")
        log(f"  PASSED - All {len(src_rows)} tables match")
    else:
        FAILED.append(f"ROW COUNTS: {len(mismatches)} tables have mismatches")
        log(f"  FAILED - {len(mismatches)} mismatches found")
        for m in mismatches:
            log(f"    {m['table']}: source={m['source_rows']} target={m['target_rows']}")

    return src_rows, tgt_rows, mismatches

# =============================================
# TEST 2: Object Count Validation
# =============================================
def test_object_counts(src_conn, tgt_conn):
    log("TEST 2: Object count validation...")
    sql = """
        SELECT type_desc, COUNT(*) AS object_count
        FROM sys.objects
        WHERE is_ms_shipped = 0
        GROUP BY type_desc
        ORDER BY type_desc
    """
    src_objects = {r['type_desc']: r['object_count'] 
                   for r in run_query(src_conn, sql)}
    tgt_objects = {r['type_desc']: r['object_count'] 
                   for r in run_query(tgt_conn, sql)}

    mismatches = []
    for obj_type, src_count in src_objects.items():
        tgt_count = tgt_objects.get(obj_type, 0)
        if src_count != tgt_count:
            mismatches.append({
                "object_type": obj_type,
                "source": src_count,
                "target": tgt_count
            })

    if not mismatches:
        PASSED.append(f"OBJECT COUNTS: All object types match")
        log(f"  PASSED - All object types match")
    else:
        FAILED.append(f"OBJECT COUNTS: {len(mismatches)} mismatches")
        log(f"  FAILED - {len(mismatches)} mismatches")

    return mismatches

# =============================================
# TEST 3: Checksum Validation (Key Tables)
# =============================================
def test_checksums(src_conn, tgt_conn):
    log("TEST 3: Checksum validation on key tables...")
    key_tables = [
        ("Sales", "SalesOrderHeader", "SalesOrderID", "TotalDue"),
        ("Sales", "SalesOrderDetail", "SalesOrderDetailID", "UnitPrice"),
        ("Production", "Product", "ProductID", "ListPrice"),
        ("Person", "Person", "BusinessEntityID", "BusinessEntityID"),
        ("Purchasing", "PurchaseOrderHeader", "PurchaseOrderID", "TotalDue"),
    ]

    results = []
    for schema, table, pk, agg_col in key_tables:
        sql = f"""
            SELECT 
                COUNT(*) AS row_count,
                SUM(CAST({agg_col} AS FLOAT)) AS column_sum,
                MAX({agg_col}) AS max_val,
                MIN({agg_col}) AS min_val
            FROM [{schema}].[{table}]
        """
        try:
            src = run_query(src_conn, sql)[0]
            tgt = run_query(tgt_conn, sql)[0]

            match = (
                src['row_count'] == tgt['row_count'] and
                abs((src['column_sum'] or 0) - (tgt['column_sum'] or 0)) < 0.01
            )

            status = "PASSED" if match else "FAILED"
            results.append({
                "table": f"{schema}.{table}",
                "status": status,
                "src_count": src['row_count'],
                "tgt_count": tgt['row_count'],
                "src_sum": src['column_sum'],
                "tgt_sum": tgt['column_sum']
            })

            if match:
                PASSED.append(f"CHECKSUM: {schema}.{table} matches")
                log(f"  PASSED - {schema}.{table} rows={src['row_count']} sum={src['column_sum']:.2f}")
            else:
                FAILED.append(f"CHECKSUM: {schema}.{table} mismatch")
                log(f"  FAILED - {schema}.{table}")

        except Exception as e:
            WARNINGS.append(f"CHECKSUM: {schema}.{table} error: {str(e)}")
            log(f"  WARNING - {schema}.{table}: {str(e)}")

    return results

# =============================================
# TEST 4: Foreign Key Integrity
# =============================================
def test_foreign_keys(src_conn, tgt_conn):
    log("TEST 4: Foreign key count validation...")
    sql = """
        SELECT COUNT(*) AS fk_count
        FROM sys.foreign_keys
    """
    src_fk = run_query(src_conn, sql)[0]['fk_count']
    tgt_fk = run_query(tgt_conn, sql)[0]['fk_count']

    if src_fk == tgt_fk:
        PASSED.append(f"FOREIGN KEYS: Count matches ({src_fk})")
        log(f"  PASSED - Foreign key count matches: {src_fk}")
    else:
        FAILED.append(f"FOREIGN KEYS: Source={src_fk} Target={tgt_fk}")
        log(f"  FAILED - Source={src_fk} Target={tgt_fk}")

    return src_fk, tgt_fk

# =============================================
# TEST 5: Schema Validation
# =============================================
def test_schema(src_conn, tgt_conn):
    log("TEST 5: Schema validation...")
    sql = """
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, 
               DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
    """
    src_schema = {f"{r['TABLE_SCHEMA']}.{r['TABLE_NAME']}.{r['COLUMN_NAME']}": r 
                  for r in run_query(src_conn, sql)}
    tgt_schema = {f"{r['TABLE_SCHEMA']}.{r['TABLE_NAME']}.{r['COLUMN_NAME']}": r 
                  for r in run_query(tgt_conn, sql)}

    missing = [k for k in src_schema if k not in tgt_schema]
    type_mismatches = []

    for k in src_schema:
        if k in tgt_schema:
            if src_schema[k]['DATA_TYPE'] != tgt_schema[k]['DATA_TYPE']:
                type_mismatches.append(k)

    if not missing and not type_mismatches:
        PASSED.append(f"SCHEMA: All {len(src_schema)} columns match")
        log(f"  PASSED - All {len(src_schema)} columns match")
    else:
        if missing:
            FAILED.append(f"SCHEMA: {len(missing)} missing columns in target")
            log(f"  FAILED - {len(missing)} missing columns")
        if type_mismatches:
            FAILED.append(f"SCHEMA: {len(type_mismatches)} data type mismatches")
            log(f"  FAILED - {len(type_mismatches)} type mismatches")

    return missing, type_mismatches

# =============================================
# GENERATE REPORT
# =============================================
def generate_report(row_count_mismatches, obj_mismatches, 
                    checksum_results, fk_counts, schema_missing):
    report = {
        "assessment": "DB Migration Architect - Validation Report",
        "timestamp": datetime.now().isoformat(),
        "source": f"{SOURCE['host']}:{SOURCE['port']}/{SOURCE['database']}",
        "target": f"{TARGET['host']}:{TARGET['port']}/{TARGET['database']}",
        "summary": {
            "total_passed": len(PASSED),
            "total_failed": len(FAILED),
            "total_warnings": len(WARNINGS),
            "overall_status": "PASSED" if not FAILED else "FAILED"
        },
        "passed_checks": PASSED,
        "failed_checks": FAILED,
        "warnings": WARNINGS,
        "details": {
            "row_count_mismatches": row_count_mismatches,
            "object_count_mismatches": obj_mismatches,
            "checksum_results": checksum_results,
            "foreign_key_counts": {
                "source": fk_counts[0],
                "target": fk_counts[1]
            },
            "missing_columns": schema_missing
        }
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    return report

# =============================================
# MAIN
# =============================================
def main():
    log("===========================================")
    log("DB Migration Validation Starting")
    log("===========================================")

    try:
        log("Connecting to source database...")
        src_conn = get_connection(SOURCE)
        log("Connecting to target database...")
        tgt_conn = get_connection(TARGET)
    except Exception as e:
        log(f"ERROR: Cannot connect to database: {str(e)}")
        sys.exit(1)

    src_rows, tgt_rows, row_mismatches = test_row_counts(src_conn, tgt_conn)
    obj_mismatches = test_object_counts(src_conn, tgt_conn)
    checksum_results = test_checksums(src_conn, tgt_conn)
    fk_counts = test_foreign_keys(src_conn, tgt_conn)
    schema_missing, _ = test_schema(src_conn, tgt_conn)

    report = generate_report(
        row_mismatches, obj_mismatches,
        checksum_results, fk_counts, schema_missing
    )

    log("")
    log("===========================================")
    log(f"VALIDATION COMPLETE")
    log(f"PASSED : {len(PASSED)}")
    log(f"FAILED : {len(FAILED)}")
    log(f"WARNINGS: {len(WARNINGS)}")
    log(f"STATUS : {report['summary']['overall_status']}")
    log(f"REPORT : {OUTPUT_FILE}")
    log("===========================================")

    src_conn.close()
    tgt_conn.close()

if __name__ == "__main__":
    main()