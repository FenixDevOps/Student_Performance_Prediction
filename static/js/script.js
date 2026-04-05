document.addEventListener('DOMContentLoaded', () => {

    // ── LOADING SPLASH ────────────────────────────────────────────────────────
    const splash = document.getElementById('loading-splash');
    let waited = 0;
    async function waitForServer() {
        try {
            const r = await fetch('/api/health', { cache: 'no-store' });
            const d = await r.json();
            if (d.status === 'OK' || d.status === 'ok') {
                splash.classList.add('hidden');
                setTimeout(() => splash.remove(), 700);
                init();
                return;
            }
        } catch (_) {}
        waited += 3;
        if (waited < 90) setTimeout(waitForServer, 3000);
        else { splash.classList.add('hidden'); setTimeout(() => splash.remove(), 700); init(); }
    }
    waitForServer();

    // ── TOAST ─────────────────────────────────────────────────────────────────
    function toast(msg, type = 'success') {
        const el = document.createElement('div');
        el.className = `toast toast-${type}`;
        el.innerHTML = `<span class="toast-icon">${type==='success'?'✅':type==='error'?'❌':'ℹ️'}</span><span>${msg}</span>`;
        document.getElementById('toast-container').appendChild(el);
        requestAnimationFrame(() => el.classList.add('show'));
        setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 400); }, 3500);
    }

    // ── NAVIGATION ───────────────────────────────────────────────────────────
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.page').forEach(p => {
                p.classList.toggle('active', p.id === `${page}-page`);
            });
            if (page === 'dashboard') loadDashboard();
            if (page === 'history')   loadHistory();
        });
    });

    // ── SLIDERS ───────────────────────────────────────────────────────────────
    ['attendance','study_hours','assignment_completion',
     'participation_score','sleep_hours','practice_test_score'].forEach(id => {
        const s = document.getElementById(id);
        const v = document.getElementById(`val-${id}`);
        if (s && v) s.addEventListener('input', () => v.textContent = s.value);
    });

    // ── FORM VALIDATION ───────────────────────────────────────────────────────
    const predictBtn = document.getElementById('predict-btn');
    function checkValid() {
        const name = (document.getElementById('student_name').value || '').trim();
        const gpa  = document.getElementById('previous_gpa').value;
        const prob = document.getElementById('practice_problems').value;
        const ok   = (name.length > 0) && (gpa !== '') && (prob !== '');
        predictBtn.disabled      = !ok;
        predictBtn.style.opacity = ok ? '1' : '0.5';
    }
    ['student_name','previous_gpa','practice_problems'].forEach(id =>
        document.getElementById(id)?.addEventListener('input', checkValid)
    );
    checkValid();

    // ── PREDICTION ────────────────────────────────────────────────────────────
    document.getElementById('prediction-form').addEventListener('submit', async e => {
        e.preventDefault();
        const body = {
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

        predictBtn.disabled = true;
        predictBtn.innerHTML = `<span class="btn-spinner"></span> Predicting…`;

        try {
            const res    = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const result = await res.json();
            if (!res.ok || result.error) throw new Error(result.error || `Server error ${res.status}`);

            renderResults(result);
            document.getElementById('results-container').classList.remove('hidden');
            document.getElementById('results-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
            toast('Prediction complete! Data saved. ✨');

            // ── AUTO-REFRESH background data ──────────────────────────────
            refreshAnalyticsQuietly();

        } catch (err) {
            toast(err.message || 'Prediction failed — please try again.', 'error');
        } finally {
            predictBtn.disabled  = false;
            predictBtn.innerHTML = '🔮 Predict Performance';
            checkValid();
        }
    });

    // ── RENDER RESULTS ────────────────────────────────────────────────────────
    function renderResults(d) {
        document.getElementById('res-score').textContent   = d.score;
        document.getElementById('res-level').textContent   = d.level;
        document.getElementById('res-emoji').textContent   = d.emoji;
        document.getElementById('res-summary').textContent = d.summary;

        const lvl  = (d.level || '').replace(' ', '-').toLowerCase();
        const badge = document.getElementById('res-badge');
        badge.style.backgroundColor = `var(--${lvl}-bg)`;
        badge.style.borderColor     = `var(--${lvl}-border)`;
        document.getElementById('res-level').style.color = `var(--${lvl}-text)`;

        document.getElementById('res-strengths').innerHTML = d.strengths.length
            ? d.strengths.map(s => `<span class="stag">✓ ${esc(s)}</span>`).join('')
            : `<p class="empty-state-sm">No standout strengths yet — keep going!</p>`;

        document.getElementById('res-weaknesses').innerHTML = d.weaknesses.length
            ? d.weaknesses.map(w => `<span class="wtag">⚡ ${esc(w)}</span>`).join('')
            : `<p style="color:#86efac;font-weight:600">All features above benchmarks! 🎉</p>`;

        document.getElementById('res-recommendations').innerHTML = d.recommendations.length
            ? d.recommendations.map((r, i) => `
                <div class="rec-row">
                    <span class="rnum">${i+1}</span>
                    <span class="rtxt">${esc(r)}</span>
                </div>`).join('')
            : `<p class="empty-state-sm">No recommendations — excellent student!</p>`;

        renderRadarChart(d.features);
    }

    // ── RADAR CHART ───────────────────────────────────────────────────────────
    let radarChart = null;
    function renderRadarChart(f) {
        const ctx = document.getElementById('radarChart')?.getContext('2d');
        if (!ctx) return;
        if (radarChart) radarChart.destroy();
        const maxima = [100,10,40,100,10,12,100,200];
        const vals   = [f.attendance,f.previous_gpa,f.study_hours,f.assignment_completion,
                        f.participation_score,f.sleep_hours,f.practice_test_score,f.practice_problems];
        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Attendance','GPA','Study Hrs','Assignments','Participation','Sleep','Practice Test','Problems'],
                datasets: [{
                    label: 'Profile (%)',
                    data: vals.map((v,i) => Math.round((v/maxima[i])*100)),
                    fill: true,
                    backgroundColor: 'rgba(59,130,246,0.2)',
                    borderColor: '#3b82f6',
                    pointBackgroundColor: '#3b82f6', pointBorderColor: '#fff',
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { r: {
                    angleLines:{color:'#334155'}, grid:{color:'#334155'},
                    pointLabels:{color:'#e2e8f0',font:{size:11,weight:'600'}},
                    ticks:{display:false}, min:0, max:100
                }},
                plugins:{ legend:{display:false} }
            }
        });
    }

    // ── DASHBOARD ─────────────────────────────────────────────────────────────
    let distChart = null, trendChart = null;

    async function loadDashboard() {
        setDashLoading(true);
        try {
            const res   = await fetch('/api/analytics');
            const stats = await res.json();
            renderDashboard(stats);
        } catch (err) {
            console.error('Dashboard error:', err);
            toast('Could not load analytics.', 'error');
        } finally {
            setDashLoading(false);
        }
    }

    /** Silent refresh called after each prediction (no toast, no spinner) */
    async function refreshAnalyticsQuietly() {
        try {
            const res   = await fetch('/api/analytics');
            const stats = await res.json();
            // Only update if on dashboard page to avoid destroying inactive charts
            const onDash = document.getElementById('dashboard-page')?.classList.contains('active');
            if (onDash) renderDashboard(stats);
            // always update the sidebar stat badges
            updateStatCards(stats);
        } catch (_) {}
    }

    function updateStatCards(s) {
        document.getElementById('stat-total').textContent = s.total ?? 0;
        document.getElementById('stat-avg').textContent   = s.total ? Number(s.avg_score).toFixed(1) : '—';
        document.getElementById('stat-max').textContent   = s.total ? Number(s.max_score).toFixed(1) : '—';
        document.getElementById('stat-min').textContent   = s.total ? Number(s.min_score).toFixed(1) : '—';
    }

    function renderDashboard(s) {
        updateStatCards(s);
        renderDistChart(s);
        renderTrendChart(s.recent_scores || []);
    }

    function renderDistChart(s) {
        const canvas = document.getElementById('distributionChart');
        if (!canvas) return;
        if (distChart) distChart.destroy();
        const total = (s.excellent||0)+(s.good||0)+(s.average||0)+(s.at_risk||0);
        if (!total) {
            canvas.parentElement.innerHTML = `<div class="empty-state">📊 No data yet — make a prediction first!</div>`;
            return;
        }
        distChart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Excellent 🏆','Good ✅','Average ⚠️','At Risk 🚨'],
                datasets:[{
                    data:[s.excellent,s.good,s.average,s.at_risk],
                    backgroundColor:['#16a34a','#1d4ed8','#d97706','#dc2626'],
                    borderWidth: 0
                }]
            },
            options:{
                responsive:true, maintainAspectRatio:false,
                plugins:{legend:{position:'bottom',labels:{color:'#e2e8f0',padding:15,font:{size:12}}}}
            }
        });
    }

    function renderTrendChart(recent) {
        const canvas = document.getElementById('trendChart');
        if (!canvas) return;
        if (trendChart) trendChart.destroy();
        if (!recent || !recent.length) {
            canvas.parentElement.innerHTML = `<div class="empty-state">📈 No prediction records yet.</div>`;
            return;
        }
        trendChart = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: recent.map(r => r.name || '?'),
                datasets:[{
                    label:'Predicted Score',
                    data: recent.map(r => r.score),
                    borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,0.1)',
                    fill:true, tension:0.4, pointRadius:5, pointHoverRadius:8
                }]
            },
            options:{
                responsive:true, maintainAspectRatio:false,
                scales:{
                    y:{min:0,max:100,grid:{color:'#334155'},ticks:{color:'#94a3b8'}},
                    x:{grid:{color:'#334155'},ticks:{color:'#94a3b8',maxRotation:45,maxTicksLimit:10}}
                },
                plugins:{legend:{display:false}}
            }
        });
    }

    function setDashLoading(on) {
        ['stat-total','stat-avg','stat-max','stat-min'].forEach(id => {
            if (on) document.getElementById(id).innerHTML = '<span class="loading-dot">…</span>';
        });
    }

    // ── HISTORY ───────────────────────────────────────────────────────────────
    const histSearch = document.getElementById('history-search');
    const histFilter = document.getElementById('history-level-filter');
    const histSort   = document.getElementById('history-sort');

    [histSearch, histFilter, histSort].forEach(el =>
        el?.addEventListener('input', loadHistory)
    );

    async function loadHistory() {
        const query = histSearch?.value || '';
        const level = histFilter?.value || 'All';
        const sort  = histSort?.value  || 'latest';
        const tbody = document.getElementById('history-tbody');

        tbody.innerHTML = `<tr><td colspan="5" class="empty-state"><span class="loading-dot">Loading history…</span></td></tr>`;

        try {
            const res  = await fetch(`/api/history?query=${encodeURIComponent(query)}&level=${encodeURIComponent(level)}&sort=${sort}`);
            const rows = await res.json();

            if (!Array.isArray(rows) || !rows.length) {
                tbody.innerHTML = `<tr><td colspan="5" class="empty-state">📁 No records found. Make a prediction to get started!</td></tr>`;
                return;
            }

            tbody.innerHTML = rows.map(r => `
                <tr id="row-${esc(r.id)}">
                    <td><strong>${esc(r.student_name || '—')}</strong></td>
                    <td><strong>${r.predicted_score ?? '—'}</strong>/100</td>
                    <td><span class="lvl-cell lvl-${(r.performance_level||'').replace(' ','-')}">${esc(r.performance_level||'—')}</span></td>
                    <td>${(r.created_at || r.timestamp || '').slice(0,10)}</td>
                    <td>
                        <button class="btn-delete" onclick="deleteRecord('${esc(r.id)}',this)" title="Delete record">
                            🗑️ Delete
                        </button>
                    </td>
                </tr>`).join('');
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-state">❌ Could not load history. ${err.message}</td></tr>`;
        }
    }

    window.deleteRecord = async (id, btn) => {
        if (!confirm('Delete this record? This cannot be undone.')) return;
        btn.disabled = true; btn.textContent = '⏳';
        try {
            const res = await fetch(`/api/history/${encodeURIComponent(id)}`, { method: 'DELETE' });
            const d   = await res.json();
            if (!res.ok || d.error) throw new Error(d.error || 'Delete failed');
            document.getElementById(`row-${id}`)?.remove();
            toast('Record deleted.', 'info');
            refreshAnalyticsQuietly();
            // if history tbody is now empty refetch fully
            if (!document.getElementById('history-tbody').querySelector('tr[id]')) loadHistory();
        } catch (err) {
            toast(err.message || 'Delete failed.', 'error');
            btn.disabled = false; btn.innerHTML = '🗑️ Delete';
        }
    };

    // ── UTILITY ───────────────────────────────────────────────────────────────
    function esc(s) {
        return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    // ── INIT ──────────────────────────────────────────────────────────────────
    async function init() {
        // Load model info into sidebar
        try {
            const r = await fetch('/api/model-info');
            const m = await r.json();
            if (m && m.model_name) {
                document.getElementById('model-algo').textContent  = m.algorithm || m.model_name || '—';
                document.getElementById('model-r2').textContent    = m.r2   ?? '—';
                document.getElementById('model-rmse').textContent  = m.rmse ?? '—';
            }
        } catch (_) {}

        // Prime the analytics stats (quiet, no spinner)
        refreshAnalyticsQuietly();
    }
});
