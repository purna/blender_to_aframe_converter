"""
A-Frame Exporter - UI Module

This module handles the Blender UI registration for the A-Frame exporter.
"""

import bpy
from bpy.types import Panel


# Panel class for export options (displayed in render properties)
class AFRAME_PT_export_panel(Panel):
    """A-Frame export options panel."""
    bl_label = "A-Frame Export"
    bl_idname = "AFRAME_PT_export_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    @classmethod
    def poll(cls, context):
        return context.scene
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Export settings
        box = layout.box()
        box.label(text="Export Settings", icon='EXPORT')
        box.prop(scene, "aframe_export_path", text="Export Path")
        box.prop(scene, "aframe_project_name", text="Project Name")
        
        # A-Frame settings
        box = layout.box()
        box.label(text="A-Frame Settings", icon='WORLD')
        box.prop(scene, "aframe_version")
        box.prop(scene, "aframe_include_environment")
        if scene.aframe_include_environment:
            box.prop(scene, "aframe_environment_preset")
        
        # Export button
        layout.separator()
        layout.operator("export_scene.aframe", icon='EXPORT', text="Export to A-Frame")


def register():
    """Register UI elements."""
    # Register the panel class
    bpy.utils.register_class(AFRAME_PT_export_panel)
    
    # Add properties to scene
    bpy.types.Scene.aframe_export_path = bpy.props.StringProperty(
        name="Export Path",
        description="Path to export the A-Frame project",
        subtype='DIR_PATH',
        default="",
    )
    
    bpy.types.Scene.aframe_project_name = bpy.props.StringProperty(
        name="Project Name",
        description="Name of the A-Frame project",
        default="aframe-project",
    )
    
    bpy.types.Scene.aframe_version = bpy.props.EnumProperty(
        name="A-Frame Version",
        description="A-Frame version to use",
        items=[
            ('1.7.1', '1.7.1', 'Latest stable 1.7.1'),
            ('1.6.0', '1.6.0', 'Version 1.6.0'),
            ('1.5.0', '1.5.0', 'Version 1.5.0'),
            ('1.4.0', '1.4.0', 'Version 1.4.0'),
        ],
        default='1.7.1',
    )
    
    bpy.types.Scene.aframe_include_environment = bpy.props.BoolProperty(
        name="Include Environment",
        description="Include A-Frame environment component",
        default=True,
    )
    
    bpy.types.Scene.aframe_environment_preset = bpy.props.EnumProperty(
        name="Environment Preset",
        description="Choose the environment preset",
        items=[
            ('none', 'None', 'No environment'),
            ('arches', 'Arches', 'Arches environment'),
            ('contact', 'Contact', 'Contact environment'),
            ('default', 'Default', 'Default environment'),
            ('eos', 'EOS', 'EOS environment'),
            ('forest', 'Forest', 'Forest environment'),
            ('goldmine', 'Goldmine', 'Goldmine environment'),
            ('goaland', 'Goaland', 'Goaland environment'),
            ('joshuatree', 'Joshua Tree', 'Joshua Tree environment'),
            ('moon', 'Moon', 'Moon environment'),
            ('osiris', 'Osiris', 'Osiris environment'),
            ('poison', 'Poison', 'Poison environment'),
            ('starry', 'Starry', 'Starry environment'),
            ('threetowers', 'Three Towers', 'Three Towers environment'),
            ('touch', 'Touch', 'Touch environment'),
            ('trek', 'Trek', 'Trek environment'),
            ('yavapai', 'Yavapai', 'Yavapai environment'),
        ],
        default='yavapai',
    )


def unregister():
    """Unregister UI elements."""
    # Unregister the panel class
    bpy.utils.unregister_class(AFRAME_PT_export_panel)
    
    # Remove properties from scene
    if hasattr(bpy.types.Scene, 'aframe_export_path'):
        del bpy.types.Scene.aframe_export_path
    if hasattr(bpy.types.Scene, 'aframe_project_name'):
        del bpy.types.Scene.aframe_project_name
    if hasattr(bpy.types.Scene, 'aframe_version'):
        del bpy.types.Scene.aframe_version
    if hasattr(bpy.types.Scene, 'aframe_include_environment'):
        del bpy.types.Scene.aframe_include_environment
    if hasattr(bpy.types.Scene, 'aframe_environment_preset'):
        del bpy.types.Scene.aframe_environment_preset
