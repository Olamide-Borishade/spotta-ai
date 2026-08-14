// Tap-to-talk voice input using the browser Web Speech API.
// One tap starts listening; the transcript fills the target input and submits its form.
(function () {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  function attachVoiceInput(micId, inputId) {
    const micButton = document.getElementById(micId);
    const targetInput = document.getElementById(inputId);

    if (!micButton) return;

    if (!SpeechRecognition || !targetInput) {
      micButton.style.display = "none"; // fail clearly: hide if unsupported
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-CA";
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let listening = false;

    micButton.addEventListener("click", function () {
      if (listening) {
        recognition.stop();
        return;
      }
      recognition.start();
    });

    recognition.addEventListener("start", function () {
      listening = true;
      micButton.classList.add("listening");
    });

    recognition.addEventListener("end", function () {
      listening = false;
      micButton.classList.remove("listening");
    });

    recognition.addEventListener("result", function (event) {
      let transcript = "";
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      targetInput.value = transcript;

      if (event.results[event.results.length - 1].isFinal) {
        targetInput.form.requestSubmit();
      }
    });

    recognition.addEventListener("error", function () {
      listening = false;
      micButton.classList.remove("listening");
    });
  }

  attachVoiceInput("mic-button", "chat-input");
  attachVoiceInput("assistant-mic-button", "assistant-input");
})();
