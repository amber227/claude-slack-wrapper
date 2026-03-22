# Agent Guidelines

This document contains guidelines for AI agents (like Claude Code) working on this project.

## Project Overview

This is a wrapper that enables bidirectional interaction with agentic terminal tools (Claude Code, Codex, etc.) through Slack. The goal is to allow starting, monitoring, and interacting with these tools from Slack channels.

## Development Guidelines

### Slack Channel Usage

Only interact with the Slack channel specified in `SLACK_CHANNEL` in the `.env` file to avoid sending messages to the wrong channel.

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
