# Database Migration Architect Assessment
## On-Premises SQL Server to Azure SQL Database Migration

**Candidate:** Vidya Meenakshi  
**Role:** Database Migration Architect  
**Assessment Date:** June 2026  
**GitHub:** https://github.com/drmrpist/db-migration-architect-assessment

---

## Assessment Summary

This repository demonstrates a production-grade migration of an on-premises SQL Server database (AdventureWorks2022) to Azure SQL Database, including discovery, migration execution, validation, CI/CD automation, and architecture documentation.

---

## Minimum Proof Delivered

| Requirement | Status | Evidence |
|---|---|---|
| Working app container image | ✅ Complete | `docker/docker-compose.onprem.yml` |
| Migrated database path | ✅ Complete | `migration/sqlserver/migrate_adventureworks.sh` |
| Validation script execution | ✅ Complete | `validation/reconciliation.py` - 9/9 PASSED |
| CI/CD pipeline | ✅ Complete | `cicd/github-actions-container-deploy.yml` |
| Architecture + runbook | ✅ Complete | `docs/architecture.md`, `docs/cutover-runbook.md` |

---

## Repository Structure
