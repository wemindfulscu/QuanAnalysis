// 量化决策系统 Web版 - JavaScript应用逻辑

const API_BASE = 'http://localhost:5000/api';

// 全局状态
let currentSymbol = null;
let currentName = null;
let watchlist = [];
let klineChartInstance = null;
let rsiChartInstance = null;
let macdChartInstance = null;
let kdjChartInstance = null;

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

async function initApp() {
    await loadSystemInfo();
    await loadWatchlist();
    setStatus('就绪', 'ready');
}

// ==================== API调用 ====================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!data.success && response.status >= 400) {
            throw new Error(data.message || data.error || '请求失败');
        }
        
        return data;
    } catch (error) {
        console.error('API调用失败:', error);
        showNotification(error.message || '网络请求失败', 'error');
        throw error;
    }
}

// ==================== 状态管理 ====================

function setStatus(text, type = 'ready') {
    const statusEl = document.getElementById('status');
    statusEl.textContent = text;
    statusEl.className = `status-${type}`;
}

function showNotification(message, type = 'info') {
    // 简单的通知显示，可以后续增强
    alert(message);
}

// ==================== 系统信息 ====================

async function loadSystemInfo() {
    try {
        const result = await apiCall('/system/info');
        
        if (result.success) {
            document.getElementById('watchlistCount').textContent = 
                `监控: ${result.data.watchlist_count}`;
            document.getElementById('strategyCount').textContent = 
                `策略: ${result.data.strategy_count}`;
        }
    } catch (error) {
        console.error('加载系统信息失败:', error);
    }
}

// ==================== 监控列表 ====================

async function loadWatchlist() {
    try {
        setStatus('加载监控列表...', 'loading');
        
        const result = await apiCall('/watchlist');
        
        if (result.success) {
            watchlist = result.data;
            renderWatchlist();
            setStatus('就绪', 'ready');
        }
    } catch (error) {
        setStatus('加载失败', 'error');
    }
}

function renderWatchlist() {
    const tbody = document.getElementById('watchlistBody');
    tbody.innerHTML = '';
    
    watchlist.forEach(item => {
        const row = document.createElement('tr');
        row.onclick = () => selectWatchlistItem(item);
        
        const typeClass = `type-${item.type}`;
        
        row.innerHTML = `
            <td>${item.symbol}</td>
            <td>${item.name}</td>
            <td><span class="type-badge ${typeClass}">${getTypeLabel(item.type)}</span></td>
            <td>
                <button class="btn btn-sm btn-info" onclick="viewChart('${item.symbol}', '${item.name}'); event.stopPropagation();">
                    查看
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // 更新计数
    document.getElementById('watchlistCount').textContent = `监控: ${watchlist.length}`;
}

function getTypeLabel(type) {
    const labels = {
        'industry': '行业',
        'concept': '概念',
        'csindex': '中证',
        'hk_tech': '恒生'
    };
    return labels[type] || type;
}

function selectWatchlistItem(item) {
    currentSymbol = item.symbol;
    currentName = item.name;
    
    // 高亮选中行
    const rows = document.querySelectorAll('#watchlistBody tr');
    rows.forEach(row => row.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    
    // 显示信息
    showIndexInfo(item);
}

async function showIndexInfo(item) {
    const container = document.getElementById('indexInfo');
    
    // 格式化更新时间
    let updateTime = '未更新';
    if (item.last_update) {
        try {
            const date = new Date(item.last_update);
            updateTime = date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            updateTime = item.last_update;
        }
    }
    
    container.innerHTML = `
        <div class="info-item">
            <div class="info-label">指数代码</div>
            <div class="info-value">${item.symbol}</div>
        </div>
        <div class="info-item">
            <div class="info-label">指数名称</div>
            <div class="info-value">${item.name}</div>
        </div>
        <div class="info-item">
            <div class="info-label">类型</div>
            <div class="info-value">${getTypeLabel(item.type)}</div>
        </div>
        <div class="info-item">
            <div class="info-label">最后更新</div>
            <div class="info-value">${updateTime}</div>
        </div>
    `;
    
    // 加载更多详细信息
    try {
        const result = await apiCall(`/analysis/${item.symbol}?days=100`);
        
        if (result.success && result.data.latest_data) {
            const latest = result.data.latest_data;
            
            container.innerHTML += `
                <div class="info-item">
                    <div class="info-label">最新价格</div>
                    <div class="info-value">${latest.close.toFixed(2)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">RSI(14)</div>
                    <div class="info-value">${latest.rsi.toFixed(2)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">当前信号</div>
                    <div class="info-value">
                        <span class="signal-badge signal-${result.data.signal ? result.data.signal.toLowerCase() : 'hold'}">
                            ${result.data.signal || 'HOLD'}
                        </span>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载详细信息失败:', error);
    }
}

// ==================== 对话框管理 ====================

function showAddDialog() {
    document.getElementById('addDialog').classList.add('show');
}

function showSearchDialog() {
    document.getElementById('searchDialog').classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

async function confirmAdd() {
    const symbol = document.getElementById('addSymbol').value.trim();
    const name = document.getElementById('addName').value.trim();
    const type = document.getElementById('addType').value;
    
    if (!symbol || !name) {
        showNotification('请填写完整信息', 'warning');
        return;
    }
    
    try {
        setStatus('添加中...', 'loading');
        
        const result = await apiCall('/watchlist', {
            method: 'POST',
            body: JSON.stringify({ symbol, name, type: type || undefined })
        });
        
        if (result.success) {
            showNotification('添加成功', 'success');
            closeModal('addDialog');
            
            // 清空输入
            document.getElementById('addSymbol').value = '';
            document.getElementById('addName').value = '';
            document.getElementById('addType').value = '';
            
            // 重新加载列表
            await loadWatchlist();
        }
    } catch (error) {
        setStatus('添加失败', 'error');
    }
}

async function removeWatchlist() {
    if (!currentSymbol) {
        showNotification('请先选择要删除的项目', 'warning');
        return;
    }
    
    if (!confirm(`确定要删除 ${currentName} 吗？`)) {
        return;
    }
    
    try {
        setStatus('删除中...', 'loading');
        
        const result = await apiCall(`/watchlist/${currentSymbol}`, {
            method: 'DELETE'
        });
        
        if (result.success) {
            showNotification('删除成功', 'success');
            currentSymbol = null;
            currentName = null;
            
            // 重新加载列表
            await loadWatchlist();
        }
    } catch (error) {
        setStatus('删除失败', 'error');
    }
}

// ==================== 数据更新 ====================

async function updateSelectedData() {
    if (!currentSymbol) {
        showNotification('请先选择要更新的监控项', 'warning');
        return;
    }
    
    if (!confirm(`确定要更新 ${currentName} 的数据吗？`)) {
        return;
    }
    
    try {
        setStatus('更新中...', 'loading');
        
        const result = await apiCall('/data/update', {
            method: 'POST',
            body: JSON.stringify({ symbol: currentSymbol })
        });
        
        if (result.success) {
            showNotification(`${currentName} 数据更新成功！`, 'success');
            
            // 重新加载监控列表以获取更新时间
            await loadWatchlist();
            
            // 等待一小段时间确保数据已加载
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // 刷新当前选中项的信息显示
            const item = watchlist.find(w => w.symbol === currentSymbol);
            if (item) {
                console.log('[Update] 刷新指数信息:', item);
                showIndexInfo(item);
            } else {
                console.warn('[Update] 未找到当前指数:', currentSymbol);
            }
            
            // 如果当前有查看的图表，刷新图表
            if (currentSymbol) {
                await viewChart(currentSymbol, currentName);
            }
            
            setStatus('ready');
        }
    } catch (error) {
        setStatus('更新失败', 'error');
    }
}

// ==================== 搜索功能 ====================

let searchTimeout = null;

async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    
    if (!query) {
        document.getElementById('searchResults').innerHTML = '';
        return;
    }
    
    // 防抖
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    searchTimeout = setTimeout(async () => {
        try {
            const result = await apiCall(`/data/search?q=${encodeURIComponent(query)}`);
            
            if (result.success) {
                renderSearchResults(result.data);
            }
        } catch (error) {
            console.error('搜索失败:', error);
        }
    }, 300);
}

function renderSearchResults(results) {
    const container = document.getElementById('searchResults');
    
    if (results.length === 0) {
        container.innerHTML = '<p class="info-placeholder">未找到匹配的指数</p>';
        return;
    }
    
    container.innerHTML = '';
    
    results.forEach(item => {
        const div = document.createElement('div');
        div.className = 'search-item';
        div.onclick = () => addFromSearch(item);
        
        div.innerHTML = `
            <div class="search-item-name">${item.name}</div>
            <div class="search-item-symbol">
                ${item.symbol} - 
                <span class="type-badge type-${item.type}">${getTypeLabel(item.type)}</span>
            </div>
        `;
        
        container.appendChild(div);
    });
}

function addFromSearch(item) {
    document.getElementById('addSymbol').value = item.symbol;
    document.getElementById('addName').value = item.name;
    document.getElementById('addType').value = item.type;
    
    closeModal('searchDialog');
    showAddDialog();
}

// ==================== 信号扫描 ====================

async function scanSelectedSignal() {
    if (!currentSymbol) {
        showNotification('请先选择要扫描的监控项', 'warning');
        return;
    }
    
    if (!confirm(`确定要扫描 ${currentName} 的交易信号吗？`)) {
        return;
    }
    
    try {
        setStatus('扫描中...', 'loading');
        
        const result = await apiCall('/signals/scan', {
            method: 'POST',
            body: JSON.stringify({ symbol: currentSymbol })
        });
        
        if (result.success) {
            const signalCount = result.data.length;
            if (signalCount > 0) {
                showNotification(`扫描完成！${currentName} 发现 ${signalCount} 个信号`, 'success');
                
                // 切换到信号标签页
                switchTab('signals');
                renderSignals(result.data);
            } else {
                showNotification(`${currentName} 暂无交易信号`, 'info');
            }
            
            setStatus('就绪', 'ready');
        }
    } catch (error) {
        setStatus('扫描失败', 'error');
    }
}

function renderSignals(signals) {
    const tbody = document.getElementById('signalsBody');
    tbody.innerHTML = '';
    
    if (signals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#adb5bd;padding:40px;">暂无信号</td></tr>';
        return;
    }
    
    signals.forEach(signal => {
        const row = document.createElement('tr');
        
        const signalClass = signal.signal === 'BUY' ? 'signal-buy' : 'signal-sell';
        
        row.innerHTML = `
            <td>${signal.date}</td>
            <td>${signal.symbol}</td>
            <td>${signal.name}</td>
            <td>${signal.strategy}</td>
            <td><span class="signal-badge ${signalClass}">${signal.signal}</span></td>
            <td>${signal.price.toFixed(2)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// ==================== 标签页切换 ====================

function switchTab(tabName) {
    // 更新标签按钮
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // 更新标签页内容
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
    
    // 如果切换到监控任务标签页，加载任务数据
    if (tabName === 'monitor') {
        loadMonitorTasksTab();
    }
}

// ==================== 图表显示 ====================

async function viewChart(symbol, name) {
    currentSymbol = symbol;
    currentName = name;
    
    // 切换到K线图标签页
    switchTab('kline');
    
    try {
        setStatus('加载图表数据...', 'loading');
        
        const result = await apiCall(`/chart/${symbol}?days=250`);
        
        if (result.success) {
            renderKlineChart(result.data);
            renderIndicatorCharts(result.data);
            setStatus('就绪', 'ready');
        }
    } catch (error) {
        setStatus('加载失败', 'error');
    }
}

function renderKlineChart(data) {
    if (!klineChartInstance) {
        klineChartInstance = echarts.init(document.getElementById('klineChart'));
    }
    
    // 准备成交量颜色（根据涨跌）
    const volumeColor = data.ohlcv.map(item => {
        return item[1] >= item[0] ? '#ef5350' : '#26a69a';  // close >= open ? 红 : 绿
    });
    
    // 标记买卖信号点
    const buyPoints = [];
    const sellPoints = [];
    if (data.signals && data.signals.length > 0) {
        data.signals.forEach(signal => {
            const dateIndex = data.dates.indexOf(signal.date);
            if (dateIndex >= 0 && data.ohlcv[dateIndex]) {
                const point = [dateIndex, data.ohlcv[dateIndex][2]]; // 使用最低价位置
                if (signal.signal_type === 'BUY') {
                    buyPoints.push(point);
                } else if (signal.signal_type === 'SELL') {
                    sellPoints.push(point);
                }
            }
        });
    }
    
    const option = {
        title: {
            text: `${currentName} K线图`,
            left: 'center',
            textStyle: {
                fontSize: 16,
                fontWeight: 'bold'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                lineStyle: {
                    color: '#999',
                    type: 'dashed'
                }
            },
            backgroundColor: 'rgba(50, 50, 50, 0.9)',
            borderColor: '#333',
            textStyle: {
                color: '#fff'
            },
            formatter: function(params) {
                let result = params[0].axisValueLabel + '<br/>';
                params.forEach(param => {
                    if (param.seriesName === 'K线' && param.data) {
                        result += `开盘: ${param.data[1]}<br/>`;
                        result += `收盘: ${param.data[2]}<br/>`;
                        result += `最低: ${param.data[3]}<br/>`;
                        result += `最高: ${param.data[4]}<br/>`;
                        const change = ((param.data[2] - param.data[1]) / param.data[1] * 100).toFixed(2);
                        result += `涨跌: ${change}%<br/>`;
                    } else if (param.value !== null && param.value !== undefined) {
                        result += `${param.marker} ${param.seriesName}: ${typeof param.value === 'number' ? param.value.toFixed(2) : param.value}<br/>`;
                    }
                });
                return result;
            }
        },
        legend: {
            data: ['K线', 'MA5', 'MA20', 'MA60', '布林上轨', '布林中轨', '布林下轨', '买入信号', '卖出信号', '成交量', '量MA5', '量MA10', 'MACD', 'Signal', 'Histogram'],
            top: 30,
            selected: {
                '布林上轨': false,
                '布林中轨': false,
                '布林下轨': false
            }
        },
        grid: [
            {
                left: '8%',
                right: '8%',
                top: '12%',
                height: '42%'
            },
            {
                left: '8%',
                right: '8%',
                top: '58%',
                height: '12%'
            },
            {
                left: '8%',
                right: '8%',
                top: '74%',
                height: '16%'
            }
        ],
        xAxis: [
            {
                type: 'category',
                data: data.dates,
                scale: true,
                boundaryGap: false,
                axisLine: { 
                    onZero: false,
                    lineStyle: { color: '#666' }
                },
                splitLine: { show: false },
                min: 'dataMin',
                max: 'dataMax',
                axisLabel: { show: false }
            },
            {
                type: 'category',
                gridIndex: 1,
                data: data.dates,
                scale: true,
                boundaryGap: false,
                axisLine: { onZero: false },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { show: false },
                min: 'dataMin',
                max: 'dataMax'
            },
            {
                type: 'category',
                gridIndex: 2,
                data: data.dates,
                scale: true,
                boundaryGap: false,
                axisLine: { 
                    onZero: false,
                    lineStyle: { color: '#666' }
                },
                axisTick: { show: true },
                splitLine: { show: false },
                axisLabel: {
                    show: true,
                    formatter: function(value) {
                        return value.substring(5);
                    }
                },
                min: 'dataMin',
                max: 'dataMax'
            }
        ],
        yAxis: [
            {
                scale: true,
                splitArea: {
                    show: true
                },
                axisLine: { lineStyle: { color: '#666' } },
                splitLine: { lineStyle: { color: '#eee' } }
            },
            {
                scale: true,
                gridIndex: 1,
                splitNumber: 2,
                axisLabel: { show: false },
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { show: false }
            },
            {
                scale: true,
                gridIndex: 2,
                splitNumber: 3,
                axisLine: { lineStyle: { color: '#666' } },
                splitLine: { lineStyle: { color: '#eee' } }
            }
        ],
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0, 1, 2],
                start: 70,
                end: 100
            },
            {
                show: true,
                xAxisIndex: [0, 1, 2],
                type: 'slider',
                top: '93%',
                start: 70,
                end: 100,
                height: 20
            }
        ],
        series: [
            {
                name: 'K线',
                type: 'candlestick',
                data: data.ohlcv,
                itemStyle: {
                    color: '#ec4848',
                    color0: '#00b386',
                    borderColor: '#ec4848',
                    borderColor0: '#00b386'
                },
                emphasis: {
                    itemStyle: {
                        borderWidth: 2
                    }
                }
            },
            {
                name: 'MA5',
                type: 'line',
                data: data.ma.ma5,
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#FF6B6B',
                    opacity: 0.9,
                    width: 1.5
                }
            },
            {
                name: 'MA20',
                type: 'line',
                data: data.ma.ma20,
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#4ECDC4',
                    opacity: 0.9,
                    width: 1.5
                }
            },
            {
                name: 'MA60',
                type: 'line',
                data: data.ma.ma60,
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#FFD93D',
                    opacity: 0.9,
                    width: 1.5
                }
            },
            {
                name: '布林上轨',
                type: 'line',
                data: data.boll ? data.boll.upper : [],
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#999',
                    opacity: 0.5,
                    width: 1,
                    type: 'dashed'
                }
            },
            {
                name: '布林中轨',
                type: 'line',
                data: data.boll ? data.boll.middle : [],
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#999',
                    opacity: 0.6,
                    width: 1
                }
            },
            {
                name: '布林下轨',
                type: 'line',
                data: data.boll ? data.boll.lower : [],
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#999',
                    opacity: 0.5,
                    width: 1,
                    type: 'dashed'
                }
            },
            {
                name: '买入信号',
                type: 'scatter',
                data: buyPoints,
                symbol: 'triangle',
                symbolSize: 12,
                symbolRotate: 0,
                itemStyle: {
                    color: '#ff4444'
                },
                z: 10
            },
            {
                name: '卖出信号',
                type: 'scatter',
                data: sellPoints,
                symbol: 'triangle',
                symbolSize: 12,
                symbolRotate: 180,
                itemStyle: {
                    color: '#00b386'
                },
                z: 10
            },
            {
                name: '成交量',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.volume,
                itemStyle: {
                    color: function(params) {
                        return volumeColor[params.dataIndex];
                    },
                    opacity: 0.6
                }
            },
            {
                name: '量MA5',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.volume_ma ? data.volume_ma.ma5 : [],
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#FF6B6B',
                    width: 1.5
                }
            },
            {
                name: '量MA10',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.volume_ma ? data.volume_ma.ma10 : [],
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#4ECDC4',
                    width: 1.5
                }
            },
            {
                name: 'MACD',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: data.macd ? data.macd.macd : [],
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#FF6B6B',
                    width: 1.5
                }
            },
            {
                name: 'Signal',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: data.macd ? data.macd.signal : [],
                smooth: false,
                showSymbol: false,
                lineStyle: {
                    color: '#4ECDC4',
                    width: 1.5
                }
            },
            {
                name: 'Histogram',
                type: 'bar',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: data.macd ? data.macd.histogram : [],
                itemStyle: {
                    color: function(params) {
                        return params.value >= 0 ? '#ec4848' : '#00b386';
                    },
                    opacity: 0.6
                }
            }
        ]
    };
    
    klineChartInstance.setOption(option, true);
    
    // 添加窗口resize事件
    window.addEventListener('resize', function() {
        if (klineChartInstance) {
            klineChartInstance.resize();
        }
    });
}

function renderIndicatorCharts(data) {
    // 切换到技术指标标签页时才渲染
    switchTab('indicators');
    
    // RSI图表
    if (!rsiChartInstance) {
        rsiChartInstance = echarts.init(document.getElementById('rsiChart'));
    }
    
    rsiChartInstance.setOption({
        title: {
            text: 'RSI 相对强弱指标',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: data.dates
        },
        yAxis: {
            type: 'value',
            min: 0,
            max: 100
        },
        dataZoom: [
            {
                type: 'inside',
                start: 70,
                end: 100
            }
        ],
        series: [
            {
                name: 'RSI',
                type: 'line',
                data: data.rsi,
                markLine: {
                    data: [
                        { yAxis: 30, lineStyle: { color: '#26de81' } },
                        { yAxis: 70, lineStyle: { color: '#fc5c65' } }
                    ]
                }
            }
        ]
    });
    
    // MACD图表
    if (!macdChartInstance) {
        macdChartInstance = echarts.init(document.getElementById('macdChart'));
    }
    
    macdChartInstance.setOption({
        title: {
            text: 'MACD 指标',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: ['MACD', 'Signal', 'Histogram'],
            top: 30
        },
        xAxis: {
            type: 'category',
            data: data.dates
        },
        yAxis: {
            type: 'value'
        },
        dataZoom: [
            {
                type: 'inside',
                start: 70,
                end: 100
            }
        ],
        series: [
            {
                name: 'MACD',
                type: 'line',
                data: data.macd.macd
            },
            {
                name: 'Signal',
                type: 'line',
                data: data.macd.signal
            },
            {
                name: 'Histogram',
                type: 'bar',
                data: data.macd.histogram
            }
        ]
    });
    
    // KDJ图表
    if (!kdjChartInstance) {
        kdjChartInstance = echarts.init(document.getElementById('kdjChart'));
    }
    
    kdjChartInstance.setOption({
        title: {
            text: 'KDJ 随机指标',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: ['K', 'D', 'J'],
            top: 30
        },
        xAxis: {
            type: 'category',
            data: data.dates
        },
        yAxis: {
            type: 'value',
            min: 0,
            max: 100
        },
        dataZoom: [
            {
                type: 'inside',
                start: 70,
                end: 100
            }
        ],
        series: [
            {
                name: 'K',
                type: 'line',
                data: data.kdj.k
            },
            {
                name: 'D',
                type: 'line',
                data: data.kdj.d
            },
            {
                name: 'J',
                type: 'line',
                data: data.kdj.j
            }
        ]
    });
    
    // 切回K线图
    switchTab('kline');
}

// 窗口大小改变时重绘图表
window.addEventListener('resize', function() {
    if (klineChartInstance) klineChartInstance.resize();
    if (rsiChartInstance) rsiChartInstance.resize();
    if (macdChartInstance) macdChartInstance.resize();
    if (kdjChartInstance) kdjChartInstance.resize();
});

// ==================== 监控任务管理 ====================

async function showMonitorTaskDialog() {
    if (!currentSymbol) {
        showNotification('请先选择一个监控项', 'warning');
        return;
    }
    
    document.getElementById('monitorTaskDialog').classList.add('show');
    await loadMonitorTasks();
}

async function loadMonitorTasks() {
    try {
        const result = await apiCall(`/monitor/tasks?symbol=${currentSymbol}`);
        
        if (result.success) {
            renderMonitorTasks(result.data);
        }
    } catch (error) {
        console.error('加载监控任务失败:', error);
    }
}

function renderMonitorTasks(tasks) {
    const tbody = document.getElementById('tasksBody');
    tbody.innerHTML = '';
    
    if (!tasks || tasks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #999;">暂无监控任务</td></tr>';
        return;
    }
    
    tasks.forEach(task => {
        const row = document.createElement('tr');
        
        const conditions = JSON.parse(task.conditions || '[]');
        const conditionsText = conditions.map(c => c.expression || c.description).join('; ');
        
        const statusBadge = task.enabled ? 
            '<span class="status-badge status-enabled">启用</span>' : 
            '<span class="status-badge status-disabled">禁用</span>';
        
        const lastCheck = task.last_check || '从未';
        
        row.innerHTML = `
            <td>${task.id}</td>
            <td>${task.task_name}</td>
            <td style="font-size: 12px; word-break: break-all;">${conditionsText}</td>
            <td>${task.email}</td>
            <td>${statusBadge}</td>
            <td style="font-size: 11px;">${lastCheck}</td>
            <td>
                <button class="btn btn-sm ${task.enabled ? 'btn-secondary' : 'btn-info'}" 
                        onclick="toggleTask(${task.id}, ${!task.enabled})">
                    ${task.enabled ? '禁用' : '启用'}
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">删除</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

function showAddTaskForm() {
    document.getElementById('addTaskForm').style.display = 'block';
    // 初始化表单
    document.getElementById('taskName').value = `${currentName}监控任务`;
    document.getElementById('taskEmail').value = '';
    document.getElementById('taskInterval').value = '60';
    
    // 清空条件列表
    const conditionsList = document.getElementById('conditionsList');
    conditionsList.innerHTML = `
        <div class="condition-item">
            <input type="text" class="condition-expr" placeholder="例如：([CLOSE,0,c]-[MA,0,c,20])/[MA,0,c,20]<-8%">
            <button class="btn btn-sm btn-danger" onclick="removeCondition(this)">删除</button>
        </div>
    `;
}

function cancelAddTask() {
    document.getElementById('addTaskForm').style.display = 'none';
}

function addConditionInput() {
    const conditionsList = document.getElementById('conditionsList');
    const newCondition = document.createElement('div');
    newCondition.className = 'condition-item';
    newCondition.innerHTML = `
        <input type="text" class="condition-expr" placeholder="输入监控条件表达式">
        <button class="btn btn-sm btn-danger" onclick="removeCondition(this)">删除</button>
    `;
    conditionsList.appendChild(newCondition);
}

function removeCondition(button) {
    const conditionsList = document.getElementById('conditionsList');
    if (conditionsList.children.length > 1) {
        button.parentElement.remove();
    } else {
        showNotification('至少保留一个条件', 'warning');
    }
}

async function confirmAddTask() {
    const taskName = document.getElementById('taskName').value.trim();
    const email = document.getElementById('taskEmail').value.trim();
    const interval = parseInt(document.getElementById('taskInterval').value);
    
    if (!taskName || !email) {
        showNotification('请填写任务名称和邮箱', 'warning');
        return;
    }
    
    // 收集所有条件
    const conditionInputs = document.querySelectorAll('.condition-expr');
    const conditions = [];
    
    for (let input of conditionInputs) {
        const expr = input.value.trim();
        if (expr) {
            conditions.push({
                type: 'expression',
                expression: expr,
                description: expr,
                value: 'N/A'
            });
        }
    }
    
    if (conditions.length === 0) {
        showNotification('请至少添加一个监控条件', 'warning');
        return;
    }
    
    try {
        setStatus('创建中...', 'loading');
        
        const result = await apiCall('/monitor/tasks', {
            method: 'POST',
            body: JSON.stringify({
                symbol: currentSymbol,
                task_name: taskName,
                conditions: conditions,
                email: email,
                check_interval: interval
            })
        });
        
        if (result.success) {
            showNotification('监控任务创建成功', 'success');
            cancelAddTask();
            await loadMonitorTasks();
        }
        
        setStatus('就绪', 'ready');
    } catch (error) {
        setStatus('创建失败', 'error');
    }
}

async function toggleTask(taskId, enabled) {
    try {
        const result = await apiCall(`/monitor/tasks/${taskId}/toggle`, {
            method: 'POST',
            body: JSON.stringify({ enabled: enabled })
        });
        
        if (result.success) {
            showNotification(result.message, 'success');
            await loadMonitorTasks();
        }
    } catch (error) {
        console.error('切换任务状态失败:', error);
    }
}

async function deleteTask(taskId) {
    if (!confirm('确定要删除这个监控任务吗？')) {
        return;
    }
    
    try {
        const result = await apiCall(`/monitor/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (result.success) {
            showNotification('任务已删除', 'success');
            await loadMonitorTasks();
        }
    } catch (error) {
        console.error('删除任务失败:', error);
    }
}

async function testEmail() {
    const email = prompt('请输入要接收测试邮件的邮箱地址：');
    
    if (!email) {
        return;
    }
    
    try {
        setStatus('发送中...', 'loading');
        
        const result = await apiCall('/monitor/test-email', {
            method: 'POST',
            body: JSON.stringify({ email: email })
        });
        
        if (result.success) {
            showNotification('测试邮件发送成功，请检查收件箱', 'success');
        }
        
        setStatus('就绪', 'ready');
    } catch (error) {
        setStatus('发送失败', 'error');
        showNotification('邮件发送失败，请检查邮件配置', 'error');
    }
}
