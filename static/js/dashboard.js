/**
 * CryptoSatX Dashboard - Main JavaScript
 * Handles API calls, real-time updates, and UI interactions
 */

// Configuration
const API_BASE_URL = window.location.origin;
const REFRESH_INTERVAL = 30000; // 30 seconds
let refreshTimer = null;
let charts = {};
let allSignals = []; // Store all signals for filtering
let monitoredSymbols = new Set(); // Store symbols being monitored
let monitorTimer = null;

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
async function loadLatestSignals(filterAsset = 'all') {
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
            allSignals = [];
            return;
        }

        // Store all signals for filtering
        allSignals = history.outcomes;

        // Filter signals based on selected asset
        let filteredSignals = allSignals;
        if (filterAsset !== 'all') {
            filteredSignals = allSignals.filter(s => s.symbol.startsWith(filterAsset));
        }

        if (filteredSignals.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <i class="fas fa-filter text-4xl text-gray-400 mb-4"></i>
                    <p class="text-gray-500 dark:text-gray-400">No signals found for ${filterAsset}</p>
                </div>
            `;
            return;
        }

        const signalsHTML = filteredSignals.slice(0, 10).map(signal => {
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

// Initialize TradingView Charts - DISABLED FOR PERFORMANCE
// TradingView charts removed to improve load time and reduce scroll length
function initTradingViewCharts() {
    // Disabled - charts removed from HTML for compact layout
    console.log('TradingView charts disabled for performance');
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

// Destroy all charts (for cleanup)
function destroyCharts() {
    Object.keys(charts).forEach(key => {
        if (charts[key]) {
            charts[key].destroy();
        }
    });
    charts = {};
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
            charts.verdict.update('none'); // Skip animation for better performance
        }

        // Update Signal Distribution Chart
        const history = await getOutcomesHistory();
        if (history && history.outcomes) {
            const longCount = history.outcomes.filter(s => s.signal_type === 'LONG').length;
            const shortCount = history.outcomes.filter(s => s.signal_type === 'SHORT').length;
            const neutralCount = history.outcomes.filter(s => s.signal_type === 'NEUTRAL').length;

            charts.distribution.data.datasets[0].data = [longCount, shortCount, neutralCount];
            charts.distribution.update('none'); // Skip animation for better performance
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
            charts.timeline.update('none'); // Skip animation for better performance
        }

    } catch (error) {
        console.error('Error updating charts:', error);
    }
}

// Bulk Scanner Handler
async function handleBulkScan() {
    const textarea = document.getElementById('bulkSymbols');
    const scanBtn = document.getElementById('scanBtn');
    const resultsContainer = document.getElementById('scanResults');
    const resultsList = document.getElementById('scanResultsList');

    const symbols = textarea.value
        .split(',')
        .map(s => s.trim().toUpperCase())
        .filter(s => s.length > 0);

    if (symbols.length === 0) {
        alert('Please enter at least one symbol');
        return;
    }

    // Show loading state
    scanBtn.disabled = true;
    scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scanning...';
    resultsList.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-2xl text-primary"></i></div>';
    resultsContainer.classList.remove('hidden');

    try {
        const results = [];

        // Scan symbols in batches of 3 to avoid overwhelming the API
        for (let i = 0; i < symbols.length; i += 3) {
            const batch = symbols.slice(i, i + 3);
            const batchResults = await Promise.all(
                batch.map(symbol =>
                    generateSignal(symbol)
                        .then(result => ({ symbol, result, success: true }))
                        .catch(error => ({ symbol, error: error.message, success: false }))
                )
            );
            results.push(...batchResults);

            // Small delay between batches
            if (i + 3 < symbols.length) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        // Display results
        const resultsHTML = results.map(item => {
            if (!item.success) {
                return `
                    <div class="p-3 bg-red-50 dark:bg-red-900 dark:bg-opacity-20 rounded-lg border border-red-200 dark:border-red-800">
                        <div class="flex items-center justify-between">
                            <span class="font-semibold text-red-700 dark:text-red-300">${item.symbol}</span>
                            <span class="text-xs text-red-600 dark:text-red-400">Failed</span>
                        </div>
                    </div>
                `;
            }

            const signal = item.result;
            const signalColor = signal.signal === 'LONG' ? 'green' :
                               signal.signal === 'SHORT' ? 'red' : 'gray';

            const verdict = signal.aiVerdictLayer?.verdict || 'N/A';
            const verdictColor = verdict === 'CONFIRM' ? 'green' :
                                verdict === 'SKIP' ? 'red' :
                                verdict === 'DOWNSIZE' ? 'yellow' : 'gray';

            return `
                <div class="p-3 bg-${signalColor}-50 dark:bg-${signalColor}-900 dark:bg-opacity-20 rounded-lg border border-${signalColor}-200 dark:border-${signalColor}-800">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center space-x-2">
                            <span class="font-bold text-${signalColor}-700 dark:text-${signalColor}-300">${signal.symbol}</span>
                            <span class="px-2 py-0.5 bg-${signalColor}-500 text-white text-xs rounded-full font-semibold">${signal.signal}</span>
                        </div>
                        <button onclick="addToMonitor('${signal.symbol}')" class="px-2 py-1 bg-primary text-white text-xs rounded hover:bg-blue-600 transition">
                            <i class="fas fa-eye mr-1"></i>Monitor
                        </button>
                    </div>
                    <div class="grid grid-cols-3 gap-2 text-xs">
                        <div>
                            <span class="text-gray-600 dark:text-gray-400">Score:</span>
                            <span class="font-semibold text-gray-900 dark:text-white ml-1">${signal.score}/100</span>
                        </div>
                        <div>
                            <span class="text-gray-600 dark:text-gray-400">Verdict:</span>
                            <span class="font-semibold text-${verdictColor}-600 dark:text-${verdictColor}-400 ml-1">${verdict}</span>
                        </div>
                        <div>
                            <span class="text-gray-600 dark:text-gray-400">Price:</span>
                            <span class="font-semibold text-gray-900 dark:text-white ml-1">$${signal.price.toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        resultsList.innerHTML = resultsHTML;

    } catch (error) {
        console.error('Error in bulk scan:', error);
        resultsList.innerHTML = `
            <div class="text-center py-4 text-red-500">
                <i class="fas fa-exclamation-triangle mb-2"></i>
                <p class="text-sm">Error during scan</p>
            </div>
        `;
    } finally {
        scanBtn.disabled = false;
        scanBtn.innerHTML = '<i class="fas fa-radar mr-2"></i>Scan All Symbols';
    }
}

// Add symbol to monitor list
function addToMonitor(symbol) {
    if (monitoredSymbols.has(symbol)) {
        alert(`${symbol} is already being monitored`);
        return;
    }

    monitoredSymbols.add(symbol);
    updateMonitorList();

    // Start monitoring if not already running
    if (!monitorTimer) {
        startMonitoring();
    }
}

// Remove symbol from monitor list
function removeFromMonitor(symbol) {
    monitoredSymbols.delete(symbol);
    updateMonitorList();

    // Stop monitoring if list is empty
    if (monitoredSymbols.size === 0 && monitorTimer) {
        clearInterval(monitorTimer);
        monitorTimer = null;
    }
}

// Update monitor list display
function updateMonitorList() {
    const container = document.getElementById('monitorList');

    if (monitoredSymbols.size === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-eye-slash text-4xl text-gray-400 mb-2"></i>
                <p class="text-sm text-gray-500 dark:text-gray-400">No symbols being monitored</p>
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Add symbols from the scanner</p>
            </div>
        `;
        return;
    }

    const itemsHTML = Array.from(monitoredSymbols).map(symbol => `
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-dark-200 rounded-lg" data-symbol="${symbol}">
            <div class="flex items-center space-x-3">
                <div class="w-2 h-2 bg-green-500 rounded-full pulse-dot"></div>
                <span class="font-semibold text-gray-900 dark:text-white">${symbol}</span>
                <span class="text-xs text-gray-500 dark:text-gray-400" id="monitor-status-${symbol}">Monitoring...</span>
            </div>
            <button onclick="removeFromMonitor('${symbol}')" class="px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');

    container.innerHTML = itemsHTML;
}

// Start monitoring symbols
function startMonitoring() {
    // Initial check
    checkMonitoredSymbols();

    // Check every minute
    monitorTimer = setInterval(() => {
        checkMonitoredSymbols();
    }, 60000);
}

// Check monitored symbols for updates
async function checkMonitoredSymbols() {
    for (const symbol of monitoredSymbols) {
        try {
            const signal = await generateSignal(symbol);
            const statusElement = document.getElementById(`monitor-status-${symbol}`);

            if (statusElement) {
                const verdict = signal.aiVerdictLayer?.verdict || 'N/A';
                const verdictColor = verdict === 'CONFIRM' ? 'text-green-500' :
                                    verdict === 'SKIP' ? 'text-red-500' :
                                    verdict === 'DOWNSIZE' ? 'text-yellow-500' : 'text-gray-500';

                statusElement.innerHTML = `${signal.signal} | <span class="${verdictColor}">${verdict}</span> | $${signal.price.toLocaleString()}`;
            }
        } catch (error) {
            console.error(`Error monitoring ${symbol}:`, error);
        }

        // Small delay between checks
        await new Promise(resolve => setTimeout(resolve, 500));
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

    // TradingView charts disabled for compact layout
    // setTimeout(() => { initTradingViewCharts(); }, 500);

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
        const selectedAsset = e.target.value;
        loadLatestSignals(selectedAsset);
    });

    // Bulk scan button
    document.getElementById('scanBtn').addEventListener('click', handleBulkScan);

    // Clear monitor list button
    document.getElementById('clearMonitorBtn').addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all monitored symbols?')) {
            monitoredSymbols.clear();
            updateMonitorList();
            if (monitorTimer) {
                clearInterval(monitorTimer);
                monitorTimer = null;
            }
        }
    });
});

// Make functions globally accessible for onclick handlers
window.addToMonitor = addToMonitor;
window.removeFromMonitor = removeFromMonitor;

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    if (monitorTimer) {
        clearInterval(monitorTimer);
    }
    destroyCharts();
});
