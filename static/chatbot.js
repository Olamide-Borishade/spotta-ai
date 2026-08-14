// Spotta Assistant widget: floating button + panel, calls POST /assistant.
(function () {
  const toggleBtn = document.getElementById("assistant-toggle");
  const panel = document.getElementById("assistant-panel");
  const closeBtn = document.getElementById("assistant-close");
  const form = document.getElementById("assistant-form");
  const input = document.getElementById("assistant-input");
  const modelSelect = document.getElementById("assistant-model");
  const messages = document.getElementById("assistant-messages");

  if (!toggleBtn || !panel || !form) return;

  function setOpen(isOpen) {
    panel.hidden = !isOpen;
    toggleBtn.setAttribute("aria-expanded", String(isOpen));
    if (isOpen) input.focus();
  }

  toggleBtn.addEventListener("click", function () {
    setOpen(panel.hidden);
  });

  closeBtn.addEventListener("click", function () {
    setOpen(false);
  });

  function addMessage(text, sender) {
    const el = document.createElement("div");
    el.className = "assistant-msg assistant-msg-" + sender;
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    input.value = "";
    input.disabled = true;

    fetch("/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, model: modelSelect.value }),
    })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        addMessage(data.reply || "Something went wrong. Please try again.", "bot");
      })
      .catch(function () {
        addMessage("Could not reach the assistant. Check your connection and try again.", "bot");
      })
      .finally(function () {
        input.disabled = false;
        input.focus();
      });
  });
})();
