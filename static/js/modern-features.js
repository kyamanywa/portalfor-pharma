/**
 * Modern Theme System with Dark/Light Mode Toggle
 * KPI Operations System
 */

class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('kpi-theme') || 'light';
        this.init();
    }

    init() {
        // Apply saved theme
        this.applyTheme(this.currentTheme);
        
        // Create theme toggle button
        this.createThemeToggle();
        
        // Add event listeners
        this.bindEvents();
        
        // Initialize other modern features
        this.initModernFeatures();
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        localStorage.setItem('kpi-theme', theme);
        
        // Update theme toggle icon
        this.updateThemeIcon();
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        
        // Add a subtle animation
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    createThemeToggle() {
        const toggle = document.createElement('div');
        toggle.className = 'theme-toggle';
        toggle.innerHTML = '<i class="fas fa-moon" id="theme-icon"></i>';
        toggle.setAttribute('title', 'Toggle theme');
        toggle.setAttribute('data-bs-toggle', 'tooltip');
        
        document.body.appendChild(toggle);
        
        // Initialize Bootstrap tooltip
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Tooltip(toggle);
        }
    }

    updateThemeIcon() {
        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.className = this.currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }

    bindEvents() {
        // Theme toggle click
        document.addEventListener('click', (e) => {
            if (e.target.closest('.theme-toggle')) {
                this.toggleTheme();
            }
        });

        // System theme preference detection
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                if (!localStorage.getItem('kpi-theme')) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    initModernFeatures() {
        // Add fade-in animation to cards
        this.animateCards();
        
        // Initialize loading states
        this.initLoadingStates();
        
        // Enhanced tooltips
        this.initTooltips();
        
        // Real-time clock
        this.initClock();
    }

    animateCards() {
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('fade-in');
        });
    }

    initLoadingStates() {
        // Skip initialization entirely on admin dashboard to avoid conflicts
        if (window.location.pathname.includes('/admin-overview/') || 
            document.body.classList.contains('admin-dashboard') || 
            document.querySelector('.admin-dashboard-container')) {
            console.log('Modern features: Skipping loading states on admin dashboard');
            return;
        }
        
        // Add loading states to forms when submitted
        document.addEventListener('submit', (e) => {
            const form = e.target;
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            
            if (submitBtn) {
                this.showButtonLoading(submitBtn);
            }
        });
        
        // Handle direct button clicks for other button types - EXCLUDE NAVIGATION LINKS
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn');
            // FIXED: Exclude sidebar navigation links and other important navigation elements
            if (btn && 
                btn.type !== 'submit' && 
                !btn.closest('form') && 
                !btn.closest('.section-link') &&  // Exclude section navigation
                !btn.closest('.sidebar-menu') &&  // Exclude sidebar menu items
                !btn.closest('.nav-item') &&      // Exclude navbar items
                !btn.hasAttribute('data-section') && // Exclude data-section elements
                !btn.hasAttribute('data-bs-toggle') && // Exclude Bootstrap toggles
                !btn.classList.contains('section-link') // Double-check section links
            ) {
                // Only add loading to non-navigation buttons
                this.showButtonLoading(btn);
            }
        });
    }

    showButtonLoading(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<span class="loading-spinner"></span> Processing...';
        button.disabled = true;
        
        // Restore button after 3 seconds (or when form submits)
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    }

    initTooltips() {
        // Initialize all Bootstrap tooltips
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    initClock() {
        // Add a real-time clock to the navbar if there's a placeholder
        const clockElement = document.getElementById('live-clock');
        if (clockElement) {
            this.updateClock();
            setInterval(() => this.updateClock(), 1000);
        }
    }

    updateClock() {
        const clockElement = document.getElementById('live-clock');
        if (clockElement) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            const dateString = now.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
            });
            clockElement.innerHTML = `${dateString} ${timeString}`;
        }
    }
}

/**
 * Enhanced Dashboard Features
 */
class DashboardEnhancements {
    constructor() {
        this.init();
    }

    init() {
        this.createKPICards();
        this.enhanceStatusBadges();
        this.addProgressBars();
        this.initCounterAnimations();
    }

    createKPICards() {
        // Convert existing metrics to modern KPI cards
        const existingMetrics = document.querySelectorAll('.metric, .stat-card');
        existingMetrics.forEach(metric => {
            if (!metric.classList.contains('kpi-card')) {
                metric.classList.add('kpi-card');
            }
        });
    }

    enhanceStatusBadges() {
        // Convert status text to modern badges
        const statusElements = document.querySelectorAll('[class*="status-"], .badge');
        statusElements.forEach(element => {
            const status = this.getStatusFromElement(element);
            if (status) {
                element.className = `status-badge status-${status}`;
                
                // Add status icon
                const icon = this.getStatusIcon(status);
                if (icon && !element.querySelector('i')) {
                    element.innerHTML = `<i class="${icon}"></i> ${element.textContent.trim()}`;
                }
            }
        });
    }

    getStatusFromElement(element) {
        const text = element.textContent.toLowerCase();
        const className = element.className.toLowerCase();
        
        if (text.includes('completed') || className.includes('completed') || className.includes('success')) {
            return 'completed';
        } else if (text.includes('pending') || className.includes('pending') || className.includes('warning')) {
            return 'pending';
        } else if (text.includes('progress') || className.includes('progress') || className.includes('info')) {
            return 'in-progress';
        } else if (text.includes('failed') || className.includes('failed') || className.includes('danger')) {
            return 'failed';
        }
        return null;
    }

    getStatusIcon(status) {
        const icons = {
            'completed': 'fas fa-check-circle',
            'pending': 'fas fa-clock',
            'in-progress': 'fas fa-spinner fa-spin',
            'failed': 'fas fa-exclamation-triangle'
        };
        return icons[status];
    }

    addProgressBars() {
        // Add progress indicators where appropriate
        const progressElements = document.querySelectorAll('[data-progress]');
        progressElements.forEach(element => {
            const progress = element.getAttribute('data-progress');
            if (progress) {
                this.createProgressBar(element, progress);
            }
        });
    }

    createProgressBar(container, progress) {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress mt-2';
        progressBar.style.height = '8px';
        
        const progressBarFill = document.createElement('div');
        progressBarFill.className = 'progress-bar bg-primary';
        progressBarFill.style.width = `${progress}%`;
        progressBarFill.setAttribute('role', 'progressbar');
        
        progressBar.appendChild(progressBarFill);
        container.appendChild(progressBar);
        
        // Animate the progress bar
        setTimeout(() => {
            progressBarFill.style.transition = 'width 1s ease-in-out';
        }, 100);
    }

    initCounterAnimations() {
        // Animate numbers in KPI cards
        const counters = document.querySelectorAll('.kpi-value, [data-counter]');
        counters.forEach(counter => {
            const target = parseInt(counter.textContent) || 0;
            if (target > 0) {
                this.animateCounter(counter, target);
            }
        });
    }

    animateCounter(element, target) {
        let current = 0;
        const increment = target / 50; // 50 steps
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 20);
    }
}

/**
 * Integration-Ready Features
 */
class IntegrationManager {
    constructor() {
        this.apiBaseUrl = window.location.origin + '/api/';
        this.init();
    }

    init() {
        this.setupCSRFToken();
        this.createAPIHelpers();
        this.initWebSocketSupport();
    }

    setupCSRFToken() {
        // Get CSRF token for API calls
        const csrfToken = document.querySelector('[name=csrf-token]')?.getAttribute('content') ||
                         document.querySelector('[name=csrfmiddlewaretoken]')?.getAttribute('value');
        
        if (csrfToken) {
            this.csrfToken = csrfToken;
            
            // Set default headers for fetch requests
            window.fetch = ((originalFetch) => {
                return (url, options = {}) => {
                    if (!options.headers) options.headers = {};
                    if (!options.headers['X-CSRFToken'] && this.csrfToken) {
                        options.headers['X-CSRFToken'] = this.csrfToken;
                    }
                    return originalFetch(url, options);
                };
            })(window.fetch);
        }
    }

    createAPIHelpers() {
        // Create global API helper object
        window.KPIAPI = {
            get: (endpoint) => this.apiRequest('GET', endpoint),
            post: (endpoint, data) => this.apiRequest('POST', endpoint, data),
            put: (endpoint, data) => this.apiRequest('PUT', endpoint, data),
            delete: (endpoint) => this.apiRequest('DELETE', endpoint),
        };
    }

    async apiRequest(method, endpoint, data = null) {
        const url = endpoint.startsWith('http') ? endpoint : this.apiBaseUrl + endpoint.replace(/^\//, '');
        
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'API request failed');
            }
            
            return result;
        } catch (error) {
            console.error(`API ${method} request failed:`, error);
            throw error;
        }
    }

    initWebSocketSupport() {
        // Prepare WebSocket connection for real-time features
        if (typeof WebSocket !== 'undefined') {
            window.KPIWebSocket = {
                connect: (endpoint) => this.connectWebSocket(endpoint),
                disconnect: () => this.disconnectWebSocket()
            };
        }
    }

    connectWebSocket(endpoint) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${endpoint}/`;
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.dispatchEvent('websocket:connected');
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.dispatchEvent('websocket:message', data);
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this.dispatchEvent('websocket:disconnected');
            };
            
            return this.socket;
        } catch (error) {
            console.log('WebSocket not available, using polling instead');
            return null;
        }
    }

    disconnectWebSocket() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    dispatchEvent(type, data = null) {
        const event = new CustomEvent(type, { detail: data });
        document.dispatchEvent(event);
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
    window.dashboardEnhancements = new DashboardEnhancements();
    window.integrationManager = new IntegrationManager();
    
    console.log('🚀 KPI Operations System - Modern Features Loaded');
});