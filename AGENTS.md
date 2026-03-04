# Agent Guidelines

This document contains guidelines for AI agents (like Claude Code) working on this project.

## Project Overview

This is a wrapper that enables bidirectional interaction with agentic terminal tools (Claude Code, Codex, etc.) through Slack. The goal is to allow starting, monitoring, and interacting with these tools from Slack channels.

## Development Guidelines

### ⚠️ CRITICAL: Slack Channel Restrictions ⚠️

**NEVER, UNDER ANY CIRCUMSTANCES, interact with ANY Slack channel except the one specified in `SLACK_CHANNEL` in the `.env` file.**

This means:
- **DO NOT** send messages to any other channel
- **DO NOT** read messages from any other channel
- **DO NOT** list, browse, or query other channels
- **DO NOT** use any channel ID or name that is not explicitly from the `SLACK_CHANNEL` environment variable
- **DO NOT** test, debug, or experiment in other channels

**There is ONLY ONE channel you are permitted to interact with: the one in `SLACK_CHANNEL`. Violating this restriction could cause serious disruption to the workspace.**

### Package Management
- Use `uv` for all Python package management
- Run Python scripts with `uv run`, e.g., `uv run main.py`
- Add dependencies with `uv add <package>`

### Simplicity First
- Keep solutions as simple as possible
- Never make code more complex or general than needed for the specific requirement
- Prefer terse, readable scripts over sprawling architectures
- Avoid over-engineering and premature abstraction
- Don't add features that weren't explicitly requested

### Code Style
- Prioritize readability over cleverness
- It's okay to skip production-level patterns (extensive error handling, logging frameworks, etc.) unless specifically needed
- Focus on features that work well enough to iterate quickly
- Direct, straightforward code is better than "proper" architecture

### Iteration Speed
- Ship working features fast
- Don't worry about edge cases unless they actually come up
- Refactor only when current code becomes a real problem
- Quick iteration > perfect code
