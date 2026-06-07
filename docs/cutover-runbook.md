# Cutover Runbook
## On-Premises SQL Server to Azure SQL Database

**Assessment:** Database Migration Architect  
**Candidate:** Vidya Meenakshi  
**Database:** AdventureWorks2022  
**Date:** June 2026

---

## Pre-Cutover Checklist

### T-7 Days
- [ ] Migration assessment report signed off
- [ ] Azure SQL Database provisioned and tested
- [ ] Private endpoint and DNS configured
- [ ] Key Vault secrets loaded (DB connection string)
- [ ] App Service configured with managed identity
- [ ] Validation scripts tested against target
- [ ] Rollback plan reviewed and approved
- [ ] Hypercare team identified

### T-3 Days
- [ ] Trial migration executed and validated
- [ ] Performance baseline captured on source
- [ ] Performance baseline captured on target
- [ ] Application smoke test passed on target
- [ ] Stakeholder sign-off obtained
- [ ] Maintenance window communicated to users
- [ ] Support team briefed

### T-1 Day
- [