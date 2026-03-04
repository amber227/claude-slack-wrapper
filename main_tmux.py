#!/usr/bin/env python3
import os
import subprocess
import time
import argparse
from pathlib import Path
from slack_sdk import WebClient
from dotenv import load_dotenv

# Parse arguments
parser = argparse.ArgumentParser(description='Claude Code Slack wrapper')
parser.add_argument('-d', '--directory', type=str, help='Directory to run Claude Code in (defaults to wrapper repo)')
parser.add_argument('--unsafe', action='store_true', help='Skip permissions prompts (enables --dangerously-skip-permissions)')
args = parser.parse_args()

load_dotenv()

# Setup
repo_dir = Path(__file__).parent.absolute()
work_dir = Path(args.directory).absolute() if args.directory else repo_dir
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
response_file = repo_dir / 'claude_response.txt'
session_name = "claude-wrapper"

# Get channel ID
channel_str = os.environ["SLACK_CHANNEL"]
init_msg = client.chat_postMessage(channel=channel_str, text="🤖 Claude Code wrapper started (tmux)")
channel = init_msg['channel']

print(f"Using channel: {channel}")
print(f"Working directory: {work_dir}")

# Create tmux session with Claude Code
subprocess.run(['tmux', 'kill-session', '-t', session_name], capture_output=True)

# Build claude command
claude_cmd = ['claude', 'code']
if args.unsafe:
    claude_cmd.append('--dangerously-skip-permissions')
    print("⚠️  Running in unsafe mode (permissions disabled)")

subprocess.run([
    'tmux', 'new-session', '-d', '-s', session_name,
    '-c', str(work_dir)
] + claude_cmd)

print(f"Claude Code started in tmux session '{session_name}'")
time.sleep(3)  # Let Claude initialize

# Track latest message timestamp
latest_ts = init_msg['ts']

# Image monitoring setup
image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
watch_dirs = [work_dir / d.strip() for d in os.environ.get('IMAGE_WATCH_DIRS', '.').split(',')]
seen_images = set()

# Initialize with existing images
for watch_dir in watch_dirs:
    if watch_dir.exists():
        for img in watch_dir.glob('*'):
            if img.suffix.lower() in image_extensions and img.is_file():
                seen_images.add(img)

print(f"Monitoring for images in: {watch_dirs}")

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

        # Check for new images
        for watch_dir in watch_dirs:
            if not watch_dir.exists():
                continue
            for img in watch_dir.glob('*'):
                if img.suffix.lower() in image_extensions and img.is_file() and img not in seen_images:
                    print(f"New image detected: {img.name}")
                    try:
                        client.files_upload_v2(
                            channel=channel,
                            file=str(img),
                            title=img.name
                        )
                        print(f"Uploaded image to Slack: {img.name}")
                        seen_images.add(img)
                    except Exception as e:
                        print(f"Failed to upload {img.name}: {e}")

        time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
        subprocess.run(['tmux', 'kill-session', '-t', session_name])
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
