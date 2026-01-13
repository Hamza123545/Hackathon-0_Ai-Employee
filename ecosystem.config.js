/**
 * PM2 Ecosystem Configuration for Gold Tier AI Employee
 *
 * Manages three Gold Tier processes:
 * 1. ai-processor: Autonomous action item processor (30-second interval)
 * 2. weekly-audit: Weekly audit and CEO briefing generator (Monday 9 AM / 10 AM)
 * 3. mcp-health-checker: MCP server health monitoring (5-minute interval)
 */

module.exports = {
  apps: [
    {
      name: 'ai-processor',
      script: 'ai_process_items.py',
      interpreter: 'python',
      cwd: './',

      // Auto-restart configuration
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 10000, // 10 seconds

      // Resource limits
      max_memory_restart: '500M',

      // Logging
      error_file: './AI_Employee/Logs/ai-processor-error.log',
      out_file: './AI_Employee/Logs/ai-processor-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Environment
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },

      // Watch for changes (disable in production)
      watch: false,
      ignore_watch: ['node_modules', 'AI_Employee/Logs', 'AI_Employee/Needs_Action'],

      // Startup configuration
      exec_mode: 'fork',
      instances: 1,

      // Cron restart (optional - restart daily at 3 AM for fresh state)
      cron_restart: '0 3 * * *'
    },

    {
      name: 'weekly-audit',
      script: 'run_weekly_audit.py',
      interpreter: 'python',
      cwd: './',

      // Auto-restart configuration
      autorestart: true,
      max_restarts: 5,
      min_uptime: '5s',
      restart_delay: 10000,

      // Resource limits
      max_memory_restart: '1G',

      // Logging
      error_file: './AI_Employee/Logs/weekly-audit-error.log',
      out_file: './AI_Employee/Logs/weekly-audit-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Environment
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },

      // Cron-based execution (Monday 9:00 AM for audit, 10:00 AM for CEO briefing)
      cron_restart: '0 9 * * 1', // Monday 9 AM

      // Watch disabled
      watch: false,

      // Startup configuration
      exec_mode: 'fork',
      instances: 1
    },

    {
      name: 'mcp-health-checker',
      script: 'AI_Employee/scripts/check_mcp_health.py',
      interpreter: 'python',
      cwd: './',

      // Auto-restart configuration
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 10000,

      // Resource limits
      max_memory_restart: '200M',

      // Logging
      error_file: './AI_Employee/Logs/mcp-health-error.log',
      out_file: './AI_Employee/Logs/mcp-health-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Environment
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },

      // Watch disabled
      watch: false,

      // Startup configuration
      exec_mode: 'fork',
      instances: 1,

      // Cron restart (optional - restart daily for fresh state)
      cron_restart: '0 4 * * *' // Daily at 4 AM
    }
  ],

  /**
   * Deployment configuration (optional)
   *
   * Allows deploying to remote servers via PM2
   * Example: pm2 deploy ecosystem.config.js production setup
   */
  deploy: {
    production: {
      user: 'deploy',
      host: 'your-server.com',
      ref: 'origin/main',
      repo: 'git@github.com:your-repo/ai-employee.git',
      path: '/var/www/ai-employee',
      'post-deploy': 'pip install -r requirements.txt && pm2 reload ecosystem.config.js --env production',
      'pre-setup': 'apt-get install -y python3 python3-pip'
    }
  }
};

/**
 * PM2 Commands Cheat Sheet:
 *
 * Start all processes:
 *   pm2 start ecosystem.config.js
 *
 * Start specific process:
 *   pm2 start ecosystem.config.js --only ai-processor
 *
 * Stop all processes:
 *   pm2 stop ecosystem.config.js
 *
 * Restart all processes:
 *   pm2 restart ecosystem.config.js
 *
 * Delete all processes:
 *   pm2 delete ecosystem.config.js
 *
 * View logs:
 *   pm2 logs
 *   pm2 logs ai-processor
 *   pm2 logs --lines 100
 *
 * Monitor processes:
 *   pm2 monit
 *
 * List processes:
 *   pm2 list
 *
 * View process details:
 *   pm2 show ai-processor
 *
 * Save process list (for auto-restart on boot):
 *   pm2 save
 *
 * Setup auto-start on boot:
 *   pm2 startup
 *
 * Flush logs:
 *   pm2 flush
 *
 * Reload (zero-downtime restart):
 *   pm2 reload ecosystem.config.js
 */
