import subprocess
import json

def test_agent_output():
    result = subprocess.run(
        ["uv", "run", "agent.py", "What is 2+2?"],
        capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip())
    assert "answer" in data
    assert "tool_calls" in data

def test_framework_question_uses_read_file():
    result = subprocess.run(
        ["uv", "run", "agent.py", "What Python web framework does this project's backend use? Read the source code to find out."],
        capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip())
    tools_used = [t["tool"] for t in data["tool_calls"]]
    assert "read_file" in tools_used, f"Expected read_file in tool_calls, got: {tools_used}"

def test_item_count_uses_query_api():
    result = subprocess.run(
        ["uv", "run", "agent.py", "How many items are currently stored in the database? Query the running API to find out."],
        capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip())
    tools_used = [t["tool"] for t in data["tool_calls"]]
    assert "query_api" in tools_used, f"Expected query_api in tool_calls, got: {tools_used}"
