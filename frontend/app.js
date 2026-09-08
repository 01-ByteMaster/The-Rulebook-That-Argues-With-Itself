/* Medicaps University — Rulebook QA
   Ask page interactions: input handling, /ask request, result rendering. */

(function () {
  const API_ENDPOINT = '/ask';

  const queryInput = document.getElementById('query-input');
  const submitBtn = document.getElementById('submit-btn');
  const resultsContainer = document.getElementById('results-container');

  // Auto-expand the textarea as the user types.
  queryInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 140) + 'px';
  });

  submitBtn.addEventListener('click', handleQuerySubmit);

  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuerySubmit();
    }
  });

  document.querySelectorAll('.chip').forEach((button) => {
    button.addEventListener('click', () => {
      queryInput.value = button.getAttribute('data-q');
      queryInput.style.height = 'auto';
      queryInput.style.height = queryInput.scrollHeight + 'px';
      queryInput.focus();
      handleQuerySubmit();
    });
  });

  async function handleQuerySubmit() {
    const question = queryInput.value.trim();
    if (!question) {
      queryInput.focus();
      return;
    }

    toggleLoading(true);
    renderLoadingSkeleton();

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`Server returned code ${response.status}`);
      }

      const data = await response.json();
      renderResponse(data);
    } catch (err) {
      renderErrorCard(err.message);
    } finally {
      toggleLoading(false);
    }
  }

  function toggleLoading(isLoading) {
    submitBtn.disabled = isLoading;
    submitBtn.classList.toggle('loading', isLoading);
  }

  function renderLoadingSkeleton() {
    resultsContainer.innerHTML = `
      <div class="output-card">
        <div class="sk-wrap">
          <div class="sk-bar" style="width: 30%;"></div>
          <div class="sk-bar" style="width: 95%;"></div>
          <div class="sk-bar" style="width: 88%;"></div>
          <div class="sk-bar" style="width: 62%;"></div>
        </div>
      </div>
    `;
  }

  function renderErrorCard(message) {
    resultsContainer.innerHTML = `
      <div class="output-card">
        <div class="status-stamp conflict">
          ${icon('alert-circle', 13)} Connection error
        </div>
        <p style="font-size: 0.9rem; color: var(--ink-soft);">
          ${escapeMarkup(message)} — make sure the backend is running at <code>${API_ENDPOINT}</code>.
        </p>
      </div>
    `;
    lucide.createIcons();
  }

  function renderResponse(data) {
    const { type, answer, passages, conflict_note } = data;

    const badgeMeta = {
      answered: { label: 'Verified answer', icon: 'check', cls: 'answered' },
      conflict: { label: 'Policy conflict detected', icon: 'alert-triangle', cls: 'conflict' },
      not_covered: { label: 'Not in rulebook', icon: 'help-circle', cls: 'not_covered' },
    }[type] || { label: type || 'Result', icon: 'info', cls: 'answered' };

    let html = '<div class="output-card">';

    html += `
      <div class="status-stamp ${badgeMeta.cls}">
        ${icon(badgeMeta.icon, 13)} ${badgeMeta.label}
      </div>
    `;

    if (conflict_note) {
      html += `
        <div class="conflict-box">
          ${icon('alert-circle', 17)}
          <div>${escapeMarkup(conflict_note)}</div>
        </div>
      `;
    }

    if (answer) {
      html += `<div class="answer-container">${escapeMarkup(answer)}</div>`;
    }

    if (type === 'not_covered') {
      html += `
        <div class="not-covered-note">
          This question isn't resolved by Medicaps University's current rulebook. Please check with Academic Affairs.
        </div>
      `;
    }

    if (passages && passages.length > 0 && type !== 'not_covered') {
      html += `<div class="sources-title">${icon('book', 13)} Cited passages</div>`;
      passages.forEach((p) => {
        html += `
          <div class="passage-item">
            <div class="passage-header">
              <span class="passage-tag">${escapeMarkup(p.section_id || 'Ref')}</span>
              <span class="passage-meta">${escapeMarkup(p.source_file || '')} · score ${Number(p.score || 0).toFixed(3)}</span>
            </div>
            <div class="passage-content">${escapeMarkup(p.text || '')}</div>
          </div>
        `;
      });
    }

    html += '</div>';
    resultsContainer.innerHTML = html;
    lucide.createIcons();
  }

  function icon(name, size) {
    return `<i data-lucide="${name}" width="${size}" height="${size}"></i>`;
  }

  function escapeMarkup(str) {
    if (!str) return '';
    const el = document.createElement('span');
    el.textContent = str;
    return el.innerHTML;
  }

  lucide.createIcons();
})();
