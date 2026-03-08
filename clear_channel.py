#!/usr/bin/env python3
import os
import sys
from slack_sdk import WebClient
from dotenv import load_dotenv
import time

load_dotenv()

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
channel_str = os.environ["SLACK_CHANNEL"]

# Get number of messages to delete
if len(sys.argv) > 1:
    try:
        num_to_delete = int(sys.argv[1])
        print(f"Will delete the last {num_to_delete} bot messages from channel: {channel_str}")
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid number")
        exit(1)
else:
    num_to_delete = None
    print(f"This will delete ALL bot messages from channel: {channel_str}")

# Confirmation prompt
confirmation = input(f"Type the full channel name to confirm: ")

if confirmation != channel_str:
    print("Channel name mismatch. Aborting.")
    exit(1)

# Get channel ID by posting a temporary message
temp_msg = client.chat_postMessage(channel=channel_str, text="Clearing bot messages...")
channel = temp_msg['channel']

print(f"Fetching messages from channel {channel}...")

# Fetch all messages
messages = []
cursor = None
while True:
    result = client.conversations_history(channel=channel, cursor=cursor, limit=1000)
    messages.extend(result['messages'])
    cursor = result.get('response_metadata', {}).get('next_cursor')
    if not cursor:
        break

# Filter for bot messages (most recent first)
bot_messages = [msg for msg in messages if msg.get('bot_id')]

# Limit to N most recent if specified
if num_to_delete is not None:
    bot_messages = bot_messages[:num_to_delete]

print(f"Found {len(bot_messages)} bot messages to delete out of {len(messages)} total messages")

# Delete each bot message
deleted = 0
for msg in bot_messages:
    try:
        client.chat_delete(channel=channel, ts=msg['ts'])
        deleted += 1
        if deleted % 10 == 0:
            print(f"Deleted {deleted}/{len(bot_messages)} messages...")
        time.sleep(0.1)  # Rate limiting
    except Exception as e:
        print(f"Failed to delete message {msg['ts']}: {e}")

print(f"Done! Deleted {deleted} bot messages")
