bidirectional interaction with claude code through slack. supports file attachments both ways.

below are generated docs, if something is unclear/unreproducible lmk
-amber

## Setup

### Slack App OAuth Permissions

Your Slack app needs the following Bot Token Scopes:

**Required:**
- `chat:write` - Post messages
- `channels:history` - Read public channel messages
- `channels:read` - List public channels
- `groups:history` - Read private channel messages
- `files:write` - Upload images

**Optional (depending on usage):**
- `app_mentions:read` - Respond to @mentions
- `im:history`, `im:read`, `im:write` - Direct messages
- `reactions:write` - Add reactions to messages

Configure these at: https://api.slack.com/apps → Your App → OAuth & Permissions → Scopes

After adding scopes, reinstall the app to your workspace.

### Installation

1. Install dependencies:
   ```bash
   uv add slack-sdk python-dotenv
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Slack tokens and channel
   ```

3. Hook configuration is already set up in `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "uv run stop_hook.py"
             }
           ]
         }
       ]
     }
   }
   ```

4. Run the wrapper:
   ```bash
   uv run main_tmux.py
   ```

   To run Claude Code in a different directory:
   ```bash
   uv run main_tmux.py --directory /path/to/project
   # or short form:
   uv run main_tmux.py -d /path/to/project
   ```

   To skip permission prompts (unsafe mode):
   ```bash
   uv run main_tmux.py --unsafe
   ```
   ⚠️ **Warning:** This enables `--dangerously-skip-permissions` which allows Claude Code to execute operations without prompting. Use only in trusted environments.

## Features

### Bidirectional Slack ↔ Claude Code Communication

1. Wrapper spawns Claude Code in a tmux session
2. Polls Slack for new messages
3. Sends Slack messages to Claude Code
   - Text messages are forwarded directly
   - Images attached to messages are downloaded to `FILE_INBOX` directory (default: `file_inbox/`) and file paths are included in the prompt
4. When Claude finishes responding, Stop hook writes response to a file
5. Wrapper reads the file and posts response to Slack

### Automatic File Forwarding (Outbox)

The wrapper monitors specified directories for new files and automatically uploads them to Slack.

**Configuration** (in `.env`):
```bash
FILE_OUTBOX=.
FILE_OUTBOX_EXTENSIONS=.png,.jpg,.jpeg,.gif,.bmp,.webp
```

Set `FILE_OUTBOX` to comma-separated relative paths to monitor multiple directories:
```bash
FILE_OUTBOX=.,screenshots,outputs
```

Set `FILE_OUTBOX_EXTENSIONS` to specify which file types to watch:
```bash
FILE_OUTBOX_EXTENSIONS=.png,.jpg  # Only PNG and JPG
FILE_OUTBOX_EXTENSIONS=*          # All file types
```
