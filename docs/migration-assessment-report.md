# Migration Assessment Report
## On-Premises SQL Server to Azure SQL Database

**Assessment:** Database Migration Architect  
**Candidate:** Vidya Meenakshi  
**Database:** AdventureWorks2022  
**Date:** June 2026

---

## 1. Executive Summary

AdventureWorks2022 is a SQL Server 2022 database running on an on-premises
VM (simulated via Docker). This assessment recommends migration to Azure SQL
Database (General Purpose, 2 vCores) using an offline backup/restore approach
during a scheduled maintenance window.

**Recommendation:** Azure SQL Database — low risk, low cost, fully managed.

---

## 2. Source Database Profile

| Item | Detail |
|---|---|
| Database | AdventureWorks2022 |
| SQL Server version | SQL Server 2022 (16.0.4260.1) |
| Compatibility level | 150 |
| Size | ~200MB |
| Tables | 71 |
| Views | 20 |
| Stored Procedures | 10 |
| Functions | 11 |
| Triggers | 10 |
| Foreign Keys | 90 |
| Indexes | 173 |
| Columns | 744 |
| Largest table | Person.Person (19,972 rows) |
| Recovery model | SIMPLE |

---

## 3. Discovery Findings

### Database Objects Inventory
| Object Type | Count | Azure SQL DB Compatible |
|---|---|---|
| Tables | 71 | ✅ Yes |
| Views | 20 | ✅ Yes |
| Stored Procedures | 10 | ✅ Yes |
| Scalar Functions | 10 | ✅ Yes |
| Table-Valued Functions | 1 | ✅ Yes |
| Triggers | 10 | ✅ Yes |
| Foreign Keys | 90 | ✅ Yes |
| Check Constraints | 89 | ✅ Yes |
| Default Constraints | 152 | ✅ Yes |
| SQL Agent Jobs | 0 | N/A |
| Linked Servers | 0 | N/A |
| CLR Assemblies | 0 | N/A |
| Service Broker | 0 | N/A |

### Compatibility Blockers
| Blocker | Found | Risk | Remediation |
|---|---|---|---|
| SQL Agent Jobs | None | None | N/A |
| Linked Servers | None | None | N/A |
| CLR Assemblies | None | None | N/A |
| Cross-DB queries | None | None | N/A |
| Windows Auth | None | None | N/A |
| SSIS packages | None | None | N/A |
| Deprecated syntax | Minor | Low | Review T-SQL |

**Result: Zero compatibility blockers found. Azure SQL Database is viable.**

---

## 4. Target Selection Matrix

| Factor | Azure SQL DB | Azure SQL MI | SQL Server on VM |
|---|---|---|---|
| SQL Agent Jobs | ❌ | ✅ | ✅ |
| Linked Servers | ❌ | ✅ | ✅ |
| CLR | Limited | ✅ | ✅ |
| Cost (monthly) | ~₹8,000 | ~₹25,000 | ~₹15,000 |
| Provisioning time | Minutes | 4-6 hours | 30 mins |
| Management overhead | Low | Medium | High |
| Automatic backups | ✅ | ✅ | Manual |
| Built-in HA | ✅ | ✅ | Manual |
| Private Endpoint | ✅ | ✅ | ✅ |
| PaaS | Full | Partial | No |
| **Recommended** | **✅ YES** | No | No |

---

## 5. Migration Approach

### Selected: Offline Backup/Restore

| Item | Detail |
|---|---|
| Method | Native SQL Server backup (.bak) → restore |
| Downtime | 2-4 hours |
| Complexity | Low |
| Risk | Low |
| Tooling | sqlcmd, docker cp |
| Validation | Automated Python script |

### Why not Azure DMS?
- Database size < 500GB — offline migration acceptable
- Maintenance window available — downtime manageable
- Backup/restore is simpler, faster, well understood
- DMS recommended when zero downtime is required

### Why not BACPAC?
- BACPAC does not preserve all SQL Server objects faithfully
- Backup/restore is faster for large databases
- BACPAC better suited for smaller, simpler schemas

---

## 6. Sizing Recommendation

| Resource | Recommendation | Justification |
|---|---|---|
| Compute | General Purpose, 2 vCores | AdventureWorks is a small-medium workload |
| Storage | 32GB (auto-grow enabled) | Current size ~200MB, room to grow |
| Backup retention | 35 days | Standard enterprise requirement |
| Zone redundancy | Enabled | Production HA requirement |
| Read replica | Optional | Not required for this workload |

---

## 7. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Data loss during migration | Low | High | Validated backup, checksums |
| Application connection failure | Medium | High | Rollback via Key Vault |
| Performance degradation | Low | Medium | Baseline comparison, Query Store |
| Extended downtime | Low | High | Trial migration, rehearsal |
| Collation mismatch | Low | Medium | Verify collation pre-migration |
| Missing objects post-migration | Low | High | Automated validation script |

---

## 8. Validation Results

| Test | Result | Detail |
|---|---|---|
| Row counts | ✅ PASSED | 71 tables — all match |
| Object counts | ✅ PASSED | All object types match |
| Checksum — SalesOrderHeader | ✅ PASSED | 31,465 rows, sum=123,216,786 |
| Checksum — SalesOrderDetail | ✅ PASSED | 121,317 rows, sum=56,423,747 |
| Checksum — Product | ✅ PASSED | 504 rows, sum=221,087 |
| Checksum — Person | ✅ PASSED | 19,972 rows |
| Checksum — PurchaseOrderHeader | ✅ PASSED | 4,012 rows |
| Foreign key count | ✅ PASSED | 90 FK keys match |
| Schema validation | ✅ PASSED | 744 columns match |
| **Overall** | **✅ PASSED** | **9/9 checks, 0 failures** |

---

## 9. Post-Migration Recommendations

| Action | Priority | Detail |
|---|---|---|
| Update compatibility level | High | Change from 150 to 160 |
| Enable Query Store | High | Monitor query performance |
| Update statistics | Medium | Run after migration |
| Rebuild indexes | Medium | Check fragmentation |
| Enable auditing | High | Azure SQL Auditing to Log Analytics |
| Configure alerts | High | CPU, DTU, connections, storage |
| Test backup restore | High | Verify PITR works within 24h |
| Remove sa login | High | Use managed identity instead |

---

## 10. Lessons Learned

| Item | Learning |
|---|---|
| File permissions | Docker cp creates files owned by host user — chown needed before restore |
| ARM64 compatibility | SQL Server 2022 runs on Mac M-series via Docker with minor warnings |
| GitHub file limits | .bak files exceed 100MB limit — exclude from git, document download steps |
| Token authentication | GitHub requires PAT — store securely, rotate regularly |
| Validation first | Always run validation before cutover — automated script saves time |

---

## 11. Scale Model — 50-200 Database Factory

To scale this pattern across 50-200 databases:

```
1. Wave Planning
   → Group databases by size, complexity, downtime tolerance
   → Assign to waves (pilot → small → medium → large)

2. Automation
   → Parameterize migration scripts per database
   → Run discovery crawler across all source servers
   → Generate assessment report per database automatically

3. CI/CD Factory
   → One pipeline template, N database instances
   → Parallel migration waves where dependencies allow
   → Automated validation gates before cutover

4. Operating Model
   → Migration team: DBA + Azure Admin + App Team per wave
   → Hypercare: 72 hours per wave
   → Runbook: same template, database-specific parameters
```