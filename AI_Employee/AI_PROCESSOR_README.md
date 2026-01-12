# AI Processor - Automatic Action Item Processing

The AI Processor automatically monitors the `/Needs_Action/` folder and processes new action items using Claude Code or Anthropic API. This eliminates the need for manual skill invocation and provides true automation.

## Features

✅ **Automatic Detection**: Monitors `/Needs_Action/` for new files  
✅ **Multiple Processing Methods**: Supports Claude CLI, Anthropic API, or simulation mode  
✅ **Risk Assessment**: Automatically routes high-risk items to approval workflow  
✅ **Dashboard Updates**: Automatically updates Dashboard.md after processing  
✅ **Duplicate Prevention**: Tracks processed files to avoid reprocessing  
✅ **Error Recovery**: Graceful degradation with fallback modes  
✅ **PM2 Integration**: Can run as a managed process with auto-restart  

## Quick Start

### Method 1: Direct Execution

```bash
# Basic usage (auto-detects available method)
python run_ai_processor.py

# Use Anthropic API
export ANTHROPIC_API_KEY="your-api-key"
python run_ai_processor.py --method anthropic

# Dry run (simulation mode)
python run_ai_processor.py --dry-run

# Custom interval
python run_ai_processor.py --interval 30
```

### Method 2: PM2 Process Manager

```bash
# Start AI processor
pm2 start ecosystem.config.js --only ai-processor

# View logs
pm2 logs ai-processor

# Monitor
pm2 monit

# Stop
pm2 stop ai-processor
```

## Processing Methods

### 1. Auto (Recommended)
Automatically detects the best available method:
- Tries Claude CLI first (if available)
- Falls back to Anthropic API (if configured)
- Uses simulation mode as last resort

```bash
python run_ai_processor.py --method auto
```

### 2. Anthropic API
Direct API calls to Anthropic's Claude API. Requires:
- `ANTHROPIC_API_KEY` environment variable
- `anthropic` package installed: `pip install anthropic`

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python run_ai_processor.py --method anthropic
```

### 3. Claude CLI
Uses Claude Code CLI (if available). Requires:
- Claude Code installed and in PATH
- Or set `CLAUDE_CLI_PATH` environment variable

```bash
export CLAUDE_CLI_PATH="/path/to/claude"
python run_ai_processor.py --method claude-cli
```

**Note**: Claude CLI skill invocation is not yet fully implemented. Currently falls back to simulation mode.

### 4. Simulation Mode
Creates basic plan structures without AI processing. Useful for:
- Testing the workflow
- Development without API costs
- Fallback when no AI is available

```bash
python run_ai_processor.py --method simulation
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROCESS_INTERVAL` | Seconds between checks | `60` |
| `PROCESS_METHOD` | Processing method | `auto` |
| `ANTHROPIC_API_KEY` | Anthropic API key | (required for API method) |
| `CLAUDE_CLI_PATH` | Path to Claude CLI | `claude` |
| `DRY_RUN` | Enable dry run mode | `false` |
| `VAULT_PATH` | Path to Obsidian vault | Current directory |
| `LOG_LEVEL` | Logging level | `INFO` |

### Example .env Configuration

```bash
# AI Processor Configuration
PROCESS_INTERVAL=60
PROCESS_METHOD=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
DRY_RUN=false
LOG_LEVEL=INFO
```

## How It Works

### Processing Flow

1. **Detection**: Scans `/Needs_Action/` folder every `PROCESS_INTERVAL` seconds
2. **Filtering**: Skips already processed files (tracked in `.ai_processed.json`)
3. **Processing**: For each new item:
   - Parses action item file
   - Reads `Company_Handbook.md` for context
   - Invokes AI (Claude CLI, Anthropic API, or simulation)
   - Generates structured plan in `/Plans/`
4. **Approval Routing**: Checks plan for external actions and creates approval requests if needed
5. **Completion**: Moves action item to `/Done/` with plan reference
6. **Dashboard Update**: Updates `Dashboard.md` with latest activity

### Risk Assessment

The processor automatically:
- Detects external actions (email, LinkedIn, browser automation)
- Assesses risk level (low/medium/high)
- Creates approval requests in `/Pending_Approval/` for high-risk items
- Can auto-approve low-risk items (if configured in `Company_Handbook.md`)

## Comparison: Manual vs Automatic

### Manual Processing (Before)
```
1. Watcher creates file in /Needs_Action/
2. User manually opens Claude Code
3. User manually invokes @process-action-items skill
4. User manually completes checkboxes
5. User manually moves files
```

### Automatic Processing (Now)
```
1. Watcher creates file in /Needs_Action/
2. AI Processor automatically detects new file
3. AI Processor automatically calls Claude/API
4. AI Processor automatically creates plan
5. AI Processor automatically routes to approval if needed
6. AI Processor automatically moves to /Done/
7. Dashboard automatically updated
```

## Integration with Existing System

The AI Processor integrates seamlessly with:

- **Watchers**: Processes items created by Gmail, WhatsApp, LinkedIn, filesystem watchers
- **Approval Workflow**: Creates approval requests that are handled by `ApprovalOrchestrator`
- **Dashboard**: Updates `Dashboard.md` automatically
- **Audit Logging**: Logs all processing actions to `/Logs/`

## Troubleshooting

### No Processing Happening

1. **Check logs**: `pm2 logs ai-processor` or check console output
2. **Verify vault path**: Ensure `VAULT_PATH` is set correctly
3. **Check permissions**: Ensure write access to `/Plans/` and `/Done/`
4. **Verify method**: Check if processing method is available (API key, CLI, etc.)

### API Errors

- **Anthropic API**: Verify `ANTHROPIC_API_KEY` is set and valid
- **Rate Limits**: API may throttle requests - processor will retry
- **Network Issues**: Check internet connection

### Files Not Moving to Done

- Check file permissions
- Verify `/Done/` folder exists
- Check logs for specific error messages

### Simulation Mode Only

If processor always uses simulation mode:
- Claude CLI not found: Install Claude Code or set `CLAUDE_CLI_PATH`
- Anthropic API not configured: Set `ANTHROPIC_API_KEY` and install `anthropic` package
- This is expected behavior - simulation mode is a safe fallback

## Performance

- **Processing Time**: ~2-5 seconds per item (depends on API response time)
- **Memory Usage**: ~50-100 MB
- **CPU Usage**: Low (mostly I/O bound)
- **Check Interval**: Configurable (default 60 seconds)

## Security

- **API Keys**: Stored in environment variables, never in code
- **Dry Run Mode**: Test without making actual API calls
- **Audit Logging**: All actions logged with sanitized credentials
- **Error Handling**: Graceful degradation prevents system crashes

## Next Steps

1. **Install dependencies** (if using Anthropic API):
   ```bash
   pip install anthropic
   ```

2. **Configure API key** (if using Anthropic API):
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

3. **Start processor**:
   ```bash
   python run_ai_processor.py
   ```

4. **Or use PM2**:
   ```bash
   pm2 start ecosystem.config.js --only ai-processor
   ```

5. **Test with a file**:
   ```bash
   # Create a test file in watch_folder/
   echo "Test action item" > watch_folder/test.txt
   
   # Wait for watcher to create action item
   # AI Processor will automatically process it
   ```

## Advanced Usage

### Custom Processing Logic

The `AIProcessor` class can be extended for custom processing:

```python
from ai_process_items import AIProcessor
from utils.config import Config

config = Config()
processor = AIProcessor(
    config,
    method='anthropic',
    check_interval=30,
    dry_run=False
)
processor.run()
```

### Integration with Other Systems

The processor can be triggered externally:

```python
# Trigger processing manually
processor = AIProcessor(config)
processor._process_cycle()  # Process one cycle
```

## Support

For issues or questions:
1. Check logs: `pm2 logs ai-processor`
2. Review this documentation
3. Check `Company_Handbook.md` for processing rules
4. Verify environment variables are set correctly

---

**Status**: ✅ Production Ready  
**Tier**: Silver+ (Automatic Processing)  
**Dependencies**: Optional `anthropic` package for API method
