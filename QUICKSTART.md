# 🚀 Quick Start Guide

Get TheraGenome running in minutes!

## Prerequisites

- A modern web browser (Chrome, Firefox, Safari, Edge)
- A GLB/GLTF 3D model file
- Optional: A local HTTP server (for testing)

## Step 1: Get a 3D Model

Choose one of these options:

### Option A: Download a Free Model
1. Visit [Sketchfab](https://sketchfab.com)
2. Search for "organ", "body", or "molecule"
3. Filter for downloadable GLB format
4. Download the model

**Recommended Models:**
- Human body anatomy
- Individual organs (heart, brain, liver)
- DNA helix
- Protein structures

### Option B: Use Your Own Model
- Export from Blender, 3D Max, Maya as GLB
- Ensure it's in GLB format (not GLTF with separate files)

### Option C: Test Mode (No Model)
- The viewer will show an error message
- Perfect for testing the UI and controls

## Step 2: Place Model

1. Save your GLB file as `body.glb`
2. Place it in the `models/` folder
3. Folder structure should look like:
   ```
   3D Components/
   └── models/
       └── body.glb
   ```

## Step 3: Run Locally

### Option A: Using Python (Recommended)
```bash
cd "3D Components"
python -m http.server 8000
```

Then open: `http://localhost:8000`

### Option B: Using Node.js
```bash
cd "3D Components"
npx http-server
```

Then open: `http://localhost:8080`

### Option C: Direct Browser
- On Windows: Double-click `index.html` to open in default browser
- Note: Some features may not work (CORS restrictions)

## Step 4: Test the Viewer

1. Browser opens and loads the viewer
2. Click buttons to test:
   - 🔴 **High (Toxic)** - Model turns red with pulse
   - 🟢 **Low (Safe)** - Model turns green
   - **Reset** - Returns to original color

3. Interact with model:
   - **Rotate**: Click and drag
   - **Zoom**: Scroll wheel
   - **Pan**: Right-click and drag

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Black screen | No model loaded - check file path |
| Model doesn't rotate | Check your mouse/trackpad |
| Colors not changing | File may not be in models/ folder |
| CORS error | Use HTTP server (not file://) |

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [integration-examples.js](js/integration-examples.js) for API usage
- Customize colors and animations in [theragenome-viewer.js](js/theragenome-viewer.js)

## Common Customizations

### Change Model Path
Edit `theragenome-viewer.js`:
```javascript
loadModel('/models/your-model.glb');
```

### Adjust Colors
Edit in `theragenome-viewer.js`:
```javascript
const toxicColor = new THREE.Color(0xff3333);  // Red
const safeColor = new THREE.Color(0x33ff33);   // Green
```

### Increase Glow Intensity
```javascript
child.material.emissiveIntensity = 1.0; // Higher = more glow
```

## Demo Commands

Open browser console (F12) and try:

```javascript
// High toxicity
window.updateModel('high');

// Low toxicity
window.updateModel('low');

// Reset
window.updateModel('reset');

// Get viewer state
window.TheraGenomeViewer.getState();
```

## API Quick Reference

```javascript
// Main function
window.updateModel(toxicity)
  // toxicity: 'high', 'low', or 'reset'

// Get internal state
window.TheraGenomeViewer.getState()
window.TheraGenomeViewer.getScene()
window.TheraGenomeViewer.getModel()
window.TheraGenomeViewer.getCamera()
```

## Performance Tips

- Use models < 10MB for smooth performance
- Close other browser tabs
- Use Chrome for best performance
- Enable GPU acceleration in browser settings

## Next: Integration

Once the viewer runs successfully:

1. Connect to your AI backend
2. Call `window.updateModel()` with AI predictions
3. See [integration-examples.js](js/integration-examples.js) for code

Enjoy! 🧬
