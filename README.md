# 🧬 TheraGenome 3D Viewer

A professional **Three.js-based healthcare AI application** for visualizing 3D molecular/organ models with real-time toxicity assessment visualization.

## 📋 Overview

TheraGenome is a sophisticated 3D viewer designed for healthcare AI applications that need to visually represent drug toxicity predictions. Perfect for **Meshy AI-generated organ models**, the viewer provides:

- **Multi-Organ Support** - Switch between organs (heart, liver, kidneys, lungs, full body)
- **Interactive 3D Model Visualization** - Smooth rotation, zoom, and pan controls  
- **Toxicity-Based Visual Feedback** - Red for toxic effects, green for safe effects
- **Real-Time Animations** - Pulse effects and smooth color transitions
- **Organ Information Display** - Name, description, and metadata for each model
- **Responsive Design** - Works seamlessly on different screen sizes
- **Clean, Modular Architecture** - Well-organized, commented code

## 🎯 Key Features

### 1. **Meshy Organ Model Support**
- Load GLB models directly from Meshy AI
- Organ selector dropdown and quick-access buttons
- Automatic centering and scaling
- Support for complex anatomical models

### 2. **Multi-Organ Switching**
- 5 pre-configured organ models (expand as needed)
- Quick access buttons: 👤 Full Body, ❤️ Heart, 🫘 Liver, 🫘 Kidneys, 🫁 Lungs
- Dropdown selector for all available organs
- Smooth transitions between models

### 3. **Interactive Controls**
- **Orbit Controls** for intuitive 3D navigation
- Mouse rotate, scroll zoom, right-click pan
- Smooth damping for professional feel

### 4. **Toxicity Visualization**

| State | Visual Effect | Use Case |
|-------|---------------|----------|
| **High (Toxic)** | 🔴 Red color + Emissive glow + Pulse animation | Drug shows toxic effects |
| **Low (Safe)** | 🟢 Green color + No glow + Normal scale | Drug is safe |
| **Reset** | Original colors and state | Return to baseline |

### 5. **Organ Information**
- Display organ name with icon
- Show description and relevant metadata
- Tag system for classification

## 📁 Project Structure

```
3D Components/
├── index.html                          # Main HTML container
├── integration.html                    # Advanced integration demo
├── js/
│   ├── theragenome-viewer.js          # Core viewer with organ support
│   ├── config.js                      # Configuration file
│   └── integration-examples.js        # Code examples
├── models/
│   ├── human_body.glb                 # Complete human anatomy
│   ├── heart.glb                      # Heart model
│   ├── liver.glb                      # Liver model
│   ├── kidneys.glb                    # Kidneys model
│   └── lungs.glb                      # Lungs model
└── README.md                          # This file
```

## 🚀 Getting Started with Meshy Models

### Step 1: Generate Models on Meshy

1. Go to [Meshy AI](https://www.meshy.ai/)
2. Create projects for each organ:
   - Human Body Anatomy
   - Heart
   - Liver  
   - Kidneys
   - Lungs
3. Generate models with good textures
4. Download as **GLB format**

### Step 2: Organize Your Models

1. Download each GLB file from Meshy
2. Rename them to match the organ database:
   ```
   human_body.glb
   heart.glb
   liver.glb
   kidneys.glb
   lungs.glb
   ```
3. Place all files in the `models/` folder

**Example Meshy export naming pattern:**
```
Meshy_AI_Full_Body_Anatomy_Mod_0408202932_texture.glb
    ↓ Rename to
human_body.glb
```

### Step 3: Open in Browser

```bash
cd "3D Components"
python -m http.server 8000
# Open: http://localhost:8000
```

### Step 4: Test the Viewer

1. **Organ Selector**: Choose organ from dropdown
2. **Quick Buttons**: Click organ buttons to switch instantly
3. **Toxicity Testing**: 
   - 🔴 Click "High (Toxic)" to see red effect
   - 🟢 Click "Low (Safe)" to see green effect
   - Click "Reset" to return to normal
4. **Interact**: Drag to rotate, scroll to zoom

## 💻 JavaScript API

### Switching Organs

```javascript
// Switch to a specific organ
window.switchOrgan('heart');      // Heart
window.switchOrgan('liver');      // Liver
window.switchOrgan('kidneys');    // Kidneys
window.switchOrgan('lungs');      // Lungs
window.switchOrgan('human_body'); // Full body anatomy
```

### Update Toxicity

```javascript
// Set toxicity level (updates current organ display)
window.updateModel('high');   // Red + glow + pulse
window.updateModel('low');    // Green + normal
window.updateModel('reset');  // Original state
```

### Access Viewer State

```javascript
// Get internal state for debugging
const state = window.TheraGenomeViewer.getState();
const currentOrgan = window.TheraGenomeViewer.getCurrentOrgan();
const model = window.TheraGenomeViewer.getModel();
```

## 🎨 Customization Guide

### Add More Organs

Edit `js/theragenome-viewer.js` - `ORGAN_DATABASE` section:

```javascript
const ORGAN_DATABASE = {
    brain: {
        name: 'Brain',
        path: '/models/brain.glb',
        description: 'Neurological model for CNS toxicity',
        icon: '🧠',
        tags: ['neurological', 'organ', 'cns'],
    },
    // ... add more organs
};
```

Then add a quick-access button in `index.html`:
```html
<button class="btn btn-reset btn-small" onclick="window.switchOrgan('brain')">
    🧠 Brain
</button>
```

### Change Organ Naming Convention

If your Meshy exports use different names:

```javascript
const ORGAN_DATABASE = {
    heart: {
        name: 'Heart',
        path: '/models/Meshy_AI_Heart_Mod_0408202932_texture.glb', // Your actual path
        // ... rest of config
    },
};
```

### Customize Colors

Edit in `theragenome-viewer.js`:

```javascript
// High toxicity (red)
const toxicColor = new THREE.Color(0xff3333);

// Low toxicity (green)  
const safeColor = new THREE.Color(0x33ff33);
```

### Adjust Animation Speeds

```javascript
// Pulse speed (0.01 = slow, 0.05 = fast)
ViewerState.pulseSpeed = 0.02;

// Pulse range
if (ViewerState.pulseScale >= 1.15) { // Max pulse
if (ViewerState.pulseScale <= 0.90) { // Min pulse
```

## 🔧 Technical Details

### Supported Model Formats
- ✅ GLB (Binary GLTF) - Recommended, fastest
- ✅ GLTF (with embedded textures)

### Browser Compatibility
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Performance Guidelines
- Target: 60 FPS
- Recommended model size: < 10MB
- Memory usage: 50-200MB varies with model

## 🐛 Troubleshooting

### Model Not Loading

**Problem:** Shows "Failed to load model"

**Solutions:**
1. Verify file exists: `models/organ_name.glb`
2. Check filename matches database exactly
3. Ensure GLB is properly exported from Meshy
4. Check browser console for CORS errors
5. Use HTTP server (not file://)

```bash
# Test with Python server
python -m http.server 8000
```

### Organ Selector Empty

**Problem:** Dropdown has no organs

**Solutions:**
1. Ensure `setupOrganSelector()` runs at startup
2. Check DOM has element: `<select id="organSelector">`
3. Verify ORGAN_DATABASE is defined
4. Check browser console for errors

### Model Doesn't Switch

**Problem:** Clicking organs doesn't change model

**Solutions:**
1. Check all organ files (*.glb) are in `models/` folder
2. Verify filenames match ORGAN_DATABASE paths exactly
3. Check browser console for loading errors
4. Try loading a single model first

### Poor Performance

**Problem:** Laggy or stuttering

**Solutions:**
1. Reduce model polygon count in Meshy settings
2. Use lower resolution textures
3. Close other browser tabs
4. Check system GPU usage

## 📊 Meshy Export Tips

**For Best Results:**

1. **Quality Settings**: Use "High" quality in Meshy
2. **Texture Size**: 2048x2048 is good balance
3. **File Format**: Always export as GLB
4. **Name Convention**: Use descriptive organ names
5. **Testing**: Test smaller models first

**Meshy Export Checklist:**
- ✅ Format: GLB
- ✅ Texture included
- ✅ Single file (not split files)
- ✅ File size < 20MB
- ✅ Descriptive filename

## 🔐 Security Notes

- Script only loads from `/models/` folder
- No external data transmission
- Safe material manipulation
- Validated organ switching

## 📈 Advanced Features

### Multi-organ Comparison
See `integration.html` for side-by-side organ comparison

### AI Integration
See `js/integration-examples.js` for connecting to AI backend

### Batch Processing
See code examples for testing multiple organs

## 🎓 Resources

- [Meshy AI Documentation](https://www.meshy.ai/docs)
- [Three.js Documentation](https://threejs.org/docs/)
- [Three.js Examples](https://threejs.org/examples/)
- [GLB/GLTF Format Guide](https://docs.microsoft.com/en-us/windows/mixed-reality/develop/javascript/exporting-gltf)

---

**TheraGenome** - Healthcare AI visualization with Meshy organ models 🧬❤️

