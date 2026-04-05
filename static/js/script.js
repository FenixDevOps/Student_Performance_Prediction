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

            // Refresh background data
            refreshAnalyticsQuietly();

        } catch (err) {
            toast(err.message || 'Prediction failed — please try again.', 'error');
        } finally {
            predictBtn.disabled  = false;
            predictBtn.innerHTML = '🔮 Predict Performance';
            checkValid();
        }
    });

    // ── ADMIN ACTIONS ─────────────────────────────────────────────────────────
    const loadDemoBtn = document.getElementById('load-demo-btn');
    const clearAllBtn = document.getElementById('clear-all-btn');

    loadDemoBtn?.addEventListener('click', async () => {
        if (!confirm('Load 23 sample records? This will only add data if not already present.')) return;
        loadDemoBtn.disabled = true;
        try {
            const res = await fetch('/api/seed-data', { method: 'POST' });
            const d   = await res.json();
            if (d.success) {
                toast(`Successfully loaded demo data!`, 'success');
                refreshAllData();
            } else {
                toast(d.error || 'Failed to load demo data.', 'error');
            }
        } catch (err) {
            toast('Error connecting to server.', 'error');
        } finally {
            loadDemoBtn.disabled = false;
        }
    });

    clearAllBtn?.addEventListener('click', async () => {
        if (!confirm('🚨 ARE YOU SURE? This will delete ALL student records permanently.')) return;
        clearAllBtn.disabled = true;
        try {
            const res = await fetch('/api/clear-data', { method: 'DELETE' });
            const d   = await res.json();
            if (d.success) {
                toast('All data cleared successfully.', 'info');
                refreshAllData();
            } else {
                toast(d.error || 'Failed to clear data.', 'error');
            }
        } catch (err) {
            toast('Error connecting to server.', 'error');
        } finally {
            clearAllBtn.disabled = false;
        }
    });

    function refreshAllData() {
        // Refresh whatever is currently visible
        if (document.getElementById('dashboard-page').classList.contains('active')) loadDashboard();
        if (document.getElementById('history-page').classList.contains('active')) loadHistory();
        refreshAnalyticsQuietly(); // Updates sidebar badges
    }

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

        document.getElementById('res-strengths').innerHTML = (d.strengths || []).map(s => `<span class="stag">✓ ${esc(s)}</span>`).join('') || '<p>No strengths identified.</p>';
        document.getElementById('res-weaknesses').innerHTML = (d.weaknesses || []).map(w => `<span class="wtag">⚡ ${esc(w)}</span>`).join('') || '<p>No weaknesses identified.</p>';
        document.getElementById('res-recommendations').innerHTML = (d.recommendations || []).map((r, i) => `<div class="rec-row"><span class="rnum">${i+1}</span><span class="rtxt">${esc(r)}</span></div>`).join('') || '<p>No recommendations.</p>';

        renderRadarChart(d.features);
    }

    // ── CHARTS & DASHBOARD ────────────────────────────────────────────────────
    let radarChart = null, distChart = null, trendChart = null;

    async function loadDashboard() {
        setDashLoading(true);
        try {
            const res   = await fetch('/api/analytics');
            const stats = await res.json();
            renderDashboard(stats);
        } catch (err) {
            toast('Could not load analytics.', 'error');
        } finally {
            setDashLoading(false);
        }
    }

    async function refreshAnalyticsQuietly() {
        try {
            const res = await fetch('/api/analytics');
            const s   = await res.json();
            updateStatCards(s);
            if (document.getElementById('dashboard-page').classList.contains('active')) {
                renderDashboard(s);
            }
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
            canvas.parentElement.innerHTML = '<canvas id="distributionChart"></canvas><div class="empty-state">📊 No data available.</div>';
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
            options:{ responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom',labels:{color:'#e2e8f0',font:{size:11}}}} }
        });
    }

    function renderTrendChart(recent) {
        const canvas = document.getElementById('trendChart');
        if (!canvas) return;
        if (trendChart) trendChart.destroy();
        if (!recent || !recent.length) {
            canvas.parentElement.innerHTML = '<canvas id="trendChart"></canvas><div class="empty-state">📈 No records yet.</div>';
            return;
        }
        trendChart = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: recent.map(r => r.name || '?'),
                datasets:[{
                    label:'Score', data: recent.map(r => r.score),
                    borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,0.1)',
                    fill:true, tension:0.4, pointRadius:4
                }]
            },
            options:{
                responsive:true, maintainAspectRatio:false,
                scales:{ y:{min:0,max:100,grid:{color:'#334155'}}, x:{grid:{color:'#334155'},ticks:{display:false}} },
                plugins:{legend:{display:false}}
            }
        });
    }

    function setDashLoading(on) {
        ['stat-total','stat-avg','stat-max','stat-min'].forEach(id => {
            const el = document.getElementById(id);
            if (on && el.textContent === '—') el.innerHTML = '<span class="loading-dot">…</span>';
        });
    }

    // ── RADAR CHART ───────────────────────────────────────────────────────────
    function renderRadarChart(f) {
        const ctx = document.getElementById('radarChart')?.getContext('2d');
        if (!ctx) return;
        if (radarChart) radarChart.destroy();
        const maxima = [100,10,40,100,10,12,100,200];
        const vals   = [f.attendance,f.previous_gpa,f.study_hours,f.assignment_completion,f.participation_score,f.sleep_hours,f.practice_test_score,f.practice_problems];
        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Attendance','GPA','Study','Asgn','Part','Sleep','Test','Prob'],
                datasets: [{ data: vals.map((v,i) => (v/maxima[i])*100), backgroundColor: 'rgba(59,130,246,0.2)', borderColor: '#3b82f6' }]
            },
            options: { responsive:true, maintainAspectRatio:false, scales:{r:{grid:{color:'#334155'},ticks:{display:false},min:0,max:100}}, plugins:{legend:{display:false}} }
        });
    }

    // ── HISTORY ───────────────────────────────────────────────────────────────
    const histSearch = document.getElementById('history-search');
    const histFilter = document.getElementById('history-level-filter');
    const histSort   = document.getElementById('history-sort');

    [histSearch, histFilter, histSort].forEach(el => el?.addEventListener('input', loadHistory));

    async function loadHistory() {
        const query = histSearch?.value || '';
        const level = histFilter?.value || 'All';
        const sort  = histSort?.value  || 'latest';
        const tbody = document.getElementById('history-tbody');
        try {
            const res  = await fetch(`/api/history?query=${encodeURIComponent(query)}&level=${encodeURIComponent(level)}&sort=${sort}`);
            const rows = await res.json();
            if (!rows || !rows.length) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty-state">📁 No records found.</td></tr>';
                return;
            }
            tbody.innerHTML = rows.map(r => `
                <tr id="row-${esc(r.id)}">
                    <td><strong>${esc(r.student_name)}</strong></td>
                    <td><strong>${r.predicted_score}</strong>/100</td>
                    <td><span class="lvl-cell lvl-${(r.performance_level||'').replace(' ','-')}">${esc(r.performance_level)}</span></td>
                    <td>${(r.created_at || '').slice(0,10)}</td>
                    <td><button class="btn-delete" onclick="deleteRecord('${esc(r.id)}',this)">🗑️</button></td>
                </tr>`).join('');
        } catch (err) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">❌ Error loading history.</td></tr>';
        }
    }

    window.deleteRecord = async (id, btn) => {
        if (!confirm('Delete record?')) return;
        btn.disabled = true;
        try {
            await fetch(`/api/history/${encodeURIComponent(id)}`, { method: 'DELETE' });
            document.getElementById(`row-${id}`)?.remove();
            refreshAnalyticsQuietly();
        } catch (_) { btn.disabled = false; }
    };

    function esc(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

    // ── INIT ──────────────────────────────────────────────────────────────────
    async function init() {
        try {
            const r = await fetch('/api/model-info');
            const m = await r.json();
            document.getElementById('model-algo').textContent = m.algorithm || '—';
            document.getElementById('model-r2').textContent = m.r2 || '—';
            document.getElementById('model-rmse').textContent = m.rmse || '—';
        } catch (_) {}
        
        // Initial data load
        loadDashboard();
        loadHistory();
    }
});
