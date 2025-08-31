// Expense Preview Modal Functionality
(function() {
    
    // Show expense preview modal
    window.showExpensePreview = function(expenseId, expenseTitle) {
        // Fetch expense details from the server
        fetch(`/api/expense/${expenseId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch expense details');
                }
                return response.json();
            })
            .then(expense => {
                displayExpenseModal(expense);
            })
            .catch(error => {
                console.error('Error fetching expense details:', error);
                showToast('Error loading expense details', 'error');
            });
    };

    // Display the expense modal with data
    function displayExpenseModal(expense) {
        // Remove existing modal if present
        const existingModal = document.getElementById('expensePreviewModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Format date helper
        const formatDate = (dateString) => {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleDateString();
        };

        // Format currency helper
        const formatCurrency = (amount) => {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount || 0);
        };

        // Get reimbursable status badge
        const getReimbursableBadge = (expense) => {
            if (expense.is_reimbursable === 'yes') {
                if (expense.reimbursement_status === 'pending') {
                    return '<span class="badge bg-warning">Pending</span>';
                } else if (expense.reimbursement_status === 'approved') {
                    return '<span class="badge bg-info">Approved</span>';
                } else if (expense.reimbursement_status === 'received') {
                    return '<span class="badge bg-success">Received</span>';
                } else {
                    return '<span class="badge bg-success">Yes</span>';
                }
            } else if (expense.is_reimbursable === 'maybe') {
                return '<span class="badge bg-warning">Maybe</span>';
            } else {
                return '<span class="badge bg-secondary">No</span>';
            }
        };

        // Get tags HTML
        const getTagsHtml = (tags) => {
            if (!tags) return '<span class="text-muted">No tags</span>';
            
            const tagList = tags.split(',');
            return tagList.map(tag => 
                `<span class="badge bg-light text-dark me-1">${tag.trim()}</span>`
            ).join('');
        };

        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="expensePreviewModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-receipt"></i> ${expense.title || 'Untitled Expense'}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <!-- Left Column -->
                                <div class="col-md-6">
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Date</label>
                                        <div>${formatDate(expense.date)}</div>
                                    </div>
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Amount</label>
                                        <div class="h5 text-primary">${formatCurrency(expense.cost)}</div>
                                    </div>
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Category</label>
                                        <div>
                                            ${expense.category 
                                                ? `<span class="badge" style="background-color: ${expense.category.color};">
                                                     <i class="fas ${expense.category.icon}"></i> ${expense.category.name}
                                                   </span>`
                                                : '<span class="badge bg-secondary">Uncategorized</span>'
                                            }
                                        </div>
                                    </div>
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Payment Method</label>
                                        <div>
                                            ${expense.payment_method 
                                                ? `<span class="badge bg-info">
                                                     <i class="fas ${expense.payment_method.icon}"></i> ${expense.payment_method.name}
                                                   </span>`
                                                : '<span class="badge bg-secondary">Unknown</span>'
                                            }
                                        </div>
                                    </div>
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Location</label>
                                        <div>${expense.location || '<span class="text-muted">Not specified</span>'}</div>
                                    </div>
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Vendor</label>
                                        <div>${expense.vendor || '<span class="text-muted">Not specified</span>'}</div>
                                    </div>
                                </div>
                                
                                <!-- Right Column -->
                                <div class="col-md-6">
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Reimbursable</label>
                                        <div>${getReimbursableBadge(expense)}</div>
                                    </div>
                                    
                                    ${expense.reimbursement_status && expense.reimbursement_status !== 'none' ? `
                                        <div class="expense-detail-group mb-3">
                                            <label class="fw-bold text-muted">Reimbursement Status</label>
                                            <div>
                                                ${expense.reimbursement_status === 'pending' ? '<span class="badge bg-warning">Pending</span>' :
                                                  expense.reimbursement_status === 'approved' ? '<span class="badge bg-info">Approved</span>' :
                                                  expense.reimbursement_status === 'received' ? '<span class="badge bg-success">Received</span>' :
                                                  `<span class="text-muted">${expense.reimbursement_status}</span>`
                                                }
                                            </div>
                                        </div>
                                    ` : ''}
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Tags</label>
                                        <div>${getTagsHtml(expense.tags)}</div>
                                    </div>
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Receipt</label>
                                        <div>
                                            ${expense.receipt_image 
                                                ? `<a href="/expense/${expense.id}/receipt" target="_blank" class="btn btn-sm btn-outline-info">
                                                     <i class="fas fa-image"></i> View Receipt
                                                   </a>`
                                                : '<span class="text-muted">No receipt uploaded</span>'
                                            }
                                        </div>
                                    </div>
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Created</label>
                                        <div><small class="text-muted">${formatDate(expense.created_at)}</small></div>
                                    </div>
                                    
                                    <div class="expense-detail-group mb-3">
                                        <label class="fw-bold text-muted">Last Updated</label>
                                        <div><small class="text-muted">${formatDate(expense.updated_at)}</small></div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Full-width sections -->
                            ${expense.description ? `
                                <div class="expense-detail-group mb-3">
                                    <label class="fw-bold text-muted">Description</label>
                                    <div class="border p-2 rounded bg-light">
                                        <small>${expense.description}</small>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${expense.notes ? `
                                <div class="expense-detail-group mb-3">
                                    <label class="fw-bold text-muted">Notes</label>
                                    <div class="border p-2 rounded bg-light">
                                        <small>${expense.notes}</small>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${expense.reimbursement_notes ? `
                                <div class="expense-detail-group mb-3">
                                    <label class="fw-bold text-muted">Reimbursement Notes</label>
                                    <div class="border p-2 rounded bg-light">
                                        <small>${expense.reimbursement_notes}</small>
                                    </div>
                                </div>
                            ` : ''}

                            ${expense.receipt_image ? `
                                <div class="expense-detail-group mb-3">
                                    <label class="fw-bold text-muted">Receipt Preview</label>
                                    <div class="text-center">
                                        <img src="/expense/${expense.id}/receipt" 
                                             class="img-thumbnail" 
                                             style="max-height: 200px; cursor: pointer;" 
                                             onclick="window.open('/expense/${expense.id}/receipt', '_blank')"
                                             alt="Receipt thumbnail">
                                        <br><small class="text-muted">Click to view full size</small>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <a href="/expense/${expense.id}/edit" class="btn btn-primary">
                                <i class="fas fa-edit"></i> Edit Expense
                            </a>
                            <form method="POST" action="/expense/${expense.id}/delete" style="display: inline;" 
                                  onsubmit="return confirm('Are you sure you want to delete this expense?');">
                                <button type="submit" class="btn btn-outline-danger">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </form>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Initialize and show modal
        const modal = new bootstrap.Modal(document.getElementById('expensePreviewModal'));
        modal.show();
        
        // Remove modal from DOM when hidden
        document.getElementById('expensePreviewModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    // Show toast notification
    function showToast(message, type = 'info') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0" 
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
        const toast = new bootstrap.Toast(toastElement, { delay: 4000 });
        toast.show();
        
        // Remove after hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Add CSS for expense detail groups
    document.addEventListener('DOMContentLoaded', function() {
        // Add custom styles
        const style = document.createElement('style');
        style.textContent = `
            .expense-detail-group label {
                font-size: 0.85rem;
                margin-bottom: 0.25rem;
                display: block;
            }
            .expense-title-link:hover {
                text-decoration: underline !important;
            }
            .expense-detail-group div {
                margin-bottom: 0.5rem;
            }
            .modal-lg .expense-detail-group {
                padding-bottom: 0.5rem;
                border-bottom: 1px solid #f0f0f0;
            }
            .modal-lg .expense-detail-group:last-child {
                border-bottom: none;
            }
        `;
        document.head.appendChild(style);
    });

})();