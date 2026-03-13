# Plan: The Documentation Agent

## Tools
- `read_file(path)` — reads file contents, blocks `../` traversal
- `list_files(path)` — lists directory entries, blocks `../` traversal

## Agentic Loop
1. Send question + tool schemas to LLM
2. If response has tool_calls → execute tools, append results as `tool` messages, repeat
3. If response has text (no tool_calls) → output final JSON
4. Stop after 10 tool calls max

## System Prompt
Tell LLM to use list_files to discover wiki files, then read_file to find the answer, and always include source as file#section.
