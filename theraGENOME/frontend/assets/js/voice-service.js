/**
 * TheraGENOME AI — Voice Service
 * Handles speech-to-text and text-to-speech functionality
 */

class VoiceService {
    constructor() {
        // Speech Recognition Setup
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = SpeechRecognition ? new SpeechRecognition() : null;
        
        // Speech Synthesis Setup
        this.synthesis = window.speechSynthesis;
        
        // State
        this.isListening = false;
        this.isSpeaking = false;
        this.currentLanguage = 'en-US';
        this.listeners = {};
        
        // Language config
        this.languages = {
            'en-US': { name: 'English', flag: '🇬🇧', region: 'en-US' },
            'hi-IN': { name: 'Hindi', flag: '🇮🇳', region: 'hi-IN' },
            'ta-IN': { name: 'Tamil', flag: '🇮🇳', region: 'ta-IN' },
            'te-IN': { name: 'Telugu', flag: '🇮🇳', region: 'te-IN' },
            'kn-IN': { name: 'Kannada', flag: '🇮🇳', region: 'kn-IN' }
        };
        
        // Initialize recognition settings
        if (this.recognition) {
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = this.currentLanguage;
            this.setupRecognitionListeners();
        }
    }

    /**
     * Set the current language for voice input and output
     */
    setLanguage(languageCode) {
        if (!this.languages[languageCode]) {
            console.error(`Language ${languageCode} not supported`);
            return false;
        }

        this.currentLanguage = languageCode;

        // Update recognition language
        if (this.recognition) {
            this.recognition.lang = languageCode;
        }

        // Emit language change event
        this.emit('language-changed', languageCode);
        localStorage.setItem('preferredVoiceLanguage', languageCode);
        
        return true;
    }

    /**
     * Get current language
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    /**
     * Get all supported languages
     */
    getSupportedLanguages() {
        return this.languages;
    }

    /**
     * Get language name by code
     */
    getLanguageName(languageCode) {
        return this.languages[languageCode]?.name || 'Unknown';
    }

    /**
     * Setup Speech Recognition event listeners
     */
    setupRecognitionListeners() {
        this.recognition.onstart = () => {
            this.isListening = true;
            this.emit('listening-start');
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.emit('listening-error', event.error);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.emit('listening-end');
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;

                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            if (interimTranscript) {
                this.emit('transcript-interim', interimTranscript);
            }

            if (finalTranscript) {
                this.emit('transcript-final', finalTranscript.trim());
            }
        };
    }

    /**
     * Start listening for voice input
     */
    startListening() {
        if (!this.recognition) {
            this.emit('listening-error', 'Speech Recognition not supported in your browser');
            return false;
        }

        if (this.isListening) return false;

        try {
            this.recognition.start();
            return true;
        } catch (error) {
            console.error('Error starting recognition:', error);
            this.emit('listening-error', error.message);
            return false;
        }
    }

    /**
     * Stop listening for voice input
     */
    stopListening() {
        if (!this.recognition || !this.isListening) return false;

        try {
            this.recognition.stop();
            return true;
        } catch (error) {
            console.error('Error stopping recognition:', error);
            return false;
        }
    }

    /**
     * Abort listening
     */
    abortListening() {
        if (this.recognition && this.isListening) {
            this.recognition.abort();
        }
    }

    /**
     * Check if speech recognition is supported
     */
    isRecognitionSupported() {
        return this.recognition !== null;
    }

    /**
     * Speak text using Text-to-Speech
     */
    speak(text, options = {}) {
        // Cancel any ongoing speech
        if (this.isSpeaking) {
            this.synthesis.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(text);
        
        // Configure utterance
        utterance.rate = options.rate || 1.0; // 0.1 to 10
        utterance.pitch = options.pitch || 1.0; // 0 to 2
        utterance.volume = options.volume || 1.0; // 0 to 1
        utterance.lang = options.lang || this.currentLanguage;

        // Select voice if available
        if (options.voiceIndex !== undefined) {
            const voices = this.synthesis.getVoices();
            if (voices[options.voiceIndex]) {
                utterance.voice = voices[options.voiceIndex];
            }
        }

        // Event listeners
        utterance.onstart = () => {
            this.isSpeaking = true;
            this.emit('speaking-start');
        };

        utterance.onend = () => {
            this.isSpeaking = false;
            this.emit('speaking-end');
        };

        utterance.onerror = (event) => {
            this.isSpeaking = false;
            console.error('Speech synthesis error:', event.error);
            this.emit('speaking-error', event.error);
        };

        utterance.onpause = () => {
            this.emit('speaking-pause');
        };

        utterance.onresume = () => {
            this.emit('speaking-resume');
        };

        this.synthesis.speak(utterance);
        return true;
    }

    /**
     * Pause speech
     */
    pauseSpeech() {
        if (this.isSpeaking) {
            this.synthesis.pause();
            return true;
        }
        return false;
    }

    /**
     * Resume speech
     */
    resumeSpeech() {
        if (this.synthesis.paused) {
            this.synthesis.resume();
            return true;
        }
        return false;
    }

    /**
     * Stop speech
     */
    stopSpeech() {
        if (this.isSpeaking || this.synthesis.paused) {
            this.synthesis.cancel();
            this.isSpeaking = false;
            this.emit('speaking-stop');
            return true;
        }
        return false;
    }

    /**
     * Check if speech synthesis is supported
     */
    isSynthesisSupported() {
        return this.synthesis !== null;
    }

    /**
     * Get available voices
     */
    getVoices() {
        return this.synthesis.getVoices();
    }

    /**
     * Event emitter methods
     */
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Get speech recognition status
     */
    getStatus() {
        return {
            isListening: this.isListening,
            isSpeaking: this.isSpeaking,
            currentLanguage: this.currentLanguage,
            recognitionSupported: this.isRecognitionSupported(),
            synthesisSupported: this.isSynthesisSupported()
        };
    }
}

// Create global instance
const voiceService = new VoiceService();
