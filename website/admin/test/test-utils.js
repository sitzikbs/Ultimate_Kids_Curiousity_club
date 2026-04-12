/**
 * Shared utilities for the test dashboard.
 */

const SERVICES = {
    llm: { name: 'LLM (Gemma 4)', url: '/llm', healthUrl: '/llm/api/tags', port: 11434 },
    tts: { name: 'TTS (VibeVoice)', url: '/tts', healthUrl: '/tts/health', port: 8100 },
    distribution: { name: 'Distribution', url: '/dist', healthUrl: '/dist/health', port: 8200 },
    app: { name: 'App', url: '/api', healthUrl: '/api/health', port: 8000 },
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
    const results = {};
    for (const key of Object.keys(SERVICES)) {
        results[key] = await checkServiceHealth(key);
    }
    return results;
}

function statusBadge(status) {
    const colors = { healthy: 'success', unhealthy: 'warning', down: 'danger' };
    const icons = { healthy: '●', unhealthy: '◐', down: '○' };
    return `<span class="badge bg-${colors[status] || 'secondary'}">${icons[status] || '?'} ${status}</span>`;
}

function formatJson(obj) {
    return JSON.stringify(obj, null, 2);
}

function createAudioPlayer(blob) {
    const url = URL.createObjectURL(blob);
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
        `<div class="alert alert-danger">${message}</div>`;
}

function showLoading(containerId, message = 'Loading...') {
    document.getElementById(containerId).innerHTML =
        `<div class="text-center p-3"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">${message}</p></div>`;
}
