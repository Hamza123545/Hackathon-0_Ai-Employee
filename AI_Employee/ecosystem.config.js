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
      script: './watchers/gmail_watcher.py',
      interpreter: 'python',
      cwd: './AI_Employee',

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
        PYTHONUNBUFFERED: '1'
      },

      // Logging
      error_file: './Logs/gmail-watcher-err.log',
      out_file: './Logs/gmail-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Cron restart every 12 hours for cleanup
      cron_restart: '0 */12 * * *'
    },

    {
      name: 'whatsapp-watcher',
      script: './watchers/whatsapp_watcher.py',
      interpreter: 'python',
      cwd: './AI_Employee',

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
        PYTHONUNBUFFERED: '1'
      },

      // Logging
      error_file: './Logs/whatsapp-watcher-err.log',
      out_file: './Logs/whatsapp-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Cron restart every 12 hours
      cron_restart: '0 */12 * * *'
    },

    {
      name: 'linkedin-watcher',
      script: './watchers/linkedin_watcher.py',
      interpreter: 'python',
      cwd: './AI_Employee',

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
        PYTHONUNBUFFERED: '1'
      },

      // Logging
      error_file: './Logs/linkedin-watcher-err.log',
      out_file: './Logs/linkedin-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Cron restart every 12 hours
      cron_restart: '0 */12 * * *'
    },

    // ============================================
    // APPROVAL ORCHESTRATOR (HITL workflow)
    // ============================================
    {
      name: 'approval-orchestrator',
      script: './orchestrator.py',
      interpreter: 'python',
      cwd: './AI_Employee',

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
        PYTHONUNBUFFERED: '1'
      },

      // Logging
      error_file: './Logs/orchestrator-err.log',
      out_file: './Logs/orchestrator-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Cron restart every 12 hours for cleanup
      cron_restart: '0 */12 * * *'
    }
  ]
};
