/**
 * TheraGenome Integration Examples
 * ================================
 *
 * This file demonstrates how to integrate TheraGenome with your AI backend
 * and use the updateModel() API for different scenarios.
 */

// ============================================
// EXAMPLE 1: Basic AI Prediction Integration
// ============================================

/**
 * Example: Process AI model prediction and update viewer
 */
async function integrateAIPrediction() {
    try {
        // Simulate calling your AI backend
        const prediction = await fetchDrugToxicityPrediction({
            drugId: 'COMPOUND_123',
            concentration: 50, // mg/ml
        });

        console.log('🤖 AI Prediction:', prediction);

        // Determine toxicity level
        const toxicityLevel = prediction.score > 0.7 ? 'high' : 'low';

        // Update viewer
        window.updateModel(toxicityLevel);

        // Display results
        displayResults(prediction);
    } catch (error) {
        console.error('Error fetching prediction:', error);
    }
}

/**
 * Mock function - Replace with your actual API call
 */
async function fetchDrugToxicityPrediction(drugParams) {
    // Simulate API delay
    await new Promise(r => setTimeout(r, 500));

    // Mock response
    return {
        drugId: drugParams.drugId,
        score: Math.random(), // 0-1 toxicity score
        confidence: 0.92,
        tissues: ['liver', 'kidney'],
        timestamp: new Date().toISOString(),
    };
}

/**
 * Display prediction results in UI
 */
function displayResults(prediction) {
    console.log('=== Prediction Results ===');
    console.log(`Drug ID: ${prediction.drugId}`);
    console.log(`Toxicity Score: ${(prediction.score * 100).toFixed(1)}%`);
    console.log(`Confidence: ${(prediction.confidence * 100).toFixed(1)}%`);
    console.log(`Affected Tissues: ${prediction.tissues.join(', ')}`);
}

// ============================================
// EXAMPLE 2: Real-time Monitoring
// ============================================

/**
 * Monitor parameters and update visualization in real-time
 */
class ToxicityMonitor {
    constructor(updateIntervalMs = 2000) {
        this.updateInterval = updateIntervalMs;
        this.isMonitoring = false;
        this.statusElement = null;
    }

    /**
     * Start real-time monitoring
     */
    startMonitoring() {
        if (this.isMonitoring) return;

        this.isMonitoring = true;
        console.log('📊 Starting toxicity monitoring...');

        this.monitoringLoop();
    }

    /**
     * Stop monitoring
     */
    stopMonitoring() {
        this.isMonitoring = false;
        console.log('⏹️ Stopped monitoring');
    }

    /**
     * Monitor loop
     */
    async monitoringLoop() {
        while (this.isMonitoring) {
            try {
                // Get current parameters
                const params = await getCurrentParameters();

                // Calculate toxicity
                const toxicity = this.calculateToxicity(params);

                // Update viewer
                window.updateModel(toxicity);

                // Update status
                this.updateStatus(params, toxicity);

            } catch (error) {
                console.error('Monitoring error:', error);
            }

            // Wait before next update
            await new Promise(r => setTimeout(r, this.updateInterval));
        }
    }

    /**
     * Calculate toxicity from parameters
     */
    calculateToxicity(params) {
        const {
            pH = 7,
            temperature = 37,
            concentration = 50,
            time = 0,
        } = params;

        // Simple toxicity calculation
        const pHDiff = Math.abs(pH - 7);
        const tempDiff = Math.abs(temperature - 37);

        let toxicityScore = (concentration / 100) * 0.5;
        toxicityScore += (pHDiff / 2) * 0.25;
        toxicityScore += (tempDiff / 10) * 0.25;

        return toxicityScore > 0.5 ? 'high' : 'low';
    }

    /**
     * Update status display
     */
    updateStatus(params, toxicity) {
        const status = document.getElementById('status-display');
        if (status) {
            const icon = toxicity === 'high' ? '⚠️' : '✅';
            status.textContent = `${icon} ${toxicity.toUpperCase()}`;
        }
    }
}

// Usage example
// const monitor = new ToxicityMonitor(2000);
// monitor.startMonitoring();

/**
 * Mock: Get current monitoring parameters
 */
async function getCurrentParameters() {
    return {
        pH: 7.2 + Math.random() * 0.5,
        temperature: 37 + Math.random() * 2,
        concentration: 40 + Math.random() * 20,
        time: Date.now(),
    };
}

// ============================================
// EXAMPLE 3: Interactive Compound Testing
// ============================================

/**
 * Test multiple compounds and compare results
 */
async function compareCompounds(compoundList) {
    console.log('🔬 Comparing compounds...');

    const results = [];

    for (const compound of compoundList) {
        const prediction = await fetchDrugToxicityPrediction({
            drugId: compound.id,
            concentration: compound.concentration,
        });

        results.push({
            name: compound.name,
            prediction,
            isSafe: prediction.score < 0.5,
        });
    }

    // Display comparison
    console.table(results.map(r => ({
        'Compound': r.name,
        'Toxicity': (r.prediction.score * 100).toFixed(1) + '%',
        'Safe': r.isSafe ? '✅' : '⚠️',
        'Confidence': (r.prediction.confidence * 100).toFixed(1) + '%',
    })));

    return results;
}

// Usage example
// const compounds = [
//   { id: 'COMP_001', name: 'Aspirin', concentration: 100 },
//   { id: 'COMP_002', name: 'Ibuprofen', concentration: 50 },
//   { id: 'COMP_003', name: 'Paracetamol', concentration: 75 },
// ];
// compareCompounds(compounds);

// ============================================
// EXAMPLE 4: Animation Sequences
// ============================================

/**
 * Play animation sequence (high -> low -> reset)
 */
async function playDemoSequence() {
    console.log('🎬 Playing demo sequence...');

    // Sequence of states
    const sequence = [
        { state: 'reset', duration: 1000, label: 'Initial State' },
        { state: 'low', duration: 2000, label: 'Safe Drug Effect' },
        { state: 'reset', duration: 1000, label: 'Back to Baseline' },
        { state: 'high', duration: 3000, label: 'Toxic Drug Effect' },
        { state: 'reset', duration: 1000, label: 'Final Reset' },
    ];

    for (const step of sequence) {
        console.log(`→ ${step.label}`);
        window.updateModel(step.state);
        await new Promise(r => setTimeout(r, step.duration));
    }

    console.log('✅ Demo sequence complete');
}

// ============================================
// EXAMPLE 5: Data Persistence
// ============================================

/**
 * Save prediction results to local storage
 */
function savePredictionResults(prediction) {
    const results = JSON.parse(localStorage.getItem('predictions') || '[]');

    results.push({
        ...prediction,
        savedAt: new Date().toISOString(),
    });

    // Keep only last 50 results
    if (results.length > 50) {
        results.shift();
    }

    localStorage.setItem('predictions', JSON.stringify(results));
    console.log(`💾 Saved prediction (total: ${results.length})`);
}

/**
 * Load prediction history
 */
function loadPredictionHistory() {
    const results = JSON.parse(localStorage.getItem('predictions') || '[]');
    console.log('📋 Prediction History:', results);
    return results;
}

/**
 * Clear all saved predictions
 */
function clearPredictionHistory() {
    localStorage.removeItem('predictions');
    console.log('🗑️ Prediction history cleared');
}

// ============================================
// EXAMPLE 6: Batch Processing
// ============================================

/**
 * Process multiple predictions in batch
 */
async function batchProcessPredictions(drugList) {
    console.log(`⚙️ Processing ${drugList.length} compounds...`);

    const batchSize = 5;
    const results = [];

    for (let i = 0; i < drugList.length; i += batchSize) {
        const batch = drugList.slice(i, i + batchSize);

        // Process batch in parallel
        const batchResults = await Promise.all(
            batch.map(drug => fetchDrugToxicityPrediction({
                drugId: drug.id,
                concentration: drug.concentration,
            }))
        );

        results.push(...batchResults);

        // Show progress
        console.log(`✓ Processed ${Math.min(i + batchSize, drugList.length)}/${drugList.length}`);
    }

    return results;
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Wait for viewer to be ready
 */
function waitForViewer() {
    return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
            if (window.updateModel && window.TheraGenomeViewer) {
                clearInterval(checkInterval);
                resolve();
            }
        }, 100);
    });
}

/**
 * Initialize examples when viewer is ready
 */
document.addEventListener('DOMContentLoaded', async () => {
    console.log('⏳ Waiting for TheraGenome viewer to be ready...');
    await waitForViewer();
    console.log('✅ TheraGenome ready!');

    // Uncomment examples to run:
    // integrateAIPrediction();
    // playDemoSequence();
    // monitor.startMonitoring();
});

// ============================================
// EXPORT FOR MODULE USE
// ============================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        integrateAIPrediction,
        ToxicityMonitor,
        compareCompounds,
        playDemoSequence,
        savePredictionResults,
        loadPredictionHistory,
        clearPredictionHistory,
        batchProcessPredictions,
        waitForViewer,
    };
}
