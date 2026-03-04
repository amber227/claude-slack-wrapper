#!/usr/bin/env python3
import os
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

print("Available channels:")
result = client.conversations_list(types=['public_channel'])
for c in result['channels']:
    print(f"  - {c['name']} ({c['id']})")
