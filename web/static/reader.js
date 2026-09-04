(function () {
  "use strict";

  var reader = document.getElementById("reader");
  if (!reader || !("speechSynthesis" in window)) {
    if (reader) {
      reader.querySelectorAll(".controls button, .controls select").forEach(function (el) {
        el.disabled = true;
      });
    }
    return;
  }

  var paragraphs = JSON.parse(reader.dataset.paragraphs || "[]");
  var btnPlay = document.getElementById("btn-play");
  var btnPause = document.getElementById("btn-pause");
  var btnStop = document.getElementById("btn-stop");
  var rateInput = document.getElementById("rate");
  var rateValue = document.getElementById("rate-value");
  var voiceSelect = document.getElementById("voice");
  var toggleZh = document.getElementById("toggle-zh");

  var voices = [];
  var nextIndex = 0;
  var playing = false;

  function loadVoices() {
    var all = window.speechSynthesis.getVoices();
    voices = all.filter(function (v) { return v.lang.toLowerCase().indexOf("en") === 0; });
    if (voices.length === 0) voices = all;
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

  rateInput.addEventListener("input", function () {
    rateValue.textContent = rateInput.value + "x";
  });

  toggleZh.addEventListener("change", function () {
    document.querySelectorAll(".para-zh").forEach(function (el) {
      el.style.display = toggleZh.checked ? "" : "none";
    });
  });

  function currentVoice() {
    return voices[voiceSelect.value] || null;
  }

  function speakText(text, onend) {
    var utter = new SpeechSynthesisUtterance(text);
    utter.rate = parseFloat(rateInput.value);
    var voice = currentVoice();
    if (voice) utter.voice = voice;
    utter.onend = onend || null;
    window.speechSynthesis.speak(utter);
  }

  function highlight(index) {
    document.querySelectorAll(".para").forEach(function (el) { el.classList.remove("speaking"); });
    if (index >= 0) {
      var el = document.querySelector('.para[data-index="' + index + '"]');
      if (el) {
        el.classList.add("speaking");
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }

  function setButtonsPlaying() {
    btnPlay.disabled = true;
    btnPause.disabled = false;
    btnPause.textContent = "⏸ 暫停";
    btnStop.disabled = false;
  }

  function setButtonsStopped() {
    btnPlay.disabled = false;
    btnPause.disabled = true;
    btnStop.disabled = true;
    highlight(-1);
  }

  function playFrom(index) {
    if (index >= paragraphs.length) {
      playing = false;
      nextIndex = 0;
      setButtonsStopped();
      return;
    }
    playing = true;
    setButtonsPlaying();
    highlight(index);
    speakText(paragraphs[index].en, function () {
      if (!playing) return;
      nextIndex = index + 1;
      playFrom(nextIndex);
    });
  }

  btnPlay.addEventListener("click", function () {
    window.speechSynthesis.cancel();
    playFrom(nextIndex);
  });

  btnPause.addEventListener("click", function () {
    var synth = window.speechSynthesis;
    if (synth.speaking && !synth.paused) {
      synth.pause();
      btnPause.textContent = "▶ 繼續";
    } else if (synth.paused) {
      synth.resume();
      btnPause.textContent = "⏸ 暫停";
    }
  });

  btnStop.addEventListener("click", function () {
    playing = false;
    nextIndex = 0;
    window.speechSynthesis.cancel();
    setButtonsStopped();
  });

  document.querySelectorAll(".btn-para-play").forEach(function (btn) {
    btn.addEventListener("click", function () {
      window.speechSynthesis.cancel();
      nextIndex = parseInt(btn.dataset.index, 10);
      playFrom(nextIndex);
    });
  });

  document.querySelectorAll(".btn-say").forEach(function (btn) {
    btn.addEventListener("click", function () {
      window.speechSynthesis.cancel();
      speakText(btn.dataset.text);
    });
  });
})();
