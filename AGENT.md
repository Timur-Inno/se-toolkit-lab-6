# Agent Documentation

## Architecture

`agent.py` is a CLI that takes a question, runs an agentic loop with tool calls, and returns a JSON answer with sources and tool call history.

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
{"answer": "...", "source": "wiki/file.md", "tool_calls": [{"tool": "...", "args": {}, "result": "..."}]}
```

## Configuration

| Variable | Purpose | Source |
|----------|---------|--------|
| `LLM_API_KEY` | LLM provider API key | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint URL | `.env.agent.secret` |
| `LLM_MODEL` | Model name | `.env.agent.secret` |
| `LMS_API_KEY` | Backend API key for query_api | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Backend base URL | optional, defaults to `http://localhost:42002` |

## Tools

### `read_file(path)`
Reads a file from the project. Used for source code inspection, config files, and wiki docs.

### `list_files(path)`
Lists directory contents. Used to discover files before reading them.

### `query_api(method, path, body?, no_auth?)`
Calls the deployed backend API, authenticated via `LMS_API_KEY` Bearer token. Set `no_auth=true` to omit the Authorization header (e.g. to test unauthenticated status codes). Returns `{"status_code": ..., "body": ...}`.

## Tool Selection Logic

- **Wiki/docs questions** → `list_files("wiki")` then `read_file`
- **Source code / framework questions** → `list_files("backend/app")` then `read_file`
- **Live data, counts, scores** → `query_api`
- **HTTP status codes / API behavior** → `query_api` (with `no_auth=true` for unauthenticated tests)
- **Bug diagnosis** → `query_api` to get the error, then `read_file` to find the buggy line

## Lessons Learned

1. **Tool descriptions drive behavior.** Vague descriptions like "use for source code" were not enough — the LLM needs the exact starting directory (`backend/app`) and the sequence of steps to follow.
2. **LLMs hallucinate over tool results.** The model ignored a `status_code: 401` response and answered 200. Adding "Never contradict tool results" to the system prompt fixed this.
3. **Auth must be controllable.** The `no_auth` parameter was essential — without it the agent could never simulate an unauthenticated request to observe the real status code.
4. **Empty results do not mean no bug.** For crash-diagnosis questions, the LLM needed explicit guidance to try multiple parameter values (e.g. `lab=lab-1`) to find one that triggers the error.
5. **Reasoning filtering helps.** Without filtering "Let me check..." style output via `looks_incomplete`, the agent would stop early and waste iterations.

## Final Eval Score

10/10 local questions passed.
