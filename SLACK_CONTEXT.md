# Slack Wrapper Context

You are being controlled through a Slack wrapper interface. Here are important details about this env

## Message Flow

- **User messages from Slack** are forwarded to you as prompts
- **Your responses** are automatically posted back to the Slack channel
- All communication is bidirectional through Slack

## File Handling

### Incoming Files (from Slack)
- Images and files attached to Slack messages are downloaded to the `file_inbox/` directory
- File paths are included in the message text you receive
- Use the Read tool to view these files

### Outgoing Files (to Slack)
- Files you create in the working directory root (`.`) are automatically uploaded to Slack
- Files appear in Slack shortly after creation

## Best Practices

- When asked to view an image from Slack, look for paths like `file_inbox/image_name.png`
- If you create visualizations or outputs, or if you are asked to "send" or "show" files such as source code files, copy them to `file_outbox` (with a commit hash appended to the filename if it doesn't have one already) for automatic sharing
- Your responses will be posted to Slack exactly as you write them - be clear and concise
