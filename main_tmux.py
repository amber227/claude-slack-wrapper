#!/usr/bin/env python3
import os
import subprocess
import time
from pathlib import Path
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

# Setup
repo_dir = Path(__file__).parent.absolute()
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
response_file = repo_dir / 'claude_response.txt'
session_name = "claude-wrapper"

# Get channel ID
channel_str = os.environ["SLACK_CHANNEL"]
init_msg = client.chat_postMessage(channel=channel_str, text="🤖 Claude Code wrapper started (tmux)")
channel = init_msg['channel']

print(f"Using channel: {channel}")

# Create tmux session with Claude Code
subprocess.run(['tmux', 'kill-session', '-t', session_name], capture_output=True)
subprocess.run([
    'tmux', 'new-session', '-d', '-s', session_name,
    '-c', str(repo_dir),
    'claude', 'code'
])

print(f"Claude Code started in tmux session '{session_name}'")
time.sleep(3)  # Let Claude initialize

# Track latest message timestamp
latest_ts = init_msg['ts']

# Main loop
while True:
    try:
        # Check for new Slack messages
        result = client.conversations_history(channel=channel, oldest=latest_ts, limit=10)
        messages = result['messages']

        for msg in reversed(messages):
            if msg['ts'] > latest_ts:
                # Skip bot's own messages
                if msg.get('bot_id'):
                    latest_ts = msg['ts']
                    continue

                text = msg.get('text', '')
                print(f"Slack -> Claude: {text}")

                # Send to Claude via tmux
                # Use -l to send text literally, then send C-m separately to submit
                subprocess.run([
                    'tmux', 'send-keys', '-t', session_name, '-l', text
                ])
                subprocess.run([
                    'tmux', 'send-keys', '-t', session_name, 'C-m'
                ])
                latest_ts = msg['ts']

        # Check for Claude response
        if response_file.exists():
            response = response_file.read_text()
            response_file.unlink()

            print(f"Claude -> Slack: {response[:100]}...")

            # Post to Slack
            client.chat_postMessage(channel=channel, text=response)

        time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
        subprocess.run(['tmux', 'kill-session', '-t', session_name])
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
