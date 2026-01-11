# Backup and Recovery Guide

This guide covers how to backup and recover your Silver Tier Personal AI Employee system.

---

## What to Backup

### Critical Files (Required for Recovery)

1. **Configuration Files**:
   - `Company_Handbook.md` - All rules and configuration
   - `.env` - Environment variables (credentials, API keys)
   - `ecosystem.config.js` - PM2 configuration

2. **Session Files**:
   - `whatsapp_session.json` - WhatsApp Web session (if using WhatsApp watcher)
   - LinkedIn OAuth tokens (stored in `.env` as `LINKEDIN_ACCESS_TOKEN`)

3. **Audit Logs**:
   - `/Logs/YYYY-MM-DD.json` - Daily audit log files
   - `/Logs/screenshots/` - Browser automation screenshots

4. **Vault Structure**:
   - `/Plans/` - Action plans
   - `/Done/` - Completed actions
   - `/Pending_Approval/` - Pending approvals (if any)
   - `/Approved/` - Approved actions awaiting execution (if any)

### Optional Files (Nice to Have)

- `/Needs_Action/` - Action items (can be regenerated)
- `Dashboard.md` - Dashboard (can be regenerated)
- PM2 process list (can be recreated)

---

## Backup Procedures

### Method 1: Complete Vault Backup

**Backup entire vault directory**:

```bash
# Create backup directory
mkdir -p ~/backups/ai-employee

# Backup entire vault
cp -r AI_Employee ~/backups/ai-employee/vault-$(date +%Y%m%d)

# Backup .env file separately (if outside vault)
cp .env ~/backups/ai-employee/env-$(date +%Y%m%d)
```

**Restore**:
```bash
# Restore vault
cp -r ~/backups/ai-employee/vault-YYYYMMDD AI_Employee

# Restore .env
cp ~/backups/ai-employee/env-YYYYMMDD .env
```

---

### Method 2: Selective Backup

**Backup only critical files**:

```bash
# Create backup directory
mkdir -p ~/backups/ai-employee/$(date +%Y%m%d)

# Backup configuration
cp AI_Employee/Company_Handbook.md ~/backups/ai-employee/$(date +%Y%m%d)/
cp AI_Employee/ecosystem.config.js ~/backups/ai-employee/$(date +%Y%m%d)/
cp .env ~/backups/ai-employee/$(date +%Y%m%d)/

# Backup session files
cp AI_Employee/whatsapp_session.json ~/backups/ai-employee/$(date +%Y%m%d)/ 2>/dev/null || true

# Backup audit logs
cp -r AI_Employee/Logs ~/backups/ai-employee/$(date +%Y%m%d)/

# Backup vault structure
cp -r AI_Employee/Plans ~/backups/ai-employee/$(date +%Y%m%d)/
cp -r AI_Employee/Done ~/backups/ai-employee/$(date +%Y%m%d)/
```

---

### Method 3: Automated Backup Script

**Create backup script** (`backup_ai_employee.sh`):

```bash
#!/bin/bash
BACKUP_DIR=~/backups/ai-employee/$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup critical files
cp AI_Employee/Company_Handbook.md $BACKUP_DIR/
cp AI_Employee/ecosystem.config.js $BACKUP_DIR/
cp .env $BACKUP_DIR/ 2>/dev/null || true

# Backup session files
[ -f AI_Employee/whatsapp_session.json ] && cp AI_Employee/whatsapp_session.json $BACKUP_DIR/

# Backup audit logs (last 30 days)
find AI_Employee/Logs -name "*.json" -mtime -30 -exec cp {} $BACKUP_DIR/Logs/ \;

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup created: $BACKUP_DIR.tar.gz"
```

**Schedule daily backup** (add to crontab):
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup_ai_employee.sh
```

---

## Recovery Procedures

### Recover from PM2 Crash

**Scenario**: PM2 processes crashed or system rebooted

**Recovery Steps**:

1. **Check PM2 Status**:
   ```bash
   pm2 status
   ```

2. **Restore Process List** (if you ran `pm2 save`):
   ```bash
   pm2 resurrect
   ```

3. **Or Restart Manually**:
   ```bash
   cd AI_Employee
   pm2 start ecosystem.config.js
   ```

4. **Verify All Processes Online**:
   ```bash
   pm2 status
   # Should show all watchers and orchestrator as "online"
   ```

5. **Check Logs for Errors**:
   ```bash
   pm2 logs
   ```

---

### Recover from Data Loss

**Scenario**: Vault files deleted or corrupted

**Recovery Steps**:

1. **Stop All Processes**:
   ```bash
   pm2 stop all
   ```

2. **Restore from Backup**:
   ```bash
   # Restore vault
   cp -r ~/backups/ai-employee/vault-YYYYMMDD/* AI_Employee/

   # Restore .env
   cp ~/backups/ai-employee/env-YYYYMMDD .env
   ```

3. **Verify Vault Structure**:
   ```bash
   # Check critical folders exist
   ls -la AI_Employee/{Pending_Approval,Approved,Rejected,Logs,Plans,Done}
   ```

4. **Restart Processes**:
   ```bash
   pm2 start ecosystem.config.js
   ```

5. **Verify System Health**:
   - Check Dashboard.md
   - Verify watchers are detecting items
   - Check audit logs are being created

---

### Recover from Session Expiration

**Scenario**: WhatsApp session expired or LinkedIn token expired

**Recovery Steps**:

#### WhatsApp Session Recovery:

1. **Delete Expired Session**:
   ```bash
   rm AI_Employee/whatsapp_session.json
   ```

2. **Re-initialize Session**:
   ```bash
   cd AI_Employee
   python run_watcher.py whatsapp
   # Scan QR code with WhatsApp on phone
   ```

3. **Restart Watcher**:
   ```bash
   pm2 restart whatsapp-watcher
   ```

#### LinkedIn Token Recovery:

1. **Get New OAuth Token**:
   - Go to LinkedIn Developer Portal: https://www.linkedin.com/developers/apps
   - Navigate to your app → Auth tab
   - Generate new access token

2. **Update .env File**:
   ```bash
   # Edit .env file
   LINKEDIN_ACCESS_TOKEN=new_token_here
   ```

3. **Restart LinkedIn Watcher**:
   ```bash
   pm2 restart linkedin-watcher
   ```

4. **Verify Token**:
   - Check LinkedIn MCP health in Dashboard
   - Should show ✅ available status

---

### Migrate to New Machine

**Scenario**: Moving system to new computer

**Migration Steps**:

1. **On Old Machine - Export**:
   ```bash
   # Create migration package
   mkdir -p ~/ai-employee-migration
   
   # Export configuration
   cp AI_Employee/Company_Handbook.md ~/ai-employee-migration/
   cp AI_Employee/ecosystem.config.js ~/ai-employee-migration/
   cp .env ~/ai-employee-migration/
   
   # Export session files
   cp AI_Employee/whatsapp_session.json ~/ai-employee-migration/ 2>/dev/null || true
   
   # Export audit logs
   cp -r AI_Employee/Logs ~/ai-employee-migration/
   
   # Export PM2 process list
   pm2 save
   cp ~/.pm2/dump.pm2 ~/ai-employee-migration/ 2>/dev/null || true
   
   # Compress
   tar -czf ~/ai-employee-migration.tar.gz ~/ai-employee-migration
   ```

2. **Transfer to New Machine**:
   - Copy `ai-employee-migration.tar.gz` to new machine
   - Extract: `tar -xzf ai-employee-migration.tar.gz`

3. **On New Machine - Setup**:
   ```bash
   # Install prerequisites (Node.js, Python, PM2)
   # Follow quickstart.md Phase 1-4
   
   # Restore configuration
   cp ~/ai-employee-migration/Company_Handbook.md AI_Employee/
   cp ~/ai-employee-migration/ecosystem.config.js AI_Employee/
   cp ~/ai-employee-migration/.env .
   
   # Restore session files
   cp ~/ai-employee-migration/whatsapp_session.json AI_Employee/ 2>/dev/null || true
   
   # Restore audit logs
   cp -r ~/ai-employee-migration/Logs AI_Employee/
   
   # Update paths in ecosystem.config.js (if vault path changed)
   # Edit ecosystem.config.js and update VAULT_PATH
   
   # Restore PM2 process list (optional)
   cp ~/ai-employee-migration/dump.pm2 ~/.pm2/ 2>/dev/null || true
   pm2 resurrect
   ```

4. **Reconfigure MCP Servers**:
   - Verify SMTP credentials in `.env`
   - Verify LinkedIn OAuth token in `.env`
   - Test MCP server health: Check Dashboard

5. **Verify System**:
   ```bash
   pm2 status
   # All watchers should be online
   
   # Check Dashboard
   # Open Dashboard.md in Obsidian
   ```

---

## Backup Best Practices

1. **Regular Backups**: Schedule daily backups (use cron/Task Scheduler)
2. **Multiple Locations**: Store backups in multiple locations (local + cloud)
3. **Encrypt Sensitive Data**: Encrypt `.env` and session files before cloud backup
4. **Test Restores**: Periodically test restore procedures
5. **Version Control**: Use git for `Company_Handbook.md` and code (exclude `.env`)
6. **Retention Policy**: Keep backups for at least 90 days (match audit log retention)

---

## Recovery Checklist

After recovery, verify:

- [ ] All PM2 processes online: `pm2 status`
- [ ] Watchers detecting items: Check `/Needs_Action/` for new files
- [ ] MCP servers healthy: Check Dashboard → MCP Server Health
- [ ] Audit logs being created: Check `/Logs/YYYY-MM-DD.json`
- [ ] Dashboard updating: Check `Dashboard.md` last_updated timestamp
- [ ] Approval workflow working: Create test approval, verify execution
- [ ] Session files valid: WhatsApp/LinkedIn sessions working

---

**For more details**: See `specs/002-silver-tier-ai-employee/quickstart.md` → Troubleshooting section

