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
