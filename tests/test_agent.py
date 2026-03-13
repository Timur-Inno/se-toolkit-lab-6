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

def test_agent_uses_read_file_for_merge_conflict():
    result = subprocess.run(
        ["uv", "run", "agent.py", "How do you resolve a merge conflict?"],
        capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip())
    tools_used = [t["tool"] for t in data["tool_calls"]]
    assert "read_file" in tools_used
    assert "wiki/" in data.get("source", "")

def test_agent_uses_list_files_for_wiki():
    result = subprocess.run(
        ["uv", "run", "agent.py", "What files are in the wiki?"],
        capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip())
    tools_used = [t["tool"] for t in data["tool_calls"]]
    assert "list_files" in tools_used
