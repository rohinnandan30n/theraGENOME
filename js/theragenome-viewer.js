/**
 * TheraGenome 3D Viewer
 * =====================
 * A Three.js-based healthcare AI application viewer for visualizing
 * molecular/organ models with real-time toxicity assessment visualization.
 *
 * Features:
 * - Load GLB models with GLTFLoader
 * - Interactive OrbitControls
 * - Toxicity-based visual feedback (High = Red/Toxic, Low = Green/Safe)
 * - Pulse animation for toxicity states
 * - Responsive design
 * - Smooth material transitions
 */

// ====================================
// STATE MANAGEMENT
// ====================================

const ViewerState = {
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    model: null,
    container: null,
    animationFrameId: null,
    currentToxicity: 'neutral',
    pulseScale: 1,
    pulseDirection: 1,
    pulseSpeed: 0.02,
    isAnimating: false,
    currentOrgan: 'human_body', // Track current organ
    baseModelScale: 1,
    animationStarted: false,
    activeLoadRequestId: 0,
};

// ====================================
// ORGAN DATABASE (From Meshy)
// ====================================

const ORGAN_DATABASE = {
    human_body: {
        name: 'Human Body Anatomy',
        path: 'models/human_body_optimized.glb',
        description: 'Complete human anatomical model',
        icon: '👤',
        tags: ['anatomy', 'full-body', 'reference'],
    },
    heart: {
        name: 'Heart',
        path: 'models/heart_optimized.glb',
        description: 'Detailed cardiac model - critical for drug effect prediction',
        icon: '❤️',
        tags: ['cardiac', 'organ', 'vital'],
    },
    kidneys: {
        name: 'Kidneys',
        path: 'models/kidneys_optimized.glb',
        description: 'Renal model for toxicity filtration and elimination analysis',
        icon: '🫘',
        tags: ['renal', 'organ', 'filtration'],
    },
};

// Material backup for reset functionality
const MaterialBackup = {
    materials: new Map(),
};

// ====================================
// INITIALIZATION
// ====================================

/**
 * Initialize the Three.js viewer
 */
function initViewer() {
    console.log('🧬 Initializing TheraGenome Viewer...');
    
    // Get container element
    ViewerState.container = document.getElementById('three-container');
    if (!ViewerState.container) {
        console.error('❌ Container #three-container not found!');
        return;
    }

    // Get container dimensions
    const width = ViewerState.container.clientWidth;
    const height = ViewerState.container.clientHeight;

    // -------- SCENE SETUP --------
    ViewerState.scene = new THREE.Scene();
    ViewerState.scene.background = new THREE.Color(0xf5f5f5);

    // -------- CAMERA SETUP --------
    const aspectRatio = width / height;
    ViewerState.camera = new THREE.PerspectiveCamera(
        75,              // Field of view
        aspectRatio,     // Aspect ratio
        0.1,             // Near clipping plane
        1000             // Far clipping plane
    );
    ViewerState.camera.position.set(0, 0, 3);

    // -------- RENDERER SETUP --------
    ViewerState.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    ViewerState.renderer.setSize(width, height);
    ViewerState.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    ViewerState.renderer.shadowMap.enabled = false;
    ViewerState.renderer.shadowMap.type = THREE.PCFShadowShadowMap;
    ViewerState.container.appendChild(ViewerState.renderer.domElement);

    // -------- LIGHTING SETUP --------
    setupLighting();

    // -------- ORBIT CONTROLS SETUP --------
    setupOrbitControls();

    // -------- ORGAN SELECTOR SETUP --------
    setupOrganSelector();

    // -------- EVENT LISTENERS --------
    setupEventListeners();

    // Start a single render loop immediately so users don't see a static black canvas.
    if (!ViewerState.animationStarted) {
        ViewerState.animationStarted = true;
        animate();
    }

    // Render once before model is ready to show scene background/lights.
    ViewerState.renderer.render(ViewerState.scene, ViewerState.camera);

    console.log('✅ Viewer initialized');
}

/**
 * Setup lighting for the scene
 */
function setupLighting() {
    // Ambient light for general illumination
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    ViewerState.scene.add(ambientLight);

    // Directional light for shadows and depth
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 5, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    directionalLight.shadow.camera.near = 0.5;
    directionalLight.shadow.camera.far = 50;
    ViewerState.scene.add(directionalLight);

    console.log('💡 Lighting configured');
}

/**
 * Setup OrbitControls for interactive camera control
 */
function setupOrbitControls() {
    ViewerState.controls = new THREE.OrbitControls(
        ViewerState.camera,
        ViewerState.renderer.domElement
    );

    // Enable smooth interactions
    ViewerState.controls.enableDamping = true;
    ViewerState.controls.dampingFactor = 0.05;
    ViewerState.controls.enableZoom = true;
    ViewerState.controls.autoRotate = false;
    ViewerState.controls.autoRotateSpeed = 0;

    // Set reasonable interaction bounds
    ViewerState.controls.minDistance = 1;
    ViewerState.controls.maxDistance = 10;

    console.log('🎮 OrbitControls enabled');
}

/**
 * Setup organ selector dropdown
 */
function setupOrganSelector() {
    const selector = document.getElementById('organSelector');
    if (!selector) {
        console.warn('⚠️ Organ selector not found');
        return;
    }

    // Populate dropdown with organs
    Object.entries(ORGAN_DATABASE).forEach(([key, organ]) => {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = `${organ.icon} ${organ.name}`;
        selector.appendChild(option);
    });

    // Listen for organ selection
    selector.addEventListener('change', (e) => {
        if (e.target.value) {
            switchOrgan(e.target.value);
        }
    });

    console.log('📋 Organ selector ready');
}

/**
 * Setup event listeners for responsiveness
 */
function setupEventListeners() {
    window.addEventListener('resize', onWindowResize, false);
}

// ====================================
// MODEL LOADING
// ====================================

/**
 * Switch to a different organ model
 * @param {string} organKey - Key from ORGAN_DATABASE
 */
function switchOrgan(organKey) {
    if (!ORGAN_DATABASE[organKey]) {
        console.error(`❌ Unknown organ: ${organKey}`);
        return;
    }

    const organ = ORGAN_DATABASE[organKey];
    ViewerState.currentOrgan = organKey;

    console.log(`🔄 Switching to: ${organ.name}`);
    showLoader(`Loading ${organ.name}...`);

    // Remove current model
    if (ViewerState.model) {
        ViewerState.scene.remove(ViewerState.model);
        ViewerState.model = null;
        MaterialBackup.materials.clear();
    }

    // Reset toxicity
    ViewerState.currentToxicity = 'neutral';
    ViewerState.isAnimating = false;
    ViewerState.pulseScale = 1;

    // Load new model
    loadModel(organ.path, organKey);

    // Update UI
    updateOrganDisplay(organKey);
    updateOrganSelector(organKey);
}

/**
 * Update organ display information
 */
function updateOrganDisplay(organKey) {
    const organ = ORGAN_DATABASE[organKey];
    const nameDisplay = document.getElementById('organ-name');
    const infoDisplay = document.getElementById('organ-info');

    if (nameDisplay) {
        nameDisplay.textContent = `${organ.icon} ${organ.name}`;
        nameDisplay.className = 'status neutral';
    }

    if (infoDisplay) {
        infoDisplay.innerHTML = `
            <strong>${organ.description}</strong><br>
            Tags: ${organ.tags.map(tag => `<span style="display: inline-block; background: #e0e0e0; padding: 2px 8px; border-radius: 3px; margin-right: 5px; font-size: 0.75rem;">${tag}</span>`).join('')}
        `;
    }
}

/**
 * Update organ selector dropdown to current organ
 */
function updateOrganSelector(organKey) {
    const selector = document.getElementById('organSelector');
    if (selector) {
        selector.value = organKey;
    }
}

/**
 * Load GLB model from specified path
 * @param {string} modelPath - Path to the GLB model file
 * @param {string} organKey - Organ identifier
 */
function loadModel(modelPath = 'models/human_body_optimized.glb', organKey = 'human_body', isFallback = false) {
    console.log(`📦 Loading model: ${modelPath}`);
    const requestId = ++ViewerState.activeLoadRequestId;
    const loadStartedAt = performance.now();
    let timeoutHandle = null;

    const loader = new THREE.GLTFLoader();
    if (window.THREE && window.THREE.DRACOLoader) {
        const dracoLoader = new THREE.DRACOLoader();
        dracoLoader.setDecoderPath('node_modules/three/examples/js/libs/draco/');
        loader.setDRACOLoader(dracoLoader);
    }

    timeoutHandle = setTimeout(() => {
        if (requestId !== ViewerState.activeLoadRequestId) {
            return;
        }
        updateLoaderProgress('Still loading... large Meshy model can take 20-60s on first decode.');
    }, 8000);

    loader.load(
        modelPath,
        (gltf) => {
            if (requestId !== ViewerState.activeLoadRequestId) {
                return;
            }
            clearTimeout(timeoutHandle);

            // Model loaded successfully
            ViewerState.model = gltf.scene;

            // Add model to scene
            ViewerState.scene.add(ViewerState.model);

            // Center and scale the model
            centerAndScaleModel(ViewerState.model);

            // Backup original materials
            backupMaterials(ViewerState.model);

            // Hide loader
            hideLoader();

            const totalLoadMs = Math.round(performance.now() - loadStartedAt);
            console.log(`✅ ${ORGAN_DATABASE[organKey].name} loaded successfully`);
            console.log(`⏱️ Load + parse time: ${totalLoadMs} ms`);
            console.log('📊 Model details:', gltf);

        },
        (progress) => {
            if (requestId !== ViewerState.activeLoadRequestId) {
                return;
            }

            // Loading progress
            if (progress.total && progress.total > 0) {
                const percentComplete = (progress.loaded / progress.total) * 100;
                updateLoaderProgress(`Loading ${ORGAN_DATABASE[organKey].name}: ${percentComplete.toFixed(1)}%`);
                console.log(`⏳ Loading: ${percentComplete.toFixed(2)}%`);
            } else {
                const mbLoaded = (progress.loaded / (1024 * 1024)).toFixed(1);
                updateLoaderProgress(`Loading ${ORGAN_DATABASE[organKey].name}: ${mbLoaded} MB`);
                console.log(`⏳ Loading: ${mbLoaded} MB`);
            }
        },
        (error) => {
            if (requestId !== ViewerState.activeLoadRequestId) {
                return;
            }
            clearTimeout(timeoutHandle);

            // If optimized asset fails (decoder/network), try plain optimized fallback once.
            if (!isFallback) {
                let fallbackPath = null;
                if (modelPath.endsWith('_optimized.glb')) {
                    fallbackPath = modelPath.replace('_optimized.glb', '_plain.glb');
                }

                if (fallbackPath) {
                    console.warn(`⚠️ Optimized load failed, retrying with fallback: ${fallbackPath}`);
                    updateLoaderProgress('Retrying with compatibility model...');
                    loadModel(fallbackPath, organKey, true);
                    return;
                }
            }

            // Loading error
            console.error('❌ Error loading model:', error);
            showLoadingError(modelPath);
        }
    );
}

/**
 * Center and scale model to fit in view
 * @param {THREE.Group} model - The loaded model
 */
function centerAndScaleModel(model) {
    // Calculate bounding box
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    // Center the model
    model.position.sub(center);

    // Calculate scale to fit in view
    const maxDim = Math.max(size.x, size.y, size.z);
    const scale = maxDim > 0 ? 2 / maxDim : 1;
    model.scale.multiplyScalar(scale);
    ViewerState.baseModelScale = model.scale.x;

    console.log(`📐 Model scaled and centered (scale: ${scale.toFixed(2)})`);
}

/**
 * Backup original materials for reset functionality
 * @param {THREE.Group} model - The loaded model
 */
function backupMaterials(model) {
    model.traverse((child) => {
        if (child.material) {
            MaterialBackup.materials.set(
                child,
                child.material.clone()
            );
        }
    });
}

// ====================================
// TOXICITY VISUALIZATION
// ====================================

/**
 * Update model based on toxicity level
 * @param {string} toxicity - "high", "low", or "reset"
 */
function updateModel(toxicity) {
    if (!ViewerState.model) {
        console.warn('⚠️ Model not loaded yet');
        return;
    }

    console.log(`🧪 Updating model for toxicity: ${toxicity}`);
    ViewerState.currentToxicity = toxicity;

    const organ = ORGAN_DATABASE[ViewerState.currentOrgan];
    const nameDisplay = document.getElementById('organ-name');

    switch (toxicity) {
        case 'high':
            applyHighToxicity();
            if (nameDisplay) {
                nameDisplay.textContent = `⚠️ ${organ.name} - TOXIC`;
                nameDisplay.className = 'status high';
            }
            break;

        case 'low':
            applyLowToxicity();
            if (nameDisplay) {
                nameDisplay.textContent = `✅ ${organ.name} - SAFE`;
                nameDisplay.className = 'status low';
            }
            break;

        case 'reset':
            resetModel();
            if (nameDisplay) {
                nameDisplay.textContent = `${organ.icon} ${organ.name}`;
                nameDisplay.className = 'status neutral';
            }
            break;

        default:
            console.warn(`⚠️ Unknown toxicity level: ${toxicity}`);
    }
}

/**
 * Apply high toxicity visualization (Red, glow, pulse)
 */
function applyHighToxicity() {
    ViewerState.isAnimating = true;
    const toxicColor = new THREE.Color(0xff3333); // Bright red

    ViewerState.model.traverse((child) => {
        if (child.isMesh && child.material) {
            // Smoothly transition to red
            child.material.color.lerp(toxicColor, 0.8);
            child.material.emissive.copy(toxicColor);
            child.material.emissiveIntensity = 0.5;
            child.material.needsUpdate = true;
        }
    });

    console.log('🔴 High toxicity applied (Red + Glow + Pulse)');
}

/**
 * Apply low toxicity visualization (Green, no glow)
 */
function applyLowToxicity() {
    ViewerState.isAnimating = false;
    ViewerState.pulseScale = 1;
    const safeColor = new THREE.Color(0x33ff33); // Bright green

    if (ViewerState.model) {
        ViewerState.model.scale.set(
            ViewerState.baseModelScale,
            ViewerState.baseModelScale,
            ViewerState.baseModelScale
        );
    }

    ViewerState.model.traverse((child) => {
        if (child.isMesh && child.material) {
            // Smoothly transition to green
            child.material.color.lerp(safeColor, 0.8);
            child.material.emissive.setHex(0x000000); // No glow
            child.material.emissiveIntensity = 0;
            child.material.needsUpdate = true;
        }
    });

    console.log('🟢 Low toxicity applied (Green + No glow)');
}

/**
 * Reset model to original state
 */
function resetModel() {
    ViewerState.isAnimating = false;
    ViewerState.pulseScale = 1;

    if (ViewerState.model) {
        ViewerState.model.scale.set(
            ViewerState.baseModelScale,
            ViewerState.baseModelScale,
            ViewerState.baseModelScale
        );
    }

    ViewerState.model.traverse((child) => {
        if (child.material && MaterialBackup.materials.has(child)) {
            // Restore from backup
            const originalMaterial = MaterialBackup.materials.get(child);
            child.material.copy(originalMaterial);
            child.material.needsUpdate = true;
        }
    });

    console.log('↩️ Model reset to original state');
}

// ====================================
// ANIMATION & RENDERING
// ====================================

/**
 * Pulse animation for high toxicity state
 */
function updatePulseAnimation() {
    if (!ViewerState.model) {
        return;
    }

    if (!ViewerState.isAnimating || ViewerState.currentToxicity !== 'high') {
        if (ViewerState.pulseScale !== 1) {
            ViewerState.pulseScale = 1;
            ViewerState.model.scale.set(
                ViewerState.baseModelScale,
                ViewerState.baseModelScale,
                ViewerState.baseModelScale
            );
        }
        return;
    }

    // Update pulse scale
    ViewerState.pulseScale += ViewerState.pulseDirection * ViewerState.pulseSpeed;

    // Reverse direction at min/max
    if (ViewerState.pulseScale >= 1.1) {
        ViewerState.pulseDirection = -1;
    } else if (ViewerState.pulseScale <= 0.95) {
        ViewerState.pulseDirection = 1;
    }

    // Apply scale
    const scaleValue = ViewerState.baseModelScale * ViewerState.pulseScale;
    ViewerState.model.scale.set(scaleValue, scaleValue, scaleValue);
}

/**
 * Main animation loop
 */
function animate() {
    ViewerState.animationFrameId = requestAnimationFrame(animate);

    if (!ViewerState.renderer || !ViewerState.scene || !ViewerState.camera) {
        return;
    }

    // Update controls
    if (ViewerState.controls) {
        ViewerState.controls.update();
    }

    // Update pulse animation
    updatePulseAnimation();

    // Render scene
    ViewerState.renderer.render(ViewerState.scene, ViewerState.camera);
}

// ====================================
// RESPONSIVE DESIGN
// ====================================

/**
 * Handle window resize events
 */
function onWindowResize() {
    if (!ViewerState.container || !ViewerState.camera || !ViewerState.renderer) {
        return;
    }

    const width = ViewerState.container.clientWidth;
    const height = ViewerState.container.clientHeight;

    // Update camera
    ViewerState.camera.aspect = width / height;
    ViewerState.camera.updateProjectionMatrix();

    // Update renderer
    ViewerState.renderer.setSize(width, height);

    console.log(`📱 Resized to ${width}x${height}`);
}

// ====================================
// UI & UX HELPERS
// ====================================

/**
 * Hide the loading spinner
 */
function hideLoader() {
    const loader = document.querySelector('.loader');
    if (loader) {
        loader.style.transition = 'opacity 0.5s ease';
        loader.style.opacity = '0';
        loader.style.pointerEvents = 'none';
        setTimeout(() => {
            loader.style.display = 'none';
        }, 550);
    }
}

/**
 * Show loading overlay and optional message.
 * @param {string} message - Loader message
 */
function showLoader(message = 'Loading 3D Model...') {
    const loader = document.querySelector('.loader');
    if (!loader) {
        return;
    }

    loader.style.display = 'flex';
    loader.style.opacity = '1';
    loader.style.pointerEvents = 'auto';

    const text = loader.querySelector('p');
    if (text) {
        text.textContent = message;
    }
}

/**
 * Update loading text while downloading/parsing model.
 * @param {string} message - Progress message
 */
function updateLoaderProgress(message) {
    const loader = document.querySelector('.loader');
    if (!loader) {
        return;
    }

    const text = loader.querySelector('p');
    if (text) {
        text.textContent = message;
    }
}

/**
 * Show loading error message
 * @param {string} modelPath - Path that failed to load
 */
function showLoadingError(modelPath) {
    const loader = document.querySelector('.loader');
    if (loader) {
        loader.innerHTML = `
            <div style="color: #d32f2f; font-weight: bold;">
                ⚠️ Failed to load model
            </div>
            <div style="color: #999; font-size: 0.9rem; margin-top: 10px;">
                Expected at: ${modelPath}
            </div>
        `;
    }
}

/**
 * Update status display with current toxicity
 * @param {string} text - Status text
 * @param {string} className - CSS class for styling
 */
function updateStatusDisplay(text, className) {
    const statusDisplay = document.getElementById('status-display');
    if (statusDisplay) {
        statusDisplay.textContent = text;
        statusDisplay.className = `status ${className}`;
    }
}

// ====================================
// GLOBAL API EXPOSURE
// ====================================

// Expose updateModel globally for HTML buttons
window.updateModel = updateModel;

// Expose switchOrgan globally for organ switching
window.switchOrgan = switchOrgan;

// Expose viewer state for debugging
window.TheraGenomeViewer = {
    getState: () => ViewerState,
    getScene: () => ViewerState.scene,
    getModel: () => ViewerState.model,
    getCamera: () => ViewerState.camera,
    getRenderer: () => ViewerState.renderer,
    getControls: () => ViewerState.controls,
    getCurrentOrgan: () => ViewerState.currentOrgan,
};

// ====================================
// STARTUP
// ====================================

/**
 * Initialize on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Starting TheraGenome initialization...');

    if (!window.THREE || !window.THREE.GLTFLoader || !window.THREE.OrbitControls) {
        showLoadingError('Three.js libraries failed to load. Check internet/CDN access or use local library files.');
        console.error('❌ Missing Three.js dependency.');
        return;
    }

    initViewer();
    // Load default organ (human body)
    switchOrgan('human_body');
});

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
    if (ViewerState.animationFrameId) {
        cancelAnimationFrame(ViewerState.animationFrameId);
    }
    if (ViewerState.renderer) {
        ViewerState.renderer.dispose();
    }
    console.log('🛑 TheraGenome cleaned up');
});
