#!/usr/bin/env python3
import os
import subprocess
import time
import argparse
import json
import requests
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
init_msg = client.chat_postMessage(channel=channel_str, text="============ *Start of New Session* ============")
channel = init_msg['channel']

print(f"Using channel: {channel}")
print(f"Working directory: {work_dir}")

# Setup hook configuration in work directory
if work_dir != repo_dir:
    work_claude_dir = work_dir / '.claude'
    work_claude_dir.mkdir(exist_ok=True)

    hook_config = {
        "hooks": {
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"uv run {repo_dir}/stop_hook.py"
                        }
                    ]
                }
            ]
        }
    }

    (work_claude_dir / 'settings.json').write_text(json.dumps(hook_config, indent=2))
    print(f"Created hook configuration in {work_claude_dir}")

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

# Send initial context about Slack wrapper interface
context_file = repo_dir / 'SLACK_CONTEXT.md'
if context_file.exists():
    context_message = context_file.read_text()
    subprocess.run([
        'tmux', 'send-keys', '-t', session_name, '-l', context_message
    ])
    time.sleep(0.1)
    subprocess.run([
        'tmux', 'send-keys', '-t', session_name, 'C-m'
    ])
    print("Sent Slack wrapper context to Claude Code")
    time.sleep(2)  # Wait for Claude to process initial message

# Track latest message timestamp
latest_ts = init_msg['ts']

# Track last processed response to avoid duplicates
last_response_id = None

# File outbox monitoring setup
extensions_str = os.environ.get('FILE_OUTBOX_EXTENSIONS', '.png,.jpg,.jpeg,.gif,.bmp,.webp')
if extensions_str.strip() == '*':
    file_extensions = None  # Match all files
else:
    file_extensions = {ext.strip().lower() for ext in extensions_str.split(',')}

watch_dirs = [work_dir / d.strip() for d in os.environ.get('FILE_OUTBOX', '.').split(',')]
seen_files = {}  # Maps file path to mtime

# Initialize with existing files
for watch_dir in watch_dirs:
    if watch_dir.exists():
        for file in watch_dir.glob('*'):
            if file.is_file():
                if file_extensions is None or file.suffix.lower() in file_extensions:
                    seen_files[file] = file.stat().st_mtime

print(f"Monitoring for files in: {watch_dirs}")
if file_extensions:
    print(f"Watching extensions: {file_extensions}")
else:
    print(f"Watching all file types")

# Command handler
def handle_command(command_text):
    """Handle wrapper commands that start with backslash."""
    command = command_text.strip()

    if command.startswith('\\ignore'):
        # Drop the message silently
        print(f"Command: Ignoring message: {command}")
        return True
    elif command == '\\restart':
        print("Command: Restarting Claude Code instance...")
        client.chat_postMessage(channel=channel, text="Restarting Claude Code instance...")

        # Kill current tmux session
        subprocess.run(['tmux', 'kill-session', '-t', session_name], capture_output=True)
        time.sleep(1)

        # Restart Claude Code in new tmux session
        subprocess.run([
            'tmux', 'new-session', '-d', '-s', session_name,
            '-c', str(work_dir)
        ] + claude_cmd)

        print(f"Claude Code restarted in tmux session '{session_name}'")
        time.sleep(3)  # Let Claude initialize

        # Resend initial context
        if context_file.exists():
            context_message = context_file.read_text()
            subprocess.run([
                'tmux', 'send-keys', '-t', session_name, '-l', context_message
            ])
            time.sleep(0.1)
            subprocess.run([
                'tmux', 'send-keys', '-t', session_name, 'C-m'
            ])
            print("Resent Slack wrapper context to Claude Code")
            time.sleep(2)

        client.chat_postMessage(channel=channel, text="Claude Code instance restarted successfully.")
        return True
    else:
        client.chat_postMessage(channel=channel, text=f"Unknown command: {command}")
        return False

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
                print(f"Debug - Raw text from Slack: '{text}'")

                # Check if this is a command (starts with backslash)
                if text.strip().startswith('\\'):
                    handle_command(text.strip())
                    latest_ts = msg['ts']
                    continue

                # Handle attached files
                files = msg.get('files', [])
                file_paths = []
                print(f"Debug - Found {len(files)} attached files")
                if files:
                    file_inbox_dir = work_dir / os.environ.get('FILE_INBOX', 'file_inbox')
                    file_inbox_dir.mkdir(exist_ok=True)

                    for file in files:
                        # Download all file types
                        file_url = file.get('url_private_download') or file.get('url_private')
                        file_name = file.get('name', f"file_{file['id']}")
                        local_path = file_inbox_dir / file_name

                        try:
                            headers = {'Authorization': f'Bearer {os.environ["SLACK_BOT_TOKEN"]}'}
                            response = requests.get(file_url, headers=headers)
                            response.raise_for_status()
                            local_path.write_bytes(response.content)
                            file_paths.append(str(local_path))
                            print(f"Downloaded file: {file_name}")
                        except Exception as e:
                            print(f"Failed to download {file_name}: {e}")

                # Build full message with file references
                full_message = text
                if file_paths:
                    if full_message:
                        full_message += "\n\n"
                    full_message += "Attached files:\n" + "\n".join(file_paths)

                print(f"Slack -> Claude: {full_message}")

                # Send to Claude via tmux
                # Use -l to send text literally, then send C-m separately to submit
                subprocess.run([
                    'tmux', 'send-keys', '-t', session_name, '-l', full_message
                ])
                # Delay to ensure text is fully inserted before submitting
                # Use longer delay if message has files attached (more complex)
                delay = 5 if file_paths else 2
                time.sleep(delay)
                subprocess.run([
                    'tmux', 'send-keys', '-t', session_name, 'C-m'
                ])
                latest_ts = msg['ts']

        # Check for Claude response
        if response_file.exists():
            content = response_file.read_text()

            # Parse response ID from first line
            lines = content.split('\n', 1)
            if len(lines) >= 2:
                response_id = lines[0]
                response = lines[1]
            else:
                # Fallback for old format without ID
                response_id = None
                response = content

            # Skip if we've already processed this response
            if response_id and response_id == last_response_id:
                print(f"Skipping duplicate response ID: {response_id}")
                response_file.unlink()  # Still delete the file
            else:
                response_file.unlink()
                last_response_id = response_id

                print(f"Claude -> Slack (ID: {response_id}): {response[:100]}...")

                # Post to Slack
                client.chat_postMessage(channel=channel, text=response)

        # Check for new or modified files in outbox
        for watch_dir in watch_dirs:
            if not watch_dir.exists():
                continue
            for file in watch_dir.glob('*'):
                if not file.is_file():
                    continue
                # Check if file matches extensions filter
                if file_extensions is not None and file.suffix.lower() not in file_extensions:
                    continue

                # Check if file is new or modified
                current_mtime = file.stat().st_mtime
                if file in seen_files and seen_files[file] == current_mtime:
                    continue  # File unchanged

                is_new = file not in seen_files
                print(f"{'New' if is_new else 'Modified'} file detected: {file.name}")
                try:
                    client.files_upload_v2(
                        channel=channel,
                        file=str(file),
                        title=file.name
                    )
                    print(f"Uploaded file to Slack: {file.name}")
                    seen_files[file] = current_mtime
                except Exception as e:
                    print(f"Failed to upload {file.name}: {e}")

        time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
        subprocess.run(['tmux', 'kill-session', '-t', session_name])
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
