#!/usr/bin/env python3
import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Debug: write to /tmp so we can always find it
debug_file = Path('/tmp/claude-hook-debug.log')

try:
    # Log hook invocation
    with debug_file.open('a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Hook fired: {datetime.now()}\n")
        f.write(f"Working directory: {os.getcwd()}\n")
        f.write(f"Script location: {Path(__file__).parent}\n")
        f.write(f"Args: {sys.argv}\n")

    # Read hook data from stdin
    hook_data = json.load(sys.stdin)

    # Get the transcript path and read the last assistant message
    transcript_path = Path(hook_data['transcript_path'])

    with debug_file.open('a') as f:
        f.write(f"Reading transcript from: {transcript_path}\n")
        f.write(f"Transcript size: {transcript_path.stat().st_size} bytes\n")

    # Small delay to ensure transcript is fully written to disk
    time.sleep(0.1)

    # Read the transcript (JSONL format - one JSON object per line)
    # We need to find the MOST RECENT assistant message
    assistant_messages = []
    with transcript_path.open('r') as tf:
        for line in tf:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue

            if entry.get('type') == 'assistant' or entry.get('role') == 'assistant':
                # Get the text from content blocks (nested under 'message' field)
                message_data = entry.get('message', entry)
                timestamp = entry.get('timestamp', '')
                for block in message_data.get('content', []):
                    if block.get('type') == 'text':
                        text = block.get('text', '')
                        if text:
                            assistant_messages.append({
                                'timestamp': timestamp,
                                'text': text
                            })

    # Get the most recent message
    last_assistant_message = ""
    if assistant_messages:
        last_assistant_message = assistant_messages[-1]['text']

    with debug_file.open('a') as f:
        f.write(f"Found {len(assistant_messages)} assistant messages in transcript\n")
        if assistant_messages:
            for i, msg in enumerate(assistant_messages[-3:]):  # Show last 3
                f.write(f"  Message {i}: {msg['text'][:50]}... (ts: {msg['timestamp']})\n")

    message = last_assistant_message

    # Get timestamp from hook data to use as unique ID
    response_id = hook_data.get('timestamp', str(time.time()))

    with debug_file.open('a') as f:
        f.write(f"Response ID: {response_id}\n")
        f.write(f"Message length: {len(message)}\n")
        f.write(f"Message preview: {message[:100]}\n")

    # Write to a file that the wrapper will read (in the script's directory)
    # Include response ID on first line to prevent duplicate processing
    response_file = Path(__file__).parent / 'claude_response.txt'
    response_file.write_text(f"{response_id}\n{message}")

    with debug_file.open('a') as f:
        f.write(f"Wrote response to: {response_file}\n")
        f.write(f"SUCCESS\n")

except Exception as e:
    with debug_file.open('a') as f:
        f.write(f"ERROR: {e}\n")
        import traceback
        f.write(traceback.format_exc())
