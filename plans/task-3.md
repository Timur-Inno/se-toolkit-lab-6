# Plan: The System Agent

## New Tool: query_api
- Parameters: method, path, body (optional)
- Auth: LMS_API_KEY from environment
- Base URL: AGENT_API_BASE_URL env var (default: http://localhost:42002)
- Returns: JSON string with status_code and body

## Environment Variables
- LLM_API_KEY, LLM_API_BASE, LLM_MODEL from .env.agent.secret
- LMS_API_KEY from .env.docker.secret
- AGENT_API_BASE_URL optional, defaults to http://localhost:42002

## System Prompt Update
- Use query_api for live data (item counts, scores, API status)
- Use read_file for source code inspection
- Use list_files + read_file for wiki/documentation questions

## Benchmark Strategy
Run uv run run_eval.py, fix failures one by one.

## Benchmark Results

Initial score: 2/10. Failures and fixes:
- Q3 (framework): system prompt didn't specify `backend/app` directory → added explicit path
- Q5 (item count): agent hit `/` instead of `/items/` → improved tool description  
- Q6 (status code): LLM hallucinated 200 despite tool returning 401 → added `no_auth` param + "Never contradict tool results" rule
- Q7/Q8 (bug diagnosis): agent skipped `read_file` → added rule requiring both `query_api` + `read_file` for bug questions
- Q8 (top-learners crash): agent tested empty labs → added guidance to try `lab=lab-1` style params

Final score: 10/10.
