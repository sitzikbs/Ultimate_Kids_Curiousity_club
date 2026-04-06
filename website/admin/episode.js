/**
 * Episode Detail - Full episode view with stage timeline, outline, scripts, audio
 */

const API_BASE_URL = '';
const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

let currentEpisodeId = null;
let episodeData = null;
let ws = null;

const PIPELINE_ORDER = [
    'PENDING', 'IDEATION', 'OUTLINING', 'AWAITING_APPROVAL',
    'APPROVED', 'SEGMENT_GENERATION', 'SCRIPT_GENERATION',
    'AUDIO_SYNTHESIS', 'AUDIO_MIXING', 'COMPLETE'
];

const STAGE_LABELS = {
    PENDING: 'Pending',
    IDEATION: 'Ideation',
    OUTLINING: 'Outlining',
    AWAITING_APPROVAL: 'Awaiting Approval',
    APPROVED: 'Approved',
    SEGMENT_GENERATION: 'Segment Gen',
    SCRIPT_GENERATION: 'Script Gen',
    AUDIO_SYNTHESIS: 'Audio Synthesis',
    AUDIO_MIXING: 'Audio Mixing',
    COMPLETE: 'Complete',
    FAILED: 'Failed',
    REJECTED: 'Rejected'
};

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    currentEpisodeId = urlParams.get('episode_id');

    if (!currentEpisodeId) {
        showToast('Error: No episode ID specified', 'danger');
        return;
    }

    loadEpisode();
    connectWebSocket();
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
        renderAll();

        document.getElementById('episode-container').style.display = 'block';
    } catch (error) {
        showToast(`Error loading episode: ${error.message}`, 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Render all sections
 */
function renderAll() {
    renderHeader();
    renderStageTimeline();
    renderMetadata();
    renderOutline();
    renderScripts();
    renderAudio();
}

/**
 * Render episode header
 */
function renderHeader() {
    const ep = episodeData;
    document.getElementById('ep-title').textContent = ep.title || ep.topic;
    document.getElementById('ep-meta').textContent =
        `Show: ${ep.show_id} | Topic: ${ep.topic} | Created: ${formatDate(ep.created_at)}`;
}

/**
 * Render the stage timeline as a pill row
 */
function renderStageTimeline() {
    const stage = episodeData.current_stage;
    const currentIdx = PIPELINE_ORDER.indexOf(stage);
    const container = document.getElementById('stage-timeline');

    let html = '';
    PIPELINE_ORDER.forEach((s, i) => {
        let cls = 'future';
        if (stage === 'FAILED' || stage === 'REJECTED') {
            // Everything up to where it was is past, the failure stage shown at end
            const failIdx = PIPELINE_ORDER.indexOf(stage);
            if (i < failIdx) cls = 'past';
            else cls = 'future';
        } else if (i < currentIdx) {
            cls = 'past';
        } else if (i === currentIdx) {
            cls = 'current';
        }

        if (i > 0) html += '<span class="stage-arrow">&rarr;</span>';
        html += `<span class="stage-pill ${cls}">${STAGE_LABELS[s]}</span>`;
    });

    // Show FAILED / REJECTED pill at end if applicable
    if (stage === 'FAILED') {
        html += '<span class="stage-arrow">&rarr;</span>';
        html += '<span class="stage-pill failed">Failed</span>';
    } else if (stage === 'REJECTED') {
        html += '<span class="stage-arrow">&rarr;</span>';
        html += '<span class="stage-pill rejected">Rejected</span>';
    }

    container.innerHTML = html;
}

/**
 * Render metadata row (cost, approval status, updated)
 */
function renderMetadata() {
    const ep = episodeData;

    // Cost — not in API response currently, show placeholder
    document.getElementById('ep-cost').textContent = '$0.00';

    // Approval status
    const statusEl = document.getElementById('ep-approval-status');
    const status = ep.approval_status || 'N/A';
    const statusColors = { approved: 'text-success', rejected: 'text-danger', pending: 'text-warning' };
    statusEl.innerHTML = `<span class="meta-value ${statusColors[status] || ''}">${status.charAt(0).toUpperCase() + status.slice(1)}</span>`;

    if (ep.approval_feedback) {
        statusEl.innerHTML += `<div class="mt-1" style="font-size: 0.85rem; color: #6b7280;">"${escapeHtml(ep.approval_feedback)}"</div>`;
    }

    // Updated
    document.getElementById('ep-updated').textContent = formatDate(ep.updated_at);
}

/**
 * Render outline tab
 */
function renderOutline() {
    const card = document.getElementById('outline-card');
    const outline = episodeData.outline;
    const approveRow = document.getElementById('approve-action-row');

    if (!outline || !outline.story_beats || outline.story_beats.length === 0) {
        card.innerHTML = '<p class="text-muted">No outline generated yet.</p>';
        approveRow.style.display = 'none';
        return;
    }

    let html = '';
    if (outline.educational_concept) {
        html += `<p class="text-muted mb-3">Educational focus: ${escapeHtml(outline.educational_concept)}</p>`;
    }

    html += outline.story_beats.map((beat, i) => {
        const num = beat.beat_number || (i + 1);
        return `
            <div class="beat-card">
                <div class="d-flex align-items-center mb-1">
                    <span class="beat-number">${num}</span>
                    <span class="beat-title">${escapeHtml(beat.title || `Beat ${num}`)}</span>
                </div>
                <p class="beat-description">${escapeHtml(beat.description || '')}</p>
                ${beat.educational_focus ? `<p style="color: #6b7280; font-size: 0.85rem; font-style: italic;">Educational: ${escapeHtml(beat.educational_focus)}</p>` : ''}
                ${beat.key_moments && beat.key_moments.length > 0 ? `
                    <ul class="mb-0" style="font-size: 0.85rem; color: #4b5563;">
                        ${beat.key_moments.map(m => `<li>${escapeHtml(m)}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
    }).join('');

    card.innerHTML = html;

    // Show approve button if awaiting
    if (episodeData.current_stage === 'AWAITING_APPROVAL') {
        approveRow.style.display = 'block';
        document.getElementById('approve-link').href = `approve.html?episode_id=${currentEpisodeId}`;
    } else {
        approveRow.style.display = 'none';
    }
}

/**
 * Render scripts tab as accordion
 */
function renderScripts() {
    const container = document.getElementById('scripts-container');
    const scripts = episodeData.scripts;

    if (!scripts || scripts.length === 0) {
        container.innerHTML = '<div class="editor-card"><p class="text-muted">No scripts generated yet.</p></div>';
        return;
    }

    let html = '<div class="accordion" id="scriptsAccordion">';

    scripts.forEach((script, i) => {
        const segNum = script.segment_number || (i + 1);
        const blocks = script.script_blocks || script.blocks || [];
        const collapseId = `collapse-script-${i}`;

        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button ${i > 0 ? 'collapsed' : ''}" type="button"
                            data-bs-toggle="collapse" data-bs-target="#${collapseId}">
                        Segment ${segNum} (${blocks.length} blocks)
                    </button>
                </h2>
                <div id="${collapseId}" class="accordion-collapse collapse ${i === 0 ? 'show' : ''}"
                     data-bs-parent="#scriptsAccordion">
                    <div class="accordion-body p-0">
                        ${blocks.map(block => `
                            <div class="script-block">
                                <div class="speaker-name">${escapeHtml(block.speaker || 'Narrator')}</div>
                                <div class="script-text">${escapeHtml(block.text || '')}</div>
                                ${block.duration_estimate ? `<small class="text-muted">${block.duration_estimate}s</small>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Render audio tab
 */
function renderAudio() {
    const audioPath = episodeData.audio_path;
    const emptyEl = document.getElementById('audio-empty');
    const playerContainer = document.getElementById('audio-player-container');

    if (audioPath) {
        emptyEl.style.display = 'none';
        playerContainer.style.display = 'block';
        document.getElementById('audio-source').src = audioPath;
        document.getElementById('audio-player').load();
        document.getElementById('audio-download-link').href = audioPath;
    } else {
        emptyEl.style.display = 'block';
        playerContainer.style.display = 'none';
    }
}

/**
 * Connect to WebSocket for live updates
 */
function connectWebSocket() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        document.getElementById('ws-dot').className = 'ws-dot connected';
        document.getElementById('ws-status-text').textContent = 'Live';
    };

    ws.onmessage = (event) => {
        let msg;
        try { msg = JSON.parse(event.data); } catch { return; }

        if (msg.event_type === 'ping') {
            ws.send(JSON.stringify({ event_type: 'pong' }));
            return;
        }

        if (msg.event_type === 'episode_status_changed' && msg.data.episode_id === currentEpisodeId) {
            showToast(`Episode updated to ${STAGE_LABELS[msg.data.new_stage] || msg.data.new_stage}`, 'info');
            loadEpisode();
        }
    };

    ws.onclose = () => {
        document.getElementById('ws-dot').className = 'ws-dot connecting';
        document.getElementById('ws-status-text').textContent = 'Reconnecting...';
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => ws.close();
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date
 */
function formatDate(isoStr) {
    if (!isoStr) return '-';
    const d = new Date(isoStr);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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
