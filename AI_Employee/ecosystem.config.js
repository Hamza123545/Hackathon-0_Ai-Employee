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
      script: './run_watcher.py',
      args: 'whatsapp',
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
        WATCHER_TYPE: 'whatsapp',
        CHECK_INTERVAL: '300',  // 5 minutes
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: process.env.VAULT_PATH || require('path').resolve(__dirname)
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
    }
  ]
};
