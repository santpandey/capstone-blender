# 📖 User Guide - 3D Model Viewer

## Quick Start

When you generate a 3D asset, you can now **download and view it in full 3D** with just one click!

## Step-by-Step Guide

### 1. Generate Your 3D Asset

1. Open `front_end/index.html` in your browser
2. Enter a description (e.g., "Create a red cube")
3. Click **"🚀 Generate 3D Asset"**
4. Wait for the generation to complete (~10-20 seconds)

### 2. Preview in Main Window

Once completed, you'll see:
- ✅ Status: "3D asset generated successfully!"
- 🖼️ An embedded 3D preview of your model
- 🔘 A green button: **"📥 Download & View in 3D"**

### 3. Download & View

Click the **"📥 Download & View in 3D"** button:

**What happens:**
1. 📥 The GLB file downloads to your Downloads folder
2. 🌐 A new browser tab opens automatically
3. 🎨 The 3D viewer loads with your model
4. 🔄 Model starts auto-rotating for easy viewing

## 🎮 Using the 3D Viewer

### Mouse Controls

| Action | How To |
|--------|--------|
| **Rotate** | Left-click + drag |
| **Pan (Move)** | Right-click + drag |
| **Zoom** | Scroll wheel up/down |
| **Reset View** | Double-click anywhere |

### Touch Controls (Mobile/Tablet)

| Action | How To |
|--------|--------|
| **Rotate** | Single finger drag |
| **Pan** | Two finger drag |
| **Zoom** | Pinch in/out |

### Buttons

The viewer has 4 control buttons:

1. **📥 Download GLB** - Download the model again
2. **🔄 Reset Camera** - Return to default view
3. **🔁 Toggle Rotation** - Start/stop auto-rotation
4. **ℹ️ Model Info** - Show file details

### Keyboard Shortcuts

Press these keys for quick actions:

- `R` - Reset camera
- `D` - Download model
- `Space` - Toggle auto-rotation

## 🎯 Viewer Features

### Auto-Rotation
- **Default:** Enabled (model spins slowly)
- **Toggle:** Click "🔁" button or press Space
- **Best for:** Showcasing the model to others

### Model Information Panel

Click **"ℹ️ Model Info"** to see:
- File name (with job ID)
- Format (GLTF 2.0 Binary)
- Generation timestamp

### AR Mode (Mobile Only)

On compatible mobile devices:
- Look for the AR icon in the viewer
- Click to view model in your real-world space
- Point camera at flat surface
- Place and scale the 3D model

## 💡 Tips & Tricks

### Best Viewing Experience

✅ **Use Chrome or Edge** for best performance
✅ **Full screen** - Press F11 for immersive viewing
✅ **Good lighting** - Models look better with proper shadows
✅ **Zoom in** - Get close to see fine details

### Sharing Models

📤 **Method 1:** Share the downloaded GLB file
- File is in your Downloads folder
- Recipients can drag-drop into any GLB viewer

📤 **Method 2:** Take screenshots
- Rotate to best angle
- Use browser's screenshot tool (Ctrl+Shift+S in Chrome)
- Share the image

### Comparing Models

Want to compare multiple generated models?
1. Generate first model → Download & View
2. Keep viewer tab open
3. Go back to main window
4. Generate second model → Download & View
5. Now you have 2 tabs with different models!

## 🔧 Troubleshooting

### New Tab Doesn't Open

**Problem:** Browser blocks popups
**Solution:** 
- Allow popups for localhost (or your domain)
- Look for popup blocker icon in address bar
- Click and select "Always allow"

### Model Doesn't Load

**Problem:** Blank screen or error message
**Solution:**
- Check if GLB file downloaded successfully
- Try refreshing the viewer tab
- Check browser console (F12) for errors

### Download Doesn't Start

**Problem:** No file in Downloads folder
**Solution:**
- Check browser download permissions
- Look in browser's Downloads section (Ctrl+J)
- Verify backend is running

### Viewer Shows "Loading..." Forever

**Problem:** Model never appears
**Solution:**
- Ensure Blender exported GLB successfully
- Check `generated_models/` folder has the .glb file
- Verify backend `/download/{job_id}` endpoint works

## 📱 Mobile Experience

### iOS Safari
- ✅ Full 3D viewer support
- ✅ AR mode available (iOS 12+)
- ✅ Touch controls optimized

### Android Chrome
- ✅ Full 3D viewer support
- ✅ AR mode via ARCore
- ✅ Hardware acceleration enabled

## 🎨 Viewing Different Asset Types

### Simple Objects (Cubes, Spheres)
- Quick to load and render
- Great for testing
- Easy to manipulate

### Complex Models (Multi-object scenes)
- May take 2-3 seconds to load
- Use zoom to see details
- Reset camera if view is off

### Colored/Textured Models
- Materials render automatically
- Colors visible in Material Preview
- Shadows enhance realism

## 🚀 Advanced Features

### For Developers

The viewer URL accepts parameters:
```
viewer.html?model=/download/job_123&jobId=job_123
```

You can also use it standalone:
1. Open `viewer.html` directly
2. It will accept model data via postMessage
3. Or use URL parameters as shown above

### For Power Users

- **Direct file viewing:** Drag-drop GLB files into viewer (future feature)
- **Export screenshots:** Right-click → Save image
- **Inspect in DevTools:** F12 to see model structure
- **Performance stats:** Available in console logs

## 📊 What You're Viewing

### GLTF 2.0 Format
Your models are in industry-standard GLTF 2.0 format:
- **GLB** = Binary version (single file, smaller)
- **Compatible** with Blender, Unity, Unreal, Three.js
- **Web-optimized** for fast loading
- **Future-proof** format supported everywhere

### Model Structure
Each GLB contains:
- 🔷 Geometry (mesh data)
- 🎨 Materials (colors, textures)
- 💡 Lighting data (baked)
- 📐 Scene hierarchy
- 🎬 Animations (if any)

## ✅ Quality Checklist

After viewing your model, check:
- [ ] Model looks correct (shape, size)
- [ ] Colors match your prompt
- [ ] No missing parts or errors
- [ ] Rotates smoothly
- [ ] Downloads successfully

## 🎉 You're All Set!

Now you can:
- ✨ Generate 3D assets from text
- 👀 View them in full interactive 3D
- 💾 Download as industry-standard GLB
- 📱 View in AR on mobile
- 🔄 Iterate and improve your prompts

**Enjoy creating amazing 3D assets!** 🚀

---

## Quick Reference Card

```
┌─────────────────────────────────────┐
│     QUICK REFERENCE CARD            │
├─────────────────────────────────────┤
│ MOUSE CONTROLS                      │
│  • Left drag    → Rotate            │
│  • Right drag   → Pan               │
│  • Scroll       → Zoom              │
│  • Double-click → Reset             │
├─────────────────────────────────────┤
│ KEYBOARD SHORTCUTS                  │
│  • R      → Reset camera            │
│  • D      → Download                │
│  • Space  → Toggle rotation         │
├─────────────────────────────────────┤
│ BUTTONS                             │
│  • 📥 → Download GLB                │
│  • 🔄 → Reset Camera                │
│  • 🔁 → Toggle Rotation             │
│  • ℹ️ → Model Info                  │
└─────────────────────────────────────┘
```

**Need help?** Check `FRONTEND_VIEWER_ENHANCEMENT.md` for technical details.
