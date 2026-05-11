/**
 * TheraGenome AI — Chatbot Controller
 * Handles chatbot queries, responses, and chat history
 */

class ChatbotController {
    constructor() {
        this.chatHistory = [];
        this.isLoading = false;
        this.currentMode = localStorage.getItem('chatbotMode') || 'doctor';
        this.init();
    }

    /**
     * Initialize the chatbot
     */
    init() {
        this.setupEventListeners();
        this.restoreSavedMode();
        console.log('Chatbot initialized');
    }

    /**
     * Setup event listeners for chatbot interface
     */
    setupEventListeners() {
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const modeSelect = document.getElementById('chatbotModeSelect');

        console.log('Setting up event listeners...');
        console.log('chatInput:', chatInput);
        console.log('sendButton:', sendButton);
        console.log('modeSelect:', modeSelect);

        // Send button click
        if (sendButton) {
            sendButton.addEventListener('click', () => {
                console.log('Send button clicked!');
                this.handleSendMessage();
            });
            console.log('Send button listener attached');
        } else {
            console.error('Send button not found!');
        }

        // Enter key in input
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !this.isLoading) {
                    this.handleSendMessage();
                }
            });
            console.log('Chat input listener attached');
        } else {
            console.error('Chat input not found!');
        }

        // Mode selector change
        if (modeSelect) {
            modeSelect.addEventListener('change', (e) => {
                this.currentMode = e.target.value;
                localStorage.setItem('chatbotMode', e.target.value);
                console.log(`Chatbot mode switched to: ${this.currentMode}`);
            });
            console.log('Mode selector listener attached');
        } else {
            console.error('Mode selector not found!');
        }
    }

    /**
     * Restore saved mode from localStorage
     */
    restoreSavedMode() {
        const modeSelect = document.getElementById('chatbotModeSelect');
        if (modeSelect) {
            modeSelect.value = this.currentMode;
        }
    }

    /**
     * Handle sending a message
     */
    async handleSendMessage() {
        console.log('handleSendMessage called');
        
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();

        console.log('Message:', message);
        console.log('Is loading:', this.isLoading);

        if (!message) {
            console.warn('Message is empty');
            return;
        }

        if (this.isLoading) {
            console.warn('Already processing a message');
            return;
        }

        // Clear input
        chatInput.value = '';

        // Add user message to chat
        this.addUserMessage(message);

        // Send to backend
        console.log('Sending query to backend...');
        await this.sendQueryToBackend(message);
    }

    /**
     * Add a user message to the chat history
     */
    addUserMessage(message) {
        const chatHistory = document.getElementById('chatHistory');

        // Hide welcome message on first message
        const welcome = chatHistory.querySelector('.chat-welcome');
        if (welcome) {
            welcome.style.display = 'none';
        }

        // Create user message element
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message user-message';
        messageEl.innerHTML = `
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(message)}</div>
                <div class="message-time">${this.getCurrentTime()}</div>
            </div>
        `;

        chatHistory.appendChild(messageEl);
        this.scrollChatToBottom();

        // Store in history
        this.chatHistory.push({
            type: 'user',
            content: message,
            timestamp: new Date(),
            mode: this.currentMode
        });
    }

    /**
     * Send query to backend API
     */
    async sendQueryToBackend(userInput) {
        console.log('sendQueryToBackend called with:', userInput);
        
        const chatLoading = document.getElementById('chatLoading');
        const sendButton = document.getElementById('sendButton');

        // Show loading state
        this.isLoading = true;
        if (chatLoading) {
            chatLoading.classList.remove('hidden');
            console.log('Loading indicator shown');
        } else {
            console.error('Chat loading element not found!');
        }
        
        if (sendButton) {
            sendButton.disabled = true;
            console.log('Send button disabled');
        }

        try {
            const requestBody = {
                input: userInput,
                mode: this.currentMode,
                context: {
                    user_input: userInput,  // ✅ Send user input for drug name extraction
                    patient_allergies: [],  // ✅ Support for allergy detection
                    user_role: this.currentMode === 'doctor' ? 'doctor' : 'patient'
                },
                scope: 'full'
            };
            
            const apiUrl = 'http://localhost:8000/api/v1/chatbot/query';
            console.log('Sending request to:', apiUrl);
            console.log('Request body:', JSON.stringify(requestBody));
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            console.log('Response received:', response.status, response.statusText);
            console.log('Response headers:', {
                contentType: response.headers.get('content-type'),
                contentLength: response.headers.get('content-length')
            });

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                    console.error('Error response JSON:', errorData);
                } catch (e) {
                    console.error('Could not parse error response as JSON');
                    errorData = { detail: `HTTP ${response.status}` };
                }
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ Chatbot response parsed successfully:', result);

            // Add bot response to chat
            this.addBotMessage(result);

        } catch (error) {
            console.error('❌ Error sending query:', error);
            console.error('Error type:', error.constructor.name);
            console.error('Error message:', error.message);
            console.error('Full error:', error);
            this.addErrorMessage(error.message || 'Failed to process your question. Please try again.');
        } finally {
            // Hide loading state
            this.isLoading = false;
            if (chatLoading) {
                chatLoading.classList.add('hidden');
            }
            if (sendButton) {
                sendButton.disabled = false;
            }
            console.log('Request completed');
        }
    }

    /**
     * Add a bot response message to chat
     */
    addBotMessage(response) {
        const chatHistory = document.getElementById('chatHistory');

        // Create bot message container
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message bot-message';

        // Extract key information from response
        const template = response.template || 'UNKNOWN';
        const intent = response.intent || 'unknown';
        const variables = response.variables || {};
        const explanation = response.explanation || {};
        const metadata = response.metadata || {};

        // Build response HTML based on mode
        const responseHTML = this.buildResponseHTML(template, variables, explanation, intent, this.currentMode);

        messageEl.innerHTML = `
            <div class="message-content">
                <div class="response-wrapper">
                    <div class="response-header">
                        <span class="template-badge">${this.sanitize(template)}</span>
                        <span class="intent-label">${this.sanitize(intent)}</span>
                    </div>
                    ${responseHTML}
                </div>
                <div class="message-time">${this.getCurrentTime()}</div>
            </div>
        `;

        chatHistory.appendChild(messageEl);
        this.scrollChatToBottom();

        // Store in history
        this.chatHistory.push({
            type: 'bot',
            content: response,
            timestamp: new Date(),
            template: template,
            intent: intent
        });

        // Optionally speak the response in patient mode
        if (this.currentMode === 'patient' && typeof voiceService !== 'undefined') {
            this.speakResponse(template, variables);
        }
    }

    /**
     * Build response HTML based on template and mode
     */
    buildResponseHTML(template, variables, explanation, intent, mode) {
        let html = '';

        // Common fields
        const drugName = variables.drug_name || 'N/A';
        const riskLevel = variables.risk_level || 'N/A';
        const confidence = variables.confidence_score || 'N/A';
        
        // Handle domain-specific intents
        if (intent === 'input_genetic_data') {
            return this.formatGeneticResponse(variables, explanation, mode);
        } else if (intent === 'input_infection_data') {
            return this.formatInfectionResponse(variables, explanation, mode);
        } else if (intent === 'drug_analysis') {
            return this.formatDrugResponse(template, variables, explanation, mode);
        } else if (intent === 'compare_drugs') {
            return this.formatComparisonResponse(variables, explanation, mode);
        }

        // Build content based on template
        if (template === 'SAFE_TO_USE') {
            html += `
                <div class="response-safe">
                    <div class="status-icon">✅</div>
                    <p><strong>${this.escapeHtml(drugName)}</strong> is safe to use for this patient.</p>
                    ${mode === 'doctor' ? `<p class="small-text">No contraindications detected. Risk level: <strong>${this.escapeHtml(riskLevel)}</strong></p>` : ''}
                </div>
            `;
        } else if (template === 'DRUG_USE_WITH_CAUTION') {
            html += `
                <div class="response-caution">
                    <div class="status-icon">⚠️</div>
                    <p><strong>${this.escapeHtml(drugName)}</strong> can be used with caution.</p>
                    ${mode === 'doctor' ? `<p class="small-text">Some minor interactions detected. Risk level: <strong>${this.escapeHtml(riskLevel)}</strong></p>` : ''}
                </div>
            `;
        } else if (template === 'DRUG_NOT_RECOMMENDED') {
            html += `
                <div class="response-danger">
                    <div class="status-icon">❌</div>
                    <p><strong>${this.escapeHtml(drugName)}</strong> is not recommended for this patient.</p>
                    ${mode === 'doctor' ? `<p class="small-text">Significant contraindications present. Risk level: <strong>${this.escapeHtml(riskLevel)}</strong></p>` : ''}
                </div>
            `;
        } else if (template === 'COMPARISON_RESULT') {
            html += `
                <div class="response-comparison">
                    <div class="status-icon">⚖️</div>
                    <p>Drug comparison analysis completed.</p>
                    ${mode === 'doctor' ? `<p class="small-text">Multiple drugs evaluated. Confidence: <strong>${this.escapeHtml(confidence)}</strong></p>` : ''}
                </div>
            `;
        } else if (template === 'REQUIRE_MORE_DATA') {
            html += `
                <div class="response-info">
                    <div class="status-icon">ℹ️</div>
                    <p>I need more information to provide a complete analysis.</p>
                    <p class="small-text">Please provide patient genetic data, existing medications, or allergies.</p>
                </div>
            `;
        } else if (template === 'INSUFFICIENT_CONTEXT') {
            html += `
                <div class="response-info">
                    <div class="status-icon">❓</div>
                    <p>Insufficient context to answer your question.</p>
                    <p class="small-text">Please provide more details about the patient or specific concern.</p>
                </div>
            `;
        } else if (template === 'GENERAL_RESPONSE') {
            // Handle general responses from the backend
            const summary = explanation.summary || explanation.description || variables.summary || 'Analysis complete.';
            html += `
                <div class="response-generic">
                    <p class="response-text">${this.escapeHtml(String(summary))}</p>
                </div>
            `;
        } else {
            // Generic fallback for unknown templates
            html += `
                <div class="response-generic">
                    <p>Template: <strong>${this.sanitize(template)}</strong></p>
                    <p>Intent: <strong>${this.sanitize(intent)}</strong></p>
                </div>
            `;
        }

        // Add explanation if in doctor mode
        if (mode === 'doctor' && explanation && Object.keys(explanation).length > 0) {
            const reasonDetails = explanation.reason_details || {};
            
            // Handle reason_details when it's an array
            if (Array.isArray(reasonDetails) && reasonDetails.length > 0) {
                html += '<div class="explanation-section doctor-only">';
                html += '<h4>Analysis Details:</h4>';
                html += '<ul>';
                reasonDetails.forEach(detail => {
                    if (typeof detail === 'object' && detail !== null) {
                        const code = detail.code || detail.type || 'Detail';
                        const description = detail.description || detail.message || '';
                        const severity = detail.severity || 'info';
                        html += `<li><strong>${this.sanitize(code)}</strong> (${severity}): ${this.escapeHtml(description)}</li>`;
                    } else {
                        html += `<li>${this.escapeHtml(String(detail))}</li>`;
                    }
                });
                html += '</ul></div>';
            } 
            // Handle reason_details when it's an object
            else if (!Array.isArray(reasonDetails) && Object.keys(reasonDetails).length > 0) {
                html += '<div class="explanation-section doctor-only">';
                html += '<h4>Clinical Details:</h4>';
                html += '<ul>';
                for (const [key, value] of Object.entries(reasonDetails)) {
                    // Safely convert values to strings, handling nested objects
                    let displayValue = '';
                    if (value === null || value === undefined) {
                        displayValue = 'N/A';
                    } else if (typeof value === 'object') {
                        try {
                            displayValue = JSON.stringify(value, null, 2);
                        } catch (e) {
                            displayValue = String(value) !== '[object Object]' ? String(value) : 'Complex data structure';
                        }
                    } else {
                        displayValue = String(value);
                    }
                    // Only add if we have actual content
                    if (displayValue) {
                        html += `<li><strong>${this.sanitize(key)}:</strong> ${this.escapeHtml(displayValue)}</li>`;
                    }
                }
                html += '</ul></div>';
            }
        }

        return html;
    }

    /**
     * Add an error message to chat
     */
    addErrorMessage(errorText) {
        const chatHistory = document.getElementById('chatHistory');

        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message error-message';
        messageEl.innerHTML = `
            <div class="message-content">
                <div class="error-box">
                    <span class="error-icon">❌</span>
                    <p>${this.escapeHtml(errorText)}</p>
                </div>
                <div class="message-time">${this.getCurrentTime()}</div>
            </div>
        `;

        chatHistory.appendChild(messageEl);
        this.scrollChatToBottom();
    }

    /**
     * Format genetic variant analysis response
     */
    formatGeneticResponse(variables, explanation, mode) {
        const metabolizerStatus = variables.metabolizer_status || variables.patient_metabolizer_status || 'Unknown';
        const variants = variables.variants_detected || [];
        const interactions = variables.gene_drug_interactions || [];
        const riskLevel = variables.overall_genetic_risk || variables.risk_level || 'Unknown';

        let html = `
            <div class="response-genetic">
                <div class="status-icon">🧬</div>
                <p><strong>Genetic Analysis Complete</strong></p>
                <p class="small-text">Metabolizer Status: <strong>${this.escapeHtml(metabolizerStatus)}</strong></p>
                <p class="small-text">Overall Genetic Risk: <strong>${this.escapeHtml(riskLevel)}</strong></p>
        `;

        if (mode === 'doctor' && variants.length > 0) {
            html += '<div class="genetic-variants"><h5>Variants Detected:</h5><ul>';
            variants.slice(0, 5).forEach(v => {
                html += `<li><strong>${this.escapeHtml(v.gene)}</strong>: ${this.escapeHtml(v.variant)} (${this.escapeHtml(v.pathogenicity)})</li>`;
            });
            html += '</ul></div>';
        }

        if (mode === 'doctor' && interactions.length > 0) {
            html += '<div class="drug-interactions"><h5>Gene-Drug Interactions:</h5><ul>';
            interactions.slice(0, 3).forEach(i => {
                html += `<li><strong>${this.escapeHtml(i.drug)}</strong> (${this.escapeHtml(i.gene)}): ${this.escapeHtml(i.recommendation)}</li>`;
            });
            html += '</ul></div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Format infection/antibiotic resistance response
     */
    formatInfectionResponse(variables, explanation, mode) {
        const pathogen = variables.pathogen_identified || 'Unknown pathogen';
        const susceptibility = variables.susceptibility_profile || {};
        const markers = variables.resistance_markers || [];
        const recommended = variables.recommended_antibiotics || [];
        const avoid = variables.avoid_antibiotics || [];
        const riskLevel = variables.overall_resistance_risk || 'Unknown';

        let html = `
            <div class="response-infection">
                <div class="status-icon">🦠</div>
                <p><strong>Infection Analysis Complete</strong></p>
                <p class="small-text">Pathogen: <strong>${this.escapeHtml(pathogen)}</strong></p>
                <p class="small-text">Resistance Risk: <strong>${this.escapeHtml(riskLevel)}</strong></p>
        `;

        if (recommended.length > 0) {
            html += '<div class="recommended-meds"><h5>✅ Recommended Antibiotics:</h5><ul>';
            recommended.slice(0, 5).forEach(ab => {
                html += `<li>${this.escapeHtml(ab)}</li>`;
            });
            html += '</ul></div>';
        }

        if (avoid.length > 0) {
            html += '<div class="avoid-meds"><h5>❌ Antibiotics to Avoid:</h5><ul>';
            avoid.slice(0, 3).forEach(ab => {
                html += `<li>${this.escapeHtml(ab)}</li>`;
            });
            html += '</ul></div>';
        }

        if (mode === 'doctor' && markers.length > 0) {
            html += '<div class="resistance-markers"><h5>Resistance Markers:</h5><ul>';
            markers.slice(0, 4).forEach(m => {
                html += `<li><strong>${this.escapeHtml(m.gene)}</strong>: ${this.escapeHtml(m.mechanism)} (${Math.round(m.confidence * 100)}%)</li>`;
            });
            html += '</ul></div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Format drug toxicity/safety response
     */
    formatDrugResponse(template, variables, explanation, mode) {
        const drugName = variables.drug_name || 'N/A';
        
        // Backend sends risk_level, not overall_toxicity_risk
        let toxicityRisk = variables.risk_level || variables.overall_toxicity_risk || 'Unknown';
        
        // Extract toxicity flags from explanation if not in variables
        let toxicityFlags = variables.toxicity_flags || [];
        if (!toxicityFlags.length && explanation && explanation.modules && explanation.modules.toxicity_analysis) {
            toxicityFlags = explanation.modules.toxicity_analysis.toxicity_flags || [];
        }
        
        let interactions = variables.drug_interactions || [];
        if (!interactions.length && explanation && explanation.modules && explanation.modules.toxicity_analysis) {
            interactions = explanation.modules.toxicity_analysis.drug_interactions || [];
        }
        
        let contraindications = variables.contraindications || [];
        if (!contraindications.length && explanation && explanation.modules && explanation.modules.toxicity_analysis) {
            contraindications = explanation.modules.toxicity_analysis.contraindications || [];
        }
        
        const therapeuticIndex = variables.therapeutic_index || (explanation && explanation.modules && explanation.modules.toxicity_analysis && explanation.modules.toxicity_analysis.therapeutic_index) || 0;

        let html = `
            <div class="response-drug-safety">
                <div class="status-icon">💊</div>
                <p><strong>${this.escapeHtml(drugName)}</strong></p>
                <p class="small-text">Toxicity Risk: <strong class="risk-${this.escapeHtml(String(toxicityRisk).toLowerCase())}">${this.escapeHtml(String(toxicityRisk))}</strong></p>
        `;

        if (contraindications.length > 0) {
            html += '<div class="contraindications"><h5>⚠️ Contraindications:</h5><ul>';
            contraindications.slice(0, 3).forEach(c => {
                html += `<li>${this.escapeHtml(String(c))}</li>`;
            });
            html += '</ul></div>';
        }

        if (mode === 'doctor' && toxicityFlags.length > 0) {
            html += '<div class="toxicity-details"><h5>Toxicity Flags:</h5><ul>';
            toxicityFlags.slice(0, 3).forEach(f => {
                const organ = typeof f === 'string' ? f : (f.organ_system || '');
                const severity = typeof f === 'object' ? (f.severity || '') : '';
                const desc = typeof f === 'object' ? (f.description || '') : '';
                html += `<li><strong>${this.escapeHtml(organ)}</strong> ${severity ? `(${this.escapeHtml(severity)})` : ''}: ${this.escapeHtml(desc)}</li>`;
            });
            html += '</ul></div>';
        }

        if (mode === 'doctor' && interactions.length > 0) {
            html += '<div class="drug-interactions"><h5>Drug Interactions:</h5><ul>';
            interactions.slice(0, 3).forEach(i => {
                const drugA = i.drug_a || '';
                const drugB = i.drug_b || '';
                const recommendation = i.recommendation || '';
                html += `<li><strong>${this.escapeHtml(drugA)}</strong> + <strong>${this.escapeHtml(drugB)}</strong>: ${this.escapeHtml(recommendation)}</li>`;
            });
            html += '</ul></div>';
        }

        if (mode === 'doctor' && therapeuticIndex > 0) {
            html += `<p class="small-text">Therapeutic Index: <strong>${Number(therapeuticIndex).toFixed(2)}</strong></p>`;
        }

        html += '</div>';
        return html;
    }

    /**
     * Format drug comparison response
     */
    formatComparisonResponse(variables, explanation, mode) {
        const drugs = variables.drugs_compared || [];
        const comparison = variables.comparison_details || {};

        let html = `
            <div class="response-comparison">
                <div class="status-icon">⚖️</div>
                <p><strong>Drug Comparison Analysis</strong></p>
        `;

        if (drugs.length > 0) {
            html += '<div class="comparison-table"><h5>Drugs Compared:</h5><ul>';
            drugs.forEach(drug => {
                html += `<li><strong>${this.escapeHtml(drug)}</strong></li>`;
            });
            html += '</ul></div>';
        }

        if (mode === 'doctor' && Object.keys(comparison).length > 0) {
            html += '<div class="comparison-details"><h5>Comparison Details:</h5><ul>';
            for (const [key, value] of Object.entries(comparison).slice(0, 5)) {
                html += `<li><strong>${this.sanitize(key)}:</strong> ${this.escapeHtml(String(value))}</li>`;
            }
            html += '</ul></div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Speak the response using Text-to-Speech
     */
    speakResponse(template, variables) {
        if (typeof voiceService === 'undefined') {
            console.warn('Voice service not available');
            return;
        }

        try {
            const drugName = variables.drug_name || 'the medication';
            let textToSpeak = '';

            if (template === 'SAFE_TO_USE') {
                textToSpeak = `${drugName} is safe to use for this patient.`;
            } else if (template === 'DRUG_USE_WITH_CAUTION') {
                textToSpeak = `${drugName} can be used with caution. Please review the contraindications.`;
            } else if (template === 'DRUG_NOT_RECOMMENDED') {
                textToSpeak = `${drugName} is not recommended for this patient due to significant contraindications.`;
            } else if (template === 'COMPARISON_RESULT') {
                textToSpeak = 'Drug comparison analysis completed. Please review the results.';
            }

            if (textToSpeak) {
                voiceService.speak(textToSpeak);
            }
        } catch (error) {
            console.error('Error speaking response:', error);
        }
    }

    /**
     * Scroll chat to bottom
     */
    scrollChatToBottom() {
        const chatHistory = document.getElementById('chatHistory');
        if (chatHistory) {
            setTimeout(() => {
                chatHistory.scrollTop = chatHistory.scrollHeight;
            }, 100);
        }
    }

    /**
     * Get current time formatted
     */
    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    }

    /**
     * Escape HTML special characters
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    /**
     * Sanitize text for display
     */
    sanitize(text) {
        return this.escapeHtml(text).replace(/_/g, ' ');
    }

    /**
     * Clear chat history
     */
    clearHistory() {
        this.chatHistory = [];
        const chatHistory = document.getElementById('chatHistory');
        if (chatHistory) {
            chatHistory.innerHTML = `
                <div class="chat-welcome">
                    <h3>Welcome to TheraGenome AI Chatbot</h3>
                    <p>Ask me anything about drug interactions, safety, and clinical decisions.</p>
                </div>
            `;
        }
    }

    /**
     * Export chat history
     */
    exportHistory() {
        const timestamp = new Date().toISOString();
        const exportData = {
            timestamp,
            mode: this.currentMode,
            conversations: this.chatHistory
        };
        return JSON.stringify(exportData, null, 2);
    }
}

// Initialize chatbot when DOM is ready
console.log('Chatbot controller script loaded');

function initializeChatbot() {
    console.log('Initializing ChatbotController...');
    
    // Check if required elements exist
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    
    if (!chatInput || !sendButton) {
        console.error('Required chat elements not found. Retrying...');
        setTimeout(initializeChatbot, 100);
        return;
    }
    
    console.log('Chat elements found, creating ChatbotController instance');
    window.chatbotController = new ChatbotController();
    console.log('✅ Chatbot controller initialized successfully!');
}

// Try to initialize immediately if DOM is ready
if (document.readyState === 'loading') {
    console.log('DOM still loading, waiting for DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', initializeChatbot);
} else {
    console.log('DOM already loaded, initializing immediately');
    initializeChatbot();
}
