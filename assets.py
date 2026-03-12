"""
A-Frame Exporter - Assets Module

This module handles exporting textures and generating default assets.
"""

import bpy
import os
import shutil


def export_default_icons(assets_dir, theme_color="#ff6b6b"):
    """Export default app icons."""
    
    # 192x192 icon
    icon_192 = f'''<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">
  <rect width="192" height="192" fill="{theme_color}" rx="24"/>
  <text x="96" y="130" font-family="Arial, sans-serif" font-size="100" text-anchor="middle" fill="white">A</text>
</svg>'''
    
    # 512x512 icon
    icon_512 = f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" fill="{theme_color}" rx="64"/>
  <text x="256" y="350" font-family="Arial, sans-serif" font-size="280" text-anchor="middle" fill="white">A</text>
</svg>'''
    
    # Write icon files
    icon_192_path = os.path.join(assets_dir, "icon-192.svg")
    icon_512_path = os.path.join(assets_dir, "icon-512.svg")
    
    with open(icon_192_path, 'w', encoding='utf-8') as f:
        f.write(icon_192)
    
    with open(icon_512_path, 'w', encoding='utf-8') as f:
        f.write(icon_512)
    
    return [icon_192_path, icon_512_path]


def export_textures(context, assets_dir):
    """Export textures used in the scene."""
    
    # Collect all textures from materials
    textures = set()
    
    for obj in context.scene.objects:
        if not obj.data:
            continue
        
        # Get materials from mesh
        if hasattr(obj.data, 'materials'):
            for mat in obj.data.materials:
                if mat and mat.use_nodes:
                    # Get textures from node tree
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            textures.add(node.image)
    
    exported_textures = []
    
    for tex in textures:
        if tex.filepath:
            # Try to export the texture
            try:
                source_path = bpy.path.abspath(tex.filepath)
                if os.path.exists(source_path):
                    # Copy to assets directory
                    filename = os.path.basename(source_path)
                    dest_path = os.path.join(assets_dir, filename)
                    
                    # Avoid overwriting
                    if os.path.exists(dest_path):
                        # Generate unique name
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(dest_path):
                            dest_path = os.path.join(assets_dir, f"{base}_{counter}{ext}")
                            counter += 1
                    
                    shutil.copy2(source_path, dest_path)
                    exported_textures.append(dest_path)
            except Exception as e:
                print(f"Failed to export texture {tex.name}: {e}")
    
    return exported_textures


def get_scene_materials(context):
    """Get all unique materials used in the scene."""
    materials = set()
    
    for obj in context.scene.objects:
        if hasattr(obj.data, 'materials'):
            for mat in obj.data.materials:
                if mat:
                    materials.add(mat)
    
    return materials


def get_scene_textures(context):
    """Get all unique textures used in the scene."""
    textures = set()
    
    for mat in get_scene_materials(context):
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    textures.add(node.image)
    
    return textures


def export_gltf_intermediate(context, export_dir):
    """Export scene as GLTF for complex objects."""
    # This is a placeholder for advanced export functionality
    # Could be used for complex meshes that need GLTF conversion
    pass
