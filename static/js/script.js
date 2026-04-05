document.addEventListener('DOMContentLoaded', () => {

    // ── LOADING SPLASH ────────────────────────────────────────────────────────
    const splash = document.getElementById('loading-splash');
    let waited = 0;
    async function waitForServer() {
        try {
            const res = await fetch('/api/ping', { cache: 'no-store' });
            const data = await res.json();
            if (data.status === 'ok') {
                splash.classList.add('hidden');
                setTimeout(() => splash.remove(), 700);
                init(); // load model info once ready
                return;
            }
        } catch (_) {}
        waited += 3;
        if (waited < 90) setTimeout(waitForServer, 3000);
        else { splash.classList.add('hidden'); setTimeout(() => splash.remove(), 700); init(); }
    }
    waitForServer();

    // ── STATE ─────────────────────────────────────────────────────────────────
    let radarChart = null, distributionChart = null, trendChart = null;

    // ── TOAST NOTIFICATIONS ───────────────────────────────────────────────────
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span><span>${message}</span>`;
        document.getElementById('toast-container').appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 400); }, 3500);
    }

    // ── NAVIGATION ────────────────────────────────────────────────────────────
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.getAttribute('data-page');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            document.querySelectorAll('.page').forEach(p => {
                p.classList.remove('active');
                if (p.id === `${page}-page`) p.classList.add('active');
            });
            if (page === 'dashboard') loadDashboard();
            if (page === 'history') loadHistory();
        });
    });

    // ── FORM: SLIDERS ─────────────────────────────────────────────────────────
    ['attendance','study_hours','assignment_completion','participation_score','sleep_hours','practice_test_score'].forEach(id => {
        const slider = document.getElementById(id);
        const val = document.getElementById(`val-${id}`);
        if (slider && val) slider.addEventListener('input', () => val.textContent = slider.value);
    });

    // ── FORM: FIELD VALIDATION ────────────────────────────────────────────────
    const submitBtn = document.getElementById('predict-btn');
    function validateForm() {
        const name = document.getElementById('student_name').value.trim();
        const gpa  = document.getElementById('previous_gpa').value;
        const prob = document.getElementById('practice_problems').value;
        const valid = name.length > 0 && gpa !== '' && prob !== '';
        submitBtn.disabled = !valid;
        submitBtn.style.opacity = valid ? '1' : '0.5';
    }
    ['student_name','previous_gpa','practice_problems'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', validateForm);
    });
    validateForm();

    // ── PREDICTION ────────────────────────────────────────────────────────────
    document.getElementById('prediction-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = {
            student_name:          document.getElementById('student_name').value.trim(),
            attendance:            parseFloat(document.getElementById('attendance').value),
            previous_gpa:          parseFloat(document.getElementById('previous_gpa').value),
            study_hours:           parseFloat(document.getElementById('study_hours').value),
            assignment_completion: parseFloat(document.getElementById('assignment_completion').value),
            participation_score:   parseFloat(document.getElementById('participation_score').value),
            sleep_hours:           parseFloat(document.getElementById('sleep_hours').value),
            practice_test_score:   parseFloat(document.getElementById('practice_test_score').value),
            practice_problems:     parseInt(document.getElementById('practice_problems').value),
        };

        // Button loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="btn-spinner"></span> Predicting...`;

        try {
            const res = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const result = await res.json();
            if (!res.ok || result.error) throw new Error(result.error || 'Prediction failed');

            renderResults(result);
            document.getElementById('results-container').classList.remove('hidden');
            window.scrollTo({ top: document.getElementById('results-container').offsetTop - 50, behavior: 'smooth' });
            showToast('Prediction complete! ✨');

        } catch (err) {
            showToast(err.message || 'Something went wrong. Please try again.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `🔮 Predict Performance`;
            validateForm();
        }
    });

    // ── RENDER RESULTS ────────────────────────────────────────────────────────
    function renderResults(data) {
        document.getElementById('res-score').textContent   = data.score;
        document.getElementById('res-level').textContent   = data.level;
        document.getElementById('res-emoji').textContent   = data.emoji;
        document.getElementById('res-summary').textContent = data.summary;

        // Badge colouring
        const badge      = document.getElementById('res-badge');
        const levelClass = data.level.replace(' ', '-').toLowerCase();
        badge.style.backgroundColor  = `var(--${levelClass}-bg)`;
        badge.style.borderColor      = `var(--${levelClass}-border)`;
        document.getElementById('res-level').style.color = `var(--${levelClass}-text)`;

        // Strengths
        const sBox = document.getElementById('res-strengths');
        sBox.innerHTML = data.strengths.length
            ? data.strengths.map(s => `<span class="stag">✓ ${s}</span>`).join('')
            : `<p class="empty-state-sm">No standout strengths yet — keep going!</p>`;

        // Weaknesses
        const wBox = document.getElementById('res-weaknesses');
        wBox.innerHTML = data.weaknesses.length
            ? data.weaknesses.map(w => `<span class="wtag">⚡ ${w}</span>`).join('')
            : `<p style="color:#86efac;font-weight:600">All features above benchmarks! 🎉</p>`;

        // Recommendations
        document.getElementById('res-recommendations').innerHTML = data.recommendations.length
            ? data.recommendations.map((r, i) => `
                <div class="rec-row">
                    <span class="rnum">${i + 1}</span>
                    <span class="rtxt">${r}</span>
                </div>`).join('')
            : `<p class="empty-state-sm">No recommendations — student is performing excellently!</p>`;

        renderRadarChart(data.features);
    }

    // ── RADAR CHART ───────────────────────────────────────────────────────────
    function renderRadarChart(features) {
        const ctx = document.getElementById('radarChart').getContext('2d');
        if (radarChart) radarChart.destroy();
        const maxima = [100, 10, 40, 100, 10, 12, 100, 200];
        const vals   = [features.attendance, features.previous_gpa, features.study_hours,
                        features.assignment_completion, features.participation_score,
                        features.sleep_hours, features.practice_test_score, features.practice_problems];
        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Attendance','GPA','Study Hrs','Assignments','Participation','Sleep','Practice Test','Problems'],
                datasets: [{
                    label: 'Student Profile (%)',
                    data: vals.map((v, i) => (v / maxima[i]) * 100),
                    fill: true,
                    backgroundColor: 'rgba(59,130,246,0.2)',
                    borderColor: 'rgb(59,130,246)',
                    pointBackgroundColor: 'rgb(59,130,246)',
                    pointBorderColor: '#fff',
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { r: {
                    angleLines: { color: '#334155' }, grid: { color: '#334155' },
                    pointLabels: { color: '#e2e8f0', font: { size: 11, weight: '600' } },
                    ticks: { display: false }, suggestedMin: 0, suggestedMax: 100
                }},
                plugins: { legend: { display: false } }
            }
        });
    }

    // ── DASHBOARD ─────────────────────────────────────────────────────────────
    async function loadDashboard() {
        try {
            const [statsRes, histRes] = await Promise.all([
                fetch('/api/stats'), fetch('/api/history')
            ]);
            const stats   = await statsRes.json();
            const history = await histRes.json();

            document.getElementById('stat-total').textContent = stats.total || 0;
            document.getElementById('stat-avg').textContent   = stats.avg_score  ? Number(stats.avg_score).toFixed(1)  : '—';
            document.getElementById('stat-max').textContent   = stats.max_score  ? Number(stats.max_score).toFixed(1)  : '—';
            document.getElementById('stat-min').textContent   = stats.min_score  ? Number(stats.min_score).toFixed(1)  : '—';

            renderDistributionChart(stats);
            renderTrendChart(history);
        } catch (err) {
            console.error('Dashboard error:', err);
            showToast('Could not load dashboard data.', 'error');
        }
    }

    function renderDistributionChart(stats) {
        const ctx = document.getElementById('distributionChart').getContext('2d');
        if (distributionChart) distributionChart.destroy();
        const total = (stats.excellent||0) + (stats.good||0) + (stats.average||0) + (stats.at_risk||0);
        if (total === 0) {
            document.getElementById('distributionChart').parentElement.innerHTML =
                `<div class="empty-state">📊 No data yet — make some predictions!</div>`;
            return;
        }
        distributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Excellent 🏆','Good ✅','Average ⚠️','At Risk 🚨'],
                datasets: [{ data: [stats.excellent,stats.good,stats.average,stats.at_risk],
                    backgroundColor: ['#16a34a','#1d4ed8','#d97706','#dc2626'], borderWidth: 0 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#e2e8f0', padding: 15 } } } }
        });
    }

    function renderTrendChart(history) {
        const ctx = document.getElementById('trendChart').getContext('2d');
        if (trendChart) trendChart.destroy();
        if (!history || history.length === 0) {
            document.getElementById('trendChart').parentElement.innerHTML =
                `<div class="empty-state">📈 No predictions recorded yet.</div>`;
            return;
        }
        const sorted = [...history].sort((a, b) => (a.id || 0) - (b.id || 0)).slice(-20);
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sorted.map(r => r.student_name || 'Unknown'),
                datasets: [{ label: 'Score', data: sorted.map(r => r.predicted_score),
                    borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)',
                    fill: true, tension: 0.4, pointRadius: 5, pointHoverRadius: 8 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' }, min: 0, max: 100 },
                    x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8', maxRotation: 45 } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // ── HISTORY ───────────────────────────────────────────────────────────────
    const histSearch = document.getElementById('history-search');
    const histFilter = document.getElementById('history-level-filter');
    [histSearch, histFilter].forEach(el => el && el.addEventListener('input', loadHistory));

    async function loadHistory() {
        const query = histSearch ? histSearch.value : '';
        const level = histFilter ? histFilter.value : 'All';
        try {
            const res     = await fetch(`/api/history?query=${encodeURIComponent(query)}&level=${level}`);
            const records = await res.json();
            const tbody   = document.getElementById('history-tbody');

            if (!records.length) {
                tbody.innerHTML = `<tr><td colspan="5" class="empty-state">
                    📁 No records found. Make a prediction to get started!
                </td></tr>`;
                return;
            }

            tbody.innerHTML = records.map(r => `
                <tr>
                    <td><strong>${escHtml(r.student_name)}</strong></td>
                    <td><strong>${r.predicted_score}</strong>/100</td>
                    <td><span class="lvl-cell lvl-${(r.performance_level||'').replace(' ','-')}">${r.performance_level}</span></td>
                    <td>${(r.timestamp || '').split(' ')[0]}</td>
                    <td>
                        <button class="btn-delete" onclick="deleteRecord('${r.id}', this)">🗑️ Delete</button>
                    </td>
                </tr>`).join('');
        } catch (err) {
            console.error('History error:', err);
        }
    }

    window.deleteRecord = async function(id, btn) {
        if (!confirm('Delete this record?')) return;
        btn.disabled = true; btn.textContent = '...';
        try {
            const res = await fetch(`/api/history/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                showToast('Record deleted.', 'info');
                loadHistory();
            } else throw new Error(data.error);
        } catch (e) {
            showToast('Could not delete record.', 'error');
            btn.disabled = false; btn.innerHTML = '🗑️ Delete';
        }
    };

    function escHtml(str) {
        return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    // ── INITIAL LOAD ──────────────────────────────────────────────────────────
    async function init() {
        try {
            const res  = await fetch('/api/model-info');
            const info = await res.json();
            if (info && info.model_name) {
                document.getElementById('model-algo').textContent = info.model_name || '—';
                document.getElementById('model-r2').textContent   = info.r2   !== undefined ? info.r2   : '—';
                document.getElementById('model-rmse').textContent = info.rmse !== undefined ? info.rmse : '—';
            }
        } catch (err) {
            console.error('Model info error:', err);
        }
    }
});
