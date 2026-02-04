/**
 * Public Transport Tracking Frontend Application
 */

const API_BASE = 'http://localhost:8000';

class TransportTracker {
    constructor() {
        this.healthCheckInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkHealthStatus();
        this.addActivityLog('Application initialized');
        this.startHealthCheck();
    }

    startHealthCheck() {
        this.healthCheckInterval = setInterval(() => {
            this.checkHealthStatus();
        }, 30000);
    }

    stopHealthCheck() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }
    }

    bindEvents() {
        const locationBtn = document.getElementById('get-location');
        const routesBtn = document.getElementById('get-routes');
        const etaBtn = document.getElementById('get-eta');

        if (locationBtn) locationBtn.addEventListener('click', () => this.getBusLocation());
        if (routesBtn) routesBtn.addEventListener('click', () => this.getBusRoutes());
        if (etaBtn) etaBtn.addEventListener('click', () => this.getETA());

        const busIdInput = document.getElementById('bus-id');
        const busNumberRoutesInput = document.getElementById('bus-number-routes');
        const busNumberEtaInput = document.getElementById('bus-number-eta');
        const routeIdInput = document.getElementById('user-route-id');

        if (busIdInput) busIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.getBusLocation();
        });
        if (busNumberRoutesInput) busNumberRoutesInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.getBusRoutes();
        });
        if (busNumberEtaInput) busNumberEtaInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.getETA();
        });
        if (routeIdInput) routeIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.getETA();
        });
    }

    async checkHealthStatus() {
        const statusElement = document.getElementById('health-status');
        if (!statusElement) return;

        try {
            const response = await fetch(`${API_BASE}/health`);
            const data = await response.json();

            if (response.ok && data.status === 'healthy') {
                statusElement.className = 'status-indicator healthy';
                statusElement.innerHTML = '<i class="fas fa-check-circle"></i> System Online';
            } else {
                statusElement.className = 'status-indicator unhealthy';
                statusElement.innerHTML = '<i class="fas fa-times-circle"></i> System Issues';
            }
        } catch (error) {
            statusElement.className = 'status-indicator unhealthy';
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Connection Failed';
        }
    }

    async getBusLocation() {
        const busIdInput = document.getElementById('bus-id');
        const resultElement = document.getElementById('location-result');
        const button = document.getElementById('get-location');

        if (!busIdInput || !resultElement || !button) return;

        const busId = busIdInput.value.trim();

        if (!busId || isNaN(parseInt(busId)) || parseInt(busId) < 1) {
            this.showResult(resultElement, 'Please enter a valid bus ID', 'error');
            return;
        }

        this.setLoading(button, true);
        this.addActivityLog(`Fetching location for bus ID: ${busId}`);

        try {
            const response = await fetch(`${API_BASE}/bus/${busId}/live`);
            const data = await response.json();

            if (response.ok) {
                const locationHtml = this.formatLocationData(data);
                this.showResult(resultElement, locationHtml, 'success');
                this.addActivityLog(`Location retrieved for bus ${data.bus_number}`, 'success');
            } else {
                this.showResult(resultElement, data.detail || 'Bus not found', 'error');
                this.addActivityLog(`Location lookup failed`, 'error');
            }
        } catch (error) {
            this.showResult(resultElement, 'Connection error. Please check if the API is running.', 'error');
            this.addActivityLog(`Error: ${error.message}`, 'error');
        } finally {
            this.setLoading(button, false);
        }
    }

    async getBusRoutes() {
        const busNumberInput = document.getElementById('bus-number-routes');
        const resultElement = document.getElementById('routes-result');
        const button = document.getElementById('get-routes');

        if (!busNumberInput || !resultElement || !button) return;

        const busNumber = busNumberInput.value.trim().toUpperCase();

        if (!busNumber) {
            this.showResult(resultElement, 'Please enter a bus number', 'error');
            return;
        }

        this.setLoading(button, true);
        this.addActivityLog(`Fetching routes for bus: ${busNumber}`);

        try {
            const response = await fetch(`${API_BASE}/bus/${encodeURIComponent(busNumber)}/routes`);
            const data = await response.json();

            if (response.ok) {
                const routesHtml = this.formatRoutesData(data);
                this.showResult(resultElement, routesHtml, 'success');
                this.addActivityLog(`Routes retrieved for bus ${data.bus_number}`, 'success');
            } else {
                this.showResult(resultElement, data.detail || 'Bus not found', 'error');
                this.addActivityLog(`Routes lookup failed`, 'error');
            }
        } catch (error) {
            this.showResult(resultElement, 'Connection error.', 'error');
            this.addActivityLog(`Error: ${error.message}`, 'error');
        } finally {
            this.setLoading(button, false);
        }
    }

    async getETA() {
        const busNumberInput = document.getElementById('bus-number-eta');
        const routeIdInput = document.getElementById('user-route-id');
        const resultElement = document.getElementById('eta-result');
        const button = document.getElementById('get-eta');

        if (!busNumberInput || !routeIdInput || !resultElement || !button) return;

        const busNumber = busNumberInput.value.trim().toUpperCase();
        const routeId = routeIdInput.value.trim();

        if (!busNumber || !routeId) {
            this.showResult(resultElement, 'Please enter both bus number and route ID', 'error');
            return;
        }

        this.setLoading(button, true);
        this.addActivityLog(`Calculating ETA for bus ${busNumber}`);

        try {
            const response = await fetch(`${API_BASE}/bus/${encodeURIComponent(busNumber)}/eta?route_id=${routeId}`);
            const data = await response.json();

            if (response.ok) {
                const etaHtml = this.formatETAData(data);
                this.showResult(resultElement, etaHtml, 'info');
                this.addActivityLog(`ETA calculated for bus ${data.bus_number}`, 'success');
            } else {
                this.showResult(resultElement, data.detail || 'Unable to calculate ETA', 'error');
                this.addActivityLog(`ETA calculation failed`, 'error');
            }
        } catch (error) {
            this.showResult(resultElement, 'Connection error.', 'error');
            this.addActivityLog(`Error: ${error.message}`, 'error');
        } finally {
            this.setLoading(button, false);
        }
    }

    formatLocationData(data) {
        const statusStyle = data.is_active ? 'color: #27ae60;' : 'color: #dc3545;';
        const statusText = data.is_active ? 'Active' : 'Inactive';

        let locationInfo = 'No location data available';
        if (data.latest_latitude !== null && data.latest_longitude !== null) {
            locationInfo = `
                <div class="location-info">
                    <div class="coordinates">
                        Lat: ${data.latest_latitude.toFixed(6)}<br>
                        Lon: ${data.latest_longitude.toFixed(6)}
                    </div>
                    ${data.route_name ? `<div class="route-name">Route: ${data.route_name}</div>` : ''}
                </div>
            `;
        }

        const recordedAt = data.recorded_at ? new Date(data.recorded_at).toLocaleString() : 'Never';

        return `
            <div class="data-grid">
                <span class="data-label">Bus Number:</span>
                <span class="data-value"><strong>${data.bus_number}</strong></span>
                <span class="data-label">Status:</span>
                <span class="data-value"><span style="${statusStyle}">${statusText}</span></span>
                <span class="data-label">Location:</span>
                <span class="data-value">${locationInfo}</span>
                <span class="data-label">Last Updated:</span>
                <span class="data-value">${recordedAt}</span>
            </div>
        `;
    }

    formatRoutesData(data) {
        return `
            <div class="data-grid">
                <span class="data-label">Bus Number:</span>
                <span class="data-value"><strong>${data.bus_number}</strong></span>
                <span class="data-label">Current Route:</span>
                <span class="data-value">${data.current_route_id !== null ? `Route ${data.current_route_id}` : 'Not assigned'}</span>
                <span class="data-label">Previous Route:</span>
                <span class="data-value">${data.previous_route_id !== null ? `Route ${data.previous_route_id}` : 'None'}</span>
            </div>
        `;
    }

    formatETAData(data) {
        return `
            <div style="text-align: center;">
                <div style="font-size: 1.2rem; margin-bottom: 15px; color: #2c3e50;">
                    <strong>${data.bus_number}</strong>
                </div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #3498db; margin-bottom: 15px;">
                    <i class="fas fa-clock"></i> ${data.estimated_arrival_time}
                </div>
                <div class="data-grid" style="justify-content: center;">
                    <span class="data-label">Current Route:</span>
                    <span class="data-value">Route ${data.current_route_id}</span>
                </div>
            </div>
        `;
    }

    showResult(element, content, type = 'info') {
        if (!element) return;
        element.className = `result-box ${type}`;
        element.innerHTML = content;
        element.classList.remove('hidden');
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    setLoading(button, loading) {
        if (!button) return;
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    addActivityLog(message, type = 'info') {
        const logElement = document.getElementById('activity-log');
        if (!logElement) return;

        const timestamp = new Date().toLocaleTimeString();
        const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️' };

        const logItem = document.createElement('div');
        logItem.className = `activity-item ${type}`;
        logItem.innerHTML = `<span class="timestamp">[${timestamp}]</span> <span>${icons[type] || icons.info} ${this.escapeHtml(message)}</span>`;

        logElement.insertBefore(logItem, logElement.firstChild);

        while (logElement.children.length > 15) {
            logElement.removeChild(logElement.lastChild);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

let tracker = null;

document.addEventListener('DOMContentLoaded', () => {
    tracker = new TransportTracker();
    window.tracker = tracker;
});

window.addEventListener('beforeunload', () => {
    if (tracker) tracker.stopHealthCheck();
});
