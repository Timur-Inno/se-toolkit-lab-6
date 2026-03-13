# Plan: Call an LLM from Code

## LLM Provider
- Provider: Qwen Code API (self-hosted on VM via qwen-code-oai-proxy)
- Model: qwen3-coder-plus
- Base URL: http://10.93.25.190:42005/v1
- API key stored in .env.agent.secret

## Structure
1. Load env vars from .env.agent.secret
2. Parse the question from CLI args
3. Send to LLM via OpenAI-compatible chat completions API
4. Parse response and print JSON with `answer` and `tool_calls` fields
5. All debug output goes to stderr
