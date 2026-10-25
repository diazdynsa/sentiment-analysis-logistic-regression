/**
 * ReviewScope — main.js
 * Interaksi UI: character counter, form loading state, clear button.
 * Tidak ada logika prediksi di sini — semua inferensi dilakukan di backend Flask.
 */

(function () {
  "use strict";

  // ---------------------------------------------------------------------------
  // Element references
  // ---------------------------------------------------------------------------
  const form       = document.getElementById("sentiment-form");
  const textarea   = document.getElementById("review-input");
  const submitBtn  = document.getElementById("submit-btn");
  const clearBtn   = document.getElementById("clear-btn");
  const charCurrent = document.getElementById("char-current");
  const charCount   = document.getElementById("char-count");

  const MAX_LENGTH = 2000;

  // ---------------------------------------------------------------------------
  // Character counter
  // ---------------------------------------------------------------------------
  function updateCharCount() {
    if (!textarea || !charCurrent || !charCount) return;

    const len = textarea.value.length;
    charCurrent.textContent = len;

    charCount.classList.remove("char-count--warn", "char-count--over");
    if (len >= MAX_LENGTH) {
      charCount.classList.add("char-count--over");
    } else if (len >= MAX_LENGTH * 0.85) {
      charCount.classList.add("char-count--warn");
    }
  }

  if (textarea) {
    textarea.addEventListener("input", updateCharCount);
    // Initialise on load (for back-navigation with pre-filled text)
    updateCharCount();
  }

  // ---------------------------------------------------------------------------
  // Form submit — loading state
  // ---------------------------------------------------------------------------
  if (form && submitBtn) {
    form.addEventListener("submit", function (e) {
      const value = textarea ? textarea.value.trim() : "";

      // Client-side empty check (backend also validates)
      if (!value) {
        e.preventDefault();
        textarea && textarea.focus();
        return;
      }

      // Activate loading state
      submitBtn.classList.add("btn--loading");
      submitBtn.setAttribute("aria-disabled", "true");
      submitBtn.disabled = true;
    });
  }

  // ---------------------------------------------------------------------------
  // Clear button — reset textarea and scroll to form
  // ---------------------------------------------------------------------------
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      // If there's a result on the page, navigate back to clean state
      const resultPanel = document.getElementById("result-panel");
      const emptyState  = document.getElementById("empty-state");

      if (textarea) {
        textarea.value = "";
        textarea.classList.remove("form-textarea--error");
        updateCharCount();
      }

      // If result panel is visible, reload page to show empty state
      // (server-side rendered — simplest reliable approach)
      if (resultPanel) {
        window.location.href = "/";
        return;
      }

      // Already on clean state — just clear and focus
      if (textarea) {
        textarea.focus();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Smooth scroll for in-page nav links
  // ---------------------------------------------------------------------------
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (e) {
      const targetId = this.getAttribute("href").slice(1);
      const target   = document.getElementById(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  // ---------------------------------------------------------------------------
  // Animate probability bars on page load (if result is present)
  // ---------------------------------------------------------------------------
  const probBars = document.querySelectorAll(".prob-bar-fill");
  if (probBars.length) {
    // Bars have CSS transition; briefly set to 0 then animate to actual width
    probBars.forEach(function (bar) {
      const finalWidth = bar.style.width;
      bar.style.width = "0";
      // Use rAF to allow layout paint, then trigger transition
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          bar.style.width = finalWidth;
        });
      });
    });
  }

})();
