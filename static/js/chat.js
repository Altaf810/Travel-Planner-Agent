/**
 * TravelMind AI — Chat JavaScript
 * Handles AI chat interface with conversation history
 */

let chatHistory = [];
let isTyping = false;

/* ── Send message ────────────────────────────────────────────── */
async function sendMessage() {
  const input = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message || isTyping) return;

  input.value = "";
  input.style.height = "auto";
  appendMessage("user", message);
  chatHistory.push({ role: "user", content: message });

  showTypingIndicator();
  isTyping = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: chatHistory.slice(-10) }),
    });
    const data = await res.json();
    removeTypingIndicator();
    isTyping = false;

    if (data.success) {
      appendMessage("assistant", data.response);
      chatHistory.push({ role: "assistant", content: data.response });
    } else {
      appendMessage("assistant", `⚠️ Error: ${data.error || "Failed to get response."}`);
    }
  } catch (err) {
    removeTypingIndicator();
    isTyping = false;
    appendMessage("assistant", `⚠️ Connection error. Please check that the server is running.\n\n_${err.message}_`);
  }
}

/* ── Quick ask ───────────────────────────────────────────────── */
function quickAsk(btn) {
  const input = document.getElementById("chatInput");
  input.value = btn.textContent.trim();
  input.focus();
  sendMessage();
}

/* ── Clear chat ──────────────────────────────────────────────── */
function clearChat() {
  chatHistory = [];
  const msgs = document.getElementById("chatMessages");
  // Keep only welcome message (first child)
  while (msgs.children.length > 1) msgs.removeChild(msgs.lastChild);
  showToast("Chat cleared", "info");
}

/* ── Append message ──────────────────────────────────────────── */
function appendMessage(role, content) {
  const msgs = document.getElementById("chatMessages");
  const isUser = role === "user";
  const now = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  const wrapper = document.createElement("div");
  wrapper.className = `d-flex gap-3 mb-4 ${isUser ? "flex-row-reverse" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "tm-ai-avatar flex-shrink-0 mt-1";
  avatar.innerHTML = isUser ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-robot"></i>';
  if (isUser) {
    avatar.style.background = "linear-gradient(135deg, #22c55e, #16a34a)";
  }

  const bubble = document.createElement("div");
  bubble.className = `tm-msg-bubble ${role}`;

  const contentDiv = document.createElement("div");
  contentDiv.className = "tm-ai-content";

  if (typeof marked !== "undefined") {
    contentDiv.innerHTML = marked.parse(content);
  } else {
    contentDiv.textContent = content;
  }

  const time = document.createElement("div");
  time.className = "tm-msg-time";
  time.textContent = isUser ? `You • ${now}` : `IBM Granite AI • ${now}`;

  bubble.appendChild(contentDiv);
  bubble.appendChild(time);
  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  msgs.appendChild(wrapper);

  // Scroll to bottom
  msgs.scrollTop = msgs.scrollHeight;
}

/* ── Typing indicator ────────────────────────────────────────── */
function showTypingIndicator() {
  const msgs = document.getElementById("chatMessages");
  const wrapper = document.createElement("div");
  wrapper.id = "typingIndicator";
  wrapper.className = "d-flex gap-3 mb-4";
  wrapper.innerHTML = `
    <div class="tm-ai-avatar flex-shrink-0 mt-1"><i class="bi bi-robot"></i></div>
    <div class="tm-msg-bubble assistant">
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
      <div class="tm-msg-time">IBM Granite AI is thinking...</div>
    </div>`;
  msgs.appendChild(wrapper);
  msgs.scrollTop = msgs.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

/* ── Keyboard handling ───────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");

  if (input) {
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-resize textarea
    input.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = Math.min(this.scrollHeight, 120) + "px";
    });
  }

  // Focus on load
  setTimeout(() => input && input.focus(), 100);
});
