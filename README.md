# Nova — Local AI Assistant

[![Lint & Check](https://github.com/Memphis465/Nova/actions/workflows/lint.yml/badge.svg)](https://github.com/Memphis465/Nova/actions/workflows/lint.yml)

A local AI assistant with tool integration and intelligent task execution.

## Quick Setup

1. **Create virtual environment & install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set API keys:**
   ```bash
   export GROQ_API_KEY="your_groq_key_here"
   export GEMINI_API_KEY="your_gemini_key_here"
   ```
   
   Or add to `.env` file (auto-loaded if `python-dotenv` is installed).

3. **Start the server:**
   ```bash
   ./START_NOVA_SERVER.command
   ```

## Development

Install dev dependencies (linters):
```bash
pip install -r requirements-dev.txt
```

Run linters locally:
```bash
python -m pyflakes tools/ *.py
python -m flake8 tools/ *.py
```

CI runs automatically on push to `main` via GitHub Actions (see `.github/workflows/lint.yml`).

## Project Structure

- `tools/` — Tool modules (base classes, registry, discovery)
- `static/` — Frontend files (HTML, JS, manifest, service worker)
- `Documentation/` — Setup & usage guides
- `uploads/` — User file uploads
- `backups/` — File backups from modifications

## Notes

- **Shell execution** is disabled by default (whitelist). Use `./run_one_shot.sh` with `SHELL_ALLOW=1` for one-off commands (use with caution).
- **API keys** should come from environment or `.env` file.
- **Uploads** and **backups** are stored locally in `uploads/` and `backups/` directories.
- **Tools** are auto-discovered via `tools.loader.discover_tools()`.

## Repository

- **GitHub:** [Memphis465/Nova](https://github.com/Memphis465/Nova)
- **License:** (see LICENSE file if present)
