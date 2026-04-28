let sessionId = null;

const messagesDiv = document.getElementById("messages");
const userInput = document.getElementById("user-input");
const typingIndicator = document.getElementById("typing-indicator");
const sendBtn = document.getElementById("send-btn");
const endConversationBtn = document.getElementById("end-conversation");
const feedbackModal = document.getElementById("feedback-modal");
const submitFeedbackBtn = document.getElementById("submit-feedback");
const sessionEnded = document.getElementById("session-ended");

// Feedback modal elements
const feedbackForm = document.getElementById("feedback-form");
const feedbackThankyou = document.getElementById("feedback-thankyou");

// Attach slider update for q1–q6
function attachSliderUpdate(id) {
    const slider = document.getElementById(id);
    const value = document.getElementById(id + "-value");
    slider.addEventListener("input", () => {
        value.textContent = slider.value;
    });
}

["q1", "q2", "q3", "q4", "q5", "q6"].forEach(attachSliderUpdate);

// Theme toggle
const toggle = document.getElementById("theme-toggle");
toggle.addEventListener("click", () => {
    document.body.classList.toggle("dark");
});

// Enter to send
userInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendBtn.click();
    }
});

sendBtn.addEventListener("click", sendMessage);

function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.textContent = text;
    messagesDiv.appendChild(msg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showTyping() {
    typingIndicator.classList.remove("hidden");
}

function hideTyping() {
    typingIndicator.classList.add("hidden");
}

function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, "user");
    userInput.value = "";
    sendBtn.disabled = true;
    showTyping();

    fetch("https://conversational-support-chatbot-9d5s.onrender.com/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Session-ID": sessionId || ""
        },
        body: JSON.stringify({ message: text })
    })
    .then(response => response.json())
    .then(data => {
        if (!sessionId) sessionId = data.session_id;

        hideTyping();
        sendBtn.disabled = false;
        addMessage(data.reply, "bot");
    })
    .catch(error => {
        hideTyping();
        sendBtn.disabled = false;
        addMessage("Error: Could not reach backend.", "bot");
        console.error(error);
    });
}

// END CONVERSATION — now opens confirmation modal
endConversationBtn.addEventListener("click", () => {
    document.getElementById("confirm-end-modal").classList.remove("hidden");
});

// CONFIRM END
document.getElementById("confirm-end").addEventListener("click", () => {

    // Close modal
    document.getElementById("confirm-end-modal").classList.add("hidden");

    // End session on backend
    fetch("https://conversational-support-chatbot-9d5s.onrender.com/end_session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
    });

    // Hide chat UI
    document.getElementById("messages").style.display = "none";
    document.getElementById("input-area").style.display = "none";
    endConversationBtn.style.display = "none";

    // Show session ended + feedback modal
    sessionEnded.classList.remove("hidden");
    feedbackModal.classList.remove("hidden");
});

// CANCEL END
document.getElementById("cancel-end").addEventListener("click", () => {
    document.getElementById("confirm-end-modal").classList.add("hidden");
});

submitFeedbackBtn.addEventListener("click", () => {

    // Collect all slider values
    const q1 = document.getElementById("q1").value;
    const q2 = document.getElementById("q2").value;
    const q3 = document.getElementById("q3").value;
    const q4 = document.getElementById("q4").value;
    const q5 = document.getElementById("q5").value;
    const q6 = document.getElementById("q6").value;

    fetch("https://conversational-support-chatbot-9d5s.onrender.com/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            session_id: sessionId,
            q1, q2, q3, q4, q5, q6
        })
    })
    .then(() => {
        // Hide form, show thank-you message
        feedbackForm.classList.add("hidden");
        feedbackThankyou.classList.remove("hidden");

        // Auto-close after 2 seconds
        setTimeout(() => {
            feedbackModal.classList.add("hidden");
        }, 2000);
    })
    .catch(err => console.error("Feedback error:", err));
});

// Disclaimer modal
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("disclaimer-modal");
  const acceptBtn = document.getElementById("disclaimer-accept");

  modal.style.display = "flex";

  acceptBtn.addEventListener("click", () => {
    modal.style.display = "none";
  });
});