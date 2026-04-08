/**
 * TheraGENOME AI — API Client
 * Handles all communication with the backend demo API
 */

class DemoAPIClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    /**
     * Run a demo scenario
     * @param {string} caseId - Demo scenario ID (safe_case, high_risk_case, comparison_case)
     * @param {string} mode - Display mode (doctor, patient)
     * @param {string} scope - Explanation scope (full, summary)
     * @returns {Promise<Object>} Demo result with DEMO_RESULT template
     */
    async runDemoCase(caseId, mode = 'doctor', scope = 'full') {
        try {
            const response = await fetch(`${this.baseUrl}/api/demo/run`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    case_id: caseId,
                    mode: mode,
                    scope: scope,
                }),
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            return {
                success: true,
                data: data,
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
            };
        }
    }

    /**
     * Get list of available demo cases
     * @returns {Promise<Object>} List of available scenarios
     */
    async getAvailableCases() {
        try {
            const response = await fetch(`${this.baseUrl}/api/demo/cases`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            return {
                success: true,
                data: data,
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
            };
        }
    }

    /**
     * Health check - verify backend is running
     * @returns {Promise<boolean>} True if backend is healthy
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Create global API client instance
const apiClient = new DemoAPIClient();
