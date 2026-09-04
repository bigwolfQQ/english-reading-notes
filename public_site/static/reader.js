(function () {
  "use strict";
  if (!("speechSynthesis" in window)) return;

  var rateInput = document.getElementById("rate");
  var rateValue = document.getElementById("rate-value");
  var voiceSelect = document.getElementById("voice");
  var voices = [];

  function loadVoices() {
    var all = window.speechSynthesis.getVoices();
    voices = all.filter(function (v) { return v.lang.toLowerCase().indexOf("en") === 0; });
    if (voices.length === 0) voices = all;
    if (!voiceSelect) return;
    voiceSelect.innerHTML = "";
    voices.forEach(function (v, i) {
      var opt = document.createElement("option");
      opt.value = i;
      opt.textContent = v.name + " (" + v.lang + ")";
      voiceSelect.appendChild(opt);
    });
  }

  loadVoices();
  window.speechSynthesis.onvoiceschanged = loadVoices;

  if (rateInput) {
    rateInput.addEventListener("input", function () {
      rateValue.textContent = rateInput.value + "x";
    });
  }

  document.querySelectorAll(".btn-say").forEach(function (btn) {
    btn.addEventListener("click", function () {
      window.speechSynthesis.cancel();
      var utter = new SpeechSynthesisUtterance(btn.dataset.text);
      utter.rate = rateInput ? parseFloat(rateInput.value) : 1;
      var voice = voiceSelect ? voices[voiceSelect.value] : null;
      if (voice) utter.voice = voice;
      window.speechSynthesis.speak(utter);
    });
  });
})();
