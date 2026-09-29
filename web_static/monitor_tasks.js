// ==================== 监控任务管理功能 ====================

// 辅助函数：解析策略字符串为数组
function parseStrategies(strategyStr) {
    if (!strategyStr) return ['default'];
    
    try {
        // 尝试解析 JSON 数组
        const parsed = JSON.parse(strategyStr);
        return Array.isArray(parsed) ? parsed : [strategyStr];
    } catch {
        // 如果不是 JSON，返回单个策略
        return [strategyStr];
    }
}

// 辅助函数：格式化策略显示
function formatStrategies(strategyStr) {
    const strategies = parseStrategies(strategyStr);
    if (strategies.length === 1) {
        return strategies[0];
    }
    return `${strategies.length}个策略`;
}

// 显示监控任务标签页时加载数据
function loadMonitorTasksTab() {
    loadMonitorTasksList();
    loadWatchlistForMonitor();
    loadStrategiesForMonitor();
}

// 加载监控列表到下拉框
function loadWatchlistForMonitor() {
    fetch('/api/watchlist')
        .then(response => response.json())
        .then(result => {
            if (result.success && result.data) {
                const select = document.getElementById('monitorSymbol');
                select.innerHTML = '<option value="">-- 请从监控列表选择 --</option>';
                
                result.data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.symbol;
                    option.textContent = `${item.symbol} - ${item.name}`;
                    option.dataset.name = item.name;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('加载监控列表失败:', error);
        });
}

// 加载策略列表到下拉框
function loadStrategiesForMonitor() {
    fetch('/api/strategies')
        .then(response => response.json())
        .then(result => {
            if (result.success && result.data) {
                const select = document.getElementById('monitorStrategy');
                select.innerHTML = '';
                
                result.data.forEach(strategy => {
                    const option = document.createElement('option');
                    option.value = strategy.name;
                    option.textContent = strategy.description || strategy.name;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('加载策略列表失败:', error);
            // 使用默认值
            const select = document.getElementById('monitorStrategy');
            select.innerHTML = '<option value="default">默认策略</option>';
        });
}

// 加载监控任务列表
function loadMonitorTasksList() {
    fetch('/api/monitor/tasks')
        .then(response => response.json())
        .then(result => {
            if (result.success && result.data) {
                renderMonitorTasksList(result.data);
            }
        })
        .catch(error => {
            console.error('加载监控任务失败:', error);
            showNotification('加载监控任务失败', 'error');
        });
}

// 渲染监控任务列表
function renderMonitorTasksList(tasks) {
    const tbody = document.getElementById('monitorTasksBody');
    
    if (!tasks || tasks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="info-placeholder">暂无监控任务，点击"添加任务"创建</td></tr>';
        return;
    }
    
    tbody.innerHTML = tasks.map(task => `
        <tr>
            <td>${task.id}</td>
            <td>${task.symbol}</td>
            <td>${task.task_name}</td>
            <td>${task.email}</td>
            <td>${task.update_schedule || '-'}</td>
            <td>${task.scan_schedule || '-'}</td>
            <td>${formatStrategies(task.strategy)}</td>
            <td>
                <span class="status-badge ${task.enabled ? 'status-enabled' : 'status-disabled'}">
                    ${task.enabled ? '运行中' : '已暂停'}
                </span>
            </td>
            <td>${task.last_scan ? new Date(task.last_scan).toLocaleString('zh-CN', {month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'}) : '-'}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="editMonitorTask(${task.id})">✏️ 编辑</button>
                ${task.enabled ? 
                    `<button class="btn btn-sm btn-warning" onclick="pauseMonitorTask(${task.id})">⏸ 暂停</button>` :
                    `<button class="btn btn-sm btn-success" onclick="resumeMonitorTask(${task.id})">▶ 恢复</button>`
                }
                <button class="btn btn-sm btn-danger" onclick="deleteMonitorTask(${task.id})">🗑 删除</button>
            </td>
        </tr>
    `).join('');
}

// 显示添加任务表单
function showAddMonitorTaskForm() {
    const form = document.getElementById('addMonitorTaskForm');
    const title = document.getElementById('taskFormTitle');
    
    // 设置为新建模式
    title.textContent = '新建监控任务';
    document.getElementById('editTaskId').value = '';
    
    // 重置表单
    document.getElementById('monitorSymbol').value = '';
    document.getElementById('monitorSymbol').disabled = false;
    document.getElementById('monitorTaskName').value = '';
    document.getElementById('monitorEmail').value = '';
    document.getElementById('monitorUpdateTime').value = '09:30';
    document.getElementById('monitorScanTime').value = '15:30';
    document.getElementById('monitorStrategy').value = 'default';
    document.getElementById('monitorRemark').value = '';
    
    form.style.display = 'block';
    
    // 滚动到表单位置
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 编辑监控任务
function editMonitorTask(taskId) {
    // 获取任务详情
    fetch('/api/monitor/tasks')
        .then(response => response.json())
        .then(result => {
            if (result.success && result.data) {
                const task = result.data.find(t => t.id === taskId);
                if (task) {
                    showEditMonitorTaskForm(task);
                } else {
                    showNotification('任务不存在', 'error');
                }
            }
        })
        .catch(error => {
            console.error('获取任务详情失败:', error);
            showNotification('获取任务详情失败', 'error');
        });
}

// 显示编辑任务表单
function showEditMonitorTaskForm(task) {
    const form = document.getElementById('addMonitorTaskForm');
    const title = document.getElementById('taskFormTitle');
    
    // 设置为编辑模式
    title.textContent = '编辑监控任务';
    document.getElementById('editTaskId').value = task.id;
    
    // 填充表单数据
    document.getElementById('monitorSymbol').value = task.symbol;
    document.getElementById('monitorSymbol').disabled = true;  // 编辑时不允许修改指数
    document.getElementById('monitorTaskName').value = task.task_name;
    document.getElementById('monitorEmail').value = task.email;
    document.getElementById('monitorUpdateTime').value = task.update_schedule || '09:30';
    document.getElementById('monitorScanTime').value = task.scan_schedule || '15:30';
    
    // 处理多选策略
    const strategySelect = document.getElementById('monitorStrategy');
    const strategies = parseStrategies(task.strategy);
    Array.from(strategySelect.options).forEach(option => {
        option.selected = strategies.includes(option.value);
    });
    
    document.getElementById('monitorRemark').value = task.remark || '';
    
    form.style.display = 'block';
    
    // 滚动到表单位置
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 取消表单
function cancelMonitorTaskForm() {
    const form = document.getElementById('addMonitorTaskForm');
    form.style.display = 'none';
    document.getElementById('editTaskId').value = '';
    document.getElementById('monitorSymbol').disabled = false;
}

// 保存任务（新建或编辑）
function saveMonitorTask() {
    const editTaskId = document.getElementById('editTaskId').value;
    
    if (editTaskId) {
        // 编辑模式
        updateMonitorTask(parseInt(editTaskId));
    } else {
        // 新建模式
        createMonitorTask();
    }
}

// 创建新任务
function createMonitorTask() {
    const symbol = document.getElementById('monitorSymbol').value;
    const taskName = document.getElementById('monitorTaskName').value;
    const email = document.getElementById('monitorEmail').value;
    const updateSchedule = document.getElementById('monitorUpdateTime').value;
    const scanSchedule = document.getElementById('monitorScanTime').value;
    
    // 获取所有选中的策略
    const strategySelect = document.getElementById('monitorStrategy');
    const selectedStrategies = Array.from(strategySelect.selectedOptions).map(opt => opt.value);
    const strategy = selectedStrategies.length > 0 ? JSON.stringify(selectedStrategies) : JSON.stringify(['default']);
    
    const remark = document.getElementById('monitorRemark').value;
    
    // 验证必填字段
    if (!symbol) {
        showNotification('请选择要监控的指数', 'error');
        return;
    }
    if (!taskName) {
        showNotification('请输入任务名称', 'error');
        return;
    }
    if (!email) {
        showNotification('请输入接收邮箱', 'error');
        return;
    }
    
    // 验证邮箱格式
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        showNotification('请输入有效的邮箱地址', 'error');
        return;
    }
    
    // 验证时间格式
    const timePattern = /^([01]\d|2[0-3]):([0-5]\d)$/;
    if (!timePattern.test(updateSchedule) || !timePattern.test(scanSchedule)) {
        showNotification('时间格式不正确，请使用HH:MM格式', 'error');
        return;
    }
    
    const data = {
        symbol,
        task_name: taskName,
        email,
        update_schedule: updateSchedule,
        scan_schedule: scanSchedule,
        strategy,
        remark
    };
    
    setStatus('loading', '创建任务中...');
    
    fetch('/api/monitor/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification('任务创建成功', 'success');
            cancelMonitorTaskForm();
            loadMonitorTasksList();
            reloadScheduler();  // 重新加载调度器
            setStatus('ready');
        } else {
            showNotification(result.message || '创建失败', 'error');
            setStatus('ready');
        }
    })
    .catch(error => {
        console.error('创建任务失败:', error);
        showNotification('创建任务失败', 'error');
        setStatus('ready');
    });
}

// 更新任务
function updateMonitorTask(taskId) {
    const taskName = document.getElementById('monitorTaskName').value;
    const email = document.getElementById('monitorEmail').value;
    const updateSchedule = document.getElementById('monitorUpdateTime').value;
    const scanSchedule = document.getElementById('monitorScanTime').value;
    
    // 获取所有选中的策略
    const strategySelect = document.getElementById('monitorStrategy');
    const selectedStrategies = Array.from(strategySelect.selectedOptions).map(opt => opt.value);
    const strategy = selectedStrategies.length > 0 ? JSON.stringify(selectedStrategies) : JSON.stringify(['default']);
    
    const remark = document.getElementById('monitorRemark').value;
    
    // 验证必填字段
    if (!taskName) {
        showNotification('请输入任务名称', 'error');
        return;
    }
    if (!email) {
        showNotification('请输入接收邮箱', 'error');
        return;
    }
    
    // 验证邮箱格式
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        showNotification('请输入有效的邮箱地址', 'error');
        return;
    }
    
    // 验证时间格式
    const timePattern = /^([01]\d|2[0-3]):([0-5]\d)$/;
    if (!timePattern.test(updateSchedule) || !timePattern.test(scanSchedule)) {
        showNotification('时间格式不正确，请使用HH:MM格式', 'error');
        return;
    }
    
    const data = {
        task_name: taskName,
        email,
        update_schedule: updateSchedule,
        scan_schedule: scanSchedule,
        strategy,
        remark
    };
    
    setStatus('loading', '更新任务中...');
    
    fetch(`/api/monitor/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification('任务更新成功', 'success');
            cancelMonitorTaskForm();
            loadMonitorTasksList();
            reloadScheduler();  // 重新加载调度器
            setStatus('ready');
        } else {
            showNotification(result.message || '更新失败', 'error');
            setStatus('ready');
        }
    })
    .catch(error => {
        console.error('更新任务失败:', error);
        showNotification('更新任务失败', 'error');
        setStatus('ready');
    });
}

// 暂停监控任务
function pauseMonitorTask(taskId) {
    if (!confirm('确定要暂停这个任务吗？')) {
        return;
    }
    
    fetch(`/api/monitor/tasks/${taskId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: false })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification('任务已暂停', 'success');
            loadMonitorTasksList();
            reloadScheduler();  // 重新加载调度器
        } else {
            showNotification(result.message || '操作失败', 'error');
        }
    })
    .catch(error => {
        console.error('暂停任务失败:', error);
        showNotification('操作失败', 'error');
    });
}

// 恢复监控任务
function resumeMonitorTask(taskId) {
    fetch(`/api/monitor/tasks/${taskId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: true })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification('任务已恢复', 'success');
            loadMonitorTasksList();
            reloadScheduler();  // 重新加载调度器
        } else {
            showNotification(result.message || '操作失败', 'error');
        }
    })
    .catch(error => {
        console.error('恢复任务失败:', error);
        showNotification('操作失败', 'error');
    });
}

// 删除监控任务
function deleteMonitorTask(taskId) {
    if (!confirm('确定要删除这个任务吗？此操作不可恢复！')) {
        return;
    }
    
    fetch(`/api/monitor/tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification('任务已删除', 'success');
            loadMonitorTasksList();
            reloadScheduler();  // 重新加载调度器
        } else {
            showNotification(result.message || '删除失败', 'error');
        }
    })
    .catch(error => {
        console.error('删除任务失败:', error);
        showNotification('删除失败', 'error');
    });
}

// 测试邮件发送
function testMonitorEmail() {
    const email = prompt('请输入要测试的邮箱地址：');
    
    if (!email) {
        return;
    }
    
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        showNotification('请输入有效的邮箱地址', 'error');
        return;
    }
    
    setStatus('loading', '发送测试邮件中...');
    
    fetch('/api/monitor/test-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification('测试邮件已发送，请查收', 'success');
            setStatus('ready');
        } else {
            showNotification(result.message || '发送失败', 'error');
            setStatus('ready');
        }
    })
    .catch(error => {
        console.error('发送测试邮件失败:', error);
        showNotification('发送失败', 'error');
        setStatus('ready');
    });
}

// 重新加载调度器
function reloadScheduler() {
    fetch('/api/monitor/scheduler/reload', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('[Monitor] 调度器已重新加载');
        } else {
            console.error('[Monitor] 调度器重新加载失败');
        }
    })
    .catch(error => {
        console.error('[Monitor] 调度器重新加载失败:', error);
    });
}
