/**
 * VibeTrip - Main Application Scripts
 * Manages theme persistence, responsive navigation, scroll reveals,
 * and tour research note interactions.
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- 1. Theme Persistence & Switcher ---
  const themeToggle = document.getElementById("themeToggle");
  const htmlRoot = document.documentElement;

  let savedTheme = localStorage.getItem("vibetrip-theme");
  if (!savedTheme || savedTheme === "dark" || savedTheme === "linear-dark") {
    savedTheme = "paper-cream";
    localStorage.setItem("vibetrip-theme", "paper-cream");
  }
  htmlRoot.setAttribute("data-theme", savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const currentTheme = htmlRoot.getAttribute("data-theme");
      const nextTheme = currentTheme === "paper-cream" ? "warm-editorial" : "paper-cream";
      htmlRoot.setAttribute("data-theme", nextTheme);
      localStorage.setItem("vibetrip-theme", nextTheme);
    });
  }

  // --- 2. Mobile Navigation Drawer ---
  const navToggle = document.getElementById("navToggle");
  const primaryNav = document.getElementById("primaryNav");

  if (navToggle && primaryNav) {
    navToggle.addEventListener("click", () => {
      const isExpanded = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", !isExpanded);
      primaryNav.classList.toggle("is-open", !isExpanded);
    });

    document.addEventListener("click", (e) => {
      if (!navToggle.contains(e.target) && !primaryNav.contains(e.target) && primaryNav.classList.contains("is-open")) {
        navToggle.setAttribute("aria-expanded", "false");
        primaryNav.classList.remove("is-open");
      }
    });
  }

  // --- 3. Sticky Header Scroll Response ---
  const siteHeader = document.querySelector(".site-header");
  if (siteHeader) {
    const handleHeaderScroll = () => {
      if (window.scrollY > 40) {
        siteHeader.classList.add("is-scrolled");
      } else {
        siteHeader.classList.remove("is-scrolled");
      }
    };
    window.addEventListener("scroll", handleHeaderScroll, { passive: true });
    handleHeaderScroll();
  }

  // --- 4. Scroll Reveal Animations ---
  const revealElements = document.querySelectorAll(".reveal");
  const prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (window.navigator.webdriver || prefersReduced) {
    revealElements.forEach((el) => el.classList.add("visible"));
  } else if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px 200px 0px" }
    );
    revealElements.forEach((el) => observer.observe(el));
  } else {
    revealElements.forEach((el) => el.classList.add("visible"));
  }

  // --- 5. Shared Navbar Badge Helper ---
  function updateNavBadge(count) {
    let navBadge = document.querySelector(".nav-saved-badge");
    const tourLink = document.querySelector(".nav-btn-tour");
    if (count > 0) {
      if (!navBadge && tourLink) {
        navBadge = document.createElement("span");
        navBadge.className = "nav-saved-badge";
        tourLink.appendChild(navBadge);
      }
      if (navBadge) {
        navBadge.textContent = count;
        navBadge.style.display = "inline-flex";
      }
    } else if (navBadge) {
      navBadge.style.display = "none";
    }
  }

  // --- 6. Place Detail: Wishlist Toggle ---
  const savePlaceForm = document.getElementById("savePlaceForm");
  const savePlaceBtn = document.getElementById("savePlaceBtn");

  if (savePlaceForm && savePlaceBtn) {
    savePlaceForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formUrl = savePlaceForm.getAttribute("action");
      const iconSpan = savePlaceBtn.querySelector(".save-icon");
      const textSpan = savePlaceBtn.querySelector(".save-text");

      try {
        const response = await fetch(formUrl, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json",
          },
        });

        if (response.status === 401) {
          const data = await response.json();
          window.location.href = data.redirect || "/login";
          return;
        }

        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            const isSaved = Boolean(data.is_saved);
            savePlaceBtn.classList.toggle("is-saved", isSaved);
            savePlaceBtn.setAttribute("aria-pressed", isSaved ? "true" : "false");

            if (iconSpan) {
              iconSpan.innerHTML = isSaved
                ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`
                : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`;
            }
            if (textSpan) {
              textSpan.textContent = isSaved ? "Saved in Tour Notes" : "Save to Wishlist";
            }
            updateNavBadge(data.count);
          }
        } else {
          console.error("Save place failed with status:", response.status);
        }
      } catch (err) {
        console.error("AJAX error while saving place:", err);
      }
    });
  }

  // --- 7. My Tour Dashboard: Tab Navigation & Note Saving ---
  const tourTabs = document.querySelectorAll(".tour-tab-btn");
  const sectionSavedPlaces = document.getElementById("saved-places");
  const sectionSavedPlans = document.getElementById("saved-plans");

  if (tourTabs.length && (sectionSavedPlaces || sectionSavedPlans)) {
    tourTabs.forEach((tab) => {
      tab.addEventListener("click", (e) => {
        e.preventDefault();
        const href = tab.getAttribute("href") || "";
        const targetId = href.replace("#", "");

        tourTabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");

        if (targetId === "saved-places") {
          if (sectionSavedPlaces) sectionSavedPlaces.style.display = "block";
          if (sectionSavedPlans) sectionSavedPlans.style.display = "none";
        } else if (targetId === "saved-plans") {
          if (sectionSavedPlaces) sectionSavedPlaces.style.display = "none";
          if (sectionSavedPlans) sectionSavedPlans.style.display = "block";
        }
      });
    });

    if (sectionSavedPlaces && sectionSavedPlans) {
      sectionSavedPlans.style.display = "none";
    }
  }

  document.querySelectorAll(".inline-note-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const saveBtn = form.querySelector(".btn-dashboard-save-note, .btn-save-inline-note");
      const originalText = saveBtn ? saveBtn.innerHTML : "Save";
      const formData = new FormData(form);

      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = "Saving...";
      }

      try {
        const response = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
          body: formData,
        });

        if (response.ok) {
          if (saveBtn) {
            saveBtn.innerHTML = "<span>Saved!</span>";
            saveBtn.style.background = "#059669";
            setTimeout(() => {
              saveBtn.innerHTML = originalText;
              saveBtn.style.background = "";
              saveBtn.disabled = false;
            }, 2000);
          }
        } else {
          console.error("Failed to save note. Server returned:", response.status);
          if (saveBtn) {
            saveBtn.innerHTML = "<span>Retry</span>";
            setTimeout(() => {
              saveBtn.innerHTML = originalText;
              saveBtn.disabled = false;
            }, 2000);
          }
        }
      } catch (err) {
        console.error("Network error while saving note:", err);
        if (saveBtn) {
          saveBtn.innerHTML = originalText;
          saveBtn.disabled = false;
        }
      }
    });
  });
});
