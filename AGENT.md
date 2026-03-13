# Agent Documentation

## Architecture
`agent.py` is a CLI that takes a question, runs an agentic loop with tools, and returns a JSON answer.

## LLM Provider
- Provider: Qwen Code API (self-hosted via qwen-code-oai-proxy)
- Model: qwen3-coder-plus
- Config: `.env.agent.secret`

## Tools
- `read_file(path)` — reads a file from the project. Blocks path traversal outside project root.
- `list_files(path)` — lists directory contents. Blocks path traversal outside project root.

## Agentic Loop
1. Send question + tool schemas to LLM
2. If LLM responds with tool_calls → execute tools, feed results back, repeat
3. If LLM responds with text → output final JSON and exit
4. Max 10 tool calls per run

## System Prompt
Instructs the LLM to use `list_files` to discover wiki files, then `read_file` to find the answer, and always return a `source` reference in `wiki/file.md#section` format.

## How to Run
```bash
cat > AGENT.md << 'EOF'
# Agent Documentation

## Architecture
`agent.py` is a CLI that takes a question, runs an agentic loop with tools, and returns a JSON answer.

## LLM Provider
- Provider: Qwen Code API (self-hosted via qwen-code-oai-proxy)
- Model: qwen3-coder-plus
- Config: `.env.agent.secret`

## Tools
- `read_file(path)` — reads a file from the project. Blocks path traversal outside project root.
- `list_files(path)` — lists directory contents. Blocks path traversal outside project root.

## Agentic Loop
1. Send question + tool schemas to LLM
2. If LLM responds with tool_calls → execute tools, feed results back, repeat
3. If LLM responds with text → output final JSON and exit
4. Max 10 tool calls per run

## System Prompt
Instructs the LLM to use `list_files` to discover wiki files, then `read_file` to find the answer, and always return a `source` reference in `wiki/file.md#section` format.

## How to Run
```bash
uv run agent.py "Your question here"
```

## Output Format
```json
{"answer": "...", "source": "wiki/file.md#section", "tool_calls": [...]}
```

## Configuration
Set in `.env.agent.secret`:
- `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL`
