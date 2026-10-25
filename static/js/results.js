/**
 * VibeTrip - Results Page Interactive Monograph
 * Handles cultural audio phrasebook, interactive Leaflet map sync,
 * day filtering, sequential transit ribbon, scrollytelling highlights,
 * Gemini AI itinerary synthesis modal, and print/share actions.
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- 1. Audio Phrasebook native pronunciations & cultural chime ---
  const audioButtons = document.querySelectorAll('.phrase-audio-btn');
  audioButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const phrase = btn.getAttribute('data-phrase') || btn.textContent.trim();
      if (!phrase) return;

      // Highlight card border and trigger active pulse animation
      audioButtons.forEach(b => b.classList.remove('is-playing', 'playing'));
      btn.classList.add('is-playing', 'playing');

      // Play soft harmonic meditation chime (528 Hz) via Web Audio API
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          const ctx = new AudioCtx();
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = "sine";
          osc.frequency.setValueAtTime(528, ctx.currentTime);
          gain.gain.setValueAtTime(0.04, ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.8);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start();
          osc.stop(ctx.currentTime + 0.8);
        }
      } catch (e) {
        // Safe fallback if audio context restricted by user agent
      }

      // Pronounce word via SpeechSynthesis if available
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(phrase);
        utterance.rate = 0.85;
        utterance.pitch = 1.0;

        const voices = window.speechSynthesis.getVoices();
        const neVoice = voices.find(v => v.lang.startsWith("ne") || v.lang.startsWith("hi"));
        if (neVoice) utterance.voice = neVoice;

        utterance.onend = () => {
          btn.classList.remove('is-playing', 'playing');
        };
        utterance.onerror = () => {
          btn.classList.remove('is-playing', 'playing');
        };

        // Fallback timer in case speech synthesis event is suppressed
        setTimeout(() => {
          btn.classList.remove('is-playing', 'playing');
        }, 2200);

        window.speechSynthesis.speak(utterance);
      } else {
        setTimeout(() => {
          btn.classList.remove('is-playing', 'playing');
        }, 800);
      }
    });
  });
  // --- 2. Interactive Leaflet Sticky Map with Day Filtering & Route Polylines ---
  let map = null;
  let allMarkers = [];
  let routePolyline = null;

  const stopCards = Array.from(document.querySelectorAll('.stop-card'));
  const dayTabButtons = document.querySelectorAll('.day-tab-btn');
  const sequentialRouteChain = document.getElementById('sequentialRouteChain');
  const mapDayIndicator = document.getElementById('mapDayIndicator');
  const mapStopsCount = document.getElementById('mapStopsCount');
  const btnResetMapView = document.getElementById('btnResetMapView');

  // Devanagari digit converter for client-side labels
  const devanagariDigits = {"0": "०", "1": "१", "2": "२", "3": "३", "4": "४", "5": "५", "6": "६", "7": "७", "8": "८", "9": "९"};
  function toDevanagari(num) {
    const s = num < 10 ? "0" + num : "" + num;
    return s.split("").map(c => devanagariDigits[c] || c).join("");
  }

  if (typeof L !== 'undefined' && document.getElementById('valleyResultsMap')) {
    try {
      map = L.map('valleyResultsMap', {
        center: [27.705, 85.34],
        zoom: 12,
        scrollWheelZoom: false
      });

      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
      }).addTo(map);

      // Initialize markers for all cards
      stopCards.forEach((card) => {
        const idx = parseInt(card.getAttribute('data-stop-idx'), 10);
        const day = parseInt(card.getAttribute('data-day'), 10);
        const lat = parseFloat(card.getAttribute('data-lat'));
        const lng = parseFloat(card.getAttribute('data-lng'));
        const title = card.getAttribute('data-title') || `Stop ${idx}`;

        if (!isNaN(lat) && !isNaN(lng)) {
          const devNum = toDevanagari(idx);
          const customIcon = L.divIcon({
            className: 'custom-leaflet-ink-marker',
            html: `<div style="background: #B84A27; color: #FFFFFF; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: sans-serif; font-weight: 700; font-size: 11px; border: 2px solid #FFFDF9; box-shadow: 0 2px 8px rgba(30,27,24,0.3);">${devNum}</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
          });

          const marker = L.marker([lat, lng], { icon: customIcon });
          marker.bindPopup(`<strong>यात्रा ${devNum} • ${title}</strong><br><small>Day ${day}</small>`);

          marker.on('click', () => {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            highlightActiveStop(idx);
          });

          allMarkers.push({
            marker: marker,
            card: card,
            day: day,
            idx: idx,
            lat: lat,
            lng: lng,
            title: title
          });
        }
      });
    } catch (err) {
      console.warn("Leaflet map initialization warning:", err);
    }
  }

  // Function to render active day markers, polyline, and sequential transit chain
  let currentActiveDay = 1;

  function renderDayState(selectedDay) {
    currentActiveDay = selectedDay;

    // 1. Filter visible cards
    let visibleCards = [];
    stopCards.forEach(card => {
      const cardDay = parseInt(card.getAttribute('data-day'), 10);
      const isVisible = (selectedDay === 'all' || cardDay === parseInt(selectedDay, 10));
      card.style.display = isVisible ? 'block' : 'none';
      if (isVisible) visibleCards.push(card);
    });

    // 2. Render Sequential Route Chain on the sticky subnav
    if (sequentialRouteChain) {
      sequentialRouteChain.innerHTML = '';
      visibleCards.forEach((c, i) => {
        const idx = parseInt(c.getAttribute('data-stop-idx'), 10);
        const title = c.getAttribute('data-title') || `Stop ${idx}`;
        const transitNext = c.getAttribute('data-transit-next');

        const nodeBtn = document.createElement('button');
        nodeBtn.type = 'button';
        nodeBtn.className = 'route-chain-node' + (i === 0 ? ' is-active' : '');
        nodeBtn.setAttribute('data-target-idx', idx);
        nodeBtn.title = title;
        nodeBtn.innerHTML = `<span class="node-idx">${toDevanagari(idx)}</span> <span class="node-label">${title}</span>`;
        nodeBtn.addEventListener('click', () => {
          c.scrollIntoView({ behavior: 'smooth', block: 'center' });
          highlightActiveStop(idx);
        });
        sequentialRouteChain.appendChild(nodeBtn);

        // Transit line between stops
        if (i < visibleCards.length - 1 && transitNext) {
          const transitEl = document.createElement('span');
          transitEl.className = 'route-chain-transit';
          transitEl.innerHTML = `── <em>${transitNext}</em> ──▸`;
          sequentialRouteChain.appendChild(transitEl);
        }
      });
    }

    // 3. Update Map Markers and Polyline
    if (map) {
      // Remove all current markers
      allMarkers.forEach(item => {
        if (map.hasLayer(item.marker)) {
          map.removeLayer(item.marker);
        }
      });

      if (routePolyline && map.hasLayer(routePolyline)) {
        map.removeLayer(routePolyline);
      }

      const activePoints = [];
      allMarkers.forEach(item => {
        const isVisible = (selectedDay === 'all' || item.day === parseInt(selectedDay, 10));
        if (isVisible) {
          item.marker.addTo(map);
          activePoints.push([item.lat, item.lng]);
        }
      });

      // Draw active polyline
      if (activePoints.length > 1) {
        routePolyline = L.polyline(activePoints, {
          color: '#B84A27',
          weight: 3.5,
          dashArray: '6, 8',
          opacity: 0.85
        }).addTo(map);

        map.fitBounds(L.latLngBounds(activePoints), { padding: [40, 40] });
      } else if (activePoints.length === 1) {
        map.setView(activePoints[0], 14);
      }

      // Update map header labels
      if (mapDayIndicator) {
        mapDayIndicator.textContent = selectedDay === 'all' ? 'Full Valley Loop' : `Day ${selectedDay < 10 ? '0' + selectedDay : selectedDay} Route`;
      }
      if (mapStopsCount) {
        mapStopsCount.textContent = `${activePoints.length} Stops Active`;
      }
    }
  }

  // Day Tab Click Handlers
  dayTabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      dayTabButtons.forEach(b => {
        b.classList.remove('is-active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('is-active');
      btn.setAttribute('aria-selected', 'true');

      const dayVal = btn.getAttribute('data-day');
      renderDayState(dayVal);
    });
  });

  // Initial render for Day 01
  renderDayState(1);

  // Reset View button handler
  if (btnResetMapView && map) {
    btnResetMapView.addEventListener('click', () => {
      const activePoints = allMarkers
        .filter(item => currentActiveDay === 'all' || item.day === parseInt(currentActiveDay, 10))
        .map(item => [item.lat, item.lng]);
      if (activePoints.length > 1) {
        map.fitBounds(L.latLngBounds(activePoints), { padding: [40, 40] });
      } else if (activePoints.length === 1) {
        map.setView(activePoints[0], 14);
      }
    });
  }
  // --- 3. Highlight Stop & Scroll-to-Map Sync ---
  function highlightActiveStop(stopIndex) {
    // 1. Highlight card
    stopCards.forEach(c => {
      const idx = parseInt(c.getAttribute('data-stop-idx'), 10);
      c.classList.toggle('is-active', idx === stopIndex);
    });

    // 2. Highlight node in sequential route ribbon
    const chainNodes = document.querySelectorAll('.route-chain-node');
    chainNodes.forEach(node => {
      const idx = parseInt(node.getAttribute('data-target-idx'), 10);
      node.classList.toggle('is-active', idx === stopIndex);
    });

    // 3. Pan and focus map marker
    const targetItem = allMarkers.find(item => item.idx === stopIndex);
    if (targetItem && map) {
      map.flyTo([targetItem.lat, targetItem.lng], 15, { duration: 0.8 });
      targetItem.marker.openPopup();
    }
  }

  // "Focus on Valley Map" buttons inside cards
  const focusButtons = document.querySelectorAll('.btn-focus-stop-map');
  focusButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.getAttribute('data-stop-idx'), 10);
      highlightActiveStop(idx);

      // On mobile viewports, scroll smoothly to the map container
      if (window.innerWidth <= 1024) {
        const mapWrapper = document.querySelector('.sticky-map-wrapper');
        if (mapWrapper) {
          mapWrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    });
  });
  // --- 4. Scrollytelling IntersectionObserver (threshold 0.45) ---
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const idx = parseInt(entry.target.getAttribute('data-stop-idx'), 10);
          highlightActiveStop(idx);
        }
      });
    }, {
      root: null,
      threshold: 0.45
    });

    stopCards.forEach(card => observer.observe(card));
  }
  // --- 5. Gemini AI Popover / Modal Handlers ---
  const btnOpenGeminiModal = document.getElementById('btnOpenGeminiModal');
  const btnCloseGeminiModal = document.getElementById('btnCloseGeminiModal');
  const btnCancelGeminiModal = document.getElementById('btnCancelGeminiModal');
  const geminiModalBackdrop = document.getElementById('geminiModalBackdrop');
  const btnSubmitGeminiEnhance = document.getElementById('btnSubmitGeminiEnhance');
  const geminiApiKeyField = document.getElementById('geminiApiKeyField');
  const geminiModalStatus = document.getElementById('geminiModalStatus');
  const heroPhilosophyText = document.getElementById('heroPhilosophyText');

  function openGeminiModal() {
    if (geminiModalBackdrop) {
      geminiModalBackdrop.classList.add('is-open');
      if (geminiApiKeyField) geminiApiKeyField.focus();
    }
  }

  function closeGeminiModal() {
    if (geminiModalBackdrop) {
      geminiModalBackdrop.classList.remove('is-open');
    }
  }

  if (btnOpenGeminiModal) btnOpenGeminiModal.addEventListener('click', openGeminiModal);
  if (btnCloseGeminiModal) btnCloseGeminiModal.addEventListener('click', closeGeminiModal);
  if (btnCancelGeminiModal) btnCancelGeminiModal.addEventListener('click', closeGeminiModal);

  if (geminiModalBackdrop) {
    geminiModalBackdrop.addEventListener('click', (e) => {
      if (e.target === geminiModalBackdrop) closeGeminiModal();
    });
  }

  // HTML escaping utility for safe DOM injection
  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  if (btnSubmitGeminiEnhance) {
    btnSubmitGeminiEnhance.addEventListener('click', async () => {
      const planId = btnSubmitGeminiEnhance.getAttribute('data-plan-id');
      const apiKey = geminiApiKeyField ? geminiApiKeyField.value.trim() : '';

      btnSubmitGeminiEnhance.disabled = true;
      btnSubmitGeminiEnhance.textContent = '✦ Synthesizing...';
      if (geminiModalStatus) {
        geminiModalStatus.style.display = 'block';
        geminiModalStatus.style.color = '#B35817';
        geminiModalStatus.textContent = 'Contacting Google Gemini 2.5 Flash to synthesize tailored guidance...';
      }

      try {
        const resp = await fetch('/api/gemini/enhance_plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ plan_id: planId, api_key: apiKey })
        });

        const resData = await resp.json();
        if (resData.success && (resData.narrative || resData.plan)) {
          const nar = resData.narrative || (resData.plan && resData.plan.personalized_narrative) || {};

          // 1. Update Hero Philosophy Text
          const philText = nar.philosophy_of_journey || nar.journey_philosophy;
          if (heroPhilosophyText && philText) {
            heroPhilosophyText.textContent = philText;
          }

          // 2. Update Hero Persona Tagline
          const heroTaglineEl = document.getElementById('heroPersonaTagline') || document.querySelector('.hero-persona-tagline');
          if (heroTaglineEl && nar.bespoke_headline) {
            heroTaglineEl.textContent = `“${nar.bespoke_headline.replace(/^“|”$/g, '')}”`;
          }

          // 3. Update Hero Rhythm Advice
          let rhythmEl = document.getElementById('heroRhythmText');
          if (!rhythmEl) {
            const philBox = document.querySelector('.hero-editorial-philosophy');
            if (philBox) {
              rhythmEl = document.createElement('p');
              rhythmEl.className = 'hero-rhythm-inline';
              rhythmEl.id = 'heroRhythmText';
              philBox.appendChild(rhythmEl);
            }
          }
          if (rhythmEl && nar.local_rhythm_advice) {
            const contentSpan = rhythmEl.querySelector('.rhythm-content');
            if (contentSpan) {
              contentSpan.textContent = nar.local_rhythm_advice;
            } else {
              rhythmEl.innerHTML = `<strong>Local Rhythm Advice:</strong> <span class="rhythm-content">${escapeHtml(nar.local_rhythm_advice)}</span>`;
            }
            rhythmEl.style.display = 'block';
          }

          // 4. Update Hero Golden Rule
          let goldenEl = document.getElementById('heroGoldenRuleText');
          if (!goldenEl) {
            const philBox = document.querySelector('.hero-editorial-philosophy');
            if (philBox) {
              goldenEl = document.createElement('p');
              goldenEl.className = 'hero-golden-rule-inline';
              goldenEl.id = 'heroGoldenRuleText';
              philBox.appendChild(goldenEl);
            }
          }
          if (goldenEl && nar.golden_rule) {
            const cleanRule = nar.golden_rule.replace(/^[✦\s*]+/, '');
            const contentSpan = goldenEl.querySelector('.golden-rule-content');
            if (contentSpan) {
              contentSpan.textContent = cleanRule;
            } else {
              goldenEl.innerHTML = `✦ <span class="golden-rule-content">${escapeHtml(cleanRule)}</span>`;
            }
            goldenEl.style.display = 'block';
          }

          // 5. Update Stop Card Directives across all days and slots
          if (resData.plan && Array.isArray(resData.plan.days)) {
            const daysMap = {};
            resData.plan.days.forEach(d => {
              daysMap[d.day] = d.slots || {};
            });

            stopCards.forEach(card => {
              const dNum = parseInt(card.getAttribute('data-day'), 10);
              const sName = card.getAttribute('data-slot');
              const daySlots = daysMap[dNum];
              if (daySlots && daySlots[sName]) {
                const slot = daySlots[sName];

                // Update Directive Copy
                const directiveText = slot.first_30_min || slot.what_to_do || slot.reason;
                const directiveCopyEl = card.querySelector('.directive-copy');
                if (directiveCopyEl && directiveText) {
                  directiveCopyEl.textContent = directiveText;
                }

                // Update Why-line
                if (slot.why_for_you) {
                  let whyEl = card.querySelector('.stop-monograph-why');
                  if (!whyEl) {
                    const leadRow = card.querySelector('.stop-editorial-lead-row');
                    if (leadRow) {
                      whyEl = document.createElement('p');
                      whyEl.className = 'stop-monograph-why';
                      leadRow.parentNode.insertBefore(whyEl, leadRow);
                    }
                  }
                  if (whyEl) {
                    whyEl.innerHTML = `<span class="why-glyph">✦</span> <em>Why this fits your rhythm: ${escapeHtml(slot.why_for_you)}</em>`;
                    whyEl.style.display = 'block';
                  }
                }

                // Update Taste & Sit matrix cell if present
                const tasteText = slot.taste_and_sit || slot.taste_pairing;
                if (tasteText) {
                  const tasteEl = card.querySelector('.matrix-cell-left.matrix-cell-top .matrix-text');
                  if (tasteEl) tasteEl.textContent = tasteText;
                }

                // Update Insider Secret matrix cell if present
                if (slot.insider_secret) {
                  const secretEl = card.querySelector('.matrix-cell-right.matrix-cell-top .matrix-text');
                  if (secretEl) secretEl.textContent = slot.insider_secret;
                }
              }
            });
          }

          if (geminiModalStatus) {
            geminiModalStatus.style.color = '#3F522C';
            geminiModalStatus.textContent = nar.is_ai_generated 
              ? '✓ Successfully synthesized travel narrative with Google Gemini!' 
              : '✓ Refined with authentic local editorial guidance.';
          }

          setTimeout(() => {
            closeGeminiModal();
          }, 1400);
        } else {
          throw new Error(resData.error || 'Failed to synthesize plan');
        }
      } catch (err) {
        if (geminiModalStatus) {
          geminiModalStatus.style.color = '#B84A27';
          geminiModalStatus.textContent = 'Note: Could not reach Gemini (' + err.message + '). Standard editorial guidance is active.';
        }
      } finally {
        btnSubmitGeminiEnhance.disabled = false;
        btnSubmitGeminiEnhance.textContent = '✦ Synthesize Dossier';
      }
    });
  }
  // --- 6. Print & Share actions ---
  const btnPrint = document.getElementById('btnPrint');
  if (btnPrint) {
    btnPrint.addEventListener('click', () => {
      // Expand all days before printing so the complete monograph is printed
      if (typeof renderDayState === 'function') {
        renderDayState('all');
      }
      setTimeout(() => {
        window.print();
      }, 250);
    });
  }

  const btnShare = document.getElementById('btnShare');
  const shareToast = document.getElementById('shareToast');
  if (btnShare && shareToast) {
    btnShare.addEventListener('click', async () => {
      const currentUrl = window.location.href;
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(currentUrl);
        } else {
          const tempInput = document.createElement('textarea');
          tempInput.value = currentUrl;
          tempInput.style.position = 'fixed';
          tempInput.style.left = '-9999px';
          document.body.appendChild(tempInput);
          tempInput.focus();
          tempInput.select();
          document.execCommand('copy');
          document.body.removeChild(tempInput);
        }
        shareToast.classList.add('show');
        setTimeout(() => {
          shareToast.classList.remove('show');
        }, 2600);
      } catch (err) {
        console.warn('Clipboard copy fallback:', err);
        prompt('Copy trip link:', currentUrl);
      }
    });
  }
});
