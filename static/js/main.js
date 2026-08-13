// HepatoX - Main JavaScript File

// Toggle dark mode
const toggleDarkMode = () => {
    const body = document.body;
    body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', body.classList.contains('dark-mode'));
};

// Initialize tooltips
const initializeTooltips = () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
};

// Initialize popovers
const initializePopovers = () => {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
};

// Show toast notifications
const showToast = (message, type = 'info', duration = 3000) => {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    toastContainer.innerHTML = toastHtml;
    
    const toast = new bootstrap.Toast(toastContainer.querySelector('.toast'));
    toast.show();
};

// Create toast container
const createToastContainer = () => {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
};

// Validate form
const validateForm = (formId) => {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
};

// API helper functions
const api = {
    baseUrl: '/api/v1',
    
    async get(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API GET error:', error);
            throw error;
        }
    },
    
    async post(endpoint, data = {}, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                body: JSON.stringify(data),
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API POST error:', error);
            throw error;
        }
    },
    
    async put(endpoint, data = {}, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                body: JSON.stringify(data),
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API PUT error:', error);
            throw error;
        }
    },
    
    async delete(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API DELETE error:', error);
            throw error;
        }
    }
};

// Utility functions
const utils = {
    formatDate: (date) => {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    formatTime: (date) => {
        return new Date(date).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    formatCurrency: (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    },
    
    formatPercent: (value, decimals = 2) => {
        return (value * 100).toFixed(decimals) + '%';
    },
    
    cloneObject: (obj) => {
        return JSON.parse(JSON.stringify(obj));
    }
};

// Search functionality
const searchTable = (inputId, tableId) => {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    input.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const table = document.getElementById(tableId);
        const rows = table.getElementsByTagName('tr');
        
        for (let i = 1; i < rows.length; i++) {
            const text = rows[i].textContent.toLowerCase();
            rows[i].style.display = text.includes(filter) ? '' : 'none';
        }
    });
};

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize popovers and tooltips
    initializeTooltips();
    initializePopovers();
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
    
    // Initialize number formatting
    const formatNumberInputs = () => {
        const numberInputs = document.querySelectorAll('input[type="number"]');
        numberInputs.forEach(input => {
            input.addEventListener('change', function() {
                this.value = parseFloat(this.value).toFixed(2);
            });
        });
    };
    // Interactive 3D Card Tilt Effect
    const initCardTilt = () => {
        const cards = document.querySelectorAll('.glass-card, .stat-card, .liver-scanner-box');
        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                card.style.transform = `perspective(1000px) rotateX(${-y / 25}deg) rotateY(${x / 25}deg) translateY(-5px)`;
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
            });
        });
    };
    initCardTilt();
});

// Scan Step Animation Helper
const animateScanSteps = (elementId) => {
    const el = document.getElementById(elementId);
    if (!el) return;
    const steps = [
        "Synthesizing patient lab metrics...",
        "Cross-referencing 10 ML neural ensembles...",
        "Evaluating LFT scores & biomarker indices...",
        "Running SHAP & LIME kernel explainers...",
        "Finalizing diagnostic confidence matrix..."
    ];
    let idx = 0;
    const interval = setInterval(() => {
        idx = (idx + 1) % steps.length;
        el.innerText = steps[idx];
    }, 800);
    return () => clearInterval(interval);
};

// Export for use in other files
window.hepatoxUtils = {
    api,
    utils,
    showToast,
    validateForm,
    searchTable,
    animateScanSteps
};
