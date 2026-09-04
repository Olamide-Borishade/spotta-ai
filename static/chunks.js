// Polls RAG build status after a re-chunk request, then reloads to show fresh chunks.
(function () {
  const statusEl = document.getElementById("chunks-status");
  if (!window.CHUNKS_PAGE_BUILDING || !statusEl) return;

  statusEl.classList.add("assistant-msg-building");

  const poll = setInterval(function () {
    fetch("/assistant/rag-status")
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (data.status === "ready") {
          clearInterval(poll);
          window.location.href = "/chunks";
        } else if (data.status === "error") {
          clearInterval(poll);
          statusEl.textContent = "Re-chunking failed: " + (data.error || "unknown error");
          statusEl.classList.remove("assistant-msg-building");
        }
      })
      .catch(function () {
        clearInterval(poll);
        statusEl.textContent = "Lost connection while re-chunking. Refresh to check status.";
        statusEl.classList.remove("assistant-msg-building");
      });
  }, 700);
})();
