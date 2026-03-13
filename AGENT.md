# Agent Documentation

## Architecture
`agent.py` is a CLI that takes a question, sends it to an LLM, and returns a JSON answer.

## LLM Provider
- Provider: Qwen Code API (self-hosted via qwen-code-oai-proxy)
- Model: qwen3-coder-plus
- Config: `.env.agent.secret`

## How to Run
```bash
uv run agent.py "Your question here"
```

## Output Format
```json
{"answer": "...", "tool_calls": []}
```

## Configuration
Set in `.env.agent.secret`:
- `LLM_API_KEY` — API key for the Qwen proxy
- `LLM_API_BASE` — Base URL of the Qwen API
- `LLM_MODEL` — Model name
