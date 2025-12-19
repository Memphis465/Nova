const log = document.getElementById("log");
const txt = document.getElementById("txt");
const send = document.getElementById("send");
const mic = document.getElementById("mic");
const ttsToggle = document.getElementById("ttsToggle");
const fileInput = document.getElementById("fileInput");
const installBtn = document.getElementById("installBtn");

let ttsEnabled = true;
let deferredPrompt = null;

// PWA Install Prompt
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  installBtn.classList.add("show");
});

installBtn.addEventListener("click", async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`PWA install ${outcome}`);
  deferredPrompt = null;
  installBtn.classList.remove("show");
});

// Register Service Worker
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js").catch(() => {});
}

function haptic(type = "light") {
  if (navigator.vibrate) {
    const patterns = {
      light: 10,
      medium: 30,
      heavy: [50, 20, 50],
    };
    navigator.vibrate(patterns[type] || 10);
  }
}

function addMsg(who, text) {
  const d = document.createElement("div");
  d.className = "msg " + (who === "you" ? "user" : "nova");
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
  haptic(who === "you" ? "light" : "medium");
}

async function uploadFile(file) {
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fetch("/api/upload", { method: "POST", body: fd });
    return await res.json();
  } catch (e) {
    return { error: "upload failed" };
  }
}

async function sendMsg() {
  const message = txt.value.trim();
  const file = fileInput.files[0];
  if (!message && !file) return;

  if (message) addMsg("you", message);
  if (file) addMsg("you", "📎 " + file.name);

  txt.value = "";
  fileInput.value = "";

  addMsg("nova", "…thinking…");
  const placeholder = log.lastChild;

  try {
    let payload = { message };
    if (file) {
      const up = await uploadFile(file);
      if (up.error) {
        placeholder.textContent = "Upload error";
        haptic("heavy");
        return;
      }
      payload.file_path = up.file_path;
    }

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const j = await res.json();
    if (j.error) {
      placeholder.textContent = "Error: " + j.error;
      haptic("heavy");
    } else {
      placeholder.textContent = j.response;
      haptic("medium");
      if (ttsEnabled) speak(j.response);
    }
  } catch (e) {
    placeholder.textContent = "Network error";
    haptic("heavy");
  }
}

function speak(text) {
  if (!("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-US";
  u.rate = 1;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

// SpeechRecognition (webkit fallback)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition && mic) {
  const recog = new SpeechRecognition();
  recog.lang = "en-US";
  recog.interimResults = false;
  recog.maxAlternatives = 1;

  let isRecording = false;

  const startRecording = () => {
    if (isRecording) return;
    isRecording = true;
    haptic("light");
    mic.style.opacity = "0.6";
    recog.start();
  };

  const stopRecording = () => {
    isRecording = false;
    mic.style.opacity = "1";
    recog.stop();
  };

  mic.addEventListener("mousedown", startRecording);
  mic.addEventListener("touchstart", (e) => {
    e.preventDefault();
    startRecording();
  });
  mic.addEventListener("mouseup", stopRecording);
  mic.addEventListener("touchend", (e) => {
    e.preventDefault();
    stopRecording();
  });

  recog.onstart = () => {
    mic.style.background = "#ff6b6b";
  };

  recog.onend = () => {
    mic.style.background = "";
    isRecording = false;
  };

  recog.onresult = (e) => {
    if (e.results[0].isFinal) {
      const spoken = e.results[0][0].transcript;
      txt.value = spoken;
      sendMsg();
    }
  };

  recog.onerror = (e) => {
    console.warn("Speech recog error", e.error);
    haptic("heavy");
    mic.style.background = "";
  };
} else if (mic) {
  mic.style.opacity = "0.4";
  mic.disabled = true;
}

ttsToggle.addEventListener("click", () => {
  ttsEnabled = !ttsEnabled;
  ttsToggle.style.opacity = ttsEnabled ? "1" : "0.4";
  haptic("light");
});

send.addEventListener("click", () => {
  sendMsg();
  haptic("medium");
});

txt.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMsg();
    haptic("medium");
  }
});

// Prevent pull-to-refresh on mobile
document.body.addEventListener("touchmove", (e) => {
  if (e.touches.length > 1) e.preventDefault();
}, { passive: false });
