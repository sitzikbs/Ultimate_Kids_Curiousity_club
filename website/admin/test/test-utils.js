/**
 * Shared utilities for the test dashboard.
 */

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Direct URLs for local dev; when behind nginx proxy these would be relative paths
const SERVICES = {
    llm: { name: 'LLM (Gemma)', url: 'http://localhost:11435', healthUrl: 'http://localhost:11435/api/tags', port: 11435 },
    tts: { name: 'TTS (VibeVoice)', url: 'http://localhost:8100', healthUrl: 'http://localhost:8100/health', port: 8100 },
    distribution: { name: 'Distribution', url: 'http://localhost:8200', healthUrl: 'http://localhost:8200/health', port: 8200 },
    app: { name: 'App', url: 'http://localhost:8000', healthUrl: 'http://localhost:8000/api/health', port: 8000 },
};

async function checkServiceHealth(serviceKey) {
    const service = SERVICES[serviceKey];
    try {
        const start = performance.now();
        const response = await fetch(service.healthUrl, { signal: AbortSignal.timeout(5000) });
        const elapsed = Math.round(performance.now() - start);
        if (response.ok) {
            const data = await response.json();
            return { status: 'healthy', latency: elapsed, data };
        }
        return { status: 'unhealthy', latency: elapsed, error: `HTTP ${response.status}` };
    } catch (err) {
        return { status: 'down', latency: null, error: err.message };
    }
}

async function checkAllHealth() {
    const keys = Object.keys(SERVICES);
    const checks = keys.map(key => checkServiceHealth(key));
    const results = await Promise.allSettled(checks);
    const output = {};
    keys.forEach((key, i) => {
        output[key] = results[i].status === 'fulfilled'
            ? results[i].value
            : { status: 'down', latency: null, error: results[i].reason?.message };
    });
    return output;
}

function statusBadge(status) {
    const colors = { healthy: 'success', unhealthy: 'warning', down: 'danger' };
    const icons = { healthy: '●', unhealthy: '◐', down: '○' };
    return `<span class="badge bg-${colors[status] || 'secondary'}">${icons[status] || '?'} ${status}</span>`;
}

function formatJson(obj) {
    return JSON.stringify(obj, null, 2);
}

let _lastAudioUrl = null;

function createAudioPlayer(blob) {
    if (_lastAudioUrl) {
        URL.revokeObjectURL(_lastAudioUrl);
    }
    const url = URL.createObjectURL(blob);
    _lastAudioUrl = url;
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.src = url;
    audio.style.width = '100%';
    return audio;
}

async function* streamResponse(url, body) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        yield decoder.decode(value, { stream: true });
    }
}

function showError(containerId, message) {
    document.getElementById(containerId).innerHTML =
        `<div class="alert alert-danger">${escapeHtml(message)}</div>`;
}

function showLoading(containerId, message = 'Loading...') {
    document.getElementById(containerId).innerHTML =
        `<div class="text-center p-3"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">${escapeHtml(message)}</p></div>`;
}
