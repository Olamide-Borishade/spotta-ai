// Spotta Assistant widget: floating button + panel, calls POST /assistant.
// Answers are grounded in retrieved knowledge-base chunks; citations like
// [Source 1] in the reply become clickable, revealing the chunk text and
// its similarity score.
(function () {
  const toggleBtn = document.getElementById("assistant-toggle");
  const panel = document.getElementById("assistant-panel");
  const closeBtn = document.getElementById("assistant-close");
  const form = document.getElementById("assistant-form");
  const input = document.getElementById("assistant-input");
  const modelSelect = document.getElementById("assistant-model");
  const messages = document.getElementById("assistant-messages");

  if (!toggleBtn || !panel || !form) return;

  // Warm the retrieval index as early as possible, in the background.
  fetch("/assistant/rag-status").catch(function () {});

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
    return el;
  }

  function toggleCitationDetail(messageEl, source) {
    const existing = messageEl.querySelector(
      '.assistant-citation-detail[data-index="' + source.index + '"]'
    );
    if (existing) {
      existing.remove();
      return;
    }

    messageEl.querySelectorAll(".assistant-citation-detail").forEach(function (el) {
      el.remove();
    });

    const detail = document.createElement("div");
    detail.className = "assistant-citation-detail";
    detail.dataset.index = source.index;

    const score = document.createElement("div");
    score.className = "assistant-citation-score";
    score.textContent = "Similarity: " + Math.round(source.similarity * 100) + "%";

    const text = document.createElement("div");
    text.className = "assistant-citation-text";
    text.textContent = source.text;

    detail.appendChild(score);
    detail.appendChild(text);
    messageEl.appendChild(detail);
    messages.scrollTop = messages.scrollHeight;
  }

  function submitRating(rateRow, upBtn, downBtn, rating, payload) {
    upBtn.disabled = true;
    downBtn.disabled = true;
    (rating === "up" ? upBtn : downBtn).classList.add("assistant-rate-selected");

    fetch("/assistant/rate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.assign({ rating: rating }, payload)),
    }).catch(function () {});
  }

  function addRatingRow(messageEl, question, replyText, meta) {
    const row = document.createElement("div");
    row.className = "assistant-rating";

    const upBtn = document.createElement("button");
    upBtn.type = "button";
    upBtn.className = "assistant-rate-btn";
    upBtn.setAttribute("aria-label", "Thumbs up");
    upBtn.textContent = "👍";

    const downBtn = document.createElement("button");
    downBtn.type = "button";
    downBtn.className = "assistant-rate-btn";
    downBtn.setAttribute("aria-label", "Thumbs down");
    downBtn.textContent = "👎";

    const payload = {
      question: question,
      response: replyText,
      model: meta.model,
      response_time: meta.response_time,
      input_tokens: meta.input_tokens,
      output_tokens: meta.output_tokens,
    };

    upBtn.addEventListener("click", function () {
      submitRating(row, upBtn, downBtn, "up", payload);
    });
    downBtn.addEventListener("click", function () {
      submitRating(row, upBtn, downBtn, "down", payload);
    });

    row.appendChild(upBtn);
    row.appendChild(downBtn);
    messageEl.appendChild(row);
  }

  function renderReply(replyText, sources, meta, question) {
    const el = document.createElement("div");
    el.className = "assistant-msg assistant-msg-bot";

    const pattern = /\[Source\s+(\d+)\]/gi;
    let lastIndex = 0;
    let match;

    while ((match = pattern.exec(replyText)) !== null) {
      el.appendChild(document.createTextNode(replyText.slice(lastIndex, match.index)));

      const sourceIndex = parseInt(match[1], 10);
      const source = (sources || []).find(function (s) {
        return s.index === sourceIndex;
      });

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "assistant-citation";
      btn.textContent = match[0];
      if (source) {
        btn.addEventListener("click", function () {
          toggleCitationDetail(el, source);
        });
      } else {
        btn.disabled = true;
      }
      el.appendChild(btn);

      lastIndex = pattern.lastIndex;
    }
    el.appendChild(document.createTextNode(replyText.slice(lastIndex)));

    if (meta) {
      addRatingRow(el, question, replyText, meta);
    }

    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  let buildingIndicator = null;

  function showBuildingIndicator() {
    if (buildingIndicator) return;
    buildingIndicator = addMessage("Preparing knowledge base…", "bot");
    buildingIndicator.classList.add("assistant-msg-building");
  }

  function clearBuildingIndicator() {
    if (buildingIndicator) {
      buildingIndicator.remove();
      buildingIndicator = null;
    }
  }

  function waitForRagReady(onReady) {
    fetch("/assistant/rag-status")
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (data.status === "ready") {
          clearBuildingIndicator();
          onReady();
          return;
        }
        if (data.status === "error") {
          clearBuildingIndicator();
          addMessage("The knowledge base failed to load: " + (data.error || "unknown error"), "bot");
          return;
        }
        showBuildingIndicator();
        setTimeout(function () {
          waitForRagReady(onReady);
        }, 600);
      })
      .catch(onReady);
  }

  function sendMessage(message) {
    fetch("/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, model: modelSelect.value }),
    })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (data.model) {
          renderReply(
            data.reply || "Something went wrong. Please try again.",
            data.sources,
            {
              model: data.model,
              response_time: data.response_time,
              input_tokens: data.input_tokens,
              output_tokens: data.output_tokens,
            },
            message
          );
        } else {
          addMessage(data.reply || "Something went wrong. Please try again.", "bot");
        }
      })
      .catch(function () {
        addMessage("Could not reach the assistant. Check your connection and try again.", "bot");
      })
      .finally(function () {
        input.disabled = false;
        input.focus();
      });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    input.value = "";
    input.disabled = true;

    waitForRagReady(function () {
      sendMessage(message);
    });
  });
})();
