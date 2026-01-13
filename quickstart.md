# Gold Tier AI Employee - Quick Start & Verification Guide

**Feature**: Gold Tier Personal AI Employee - Autonomous Processing with Cross-Domain Integration
**Version**: 1.0.0
**Last Updated**: 2026-01-13

---

## Prerequisites Verification

Run the prerequisite verification script:

```bash
python scripts/verify_gold_prerequisites.py
```

**Expected Output**: All checks should pass (✓)
- ✓ Python 3.10+ installed
- ✓ Node.js and npm installed
- ✓ Git repository initialized
- ✓ All required directories exist
- ✓ PM2 available globally

---

## Phase 1: Environment Setup

### 1.1 Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Verify**:
```bash
python -c "import xero_python, facebook, tweepy, watchdog, schedule, anthropic; print('✅ All Gold tier dependencies installed')"
```

### 1.2 Install PM2 Process Manager

```bash
npm install pm2@latest -g
```

**Verify**:
```bash
pm2 --version
```

Expected: `6.0.14` or higher

### 1.3 Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**Required Variables**:

#### Autonomous Processing
- `AI_PROCESSOR_ENABLED=true`
- `PROCESSING_INTERVAL=30`
- `AUTO_PROCESS_PERSONAL=true`
- `AUTO_PROCESS_BUSINESS=true`

#### Xero Accounting (if using)
- `XERO_CLIENT_ID=your_xero_client_id`
- `XERO_CLIENT_SECRET=your_xero_client_secret`
- `XERO_TENANT_ID=your_xero_tenant_id`

#### Facebook/Instagram (if using)
- `FACEBOOK_APP_ID=your_facebook_app_id`
- `FACEBOOK_APP_SECRET=your_facebook_app_secret`
- `FACEBOOK_PAGE_ID=your_facebook_page_id`
- `INSTAGRAM_ACCOUNT_ID=your_instagram_account_id` (optional)

#### Twitter (if using)
- `TWITTER_CLIENT_ID=your_twitter_client_id`
- `TWITTER_CLIENT_SECRET=your_twitter_client_secret` (optional)

#### Claude API
- `CLAUDE_API_KEY=your_anthropic_api_key`

#### Weekly Audit Scheduling
- `WEEKLY_AUDIT_DAY=1` (1=Monday)
- `WEEKLY_AUDIT_HOUR=9` (9 AM)
- `CEO_BRIEFING_HOUR=10` (10 AM)

### 1.4 Verify Vault Folder Structure

```bash
ls -la AI_Employee/
```

**Expected Folders**:
- ✓ `Needs_Action/` - New action items detected by watchers
- ✓ `Pending_Approval/` - Actions awaiting human approval
- ✓ `Approved/` - Actions approved by human
- ✓ `Done/` - Completed actions
- ✓ `Plans/` - Generated execution plans
- ✓ `Logs/` - Audit logs and processor logs
- ✓ `Business/` - Gold tier business domain folder
- ✓ `Accounting/` - Gold tier accounting data
- ✓ `Briefings/` - Gold tier CEO briefings and audits
- ✓ `System/` - Gold tier system status and MCP health

---

## Phase 2: MCP Server Authentication

### 2.1 Xero Authentication (Optional)

```bash
cd AI_Employee
python mcp_servers/xero_mcp_auth.py
```

**Steps**:
1. Script opens browser for OAuth authorization
2. Login to Xero and approve permissions
3. Script saves tokens to OS credential manager

**Test Connection**:
```bash
python mcp_servers/xero_mcp_test_connection.py
```

Expected: `✅ Xero connection test PASSED`

### 2.2 Facebook/Instagram Authentication (Optional)

```bash
python mcp_servers/facebook_mcp_auth.py
```

**Steps**:
1. Script opens browser for Facebook OAuth
2. Login and approve permissions
3. Select Facebook Page to manage
4. Script saves page token to OS credential manager

**Test Connections**:
```bash
python mcp_servers/facebook_mcp_test_connection.py
python mcp_servers/instagram_mcp_test_connection.py
```

Expected: `✅ Facebook connection test PASSED` and `✅ Instagram connection test PASSED`

### 2.3 Twitter Authentication (Optional)

```bash
python mcp_servers/twitter_mcp_auth.py
```

**Steps**:
1. Script opens browser for Twitter OAuth 2.0 PKCE
2. Login and authorize application
3. Script saves access/refresh tokens to OS credential manager

**Test Connection**:
```bash
python mcp_servers/twitter_mcp_test_connection.py
```

Expected: `✅ Twitter connection test PASSED`

---

## Phase 3: Start Gold Tier Daemons

### 3.1 Start All Processes with PM2

```bash
pm2 start ecosystem.config.js
```

**Expected Output**:
```
┌─────┬──────────────────────┬─────────────┬─────────┬─────────┬──────────┐
│ id  │ name                 │ mode        │ ↺       │ status  │ cpu      │
├─────┼──────────────────────┼─────────────┼─────────┼─────────┼──────────┤
│ 0   │ ai-processor         │ fork        │ 0       │ online  │ 0%       │
│ 1   │ weekly-audit         │ fork        │ 0       │ online  │ 0%       │
│ 2   │ mcp-health-checker   │ fork        │ 0       │ online  │ 0%       │
└─────┴──────────────────────┴─────────────┴─────────┴─────────┴──────────┘
```

### 3.2 View Process Logs

```bash
pm2 logs
```

**Expected**: No errors, daemons should be monitoring folders and performing health checks

### 3.3 Monitor Process Status

```bash
pm2 monit
```

**Real-time monitoring**: CPU, memory, logs for all processes

### 3.4 Save Process List (Auto-restart on Boot)

```bash
pm2 save
pm2 startup
```

Follow instructions to enable auto-start on system boot.

---

## Phase 4: Verification Testing

### 4.1 User Story 1: Autonomous Processing Test

**Objective**: Verify AI Processor automatically detects and processes action items

**Steps**:
1. Create a test action item:
```bash
cat > AI_Employee/Needs_Action/test-action.md << 'EOF'
---
priority: normal
source: manual_test
---

# Test Action Item

Please analyze this test action and create a plan.
This is a simple test to verify autonomous processing.
EOF
```

2. Wait 30 seconds and check logs:
```bash
pm2 logs ai-processor --lines 20
```

3. Verify plan created:
```bash
ls -la AI_Employee/Plans/
```

**Expected**: Plan file created with analysis and execution steps

**Success Criteria**: ✅ Action detected within 30 seconds, plan created automatically

### 4.2 User Story 2: Xero Integration Test (Optional)

**Objective**: Verify Xero expense creation with approval workflow

**Prerequisites**: Xero authentication completed (Phase 2.1)

**Steps**:
1. Create expense action item:
```bash
cat > AI_Employee/Needs_Action/expense-test.md << 'EOF'
---
priority: high
source: manual_test
domain: business
---

# Create Xero Expense

Create an expense entry in Xero:
- Amount: $50.00
- Category: Office Supplies
- Description: Test expense for verification
- Date: Today
EOF
```

2. Wait for AI Processor to create approval request
3. Check pending approvals:
```bash
ls -la AI_Employee/Pending_Approval/
```

4. Approve by moving to Approved folder:
```bash
mv AI_Employee/Pending_Approval/expense-*.json AI_Employee/Approved/
```

5. Wait for execution and check logs:
```bash
tail -f AI_Employee/Logs/$(date +%Y-%m-%d).json
```

**Expected**: Expense created in Xero, logged to audit trail

**Success Criteria**: ✅ End-to-end workflow with HITL approval, zero manual intervention

### 4.3 User Story 3: Social Media Post Test (Optional)

**Objective**: Verify cross-platform social media posting

**Prerequisites**: Facebook/Instagram/Twitter authentication completed (Phase 2.2, 2.3)

**Steps**:
1. Create social media post action:
```bash
cat > AI_Employee/Needs_Action/social-post-test.md << 'EOF'
---
priority: normal
source: manual_test
domain: business
---

# Post Business Update

Post the following message to Facebook, Instagram, and Twitter:

"Testing our automated social media posting system! 🚀 #Automation #AI"
EOF
```

2. Wait for approval request
3. Approve the post
4. Verify posts on each platform
5. Check engagement metrics:
```bash
cat AI_Employee/Business/Social_Media/facebook/*.json | tail -20
```

**Success Criteria**: ✅ Post published to all platforms, engagement metrics tracked

### 4.4 User Story 4: Weekly Audit Test

**Objective**: Verify weekly audit and CEO briefing generation

**Steps**:
1. Trigger audit manually:
```bash
cd AI_Employee
python schedulers/run_weekly_audit.py
```

2. Wait for completion (30-60 seconds)
3. Check audit report:
```bash
cat AI_Employee/Accounting/Audits/$(date +%Y-%m-%d)-audit-report.json | jq .
```

4. Check CEO briefing:
```bash
cat AI_Employee/Briefings/$(date +%Y-%m-%d)-ceo-briefing.md
```

**Expected**:
- Audit report with financial data, social media metrics, action item summary
- CEO briefing with 3-5 AI-generated insights and recommendations

**Success Criteria**: ✅ Comprehensive report with data from all sources, AI insights generated

### 4.5 User Story 5: Cross-Domain Workflow Test

**Objective**: Verify domain classification and routing

**Steps**:
1. Create cross-domain action:
```bash
cat > AI_Employee/Needs_Action/cross-domain-test.md << 'EOF'
---
priority: high
source: manual_test
---

# Business Expense from Personal Email

I paid $75 for printer ink for the home office. Please log this as a business expense in Xero and send me a confirmation email.
EOF
```

2. Verify classification in logs:
```bash
pm2 logs ai-processor --lines 30 | grep domain
```

3. Check Dashboard.md for cross-domain metrics:
```bash
cat AI_Employee/Dashboard.md | grep -A 10 "Cross-Domain"
```

**Expected**: Action classified as business domain, routed correctly, tracked in dashboard

**Success Criteria**: ✅ Correct domain identification, unified tracking

### 4.6 User Story 6: Error Recovery Test

**Objective**: Verify graceful degradation and retry logic

**Steps**:
1. Disconnect from internet or disable one MCP server
2. Create action requiring that MCP server
3. Verify error handling:
```bash
tail -f AI_Employee/Logs/processor_errors.json
```

4. Verify system continues operating:
```bash
pm2 list
```

5. Check MCP health status:
```bash
cat AI_Employee/System/MCP_Status/*.json | jq .
```

6. Reconnect internet/re-enable MCP server
7. Verify automatic retry and recovery

**Expected**: Errors logged, request cached, retry with exponential backoff, successful execution after recovery

**Success Criteria**: ✅ Zero data loss, graceful degradation, automatic recovery

---

## Phase 5: Dashboard Verification

### 5.1 View Real-Time Dashboard

Open `AI_Employee/Dashboard.md` in Obsidian or text editor.

**Expected Sections**:

1. **System Overview**
   - AI Processor status (uptime, last check)
   - Pending actions count
   - Pending approvals count

2. **Personal Domain Metrics**
   - Personal emails processed
   - WhatsApp messages handled
   - Personal tasks completed

3. **Business Domain Metrics**
   - Xero transactions synced
   - Social media posts published
   - Business tasks completed

4. **Cross-Domain KPIs**
   - Total automation rate
   - Unified response time
   - Cross-domain workflows executed

5. **MCP Server Health**
   - Xero: ✅ Healthy / ⚠️ Degraded / ❌ Failed
   - Facebook: Status with last successful call time
   - Instagram: Status
   - Twitter: Status

6. **Recent Activity**
   - Last 10 actions processed with timestamps

**Success Criteria**: ✅ Dashboard updates every 60 seconds, shows real-time system health

---

## Phase 6: Performance Validation

### 6.1 Processing Latency Test

**Objective**: Verify 95% of actions processed within 60 seconds

```bash
cd AI_Employee
python tests/test_gold_tier_performance.py
```

**Expected**: Performance test passes, 95%+ under 60s threshold

### 6.2 Concurrent Processing Test

**Objective**: Verify handling of 10+ simultaneous action items

1. Create 10 test actions:
```bash
for i in {1..10}; do
  cat > AI_Employee/Needs_Action/test-$i.md << EOF
---
priority: normal
source: test
---
# Test Action $i
Process this test action.
EOF
done
```

2. Monitor processing:
```bash
pm2 logs ai-processor
```

3. Verify all processed:
```bash
ls AI_Employee/Plans/ | wc -l
```

**Expected**: All 10 actions processed, plans created

**Success Criteria**: ✅ Priority queue working, parallel processing where possible

### 6.3 Backward Compatibility Test

**Objective**: Verify Bronze and Silver tier still work

```bash
python tests/test_gold_tier_backward_compatibility.py
```

**Expected**: All backward compatibility tests pass

---

## Phase 7: Integration Tests

### 7.1 Run Full Integration Test Suite

```bash
cd AI_Employee
python -m pytest tests/test_gold_tier_integration.py -v
```

**Expected**: All 27 test scenarios pass

### 7.2 Validate Success Criteria

Review the success criteria validation document:

```bash
cat tests/validate_success_criteria.md
```

**Verify All 14 Success Criteria**:
- ✅ SC-001: 95% under 60s processing
- ✅ SC-002: 80% end-to-end completion
- ✅ SC-003: Weekly audit on-time delivery
- ✅ SC-004: CEO briefing with 3+ insights
- ✅ SC-005: Xero 99% sync success
- ✅ SC-006: Social media 95% success
- ✅ SC-007: 90% cross-domain accuracy
- ✅ SC-008: 99% AI Processor uptime
- ✅ SC-009: Zero data loss
- ✅ SC-010: Dashboard 60s updates
- ✅ SC-011: 70% manual reduction
- ✅ SC-012: 100% HITL compliance
- ✅ SC-013: 100% audit logging
- ✅ SC-014: Backward compatibility

---

## Troubleshooting

### Issue: AI Processor not detecting files

**Symptoms**: Files remain in `/Needs_Action/` for > 30 seconds

**Diagnosis**:
```bash
pm2 logs ai-processor --lines 50
```

**Solutions**:
1. Verify `AI_PROCESSOR_ENABLED=true` in `.env`
2. Check file system permissions on vault folders
3. Restart AI Processor: `pm2 restart ai-processor`

### Issue: MCP server authentication failed

**Symptoms**: `❌ AUTH_ERROR` in logs

**Diagnosis**:
```bash
python AI_Employee/mcp_servers/<platform>_mcp_test_connection.py
```

**Solutions**:
1. Re-run authentication: `python mcp_servers/<platform>_mcp_auth.py`
2. Verify credentials in `.env`
3. Check token expiration in OS credential manager

### Issue: Weekly audit not generating

**Symptoms**: No audit report on Monday morning

**Diagnosis**:
```bash
pm2 logs weekly-audit --lines 100
```

**Solutions**:
1. Verify PM2 cron schedule: `pm2 show weekly-audit`
2. Manually trigger: `python AI_Employee/schedulers/run_weekly_audit.py`
3. Check Claude API key validity: `echo $CLAUDE_API_KEY`

### Issue: PM2 processes crash frequently

**Symptoms**: `restart` counter > 5

**Diagnosis**:
```bash
pm2 logs --err
cat AI_Employee/Logs/processor_errors.json | tail -20
```

**Solutions**:
1. Check Python dependencies: `pip install -r requirements.txt --upgrade`
2. Verify environment variables: `python -c "from utils.config import Config; c = Config(); print(c)"`
3. Check memory usage: `pm2 monit` (may need to increase `max_memory_restart`)

### Issue: Dashboard not updating

**Symptoms**: `Last Updated` timestamp stale

**Diagnosis**:
```bash
pm2 logs ai-processor | grep Dashboard
```

**Solutions**:
1. Verify Dashboard.md file permissions (must be writable)
2. Check for file locking issues
3. Restart AI Processor: `pm2 restart ai-processor`

---

## Production Deployment Checklist

- [ ] All prerequisites verified (`scripts/verify_gold_prerequisites.py` passes)
- [ ] All Python dependencies installed (`requirements.txt`)
- [ ] PM2 installed globally and configured
- [ ] Environment variables configured in `.env`
- [ ] All MCP servers authenticated and tested
- [ ] PM2 daemons started and healthy (`pm2 list` shows all online)
- [ ] PM2 saved and startup configured (`pm2 save && pm2 startup`)
- [ ] User Story 1 test passed (autonomous processing)
- [ ] User Story 2 test passed (Xero integration) - if applicable
- [ ] User Story 3 test passed (social media) - if applicable
- [ ] User Story 4 test passed (weekly audit) - if applicable
- [ ] User Story 5 test passed (cross-domain) - if applicable
- [ ] User Story 6 test passed (error recovery)
- [ ] Dashboard updates every 60 seconds
- [ ] Integration tests passed (`test_gold_tier_integration.py`)
- [ ] Performance tests passed (`test_gold_tier_performance.py`)
- [ ] Backward compatibility verified (`test_gold_tier_backward_compatibility.py`)

---

## Next Steps

Once verification is complete:

1. **Monitor System**: Use `pm2 monit` and Dashboard.md to track system health
2. **Review Logs**: Check `AI_Employee/Logs/` for audit trail and errors
3. **Weekly Review**: Read CEO briefings every Monday at 10 AM
4. **Iterate**: Adjust `Company_Handbook.md` rules based on classification accuracy
5. **Scale**: Add more watchers (Gmail, WhatsApp, etc.) as needed

---

## Support & Documentation

- **Specification**: `specs/003-gold-tier-ai-employee/spec.md`
- **Data Model**: `specs/003-gold-tier-ai-employee/data-model.md`
- **Task List**: `specs/003-gold-tier-ai-employee/tasks.md`
- **Plan**: `specs/003-gold-tier-ai-employee/plan.md`
- **Validation**: `AI_Employee/tests/validate_success_criteria.md`

For issues, review logs:
- AI Processor: `AI_Employee/Logs/ai-processor-out.log`
- Weekly Audit: `AI_Employee/Logs/weekly-audit-out.log`
- MCP Health: `AI_Employee/Logs/mcp-health-out.log`
- Errors: `AI_Employee/Logs/processor_errors.json`

---

**Status**: Ready for Production ✅
**Last Verified**: 2026-01-13
