/**
 * TheraGenome Configuration
 * ==========================
 * Customize these settings to adjust viewer behavior
 */

const CONFIG = {
    // ====================================
    // MODEL SETTINGS
    // ====================================

    model: {
        // Path to GLB model file
        path: '/models/body.glb',

        // Auto-scale model to fit view
        autoScale: true,

        // Show model at startup
        autoLoad: true,
    },

    // ====================================
    // CAMERA SETTINGS
    // ====================================

    camera: {
        // Field of view (degrees)
        fov: 75,

        // Near clipping plane
        near: 0.1,

        // Far clipping plane
        far: 1000,

        // Initial position
        position: {
            x: 0,
            y: 0,
            z: 3,
        },
    },

    // ====================================
    // RENDERER SETTINGS
    // ====================================

    renderer: {
        // Enable anti-aliasing for smooth edges
        antialias: true,

        // Enable shadows
        shadowsEnabled: true,

        // Shadow quality (PCFShadowMap, PCFShadowShadowMap, VSMShadowMap)
        shadowType: 'PCFShadowShadowMap',

        // Target pixel ratio (1 = standard, 2 = high DPI)
        pixelRatio: 'auto', // 'auto' or number
    },

    // ====================================
    // LIGHTING SETTINGS
    // ====================================

    lighting: {
        // Ambient light
        ambient: {
            color: 0xffffff,
            intensity: 0.6,
        },

        // Directional light
        directional: {
            color: 0xffffff,
            intensity: 0.8,
            position: {
                x: 5,
                y: 5,
                z: 5,
            },
        },

        // Scene background color
        backgroundColor: 0xf5f5f5,
    },

    // ====================================
    // ORBIT CONTROLS SETTINGS
    // ====================================

    controls: {
        // Enable damping (smooth movement)
        enableDamping: true,

        // Damping factor (0-1, lower = more damping)
        dampingFactor: 0.05,

        // Enable zoom
        enableZoom: true,

        // Zoom speed
        zoomSpeed: 1.2,

        // Enable rotation
        enableRotate: true,

        // Rotation speed
        rotateSpeed: 1.0,

        // Enable pan
        enablePan: true,

        // Pan speed
        panSpeed: 1.0,

        // Auto rotate
        autoRotate: false,

        // Auto rotate speed
        autoRotateSpeed: 0,

        // Min zoom distance
        minDistance: 1,

        // Max zoom distance
        maxDistance: 10,
    },

    // ====================================
    // TOXICITY VISUALIZATION SETTINGS
    // ====================================

    toxicity: {
        // High toxicity settings
        high: {
            // Color (RGB hex)
            color: 0xff3333,

            // Color blend intensity (0-1)
            colorBlend: 0.8,

            // Emissive color
            emissiveColor: 0xff3333,

            // Emissive intensity (glow)
            emissiveIntensity: 0.5,

            // Enable pulse animation
            enablePulse: true,

            // Pulse speed (pixels/frame)
            pulseSpeed: 0.02,

            // Min scale during pulse
            pulseScaleMin: 0.95,

            // Max scale during pulse
            pulseScaleMax: 1.1,
        },

        // Low toxicity settings
        low: {
            // Color (RGB hex)
            color: 0x33ff33,

            // Color blend intensity (0-1)
            colorBlend: 0.8,

            // Emissive color
            emissiveColor: 0x000000,

            // Emissive intensity (no glow)
            emissiveIntensity: 0,

            // Keep normal scale
            scale: 1.0,
        },

        // Color transition speed (0-1, higher = faster)
        transitionSpeed: 0.8,
    },

    // ====================================
    // ANIMATION SETTINGS
    // ====================================

    animation: {
        // Target frames per second
        targetFps: 60,

        // Enable continuous rendering
        enableRenderLoop: true,

        // Animation enabled on startup
        enableOnStartup: true,
    },

    // ====================================
    // UI SETTINGS
    // ====================================

    ui: {
        // Show loading spinner
        showLoader: true,

        // Show status display
        showStatus: true,

        // Status update frequency (ms)
        statusUpdateFrequency: 100,

        // Auto hide loader after (ms)
        loaderAutoHideDelay: 5000,
    },

    // ====================================
    // PERFORMANCE SETTINGS
    // ====================================

    performance: {
        // Limit maximum frame rate
        maxFrameRate: 60,

        // Enable performance monitoring
        enableStats: false,

        // Dispose of resources on unload
        autoCleanup: true,

        // Cache materials
        cacheMaterials: true,
    },

    // ====================================
    // DEBUG SETTINGS
    // ====================================

    debug: {
        // Enable console logging
        enableLogging: true,

        // Log level ('error', 'warn', 'info', 'debug')
        logLevel: 'info',

        // Show grid helper
        showGridHelper: false,

        // Show axes helper
        showAxesHelper: false,

        // Show bounding box
        showBoundingBox: false,

        // Performance monitoring
        showStats: false,
    },
};

// ====================================
// EXPORT
// ====================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}

// Make available globally
window.TheraGenomeConfig = CONFIG;
