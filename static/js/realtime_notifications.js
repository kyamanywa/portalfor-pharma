/**
 * Real-time Notifications System using WebSockets
 * Provides instant updates across all dashboards without page refresh
 * 
 * Features:
 * - Auto-reconnect on connection loss
 * - Role-based notification filtering
 * - Visual and audio notifications
 * - Keep-alive ping/pong
 */

class RealTimeNotifications {
    constructor() {
        this.socket = null;
        this.reconnectInterval = 3000; // 3 seconds
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        this.pingInterval = null;
        this.isConnected = false;
        
        // Notification sound (subtle beep)
        this.notificationSound = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdW5tZXl1c3h0c3Z0d3d3eHl5enp6e3t7fHx8fX19fn5+f39/gICAgoKChISEh4eHioqKjY2Nj4+PkZGRk5OTlZWVmJiYm5ubnZ2dn5+foaGho6Ojpqamp6enqKioqampqqqqq6urrKysra2trq6ur6+vsLCwsbGxsrKys7OztLS0tbW1tra2t7e3uLi4ubm5urq6u7u7vLy8vb29vr6+v7+/wMDAwcHBwsLCw8PDxMTExcXFxsbGx8fHyMjIycnJysrKy8vLzMzMzc3Nzs7Oz8/P0NDQ0dHR0tLS09PT1NTU1dXV1tbW19fX2NjY2dnZ2tra29vb3Nzc3d3d3t7e39/f4ODg4eHh4uLi4+Pj5OTk5eXl5ubm5+fn6Ojo6enp6urq6+vr7Ozs7e3t7u7u7+/v8PDw8fHx8vLy8/Pz9PT09fX19vb29/f3+Pj4+fn5+vr6+/v7/Pz8/f39/v7+////AAAA');
    }

    /**
     * Initialize WebSocket connection
     */
    connect() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/notifications/`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = (event) => this.onOpen(event);
        this.socket.onmessage = (event) => this.onMessage(event);
        this.socket.onclose = (event) => this.onClose(event);
        this.socket.onerror = (event) => this.onError(event);
    }

    /**
     * Handle WebSocket connection established
     */
    onOpen(event) {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Start keep-alive ping
        this.startPing();
        
        // Show connection status
        this.showConnectionStatus(true);
    }

    /**
     * Handle incoming WebSocket messages
     */
    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            switch (data.type) {
                case 'connection_established':
                    console.log('Connected as user:', data.username);
                    break;
                    
                case 'phase_update':
                    this.handlePhaseUpdate(data);
                    break;
                    
                case 'bmr_status_update':
                    this.handleBMRUpdate(data);
                    break;
                    
                case 'material_release_update':
                    this.handleMaterialReleaseUpdate(data);
                    break;
                    
                case 'qc_update':
                    this.handleQCUpdate(data);
                    break;
                    
                case 'pong':
                    // Keep-alive response
                    break;
                    
                default:
                    console.log('Unknown message type:', data.type);
            }
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
        }
    }

    /**
     * Handle WebSocket connection closed
     */
    onClose(event) {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.stopPing();
        this.showConnectionStatus(false);
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connect(), this.reconnectInterval);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    /**
     * Handle WebSocket errors
     */
    onError(event) {
        console.error('WebSocket error:', event);
    }

    /**
     * Start keep-alive ping
     */
    startPing() {
        this.pingInterval = setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                }));
            }
        }, 30000); // Ping every 30 seconds
    }

    /**
     * Stop keep-alive ping
     */
    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Handle phase status update
     */
    handlePhaseUpdate(data) {
        const { phase_id, bmr_number, phase_name, status, updated_by, timestamp } = data;
        
        // Update phase status in UI
        const phaseElement = document.querySelector(`[data-phase-id="${phase_id}"]`);
        if (phaseElement) {
            phaseElement.setAttribute('data-status', status);
            phaseElement.classList.remove('status-pending', 'status-in_progress', 'status-completed', 'status-failed');
            phaseElement.classList.add(`status-${status}`);
            
            // Update status text
            const statusBadge = phaseElement.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = status.replace('_', ' ').toUpperCase();
            }
        }
        
        // Update batch tracking table if exists
        this.updateBatchTracking(bmr_number, phase_name, status);
        
        // Show notification
        this.showNotification({
            title: 'Phase Status Updated',
            message: `${phase_name} phase for ${bmr_number} is now ${status}`,
            icon: 'info',
            updated_by: updated_by,
            timestamp: timestamp
        });
        
        // Play notification sound
        this.playNotificationSound();
    }

    /**
     * Handle BMR status update
     */
    handleBMRUpdate(data) {
        const { bmr_number, batch_number, status, updated_by, timestamp } = data;
        
        // Update BMR status in UI
        const bmrElement = document.querySelector(`[data-bmr-number="${bmr_number}"]`);
        if (bmrElement) {
            bmrElement.setAttribute('data-status', status);
            bmrElement.classList.remove('status-draft', 'status-submitted', 'status-approved', 'status-rejected', 'status-in_production', 'status-completed');
            bmrElement.classList.add(`status-${status}`);
        }
        
        // Update BMR tracking table
        this.updateBMRTracking(bmr_number, batch_number, status);
        
        // Show notification
        this.showNotification({
            title: 'BMR Status Updated',
            message: `BMR ${bmr_number} (Batch: ${batch_number}) status changed to ${status}`,
            icon: 'info',
            updated_by: updated_by,
            timestamp: timestamp
        });
        
        this.playNotificationSound();
    }

    /**
     * Handle material release update
     */
    handleMaterialReleaseUpdate(data) {
        const { release_number, status, updated_by, timestamp } = data;
        
        // Update material release in UI
        const releaseElement = document.querySelector(`[data-release-number="${release_number}"]`);
        if (releaseElement) {
            releaseElement.setAttribute('data-status', status);
        }
        
        // Show notification
        this.showNotification({
            title: 'Material Release Updated',
            message: `Release ${release_number} status: ${status}`,
            icon: 'info',
            updated_by: updated_by,
            timestamp: timestamp
        });
        
        this.playNotificationSound();
    }

    /**
     * Handle QC/quarantine update
     */
    handleQCUpdate(data) {
        const { batch_number, quarantine_status, action, updated_by, timestamp } = data;
        
        // Update quarantine status in UI
        const quarantineElement = document.querySelector(`[data-batch-number="${batch_number}"]`);
        if (quarantineElement) {
            quarantineElement.setAttribute('data-quarantine-status', quarantine_status);
        }
        
        // Show notification
        this.showNotification({
            title: 'QC Update',
            message: `Batch ${batch_number}: ${action} - Quarantine status: ${quarantine_status}`,
            icon: action === 'approved' ? 'success' : 'warning',
            updated_by: updated_by,
            timestamp: timestamp
        });
        
        this.playNotificationSound();
    }

    /**
     * Update batch tracking table
     */
    updateBatchTracking(bmr_number, phase_name, status) {
        // Find and update the row in batch tracking section
        const rows = document.querySelectorAll('.batch-tracking-row');
        rows.forEach(row => {
            const rowBmrNumber = row.getAttribute('data-bmr');
            if (rowBmrNumber === bmr_number) {
                const phaseCell = row.querySelector(`[data-phase="${phase_name}"]`);
                if (phaseCell) {
                    phaseCell.textContent = status;
                    phaseCell.classList.remove('pending', 'in-progress', 'completed', 'failed');
                    phaseCell.classList.add(status.replace('_', '-'));
                }
            }
        });
    }

    /**
     * Update BMR tracking table
     */
    updateBMRTracking(bmr_number, batch_number, status) {
        const rows = document.querySelectorAll('.bmr-tracking-row');
        rows.forEach(row => {
            const rowBmrNumber = row.getAttribute('data-bmr');
            if (rowBmrNumber === bmr_number) {
                const statusCell = row.querySelector('.status-cell');
                if (statusCell) {
                    statusCell.textContent = status;
                    statusCell.classList.remove('draft', 'submitted', 'approved', 'rejected', 'in-production', 'completed');
                    statusCell.classList.add(status.replace('_', '-'));
                }
            }
        });
    }

    /**
     * Show browser notification
     */
    showNotification({ title, message, icon, updated_by, timestamp }) {
        // Show toast notification
        const toast = document.createElement('div');
        toast.className = `notification-toast notification-${icon || 'info'}`;
        toast.innerHTML = `
            <div class="notification-content">
                <div class="notification-header">
                    <span class="notification-title">${title}</span>
                    <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
                </div>
                <div class="notification-message">${message}</div>
                ${updated_by ? `<div class="notification-meta">By: ${updated_by} • ${new Date(timestamp).toLocaleString()}</div>` : ''}
            </div>
        `;
        
        // Add to notification container
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    /**
     * Show connection status
     */
    showConnectionStatus(connected) {
        const statusElement = document.getElementById('websocket-status');
        if (statusElement) {
            statusElement.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
            statusElement.className = connected ? 'status-connected' : 'status-disconnected';
        }
    }

    /**
     * Play notification sound
     */
    playNotificationSound() {
        try {
            this.notificationSound.volume = 0.3;
            this.notificationSound.play().catch(e => console.log('Audio play failed:', e));
        } catch (error) {
            console.log('Error playing notification sound:', error);
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        this.stopPing();
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.isConnected = false;
    }
}

// Initialize real-time notifications when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated (WebSocket requires auth)
    if (typeof window.userId !== 'undefined' && window.userId) {
        const notifications = new RealTimeNotifications();
        notifications.connect();
        
        // Store instance globally for debugging
        window.realTimeNotifications = notifications;
        
        console.log('Real-time notifications system initialized');
    } else {
        console.log('User not authenticated, skipping WebSocket connection');
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (window.realTimeNotifications) {
        window.realTimeNotifications.disconnect();
    }
});