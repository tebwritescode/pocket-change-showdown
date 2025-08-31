// Expense Table Column Management
(function() {
    // Default column configuration
    const defaultColumns = {
        'date': { label: 'Date', visible: true, order: 1 },
        'title': { label: 'Title', visible: true, order: 2 },
        'description': { label: 'Description', visible: false, order: 3 },
        'category': { label: 'Category', visible: true, order: 4 },
        'payment': { label: 'Payment Method', visible: true, order: 5 },
        'amount': { label: 'Amount', visible: true, order: 6 },
        'location': { label: 'Location', visible: false, order: 7 },
        'vendor': { label: 'Vendor', visible: false, order: 8 },
        'notes': { label: 'Notes', visible: false, order: 9 },
        'tags': { label: 'Tags', visible: false, order: 10 },
        'reimbursable': { label: 'Reimbursable', visible: true, order: 11 },
        'reimbursement_status': { label: 'Reimbursement Status', visible: false, order: 12 },
        'reimbursement_notes': { label: 'Reimbursement Notes', visible: false, order: 13 },
        'receipt': { label: 'Receipt', visible: true, order: 14 },
        'created_at': { label: 'Created', visible: false, order: 15 },
        'updated_at': { label: 'Updated', visible: false, order: 16 },
        'actions': { label: 'Actions', visible: true, order: 17, fixed: true }
    };

    // Load saved preferences from localStorage
    function loadColumnPreferences() {
        const saved = localStorage.getItem('expenseTableColumns');
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error('Failed to parse saved column preferences:', e);
            }
        }
        return defaultColumns;
    }

    // Save preferences to localStorage
    function saveColumnPreferences(columns) {
        localStorage.setItem('expenseTableColumns', JSON.stringify(columns));
    }

    // Apply column visibility based on preferences
    function applyColumnVisibility() {
        const columns = loadColumnPreferences();
        const table = document.getElementById('expenseTable');
        
        if (!table) return;
        
        // Hide/show columns based on preferences
        Object.keys(columns).forEach((columnKey, index) => {
            const column = columns[columnKey];
            const columnIndex = getColumnIndex(columnKey);
            
            if (columnIndex !== -1) {
                // Apply to header
                const headers = table.querySelectorAll('thead th');
                if (headers[columnIndex]) {
                    headers[columnIndex].style.display = column.visible ? '' : 'none';
                }
                
                // Apply to all rows
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells[columnIndex]) {
                        cells[columnIndex].style.display = column.visible ? '' : 'none';
                    }
                });
            }
        });
    }

    // Get column index by key
    function getColumnIndex(columnKey) {
        const columnMap = {
            'date': 0,
            'title': 1,
            'description': 2,
            'category': 3,
            'payment': 4,
            'amount': 5,
            'location': 6,
            'vendor': 7,
            'notes': 8,
            'tags': 9,
            'reimbursable': 10,
            'reimbursement_status': 11,
            'reimbursement_notes': 12,
            'receipt': 13,
            'created_at': 14,
            'updated_at': 15,
            'actions': 16
        };
        return columnMap[columnKey] !== undefined ? columnMap[columnKey] : -1;
    }

    // Create and show the column customization modal
    function showColumnModal() {
        const columns = loadColumnPreferences();
        
        // Remove existing modal if present
        const existingModal = document.getElementById('columnCustomizationModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="columnCustomizationModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title"><i class="fas fa-columns"></i> Customize Table Columns</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted">Select which columns to display in the expense table:</p>
                            <div class="column-list">
                                ${Object.keys(columns).map(key => {
                                    const column = columns[key];
                                    const disabled = column.fixed ? 'disabled' : '';
                                    const checked = column.visible ? 'checked' : '';
                                    return `
                                        <div class="form-check mb-2">
                                            <input class="form-check-input column-toggle" 
                                                   type="checkbox" 
                                                   id="column-${key}" 
                                                   data-column="${key}"
                                                   ${checked} ${disabled}>
                                            <label class="form-check-label" for="column-${key}">
                                                ${column.label}
                                                ${column.fixed ? '<small class="text-muted">(Required)</small>' : ''}
                                            </label>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveColumnPreferences">
                                <i class="fas fa-save"></i> Save Preferences
                            </button>
                            <button type="button" class="btn btn-outline-secondary" id="resetColumnDefaults">
                                <i class="fas fa-undo"></i> Reset to Defaults
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Initialize modal
        const modal = new bootstrap.Modal(document.getElementById('columnCustomizationModal'));
        
        // Setup event handlers
        document.getElementById('saveColumnPreferences').addEventListener('click', function() {
            const updatedColumns = { ...columns };
            
            // Update visibility based on checkboxes
            document.querySelectorAll('.column-toggle').forEach(checkbox => {
                const columnKey = checkbox.dataset.column;
                if (updatedColumns[columnKey]) {
                    updatedColumns[columnKey].visible = checkbox.checked;
                }
            });
            
            // Save and apply
            saveColumnPreferences(updatedColumns);
            applyColumnVisibility();
            modal.hide();
            
            // Show success message
            showToast('Column preferences saved successfully!', 'success');
        });
        
        document.getElementById('resetColumnDefaults').addEventListener('click', function() {
            if (confirm('Reset all columns to default visibility?')) {
                saveColumnPreferences(defaultColumns);
                applyColumnVisibility();
                modal.hide();
                showToast('Columns reset to defaults', 'info');
            }
        });
        
        // Show modal
        modal.show();
    }

    // Show a toast notification
    function showToast(message, type = 'info') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'info'} border-0" 
                 role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999;">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.body.lastElementChild;
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        // Remove after hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Apply saved column preferences
        applyColumnVisibility();
        
        // Add settings button if on expenses page
        const expenseTable = document.getElementById('expenseTable');
        if (expenseTable) {
            // Look for the button group with export buttons
            const buttonGroup = document.querySelector('.d-flex.justify-content-between.align-items-center.mb-4 > div:last-child');
            if (buttonGroup) {
                // Add column settings button
                const settingsButton = document.createElement('button');
                settingsButton.className = 'btn btn-outline-secondary ms-2';
                settingsButton.innerHTML = '<i class="fas fa-columns"></i> Columns';
                settingsButton.onclick = showColumnModal;
                buttonGroup.appendChild(settingsButton);
            }
        }
    });

    // Export functions for global access if needed
    window.ExpenseColumns = {
        show: showColumnModal,
        apply: applyColumnVisibility,
        reset: function() {
            saveColumnPreferences(defaultColumns);
            applyColumnVisibility();
        }
    };
})();