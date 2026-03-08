#!/usr/bin/env python3
import os
from slack_sdk import WebClient
from dotenv import load_dotenv
import time

load_dotenv()

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
channel_str = os.environ["SLACK_CHANNEL"]

# Confirmation prompt
print(f"This will delete ALL bot messages from channel: {channel_str}")
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

# Filter for bot messages
bot_messages = [msg for msg in messages if msg.get('bot_id')]

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
