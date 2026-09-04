// Tap-to-talk voice input using the browser Web Speech API.
// One tap starts listening; the transcript fills the target input and submits its form.
(function () {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  const ERROR_MESSAGES = {
    "not-allowed": "Mic access blocked",
    "no-speech": "No speech heard",
    "audio-capture": "No microphone found",
    "network": "Network error",
    "aborted": "Cancelled"
  };

  // Some browsers never fire a "no-speech" error even when nothing is heard,
  // leaving the mic stuck "listening" forever. This backstops that.
  const NO_RESULT_TIMEOUT_MS = 10000;

  // Pulls a place name out of a spoken request like "can you find me a
  // parking spot in downtown Vancouver" so voice search works from natural
  // phrasing, not just a bare address. A real address still works fine and
  // gets geocoded more precisely, but shouldn't be required.
  function extractDestination(transcript) {
    const match = transcript.match(/\b(?:in|near|at|around|close to)\s+(.+)$/i);
    const destination = match && match[1] ? match[1] : transcript;
    return destination.trim().replace(/[.?!]+$/, "");
  }

  function attachVoiceInput(micId, inputId, transformFinalTranscript) {
    const micButton = document.getElementById(micId);
    const targetInput = document.getElementById(inputId);

    if (!micButton) return;

    if (!SpeechRecognition || !targetInput) {
      micButton.style.display = "none"; // fail clearly: hide if unsupported
      return;
    }

    const micStatus = micButton.querySelector(".mic-status");
    const defaultStatusText = micStatus ? micStatus.textContent : "";

    const recognition = new SpeechRecognition();
    recognition.lang = "en-CA";
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let listening = false;
    let noResultTimer = null;

    function clearNoResultTimer() {
      if (noResultTimer) {
        clearTimeout(noResultTimer);
        noResultTimer = null;
      }
    }

    function showStatus(message) {
      if (!micStatus) return;
      micStatus.textContent = message;
      micButton.classList.add("show-status");
      setTimeout(function () {
        micButton.classList.remove("show-status");
        micStatus.textContent = defaultStatusText;
      }, 2500);
    }

    micButton.addEventListener("click", function () {
      if (listening) {
        recognition.stop();
        return;
      }
      try {
        recognition.start();
      } catch (e) {
        console.error("Voice input failed to start:", e);
        showStatus("Could not start mic");
      }
    });

    recognition.addEventListener("start", function () {
      listening = true;
      micButton.classList.add("listening");
      clearNoResultTimer();
      noResultTimer = setTimeout(function () {
        recognition.stop();
      }, NO_RESULT_TIMEOUT_MS);
    });

    recognition.addEventListener("end", function () {
      listening = false;
      micButton.classList.remove("listening");
      clearNoResultTimer();
    });

    recognition.addEventListener("result", function (event) {
      clearNoResultTimer();
      let transcript = "";
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }

      const isFinal = event.results[event.results.length - 1].isFinal;
      targetInput.value = (isFinal && transformFinalTranscript)
        ? transformFinalTranscript(transcript)
        : transcript;

      if (isFinal) {
        targetInput.form.requestSubmit();
      }
    });

    recognition.addEventListener("error", function (event) {
      listening = false;
      micButton.classList.remove("listening");
      clearNoResultTimer();
      console.error("Voice input error:", event.error);
      showStatus(ERROR_MESSAGES[event.error] || "Voice input error");
    });
  }

  attachVoiceInput("mic-button", "chat-input", extractDestination);
  attachVoiceInput("assistant-mic-button", "assistant-input");
})();
