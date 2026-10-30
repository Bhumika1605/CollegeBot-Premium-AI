const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const newChatBtn = document.getElementById("newChatBtn");
const sidebar = document.getElementById("sidebar");
const mobileMenu = document.getElementById("mobileMenu");
const mobileScrim = document.getElementById("mobileScrim");

let isSending = false;
let activeController = null;

function closeSidebar() {
  sidebar.classList.remove("open");
  mobileScrim.classList.remove("show");
}

mobileMenu.addEventListener("click", () => {
  sidebar.classList.toggle("open");
  mobileScrim.classList.toggle("show");
});

mobileScrim.addEventListener("click", closeSidebar);

function resizeInput() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 130) + "px";
}

input.addEventListener("input", resizeInput);

function scrollToLatest() {
  messages.scrollTop = messages.scrollHeight;
}

function addMessage(text, who) {
  welcome.style.display = "none";
  messages.classList.add("visible");

  const row = document.createElement("div");
  row.className = `message-row ${who === "user" ? "user" : "bot-row"}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = who === "user" ? "Y" : "✳";

  const content = document.createElement("div");
  content.className = "message-content";

  const name = document.createElement("div");
  name.className = "message-name";
  name.textContent = who === "user" ? "You" : "CollegeBot";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  content.append(name, bubble);
  row.append(avatar, content);
  messages.appendChild(row);

  scrollToLatest();
  return row;
}

function addTyping() {
  const row = addMessage("", "bot");
  const bubble = row.querySelector(".bubble");

  bubble.classList.add("typing");
  bubble.innerHTML = "<span></span><span></span><span></span>";

  return row;
}

function setSending(sending) {
  isSending = sending;
  sendBtn.disabled = sending;
  input.setAttribute("aria-busy", String(sending));
  sendBtn.setAttribute("aria-label", sending ? "Generating response" : "Send message");
}

async function sendMessage(forcedText) {
  const message = (forcedText ?? input.value).trim();

  if (!message || isSending) return;

  addMessage(message, "user");

  input.value = "";
  resizeInput();
  closeSidebar();

  setSending(true);

  const typingRow = addTyping();
  const controller = new AbortController();
  activeController = controller;

  // A long response may take time. Abort only after 90 seconds.
  const timeoutId = setTimeout(() => controller.abort(), 90000);

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ message }),
      signal: controller.signal,
      cache: "no-store"
    });

    // Read the response body even for HTTP 503 so the actual backend
    // message is shown instead of a misleading network error.
    const data = await response.json().catch(() => ({}));

    typingRow.remove();

    if (response.ok && data.reply) {
      addMessage(data.reply, "bot");
    } else if (response.status === 503) {
      addMessage(
        data.reply ||
        "The AI service is temporarily busy. Please try again shortly.",
        "bot"
      );
    } else if (response.status === 429) {
      addMessage(
        data.reply ||
        "Too many requests were sent. Please wait a moment before trying again.",
        "bot"
      );
    } else {
      addMessage(
        data.reply ||
        `The server returned an error (${response.status}). Please try again.`,
        "bot"
      );
    }
  } catch (error) {
    typingRow.remove();

    if (error.name === "AbortError") {
      addMessage(
        "This request took too long. The AI service may be busy. Please try again.",
        "bot"
      );
    } else {
      console.error("CollegeBot request failed:", error);

      addMessage(
        "I couldn't connect to the chatbot server. Please check that CollegeBot is running and try again.",
        "bot"
      );
    }
  } finally {
    clearTimeout(timeoutId);
    activeController = null;
    setSending(false);
    input.focus();
  }
}

sendBtn.addEventListener("click", () => sendMessage());

input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

document.querySelectorAll("[data-prompt]").forEach(button => {
  button.addEventListener("click", () => {
    sendMessage(button.dataset.prompt);
  });
});

newChatBtn.addEventListener("click", () => {
  // Don't let a previous response update the new conversation.
  if (activeController) {
    activeController.abort();
  }

  messages.innerHTML = "";
  messages.classList.remove("visible");
  welcome.style.display = "";
  input.value = "";
  resizeInput();
  closeSidebar();
  input.focus();
});
