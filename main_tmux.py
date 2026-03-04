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

                # Handle attached files (images)
                files = msg.get('files', [])
                image_paths = []
                if files:
                    slack_images_dir = work_dir / 'slack_images'
                    slack_images_dir.mkdir(exist_ok=True)

                    for file in files:
                        if file.get('mimetype', '').startswith('image/'):
                            # Download the image
                            file_url = file.get('url_private_download') or file.get('url_private')
                            file_name = file.get('name', f"image_{file['id']}")
                            local_path = slack_images_dir / file_name

                            try:
                                import requests
                                headers = {'Authorization': f'Bearer {os.environ["SLACK_BOT_TOKEN"]}'}
                                response = requests.get(file_url, headers=headers)
                                response.raise_for_status()
                                local_path.write_bytes(response.content)
                                image_paths.append(str(local_path))
                                print(f"Downloaded image: {file_name}")
                            except Exception as e:
                                print(f"Failed to download {file_name}: {e}")

                # Build full message with image references
                full_message = text
                if image_paths:
                    if full_message:
                        full_message += "\n\n"
                    full_message += "Attached images:\n" + "\n".join(image_paths)

                print(f"Slack -> Claude: {full_message}")

                # Send to Claude via tmux
                # Use -l to send text literally, then send C-m separately to submit
                subprocess.run([
                    'tmux', 'send-keys', '-t', session_name, '-l', full_message
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
