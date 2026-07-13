// ===== TrafficVision AI — Premium Dashboard Engine =====
let currentVideoId = null;
let currentMediaType = null;
let pollInterval = null;
let pieChart = null;
let barChart = null;
let timelineChart = null;
let startTimestamp = null;
let elapsedTimer = null;

// Chart.js dark theme defaults
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = 'rgba(148,163,184,0.06)';
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size = 11;

// ===== ANIMATED COUNTER =====
function animateValue(el, start, end, duration = 600) {
    if (start === end) { el.innerText = end; return; }
    const range = end - start;
    const startTime = performance.now();
    function step(timestamp) {
        const progress = Math.min((timestamp - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        el.innerText = Math.floor(start + range * eased);
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

// ===== UPLOAD =====
async function uploadMedia(inputElement) {
    const file = inputElement.files[0];
    if (!file) return;

    // UI transitions
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('processing-section').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('system-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-blue-500 mr-1.5 animate-pulse"></span> Uploading...';

    // Destroy old charts
    if (pieChart) { pieChart.destroy(); pieChart = null; }
    if (barChart) { barChart.destroy(); barChart = null; }
    if (timelineChart) { timelineChart.destroy(); timelineChart = null; }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await response.json();

        if (response.ok) {
            currentVideoId = data.video_id;
            currentMediaType = data.type;
            startTimestamp = Date.now();
            startElapsedTimer();
            startPolling();
            document.getElementById('system-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-brand mr-1.5 animate-pulse"></span> Processing';

            // Show original media immediately
            showOriginalMedia();
        } else {
            alert('Upload failed: ' + (data.error || 'Unknown error'));
            document.getElementById('upload-section').classList.remove('hidden');
            document.getElementById('processing-section').classList.add('hidden');
        }
    } catch (err) {
        console.error(err);
        alert('Connection error during upload.');
        document.getElementById('upload-section').classList.remove('hidden');
        document.getElementById('processing-section').classList.add('hidden');
    }

    inputElement.value = '';
}

function showOriginalMedia() {
    if (currentMediaType === 'image') {
        const img = document.getElementById('original-image');
        img.src = `/api/download/${currentVideoId}/image`;
        img.classList.remove('hidden');
    } else {
        const vid = document.getElementById('original-video');
        vid.src = `/api/download/${currentVideoId}/original`;
        vid.classList.remove('hidden');
    }
    document.getElementById('original-placeholder').classList.add('hidden');
}

function startElapsedTimer() {
    if (elapsedTimer) clearInterval(elapsedTimer);
    elapsedTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTimestamp) / 1000);
        const m = Math.floor(elapsed / 60);
        const s = elapsed % 60;
        document.getElementById('elapsed-time').innerText = `Elapsed: ${m > 0 ? m + 'm ' : ''}${s}s`;
    }, 1000);
}

// ===== POLLING =====
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    document.getElementById('dashboard').classList.remove('hidden');

    let errCount = 0;
    const MAX_ERRORS = 30;

    pollInterval = setInterval(async () => {
        if (!currentVideoId) return;
        try {
            const res = await fetch(`/api/statistics/${currentVideoId}`);
            if (!res.ok) {
                errCount++;
                if (errCount >= MAX_ERRORS) {
                    clearInterval(pollInterval);
                    if (elapsedTimer) clearInterval(elapsedTimer);
                    document.getElementById('system-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-danger mr-1.5"></span> Failed';
                    document.getElementById('upload-section').classList.remove('hidden');
                }
                return;
            }
            errCount = 0;
            const stats = await res.json();
            updateDashboard(stats);

            if (stats.status === 'completed') {
                clearInterval(pollInterval);
                if (elapsedTimer) clearInterval(elapsedTimer);
                finishProcessing();
            } else if (stats.status === 'error') {
                clearInterval(pollInterval);
                if (elapsedTimer) clearInterval(elapsedTimer);
                document.getElementById('system-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-danger mr-1.5"></span> Error';
            }
        } catch (err) {
            console.error(err);
            errCount++;
            if (errCount >= MAX_ERRORS) {
                clearInterval(pollInterval);
                if (elapsedTimer) clearInterval(elapsedTimer);
                document.getElementById('system-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-danger mr-1.5"></span> Connection Lost';
                document.getElementById('upload-section').classList.remove('hidden');
            }
        }
    }, 1500);
}

// ===== DASHBOARD UPDATE =====
function updateDashboard(stats) {
    // Progress
    const progress = stats.progress.toFixed(1);
    document.getElementById('progress-percent').innerText = `${progress}%`;
    document.getElementById('progress-bar').style.width = `${progress}%`;
    document.getElementById('fps-counter').innerText = `${stats.fps} FPS`;
    document.getElementById('frame-counter').innerText = `Frame ${stats.current_frame} / ${stats.total_frames}`;

    if (stats.analytics) {
        const ax = stats.analytics;

        // Animated counters
        animateValue(document.getElementById('stat-total'), parseInt(document.getElementById('stat-total').innerText) || 0, ax.total);
        animateValue(document.getElementById('stat-car'), parseInt(document.getElementById('stat-car').innerText) || 0, ax.distribution["Car"] || 0);
        animateValue(document.getElementById('stat-bus'), parseInt(document.getElementById('stat-bus').innerText) || 0, ax.distribution["Bus"] || 0);
        animateValue(document.getElementById('stat-truck'), parseInt(document.getElementById('stat-truck').innerText) || 0, ax.distribution["Truck"] || 0);
        animateValue(document.getElementById('stat-motorcycle'), parseInt(document.getElementById('stat-motorcycle').innerText) || 0, ax.distribution["Motorcycle"] || 0);

        // Density badge with color
        const densityEl = document.getElementById('stat-density');
        densityEl.innerText = ax.density.level;
        densityEl.style.color = ax.density.color_hex;

        updateCharts(ax.distribution);
        updateAIInsights(ax.insights);
    }

    // Timeline chart
    if (stats.timeline && stats.timeline.length > 0) {
        updateTimeline(stats.timeline);
    }

    // Vehicle table
    if (stats.recent_detections && stats.recent_detections.length > 0) {
        updateVehicleTable(stats.recent_detections);
    }
}

// ===== CHARTS =====
function updateCharts(distribution) {
    const labels = ["Car", "Bus", "Truck", "Motorcycle", "Bicycle"];
    const colors = ['#EF4444', '#3B82F6', '#EAB308', '#A855F7', '#22C55E'];
    const data = labels.map(l => distribution[l] || 0);

    const pieCtx = document.getElementById('pieChart').getContext('2d');
    if (!pieChart) {
        pieChart = new Chart(pieCtx, {
            type: 'doughnut',
            data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0 }] },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '72%',
                plugins: { legend: { position: 'right', labels: { boxWidth: 8, padding: 12, usePointStyle: true, pointStyle: 'circle' } } }
            }
        });
    } else {
        pieChart.data.datasets[0].data = data;
        pieChart.update('none');
    }

    const barCtx = document.getElementById('barChart').getContext('2d');
    if (!barChart) {
        barChart = new Chart(barCtx, {
            type: 'bar',
            data: { labels, datasets: [{ label: 'Count', data, backgroundColor: colors, borderRadius: 6, barThickness: 24 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.06)' }, ticks: { stepSize: 1 } },
                    x: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    } else {
        barChart.data.datasets[0].data = data;
        barChart.update('none');
    }
}

function updateTimeline(timeline) {
    const labels = timeline.map(t => t.time);
    const data = timeline.map(t => t.count);

    const ctx = document.getElementById('timelineChart').getContext('2d');
    if (!timelineChart) {
        timelineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Vehicles',
                    data,
                    borderColor: '#2563EB',
                    backgroundColor: 'rgba(37,99,235,0.08)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.06)' } },
                    x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } }
                },
                plugins: { legend: { display: false } },
                interaction: { mode: 'index', intersect: false }
            }
        });
    } else {
        timelineChart.data.labels = labels;
        timelineChart.data.datasets[0].data = data;
        timelineChart.update('none');
    }
}

// ===== AI INSIGHTS =====
function updateAIInsights(insights) {
    if (!insights) return;

    const typeColors = { 'Car': 'text-red-400', 'Bus': 'text-blue-400', 'Truck': 'text-yellow-400', 'Motorcycle': 'text-purple-400', 'Bicycle': 'text-green-400' };
    const riskBg = { 'Low': 'bg-accent/15 text-accent', 'Medium': 'bg-warn/15 text-warn', 'High': 'bg-danger/15 text-danger' };

    let html = `
        <div class="flex items-center gap-2 mb-2">
            <span class="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md ${riskBg[insights.risk] || 'bg-slate-700 text-slate-300'}">${insights.status}</span>
            <span class="text-[10px] text-slate-500">Risk: ${insights.risk}</span>
        </div>
        <p class="text-xs text-slate-300 leading-relaxed mb-3">${insights.summary}</p>
        <div class="space-y-1.5">
    `;

    insights.recommendations.forEach(r => {
        html += `<div class="flex items-start gap-2 text-[11px] text-slate-400"><span class="text-accent mt-0.5">›</span> ${r}</div>`;
    });

    html += '</div>';
    document.getElementById('insights-content').innerHTML = html;
}

// ===== VEHICLE TABLE =====
function updateVehicleTable(detections) {
    const searchVal = (document.getElementById('table-search').value || '').toLowerCase();
    const filtered = detections.filter(d =>
        d.type.toLowerCase().includes(searchVal) || String(d.id).includes(searchVal)
    );

    const typeColors = { 'Car': 'bg-red-500', 'Bus': 'bg-blue-500', 'Truck': 'bg-yellow-500', 'Motorcycle': 'bg-purple-500', 'Bicycle': 'bg-green-500' };

    let html = '';
    filtered.forEach(d => {
        html += `
            <tr class="table-row border-b border-white/[0.03]">
                <td class="px-5 py-2.5 font-mono text-slate-300">#${d.id}</td>
                <td class="px-5 py-2.5"><span class="inline-flex items-center gap-1.5"><span class="w-2 h-2 rounded-full ${typeColors[d.type] || 'bg-slate-500'}"></span>${d.type}</span></td>
                <td class="px-5 py-2.5"><span class="text-accent font-medium">${d.conf}%</span></td>
                <td class="px-5 py-2.5 text-slate-500">${d.time}</td>
                <td class="px-5 py-2.5"><span class="text-[10px] px-2 py-0.5 rounded-md bg-brand/10 text-brand font-medium">${d.status}</span></td>
            </tr>`;
    });

    if (!html) html = '<tr><td colspan="5" class="px-5 py-6 text-center text-slate-600 text-xs">No matches</td></tr>';
    document.getElementById('vehicle-table-body').innerHTML = html;
}

// Table search listener
document.getElementById('table-search')?.addEventListener('input', function () {
    // Re-render with current data (will use cached data from last poll)
});

// ===== FINISH =====
function finishProcessing() {
    document.getElementById('system-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-accent mr-1.5"></span> Completed';
    document.getElementById('processing-section').classList.add('hidden');

    const videoElem = document.getElementById('result-video');
    const imageElem = document.getElementById('result-image');
    const dlBtn = document.getElementById('dl-media');
    const dlText = document.getElementById('dl-media-text');

    if (currentMediaType === 'image') {
        imageElem.src = `/api/download/${currentVideoId}/image?_t=${Date.now()}`;
        imageElem.classList.remove('hidden');
        videoElem.classList.add('hidden');
        if (dlBtn) dlBtn.href = `/api/download/${currentVideoId}/image`;
        if (dlText) dlText.innerText = 'Image';
    } else {
        videoElem.src = `/api/download/${currentVideoId}/video`;
        videoElem.classList.remove('hidden');
        imageElem.classList.add('hidden');
        if (dlBtn) dlBtn.href = `/api/download/${currentVideoId}/video`;
        if (dlText) dlText.innerText = 'Video';
    }

    document.getElementById('video-placeholder').classList.add('hidden');
    document.getElementById('video-actions').classList.remove('hidden');

    // Downloads section
    const dlSection = document.getElementById('downloads-section');
    dlSection.classList.remove('hidden');
    document.getElementById('dl-video-btn').href = `/api/download/${currentVideoId}/video`;
    document.getElementById('dl-report-btn').href = `/api/download/${currentVideoId}/report`;
    document.getElementById('dl-json-btn').href = `/api/download/${currentVideoId}/json`;
    document.getElementById('dl-original-btn').href = `/api/download/${currentVideoId}/original`;
}
