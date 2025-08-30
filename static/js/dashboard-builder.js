class DashboardBuilder {
    constructor() {
        this.widgets = [];
        this.filters = {};
        this.initDragDrop();
        this.loadDefaultPreset();
    }
    
    initDragDrop() {
        const widgetItems = document.querySelectorAll('.widget-item');
        const dashboardPreview = document.getElementById('dashboardPreview');
        
        // Make widget items draggable
        widgetItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.effectAllowed = 'copy';
                e.dataTransfer.setData('widgetType', item.dataset.widgetType);
                e.dataTransfer.setData('widgetTitle', item.textContent.trim());
            });
        });
        
        // Set up drop zone
        dashboardPreview.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            dashboardPreview.classList.add('drag-over');
        });
        
        dashboardPreview.addEventListener('dragleave', (e) => {
            if (e.target === dashboardPreview) {
                dashboardPreview.classList.remove('drag-over');
            }
        });
        
        dashboardPreview.addEventListener('drop', (e) => {
            e.preventDefault();
            dashboardPreview.classList.remove('drag-over');
            
            const widgetType = e.dataTransfer.getData('widgetType');
            const widgetTitle = e.dataTransfer.getData('widgetTitle');
            
            if (widgetType) {
                this.addWidget(widgetType, widgetTitle);
            }
        });
    }
    
    addWidget(type, title, size = 'medium') {
        const widgetId = 'widget-' + Date.now();
        const widget = {
            id: widgetId,
            type: type,
            title: title,
            size: size
        };
        
        this.widgets.push(widget);
        this.renderWidget(widget);
        this.updateWidgetData(widget);
    }
    
    renderWidget(widget) {
        const dashboardPreview = document.getElementById('dashboardPreview');
        
        // Clear empty state message if this is the first widget
        if (this.widgets.length === 1) {
            dashboardPreview.innerHTML = '';
        }
        
        const widgetElement = document.createElement('div');
        widgetElement.className = `dashboard-widget ${widget.size}`;
        widgetElement.id = widget.id;
        widgetElement.innerHTML = `
            <div class="widget-controls">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-sm btn-outline-secondary" onclick="dashboardBuilder.resizeWidget('${widget.id}')">
                        <i class="fas fa-expand"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="dashboardBuilder.removeWidget('${widget.id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <h6>${widget.title}</h6>
            <div class="widget-content" id="${widget.id}-content">
                <div class="text-center py-3">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            </div>
        `;
        
        dashboardPreview.appendChild(widgetElement);
    }
    
    updateWidgetData(widget) {
        const filters = this.getActiveFilters();
        
        // For chart widgets, fetch data and render
        if (widget.type.includes('pie') || widget.type.includes('bar') || 
            widget.type.includes('line') || widget.type.includes('area')) {
            this.fetchAndRenderChart(widget, filters);
        } else {
            // For stat widgets, fetch specific data
            this.fetchWidgetData(widget, filters);
        }
    }
    
    fetchAndRenderChart(widget, filters) {
        const params = new URLSearchParams(filters);
        
        fetch(`/api/expense_data?${params}`)
            .then(response => response.json())
            .then(data => {
                const contentEl = document.getElementById(`${widget.id}-content`);
                contentEl.innerHTML = `<canvas id="${widget.id}-chart"></canvas>`;
                
                const ctx = document.getElementById(`${widget.id}-chart`).getContext('2d');
                let chartConfig = {};
                
                if (widget.type === 'category-pie') {
                    chartConfig = {
                        type: 'pie',
                        data: {
                            labels: data.categories.labels,
                            datasets: [{
                                data: data.categories.data,
                                backgroundColor: this.generateColors(data.categories.labels.length)
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    };
                } else if (widget.type === 'category-bar') {
                    chartConfig = {
                        type: 'bar',
                        data: {
                            labels: data.categories.labels,
                            datasets: [{
                                label: 'Amount',
                                data: data.categories.data,
                                backgroundColor: '#0d6efd'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    };
                } else if (widget.type === 'payment-pie') {
                    chartConfig = {
                        type: 'pie',
                        data: {
                            labels: data.payment_methods.labels,
                            datasets: [{
                                data: data.payment_methods.data,
                                backgroundColor: this.generateColors(data.payment_methods.labels.length)
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    };
                } else if (widget.type === 'payment-bar') {
                    chartConfig = {
                        type: 'bar',
                        data: {
                            labels: data.payment_methods.labels,
                            datasets: [{
                                label: 'Amount',
                                data: data.payment_methods.data,
                                backgroundColor: '#28a745'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    };
                } else if (widget.type === 'trend-line') {
                    chartConfig = {
                        type: 'line',
                        data: {
                            labels: data.daily_trend.labels,
                            datasets: [{
                                label: 'Daily Spending',
                                data: data.daily_trend.data,
                                borderColor: '#0d6efd',
                                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    };
                } else if (widget.type === 'trend-area') {
                    chartConfig = {
                        type: 'line',
                        data: {
                            labels: data.daily_trend.labels,
                            datasets: [{
                                label: 'Daily Spending',
                                data: data.daily_trend.data,
                                borderColor: '#0d6efd',
                                backgroundColor: 'rgba(13, 110, 253, 0.3)',
                                fill: true,
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    };
                } else if (widget.type === 'reimbursement-breakdown') {
                    const reimbursementData = [
                        data.reimbursement_stats.pending,
                        data.reimbursement_stats.approved,
                        data.reimbursement_stats.received
                    ];
                    chartConfig = {
                        type: 'doughnut',
                        data: {
                            labels: ['Pending', 'Approved', 'Received'],
                            datasets: [{
                                data: reimbursementData,
                                backgroundColor: ['#ffc107', '#17a2b8', '#28a745']
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    };
                }
                
                new Chart(ctx, chartConfig);
            })
            .catch(error => {
                document.getElementById(`${widget.id}-content`).innerHTML = 
                    '<div class="alert alert-danger">Failed to load data</div>';
            });
    }
    
    fetchWidgetData(widget, filters) {
        const params = new URLSearchParams({...filters, type: widget.type});
        
        fetch(`/api/widgets/data?${params}`)
            .then(response => response.json())
            .then(data => {
                const contentEl = document.getElementById(`${widget.id}-content`);
                
                if (widget.type === 'total-spent' || widget.type === 'reimbursable-amount') {
                    contentEl.innerHTML = `
                        <div class="text-center">
                            <h2 class="text-primary">$${(data.value || 0).toFixed(2)}</h2>
                        </div>
                    `;
                } else if (widget.type === 'pending-reimbursements') {
                    contentEl.innerHTML = `
                        <div class="text-center">
                            <h3>${data.count || 0} Items</h3>
                            <p class="text-muted">Total: $${(data.total || 0).toFixed(2)}</p>
                        </div>
                    `;
                } else if (widget.type === 'expense-count') {
                    fetch(`/api/expense_data?${new URLSearchParams(filters)}`)
                        .then(r => r.json())
                        .then(d => {
                            contentEl.innerHTML = `
                                <div class="text-center">
                                    <h2 class="text-info">${d.expense_count || 0}</h2>
                                </div>
                            `;
                        });
                } else if (widget.type === 'avg-expense') {
                    fetch(`/api/expense_data?${new URLSearchParams(filters)}`)
                        .then(r => r.json())
                        .then(d => {
                            const avg = d.expense_count > 0 ? d.total_expenses / d.expense_count : 0;
                            contentEl.innerHTML = `
                                <div class="text-center">
                                    <h2 class="text-warning">$${avg.toFixed(2)}</h2>
                                </div>
                            `;
                        });
                } else if (widget.type === 'recent-expenses') {
                    let tableHtml = '<div class="table-responsive"><table class="table table-sm">';
                    tableHtml += '<thead><tr><th>Title</th><th>Amount</th></tr></thead><tbody>';
                    data.forEach(expense => {
                        tableHtml += `<tr>
                            <td>${expense.title}</td>
                            <td>$${expense.amount.toFixed(2)}</td>
                        </tr>`;
                    });
                    tableHtml += '</tbody></table></div>';
                    contentEl.innerHTML = tableHtml;
                } else if (widget.type === 'top-categories') {
                    fetch(`/api/expense_data?${new URLSearchParams(filters)}`)
                        .then(r => r.json())
                        .then(d => {
                            let tableHtml = '<div class="table-responsive"><table class="table table-sm">';
                            tableHtml += '<thead><tr><th>Category</th><th>Amount</th></tr></thead><tbody>';
                            
                            const categories = d.categories.labels.map((label, i) => ({
                                label: label,
                                value: d.categories.data[i]
                            })).sort((a, b) => b.value - a.value).slice(0, 5);
                            
                            categories.forEach(cat => {
                                tableHtml += `<tr>
                                    <td>${cat.label}</td>
                                    <td>$${cat.value.toFixed(2)}</td>
                                </tr>`;
                            });
                            tableHtml += '</tbody></table></div>';
                            contentEl.innerHTML = tableHtml;
                        });
                }
            })
            .catch(error => {
                document.getElementById(`${widget.id}-content`).innerHTML = 
                    '<div class="alert alert-danger">Failed to load data</div>';
            });
    }
    
    removeWidget(widgetId) {
        this.widgets = this.widgets.filter(w => w.id !== widgetId);
        document.getElementById(widgetId).remove();
        
        if (this.widgets.length === 0) {
            document.getElementById('dashboardPreview').innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-arrow-left fa-3x mb-3"></i>
                    <p>Drag widgets from the left panel to build your dashboard</p>
                </div>
            `;
        }
    }
    
    resizeWidget(widgetId) {
        const widget = this.widgets.find(w => w.id === widgetId);
        const element = document.getElementById(widgetId);
        
        if (widget && element) {
            const sizes = ['small', 'medium', 'large', 'full'];
            const currentIndex = sizes.indexOf(widget.size);
            const newIndex = (currentIndex + 1) % sizes.length;
            const newSize = sizes[newIndex];
            
            element.classList.remove(widget.size);
            element.classList.add(newSize);
            widget.size = newSize;
        }
    }
    
    getActiveFilters() {
        const filters = {
            period: document.getElementById('periodFilter').value
        };
        
        // Categories
        const categoryFilters = Array.from(document.querySelectorAll('.category-filter:checked'))
            .map(cb => cb.value);
        if (categoryFilters.length > 0 && categoryFilters.length < document.querySelectorAll('.category-filter').length) {
            filters['categories[]'] = categoryFilters;
        }
        
        // Payment methods
        const paymentFilters = Array.from(document.querySelectorAll('.payment-filter:checked'))
            .map(cb => cb.value);
        if (paymentFilters.length > 0 && paymentFilters.length < document.querySelectorAll('.payment-filter').length) {
            filters['payment_methods[]'] = paymentFilters;
        }
        
        // Reimbursable
        if (document.getElementById('reimbursableOnly').checked) {
            filters.reimbursable_only = 'true';
        }
        
        const reimbursementStatus = document.getElementById('reimbursementStatus').value;
        if (reimbursementStatus !== 'all') {
            filters.reimbursement_status = reimbursementStatus;
        }
        
        // Amount range
        const minAmount = document.getElementById('minAmount').value;
        const maxAmount = document.getElementById('maxAmount').value;
        if (minAmount) filters.min_amount = minAmount;
        if (maxAmount) filters.max_amount = maxAmount;
        
        this.filters = filters;
        return filters;
    }
    
    updateFilters() {
        this.getActiveFilters();
        this.widgets.forEach(widget => this.updateWidgetData(widget));
    }
    
    savePreset(name, isDefault) {
        const config = {
            widgets: this.widgets,
            layout: 'grid'
        };
        
        const presetData = {
            name: name,
            is_default: isDefault,
            config: config,
            filters: this.filters
        };
        
        fetch('/api/dashboard/presets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(presetData)
        })
        .then(response => response.json())
        .then(data => {
            alert('Preset saved successfully!');
            location.reload();
        })
        .catch(error => {
            alert('Failed to save preset');
        });
    }
    
    loadPreset(presetId) {
        fetch(`/api/dashboard/presets/${presetId}`)
            .then(response => response.json())
            .then(data => {
                // Clear current widgets
                this.widgets = [];
                document.getElementById('dashboardPreview').innerHTML = '';
                
                // Load filters
                if (data.filters) {
                    this.applyFilters(data.filters);
                }
                
                // Load widgets
                if (data.config && data.config.widgets) {
                    data.config.widgets.forEach(widget => {
                        this.addWidget(widget.type, widget.title, widget.size);
                    });
                }
            })
            .catch(error => {
                alert('Failed to load preset');
            });
    }
    
    applyFilters(filters) {
        if (filters.period) {
            document.getElementById('periodFilter').value = filters.period;
        }
        
        // Reset all checkboxes first
        document.querySelectorAll('.category-filter, .payment-filter').forEach(cb => cb.checked = false);
        
        if (filters['categories[]']) {
            filters['categories[]'].forEach(catId => {
                const checkbox = document.querySelector(`.category-filter[value="${catId}"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
        
        if (filters['payment_methods[]']) {
            filters['payment_methods[]'].forEach(pmId => {
                const checkbox = document.querySelector(`.payment-filter[value="${pmId}"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
        
        if (filters.reimbursable_only === 'true') {
            document.getElementById('reimbursableOnly').checked = true;
        }
        
        if (filters.reimbursement_status) {
            document.getElementById('reimbursementStatus').value = filters.reimbursement_status;
        }
        
        if (filters.min_amount) {
            document.getElementById('minAmount').value = filters.min_amount;
        }
        
        if (filters.max_amount) {
            document.getElementById('maxAmount').value = filters.max_amount;
        }
        
        this.filters = filters;
    }
    
    deletePreset(presetId) {
        fetch(`/api/dashboard/presets/${presetId}`, {
            method: 'DELETE'
        })
        .then(() => {
            alert('Preset deleted successfully!');
            location.reload();
        })
        .catch(error => {
            alert('Failed to delete preset');
        });
    }
    
    setDefaultPreset(presetId) {
        fetch(`/api/dashboard/presets/${presetId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_default: true })
        })
        .then(response => response.json())
        .then(data => {
            alert('Default preset updated!');
            location.reload();
        })
        .catch(error => {
            alert('Failed to set default preset');
        });
    }
    
    loadDefaultPreset() {
        const defaultOption = document.querySelector('#presetSelect option[selected]');
        if (defaultOption && defaultOption.value) {
            this.loadPreset(defaultOption.value);
        }
    }
    
    generateColors(count) {
        const colors = [
            '#0d6efd', '#28a745', '#dc3545', '#ffc107', 
            '#17a2b8', '#6f42c1', '#fd7e14', '#20c997',
            '#e83e8c', '#6c757d'
        ];
        
        const result = [];
        for (let i = 0; i < count; i++) {
            result.push(colors[i % colors.length]);
        }
        return result;
    }
}

// Make dashboardBuilder available globally
window.dashboardBuilder = null;
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardBuilder = new DashboardBuilder();
});