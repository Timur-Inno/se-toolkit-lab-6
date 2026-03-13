import sys
import json
import os
import urllib.request
from pathlib import Path
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).parent.resolve()

def safe_path(path):
    p = (PROJECT_ROOT / path).resolve()
    if not str(p).startswith(str(PROJECT_ROOT)):
        return None, "Access denied: path outside project directory"
    return p, None

def read_file(path):
    p, err = safe_path(path)
    if err:
        return err
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error: {e}"

def list_files(path):
    p, err = safe_path(path)
    if err:
        return err
    try:
        return "\n".join(e.name for e in sorted(p.iterdir()))
    except Exception as e:
        return f"Error: {e}"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from project root"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative directory path from project root"}
                },
                "required": ["path"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a documentation assistant for a software engineering project.
To answer questions, use list_files to discover files in the wiki directory, then read_file to read relevant files.
Always include a source reference in the format: wiki/filename.md#section-anchor.
Be concise and accurate."""

def call_api(env, messages):
    payload = json.dumps({
        "model": env["LLM_MODEL"],
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto"
    }).encode()
    req = urllib.request.Request(
        f"{env['LLM_API_BASE']}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {env['LLM_API_KEY']}"
        }
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

def main():
    env = dotenv_values(".env.agent.secret")
    if len(sys.argv) < 2:
        print("Usage: agent.py <question>", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
    print(f"Question: {question}", file=sys.stderr)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]

    tool_calls_log = []
    answer = ""
    source = ""
    max_calls = 10
    call_count = 0

    while call_count < max_calls:
        data = call_api(env, messages)
        msg = data["choices"][0]["message"]
        messages.append(msg)

        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                fn = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])
                print(f"Tool call: {fn}({args})", file=sys.stderr)

                if fn == "read_file":
                    result = read_file(args["path"])
                elif fn == "list_files":
                    result = list_files(args["path"])
                else:
                    result = "Unknown tool"

                tool_calls_log.append({"tool": fn, "args": args, "result": result[:500]})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result
                })
                call_count += 1
        else:
            answer = msg.get("content", "")
            # Try to extract source from answer
            for line in answer.splitlines():
                if "wiki/" in line and ".md" in line:
                    import re
                    m = re.search(r'wiki/[\w\-/.]+\.md(?:#[\w\-]+)?', line)
                    if m:
                        source = m.group(0)
                        break
            break

    print(json.dumps({"answer": answer, "source": source, "tool_calls": tool_calls_log}))

if __name__ == "__main__":
    main()
