import sys
import json
import os
from pathlib import Path
from dotenv import dotenv_values

def main():
    env = dotenv_values(".env.agent.secret")
    api_key = env.get("LLM_API_KEY")
    api_base = env.get("LLM_API_BASE")
    model = env.get("LLM_MODEL", "qwen3-coder-plus")

    if len(sys.argv) < 2:
        print("Usage: agent.py <question>", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
    print(f"Sending question to LLM: {question}", file=sys.stderr)

    import urllib.request
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Answer concisely."},
            {"role": "user", "content": question}
        ]
    }).encode()

    req = urllib.request.Request(
        f"{api_base}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())

    answer = data["choices"][0]["message"]["content"]
    print(json.dumps({"answer": answer, "tool_calls": []}))

if __name__ == "__main__":
    main()
