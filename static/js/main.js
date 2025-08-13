/**
 * XPOM-KZ Main JavaScript
 * Custom functionality for the logistics management system
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeApplication();
});

/**
 * Initialize the application
 */
function initializeApplication() {
    initializeTooltips();
    initializeFormValidation();
    initializePhoneFormatting();
    initializeAlerts();
    initializeTableEnhancements();
    initializeChartRefresh();
    initializeSearchFunctionality();
    initializeNotifications();
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Scroll to first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Real-time validation
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

/**
 * Validate individual field
 */
function validateField(field) {
    const isValid = field.checkValidity();
    
    field.classList.remove('is-valid', 'is-invalid');
    
    if (field.value.trim() !== '') {
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    }
    
    // Custom validation messages
    if (!isValid) {
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            if (field.validity.valueMissing) {
                feedback.textContent = 'Это поле обязательно для заполнения.';
            } else if (field.validity.typeMismatch) {
                if (field.type === 'email') {
                    feedback.textContent = 'Введите корректный email адрес.';
                } else if (field.type === 'tel') {
                    feedback.textContent = 'Введите корректный номер телефона.';
                }
            } else if (field.validity.patternMismatch) {
                feedback.textContent = 'Введенное значение не соответствует требуемому формату.';
            }
        }
    }
}

/**
 * Initialize phone number formatting
 */
function initializePhoneFormatting() {
    const phoneInputs = document.querySelectorAll('input[type="tel"], input[name*="phone"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            formatPhoneNumber(e.target);
        });
        
        input.addEventListener('keypress', function(e) {
            // Allow only numbers, plus, parentheses, hyphens, and spaces
            const allowedChars = /[0-9+\-\s()]/;
            if (!allowedChars.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Format phone number to Kazakhstan format
 */
function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, '');
    
    // Handle Kazakhstan numbers
    if (value.startsWith('7') || value.startsWith('8')) {
        if (value.startsWith('8')) {
            value = '7' + value.substring(1);
        }
        
        if (value.length <= 11) {
            if (value.length > 1) {
                if (value.length <= 4) {
                    value = `+7 (${value.slice(1)}`;
                } else if (value.length <= 7) {
                    value = `+7 (${value.slice(1, 4)}) ${value.slice(4)}`;
                } else if (value.length <= 9) {
                    value = `+7 (${value.slice(1, 4)}) ${value.slice(4, 7)}-${value.slice(7)}`;
                } else {
                    value = `+7 (${value.slice(1, 4)}) ${value.slice(4, 7)}-${value.slice(7, 9)}-${value.slice(9, 11)}`;
                }
            }
        }
    } else if (value.length > 0) {
        // For non-Kazakhstan numbers, just add +7 prefix
        value = '+7 ' + value;
    }
    
    input.value = value;
}

/**
 * Initialize alert auto-dismiss
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
}

/**
 * Initialize table enhancements
 */
function initializeTableEnhancements() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        // Add hover effects
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fa';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
        
        // Make rows clickable if they have a main link
        rows.forEach(row => {
            const mainLink = row.querySelector('a[href*="/admin/order/"]');
            if (mainLink) {
                row.style.cursor = 'pointer';
                row.addEventListener('click', function(e) {
                    // Don't trigger if clicking on an actual link or button
                    if (!e.target.closest('a, button')) {
                        window.location.href = mainLink.href;
                    }
                });
            }
        });
    });
}

/**
 * Initialize chart refresh functionality
 */
function initializeChartRefresh() {
    const chartRefreshButtons = document.querySelectorAll('[data-chart-refresh]');
    
    chartRefreshButtons.forEach(button => {
        button.addEventListener('click', function() {
            const chartId = this.getAttribute('data-chart-refresh');
            refreshChart(chartId);
        });
    });
}

/**
 * Refresh chart data
 */
function refreshChart(chartId) {
    const chartElement = document.getElementById(chartId);
    if (!chartElement) return;
    
    // Add loading state
    const container = chartElement.closest('.card-body');
    if (container) {
        container.classList.add('loading');
    }
    
    // Simulate data refresh (in real implementation, this would fetch from API)
    setTimeout(() => {
        if (container) {
            container.classList.remove('loading');
        }
        
        showNotification('Данные обновлены', 'success');
    }, 1000);
}

/**
 * Initialize search functionality
 */
function initializeSearchFunctionality() {
    const searchInputs = document.querySelectorAll('[data-search-table]');
    
    searchInputs.forEach(input => {
        const tableId = input.getAttribute('data-search-table');
        const table = document.getElementById(tableId);
        
        if (table) {
            input.addEventListener('input', function() {
                filterTable(table, this.value);
            });
        }
    });
}

/**
 * Filter table rows based on search term
 */
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const match = text.includes(term);
        row.style.display = match ? '' : 'none';
    });
    
    // Show "no results" message if needed
    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
    
    let noResultsRow = table.querySelector('.no-results-row');
    if (visibleRows.length === 0 && searchTerm.trim() !== '') {
        if (!noResultsRow) {
            noResultsRow = document.createElement('tr');
            noResultsRow.className = 'no-results-row';
            noResultsRow.innerHTML = `
                <td colspan="100%" class="text-center py-4">
                    <i class="fas fa-search fa-2x text-muted mb-2"></i>
                    <p class="text-muted mb-0">По запросу "${searchTerm}" ничего не найдено</p>
                </td>
            `;
            table.querySelector('tbody').appendChild(noResultsRow);
        }
    } else if (noResultsRow) {
        noResultsRow.remove();
    }
}

/**
 * Initialize notifications
 */
function initializeNotifications() {
    // Check for new orders periodically (for admin users)
    if (window.location.pathname.includes('/admin/')) {
        setInterval(checkForUpdates, 30000); // Check every 30 seconds
    }
}

/**
 * Check for updates (new orders, status changes, etc.)
 */
function checkForUpdates() {
    // In a real implementation, this would make an API call
    // For now, we'll simulate with random chance
    if (Math.random() < 0.1) { // 10% chance
        showNotification('Новая заявка получена!', 'info', {
            persistent: true,
            action: {
                text: 'Просмотреть',
                callback: () => window.location.href = '/admin/orders?status=new'
            }
        });
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', options = {}) {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const icon = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-triangle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    }[type] || 'fa-info-circle';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show ${options.persistent ? 'alert-permanent' : ''}" role="alert">
            <i class="fas ${icon}"></i>
            ${message}
            ${options.action ? `<button type="button" class="btn btn-sm btn-outline-dark ms-3">${options.action.text}</button>` : ''}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Find or create notification container
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    // Add notification
    const alertElement = document.createElement('div');
    alertElement.innerHTML = alertHtml;
    const alert = alertElement.firstElementChild;
    
    container.appendChild(alert);
    
    // Add action handler
    if (options.action) {
        const actionBtn = alert.querySelector('button:not(.btn-close)');
        if (actionBtn) {
            actionBtn.addEventListener('click', options.action.callback);
        }
    }
    
    // Auto-remove if not persistent
    if (!options.persistent) {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    }
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Скопировано в буфер обмена', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

/**
 * Fallback copy to clipboard
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Скопировано в буфер обмена', 'success');
    } catch (err) {
        showNotification('Не удалось скопировать', 'error');
    }
    
    document.body.removeChild(textArea);
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = '₸') {
    const number = parseFloat(amount);
    if (isNaN(number)) return amount;
    
    return new Intl.NumberFormat('ru-KZ', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(number) + ' ' + currency;
}

/**
 * Format date
 */
function formatDate(date, format = 'short') {
    if (!date) return '';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return date;
    
    const options = {
        'short': { day: '2-digit', month: '2-digit', year: 'numeric' },
        'long': { day: '2-digit', month: 'long', year: 'numeric' },
        'datetime': { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }
    }[format] || { day: '2-digit', month: '2-digit', year: 'numeric' };
    
    return new Intl.DateTimeFormat('ru-KZ', options).format(d);
}

/**
 * Debounce function
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

/**
 * Smooth scroll to element
 */
function scrollToElement(element, offset = 0) {
    const targetElement = typeof element === 'string' ? document.querySelector(element) : element;
    
    if (targetElement) {
        const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - offset;
        
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
}

/**
 * Generate tracking number preview
 */
function generateTrackingPreview(type = 'astana') {
    const year = new Date().getFullYear();
    const prefix = type === 'astana' ? 'AST' : 'KZ';
    const random = Math.floor(Math.random() * 999) + 1;
    const number = random.toString().padStart(3, '0');
    
    return `${prefix}-${year}-${number}`;
}

/**
 * Validate tracking number format
 */
function validateTrackingNumber(trackingNumber) {
    const pattern = /^(AST|KZ)-\d{4}-\d{3}$/;
    return pattern.test(trackingNumber.toUpperCase());
}

/**
 * Export utilities for global use
 */
window.XPOMUtils = {
    showNotification,
    copyToClipboard,
    formatCurrency,
    formatDate,
    debounce,
    scrollToElement,
    generateTrackingPreview,
    validateTrackingNumber
};

/**
 * Handle global errors
 */
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showNotification('Произошла ошибка. Пожалуйста, обновите страницу.', 'error');
});

/**
 * Handle network errors
 */
window.addEventListener('offline', function() {
    showNotification('Соединение с интернетом потеряно', 'warning', { persistent: true });
});

window.addEventListener('online', function() {
    showNotification('Соединение восстановлено', 'success');
    // Remove persistent offline notifications
    document.querySelectorAll('.alert-permanent').forEach(alert => {
        const bsAlert = new bootstrap.Alert(alert);
        if (bsAlert) {
            bsAlert.close();
        }
    });
});

/**
 * Performance monitoring
 */
if (window.performance && window.performance.timing) {
    window.addEventListener('load', function() {
        const loadTime = window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;
        console.log(`Page load time: ${loadTime}ms`);
        
        // Send to analytics if configured
        if (typeof gtag !== 'undefined') {
            gtag('event', 'timing_complete', {
                name: 'load',
                value: loadTime
            });
        }
    });
}
