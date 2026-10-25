/**
 * VibeTrip - Interactive Gallery System
 * Provides live debounced keyword search, active filter chip tags,
 * results counter, empty state handling, and URL deep linking.
 */

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("gallerySearch");
  const btnClearSearch = document.getElementById("btnClearSearch");
  const btnResetFilters = document.getElementById("btnResetFilters");
  const btnEmptyReset = document.getElementById("btnEmptyReset");
  const galleryCards = document.querySelectorAll(".gallery-card");
  const galleryCount = document.getElementById("galleryCount");
  const emptyState = document.getElementById("galleryEmptyState");
  const galleryGrid = document.getElementById("galleryGrid");
  const activeChipsContainer = document.getElementById("activeFilterChips");
  const chipsFlexRow = document.getElementById("chipsFlexRow");
  const btnClearAllChips = document.getElementById("btnClearAllChips");

  if (!galleryCards.length) return;

  let currentSearchQuery = "";
  let searchDebounceTimer = null;

  // Render Active Filter Chips
  function updateActiveChips() {
    if (!chipsFlexRow || !activeChipsContainer) return;
    chipsFlexRow.innerHTML = "";

    const query = currentSearchQuery.trim();
    if (query) {
      const searchPrefix = (activeChipsContainer.getAttribute("data-search-label") || "Search:").replace(":", "").trim();
      const chip = document.createElement("span");
      chip.className = "filter-chip-tag";
      chip.innerHTML = `${searchPrefix}: "${query}" <button type="button" class="chip-remove-btn" aria-label="Remove search filter">&times;</button>`;
      chip.querySelector(".chip-remove-btn").addEventListener("click", () => {
        if (searchInput) searchInput.value = "";
        if (btnClearSearch) btnClearSearch.style.display = "none";
        currentSearchQuery = "";
        applyFilters();
      });
      chipsFlexRow.appendChild(chip);
      activeChipsContainer.style.display = "flex";
    } else {
      activeChipsContainer.style.display = "none";
    }
  }

  // Filter cards based on keyword query
  function applyFilters() {
    let visibleCount = 0;
    const query = currentSearchQuery.trim().toLowerCase();

    galleryCards.forEach((card) => {
      const cardSearchText = card.getAttribute("data-search-terms") || "";
      const matchesSearch = !query || cardSearchText.includes(query);

      if (matchesSearch) {
        card.classList.remove("is-hidden");
        card.classList.add("visible");
        card.style.display = "";
        visibleCount++;
      } else {
        card.classList.add("is-hidden");
        card.classList.remove("visible");
        card.style.display = "none";
      }
    });

    if (galleryCount) {
      const total = galleryCards.length;
      const listedTmpl = galleryCount.getAttribute("data-listed-template") || `${total} Sanctuaries Listed`;
      const showingTmpl = galleryCount.getAttribute("data-showing-template") || `Showing ${visibleCount} of ${total} sanctuaries`;
      if (query) {
        galleryCount.textContent = showingTmpl.replace("__VISIBLE__", visibleCount).replace("__TOTAL__", total);
      } else {
        galleryCount.textContent = listedTmpl.replace("__COUNT__", total);
      }
    }

    if (visibleCount === 0) {
      if (emptyState) emptyState.style.display = "block";
      if (galleryGrid) galleryGrid.style.display = "none";
    } else {
      if (emptyState) emptyState.style.display = "none";
      if (galleryGrid) galleryGrid.style.display = "grid";
    }

    if (btnResetFilters) {
      btnResetFilters.style.display = query.length > 0 ? "inline-flex" : "none";
    }

    updateActiveChips();
  }

  // Search input events with 150ms debounce
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchDebounceTimer);
      const query = e.target.value;
      if (btnClearSearch) {
        btnClearSearch.style.display = query.length > 0 ? "block" : "none";
      }
      searchDebounceTimer = setTimeout(() => {
        currentSearchQuery = query;
        applyFilters();
      }, 150);
    });
  }

  if (btnClearSearch && searchInput) {
    btnClearSearch.addEventListener("click", () => {
      searchInput.value = "";
      btnClearSearch.style.display = "none";
      currentSearchQuery = "";
      applyFilters();
      searchInput.focus();
    });
  }

  // Reset all filters
  function resetAllFilters() {
    currentSearchQuery = "";
    if (searchInput) {
      searchInput.value = "";
      if (btnClearSearch) btnClearSearch.style.display = "none";
    }
    applyFilters();
  }

  if (btnResetFilters) btnResetFilters.addEventListener("click", resetAllFilters);
  if (btnEmptyReset) btnEmptyReset.addEventListener("click", resetAllFilters);
  if (btnClearAllChips) btnClearAllChips.addEventListener("click", resetAllFilters);

  // Deep linking via URL query parameter or hash
  const urlParams = new URLSearchParams(window.location.search);
  const qParam = urlParams.get("q") || urlParams.get("search");
  if (qParam && searchInput) {
    searchInput.value = qParam;
    if (btnClearSearch) btnClearSearch.style.display = "block";
    currentSearchQuery = qParam;
    applyFilters();
  }

  const currentHash = window.location.hash;
  if (currentHash && (currentHash.startsWith("#q=") || currentHash.startsWith("#search="))) {
    const hashQuery = decodeURIComponent(currentHash.split("=")[1] || "");
    if (hashQuery && searchInput) {
      searchInput.value = hashQuery;
      if (btnClearSearch) btnClearSearch.style.display = "block";
      currentSearchQuery = hashQuery;
      applyFilters();
    }
  }
});
