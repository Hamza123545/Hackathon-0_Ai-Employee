# Rollback Procedure Documentation (T105)

**Date**: 2026-01-09  
**Purpose**: Guide for disabling Silver Tier features and reverting to Bronze Tier operation

---

## Overview

This document describes how to rollback from Silver Tier to Bronze Tier operation if needed. The rollback preserves all data and allows clean re-enablement of Silver Tier features later.

---

## Prerequisites

- Access to the Obsidian vault
- PM2 installed (for stopping processes)
- Terminal/command line access

---

## Rollback Steps

### Step 1: Stop Silver Tier Processes

**Stop PM2 Processes**:
```bash
cd AI_Employee
pm2 stop all
pm2 delete all
```

**Verify Processes Stopped**:
```bash
pm2 list
# Should show "empty" or no processes
```

**Alternative (if PM2 not available)**:
- Manually stop any running watcher processes
- Stop orchestrator process if running

---

### Step 2: Disable MCP Servers

**Option A: Remove MCP Server Configuration**

1. Remove or comment out MCP server environment variables in `.env`:
```bash
# Comment out or remove:
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=...
# SMTP_PASSWORD=...
# LINKEDIN_ACCESS_TOKEN=...
# LINKEDIN_PERSON_URN=...
```

2. Or rename `.env` to `.env.silver` (backup):
```bash
mv .env .env.silver
cp .env.bronze .env  # If you have a Bronze-only .env backup
```

**Option B: Keep Configuration but Don't Start Servers**

- Simply don't start MCP servers
- Configuration can remain for future use

---

### Step 3: Disable Approval Orchestrator

**The orchestrator is already stopped in Step 1 (PM2 stop all).**

**Manual Verification**:
- Check that no `run_orchestrator.py` process is running
- Verify `/Approved/` folder is not being monitored

---

### Step 4: Revert to Bronze Tier Entry Point

**Use Bronze Tier Main Entry Point**:
```bash
cd AI_Employee
python -m AI_Employee.main
```

**Or with environment variables**:
```bash
export WATCHER_TYPE=gmail  # or filesystem
export VAULT_PATH=/path/to/vault
python -m AI_Employee.main
```

**This starts a single watcher (Bronze tier mode).**

---

### Step 5: Preserve Audit Logs (Optional)

**Audit logs are preserved automatically** - they remain in `/Logs/` folder.

**To Archive Logs**:
```bash
# Create archive directory
mkdir -p vault/Logs/archive

# Move old logs (optional)
mv vault/Logs/*.json vault/Logs/archive/  # If you want to archive

# Or keep logs for future reference
# Logs remain in /Logs/ folder, just not actively written to
```

**Note**: Audit logs are read-only after rollback (no new entries written).

---

### Step 6: Verify Bronze Tier Operation

**Check Vault Structure**:
- `/Needs_Action/` - Action items created ✅
- `/Done/` - Completed items archived ✅
- `/Plans/` - Plans generated ✅
- `Dashboard.md` - Dashboard updated ✅

**Verify Watcher Running**:
- Check console output for watcher activity
- Verify action items are being created
- Check `Dashboard.md` for watcher status

---

## Re-enabling Silver Tier

**To re-enable Silver Tier after rollback**:

1. **Restore Configuration**:
```bash
# Restore .env if backed up
mv .env.silver .env
```

2. **Start PM2 Processes**:
```bash
cd AI_Employee
pm2 start ecosystem.config.js
pm2 save  # Save PM2 configuration
```

3. **Verify Silver Tier Running**:
```bash
pm2 list
pm2 logs  # Check for errors
```

4. **Check Dashboard**:
- Open `Dashboard.md` in Obsidian
- Verify Silver Tier metrics displayed
- Check MCP server health status

---

## Data Preservation

### ✅ All Data Preserved During Rollback

**Preserved Data**:
- Action items in `/Needs_Action/` ✅
- Completed items in `/Done/` ✅
- Plans in `/Plans/` ✅
- Audit logs in `/Logs/` ✅ (read-only after rollback)
- Approval requests in `/Pending_Approval/` ✅ (can be processed later)
- Approved requests in `/Approved/` ✅ (can be executed when Silver re-enabled)
- Rejected requests in `/Rejected/` ✅

**No Data Loss**: All files remain in vault, just not actively processed.

---

## Rollback Scenarios

### Scenario 1: Temporary Rollback (Testing)

**Steps**:
1. Stop PM2 processes
2. Use Bronze tier entry point
3. Test Bronze tier functionality
4. Re-enable Silver tier when ready

**Data**: All preserved, can resume Silver tier immediately

---

### Scenario 2: Permanent Rollback (Downgrade)

**Steps**:
1. Stop PM2 processes
2. Remove MCP server configuration
3. Use Bronze tier entry point permanently
4. Archive Silver tier folders (optional)

**Data**: All preserved, Silver tier folders can be deleted if not needed

---

### Scenario 3: Partial Rollback (Disable Specific Features)

**Disable Approval Workflow Only**:
- Stop orchestrator: `pm2 stop approval-orchestrator`
- Keep watchers running
- Keep MCP servers running (but no approvals processed)

**Disable MCP Servers Only**:
- Stop MCP server processes
- Keep watchers running
- Keep orchestrator running (but no actions executed)

**Disable Specific Watcher**:
- Stop specific watcher: `pm2 stop gmail-watcher`
- Other watchers continue running

---

## Troubleshooting

### Issue: PM2 processes won't stop

**Solution**:
```bash
pm2 kill  # Force kill all PM2 processes
pm2 resurrect  # Restore if needed
```

### Issue: Bronze tier entry point not working

**Solution**:
- Verify environment variables set correctly
- Check vault path is correct
- Verify watcher type is valid ('filesystem' or 'gmail')

### Issue: Data appears missing after rollback

**Solution**:
- Check vault path is correct
- Verify folders exist (they should, rollback doesn't delete them)
- Check file permissions

---

## Rollback Checklist

- [ ] Stop all PM2 processes
- [ ] Verify processes stopped
- [ ] Disable MCP server configuration (optional)
- [ ] Start Bronze tier entry point
- [ ] Verify Bronze tier operation
- [ ] Preserve audit logs (optional archive)
- [ ] Document rollback reason (for future reference)

---

## Summary

**Rollback is safe and reversible**:
- ✅ No data loss
- ✅ All files preserved
- ✅ Can re-enable Silver tier anytime
- ✅ Bronze tier works independently
- ✅ Audit logs preserved (read-only)

**Rollback Time**: < 5 minutes  
**Data Risk**: None (all data preserved)

---

**Documentation Completed**: 2026-01-09

