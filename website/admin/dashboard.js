/**
 * Pipeline Dashboard - Episode tracking with WebSocket live updates
 */

const API_BASE_URL = '';
const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

let allEpisodes = [];
let currentFilter = 'all';
let ws = null;

// Stage display configuration
const STAGE_CONFIG = {
    PENDING:            { label: 'Pending',            cls: 'bg-secondary text-white' },
    IDEATION:           { label: 'Ideation',           cls: 'bg-info text-dark' },
    OUTLINING:          { label: 'Outlining',          cls: 'bg-info text-dark' },
    AWAITING_APPROVAL:  { label: 'Awaiting Approval',  cls: 'bg-warning text-dark' },
    APPROVED:           { label: 'Approved',           cls: 'bg-success text-white' },
    SEGMENT_GENERATION: { label: 'Segment Gen',        cls: 'bg-primary text-white' },
    SCRIPT_GENERATION:  { label: 'Script Gen',         cls: 'bg-primary text-white' },
    AUDIO_SYNTHESIS:    { label: 'Audio Synthesis',    cls: 'bg-primary text-white' },
    AUDIO_MIXING:       { label: 'Audio Mixing',       cls: 'bg-primary text-white' },
    COMPLETE:           { label: 'Complete',           cls: 'bg-success text-white' },
    FAILED:             { label: 'Failed',             cls: 'bg-danger text-white' },
    REJECTED:           { label: 'Rejected',           cls: 'bg-dark text-white' },
};

const IN_PROGRESS_STAGES = new Set([
    'IDEATION', 'OUTLINING', 'APPROVED', 'SEGMENT_GENERATION',
    'SCRIPT_GENERATION', 'AUDIO_SYNTHESIS', 'AUDIO_MIXING'
]);

document.addEventListener('DOMContentLoaded', () => {
    // Check for show_id filter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const showIdFilter = urlParams.get('show_id');
    if (showIdFilter) {
        document.getElementById('dashboard-subtitle').textContent =
            `Episodes for show: ${showIdFilter}`;
    }

    loadEpisodes(showIdFilter);
    connectWebSocket();
    setupFilterTabs();
});

/**
 * Load all episodes from API
 */
async function loadEpisodes(showIdFilter) {
    showLoading(true);

    try {
        let url = `${API_BASE_URL}/api/episodes`;
        if (showIdFilter) url += `?show_id=${encodeURIComponent(showIdFilter)}`;

        const response = await fetch(url);
        if (!response.ok) throw new Error(response.statusText);
        allEpisodes = await response.json();

        renderEpisodes(filterEpisodeList(currentFilter));
        updateStats();
        updateFilterBadges();

        document.getElementById('dashboard-container').style.display = 'block';
    } catch (error) {
        console.error('Error loading episodes:', error);
        showToast(`Error loading episodes: ${error.message}`, 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Filter episodes by stage category
 */
function filterEpisodeList(filter) {
    if (filter === 'all') return allEpisodes;
    if (filter === 'in_progress') {
        return allEpisodes.filter(e => IN_PROGRESS_STAGES.has(e.current_stage));
    }
    return allEpisodes.filter(e => e.current_stage === filter);
}

/**
 * Render episode rows into the table
 */
function renderEpisodes(episodes) {
    const tbody = document.getElementById('episodes-tbody');
    const emptyState = document.getElementById('empty-state');

    if (episodes.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    tbody.innerHTML = episodes.map(ep => `
        <tr data-episode-id="${ep.episode_id}">
            <td>
                <div class="episode-title">${ep.title || ep.topic}</div>
                ${ep.title ? `<div class="episode-topic">${ep.topic}</div>` : ''}
            </td>
            <td>${ep.show_id}</td>
            <td><span class="stage-badge">${renderStageBadge(ep.current_stage)}</span></td>
            <td>${formatDate(ep.updated_at)}</td>
            <td>${renderActionButtons(ep)}</td>
        </tr>
    `).join('');
}

/**
 * Render a stage badge span
 */
function renderStageBadge(stage) {
    const config = STAGE_CONFIG[stage] || { label: stage, cls: 'bg-secondary text-white' };
    return `<span class="badge ${config.cls}">${config.label}</span>`;
}

/**
 * Render action buttons for an episode row
 */
function renderActionButtons(ep) {
    let html = `<a href="episode.html?episode_id=${ep.episode_id}" class="btn btn-sm btn-outline-primary">Details</a>`;
    if (ep.current_stage === 'AWAITING_APPROVAL') {
        html += ` <a href="approve.html?episode_id=${ep.episode_id}" class="btn btn-sm btn-warning text-dark">Review</a>`;
    }
    return html;
}

/**
 * Update stat cards
 */
function updateStats() {
    const awaiting = allEpisodes.filter(e => e.current_stage === 'AWAITING_APPROVAL').length;
    const inProgress = allEpisodes.filter(e => IN_PROGRESS_STAGES.has(e.current_stage)).length;
    const complete = allEpisodes.filter(e => e.current_stage === 'COMPLETE').length;
    const failed = allEpisodes.filter(e => e.current_stage === 'FAILED' || e.current_stage === 'REJECTED').length;

    document.getElementById('stat-awaiting').textContent = awaiting;
    document.getElementById('stat-progress').textContent = inProgress;
    document.getElementById('stat-complete').textContent = complete;
    document.getElementById('stat-failed').textContent = failed;
}

/**
 * Update filter tab badges
 */
function updateFilterBadges() {
    const awaiting = allEpisodes.filter(e => e.current_stage === 'AWAITING_APPROVAL').length;
    const badge = document.getElementById('badge-awaiting');
    badge.textContent = awaiting > 0 ? awaiting : '';
}

/**
 * Setup filter tab click handlers
 */
function setupFilterTabs() {
    document.querySelectorAll('#filter-tabs .nav-link').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelector('#filter-tabs .nav-link.active').classList.remove('active');
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderEpisodes(filterEpisodeList(currentFilter));
        });
    });
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

    ws.onmessage = handleWsMessage;

    ws.onclose = () => {
        document.getElementById('ws-dot').className = 'ws-dot connecting';
        document.getElementById('ws-status-text').textContent = 'Reconnecting...';
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => ws.close();
}

/**
 * Handle incoming WebSocket messages
 */
function handleWsMessage(event) {
    let msg;
    try { msg = JSON.parse(event.data); } catch { return; }

    if (msg.event_type === 'ping') {
        ws.send(JSON.stringify({ event_type: 'pong' }));
        return;
    }

    if (msg.event_type === 'episode_status_changed') {
        handleEpisodeStatusChange(msg.data);
    }

    if (msg.event_type === 'progress_update') {
        // Could add progress bar per row in the future
    }
}

/**
 * Update a specific episode row when its status changes via WebSocket
 */
function handleEpisodeStatusChange(data) {
    const ep = allEpisodes.find(e => e.episode_id === data.episode_id);
    if (ep) {
        ep.current_stage = data.new_stage;
        // Re-render with current filter
        renderEpisodes(filterEpisodeList(currentFilter));
        updateStats();
        updateFilterBadges();
        showToast(`Episode "${ep.title || ep.topic}" moved to ${STAGE_CONFIG[data.new_stage]?.label || data.new_stage}`, 'info');
    } else {
        // New episode — reload all
        loadEpisodes();
    }
}

/**
 * Format ISO date string to locale string
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
    const spinner = document.getElementById('loading-spinner');
    const container = document.getElementById('dashboard-container');
    spinner.style.display = show ? 'block' : 'none';
    if (container && !show) container.style.display = 'block';
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
