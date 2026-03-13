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
