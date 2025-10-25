"""
Quick Fix Script for Blender - Run this in the current scene
to fix color visibility and check text objects

USAGE IN BLENDER:
1. Open Blender with your scene
2. Go to Scripting tab
3. Open this file or paste code
4. Click "Run Script"
"""

import bpy

print("\n" + "="*60)
print("QUICK FIX: Colors & Text Visibility")
print("="*60)

# FIX 1: Switch to Material Preview Mode
print("\n[1/4] Switching viewport to Material Preview mode...")
try:
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'  # Material Preview
                    print("✅ Viewport set to Material Preview - colors now visible!")
                    break
except Exception as e:
    print(f"❌ Could not set viewport: {e}")

# FIX 2: List all materials and their colors
print("\n[2/4] Checking materials in scene...")
for mat in bpy.data.materials:
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            color = bsdf.inputs['Base Color'].default_value
            print(f"  Material '{mat.name}': RGB({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")

# FIX 3: Check text objects
print("\n[3/4] Checking text objects...")
text_objects = [obj for obj in bpy.data.objects if obj.type == 'FONT']
if text_objects:
    for text_obj in text_objects:
        print(f"\n  Text Object: {text_obj.name}")
        print(f"    Content: '{text_obj.data.body}'")
        print(f"    Location: {text_obj.location}")
        print(f"    Size: {text_obj.data.size}")
        print(f"    Rotation: X={text_obj.rotation_euler[0]:.2f}, Y={text_obj.rotation_euler[1]:.2f}, Z={text_obj.rotation_euler[2]:.2f}")
        
        # Check if text has material
        if len(text_obj.data.materials) > 0:
            print(f"    Material: {text_obj.data.materials[0].name}")
        else:
            print(f"    Material: None ❌")
            # Try to apply brown material if available
            if 'Brown' in bpy.data.materials:
                text_obj.data.materials.append(bpy.data.materials['Brown'])
                print(f"    ✅ Applied Brown material!")
            elif 'brown' in bpy.data.materials:
                text_obj.data.materials.append(bpy.data.materials['brown'])
                print(f"    ✅ Applied brown material!")
        
        # Check modifiers
        if text_obj.modifiers:
            print(f"    Modifiers: {[mod.name for mod in text_obj.modifiers]}")
else:
    print("  ❌ No text objects found in scene!")

# FIX 4: Apply brown material to text if it has white
print("\n[4/4] Fixing text material to brown...")
brown_mat = None
if 'Brown' in bpy.data.materials:
    brown_mat = bpy.data.materials['Brown']
elif 'brown' in bpy.data.materials:
    brown_mat = bpy.data.materials['brown']

if brown_mat:
    for text_obj in text_objects:
        if len(text_obj.data.materials) > 0:
            current_mat = text_obj.data.materials[0]
            # Check if it's white material
            if 'white' in current_mat.name.lower():
                text_obj.data.materials[0] = brown_mat
                print(f"  ✅ Changed {text_obj.name} from white to brown!")
        else:
            text_obj.data.materials.append(brown_mat)
            print(f"  ✅ Applied brown material to {text_obj.name}!")
else:
    print("  ❌ No brown material found in scene!")
    print("     Creating brown material...")
    # Create brown material
    brown_mat = bpy.data.materials.new(name='Brown')
    brown_mat.use_nodes = True
    bsdf = brown_mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.6, 0.3, 0.1, 1.0)  # Brown color
    
    # Apply to all text objects
    for text_obj in text_objects:
        if len(text_obj.data.materials) == 0:
            text_obj.data.materials.append(brown_mat)
        else:
            text_obj.data.materials[0] = brown_mat
        print(f"  ✅ Applied new brown material to {text_obj.name}!")

# BONUS: Check cylinder/mug material
print("\n[BONUS] Checking cylinder/mug material...")
for obj in bpy.data.objects:
    if 'Cylinder' in obj.name:
        print(f"\n  Cylinder Object: {obj.name}")
        if len(obj.data.materials) > 0:
            mat = obj.data.materials[0]
            print(f"    Material: {mat.name}")
            if mat.use_nodes:
                bsdf = mat.node_tree.nodes.get('Principled BSDF')
                if bsdf:
                    color = bsdf.inputs['Base Color'].default_value
                    print(f"    Color: RGB({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")
                    if color[0] < 0.9 or color[1] < 0.9 or color[2] < 0.9:
                        print(f"    ⚠️ Not fully white! Should be (1.0, 1.0, 1.0)")
        else:
            print(f"    ❌ No material applied!")

print("\n" + "="*60)
print("QUICK FIX COMPLETE!")
print("="*60)
print("\nNOTE: If colors still don't show, manually press 'Z' key")
print("      in viewport and select 'Material Preview' (3rd option)")
print("="*60 + "\n")
