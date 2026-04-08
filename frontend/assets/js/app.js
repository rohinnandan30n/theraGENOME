/**
 * TheraGENOME AI — Demo Control Panel
 * Main application logic and event handling
 */

class DemoControlPanel {
    constructor() {
        this.isLoading = false;
        this.currentResult = null;
        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        this.setupEventListeners();
        this.checkBackendHealth();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Demo buttons
        document.querySelectorAll('.demo-button').forEach(button => {
            button.addEventListener('click', () => this.handleDemoButtonClick(button));
        });

        // Explanation toggle
        const toggleExplanation = document.getElementById('toggleExplanation');
        if (toggleExplanation) {
            toggleExplanation.addEventListener('click', () => this.toggleExplanation());
        }

        // Raw response toggle
        const toggleRawResponse = document.getElementById('toggleRawResponse');
        if (toggleRawResponse) {
            toggleRawResponse.addEventListener('click', () => this.toggleRawResponse());
        }

        // Reset button
        const resetButton = document.getElementById('resetButton');
        if (resetButton) {
            resetButton.addEventListener('click', () => this.reset());
        }

        // Error retry button
        const errorRetryButton = document.getElementById('errorRetryButton');
        if (errorRetryButton) {
            errorRetryButton.addEventListener('click', () => this.reset());
        }

        // Mode selector
        const modeSelect = document.getElementById('modeSelect');
        if (modeSelect) {
            modeSelect.addEventListener('change', (e) => {
                // Store mode preference
                localStorage.setItem('preferredMode', e.target.value);
            });
        }
    }

    /**
     * Handle demo button click
     */
    async handleDemoButtonClick(button) {
        if (this.isLoading) return;

        const caseId = button.getAttribute('data-case-id');
        const mode = document.getElementById('modeSelect')?.value || 'doctor';

        this.isLoading = true;
        button.classList.add('loading');

        // Show loading state
        UIRenderer.showLoading();

        // Simulate 1-2 second processing
        await this.simulateProcessing();

        // Call API
        const result = await apiClient.runDemoCase(caseId, mode, 'full');

        this.isLoading = false;
        button.classList.remove('loading');

        if (result.success) {
            this.currentResult = result.data;
            UIRenderer.renderDemoResult(result.data);
            UIRenderer.showResults();
        } else {
            UIRenderer.showError(result.error || 'Failed to run demo scenario');
        }
    }

    /**
     * Simulate processing delay (1-2 seconds)
     */
    simulateProcessing() {
        const delay = Math.random() * 1000 + 500; // 500-1500ms
        return new Promise(resolve => setTimeout(resolve, delay));
    }

    /**
     * Toggle explanation panel
     */
    toggleExplanation() {
        const button = document.getElementById('toggleExplanation');
        const panel = document.getElementById('explanationPanel');

        if (panel) {
            const isHidden = panel.classList.contains('hidden');

            if (isHidden) {
                panel.classList.remove('hidden');
                if (button) button.textContent = '💡 Hide Explanation';
            } else {
                panel.classList.add('hidden');
                if (button) button.textContent = '💡 Show Explanation';
            }
        }
    }

    /**
     * Toggle raw response display
     */
    toggleRawResponse() {
        const button = document.getElementById('toggleRawResponse');
        const container = document.getElementById('rawResponseContainer');

        if (container) {
            const isHidden = container.classList.contains('hidden');

            if (isHidden) {
                container.classList.remove('hidden');
                if (button) button.textContent = '📊 Hide Raw Response';
            } else {
                container.classList.add('hidden');
                if (button) button.textContent = '📊 View Raw Response';
            }
        }
    }

    /**
     * Reset to initial state
     */
    reset() {
        this.currentResult = null;
        UIRenderer.hideSection('resultsContainer');
        UIRenderer.hideSection('explanationPanel');
        UIRenderer.hideSection('comparisonView');
        UIRenderer.hideSection('reportView');
        UIRenderer.hideSection('safetyWarning');
        UIRenderer.hideSection('rawResponseContainer');

        // Reset buttons
        document.getElementById('toggleExplanation').textContent = '💡 Show Explanation';
        document.getElementById('toggleRawResponse').textContent = '📊 View Raw Response';

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /**
     * Check if backend is healthy
     */
    async checkBackendHealth() {
        const isHealthy = await apiClient.healthCheck();

        if (!isHealthy) {
            console.warn('Backend health check failed. API may not be available.');
            // Could show a warning banner here if needed
        }
    }

    /**
     * Get available demo cases (for future filtering)
     */
    async loadAvailableCases() {
        const result = await apiClient.getAvailableCases();
        if (result.success) {
            console.log('Available cases:', result.data);
            return result.data;
        }
        return null;
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.demoPanel = new DemoControlPanel();
    console.log('Demo Control Panel initialized');
});
