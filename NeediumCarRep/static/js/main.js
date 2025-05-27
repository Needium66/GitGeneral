// Main JavaScript for AutoSales Pro
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.classList.contains('show')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const cardObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                cardObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    cards.forEach(function(card) {
        cardObserver.observe(card);
    });
    
    // Form validation enhancements
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Enhanced search functionality for inventory
    const searchForm = document.querySelector('#inventory-search-form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search_term"]');
        const makeSelect = searchForm.querySelector('select[name="make"]');
        
        // Auto-submit on make selection change
        if (makeSelect) {
            makeSelect.addEventListener('change', function() {
                if (this.value) {
                    searchForm.submit();
                }
            });
        }
        
        // Add search suggestions (if you want to implement this later)
        if (searchInput) {
            searchInput.addEventListener('input', debounce(function() {
                // Implement search suggestions here if needed
                console.log('Search term:', this.value);
            }, 300));
        }
    }
    
    // Price formatting for form inputs
    const priceInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    priceInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value) {
                const value = parseFloat(this.value);
                if (!isNaN(value)) {
                    this.value = value.toFixed(2);
                }
            }
        });
    });
    
    // Dashboard chart initialization (placeholder for future charts)
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(function(container) {
        // Initialize charts here if needed
        console.log('Chart container found:', container.id);
    });
    
    // Table sorting functionality (basic implementation)
    const sortableHeaders = document.querySelectorAll('th[data-sortable]');
    sortableHeaders.forEach(function(header) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(this);
        });
        
        // Add sort indicator
        const icon = document.createElement('i');
        icon.className = 'fas fa-sort ms-1';
        header.appendChild(icon);
    });
    
    // Mobile navigation enhancements
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        let lastScrollTop = 0;
        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // Scrolling down
                navbar.style.transform = 'translateY(-100%)';
            } else {
                // Scrolling up
                navbar.style.transform = 'translateY(0)';
            }
            lastScrollTop = scrollTop;
        });
    }
    
    // Loading state for forms
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            if (form && form.checkValidity()) {
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = this.dataset.originalText || 'Submit';
                }, 10000);
            }
        });
        
        // Store original text
        button.dataset.originalText = button.innerHTML;
    });
    
    // Statistics counters animation
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length > 0) {
        const statsObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    animateNumber(entry.target);
                    statsObserver.unobserve(entry.target);
                }
            });
        });
        
        statNumbers.forEach(function(stat) {
            statsObserver.observe(stat);
        });
    }
    
    // Initialize any data tables
    initializeDataTables();
    
    // Set up real-time notifications (placeholder)
    // setupNotifications();
    
    console.log('AutoSales Pro - JavaScript initialized successfully');
});

// Utility Functions

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Table sorting function
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = header.classList.contains('sort-asc');
    
    // Clear all sort classes
    header.parentNode.querySelectorAll('th').forEach(function(th) {
        th.classList.remove('sort-asc', 'sort-desc');
        const icon = th.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-sort ms-1';
        }
    });
    
    // Sort rows
    rows.sort(function(a, b) {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? bNum - aNum : aNum - bNum;
        } else {
            return isAscending ? 
                bValue.localeCompare(aValue) : 
                aValue.localeCompare(bValue);
        }
    });
    
    // Update header class and icon
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    const icon = header.querySelector('i');
    if (icon) {
        icon.className = isAscending ? 
            'fas fa-sort-down ms-1' : 
            'fas fa-sort-up ms-1';
    }
    
    // Rebuild table body
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
}

// Animate numbers counting up
function animateNumber(element) {
    const target = parseInt(element.textContent);
    const duration = 2000; // 2 seconds
    const step = target / (duration / 16); // 60 FPS
    let current = 0;
    
    const timer = setInterval(function() {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

// Initialize data tables with enhanced features
function initializeDataTables() {
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(function(table) {
        // Add search functionality
        addTableSearch(table);
        
        // Add pagination if needed
        if (table.querySelectorAll('tbody tr').length > 10) {
            addTablePagination(table);
        }
    });
}

// Add search functionality to tables
function addTableSearch(table) {
    const tableContainer = table.parentNode;
    const searchContainer = document.createElement('div');
    searchContainer.className = 'table-search mb-3';
    searchContainer.innerHTML = `
        <div class="input-group">
            <span class="input-group-text">
                <i class="fas fa-search"></i>
            </span>
            <input type="text" class="form-control" placeholder="Search table...">
        </div>
    `;
    
    tableContainer.insertBefore(searchContainer, table);
    
    const searchInput = searchContainer.querySelector('input');
    searchInput.addEventListener('input', debounce(function() {
        filterTable(table, this.value);
    }, 300));
}

// Filter table rows based on search term
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(function(row) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

// Add pagination to large tables
function addTablePagination(table) {
    // Implementation for table pagination
    // This is a placeholder for future enhancement
    console.log('Pagination needed for table:', table);
}

// Format currency values
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format dates
function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(date));
}

// Show success message
function showSuccessMessage(message) {
    showAlert(message, 'success');
}

// Show error message
function showErrorMessage(message) {
    showAlert(message, 'danger');
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container') || 
                          document.querySelector('.container');
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alert, alertContainer.firstChild);
    
    // Auto dismiss after 5 seconds
    setTimeout(function() {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// Setup real-time notifications (placeholder)
function setupNotifications() {
    // This would implement WebSocket or Server-Sent Events
    // for real-time notifications about new purchases, etc.
    console.log('Real-time notifications setup placeholder');
}

// Export functions for use in other scripts
window.AutoSales = {
    /**
 * AutoSales Pro - Main JavaScript Module
 * Provides interactive functionality and UI enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Initialize all components
    initializeTooltips();
    initializeDataTables();
    initializeFormValidation();
    initializeSearchFunctionality();
    initializeAnimations();
    initializeDashboardFeatures();
    initializeCarInventoryFeatures();
    initializePurchaseFormFeatures();
    initializeUserFeedback();

    console.log('AutoSales Pro initialized successfully');
});

/**
 * Initialize Bootstrap tooltips for better UX
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Enhanced table functionality with sorting and search
 */
function initializeDataTables() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        // Add sorting capability to table headers
        const headers = table.querySelectorAll('th[data-sortable="true"]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, this);
            });
            
            // Add sort indicator
            if (!header.querySelector('.sort-indicator')) {
                header.innerHTML += ' <i class="fas fa-sort sort-indicator text-muted"></i>';
            }
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(table, header) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = header.classList.contains('sort-asc');
    
    // Clear all sort classes
    header.parentNode.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        const indicator = th.querySelector('.sort-indicator');
        if (indicator) {
            indicator.className = 'fas fa-sort sort-indicator text-muted';
        }
    });
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Try to parse as numbers first
        const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? bNum - aNum : aNum - bNum;
        }
        
        // String comparison
        return isAscending ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
    });
    
    // Update table
    rows.forEach(row => tbody.appendChild(row));
    
    // Update header class and icon
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    const indicator = header.querySelector('.sort-indicator');
    if (indicator) {
        indicator.className = `fas fa-sort-${isAscending ? 'down' : 'up'} sort-indicator text-primary`;
    }
}

/**
 * Enhanced form validation with real-time feedback
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate="true"], .needs-validation');
    
    forms.forEach(form => {
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
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
        
        // Form submission validation
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity() || !validateCustomRules(form)) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus first invalid field
                const firstInvalid = form.querySelector('.is-invalid, :invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
    });
}

/**
 * Validate individual field
 */
function validateField(field) {
    const isValid = field.checkValidity() && validateCustomFieldRules(field);
    
    field.classList.toggle('is-valid', isValid && field.value.trim() !== '');
    field.classList.toggle('is-invalid', !isValid);
    
    return isValid;
}

/**
 * Custom validation rules
 */
function validateCustomRules(form) {
    let isValid = true;
    
    // VIN validation
    const vinField = form.querySelector('input[name="vin"]');
    if (vinField && vinField.value) {
        const vinPattern = /^[A-HJ-NPR-Z0-9]{17}$/;
        if (!vinPattern.test(vinField.value.toUpperCase())) {
            showFieldError(vinField, 'VIN must be exactly 17 characters (letters and numbers, no I, O, or Q)');
            isValid = false;
        }
    }
    
    // Price validation
    const priceField = form.querySelector('input[name="price"]');
    if (priceField && priceField.value) {
        const price = parseFloat(priceField.value);
        if (price <= 0) {
            showFieldError(priceField, 'Price must be greater than 0');
            isValid = false;
        }
    }
    
    // Down payment validation
    const downPaymentField = form.querySelector('input[name="down_payment"]');
    const vehiclePriceField = form.querySelector('input[readonly][value]');
    if (downPaymentField && vehiclePriceField) {
        const downPayment = parseFloat(downPaymentField.value) || 0;
        const vehiclePrice = parseFloat(vehiclePriceField.value) || 0;
        
        if (downPayment > vehiclePrice) {
            showFieldError(downPaymentField, 'Down payment cannot exceed vehicle price');
            isValid = false;
        }
    }
    
    return isValid;
}

/**
 * Custom field validation rules
 */
function validateCustomFieldRules(field) {
    // Email validation enhancement
    if (field.type === 'email' && field.value) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailPattern.test(field.value);
    }
    
    // Phone validation
    if (field.name === 'phone' && field.value) {
        const phonePattern = /^\+?[\d\s\-\(\)]{10,}$/;
        return phonePattern.test(field.value);
    }
    
    return true;
}

/**
 * Show field error message
 */
function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    let feedback = field.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
}

/**
 * Enhanced search functionality
 */
function initializeSearchFunctionality() {
    const searchForms = document.querySelectorAll('.search-form, form[data-search="true"]');
    
    searchForms.forEach(form => {
        const searchInput = form.querySelector('input[name="search_term"]');
        if (searchInput) {
            // Add search icon
            if (!searchInput.parentNode.querySelector('.search-icon')) {
                const icon = document.createElement('i');
                icon.className = 'fas fa-search search-icon position-absolute';
                icon.style.cssText = 'right: 10px; top: 50%; transform: translateY(-50%); color: #6c757d; pointer-events: none;';
                searchInput.parentNode.style.position = 'relative';
                searchInput.style.paddingRight = '35px';
                searchInput.parentNode.appendChild(icon);
            }
            
            // Auto-submit on Enter
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    form.submit();
                }
            });
        }
        
        // Clear filters functionality
        const clearButton = form.querySelector('.btn[data-action="clear"]');
        if (clearButton) {
            clearButton.addEventListener('click', function(e) {
                e.preventDefault();
                form.reset();
                // Remove URL parameters and reload
                window.location.href = window.location.pathname;
            });
        }
    });
}

/**
 * Initialize smooth animations and transitions
 */
function initializeAnimations() {
    // Fade in cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe cards and other elements
    document.querySelectorAll('.card, .feature-card, .stats-card').forEach(el => {
        observer.observe(el);
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Dashboard-specific features
 */
function initializeDashboardFeatures() {
    // Animate counting numbers
    animateCounters();
    
    // Auto-refresh dashboard data
    if (window.location.pathname.includes('/dashboard') || window.location.pathname.includes('/admin')) {
        startDataRefresh();
    }
    
    // Quick action shortcuts
    initializeKeyboardShortcuts();
}

/**
 * Animate counter numbers in dashboard
 */
function animateCounters() {
    const counters = document.querySelectorAll('[data-counter]');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-counter')) || parseInt(counter.textContent);
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.textContent = Math.floor(current).toLocaleString();
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target.toLocaleString();
            }
        };
        
        // Start animation when element is visible
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
}

/**
 * Auto-refresh dashboard data every 5 minutes
 */
function startDataRefresh() {
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            // Only refresh if page is visible
            const refreshElements = document.querySelectorAll('[data-auto-refresh="true"]');
            if (refreshElements.length > 0) {
                location.reload();
            }
        }
    }, 5 * 60 * 1000); // 5 minutes
}

/**
 * Keyboard shortcuts for power users
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="search_term"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                bootstrap.Modal.getInstance(openModal).hide();
            }
        }
    });
}

/**
 * Car inventory specific features
 */
function initializeCarInventoryFeatures() {
    // Image lazy loading
    initializeLazyLoading();
    
    // Price range slider
    initializePriceRangeSlider();
    
    // Comparison feature
    initializeCarComparison();
    
    // Favorites system
    initializeFavorites();
}

/**
 * Lazy loading for images
 */
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
}

/**
 * Price range slider functionality
 */
function initializePriceRangeSlider() {
    const minPriceInput = document.querySelector('input[name="min_price"]');
    const maxPriceInput = document.querySelector('input[name="max_price"]');
    
    if (minPriceInput && maxPriceInput) {
        [minPriceInput, maxPriceInput].forEach(input => {
            input.addEventListener('input', function() {
                const min = parseFloat(minPriceInput.value) || 0;
                const max = parseFloat(maxPriceInput.value) || Infinity;
                
                if (min > max && max > 0) {
                    this.setCustomValidity('Minimum price cannot be greater than maximum price');
                } else {
                    this.setCustomValidity('');
                }
            });
        });
    }
}

/**
 * Car comparison feature
 */
function initializeCarComparison() {
    let comparisonList = JSON.parse(localStorage.getItem('carComparison') || '[]');
    
    // Add compare buttons to car cards
    document.querySelectorAll('.car-card').forEach(card => {
        const carId = card.dataset.carId;
        if (carId) {
            const compareBtn = document.createElement('button');
            compareBtn.className = 'btn btn-outline-secondary btn-sm compare-btn';
            compareBtn.innerHTML = '<i class="fas fa-balance-scale me-1"></i>Compare';
            compareBtn.addEventListener('click', () => toggleComparison(carId, compareBtn));
            
            const cardFooter = card.querySelector('.card-footer');
            if (cardFooter) {
                cardFooter.appendChild(compareBtn);
            }
            
            // Update button state
            if (comparisonList.includes(carId)) {
                compareBtn.classList.add('active');
                compareBtn.innerHTML = '<i class="fas fa-check me-1"></i>Added';
            }
        }
    });
    
    // Update comparison counter
    updateComparisonCounter();
}

/**
 * Toggle car in comparison list
 */
function toggleComparison(carId, button) {
    let comparisonList = JSON.parse(localStorage.getItem('carComparison') || '[]');
    
    if (comparisonList.includes(carId)) {
        comparisonList = comparisonList.filter(id => id !== carId);
        button.classList.remove('active');
        button.innerHTML = '<i class="fas fa-balance-scale me-1"></i>Compare';
    } else {
        if (comparisonList.length >= 3) {
            showToast('You can only compare up to 3 cars at once', 'warning');
            return;
        }
        comparisonList.push(carId);
        button.classList.add('active');
        button.innerHTML = '<i class="fas fa-check me-1"></i>Added';
    }
    
    localStorage.setItem('carComparison', JSON.stringify(comparisonList));
    updateComparisonCounter();
}

/**
 * Update comparison counter in navigation
 */
function updateComparisonCounter() {
    const comparisonList = JSON.parse(localStorage.getItem('carComparison') || '[]');
    let counter = document.querySelector('.comparison-counter');
    
    if (comparisonList.length > 0) {
        if (!counter) {
            counter = document.createElement('span');
            counter.className = 'badge bg-primary comparison-counter ms-1';
            const navLink = document.querySelector('a[href*="compare"]');
            if (navLink) {
                navLink.appendChild(counter);
            }
        }
        counter.textContent = comparisonList.length;
    } else if (counter) {
        counter.remove();
    }
}

/**
 * Favorites system
 */
function initializeFavorites() {
    let favorites = JSON.parse(localStorage.getItem('carFavorites') || '[]');
    
    document.querySelectorAll('.car-card').forEach(card => {
        const carId = card.dataset.carId;
        if (carId) {
            const favoriteBtn = document.createElement('button');
            favoriteBtn.className = 'btn btn-outline-danger btn-sm favorite-btn position-absolute';
            favoriteBtn.style.cssText = 'top: 10px; right: 10px; z-index: 10;';
            favoriteBtn.innerHTML = '<i class="fas fa-heart"></i>';
            favoriteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleFavorite(carId, favoriteBtn);
            });
            
            card.style.position = 'relative';
            card.appendChild(favoriteBtn);
            
            // Update button state
            if (favorites.includes(carId)) {
                favoriteBtn.classList.remove('btn-outline-danger');
                favoriteBtn.classList.add('btn-danger');
            }
        }
    });
}

/**
 * Toggle favorite status
 */
function toggleFavorite(carId, button) {
    let favorites = JSON.parse(localStorage.getItem('carFavorites') || '[]');
    
    if (favorites.includes(carId)) {
        favorites = favorites.filter(id => id !== carId);
        button.classList.remove('btn-danger');
        button.classList.add('btn-outline-danger');
    } else {
        favorites.push(carId);
        button.classList.remove('btn-outline-danger');
        button.classList.add('btn-danger');
    }
    
    localStorage.setItem('carFavorites', JSON.stringify(favorites));
    showToast(favorites.includes(carId) ? 'Added to favorites' : 'Removed from favorites', 'success');
}

/**
 * Purchase form enhancements
 */
function initializePurchaseFormFeatures() {
    const purchaseForm = document.querySelector('.purchase-form, form[action*="purchase"]');
    if (!purchaseForm) return;
    
    // Down payment calculator
    initializeDownPaymentCalculator();
    
    // Financing calculator
    initializeFinancingCalculator();
    
    // Form progress tracking
    initializeFormProgress();
}

/**
 * Down payment calculator
 */
function initializeDownPaymentCalculator() {
    const downPaymentInput = document.querySelector('input[name="down_payment"]');
    const vehiclePriceElement = document.querySelector('[data-vehicle-price]');
    
    if (downPaymentInput && vehiclePriceElement) {
        const vehiclePrice = parseFloat(vehiclePriceElement.dataset.vehiclePrice);
        
        // Add percentage buttons
        const percentageContainer = document.createElement('div');
        percentageContainer.className = 'mt-2';
        percentageContainer.innerHTML = `
            <small class="text-muted d-block mb-1">Quick select:</small>
            <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn btn-outline-secondary" data-percentage="10">10%</button>
                <button type="button" class="btn btn-outline-secondary" data-percentage="15">15%</button>
                <button type="button" class="btn btn-outline-secondary" data-percentage="20">20%</button>
                <button type="button" class="btn btn-outline-secondary" data-percentage="25">25%</button>
            </div>
        `;
        
        downPaymentInput.parentNode.appendChild(percentageContainer);
        
        // Handle percentage button clicks
        percentageContainer.addEventListener('click', function(e) {
            if (e.target.dataset.percentage) {
                const percentage = parseInt(e.target.dataset.percentage);
                const amount = (vehiclePrice * percentage / 100).toFixed(2);
                downPaymentInput.value = amount;
                downPaymentInput.dispatchEvent(new Event('input'));
            }
        });
        
        // Real-time calculation display
        const calculationDisplay = document.createElement('div');
        calculationDisplay.className = 'mt-2 p-2 bg-light rounded';
        calculationDisplay.innerHTML = '<small class="text-muted">Enter down payment amount to see financing details</small>';
        downPaymentInput.parentNode.appendChild(calculationDisplay);
        
        downPaymentInput.addEventListener('input', function() {
            const downPayment = parseFloat(this.value) || 0;
            const financing = vehiclePrice - downPayment;
            const percentage = ((downPayment / vehiclePrice) * 100).toFixed(1);
            
            calculationDisplay.innerHTML = `
                <small>
                    <strong>Down Payment:</strong> $${downPayment.toLocaleString()} (${percentage}%)<br>
                    <strong>Financing Needed:</strong> $${financing.toLocaleString()}
                </small>
            `;
        });
    }
}

/**
 * Financing calculator
 */
function initializeFinancingCalculator() {
    const financingCheckbox = document.querySelector('input[name="financing_needed"]');
    if (!financingCheckbox) return;
    
    financingCheckbox.addEventListener('change', function() {
        if (this.checked) {
            showFinancingOptions();
        } else {
            hideFinancingOptions();
        }
    });
}

/**
 * Show financing options
 */
function showFinancingOptions() {
    let optionsDiv = document.querySelector('.financing-options');
    if (optionsDiv) return;
    
    const financingCheckbox = document.querySelector('input[name="financing_needed"]');
    optionsDiv = document.createElement('div');
    optionsDiv.className = 'financing-options mt-3 p-3 border rounded';
    optionsDiv.innerHTML = `
        <h6><i class="fas fa-calculator me-2"></i>Financing Options</h6>
        <div class="row g-3">
            <div class="col-md-4">
                <label class="form-label">Loan Term</label>
                <select class="form-select" id="loanTerm">
                    <option value="36">36 months</option>
                    <option value="48" selected>48 months</option>
                    <option value="60">60 months</option>
                    <option value="72">72 months</option>
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Interest Rate</label>
                <input type="number" class="form-control" id="interestRate" value="5.5" step="0.1" min="0" max="30">
            </div>
            <div class="col-md-4">
                <label class="form-label">Est. Monthly Payment</label>
                <input type="text" class="form-control" id="monthlyPayment" readonly>
            </div>
        </div>
        <small class="text-muted mt-2 d-block">
            * This is an estimate. Actual rates and terms may vary based on credit approval.
        </small>
    `;
    
    financingCheckbox.parentNode.appendChild(optionsDiv);
    
    // Calculate payments
    updateMonthlyPayment();
    
    optionsDiv.addEventListener('input', updateMonthlyPayment);
}

/**
 * Hide financing options
 */
function hideFinancingOptions() {
    const optionsDiv = document.querySelector('.financing-options');
    if (optionsDiv) {
        optionsDiv.remove();
    }
}

/**
 * Update monthly payment calculation
 */
function updateMonthlyPayment() {
    const vehiclePriceElement = document.querySelector('[data-vehicle-price]');
    const downPaymentInput = document.querySelector('input[name="down_payment"]');
    const loanTermSelect = document.getElementById('loanTerm');
    const interestRateInput = document.getElementById('interestRate');
    const monthlyPaymentInput = document.getElementById('monthlyPayment');
    
    if (!vehiclePriceElement || !downPaymentInput || !loanTermSelect || !interestRateInput || !monthlyPaymentInput) return;
    
    const vehiclePrice = parseFloat(vehiclePriceElement.dataset.vehiclePrice);
    const downPayment = parseFloat(downPaymentInput.value) || 0;
    const principal = vehiclePrice - downPayment;
    const months = parseInt(loanTermSelect.value);
    const annualRate = parseFloat(interestRateInput.value) / 100;
    const monthlyRate = annualRate / 12;
    
    if (principal <= 0 || monthlyRate <= 0) {
        monthlyPaymentInput.value = '$0.00';
        return;
    }
    
    // Calculate monthly payment using loan formula
    const monthlyPayment = principal * (monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
    
    monthlyPaymentInput.value = `$${monthlyPayment.toFixed(2)}`;
}

/**
 * Form progress tracking
 */
function initializeFormProgress() {
    const forms = document.querySelectorAll('form[data-track-progress="true"]');
    
    forms.forEach(form => {
        const requiredFields = form.querySelectorAll('[required]');
        const progressBar = createProgressBar();
        form.insertBefore(progressBar, form.firstChild);
        
        function updateProgress() {
            const filledFields = Array.from(requiredFields).filter(field => {
                return field.value.trim() !== '' && field.checkValidity();
            });
            
            const progress = (filledFields.length / requiredFields.length) * 100;
            const progressBarFill = progressBar.querySelector('.progress-bar');
            progressBarFill.style.width = `${progress}%`;
            progressBarFill.textContent = `${Math.round(progress)}% Complete`;
        }
        
        requiredFields.forEach(field => {
            field.addEventListener('input', updateProgress);
            field.addEventListener('change', updateProgress);
        });
        
        updateProgress();
    });
}

/**
 * Create progress bar element
 */
function createProgressBar() {
    const container = document.createElement('div');
    container.className = 'form-progress mb-3';
    container.innerHTML = `
        <label class="form-label">Form Progress</label>
        <div class="progress">
            <div class="progress-bar bg-primary" role="progressbar" style="width: 0%">0% Complete</div>
        </div>
    `;
    return container;
}

/**
 * User feedback system
 */
function initializeUserFeedback() {
    // Auto-dismiss alerts
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            if (alert.querySelector('.btn-close')) {
                setTimeout(() => {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }, 5000);
            }
        });
    }, 1000);
    
    // Confirm dangerous actions
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-confirm]')) {
            const message = e.target.dataset.confirm || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        }
    });
    
    // Loading states for forms
    document.addEventListener('submit', function(e) {
        const submitBtn = e.target.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            submitBtn.disabled = true;
            
            // Re-enable after 10 seconds as fallback
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 10000);
        }
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
    bsToast.show();
    
    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Utility functions
 */

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format number with commas
function formatNumber(number) {
    return new Intl.NumberFormat('en-US').format(number);
}

// Debounce function for performance
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

// Throttle function for scroll events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for testing (if in test environment)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatCurrency,
        formatNumber,
        debounce,
        throttle,
        showToast
    };
}
