// PM2 Process Manager Configuration
// Silver Tier Personal AI Employee
//
// Usage:
//   pm2 start ecosystem.config.js        # Start all processes
//   pm2 start ecosystem.config.js --only gmail-watcher  # Start specific watcher
//   pm2 logs                             # View all logs
//   pm2 monit                            # Monitor processes
//   pm2 restart all                      # Restart all processes
//   pm2 stop all                         # Stop all processes
//   pm2 delete all                       # Remove all processes

module.exports = {
  apps: [
    // ============================================
    // WATCHERS (Multi-channel monitoring)
    // ============================================
    {
      name: 'gmail-watcher',
      script: './run_watcher.py',
      args: 'gmail',
      interpreter: 'python',
      cwd: './AI_Employee',
      exec_mode: 'fork',  // Python doesn't support cluster mode

      // Restart behavior
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,

      // Watch mode disabled (watchers poll internally)
      watch: false,

      // Environment variables
      env: {
        WATCHER_TYPE: 'gmail',
        CHECK_INTERVAL: '300',  // 5 minutes
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname)
      },

      // Logging
      error_file: './logs/gmail-watcher-err.log',
      out_file: './logs/gmail-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Memory management
      max_memory_restart: '500M',

      // Cron restart every 12 hours for cleanup
      cron_restart: '0 */12 * * *'
    },

    {
      name: 'whatsapp-watcher',
      script: 'python',
      args: '-u -m watchers.whatsapp_watcher',
      cwd: './AI_Employee',
      exec_mode: 'fork',

      // Restart behavior
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,

      // Watch mode disabled
      watch: false,

      // Environment variables
      env: {
        WATCHER_TYPE: 'whatsapp',
        CHECK_INTERVAL: '300',  // 5 minutes
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname),
        HEADLESS: process.env.HEADLESS || 'true'
      },

      // Logging
      error_file: './logs/whatsapp-watcher-err.log',
      out_file: './logs/whatsapp-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Playwright needs more memory
      max_memory_restart: '800M',

      // Cron restart every 12 hours
      cron_restart: '0 */12 * * *'
    },

    {
      name: 'linkedin-watcher',
      script: './run_watcher.py',
      args: 'linkedin',
      interpreter: 'python',
      cwd: './AI_Employee',
      exec_mode: 'fork',

      // Restart behavior
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,

      // Watch mode disabled
      watch: false,

      // Environment variables
      env: {
        WATCHER_TYPE: 'linkedin',
        CHECK_INTERVAL: '300',  // 5 minutes
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname),
        LINKEDIN_ACCESS_TOKEN: process.env.LINKEDIN_ACCESS_TOKEN || ''
      },

      // Logging
      error_file: './logs/linkedin-watcher-err.log',
      out_file: './logs/linkedin-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // API-based watcher uses less memory
      max_memory_restart: '300M',

      // Cron restart every 12 hours
      cron_restart: '0 */12 * * *'
    },

    // ============================================
    // AI PROCESSOR (Automatic action item processing)
    // ============================================
    {
      name: 'ai-processor',
      script: './ai_process_items.py',
      interpreter: 'python',
      cwd: './AI_Employee',
      exec_mode: 'fork',

      // Restart behavior
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,

      // Watch mode disabled (processor uses watchdog internally)
      watch: false,

      // Environment variables
      env: {
        AI_PROCESSOR_ENABLED: 'true',
        PROCESSING_INTERVAL: '30',  // 30 seconds (Gold Tier requirement)
        AUTO_PROCESS_PERSONAL: 'true',
        AUTO_PROCESS_BUSINESS: 'true',
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname, 'AI_Employee'),
        ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || ''
      },

      // Logging
      error_file: './logs/ai-processor-err.log',
      out_file: './logs/ai-processor-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Memory management
      max_memory_restart: '500M'
    },

    // ============================================
    // APPROVAL ORCHESTRATOR (HITL workflow)
    // ============================================
    {
      name: 'approval-orchestrator',
      script: './run_orchestrator.py',
      interpreter: 'python',
      cwd: './AI_Employee',
      exec_mode: 'fork',

      // Restart behavior
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,

      // Watch mode disabled (orchestrator polls /Approved folder)
      watch: false,

      // Environment variables
      env: {
        APPROVAL_CHECK_INTERVAL: '60',  // 1 minute
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname)
      },

      // Logging
      error_file: './logs/orchestrator-err.log',
      out_file: './logs/orchestrator-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Memory management
      max_memory_restart: '300M',

      // Cron restart every 12 hours for cleanup
      cron_restart: '0 */12 * * *'
    },

    // ============================================
    // WEEKLY AUDIT SCHEDULER (Gold Tier)
    // ============================================
    {
      name: 'weekly-audit',
      script: './schedulers/run_weekly_audit.py',
      args: '--phase audit',
      interpreter: 'python',
      cwd: './AI_Employee',
      exec_mode: 'fork',

      // Run every Monday at 9:00 AM
      cron_restart: '0 9 * * 1',

      // Restart behavior
      autorestart: false,  // Don't auto-restart after completion
      max_restarts: 1,
      min_uptime: '5s',

      // Environment variables
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname)
      },

      // Logging
      error_file: './logs/weekly-audit-err.log',
      out_file: './logs/weekly-audit-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Memory management
      max_memory_restart: '500M'
    },

    {
      name: 'weekly-ceo-briefing',
      script: './schedulers/run_weekly_audit.py',
      args: '--phase briefing',
      interpreter: 'python',
      cwd: './AI_Employee',
      exec_mode: 'fork',

      // Run every Monday at 10:00 AM (1 hour after audit)
      cron_restart: '0 10 * * 1',

      // Restart behavior
      autorestart: false,  // Don't auto-restart after completion
      max_restarts: 1,
      min_uptime: '5s',

      // Environment variables
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname)
      },

      // Logging
      error_file: './logs/weekly-briefing-err.log',
      out_file: './logs/weekly-briefing-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Memory management
      max_memory_restart: '500M'
    },

    // ============================================
    // AI PROCESSOR DAEMON (Gold Tier - Phase 8)
    // ============================================
    {
      name: 'ai-processor',
      script: './ai_process_items.py',
      interpreter: 'python',
      cwd: './AI_Employee',
      exec_mode: 'fork',

      // Auto-restart configuration (T089)
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 10000,

      // Environment variables
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        PROCESSING_INTERVAL: '30',  // 30 seconds
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname)
      },

      // Logging
      error_file: './logs/ai-processor-err.log',
      out_file: './logs/ai-processor-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Memory management
      max_memory_restart: '500M',

      // Watch disabled
      watch: false
    },

    // ============================================
    // MCP HEALTH CHECKER (Gold Tier - Phase 8)
    // ============================================
    {
      name: 'mcp-health-checker',
      script: './scripts/check_mcp_health.py',
      interpreter: 'python',
      cwd: './AI_Employee',
      exec_mode: 'fork',

      // Auto-restart configuration
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 10000,

      // Environment variables
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname)
      },

      // Logging
      error_file: './logs/mcp-health-err.log',
      out_file: './logs/mcp-health-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Memory management
      max_memory_restart: '200M',

      // Watch disabled
      watch: false
    },

    // ============================================
    // AUTONOMOUS AGENT (Platinum Tier - Zone Awareness)
    // ============================================
    {
      name: 'autonomous-agent',
      script: 'python',
      args: '-u autonomous_agent.py',
      cwd: './AI_Employee',
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      watch: false,
      env: {
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname),
        AGENT_MODE: process.env.AGENT_MODE || 'local',
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};
