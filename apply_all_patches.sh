#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

mkdir -p backups
cp tools/shell_cmd.py backups/shell_cmd.py.bak 2>/dev/null || true
cp nova_ultimate.py backups/nova_ultimate.py.bak 2>/dev/null || true
cp static/index.html backups/index.html.bak 2>/dev/null || true
cp static/app.js backups/app.js.bak 2>/dev/null || true

# (1) Whitelist + opt-in shell tool
cat > tools/shell_cmd.py <<'PY'
"""Whitelisted shell command tool with opt-in execution and logging."""

import os
import re
import shlex
import subprocess
from datetime import datetime
from .base import BaseTool, ToolExecutionError
from .registry import register_tool

# Simple whitelist of safe read-only/info commands (first token)
WHITELIST = {
    "ls", "df", "du", "whoami", "uname", "uptime", "id", "ps", "echo", "stat", "date"
}

# Dangerous regex patterns (case-insensitive)
DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bdd\b",
    r":\s*\(\)\s*{\s*:\|:\s*&\s*};\s*:",  # fork bomb
    r">/dev/\w+",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bmkfs\b",
    r"\bchmod\s+0\b",
    r"\bchown\s+root\b",
]

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "shell_exec.log")

def is_dangerous(command: str) -> bool:
    cmd = command.lower()
    for p in DANGEROUS_PATTERNS:
        if re.search(p, cmd, flags=re.IGNORECASE):
            return True
    return False

def log_attempt(command: str, allowed: bool, note: str = ""):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} | allowed={allowed} | cmd={command!r} | {note}\n")
    except Exception:
        pass

@register_tool
class ShellCommandTool(BaseTool):
    name = "shell"
    description = "Execute a small set of safe shell commands (whitelist). Set SHELL_ALLOW=1 to allow arbitrary commands."

    def run(self, command: str, timeout: int = 30) -> dict:
        if not command or not command.strip():
            raise ToolExecutionError("Empty command")

        if is_dangerous(command):
            log_attempt(command, allowed=False, note="blocked: dangerous pattern")
            return {"ok": False, "error": "Command blocked by safety policy (dangerous pattern detected)."}

        # Determine first token
        try:
            first = shlex.split(command)[0]
        except Exception:
            first = command.strip().split()[0]

        allow_flag = os.environ.get("SHELL_ALLOW", "") in ("1", "true", "yes")

        if first not in WHITELIST and not allow_flag:
            log_attempt(command, allowed=False, note="blocked: not whitelisted and env not set")
            return {"ok": False, "error": "Command not permitted: only a small whitelist is allowed. Set SHELL_ALLOW=1 to opt-in (risky)."}

        # Allowed: execute
        log_attempt(command, allowed=True, note="executing")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            out = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
            return {"ok": True, "result": out}
        except subprocess.TimeoutExpired:
            log_attempt(command, allowed=False, note="timeout")
            return {"ok": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            log_attempt(command, allowed=False, note=f"exc:{e}")
            return {"ok": False, "error": f"Command execution failed: {str(e)}"}
PY

# (2) Patch nova_ultimate.py to add deterministic attachment preprocessing
python3 - <<'PY'
from pathlib import Path
p = Path("nova_ultimate.py")
s = p.read_text()
marker = "for turn in range(max_turns):"
if marker not in s:
    print("ERR: insertion marker not found in nova_ultimate.py; aborting patch.")
    raise SystemExit(1)
insertion = r'''
    # --- Attachment preprocessing (auto-inserted) ---
    import re as _re
    _attachment_matches = _re.findall(r"\[ATTACHED_FILE:([^\\]]+)\\]", user_message)
    if _attachment_matches:
        for _idx, _path in enumerate(_attachment_matches, start=1):
            _path = _path.strip()
            _ext = _path.split('.')[-1].lower() if '.' in _path else ''
            if _ext in ("mp4","mov","webm","mkv"):
                _op = "analyze_video"
                _args = {"operation": _op, "video_url": _path}
            else:
                _op = "analyze_image"
                _args = {"operation": _op, "image_path": _path}
            console.print(f"[dim]🔧 Preprocessing attachment: {_path} -> {_op}[/dim]")
            try:
                _tool_result = runner.run("gemini_vision", **_args)
            except Exception as _e:
                _tool_result = {"ok": False, "error": str(_e)}
            if _tool_result.get("ok"):
                _res_content = json.dumps(_tool_result["result"])
            else:
                _res_content = f"Error: {_tool_result.get('error','Unknown error')}"
            messages.append({
                "role": "tool",
                "tool_call_id": f"attachment-{_idx}",
                "content": _res_content
            })
    # --- end attachment preprocessing ---
'''
s = s.replace(marker, insertion + "\n    " + marker, 1)
p.write_text(s)
print("Patched nova_ultimate.py with attachment preprocessing.")
PY

# (3) Overwrite PWA files (voice + upload UI)
cat > static/index.html <<'HT'
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <link rel="manifest" href="/manifest.json" />
  <title>Nova — Phone</title>
  <style>
    body{font-family:system-ui,Segoe UI,Helvetica,Arial;background:#0b0b0f;color:#e6e6ea;margin:0}
    .app{display:flex;flex-direction:column;height:100vh}
    .log{flex:1;overflow:auto;padding:16px}
    .input{display:flex;padding:8px;border-top:1px solid rgba(255,255,255,0.06);gap:8px;align-items:center}
    input[type="text"]{flex:1;padding:12px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:#0f1115;color:#fff}
    button{padding:10px;border-radius:8px;background:#7c3aed;color:white;border:none}
    .msg.user{color:#9ad1ff;margin:8px 0;text-align:right}
    .msg.nova{color:#ffddc7;margin:8px 0;text-align:left}
    #fileInput{display:none}
    .controls{display:flex;gap:8px}
    .hint{font-size:12px;color:#9aa0b2;padding:6px 12px}
  </style>
</head>
<body>
<div class="app">
  <div id="log" class="log"></div>
  <div class="hint">Tip: Tap 📎 to attach an image/file (Nova will analyze it). Hold 🎤 to speak.</div>
  <div class="input">
    <div class="controls">
      <button id="mic" title="Hold to speak">🎤</button>
      <button id="ttsToggle" title="Toggle speak replies">🔊</button>
      <label for="fileInput" style="cursor:pointer;background:#26262a;padding:8px;border-radius:8px;">📎</label>
      <input id="fileInput" type="file" />
    </div>
    <input id="txt" type="text" placeholder="Say something to Nova..." />
    <button id="send">Send</button>
  </div>
</div>
<script src="/static/app.js"></script>
</body>
</html>
HT

cat > static/app.js <<'JS'
const log = document.getElementById("log");
const txt = document.getElementById("txt");
const send = document.getElementById("send");
const mic = document.getElementById("mic");
const ttsToggle = document.getElementById("ttsToggle");
const fileInput = document.getElementById("fileInput");

let ttsEnabled = true;

function addMsg(who, text){
  const d = document.createElement("div");
  d.className = "msg " + (who === "you" ? "user" : "nova");
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

async function uploadFile(file){
  const fd = new FormData();
  fd.append("file", file);
  try{
    const res = await fetch("/api/upload", { method:"POST", body: fd });
    return await res.json();
  }catch(e){
    return { error: "upload failed" };
  }
}

async function sendMsg(){
  const message = txt.value.trim();
  const file = fileInput.files[0];
  if(!message && !file) return;
  if(message) addMsg("you", message);
  if(file) addMsg("you", "📎 " + file.name);

  txt.value = "";
  fileInput.value = "";

  addMsg("nova", "…thinking…");
  const placeholder = log.lastChild;

  try{
    let payload = { message };
    if(file){
      const up = await uploadFile(file);
      if(up.error){ placeholder.textContent = "Upload error"; return; }
      payload.file_path = up.file_path;
      // The server will translate uploads into [ATTACHED_FILE:...] for Nova
    }

    const res = await fetch("/api/chat", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    const j = await res.json();
    if(j.error) placeholder.textContent = "Error: " + j.error;
    else {
      placeholder.textContent = j.response;
      if(ttsEnabled) speak(j.response);
    }
  }catch(e){
    placeholder.textContent = "Network error";
  }
}

function speak(text){
  if(!("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-US";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

// SpeechRecognition (webkit fallback)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if(SpeechRecognition && mic){
  const recog = new SpeechRecognition();
  recog.lang = "en-US";
  recog.interimResults = false;
  recog.maxAlternatives = 1;

  mic.addEventListener("mousedown", ()=> recog.start());
  mic.addEventListener("touchstart", ()=> recog.start());
  mic.addEventListener("mouseup", ()=> recog.stop());
  mic.addEventListener("touchend", ()=> recog.stop());

  recog.onresult = (e) => {
    const spoken = e.results[0][0].transcript;
    txt.value = spoken;
    sendMsg();
  };
  recog.onerror = (e) => console.warn("Speech recog error", e);
} else if(mic) {
  mic.style.opacity = 0.4;
}

ttsToggle.addEventListener("click", ()=> {
  ttsEnabled = !ttsEnabled;
  ttsToggle.style.opacity = ttsEnabled ? "1" : "0.4";
});

send.addEventListener("click", sendMsg);
txt.addEventListener("keydown", (e)=>{ if(e.key==="Enter") sendMsg(); });
JS

# (4) Ensure uploads dir and run helper
mkdir -p uploads
cat > run_one_shot.sh <<'SH2'
#!/bin/bash
# Run the Nova server with SHELL_ALLOW enabled only for this process.
export SHELL_ALLOW=1
./START_NOVA_SERVER.command
SH2
chmod +x run_one_shot.sh

echo "Patches applied, backups saved in backups/. Modified: tools/shell_cmd.py, nova_ultimate.py, static/index.html, static/app.js."
echo "Run 'source venv/bin/activate' and then './START_NOVA_SERVER.command' to start the safe server (SHELL_ALLOW off)."
echo "Use './run_one_shot.sh' to run one process with SHELL_ALLOW=1 (risky)."
