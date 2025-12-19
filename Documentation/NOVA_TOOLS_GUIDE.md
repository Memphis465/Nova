# 🔥 Nova with TOOLS - She Can Actually DO Shit Now

## What Changed

**BEFORE:** Nova was just text - could only chat  
**NOW:** Nova has **real capabilities** - she can:

- ✅ **Execute shell commands** (run scripts, check system status, etc.)
- ✅ **Manage files** (read, write, move, copy, delete)
- ✅ **Edit code** (append, replace, insert, analyze)
- ✅ **Search the web** (DuckDuckGo API)
- ✅ **Fetch webpages** (get content from URLs)

## Quick Start

```bash
cd ~/godman_ai
python3 nova_with_tools.py
```

## Example Commands You Can Now Give Nova

### File Operations
```
"Create a new file at ~/Desktop/test.txt with some content"
"Read what's in my ~/Documents/notes.md file"
"Move ~/Desktop/old_project to ~/Archives/"
"List all files in my Downloads folder"
```

### Shell Commands
```
"Check my disk space"
"Show me what's running on port 8000"
"Create a backup of my godman_ai folder"
"What Python version do I have?"
```

### Code Editing
```
"Add a new function to ~/godman_ai/tools/echo.py"
"Replace the API key in groq_nova_setup.sh with a placeholder"
"Analyze the code in ~/godman_ai/godman_chat.py"
```

### Web Search
```
"Search for the latest Python 3.14 features"
"Fetch the content from https://news.ycombinator.com"
"Look up how to deploy FastAPI apps"
```

## How It Works

1. **You ask Nova to do something**
2. **Nova decides if she needs a tool** (automatically)
3. **Tool executes** (you see: 🔧 Nova is using: tool_name)
4. **Nova gets the result** and responds naturally

## Tech Stack

- **AI Model:** Groq API (llama-3.3-70b-versatile)
- **Function Calling:** OpenAI-compatible tool use
- **Tools Framework:** Your existing `tools/` system
- **UI:** Rich terminal interface

## Requirements

```bash
pip install requests rich
```

## API Key

The script uses your existing `GROQ_API_KEY` environment variable.

```bash
export GROQ_API_KEY="your_key_here"
```

Or it falls back to the hardcoded one in the script (already set).

## Tools Available

| Tool | Operations | Examples |
|------|-----------|----------|
| `file_ops` | read, write, move, copy, delete, list | Manage any files/folders |
| `shell` | command | Run any bash command |
| `web_search` | search, fetch | DuckDuckGo search + fetch URLs |
| `code_ops` | append, replace, insert, analyze | Edit Python/JS/any code |

## Safety Notes

- **Nova can delete files** - she won't do it maliciously, but be clear
- **She can run any shell command** - same deal
- **Web search is read-only** - can't post/modify remote content
- **Tool execution shows in terminal** - you'll see what she's doing

## Limitations

- Groq's llama-3.3 is **text-only** (no image generation/analysis)
- Web search uses DuckDuckGo (no Google/advanced search)
- File operations are synchronous (might be slow for huge files)
- No persistent memory across sessions (yet)

## Next Steps

Want to add:
- **Persistent memory** (save conversation context to DB)
- **Image capabilities** (switch to GPT-4o or Claude)
- **More tools** (git operations, database queries, API calls)
- **Web UI** (move from terminal to browser)

Let me know what you want to add next! 🚀
