/**
 * CryptoSatX Dashboard - Main JavaScript
 * Handles API calls, real-time updates, and UI interactions
 */

// Configuration
const API_BASE_URL = window.location.origin;
const REFRESH_INTERVAL = 30000; // 30 seconds
let refreshTimer = null;
let charts = {};

// Dark Mode
function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const htmlElement = document.documentElement;

    // Check for saved theme preference or default to dark mode
    const currentTheme = localStorage.getItem('theme') || 'dark';
    if (currentTheme === 'dark') {
        htmlElement.classList.add('dark');
    }

    darkModeToggle.addEventListener('click', () => {
        htmlElement.classList.toggle('dark');
        const theme = htmlElement.classList.contains('dark') ? 'dark' : 'light';
        localStorage.setItem('theme', theme);
    });
}

// API Calls
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return null;
    }
}

async function generateSignal(symbol) {
    return await fetchAPI(`/signals/${symbol}`);
}

async function getVerdictPerformance() {
    return await fetchAPI('/analytics/verdict-performance');
}

async function getOutcomesHistory() {
    return await fetchAPI('/analytics/outcomes-history?limit=50');
}

async function getTrackingStats() {
    return await fetchAPI('/analytics/tracking-stats');
}

// Update Dashboard Stats
async function updateStats() {
    try {
        const stats = await getTrackingStats();

        if (stats && stats.success) {
            // Total Signals
            document.getElementById('totalSignals').textContent = stats.total_signals || 0;

            // Win Rate
            const winRate = stats.overall_win_rate || 0;
            document.getElementById('winRate').textContent = `${winRate.toFixed(1)}%`;

            // Active Signals (being tracked)
            const activeSignals = stats.signals_being_tracked || 0;
            document.getElementById('activeSignals').textContent = activeSignals;

            // Avg P&L (24h)
            const avgPnl = stats.avg_pnl_24h || 0;
            const pnlElement = document.getElementById('avgPnl');
            pnlElement.textContent = `${avgPnl >= 0 ? '+' : ''}${avgPnl.toFixed(2)}%`;
            pnlElement.className = avgPnl >= 0 ? 'text-3xl font-bold text-green-500' : 'text-3xl font-bold text-red-500';
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Load Latest Signals
async function loadLatestSignals() {
    const container = document.getElementById('latestSignals');

    try {
        const history = await getOutcomesHistory();

        if (!history || !history.outcomes || history.outcomes.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <i class="fas fa-inbox text-4xl text-gray-400 mb-4"></i>
                    <p class="text-gray-500 dark:text-gray-400">No signals yet</p>
                </div>
            `;
            return;
        }

        const signalsHTML = history.outcomes.slice(0, 10).map(signal => {
            const signalClass = signal.signal_type === 'LONG' ? 'signal-long' :
                               signal.signal_type === 'SHORT' ? 'signal-short' : 'signal-neutral';

            const verdictColor = signal.verdict === 'CONFIRM' ? 'text-green-500' :
                                signal.verdict === 'SKIP' ? 'text-red-500' :
                                signal.verdict === 'DOWNSIZE' ? 'text-yellow-500' : 'text-gray-500';

            const pnl24h = signal.pnl_24h || 0;
            const pnlColor = pnl24h >= 0 ? 'text-green-500' : 'text-red-500';
            const outcome24h = signal.outcome_24h || 'PENDING';
            const outcomeIcon = outcome24h === 'WIN' ? 'fa-check-circle' :
                               outcome24h === 'LOSS' ? 'fa-times-circle' : 'fa-clock';

            return `
                <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition card-hover">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center space-x-3">
                            <div class="${signalClass} w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold">
                                ${signal.symbol}
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-900 dark:text-white">${signal.symbol}</h3>
                                <p class="text-xs text-gray-500 dark:text-gray-400">${new Date(signal.entry_timestamp).toLocaleString()}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="px-3 py-1 ${signalClass} rounded-full text-white text-sm font-semibold">
                                ${signal.signal_type}
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-3 gap-4 text-sm">
                        <div>
                            <p class="text-gray-500 dark:text-gray-400 text-xs">AI Verdict</p>
                            <p class="font-semibold ${verdictColor}">${signal.verdict}</p>
                        </div>
                        <div>
                            <p class="text-gray-500 dark:text-gray-400 text-xs">24h P&L</p>
                            <p class="font-semibold ${pnlColor}">${pnl24h >= 0 ? '+' : ''}${pnl24h.toFixed(2)}%</p>
                        </div>
                        <div>
                            <p class="text-gray-500 dark:text-gray-400 text-xs">Outcome</p>
                            <p class="font-semibold text-gray-900 dark:text-white">
                                <i class="fas ${outcomeIcon} mr-1"></i>${outcome24h}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = signalsHTML;
    } catch (error) {
        console.error('Error loading signals:', error);
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                <p class="text-gray-500 dark:text-gray-400">Error loading signals</p>
            </div>
        `;
    }
}

// Initialize Charts
function initCharts() {
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#e5e7eb';

    Chart.defaults.color = textColor;
    Chart.defaults.borderColor = gridColor;

    // Verdict Performance Chart
    const verdictCtx = document.getElementById('verdictChart');
    charts.verdict = new Chart(verdictCtx, {
        type: 'bar',
        data: {
            labels: ['CONFIRM', 'DOWNSIZE', 'SKIP', 'WAIT'],
            datasets: [{
                label: 'Win Rate (%)',
                data: [0, 0, 0, 0],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(107, 114, 128, 0.8)'
                ],
                borderColor: [
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)',
                    'rgb(239, 68, 68)',
                    'rgb(107, 114, 128)'
                ],
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Win Rate: ${context.parsed.y.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        color: gridColor
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // Signal Distribution Chart
    const distCtx = document.getElementById('distributionChart');
    charts.distribution = new Chart(distCtx, {
        type: 'doughnut',
        data: {
            labels: ['LONG', 'SHORT', 'NEUTRAL'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(107, 114, 128, 0.8)'
                ],
                borderColor: [
                    'rgb(16, 185, 129)',
                    'rgb(239, 68, 68)',
                    'rgb(107, 114, 128)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });

    // Performance Timeline Chart
    const timelineCtx = document.getElementById('timelineChart');
    charts.timeline = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cumulative P&L (%)',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        color: gridColor
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Update Charts with Real Data
async function updateCharts() {
    try {
        // Update Verdict Performance Chart
        const verdictPerf = await getVerdictPerformance();
        if (verdictPerf && verdictPerf.success && verdictPerf.verdicts) {
            const verdicts = ['CONFIRM', 'DOWNSIZE', 'SKIP', 'WAIT'];
            const winRates = verdicts.map(v => {
                const data = verdictPerf.verdicts.find(vd => vd.verdict === v);
                return data ? data.win_rate_24h : 0;
            });

            charts.verdict.data.datasets[0].data = winRates;
            charts.verdict.update();
        }

        // Update Signal Distribution Chart
        const history = await getOutcomesHistory();
        if (history && history.outcomes) {
            const longCount = history.outcomes.filter(s => s.signal_type === 'LONG').length;
            const shortCount = history.outcomes.filter(s => s.signal_type === 'SHORT').length;
            const neutralCount = history.outcomes.filter(s => s.signal_type === 'NEUTRAL').length;

            charts.distribution.data.datasets[0].data = [longCount, shortCount, neutralCount];
            charts.distribution.update();
        }

        // Update Performance Timeline
        if (history && history.outcomes && history.outcomes.length > 0) {
            // Sort by timestamp
            const sorted = [...history.outcomes].sort((a, b) =>
                new Date(a.entry_timestamp) - new Date(b.entry_timestamp)
            );

            // Calculate cumulative P&L
            let cumulativePnl = 0;
            const timelineData = sorted.map(signal => {
                cumulativePnl += (signal.pnl_24h || 0);
                return {
                    x: new Date(signal.entry_timestamp).toLocaleDateString(),
                    y: cumulativePnl
                };
            });

            // Get last 20 data points
            const recentData = timelineData.slice(-20);

            charts.timeline.data.labels = recentData.map(d => d.x);
            charts.timeline.data.datasets[0].data = recentData.map(d => d.y);
            charts.timeline.update();
        }

    } catch (error) {
        console.error('Error updating charts:', error);
    }
}

// Generate Signal Handler
async function handleGenerateSignal(symbol) {
    const resultContainer = document.getElementById('signalResult');
    const loadingOverlay = document.getElementById('loadingOverlay');

    if (!symbol || symbol.trim() === '') {
        alert('Please enter a symbol');
        return;
    }

    symbol = symbol.trim().toUpperCase();

    try {
        // Show loading
        loadingOverlay.classList.remove('hidden');
        resultContainer.classList.add('hidden');

        // Generate signal
        const signal = await generateSignal(symbol);

        // Hide loading
        loadingOverlay.classList.add('hidden');

        if (!signal) {
            throw new Error('Failed to generate signal');
        }

        // Display result
        const signalClass = signal.signal === 'LONG' ? 'border-green-500 bg-green-50 dark:bg-green-900 dark:bg-opacity-20' :
                           signal.signal === 'SHORT' ? 'border-red-500 bg-red-50 dark:bg-red-900 dark:bg-opacity-20' :
                           'border-gray-500 bg-gray-50 dark:bg-gray-800';

        const aiVerdict = signal.aiVerdictLayer || {};
        const verdict = aiVerdict.verdict || 'N/A';
        const verdictColor = verdict === 'CONFIRM' ? 'text-green-600' :
                            verdict === 'SKIP' ? 'text-red-600' :
                            verdict === 'DOWNSIZE' ? 'text-yellow-600' : 'text-gray-600';

        resultContainer.className = `mt-6 p-4 rounded-lg border-2 ${signalClass}`;
        resultContainer.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center justify-between">
                    <h3 class="text-2xl font-bold text-gray-900 dark:text-white">${signal.symbol}</h3>
                    <span class="px-4 py-2 rounded-full text-white font-bold text-lg ${
                        signal.signal === 'LONG' ? 'bg-green-500' :
                        signal.signal === 'SHORT' ? 'bg-red-500' : 'bg-gray-500'
                    }">
                        ${signal.signal}
                    </span>
                </div>

                <div class="grid grid-cols-2 gap-3 text-sm">
                    <div>
                        <p class="text-gray-600 dark:text-gray-400">Score</p>
                        <p class="font-bold text-lg text-gray-900 dark:text-white">${signal.score}/100</p>
                    </div>
                    <div>
                        <p class="text-gray-600 dark:text-gray-400">AI Verdict</p>
                        <p class="font-bold text-lg ${verdictColor}">${verdict}</p>
                    </div>
                    <div>
                        <p class="text-gray-600 dark:text-gray-400">Price</p>
                        <p class="font-bold text-lg text-gray-900 dark:text-white">$${signal.price.toLocaleString()}</p>
                    </div>
                    <div>
                        <p class="text-gray-600 dark:text-gray-400">Confidence</p>
                        <p class="font-bold text-lg text-gray-900 dark:text-white">${signal.confidence}</p>
                    </div>
                </div>

                ${aiVerdict.telegramSummary ? `
                    <div class="mt-3 p-3 bg-white dark:bg-dark-200 rounded-lg">
                        <p class="text-xs text-gray-600 dark:text-gray-400 mb-1">AI Analysis</p>
                        <p class="text-sm text-gray-900 dark:text-white">${aiVerdict.telegramSummary}</p>
                    </div>
                ` : ''}

                <div class="mt-3">
                    <p class="text-xs text-gray-600 dark:text-gray-400 mb-2">Top Reasons</p>
                    <ul class="space-y-1">
                        ${signal.reasons.map(reason => `
                            <li class="text-sm text-gray-800 dark:text-gray-200">
                                <i class="fas fa-check-circle text-primary mr-2"></i>${reason}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
        resultContainer.classList.remove('hidden');

    } catch (error) {
        loadingOverlay.classList.add('hidden');
        console.error('Error generating signal:', error);
        alert(`Error: ${error.message}`);
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize
    initDarkMode();
    initCharts();

    // Load initial data
    updateStats();
    loadLatestSignals();
    updateCharts();

    // Auto-refresh
    refreshTimer = setInterval(() => {
        updateStats();
        loadLatestSignals();
        updateCharts();
    }, REFRESH_INTERVAL);

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', () => {
        updateStats();
        loadLatestSignals();
        updateCharts();
    });

    // Generate signal button
    document.getElementById('generateSignalBtn').addEventListener('click', () => {
        const symbol = document.getElementById('symbolInput').value;
        handleGenerateSignal(symbol);
    });

    // Enter key on symbol input
    document.getElementById('symbolInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const symbol = e.target.value;
            handleGenerateSignal(symbol);
        }
    });

    // Quick symbol buttons
    document.querySelectorAll('.quick-symbol').forEach(btn => {
        btn.addEventListener('click', () => {
            const symbol = btn.textContent;
            document.getElementById('symbolInput').value = symbol;
            handleGenerateSignal(symbol);
        });
    });

    // Asset filter
    document.getElementById('assetFilter').addEventListener('change', (e) => {
        // Future: filter signals by asset
        loadLatestSignals();
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
});
