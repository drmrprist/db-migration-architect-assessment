-- =============================================
-- SQL Server Database Inventory Script
-- Assessment: DB Migration Architect
-- Source: AdventureWorks2022
-- =============================================

-- 1. DATABASE OVERVIEW
PRINT '=== DATABASE OVERVIEW ==='
SELECT 
    name,
    database_id,
    state_desc,
    recovery_model_desc,
    compatibility_level,
    collation_name,
    is_auto_shrink_on,
    is_auto_update_stats_on,
    create_date
FROM sys.databases
WHERE name = 'AdventureWorks2022'
GO

-- 2. DATABASE SIZE
PRINT '=== DATABASE SIZE ==='
USE AdventureWorks2022
GO
SELECT 
    DB_NAME() AS database_name,
    SUM(size * 8.0 / 1024) AS size_mb,
    SUM(size * 8.0 / 1024 / 1024) AS size_gb
FROM sys.database_files
GO

-- 3. TABLE INVENTORY WITH ROW COUNTS
PRINT '=== TABLE INVENTORY ==='
SELECT 
    s.name AS schema_name,
    t.name AS table_name,
    p.rows AS row_count,
    CAST(SUM(a.total_pages) * 8.0 / 1024 AS DECIMAL(10,2)) AS total_size_mb
FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
JOIN sys.indexes i ON t.object_id = i.object_id
JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE i.index_id <= 1
GROUP BY s.name, t.name, p.rows
ORDER BY p.rows DESC
GO

-- 4. STORED PROCEDURES
PRINT '=== STORED PROCEDURES ==='
SELECT 
    s.name AS schema_name,
    p.name AS procedure_name,
    p.create_date,
    p.modify_date
FROM sys.procedures p
JOIN sys.schemas s ON p.schema_id = s.schema_id
ORDER BY s.name, p.name
GO

-- 5. VIEWS
PRINT '=== VIEWS ==='
SELECT 
    s.name AS schema_name,
    v.name AS view_name,
    v.create_date,
    v.modify_date
FROM sys.views v
JOIN sys.schemas s ON v.schema_id = s.schema_id
ORDER BY s.name, v.name
GO

-- 6. FUNCTIONS
PRINT '=== FUNCTIONS ==='
SELECT 
    s.name AS schema_name,
    o.name AS function_name,
    o.type_desc,
    o.create_date
FROM sys.objects o
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE o.type IN ('FN','IF','TF')
ORDER BY s.name, o.name
GO

-- 7. TRIGGERS
PRINT '=== TRIGGERS ==='
SELECT 
    t.name AS trigger_name,
    OBJECT_NAME(t.parent_id) AS table_name,
    t.is_disabled,
    t.create_date
FROM sys.triggers t
WHERE t.parent_class = 1
GO

-- 8. INDEXES
PRINT '=== INDEXES ==='
SELECT 
    s.name AS schema_name,
    t.name AS table_name,
    i.name AS index_name,
    i.type_desc,
    i.is_unique,
    i.is_primary_key
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE i.name IS NOT NULL
ORDER BY s.name, t.name, i.name
GO

-- 9. FOREIGN KEYS
PRINT '=== FOREIGN KEYS ==='
SELECT 
    fk.name AS fk_name,
    OBJECT_NAME(fk.parent_object_id) AS parent_table,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS parent_column,
    OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS referenced_column
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
ORDER BY parent_table
GO

-- 10. USERS AND ROLES
PRINT '=== USERS AND ROLES ==='
SELECT 
    dp.name AS principal_name,
    dp.type_desc,
    dp.create_date,
    dp.is_disabled
FROM sys.database_principals dp
WHERE dp.type IN ('S','U','G','R')
AND dp.name NOT IN ('sys','INFORMATION_SCHEMA','guest')
ORDER BY dp.type_desc, dp.name
GO

-- 11. OBJECT COUNT SUMMARY
PRINT '=== OBJECT COUNT SUMMARY ==='
SELECT 
    type_desc,
    COUNT(*) AS object_count
FROM sys.objects
WHERE is_ms_shipped = 0
GROUP BY type_desc
ORDER BY object_count DESC
GO

-- 12. TOP 10 LARGEST TABLES
PRINT '=== TOP 10 LARGEST TABLES ==='
SELECT TOP 10
    s.name AS schema_name,
    t.name AS table_name,
    p.rows AS row_count,
    CAST(SUM(a.total_pages) * 8.0 / 1024 AS DECIMAL(10,2)) AS total_size_mb
FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
JOIN sys.indexes i ON t.object_id = i.object_id
JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE i.index_id <= 1
GROUP BY s.name, t.name, p.rows
ORDER BY total_size_mb DESC
GO