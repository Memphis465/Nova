# Nova — Local AI Assistant

Quick setup:
1. Create venv and install deps:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Set keys:
   export GROQ_API_KEY="your_groq_key_here"
   export GEMINI_API_KEY="your_gemini_key_here"

3. Start server:
   ./START_NOVA_SERVER.command

Notes:
- Keys must come from environment or a `.env` file (python-dotenv will be used if present).
- Shell execution is disabled by default (whitelist). Use `./run_one_shot.sh` to run one process with `SHELL_ALLOW=1` (risky).
- Uploads save to `uploads/`. Backups of modified files are in `backups/`.
