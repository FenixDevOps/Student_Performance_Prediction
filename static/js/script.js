document.addEventListener('DOMContentLoaded', () => {
    // ── STATE ───────────────────────────────────────────────────────────
    let currentRadarChart = null;
    let distributionChart = null;
    let trendChart = null;

    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const predictionForm = document.getElementById('prediction-form');
    const resultsContainer = document.getElementById('results-container');

    // ── NAVIGATION ──────────────────────────────────────────────────────
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetPage = item.getAttribute('data-page');
            
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            pages.forEach(page => {
                page.classList.remove('active');
                if (page.id === `${targetPage}-page`) {
                    page.classList.add('active');
                }
            });

            if (targetPage === 'dashboard') loadDashboard();
            if (targetPage === 'history') loadHistory();
        });
    });

    // ── FORM INTERACTION ────────────────────────────────────────────────
    const sliders = [
        'attendance', 'study_hours', 'assignment_completion', 
        'participation_score', 'sleep_hours', 'practice_test_score'
    ];

    sliders.forEach(id => {
        const slider = document.getElementById(id);
        const valSpan = document.getElementById(`val-${id}`);
        slider.addEventListener('input', () => {
            valSpan.textContent = slider.value;
        });
    });

    // ── PREDICTION ──────────────────────────────────────────────────────
    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            student_name: document.getElementById('student_name').value,
            attendance: parseFloat(document.getElementById('attendance').value),
            previous_gpa: parseFloat(document.getElementById('previous_gpa').value),
            study_hours: parseFloat(document.getElementById('study_hours').value),
            assignment_completion: parseFloat(document.getElementById('assignment_completion').value),
            participation_score: parseFloat(document.getElementById('participation_score').value),
            sleep_hours: parseFloat(document.getElementById('sleep_hours').value),
            practice_test_score: parseFloat(document.getElementById('practice_test_score').value),
            practice_problems: parseInt(document.getElementById('practice_problems').value),
        };

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await response.json();
            if (result.error) throw new Error(result.error);

            renderResults(result);
            resultsContainer.classList.remove('hidden');
            window.scrollTo({ top: resultsContainer.offsetTop - 50, behavior: 'smooth' });
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    });

    function renderResults(data) {
        // Basic info
        document.getElementById('res-score').textContent = data.score;
        document.getElementById('res-level').textContent = data.level;
        document.getElementById('res-emoji').textContent = data.emoji;
        document.getElementById('res-summary').textContent = data.summary;

        // Badge styling
        const badge = document.getElementById('res-badge');
        const levelClass = data.level.replace(' ', '-');
        badge.style.backgroundColor = `var(--${levelClass.toLowerCase()}-bg)`;
        badge.style.borderColor = `var(--${levelClass.toLowerCase()}-border)`;
        document.getElementById('res-level').style.color = `var(--${levelClass.toLowerCase()}-text)`;

        // Strengths & Weaknesses
        const strengthTags = document.getElementById('res-strengths');
        strengthTags.innerHTML = data.strengths.map(s => `<span class="stag">✓ ${s}</span>`).join('');

        const weaknessTags = document.getElementById('res-weaknesses');
        weaknessTags.innerHTML = data.weaknesses.map(w => `<span class="wtag">⚡ ${w}</span>`).join('');

        if (data.strengths.length === 0) strengthTags.innerHTML = '<p style="color:#64748b; font-style:italic">No standout strengths yet.</p>';
        if (data.weaknesses.length === 0) weaknessTags.innerHTML = '<p style="color:#86efac; font-weight:600">All features above benchmarks! 🎉</p>';

        // Recommendations
        const recList = document.getElementById('res-recommendations');
        recList.innerHTML = data.recommendations.map((r, i) => `
            <div class="rec-row">
                <span class="rnum">${i + 1}</span>
                <span class="rtxt">${r}</span>
            </div>
        `).join('');

        // Radar Chart
        renderRadarChart(data.features);
    }

    function renderRadarChart(features) {
        const ctx = document.getElementById('radarChart').getContext('2d');
        if (currentRadarChart) currentRadarChart.destroy();

        const labels = ["Attendance", "GPA", "Study Hrs", "Assignments", "Participation", "Sleep", "Practice Test", "Problems"];
        const maxima = [100, 10.0, 40, 100, 10, 12, 100, 200];
        const rawVals = [
            features.attendance, features.previous_gpa, features.study_hours, 
            features.assignment_completion, features.participation_score, 
            features.sleep_hours, features.practice_test_score, features.practice_problems
        ];
        const normalizedData = rawVals.map((v, i) => (v / maxima[i]) * 100);

        currentRadarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Student Profile (%)',
                    data: normalizedData,
                    fill: true,
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgb(59, 130, 246)',
                    pointBackgroundColor: 'rgb(59, 130, 246)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(59, 130, 246)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: '#334155' },
                        grid: { color: '#334155' },
                        pointLabels: { color: '#e2e8f0', font: { size: 12, weight: '600' } },
                        ticks: { display: false },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // ── DASHBOARD ───────────────────────────────────────────────────────
    async function loadDashboard() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('stat-total').textContent = stats.total || 0;
            document.getElementById('stat-avg').textContent = stats.avg_score || 0;
            document.getElementById('stat-max').textContent = stats.max_score || 0;
            document.getElementById('stat-min').textContent = stats.min_score || 0;

            renderDistributionChart(stats);
            
            // For trend chart, we need more data. Fetch full history for now.
            const hResponse = await fetch('/api/history');
            const history = await hResponse.json();
            renderTrendChart(history);
        } catch (err) {
            console.error('Error loading dashboard:', err);
        }
    }

    function renderDistributionChart(stats) {
        const ctx = document.getElementById('distributionChart').getContext('2d');
        if (distributionChart) distributionChart.destroy();

        distributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Excellent', 'Good', 'Average', 'At Risk'],
                datasets: [{
                    data: [stats.excellent, stats.good, stats.average, stats.at_risk],
                    backgroundColor: ['#16a34a', '#1d4ed8', '#d97706', '#dc2626'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#e2e8f0', padding: 20 }
                    }
                }
            }
        });
    }

    function renderTrendChart(history) {
        const ctx = document.getElementById('trendChart').getContext('2d');
        if (trendChart) trendChart.destroy();

        // Sort by ID (time) and take last 20
        const sorted = [...history].sort((a, b) => a.id - b.id).slice(-20);
        
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sorted.map(r => r.student_name),
                datasets: [{
                    label: 'Predicted Score',
                    data: sorted.map(r => r.predicted_score),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' },
                        suggestedMin: 0,
                        suggestedMax: 100
                    },
                    x: {
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // ── HISTORY ─────────────────────────────────────────────────────────
    const historySearch = document.getElementById('history-search');
    const historyFilter = document.getElementById('history-level-filter');
    
    [historySearch, historyFilter].forEach(el => {
        el.addEventListener('input', loadHistory);
    });

    async function loadHistory() {
        const query = historySearch.value;
        const level = historyFilter.value;
        
        try {
            const response = await fetch(`/api/history?query=${encodeURIComponent(query)}&level=${level}`);
            const records = await response.json();
            
            const tbody = document.getElementById('history-tbody');
            tbody.innerHTML = records.map(r => `
                <tr>
                    <td><strong>${r.student_name}</strong></td>
                    <td>${r.predicted_score}</td>
                    <td><span class="lvl-cell lvl-${r.performance_level.replace(' ', '-')}">${r.performance_level}</span></td>
                    <td>${r.timestamp.split(' ')[0]}</td>
                </tr>
            `).join('');
        } catch (err) {
            console.error('Error loading history:', err);
        }
    }



    // ── INITIAL LOAD ─────────────────────────────────────────────────────
    async function init() {
        try {
            const response = await fetch('/api/model-info');
            const info = await response.json();
            if (info) {
                document.getElementById('model-algo').textContent = info.model_name;
                document.getElementById('model-r2').textContent = info.r2;
                document.getElementById('model-rmse').textContent = info.rmse;
            }
        } catch (err) {
            console.error('Error loading model info:', err);
        }
    }

    init();
});
