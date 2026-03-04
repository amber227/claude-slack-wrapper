#!/usr/bin/env python3
import json
import sys
import os
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

    # Read the transcript (JSONL format - one JSON object per line)
    last_assistant_message = ""
    with transcript_path.open('r') as tf:
        for line in tf:
            entry = json.loads(line)
            if entry.get('type') == 'assistant' or entry.get('role') == 'assistant':
                # Get the text from content blocks (nested under 'message' field)
                message_data = entry.get('message', entry)
                for block in message_data.get('content', []):
                    if block.get('type') == 'text':
                        last_assistant_message = block.get('text', '')

    message = last_assistant_message

    with debug_file.open('a') as f:
        f.write(f"Message length: {len(message)}\n")
        f.write(f"Message preview: {message[:100]}\n")

    # Write to a file that the wrapper will read (in the script's directory)
    response_file = Path(__file__).parent / 'claude_response.txt'
    response_file.write_text(message)

    with debug_file.open('a') as f:
        f.write(f"Wrote response to: {response_file}\n")
        f.write(f"SUCCESS\n")

except Exception as e:
    with debug_file.open('a') as f:
        f.write(f"ERROR: {e}\n")
        import traceback
        f.write(traceback.format_exc())
