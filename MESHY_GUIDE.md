# 🎨 Using Meshy AI Models with TheraGenome

Quick guide to generate, export, and integrate Meshy organ models into your TheraGenome viewer.

## 📋 Quick Overview

1. Generate organs on Meshy AI
2. Download as GLB format
3. Place in `models/` folder
4. Rename to match organ database
5. Open viewer and enjoy!

## 🚀 Step-by-Step Guide

### Step 1: Generate Models on Meshy AI

1. **Create Meshy Account**
   - Go to [meshy.ai](https://www.meshy.ai)
   - Sign up for free or paid plan
   - Select "Text to 3D" or "Image to 3D"

2. **Generate Each Organ**

   For each organ you want, enter a prompt like:

   ```
   Full human body anatomy model, high quality, detailed, medical, textured, photorealistic
   ```

   **Organ Prompts:**
   - **Human Body**: "Complete human body anatomy, all organs visible, medical textured model, side view"
   - **Heart**: "Detailed human heart anatomy, textured, medical quality, realistic colors"
   - **Liver**: "Human liver organ, anatomically accurate, textured, medical visualization"
   - **Kidneys**: "Human kidneys pair, anatomically correct, textured, medical quality"
   - **Lungs**: "Human lungs anatomy, detailed bronchi, textured, medical quality"

3. **Generation Settings**
   - Quality: **High**
   - Texture: **Enable**
   - Resolution: **High**
   - Wait for generation to complete (5-15 minutes)

### Step 2: Download from Meshy

1. Once generation completes, click **"Download"**
2. Select **GLB format** (most important!)
3. Choose high-resolution texture option
4. Save to your computer

**Important:** Always download as **GLB**, not GLTF or OBJ

### Step 3: Organize Files

Create folder structure:
```
3D Components/
└── models/
    ├── human_body.glb          ← Export 1
    ├── heart.glb               ← Export 2
    ├── liver.glb               ← Export 3
    ├── kidneys.glb             ← Export 4
    └── lungs.glb               ← Export 5
```

**Renaming Example:**
```
Meshy Export Name:     Meshy_AI_Full_Body_Anatomy_Mod_0408202932_texture.glb
↓ Rename to:           human_body.glb
```

### Step 4: Test the Viewer

```bash
cd "3D Components"
python -m http.server 8000
```

Open: `http://localhost:8000`

### Step 5: Switch Organs and Test Toxicity

- 👤 Click **Full Body** button
- ❤️ Click **Heart** button  
- 🫘 Click **Liver** button
- 🫘 Click **Kidneys** button
- 🫁 Click **Lungs** button

Test toxicity colors:
- 🔴 High (Toxic) - Model turns red
- 🟢 Low (Safe) - Model turns green

## 📊 File Naming Reference

Use these exact filenames:

| Button | Filename | Database Key |
|--------|----------|--------------|
| 👤 Full Body | `human_body.glb` | `human_body` |
| ❤️ Heart | `heart.glb` | `heart` |
| 🫘 Liver | `liver.glb` | `liver` |
| 🫘 Kidneys | `kidneys.glb` | `kidneys` |
| 🫁 Lungs | `lungs.glb` | `lungs` |

## 🎯 Pro Tips

### Tip 1: Better Prompts for Medical Models
```
"Detailed human [ORGAN NAME] anatomy, high quality, 3D medical model, 
textured, realistic, professional medical visualization, clean background, 
accurate anatomical proportions"
```

### Tip 2: Consistent Styling
Use similar prompts for all organs to get consistent style and quality

### Tip 3: Texture Optimization
- High: Best quality but larger file (10-20MB)
- Medium: Good balance (5-10MB)
- Low: Smaller files (1-5MB)

For local testing, Medium is fine. Use High for production.

### Tip 4: Multiple Versions
Generate multiple versions and choose the best:
```
organs/
├── heart_v1.glb
├── heart_v2.glb
├── heart_v3.glb  ← Choose this one
└── (keep as heart.glb)
```

## 🔧 If Models Don't Match The Buttons

### Add Custom Organs

Edit `js/theragenome-viewer.js`:

```javascript
const ORGAN_DATABASE = {
    // ... existing organs ...
    
    brain: {
        name: 'Brain',
        path: '/models/brain.glb',
        description: 'Brain model for neurological toxicity',
        icon: '🧠',
        tags: ['neurological', 'organ', 'cns'],
    },
    
    pancreas: {
        name: 'Pancreas',
        path: '/models/pancreas.glb',
        description: 'Pancreatic model for metabolic effects',
        icon: '🫙',
        tags: ['metabolic', 'organ', 'endocrine'],
    },
};
```

Then add buttons in `index.html`:

```html
<button class="btn btn-reset btn-small" onclick="window.switchOrgan('brain')">
    🧠 Brain
</button>
<button class="btn btn-reset btn-small" onclick="window.switchOrgan('pancreas')">
    🫙 Pancreas
</button>
```

### Change File Locations

If you want to organize files differently:

```javascript
// Use subdirectories
liver: {
    path: '/models/organs/liver.glb',
    // ...
},

// Or different naming
heart: {
    path: '/models/Meshy_Heart_Export_v2.glb',
    // ...
},
```

## 🐛 Troubleshooting

### Issue: GLB file too large

**Problem:** File > 50MB causing slow loading

**Solution:**
- Re-export from Meshy with lower texture quality
- Use online tool to compress GLB
- Test loading time locally with Python server

```bash
python -m http.server 8000
```

### Issue: Model orientation wrong

**Problem:** Model appears upside down or rotated

**Solution:**
- Regenerate on Meshy with better prompt
- Add to prompt: "correct vertical orientation"
- Or adjust in code:

```javascript
// In switchOrgan() after loading:
if (organKey === 'heart') {
    ViewerState.model.rotation.x = Math.PI / 2;
}
```

### Issue: Texture quality poor

**Problem:** Exported model looks pixelated

**Solution:**
- Export again with "High" texture setting
- Check file size (should be 5-20MB for good quality)
- Try different image-to-3D mode on Meshy

### Issue: Colors not visible

**Problem:** Red/green effects don't show well

**Solution:**
- Choose bright, solid colored models on Meshy
- Avoid models with complex textures
- Regenerate with prompt: "solid color, no patterns"

## 🎨 Meshy Settings for Best Results

**Recommended Settings:**

| Setting | Value | Reason |
|---------|-------|--------|
| Quality | High | Better detail for medical models |
| Texture | On | Essential for realism |
| Format | GLB | Single file, fastest |
| Resolution | 2K-4K | Good balance |
| Color | Varied | Better visualization of toxicity |

## 📈 Organizing Multiple Versions

Keep originals and tested versions:

```
models/
├── Generated/
│   ├── Heart_v1.glb
│   ├── Heart_v2.glb
│   ├── Heart_v3.glb
│   └── heart_final.glb
├── heart.glb           ← Used by viewer
└── liver.glb           ← Used by viewer
```

## 🎓 Next Steps

1. **Generate on Meshy**: Create 5 organ models
2. **Download**: Save all as GLB
3. **Organize**: Rename and place in `models/` folder
4. **Test**: Open viewer and switch organs
5. **Integrate**: Connect to your AI backend

## 📞 Getting Help

- Check model files exist in correct location
- Verify filenames match database exactly
- Check browser console (F12) for errors
- Test one organ first before adding more
- See main README.md for full documentation

## 💡 Pro Workflow

```bash
# 1. Create models directory
mkdir models

# 2. Download from Meshy (5-6 files)
# Place in models/ folder

# 3. Check files
ls models/

# 4. Run viewer
python -m http.server 8000

# 5. Open browser
# http://localhost:8000

# 6. Test each organ button
# 7. Test toxicity colors
# 8. Ready for production!
```

---

**Happy modeling!** 🧬 Your TheraGenome viewer is ready for Meshy organs!
