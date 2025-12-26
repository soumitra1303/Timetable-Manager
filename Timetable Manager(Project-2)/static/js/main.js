// Load categories on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    setupEventListeners();
});

// Load categories for filter
function loadCategories() {
    fetch('/api/categories')
        .then(response => response.json())
        .then(categories => {
            const select = document.getElementById('categoryFilter');
            if (select) {
                categories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat;
                    option.textContent = cat;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error loading categories:', error));
}

// Setup event listeners
function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterTable, 300));
    }
    
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterTable);
    }
    
    // Quantity update
    const qtyInputs = document.querySelectorAll('.qty-input');
    qtyInputs.forEach(input => {
        input.addEventListener('change', function() {
            updateQuantity(this.dataset.id, this.value);
        });
    });
    
    // Modal close
    const modal = document.getElementById('lowStockModal');
    const closeBtn = document.querySelector('.close');
    
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        };
    }
    
    if (modal) {
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
    }
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Filter table
function filterTable() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const categoryValue = document.getElementById('categoryFilter').value;
    const table = document.getElementById('inventoryTable');
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const name = row.cells[1].textContent.toLowerCase();
        const category = row.cells[2].textContent;
        
        const matchesSearch = name.includes(searchValue);
        const matchesCategory = !categoryValue || category === categoryValue;
        
        if (matchesSearch && matchesCategory) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
}

// Update quantity
function updateQuantity(id, quantity) {
    fetch(`/update-quantity/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ quantity: parseInt(quantity) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Quantity updated successfully!', 'success');
            // Reload page to update calculations
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification('Error updating quantity: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showNotification('Error updating quantity', 'error');
        console.error('Error:', error);
    });
}

// Delete item
function deleteItem(id) {
    if (confirm('Are you sure you want to delete this item?')) {
        fetch(`/delete/${id}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Item deleted successfully!', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification('Error deleting item: ' + data.error, 'error');
            }
        })
        .catch(error => {
            showNotification('Error deleting item', 'error');
            console.error('Error:', error);
        });
    }
}

// Show low stock items
function showLowStock() {
    fetch('/low-stock')
        .then(response => response.json())
        .then(items => {
            const modal = document.getElementById('lowStockModal');
            const list = document.getElementById('lowStockList');
            
            if (items.length === 0) {
                list.innerHTML = '<p class="success-message">✅ All items are adequately stocked!</p>';
            } else {
                let html = '<div class="table-container"><table class="report-table"><thead><tr>';
                html += '<th>Item</th><th>Category</th><th>Current</th><th>Min Level</th><th>Action</th>';
                html += '</tr></thead><tbody>';
                
                items.forEach(item => {
                    const needed = (item.min_stock_level * 2) - item.quantity;
                    html += `<tr class="low-stock">
                        <td><strong>${item.name}</strong></td>
                        <td>${item.category}</td>
                        <td class="danger">${item.quantity}</td>
                        <td>${item.min_stock_level}</td>
                        <td><span class="status-badge low">Reorder ${needed} units</span></td>
                    </tr>`;
                });
                
                html += '</tbody></table></div>';
                list.innerHTML = html;
            }
            
            modal.style.display = 'block';
        })
        .catch(error => {
            showNotification('Error loading low stock items', 'error');
            console.error('Error:', error);
        });
}

// Show notification
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#4caf50' : '#f44336'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);