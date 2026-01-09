---
type: approval_request
action: [send_email|post_linkedin|make_payment|browser_action]
plan_id: /Plans/[plan_filename].md
source_action_item: /Needs_Action/[original_filename].md
created: [ISO_TIMESTAMP]
expires: [ISO_TIMESTAMP - 24 hours from created]
status: pending
priority: [high|medium|low]
mcp_server: [email|linkedin|browser|payment]
mcp_tool: [tool_name]
---

# Approval Request: [Action Type]

## Action Summary

**Type**: [Detailed action description]
**Reason**: [Why this action is needed - reference original action item]
**Target**: [Recipient/account/page/destination]
**Priority**: [high|medium|low]

## Action Details

### Parameters

[Action-specific parameters]
- **Parameter 1**: [value]
- **Parameter 2**: [value]
- **Parameter 3**: [value]

### Content Preview

[Preview of email body, post content, payment details, etc.]

### Related Context

- **Original Action Item**: [[source_action_item]]
- **Plan**: [[plan_id]]
- **Created**: [timestamp]
- **Requester**: Claude Code (via @process-action-items skill)

## Approval Instructions

### To Approve This Action

1. Review the action details above
2. Verify parameters are correct
3. Move this file to `/Approved/` folder
4. The `@execute-approved-actions` skill will automatically execute it

### To Reject This Action

1. Review why this action should not be executed
2. Move this file to `/Rejected/` folder
3. Optionally add rejection reason below

## Rejection Reason

*(Leave blank if approving)*

Reason for rejection: [Add reason here]

---

## Execution Status

*(Updated automatically by @execute-approved-actions skill)*

- Status: [pending|executing|executed|failed|rejected]
- Executed at: [ISO_TIMESTAMP]
- MCP Server: [server_name]
- MCP Tool: [tool_name]
- Execution ID: [id_from_mcp]
- Error: [error_message if failed]

## Audit Trail

- Created: [timestamp] by @process-action-items
- Approved: [timestamp] by [human]
- Executed: [timestamp] by @execute-approved-actions
- Result: [success|failure|rejected]

