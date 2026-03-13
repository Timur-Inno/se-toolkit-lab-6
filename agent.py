import sys
import json
import urllib.request
from pathlib import Path
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).parent.resolve()

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

TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read a file from the project repository.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files and directories at a given path.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}
]

SYSTEM_PROMPT = """You are a documentation assistant. Use list_files to discover wiki files, then read_file to find the answer. Always include a source reference as wiki/filename.md#section."""

def call_api(env, messages):
    payload = json.dumps({"model": env["LLM_MODEL"], "messages": messages, "tools": TOOLS, "tool_choice": "auto"}).encode()
    req = urllib.request.Request(f"{env['LLM_API_BASE']}/chat/completions", data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {env['LLM_API_KEY']}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

def main():
    env = dotenv_values(".env.agent.secret")
    if len(sys.argv) < 2:
        print("Usage: agent.py <question>", file=sys.stderr); sys.exit(1)
    question = sys.argv[1]
    print(f"Question: {question}", file=sys.stderr)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    tool_calls_log = []
    answer = source = ""
    for _ in range(10):
        data = call_api(env, messages)
        msg = data["choices"][0]["message"]
        messages.append(msg)
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                fn = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])
                result = read_file(args["path"]) if fn == "read_file" else list_files(args["path"]) if fn == "list_files" else "Unknown tool"
                tool_calls_log.append({"tool": fn, "args": args, "result": result[:500]})
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
        else:
            answer = msg.get("content", "")
            import re
            m = re.search(r'wiki/[\w\-/.]+\.md(?:#[\w\-]+)?', answer)
            if m: source = m.group(0)
            break
    print(json.dumps({"answer": answer, "source": source, "tool_calls": tool_calls_log}))

if __name__ == "__main__":
    main()
