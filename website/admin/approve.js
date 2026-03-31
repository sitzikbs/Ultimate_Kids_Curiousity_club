/**
 * Outline Approval - View/edit story beats and approve or reject
 */

const API_BASE_URL = 'http://localhost:8000';

let currentEpisodeId = null;
let episodeData = null;
let editMode = false;
let confirmModal = null;
let pendingAction = null;

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    currentEpisodeId = urlParams.get('episode_id');

    if (!currentEpisodeId) {
        showToast('Error: No episode ID specified', 'danger');
        return;
    }

    confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));

    // Wire confirm modal OK button
    document.getElementById('confirmModalOk').addEventListener('click', () => {
        confirmModal.hide();
        if (pendingAction) {
            const action = pendingAction;
            pendingAction = null;
            executeAction(action);
        }
    });

    loadEpisode();
});

/**
 * Load episode from API
 */
async function loadEpisode() {
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/episodes/${currentEpisodeId}`);
        if (!response.ok) throw new Error(response.statusText);

        episodeData = await response.json();
        renderEpisodeHeader();
        renderStoryBeats(false);

        document.getElementById('approve-container').style.display = 'block';
    } catch (error) {
        showToast(`Error loading episode: ${error.message}`, 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Render episode header with title and metadata
 */
function renderEpisodeHeader() {
    const ep = episodeData;
    document.getElementById('episode-title').textContent = `Review: ${ep.title || ep.topic}`;
    document.getElementById('episode-meta').textContent =
        `Show: ${ep.show_id} | Topic: ${ep.topic} | Stage: ${ep.current_stage}`;

    if (ep.outline && ep.outline.educational_concept) {
        document.getElementById('educational-concept').textContent =
            `Educational focus: ${ep.outline.educational_concept}`;
    }
}

/**
 * Render story beats in view or edit mode
 */
function renderStoryBeats(editable) {
    const container = document.getElementById('story-beats-container');
    const outline = episodeData.outline;

    if (!outline || !outline.story_beats || outline.story_beats.length === 0) {
        container.innerHTML = '<p class="text-muted">No story beats available.</p>';
        return;
    }

    container.innerHTML = outline.story_beats.map((beat, i) => {
        const num = beat.beat_number || (i + 1);

        if (editable) {
            return `
                <div class="beat-card editing" data-beat-number="${num}">
                    <div class="d-flex align-items-center mb-2">
                        <span class="beat-number">${num}</span>
                        <input type="text" class="form-control beat-title-input"
                               value="${escapeHtml(beat.title || '')}" placeholder="Beat title">
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Description</label>
                        <textarea class="form-control beat-description-input" rows="3"
                                  placeholder="Beat description">${escapeHtml(beat.description || '')}</textarea>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Educational Focus</label>
                        <input type="text" class="form-control beat-edu-focus-input"
                               value="${escapeHtml(beat.educational_focus || '')}" placeholder="Educational focus">
                    </div>
                    <div>
                        <label class="form-label">Key Moments</label>
                        <div class="beat-key-moments-list">
                            ${(beat.key_moments || []).map((m, j) => `
                                <div class="input-group mb-1">
                                    <input type="text" class="form-control beat-key-moment" value="${escapeHtml(m)}">
                                    <button class="btn btn-outline-danger btn-sm" type="button"
                                            onclick="this.parentElement.remove()">X</button>
                                </div>
                            `).join('')}
                        </div>
                        <button class="btn btn-sm btn-outline-primary mt-1" type="button"
                                onclick="addKeyMoment(this)">+ Add Moment</button>
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="beat-card" data-beat-number="${num}">
                    <div class="d-flex align-items-center mb-1">
                        <span class="beat-number">${num}</span>
                        <span class="beat-title">${escapeHtml(beat.title || `Beat ${num}`)}</span>
                    </div>
                    <p class="beat-description">${escapeHtml(beat.description || '')}</p>
                    ${beat.educational_focus ? `<p class="beat-edu-focus">Educational: ${escapeHtml(beat.educational_focus)}</p>` : ''}
                    ${beat.key_moments && beat.key_moments.length > 0 ? `
                        <div class="beat-key-moments">
                            <strong style="font-size: 0.85rem;">Key moments:</strong>
                            <ul class="mb-0">
                                ${beat.key_moments.map(m => `<li>${escapeHtml(m)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }
    }).join('');
}

/**
 * Toggle between view and edit mode
 */
function toggleEditMode() {
    editMode = !editMode;
    const btn = document.getElementById('toggle-edit-btn');
    const approveEditsBtn = document.getElementById('approve-edits-btn');

    if (editMode) {
        btn.textContent = 'Cancel Editing';
        btn.classList.remove('btn-outline-primary');
        btn.classList.add('btn-outline-danger');
        approveEditsBtn.style.display = 'inline-block';
    } else {
        btn.textContent = 'Edit Beats';
        btn.classList.remove('btn-outline-danger');
        btn.classList.add('btn-outline-primary');
        approveEditsBtn.style.display = 'none';
    }

    renderStoryBeats(editMode);
}

/**
 * Collect edited beats from the form
 */
function collectEditedBeats() {
    const beats = [];
    document.querySelectorAll('#story-beats-container [data-beat-number]').forEach(card => {
        const moments = [];
        card.querySelectorAll('.beat-key-moment').forEach(inp => {
            const v = inp.value.trim();
            if (v) moments.push(v);
        });

        beats.push({
            beat_number: parseInt(card.dataset.beatNumber),
            title: card.querySelector('.beat-title-input').value.trim(),
            description: card.querySelector('.beat-description-input').value.trim(),
            educational_focus: card.querySelector('.beat-edu-focus-input').value.trim(),
            key_moments: moments
        });
    });
    return beats;
}

/**
 * Add a key moment input to a beat card
 */
function addKeyMoment(btn) {
    const list = btn.previousElementSibling;
    const html = `
        <div class="input-group mb-1">
            <input type="text" class="form-control beat-key-moment" placeholder="Key moment">
            <button class="btn btn-outline-danger btn-sm" type="button"
                    onclick="this.parentElement.remove()">X</button>
        </div>
    `;
    list.insertAdjacentHTML('beforeend', html);
}

/**
 * Save outline edits to the backend
 */
async function saveOutlineEdits() {
    const beats = collectEditedBeats();
    const updatedOutline = { ...episodeData.outline, story_beats: beats };

    const response = await fetch(`${API_BASE_URL}/api/episodes/${currentEpisodeId}/outline`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ outline: updatedOutline })
    });

    if (!response.ok) throw new Error(`Failed to save outline: ${response.statusText}`);

    episodeData = await response.json();
}

/**
 * Submit approval or rejection
 */
async function submitApproval(approved) {
    const feedback = document.getElementById('approval-feedback').value.trim();

    const response = await fetch(`${API_BASE_URL}/api/episodes/${currentEpisodeId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved, feedback: feedback || null })
    });

    if (!response.ok) throw new Error(`Failed to submit: ${response.statusText}`);

    episodeData = await response.json();
}

/**
 * Show confirmation modal before acting
 */
function confirmAction(action) {
    // Validation: reject requires feedback
    if (action === 'reject') {
        const feedback = document.getElementById('approval-feedback').value.trim();
        if (!feedback) {
            showToast('Feedback is required when rejecting an outline.', 'warning');
            document.getElementById('approval-feedback').focus();
            return;
        }
    }

    const titles = {
        'approve': 'Approve Outline',
        'approve-edits': 'Save Edits & Approve',
        'reject': 'Reject Outline'
    };

    const bodies = {
        'approve': 'Approve this outline? The pipeline will proceed to segment generation automatically.',
        'approve-edits': 'Save your edits and approve? The pipeline will proceed with the modified outline.',
        'reject': 'Reject this outline? The episode will be sent back for regeneration.'
    };

    document.getElementById('confirmModalTitle').textContent = titles[action];
    document.getElementById('confirmModalBody').textContent = bodies[action];

    // Style the confirm button to match the action
    const okBtn = document.getElementById('confirmModalOk');
    okBtn.className = action === 'reject' ? 'btn btn-danger' : 'btn btn-success';

    pendingAction = action;
    confirmModal.show();
}

/**
 * Execute the confirmed action
 */
async function executeAction(action) {
    // Disable action buttons
    const btns = document.querySelectorAll('#approve-btn, #approve-edits-btn, #reject-btn');
    btns.forEach(b => { b.disabled = true; });

    try {
        if (action === 'approve-edits') {
            await saveOutlineEdits();
        }

        const approved = action !== 'reject';
        await submitApproval(approved);

        const msg = approved ? 'Outline approved!' : 'Outline rejected.';
        showToast(msg, approved ? 'success' : 'warning');

        // Redirect to dashboard after short delay
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1500);
    } catch (error) {
        showToast(`Error: ${error.message}`, 'danger');
        btns.forEach(b => { b.disabled = false; });
    }
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show/hide loading spinner
 */
function showLoading(show) {
    document.getElementById('loading-spinner').style.display = show ? 'block' : 'none';
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');

    const colorMap = {
        success: 'bg-success text-white',
        danger: 'bg-dark text-white border border-danger',
        warning: 'bg-warning text-dark',
        info: 'bg-info text-dark'
    };
    const colorClass = colorMap[type] || 'bg-secondary text-white';
    const closeBtnClass = (type === 'warning' || type === 'info') ? 'btn-close' : 'btn-close btn-close-white';

    const toast = document.createElement('div');
    toast.className = `toast align-items-center ${colorClass} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="${closeBtnClass} me-2 m-auto"
                    data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    if (typeof bootstrap !== 'undefined') {
        const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    } else {
        toast.style.display = 'block';
        setTimeout(() => toast.remove(), 5000);
    }
}
