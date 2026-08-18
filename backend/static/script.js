const form = document.getElementById("guess-form");
const guessInput = document.getElementById("guess");
const reveal = document.getElementById("reveal");
const guessText = document.getElementById("your-guess-text");

const chatSection = document.getElementById("chat");
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");

let chatHistory = [];

function appendMessage(role, text) {
    const p = document.createElement("p");
    p.className = role === "user" ? "chat-msg chat-user" : "chat-msg chat-ai";
    p.textContent = text;
    chatLog.appendChild(p);
    chatLog.scrollTop = chatLog.scrollHeight;
}

async function sendToAI() {
    const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: chatHistory }),
    });
    const data = await response.json();

    if (data.error) {
        appendMessage("ai", "Sorry, something went wrong: " + data.error);
        return;
    }

    chatHistory.push({ role: "assistant", content: data.reply });
    appendMessage("ai", data.reply);
}

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    chatHistory.push({ role: "user", content: text });
    appendMessage("user", text);
    chatInput.value = "";

    sendToAI();
});

form.addEventListener("submit", (event) => {
    event.preventDefault();
    guessText.textContent = guessInput.value;
    reveal.classList.remove("hidden");
    guessInput.disabled = true;
    form.querySelector("button").disabled = true;

    chatSection.classList.remove("hidden");
    sendToAI();
});
