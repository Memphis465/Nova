const log = document.getElementById("log");
const txt = document.getElementById("txt");
const send = document.getElementById("send");
const mic = document.getElementById("mic");
const ttsToggle = document.getElementById("ttsToggle");
const fileInput = document.getElementById("fileInput");
const installBtn = document.getElementById("installBtn");
const themeToggle = document.getElementById("themeToggle");
const historyBtn = document.getElementById("historyBtn");
const historyModal = document.getElementById("historyModal");
const exportBtn = document.getElementById("exportBtn");
const clearBtn = document.getElementById("clearBtn");
const historyList = document.getElementById("historyList");

let ttsEnabled = true;
let deferredPrompt = null;

// Theme Management
function initTheme() {
  const theme = localStorage.getItem("nova_theme") || "dark";
  document.documentElement.setAttribute("data-theme", theme);
  themeToggle.textContent = theme === "dark" ? "☀️" : "🌙";
}

themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const newTheme = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("nova_theme", newTheme);
  themeToggle.textContent = newTheme === "dark" ? "☀️" : "🌙";
  haptic("light");
});

initTheme();

// History Management
async function loadAndDisplayHistory() {
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    const history = data.history || [];
    
    historyList.innerHTML = "";
    if (history.length === 0) {
      historyList.innerHTML = "<p>No chat history yet.</p>";
      return;
    }
    
    history.forEach((item) => {
      const div = document.createElement("div");
      div.className = `msg ${item.role === "user" ? "user" : "nova"}`;
      div.textContent = `[${item.type || "text"}] ${item.message}`;
      historyList.appendChild(div);
    });
  } catch (e) {
    historyList.innerHTML = `<p>Error loading history: ${e.message}</p>`;
  }
}

historyBtn.addEventListener("click", () => {
  loadAndDisplayHistory();
  historyModal.classList.add("show");
});

exportBtn.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/history/export");
    const history = await res.json();
    const blob = new Blob([JSON.stringify(history, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `nova_history_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    haptic("medium");
  } catch (e) {
    alert("Export failed: " + e.message);
  }
});

clearBtn.addEventListener("click", async () => {
  if (!confirm("Are you sure you want to clear all chat history? This cannot be undone.")) return;
  try {
    await fetch("/api/history", { method: "DELETE" });
    historyList.innerHTML = "<p>History cleared.</p>";
    haptic("medium");
  } catch (e) {
    alert("Clear failed: " + e.message);
  }
});

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
