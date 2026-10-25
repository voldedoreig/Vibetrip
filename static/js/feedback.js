/**
 * VibeTrip - Feedback Form Helper
 * 
 * Manages live character counting with visual warnings near limit,
 * and handles interactive star rating state.
 */

document.addEventListener("DOMContentLoaded", () => {
  const commentInput = document.getElementById("feedbackComment");
  const charCounter = document.getElementById("charCounter");
  const maxLimit = 500;

  if (commentInput && charCounter) {
    const updateCounter = () => {
      const len = commentInput.value.length;
      charCounter.textContent = `${len} / ${maxLimit} characters`;

      if (len >= maxLimit * 0.9) {
        charCounter.classList.add("near-limit");
      } else {
        charCounter.classList.remove("near-limit");
      }
    };

    commentInput.addEventListener("input", updateCounter);
    // Initialize count
    updateCounter();
  }

  // Star Rating enhancement
  const starRadios = document.querySelectorAll(".star-radio");
  starRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
      // Announce for accessibility if needed
      const ratingVal = radio.value;
      radio.setAttribute("aria-checked", "true");
    });
  });
});
