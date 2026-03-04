# Claude Code Slack Wrapper

A simple wrapper that allows bidirectional interaction with Claude Code through Slack.

## Setup

1. Install dependencies:
   ```bash
   uv add slack-sdk python-dotenv
   ```

2. Hook configuration is already set up in `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "matchers": [],
           "handlers": [
             {
               "command": "uv run stop_hook.py"
             }
           ]
         }
       ]
     }
   }
   ```

3. Run the wrapper:
   ```bash
   uv run main_tmux.py
   ```

## How it works

1. Wrapper spawns Claude Code as a subprocess
2. Polls Slack for new messages
3. Sends Slack messages to Claude Code's stdin
4. When Claude finishes responding, Stop hook writes response to a file
5. Wrapper reads the file and posts response to Slack
