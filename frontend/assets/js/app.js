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

        // Voice Input Controls
        this.setupVoiceInputControls();

        // Voice Output Controls
        this.setupVoiceOutputControls();

        // Voice Service Events
        this.setupVoiceServiceListeners();
    }

    /**
     * Setup voice input controls (Speech-to-Text)
     */
    setupVoiceInputControls() {
        const startBtn = document.getElementById('startListeningBtn');
        const stopBtn = document.getElementById('stopListeningBtn');
        const languageSelect = document.getElementById('voiceLanguage');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startListening());
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopListening());
        }

        // Language selector
        if (languageSelect) {
            // Load saved preference
            const savedLanguage = localStorage.getItem('preferredVoiceLanguage') || 'en-US';
            languageSelect.value = savedLanguage;
            voiceService.setLanguage(savedLanguage);

            // Handle language change
            languageSelect.addEventListener('change', (e) => {
                this.handleLanguageChange(e.target.value);
            });
        }

        // Check if speech recognition is supported
        if (!voiceService.isRecognitionSupported()) {
            if (startBtn) {
                startBtn.disabled = true;
                startBtn.title = 'Speech Recognition not supported in your browser';
            }
        }
    }

    /**
     * Handle voice language change
     */
    handleLanguageChange(languageCode) {
        voiceService.setLanguage(languageCode);
        localStorage.setItem('preferredVoiceLanguage', languageCode);
        const languageName = voiceService.getLanguageName(languageCode);
        this.updateVoiceInputStatus('success', `✅ Language changed to ${languageName}`);
        setTimeout(() => this.updateVoiceInputStatus('ready', ''), 2000);
    }

    /**
     * Setup voice output controls (Text-to-Speech)
     */
    setupVoiceOutputControls() {
        const speakBtn = document.getElementById('speakResultBtn');
        const pauseBtn = document.getElementById('pauseSpeakBtn');
        const resumeBtn = document.getElementById('resumeSpeakBtn');
        const stopBtn = document.getElementById('stopSpeakBtn');

        if (speakBtn) {
            speakBtn.addEventListener('click', () => this.speakResult());
        }

        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.pauseSpeech());
        }

        if (resumeBtn) {
            resumeBtn.addEventListener('click', () => this.resumeSpeech());
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopSpeech());
        }

        // Check if speech synthesis is supported
        if (!voiceService.isSynthesisSupported()) {
            if (speakBtn) {
                speakBtn.disabled = true;
                speakBtn.title = 'Speech Synthesis not supported in your browser';
            }
        }
    }

    /**
     * Setup voice service event listeners
     */
    setupVoiceServiceListeners() {
        // Speech Recognition Events
        voiceService.on('listening-start', () => {
            this.updateVoiceInputStatus('listening', '🎤 Listening...');
        });

        voiceService.on('listening-end', () => {
            this.updateVoiceInputStatus('ready', '');
        });

        voiceService.on('listening-error', (error) => {
            this.updateVoiceInputStatus('error', `❌ Error: ${error}`);
        });

        voiceService.on('transcript-interim', (text) => {
            document.getElementById('interimTranscript').textContent = text;
        });

        voiceService.on('transcript-final', (text) => {
            document.getElementById('finalTranscript').textContent = text;
            this.handleVoiceCommand(text);
        });

        // Language Change Event
        voiceService.on('language-changed', (language) => {
            const languageName = voiceService.getLanguageName(language);
            console.log(`Voice language changed to: ${languageName}`);
        });

        // Speech Synthesis Events
        voiceService.on('speaking-start', () => {
            this.updateVoiceOutputStatus('speaking', '🔊 Speaking...');
            this.showVoiceOutputControls();
        });

        voiceService.on('speaking-end', () => {
            this.updateVoiceOutputStatus('ready', '✅ Speech completed');
            setTimeout(() => this.hideVoiceOutputControls(), 1000);
        });

        voiceService.on('speaking-error', (error) => {
            this.updateVoiceOutputStatus('error', `❌ Error: ${error}`);
        });

        voiceService.on('speaking-pause', () => {
            this.updateVoiceOutputStatus('paused', '⏸ Speech paused');
        });

        voiceService.on('speaking-resume', () => {
            this.updateVoiceOutputStatus('speaking', '🔊 Speaking...');
        });

        voiceService.on('speaking-stop', () => {
            this.updateVoiceOutputStatus('ready', '⏹ Speech stopped');
            setTimeout(() => this.hideVoiceOutputControls(), 1000);
        });
    }

    /**
     * Start listening for voice input
     */
    startListening() {
        const startBtn = document.getElementById('startListeningBtn');
        const stopBtn = document.getElementById('stopListeningBtn');

        if (voiceService.startListening()) {
            if (startBtn) startBtn.classList.add('hidden');
            if (stopBtn) stopBtn.classList.remove('hidden');
            this.showVoiceTranscript();
        } else {
            this.updateVoiceInputStatus('error', '❌ Failed to start listening');
        }
    }

    /**
     * Stop listening for voice input
     */
    stopListening() {
        const startBtn = document.getElementById('startListeningBtn');
        const stopBtn = document.getElementById('stopListeningBtn');

        if (voiceService.stopListening()) {
            if (startBtn) startBtn.classList.remove('hidden');
            if (stopBtn) stopBtn.classList.add('hidden');
        }
    }

    /**
     * Handle voice command (process recognized text)
     */
    handleVoiceCommand(text) {
        const lowerText = text.toLowerCase().trim();
        const currentLang = voiceService.getCurrentLanguage();

        // Voice command patterns for different languages
        const commandPatterns = {
            'en-US': {
                safe: ['safe', 'first case', 'first'],
                risk: ['risk', 'high risk', 'second case', 'second'],
                compare: ['compar', 'third case', 'third', 'compare drugs']
            },
            'hi-IN': {
                safe: ['सुरक्षित', 'पहला', 'पहली', 'safe'],
                risk: ['जोखिम', 'उच्च जोखिम', 'दूसरा', 'second'],
                compare: ['तुलना', 'तीसरा', 'compare']
            },
            'ta-IN': {
                safe: ['பாதுகாப்பு', 'முதல்', 'safe'],
                risk: ['அபாயம்', 'உচ்ச அபாயம்', 'இரண்டு', 'second'],
                compare: ['ஒப்பிடு', 'மூன்றாவது', 'compare']
            },
            'te-IN': {
                safe: ['సురక్ష', 'మొదటి', 'safe'],
                risk: ['ఖతరం', 'అధిక ఖతరం', 'రెండు', 'second'],
                compare: ['సరిపోల్చు', 'మూడవ', 'compare']
            },
            'kn-IN': {
                safe: ['ಸುರಕ್ಷಿತ', 'ಮೊದಲ', 'safe'],
                risk: ['ಅಪಾಯ', 'ಹೆಚ್ಚಿನ ಅಪಾಯ', 'ಎರಡು', 'second'],
                compare: ['ಹೋಲಿಸು', 'ಮೂರನೆಯ', 'compare']
            }
        };

        // Get patterns for current language
        const patterns = commandPatterns[currentLang] || commandPatterns['en-US'];

        // Check which scenario matches
        let command = null;
        if (patterns.safe.some(pattern => lowerText.includes(pattern))) {
            command = 'safe_case';
        } else if (patterns.risk.some(pattern => lowerText.includes(pattern))) {
            command = 'high_risk_case';
        } else if (patterns.compare.some(pattern => lowerText.includes(pattern))) {
            command = 'comparison_case';
        }

        if (command) {
            this.simulateButtonClick(command);
        } else {
            const langName = voiceService.getLanguageName(currentLang);
            this.updateVoiceInputStatus('error', `⚠️ Command not recognized in ${langName}`);
        }
    }

    /**
     * Simulate button click for voice commands
     */
    simulateButtonClick(caseId) {
        const button = document.querySelector(`[data-case-id="${caseId}"]`);
        if (button) {
            button.click();
            this.updateVoiceInputStatus('success', `✅ Started: ${button.querySelector('.label').textContent}`);
        }
    }

    /**
     * Speak the current result
     */
    speakResult() {
        if (!this.currentResult) {
            this.updateVoiceOutputStatus('error', '❌ No result to speak');
            return;
        }

        const result = this.currentResult;
        const innerResult = result.result || {};
        const currentLang = voiceService.getCurrentLanguage();

        // Build speech text in selected language
        let speechText = this.buildSpeechText(result, currentLang);

        if (speechText) {
            voiceService.speak(speechText, {
                rate: 0.9,
                pitch: 1.0,
                volume: 1.0,
                lang: currentLang
            });
        }
    }

    /**
     * Build speech text in the selected language
     */
    buildSpeechText(result, language) {
        const innerResult = result.result || {};
        const variables = innerResult.variables || {};
        const explanation = innerResult.explanation || {};

        // Translations for different languages
        const translations = {
            'en-US': {
                scenario: 'Scenario',
                template: 'Template',
                riskLevel: 'Risk Level',
                drug: 'Drug',
                confidence: 'Confidence',
                clinical: 'Clinical Rationale'
            },
            'hi-IN': {
                scenario: 'परिदृश्य',
                template: 'टेम्पलेट',
                riskLevel: 'जोखिम स्तर',
                drug: 'दवा',
                confidence: 'आत्मविश्वास',
                clinical: 'नैदानिक कारण'
            },
            'ta-IN': {
                scenario: 'சூழ்நிலை',
                template: 'டெம்பிளேட்',
                riskLevel: 'ஆபத்து அளவு',
                drug: 'மருந்து',
                confidence: 'நம்பக்கூறியக்கம்',
                clinical: 'மருத்துவ காரணம்'
            },
            'te-IN': {
                scenario: 'దృశ్యం',
                template: 'టెంప్లేట్',
                riskLevel: 'ఖతరం స్థితి',
                drug: 'ఔషధం',
                confidence: 'విశ్వాసం',
                clinical: 'నిర్దిష్ట కారణం'
            },
            'kn-IN': {
                scenario: 'ಸನ್ನಿವೇಶ',
                template: 'ಟೆಂಪ್ಲೇಟ್',
                riskLevel: 'ಅಪಾಯ ಮಟ್ಟ',
                drug: 'ಔಷಧ',
                confidence: 'ವಿಶ್ವಾಸ',
                clinical: 'ಚಿಕಿತ್ಸಕ ಕಾರಣ'
            }
        };

        const t = translations[language] || translations['en-US'];
        let speechText = '';

        speechText += `${t.scenario}: ${result.scenario.name}. `;
        speechText += `${t.template}: ${innerResult.template || 'Unknown'}. `;

        if (variables.risk_level) {
            speechText += `${t.riskLevel}: ${variables.risk_level}. `;
        }
        if (variables.drug_name) {
            speechText += `${t.drug}: ${variables.drug_name}. `;
        }
        if (variables.confidence) {
            speechText += `${t.confidence}: ${variables.confidence}. `;
        }

        if (explanation.clinical_rationale) {
            speechText += `${t.clinical}: ${explanation.clinical_rationale}. `;
        }

        return speechText;
    }

    /**
     * Pause speech
     */
    pauseSpeech() {
        if (voiceService.pauseSpeech()) {
            const pauseBtn = document.getElementById('pauseSpeakBtn');
            const resumeBtn = document.getElementById('resumeSpeakBtn');
            if (pauseBtn) pauseBtn.classList.add('hidden');
            if (resumeBtn) resumeBtn.classList.remove('hidden');
        }
    }

    /**
     * Resume speech
     */
    resumeSpeech() {
        if (voiceService.resumeSpeech()) {
            const pauseBtn = document.getElementById('pauseSpeakBtn');
            const resumeBtn = document.getElementById('resumeSpeakBtn');
            if (pauseBtn) pauseBtn.classList.remove('hidden');
            if (resumeBtn) resumeBtn.classList.add('hidden');
        }
    }

    /**
     * Stop speech
     */
    stopSpeech() {
        if (voiceService.stopSpeech()) {
            const pauseBtn = document.getElementById('pauseSpeakBtn');
            const resumeBtn = document.getElementById('resumeSpeakBtn');
            if (pauseBtn) pauseBtn.classList.add('hidden');
            if (resumeBtn) resumeBtn.classList.add('hidden');
        }
    }

    /**
     * Show voice transcript display
     */
    showVoiceTranscript() {
        const transcript = document.getElementById('voiceTranscript');
        if (transcript) {
            transcript.classList.remove('hidden');
            document.getElementById('interimTranscript').textContent = '';
            document.getElementById('finalTranscript').textContent = '';
        }
    }

    /**
     * Show voice output controls
     */
    showVoiceOutputControls() {
        const controls = document.getElementById('voiceOutputControls');
        if (controls) {
            controls.classList.remove('hidden');
        }
        const pauseBtn = document.getElementById('pauseSpeakBtn');
        const resumeBtn = document.getElementById('resumeSpeakBtn');
        const stopBtn = document.getElementById('stopSpeakBtn');
        if (pauseBtn) pauseBtn.classList.remove('hidden');
        if (resumeBtn) resumeBtn.classList.add('hidden');
        if (stopBtn) stopBtn.classList.remove('hidden');
    }

    /**
     * Hide voice output controls
     */
    hideVoiceOutputControls() {
        const controls = document.getElementById('voiceOutputControls');
        if (controls && !voiceService.isSpeaking) {
            controls.classList.add('hidden');
        }
    }

    /**
     * Update voice input status display
     */
    updateVoiceInputStatus(status, message) {
        const statusEl = document.getElementById('voiceStatus');
        if (statusEl) {
            statusEl.className = `voice-status ${status}`;
            statusEl.textContent = message || '';
        }
    }

    /**
     * Update voice output status display
     */
    updateVoiceOutputStatus(status, message) {
        const statusEl = document.getElementById('speechStatus');
        if (statusEl) {
            statusEl.className = `speech-status ${status}`;
            statusEl.textContent = message || '';
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
