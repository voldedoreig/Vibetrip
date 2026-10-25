/**
 * VibeTrip - Multi-Step Quiz Planner
 * 
 * Manages one-question-at-a-time navigation, interactive step timeline dot jumping,
 * answer validation before advancing, progress bar updates, and double-click protection.
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("quizForm");
  if (!form) return;

  // Activate multi-step JavaScript mode
  form.classList.add("js-quiz-active");

  const isNepali = document.documentElement.lang === "ne";
  const steps = Array.from(form.querySelectorAll(".quiz-step"));
  const totalSteps = steps.length;
  let currentStep = 0;

  // Support direct step jumping via URL param (e.g., /planner?step=6)
  const urlParams = new URLSearchParams(window.location.search);
  const requestedStep = parseInt(urlParams.get("step"), 10);
  if (!isNaN(requestedStep) && requestedStep >= 0 && requestedStep < totalSteps) {
    currentStep = requestedStep;
  }

  const btnPrev = document.getElementById("btnPrev");
  const btnNext = document.getElementById("btnNext");
  const btnSubmit = document.getElementById("btnSubmit");

  const progressBar = document.getElementById("progressBar");
  const stepIndicator = document.getElementById("stepIndicator");
  const percentIndicator = document.getElementById("percentIndicator");
  const stepDotBtns = document.querySelectorAll(".step-dot-btn");

  /**
   * Check if a step has a selected radio button
   */
  function isStepAnswered(index) {
    if (index < 0 || index >= totalSteps) return false;
    const stepEl = steps[index];
    const checkedRadio = stepEl.querySelector("input[type='radio']:checked");
    return Boolean(checkedRadio);
  }

  /**
   * Update progress bar, step indicator text, and timeline dots
   */
  function updateProgress() {
    const stepNumber = currentStep + 1;
    const percent = Math.round((stepNumber / totalSteps) * 100);

    if (progressBar) {
      progressBar.style.width = `${percent}%`;
      progressBar.setAttribute("aria-valuenow", percent);
    }
    if (percentIndicator) {
      percentIndicator.textContent = `${percent}%`;
    }
    if (stepIndicator) {
      stepIndicator.textContent = isNepali
        ? `प्रश्न ${stepNumber} / ${totalSteps}`
        : `Question ${stepNumber} of ${totalSteps}`;
    }

    // Update Step Timeline Dots
    stepDotBtns.forEach((btn, idx) => {
      const isCurrent = idx === currentStep;
      const isAnswered = isStepAnswered(idx);

      btn.classList.toggle("active", isCurrent);
      btn.classList.toggle("completed", isAnswered && !isCurrent);
      btn.setAttribute("aria-current", isCurrent ? "step" : "false");
    });
  }

  /**
   * Show current step and configure navigation buttons
   */
  function showStep(index) {
    steps.forEach((step, idx) => {
      if (idx === index) {
        step.classList.add("active-step");
        // Focus first option for keyboard accessibility
        const firstInput = step.querySelector("input[type='radio']");
        if (firstInput && document.activeElement !== document.body) {
          firstInput.focus();
        }
      } else {
        step.classList.remove("active-step");
      }
    });

    // Configure Prev button
    if (btnPrev) {
      btnPrev.style.display = index === 0 ? "none" : "inline-flex";
    }

    // Configure Next vs Submit button
    if (index === totalSteps - 1) {
      if (btnNext) btnNext.style.display = "none";
      if (btnSubmit) btnSubmit.style.display = "inline-flex";
    } else {
      if (btnNext) btnNext.style.display = "inline-flex";
      if (btnSubmit) btnSubmit.style.display = "none";
    }

    updateProgress();
  }

  // Interactive Timeline Dot Click Handlers
  stepDotBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetIdx = parseInt(btn.getAttribute("data-step-idx"), 10);
      if (isNaN(targetIdx)) return;

      // Allow jumping to any step that is already answered or backwards
      if (targetIdx <= currentStep || isStepAnswered(currentStep) || targetIdx === 0) {
        const valMsg = document.getElementById(`validationMsg-${currentStep}`);
        if (valMsg) valMsg.style.display = "none";

        currentStep = targetIdx;
        showStep(currentStep);
        window.scrollTo({ top: form.offsetTop - 80, behavior: "smooth" });
      } else {
        const valMsg = document.getElementById(`validationMsg-${currentStep}`);
        if (valMsg) {
          valMsg.style.display = "block";
        }
      }
    });
  });

  // Live Monograph Dossier Update Logic
  function updateLiveDossier() {
    const q1 = form.querySelector("input[name='q1_pace']:checked");
    const q2 = form.querySelector("input[name='q2_energy']:checked");
    const q3 = form.querySelector("input[name='q3_slot']:checked");
    const q4 = form.querySelector("input[name='q4_interests']:checked");
    const q5 = form.querySelector("input[name='q5_crowds']:checked");
    const q7 = form.querySelector("input[name='q7_timing']:checked");

    const elPace = document.getElementById("previewPace");
    const elEnergy = document.getElementById("previewEnergy");
    const elSlot = document.getElementById("previewSlot");
    const elInterests = document.getElementById("previewInterests");
    const elCrowds = document.getElementById("previewCrowds");
    const elSeason = document.getElementById("previewSeason");
    const elVibeName = document.getElementById("previewVibeName");
    const elVibeTagline = document.getElementById("previewVibeTagline");

    const getLabel = (input) => {
      if (!input) return "";
      const card = input.closest(".option-card");
      if (card && card.getAttribute("data-opt-label")) {
        return card.getAttribute("data-opt-label");
      }
      return input.value;
    };

    if (q1 && elPace) elPace.textContent = getLabel(q1);
    if (q2 && elEnergy) elEnergy.textContent = getLabel(q2);
    if (q3 && elSlot) elSlot.textContent = getLabel(q3);
    if (q4 && elInterests) elInterests.textContent = getLabel(q4);
    if (q5 && elCrowds) elCrowds.textContent = getLabel(q5);
    if (q7 && elSeason) elSeason.textContent = getLabel(q7);

    // Estimate Archetype live
    if (elVibeName && elVibeTagline) {
      if (q4 && q4.value === "spiritual") {
        elVibeName.textContent = isNepali ? "आत्मिक अन्वेषक" : "Spiritual Seeker";
        elVibeTagline.textContent = isNepali
          ? "“पवित्र स्तूपहरू, बिहानी प्रार्थना चक्रहरू र शान्त ध्यान गल्लीहरू।”"
          : "“Sacred stupas, morning prayer wheels, and meditative alleyways.”";
      } else if (q4 && q4.value === "nature") {
        elVibeName.textContent = isNepali ? "शान्त यात्री" : "Calm Explorer";
        elVibeTagline.textContent = isNepali
          ? "“शान्त वातावरण, ऐतिहासिक मन्दिरका चोकहरू र शीतल बिहानी।”"
          : "“Peaceful reflection, historic temple courtyards, and quiet mountain mornings.”";
      } else if (q4 && q4.value === "heritage") {
        elVibeName.textContent = isNepali ? "सम्पदा इतिहासकार" : "Heritage Historian";
        elVibeTagline.textContent = isNepali
          ? "“सयौँ वर्ष पुराना इँटाका चोकहरू, काष्ठकलाका नमुना र ऐतिहासिक दरबार।”"
          : "“Centuries-old brick squares, master woodcarvings, and royal dynasties.”";
      } else if (q4 && q4.value === "food") {
        elVibeName.textContent = isNepali ? "स्वाद पारखी यात्री" : "Foodie Wanderer";
        elVibeTagline.textContent = isNepali
          ? "“पिरो छोइला, नेवारी खाजा सेट, तात्तातो मःम र परम्परागत चिया पसल।”"
          : "“Spicy choila, Newari khaja sets, steamed momos, and ancient tea shops.”";
      } else if (q2 && q2.value === "high") {
        elVibeName.textContent = isNepali ? "जात्रा उत्सव प्रेमी" : "Festival Spark";
        elVibeTagline.textContent = isNepali
          ? "“रथयात्रा, रङ्गीचङ्गी पर्वहरू र जीवन्त साँझका चोकहरू।”"
          : "“Chariot parades, flying spring powders, and vibrant evening squares.”";
      } else {
        elVibeName.textContent = isNepali ? "सृजनशील यात्री" : "Creative Soul";
        elVibeTagline.textContent = isNepali
          ? "“हस्तकला स्टुडियोहरू, लुकेका कौसीका दृश्यहरू र मौलिक सांस्कृतिक भेटघाट।”"
          : "“Artisan studios, hidden rooftop vistas, and spontaneous cultural encounters.”";
      }
    }
  }

  // Handle option card selection highlights & smooth auto-advance
  steps.forEach((step, sIdx) => {
    const cards = step.querySelectorAll(".option-card");
    const valMsg = document.getElementById(`validationMsg-${sIdx}`);

    cards.forEach((card) => {
      const radio = card.querySelector("input[type='radio']");
      if (!radio) return;

      radio.addEventListener("change", () => {
        // Deselect siblings
        cards.forEach((c) => c.classList.remove("selected"));
        if (radio.checked) {
          card.classList.add("selected");
        }
        // Hide error message if one was showing
        if (valMsg) {
          valMsg.style.display = "none";
        }

        updateLiveDossier();
        updateProgress();

        // Check if this step has calendar or date inputs requiring user interaction
        const hasDatePickers = Boolean(step.querySelector("input[type='date'], .start-date-container"));

        if (!hasDatePickers) {
          // Smooth auto-advance after 280ms feedback pulse for single-choice questions
          if (currentStep < totalSteps - 1) {
            setTimeout(() => {
              currentStep++;
              showStep(currentStep);
              window.scrollTo({ top: form.offsetTop - 80, behavior: "smooth" });
            }, 280);
          } else if (btnSubmit) {
            btnSubmit.focus();
          }
        } else {
          // On Question 7 (calendar window), do NOT auto-advance in 280ms.
          // Allow the user to enter arrival/departure dates or click Continue.
          const dateContainer = step.querySelector(".start-date-container");
          if (dateContainer) {
            dateContainer.classList.add("calendar-engaged");
          }
          if (btnNext) {
            btnNext.focus();
          }
        }
      });
    });
  });

  // Keyboard shortcut listener: keys 1, 2, 3, 4 and arrows
  document.addEventListener("keydown", (e) => {
    // Only listen if not typing in text/date input
    const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
    if (tag === "input" && document.activeElement.type !== "radio") return;
    if (tag === "textarea" || tag === "select") return;

    const key = e.key;
    if (["1", "2", "3", "4"].includes(key)) {
      const activeStepEl = steps[currentStep];
      if (!activeStepEl) return;
      const cards = activeStepEl.querySelectorAll(".option-card");
      const idx = parseInt(key, 10) - 1;
      if (cards[idx]) {
        e.preventDefault();
        const radio = cards[idx].querySelector("input[type='radio']");
        if (radio) {
          radio.checked = true;
          radio.dispatchEvent(new Event("change", { bubbles: true }));
        }
      }
    } else if (key === "ArrowLeft" && currentStep > 0) {
      e.preventDefault();
      currentStep--;
      showStep(currentStep);
    } else if (key === "ArrowRight" && currentStep < totalSteps - 1 && isStepAnswered(currentStep)) {
      e.preventDefault();
      currentStep++;
      showStep(currentStep);
    }
  });

  // Next button click handler
  if (btnNext) {
    btnNext.addEventListener("click", () => {
      const valMsg = document.getElementById(`validationMsg-${currentStep}`);

      if (!isStepAnswered(currentStep)) {
        if (valMsg) {
          valMsg.style.display = "block";
          valMsg.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        return;
      }

      if (valMsg) valMsg.style.display = "none";

      if (currentStep < totalSteps - 1) {
        currentStep++;
        showStep(currentStep);
        window.scrollTo({ top: form.offsetTop - 80, behavior: "smooth" });
      }
    });
  }

  // Back button click handler
  if (btnPrev) {
    btnPrev.addEventListener("click", () => {
      const valMsg = document.getElementById(`validationMsg-${currentStep}`);
      if (valMsg) valMsg.style.display = "none";

      if (currentStep > 0) {
        currentStep--;
        showStep(currentStep);
        window.scrollTo({ top: form.offsetTop - 80, behavior: "smooth" });
      }
    });
  }

  // Form submission handler: protect against double clicks
  form.addEventListener("submit", (e) => {
    if (!isStepAnswered(currentStep)) {
      e.preventDefault();
      const valMsg = document.getElementById(`validationMsg-${currentStep}`);
      if (valMsg) valMsg.style.display = "block";
      return;
    }

    if (btnSubmit) {
      btnSubmit.disabled = true;
      const btnText = btnSubmit.querySelector(".btn-text");
      if (btnText) {
        btnText.textContent = isNepali ? "योजना बन्दैछ…" : "Building your plan…";
      }
    }
  });

  // Duration pills selection handler
  const durationBtns = document.querySelectorAll(".duration-pill-btn");
  const tripDaysInput = document.getElementById("tripDaysInput");
  const startDateInput = document.getElementById("startDateInput");
  const endDateInput = document.getElementById("endDateInput");

  durationBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      durationBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const days = btn.getAttribute("data-days");
      if (tripDaysInput) tripDaysInput.value = days;
    });
  });

  // Calculate days if dates are picked
  function updateDaysFromDates() {
    if (!startDateInput || !endDateInput || !tripDaysInput) return;
    const startVal = startDateInput.value;
    const endVal = endDateInput.value;
    if (startVal && endVal) {
      const s = new Date(startVal);
      const e = new Date(endVal);
      const diffDays = Math.round((e - s) / (1000 * 3600 * 24));
      if (diffDays >= 1) {
        const clamped = Math.max(1, Math.min(7, diffDays));
        tripDaysInput.value = clamped;
        durationBtns.forEach((b) => {
          b.classList.toggle("active", b.getAttribute("data-days") === String(clamped));
        });
      }
    }
  }

  if (startDateInput) startDateInput.addEventListener("change", updateDaysFromDates);
  if (endDateInput) endDateInput.addEventListener("change", updateDaysFromDates);

  // Scope card selection
  const scopeCards = document.querySelectorAll(".scope-option-card");
  scopeCards.forEach((card) => {
    card.addEventListener("click", () => {
      scopeCards.forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      const radio = card.querySelector("input[type='radio']");
      if (radio) {
        radio.checked = true;
      }
    });
  });

  // Initialize first step and initial dossier
  updateLiveDossier();
  showStep(currentStep);
});
