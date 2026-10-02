const API = "http://127.0.0.1:8000"; // change to your server address when deployed

const messagesEl = document.getElementById("messages");
const chipsEl = document.getElementById("chips");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const statusEl = document.getElementById("status");
const dotEl = document.querySelector(".dot");

const DEFAULT_CHIPS = [
  "Admission rules",
  "Required documents",
  "Fee structure",
  "Entrance exams",
  "Compare B.Tech and BBA",
  "Class locations",
  "Hostel rules",
  "Admission guidance"
];

const WELCOME =
  "Hello! I am ANAND, the GBU assistant for new students. " +
  "Ask me about admission, documents, fees, courses, entrance exams, class locations or hostel rules.";

let busy = false;

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function scrollDown() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addMessage(text, who) {
  const row = document.createElement("div");
  row.className = `row ${who}`;

  if (who === "bot") {
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "A";
    row.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text; // keeps user/bot text safe

  const time = document.createElement("span");
  time.className = "time";
  time.textContent = timeNow();

  bubble.appendChild(time);
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollDown();

  return row;
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "row bot";
  row.innerHTML =
    '<div class="avatar">A</div><div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div>';

  messagesEl.appendChild(row);
  scrollDown();

  return row;
}

function setChips(list) {
  chipsEl.innerHTML = "";

  (list || []).forEach((label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => sendMessage(label));
    chipsEl.appendChild(button);
  });
}

function setOnline(ok) {
  statusEl.textContent = ok ? "Online" : "Offline";
  dotEl.classList.toggle("off", !ok);
}

async function sendMessage(message) {
  const trimmedMessage = message.trim();

  if (busy || !trimmedMessage) return;

  busy = true;
  sendBtn.disabled = true;
  addMessage(trimmedMessage, "user");
  input.value = "";

  const typing = showTyping();

  try {
    const response = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmedMessage })
    });

    if (!response.ok) throw new Error("Server error");

    const data = await response.json();
    typing.remove();
    addMessage(data.reply, "bot");
    setChips(data.suggestions || DEFAULT_CHIPS);
    setOnline(true);
  } catch (error) {
    typing.remove();
    addMessage(
      "I cannot reach the server right now. Please make sure the backend is running " +
        "(uvicorn main:app --reload) and try again.",
      "bot"
    );
    setOnline(false);
  } finally {
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

function startChat() {
  messagesEl.innerHTML = "";
  addMessage(WELCOME, "bot");
  setChips(DEFAULT_CHIPS);
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(input.value);
});

document.getElementById("clearBtn").addEventListener("click", startChat);

startChat();

