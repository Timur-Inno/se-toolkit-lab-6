import sys
import json
import urllib.request
import urllib.error
import os
import re
from pathlib import Path
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).parent.resolve()

def load_env():
    env = {**dotenv_values(".env.agent.secret"), **dotenv_values(".env.docker.secret")}
    for k, v in os.environ.items():
        env[k] = v
    return env

def safe_path(path):
    p = (PROJECT_ROOT / path).resolve()
    if not str(p).startswith(str(PROJECT_ROOT)):
        return None, "Access denied"
    return p, None

def read_file(path):
    p, err = safe_path(path)
    if err: return err
    try: return p.read_text(encoding="utf-8")
    except Exception as e: return f"Error: {e}"

def list_files(path):
    p, err = safe_path(path)
    if err: return err
    try: return "\n".join(e.name for e in sorted(p.iterdir()))
    except Exception as e: return f"Error: {e}"

def query_api(env, method, path, body=None, no_auth=False):
    base_url = env.get("AGENT_API_BASE_URL", "http://localhost:42002")
    url = f"{base_url}{path}"
    data = body.encode() if body else None
    headers = {"Content-Type": "application/json"}
    if not no_auth:
        headers["Authorization"] = f"Bearer {env.get('LMS_API_KEY', '')}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status=resp.status; body=resp.read().decode()[:4000]; return json.dumps({"status_code": status, "body": body, "note": f"HTTP STATUS CODE IS {status}"})
    except urllib.error.HTTPError as e:
        status=e.code; body=e.read().decode()[:2000]; return json.dumps({"status_code": status, "body": body, "note": f"HTTP STATUS CODE IS {status}"})
    except Exception as e:
        return json.dumps({"status_code": 0, "body": str(e)})

TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read a file from the project repository. Use for source code, config files, and wiki documentation files.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files and directories at a given path in the project repository.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "query_api", "description": "Call the deployed backend API to get live data or observe real behavior: item counts (try /items/), scores, analytics, HTTP status codes, authentication errors. Always call the API directly — do not guess from source code.", "parameters": {"type": "object", "properties": {"method": {"type": "string"}, "path": {"type": "string"}, "body": {"type": "string"}}, "required": ["method", "path"]}}}
]

SYSTEM_PROMPT = """You are a system assistant for a software engineering LMS project.

Project layout:
- backend/app/  — Python backend source code (main.py or app.py is the entry point)
- wiki/         — project documentation markdown files

Tool usage rules:
- Questions about live data, HTTP status codes, API behavior: use query_api. IMPORTANT: for "what status code does X return without auth/authentication" — call query_api with no_auth=true to send the request without the Authorization header
- When an endpoint returns empty results or no error, try different parameter values (e.g. lab=lab-1, lab=lab-2) to find one that triggers a crash or real data
- Questions about ports or what port something runs on: FIRST read docker-compose.yml, THEN read .env.docker.secret to get the actual numeric values of APP_HOST_PORT, CADDY_HOST_PORT, APP_CONTAINER_PORT. Always report the concrete number from the file, not the variable name.
- Questions about source code, frameworks, imports, or implementation: use list_files("backend/app") first, then read_file on the relevant file
- Questions about HTTP request lifecycle or how requests flow through the system: read docker-compose.yml, Caddyfile, Dockerfile (in project root), and backend/app/main.py in that order
- Questions asking about a bug or error in the source code: call query_api first to get the error, then read_file on the relevant router. For /interactions/ errors you MUST call read_file on backend/app/routers/interactions.py AND read_file on backend/app/models/interaction.py — even if the error message already reveals the bug. For /analytics/ errors read backend/app/routers/analytics.py. When you find a field name mismatch (e.g. response model has "timestamp" but DB model has "created_at"), state the exact field names and the fix explicitly.
- Questions listing router modules or files and their purpose: use list_files on the routers directory, read each file briefly, then summarize each module name and its domain in plain text (do NOT dump raw code)
- Questions about documentation/wiki topics: use list_files("wiki"), then read_file on relevant file
- To explore directories: use list_files first, then read_file on specific files

IMPORTANT: Do NOT output intermediate reasoning text. Either call a tool OR give the final answer.
CRITICAL: When query_api returns a status_code, that IS the answer — report it exactly. Never contradict tool results.
Never output text like "Let me check..." or "I will now..." — just call the tool directly.

Always end your final answer with:
Source: <reference>

Where <reference> is wiki/filename.md#section, /api/path, or backend/app/file.py."""

def call_api(env, messages):
    payload = json.dumps({"model": env["LLM_API_MODEL"], "messages": messages, "tools": TOOLS, "tool_choice": "auto"}).encode()
    req = urllib.request.Request(f"{env['LLM_API_BASE_URL']}/chat/completions", data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {env['LLM_API_KEY']}", "X-Api-Key": env['LLM_API_KEY']})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

def extract_source(text):
    m = re.search(r'Source:\s*(\S+)', text)
    if m: return m.group(1)
    m = re.search(r'wiki/[\w\-/.]+\.md(?:#[\w\-]+)?', text)
    if m: return m.group(0)
    return ""

def looks_incomplete(text):
    REASONING = ["let me", "i will", "i need to", "i should", "i am going", "first, let", "now let", "let me try"]
    tl = text.strip().lower()
    if any(tl.startswith(r) for r in REASONING): return True
    text = text.strip()
    return text.endswith(':') or text.endswith('...') or len(text) < 30

def main():
    env = load_env()
    if len(sys.argv) < 2:
        print("Usage: agent.py <question>", file=sys.stderr); sys.exit(1)
    question = sys.argv[1]
    print(f"Question: {question}", file=sys.stderr)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    tool_calls_log = []
    answer = source = ""
    for _ in range(20):
        data = call_api(env, messages)
        msg = data["choices"][0]["message"]
        messages.append(msg)
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                fn = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])
                print(f"Tool: {fn}({args})", file=sys.stderr)
                if fn == "read_file": result = read_file(args["path"])
                elif fn == "list_files": result = list_files(args["path"])
                elif fn == "query_api":
                    # Auto no_auth if question mentions "without auth" or similar
                    auto_no_auth = args.get("no_auth", False)
                    if not auto_no_auth:
                        q_lower = question.lower()
                        if any(p in q_lower for p in ["without auth", "without sending", "no auth", "unauthenticated", "without a header", "without the header"]):
                            auto_no_auth = True
                    result = query_api(env, args["method"], args["path"], args.get("body"), auto_no_auth)
                else: result = "Unknown tool"
                tool_calls_log.append({"tool": fn, "args": args, "result": result[:500]})
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
        else:
            content = (msg.get("content") or "")
            if looks_incomplete(content):
                # Push it back and ask LLM to continue with tools
                messages.append({"role": "user", "content": "Continue — use tools to complete your answer."})
                continue
            answer = content
            source = extract_source(answer)
            break
    print(json.dumps({"answer": answer, "source": source, "tool_calls": tool_calls_log}))

if __name__ == "__main__":
    main()
