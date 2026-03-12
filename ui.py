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
        box.prop(scene, "aframe_use_camera_look_controls")
        box.prop(scene, "aframe_export_lights")
        box.prop(scene, "aframe_include_environment")
        if scene.aframe_include_environment:
            box.prop(scene, "aframe_environment_preset")
        box.prop(scene, "aframe_sky_color")

        # Advanced settings
        box = layout.box()
        box.label(text="Advanced", icon='SETTINGS')
        box.prop(scene, "aframe_shadows_enabled")
        box.prop(scene, "aframe_enable_cursor")
        box.prop(scene, "aframe_fog_enabled")
        if scene.aframe_fog_enabled:
            box.prop(scene, "aframe_fog_color")
            box.prop(scene, "aframe_fog_density")

        # Web App settings
        box = layout.box()
        box.label(text="Web App", icon='URL')
        box.prop(scene, "aframe_theme_color")
        box.prop(scene, "aframe_background_color")
        box.prop(scene, "aframe_include_manifest")
        box.prop(scene, "aframe_include_service_worker")

        # Materials settings
        box = layout.box()
        box.label(text="Materials", icon='MATERIAL')
        box.prop(scene, "aframe_use_mixins")
        box.prop(scene, "aframe_include_custom_css")
        if scene.aframe_include_custom_css:
            box.prop(scene, "aframe_custom_css")
        box.prop(scene, "aframe_export_textures")

        # Export Format settings
        box = layout.box()
        box.label(text="Export Format", icon='FILE_ARCHIVE')
        box.prop(scene, "aframe_export_as_zip")
        
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
            ('default', 'Default', 'Default environment'),
            ('contact', 'Contact', 'Contact environment'),
            ('egypt', 'Egypt', 'Egypt environment'),
            ('checkerboard', 'Checkerboard', 'Checkerboard environment'),
            ('forest', 'Forest', 'Forest environment'),
            ('goaland', 'Goaland', 'Goaland environment'),
            ('yavapai', 'Yavapai', 'Yavapai environment'),
            ('goldmine', 'Goldmine', 'Goldmine environment'),
            ('threetowers', 'Three Towers', 'Three Towers environment'),
            ('poison', 'Poison', 'Poison environment'),
            ('arches', 'Arches', 'Arches environment'),
            ('tron', 'Tron', 'Tron environment'),
            ('japan', 'Japan', 'Japan environment'),
            ('dream', 'Dream', 'Dream environment'),
            ('volcano', 'Volcano', 'Volcano environment'),
            ('starry', 'Starry', 'Starry environment'),
            ('osiris', 'Osiris', 'Osiris environment'),
            ('moon', 'Moon', 'Moon environment'),
        ],
        default='yavapai',
    )
    
    bpy.types.Scene.aframe_sky_color = bpy.props.EnumProperty(
        name="Sky Color",
        description="Sky/environment color",
        items=[
            ('#87CEEB', 'Sky Blue', 'Default sky blue'),
            ('#000000', 'Black', 'Black'),
            ('#FFFFFF', 'White', 'White'),
            ('#FF6B6B', 'Red', 'Red'),
            ('#4ECDC4', 'Teal', 'Teal'),
            ('#45B7D1', 'Light Blue', 'Light Blue'),
            ('#96CEB4', 'Sage Green', 'Sage Green'),
            ('#FFEAA7', 'Light Yellow', 'Light Yellow'),
            ('#DDA0DD', 'Plum', 'Plum'),
            ('#98D8C8', 'Mint', 'Mint'),
        ],
        default='#87CEEB',
    )

    bpy.types.Scene.aframe_use_camera_look_controls = bpy.props.BoolProperty(
        name="Use Camera as Look Controls",
        description="Use camera as look controls",
        default=True,
    )

    bpy.types.Scene.aframe_export_lights = bpy.props.BoolProperty(
        name="Export Lights",
        description="Export lights to A-Frame",
        default=True,
    )

    bpy.types.Scene.aframe_shadows_enabled = bpy.props.BoolProperty(
        name="Enable Shadows",
        description="Enable shadows in A-Frame",
        default=True,
    )

    bpy.types.Scene.aframe_enable_cursor = bpy.props.BoolProperty(
        name="Enable Cursor",
        description="Enable cursor in A-Frame",
        default=False,
    )

    bpy.types.Scene.aframe_theme_color = bpy.props.StringProperty(
        name="Theme Color",
        description="Theme color for web app",
        default="#ff6b6b",
    )

    bpy.types.Scene.aframe_background_color = bpy.props.StringProperty(
        name="Background Color",
        description="Background color for web app",
        default="#212121",
    )

    bpy.types.Scene.aframe_include_manifest = bpy.props.BoolProperty(
        name="Include Web App Manifest",
        description="Include web app manifest",
        default=True,
    )

    bpy.types.Scene.aframe_include_service_worker = bpy.props.BoolProperty(
        name="Include Service Worker",
        description="Include service worker for offline support",
        default=True,
    )

    bpy.types.Scene.aframe_use_mixins = bpy.props.BoolProperty(
        name="Use Material Mixins",
        description="Use material mixins for better performance",
        default=True,
    )

    bpy.types.Scene.aframe_include_custom_css = bpy.props.BoolProperty(
        name="Include Custom CSS",
        description="Include custom CSS",
        default=False,
    )

    bpy.types.Scene.aframe_custom_css = bpy.props.StringProperty(
        name="Custom CSS",
        description="Path to custom CSS file",
        default="",
        subtype='FILE_PATH',
    )

    bpy.types.Scene.aframe_export_textures = bpy.props.BoolProperty(
        name="Export Textures",
        description="Export textures with the scene",
        default=True,
    )

    bpy.types.Scene.aframe_export_as_zip = bpy.props.BoolProperty(
        name="Export as ZIP",
        description="Export as ZIP file instead of folder",
        default=False,
    )

    bpy.types.Scene.aframe_fog_enabled = bpy.props.BoolProperty(
        name="Enable Fog",
        description="Enable scene fog",
        default=False,
    )

    bpy.types.Scene.aframe_fog_color = bpy.props.StringProperty(
        name="Fog Color",
        description="Fog color as hex",
        default="#97a288",
    )

    bpy.types.Scene.aframe_fog_density = bpy.props.FloatProperty(
        name="Fog Density",
        description="Fog density (0.0 - 1.0)",
        default=0.01,
        min=0.0,
        max=1.0,
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
    if hasattr(bpy.types.Scene, 'aframe_sky_color'):
        del bpy.types.Scene.aframe_sky_color
    if hasattr(bpy.types.Scene, 'aframe_use_camera_look_controls'):
        del bpy.types.Scene.aframe_use_camera_look_controls
    if hasattr(bpy.types.Scene, 'aframe_export_lights'):
        del bpy.types.Scene.aframe_export_lights
    if hasattr(bpy.types.Scene, 'aframe_shadows_enabled'):
        del bpy.types.Scene.aframe_shadows_enabled
    if hasattr(bpy.types.Scene, 'aframe_enable_cursor'):
        del bpy.types.Scene.aframe_enable_cursor
    if hasattr(bpy.types.Scene, 'aframe_theme_color'):
        del bpy.types.Scene.aframe_theme_color
    if hasattr(bpy.types.Scene, 'aframe_background_color'):
        del bpy.types.Scene.aframe_background_color
    if hasattr(bpy.types.Scene, 'aframe_include_manifest'):
        del bpy.types.Scene.aframe_include_manifest
    if hasattr(bpy.types.Scene, 'aframe_include_service_worker'):
        del bpy.types.Scene.aframe_include_service_worker
    if hasattr(bpy.types.Scene, 'aframe_use_mixins'):
        del bpy.types.Scene.aframe_use_mixins
    if hasattr(bpy.types.Scene, 'aframe_include_custom_css'):
        del bpy.types.Scene.aframe_include_custom_css
    if hasattr(bpy.types.Scene, 'aframe_custom_css'):
        del bpy.types.Scene.aframe_custom_css
    if hasattr(bpy.types.Scene, 'aframe_export_textures'):
        del bpy.types.Scene.aframe_export_textures
    if hasattr(bpy.types.Scene, 'aframe_export_as_zip'):
        del bpy.types.Scene.aframe_export_as_zip
    if hasattr(bpy.types.Scene, 'aframe_fog_enabled'):
        del bpy.types.Scene.aframe_fog_enabled
    if hasattr(bpy.types.Scene, 'aframe_fog_color'):
        del bpy.types.Scene.aframe_fog_color
    if hasattr(bpy.types.Scene, 'aframe_fog_density'):
        del bpy.types.Scene.aframe_fog_density
