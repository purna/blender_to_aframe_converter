bl_info = {
    "name": "A-Frame Exporter",
    "author": "Pixelgent",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "bl_maxversion": (5, 99, 0),
    "location": "File > Export > A-Frame (.html)",
    "description": "Export Blender scenes to A-Frame VR projects",
    "warning": "",
    "wiki_url": "https://github.com/purna/blender_to_aframe_converter/wiki",
    "tracker_url": "https://github.com/purna/blender_to_aframe_converter/issues",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
import os
import json
import shutil
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    FloatProperty,
)
from bpy_extras.io_utils import (
    ExportHelper,
    axis_conversion,
)

# Import submodules
from . import exporter
from . import ui
from . import assets


def register():
    """Register the addon with Blender."""
    # Register the exporter operator class
    bpy.utils.register_class(AframeExporter)
    
    # Register UI
    ui.register()
    
    # Add to export menu - try multiple menu types for compatibility
    for menu_name in ('TOPBAR_MT_file_export', 'INFO_MT_file_export'):
        menu = getattr(bpy.types, menu_name, None)
        if menu is not None:
            menu.append(menu_func_export)
            break


def unregister():
    """Unregister the addon from Blender."""
    # Unregister UI
    ui.unregister()
    
    # Remove from export menu
    for menu_name in ('TOPBAR_MT_file_export', 'INFO_MT_file_export'):
        menu = getattr(bpy.types, menu_name, None)
        if menu is not None:
            menu.remove(menu_func_export)
            break
    
    # Unregister the exporter operator class
    bpy.utils.unregister_class(AframeExporter)


def menu_func_export(self, context):
    """Add export option to the file menu."""
    self.layout.operator(AframeExporter.bl_idname, text="A-Frame (.html)")


class AframeExporter(bpy.types.Operator, ExportHelper):
    """Export Blender scene to A-Frame project."""
    bl_idname = "export_scene.aframe"
    bl_label = "Export A-Frame"
    bl_options = {'PRESET'}

    filename_ext = ".html"
    
    # Export settings - using annotations for proper Blender property registration
    project_name: StringProperty(
        name="Project Name",
        description="Name of the A-Frame project",
        default="aframe-project",
    )
    
    include_environment: BoolProperty(
        name="Include Environment",
        description="Include A-Frame environment component",
        default=True,
    )
    
    environment_preset: EnumProperty(
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
    
    export_textures: BoolProperty(
        name="Export Textures",
        description="Export textures alongside the scene",
        default=True,
    )
    
    export_lights: BoolProperty(
        name="Export Lights",
        description="Export scene lights",
        default=False,  # Disabled by default to prevent crashes
    )
    
    camera_as_look_controls: BoolProperty(
        name="Use Camera as Look Controls",
        description="Set active camera as look-controls",
        default=True,
    )
    
    aframe_version: EnumProperty(
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
    
    theme_color: StringProperty(
        name="Theme Color",
        description="Theme color for the web app",
        default="#ff6b6b",
        subtype='COLOR',
    )
    
    background_color: StringProperty(
        name="Background Color",
        description="Background color for the web app",
        default="#212121",
        subtype='COLOR',
    )
    
    fog_enabled: BoolProperty(
        name="Enable Fog",
        description="Enable scene fog",
        default=False,
    )
    
    fog_color: StringProperty(
        name="Fog Color",
        description="Fog color",
        default="#97a288",
        subtype='COLOR',
    )
    
    fog_density: FloatProperty(
        name="Fog Density",
        description="Fog density",
        default=0.01,
        min=0.0,
        max=1.0,
    )
    
    use_mixins: BoolProperty(
        name="Use Material Mixins",
        description="Export materials as reusable mixins",
        default=True,
    )
    
    enable_cursor: BoolProperty(
        name="Enable Cursor",
        description="Add cursor for interaction (click/gaze)",
        default=False,
    )
    
    shadows_enabled: BoolProperty(
        name="Enable Shadows",
        description="Enable shadow casting for objects and lights",
        default=True,
    )
    
    include_custom_css: BoolProperty(
        name="Include Custom CSS",
        description="Export custom CSS file",
        default=False,
    )
    
    custom_css: StringProperty(
        name="Custom CSS",
        description="Custom CSS content",
        default="",
        subtype='FILE_PATH',
    )
    
    # PWA Options
    include_manifest: BoolProperty(
        name="Include Web App Manifest",
        description="Export manifest.json for PWA",
        default=True,
    )
    
    include_service_worker: BoolProperty(
        name="Include Service Worker",
        description="Export sw.js for offline support",
        default=True,
    )
    
    export_as_zip: BoolProperty(
        name="Export as ZIP",
        description="Export project as a ZIP file",
        default=False,
    )
    
    sky_color: StringProperty(
        name="Sky Color",
        description="Sky/environment color",
        default="#87CEEB",
        subtype='COLOR',
    )

    def execute(self, context):
        """Execute the export."""
        # Get property values using getattr to ensure proper resolution
        project_name = getattr(self, 'project_name', "aframe-project")
        if hasattr(project_name, '__class__') and 'Deferred' in project_name.__class__.__name__:
            project_name = "aframe-project"
        
        # Use blend file directory as default (or user files folder)
        blend_file = bpy.data.filepath
        if blend_file:
            export_dir = os.path.join(os.path.dirname(blend_file), project_name)
        else:
            export_dir = os.path.join(os.path.expanduser("~"), project_name)
        
        # Create export directory
        os.makedirs(export_dir, exist_ok=True)
        assets_dir = os.path.join(export_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        # Report start
        self.report({'INFO'}, f"Exporting to: {export_dir}")
        
        # Get all property values
        include_environment = getattr(self, 'include_environment', True)
        environment_preset = getattr(self, 'environment_preset', 'yavapai')
        export_lights = getattr(self, 'export_lights', True)
        shadows_enabled = getattr(self, 'shadows_enabled', True)
        camera_as_look_controls = getattr(self, 'camera_as_look_controls', True)
        enable_cursor = getattr(self, 'enable_cursor', False)
        aframe_version = getattr(self, 'aframe_version', '1.7.1')
        fog_enabled = getattr(self, 'fog_enabled', False)
        fog_color = getattr(self, 'fog_color', '#97a288')
        fog_density = getattr(self, 'fog_density', 0.01)
        include_custom_css = getattr(self, 'include_custom_css', False)
        custom_css = getattr(self, 'custom_css', "")
        use_mixins = getattr(self, 'use_mixins', True)
        include_manifest = getattr(self, 'include_manifest', True)
        include_service_worker = getattr(self, 'include_service_worker', True)
        theme_color = getattr(self, 'theme_color', '#ff6b6b')
        background_color = getattr(self, 'background_color', '#212121')
        export_textures = getattr(self, 'export_textures', True)
        export_as_zip = getattr(self, 'export_as_zip', False)
        sky_color = getattr(self, 'sky_color', '#87CEEB')
        if hasattr(sky_color, '__class__') and 'Deferred' in sky_color.__class__.__name__:
            sky_color = '#87CEEB'
        
        # Export the scene
        try:
            # Export index.html
            exporter.export_scene_to_html(
                context,
                export_dir,
                self.report,
                include_environment=include_environment,
                environment_preset=environment_preset,
                export_lights=export_lights,
                shadows_enabled=shadows_enabled,
                camera_as_look_controls=camera_as_look_controls,
                enable_cursor=enable_cursor,
                aframe_version=aframe_version,
                fog_enabled=fog_enabled,
                fog_color=fog_color,
                fog_density=fog_density,
                include_custom_css=include_custom_css,
                custom_css=custom_css,
                use_mixins=use_mixins,
                sky_color=sky_color,
            )
            
            # Export manifest.json if enabled
            if include_manifest:
                exporter.export_manifest(
                    export_dir,
                    project_name,
                    theme_color,
                    background_color,
                )
            
            # Export service worker if enabled
            if include_service_worker:
                exporter.export_service_worker(export_dir, project_name)
            
            # Export icons
            assets.export_default_icons(assets_dir, theme_color)
            
            # Export textures if enabled
            if export_textures:
                assets.export_textures(context, assets_dir)
            
            # Export as ZIP if requested
            if export_as_zip:
                import zipfile
                zip_path = export_dir + ".zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(export_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(export_dir))
                            zipf.write(file_path, arcname)
                # Remove the original directory after ZIP
                shutil.rmtree(export_dir)
                self.report({'INFO'}, f"Export completed: {zip_path}")
            else:
                self.report({'INFO'}, "Export completed successfully!")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}

    def draw(self, context):
        """Draw the export options panel."""
        layout = self.layout
        
        # Project settings
        box = layout.box()
        box.label(text="Project Settings:", icon='FILE')
        box.prop(self, "project_name")
        
        # A-Frame settings
        box = layout.box()
        box.label(text="A-Frame Settings:", icon='WORLD')
        box.prop(self, "aframe_version")
        box.prop(self, "camera_as_look_controls")
        box.prop(self, "export_lights")
        box.prop(self, "shadows_enabled")
        box.prop(self, "enable_cursor")
        
        # Environment settings
        box = layout.box()
        box.label(text="Environment:", icon='WORLD_DATA')
        box.prop(self, "include_environment")
        # Check if include_environment is True (handle deferred property)
        try:
            inc_env = getattr(self, 'include_environment', True)
            if hasattr(inc_env, '__class__') and 'Deferred' in inc_env.__class__.__name__:
                inc_env = True
            if inc_env:
                box.prop(self, "environment_preset")
                box.prop(self, "sky_color")
        except Exception:
            pass
        
        # Fog settings
        box = layout.box()
        box.label(text="Fog:", icon='FOG')
        box.prop(self, "fog_enabled")
        # Check if fog_enabled is True (handle deferred property)
        try:
            fog_en = getattr(self, 'fog_enabled', False)
            if hasattr(fog_en, '__class__') and 'Deferred' in fog_en.__class__.__name__:
                fog_en = False
            if fog_en:
                box.prop(self, "fog_color")
                box.prop(self, "fog_density")
        except Exception:
            pass
        
        # Web App settings
        box = layout.box()
        box.label(text="Web App:", icon='APP')
        box.prop(self, "theme_color")
        box.prop(self, "background_color")
        box.prop(self, "include_manifest")
        box.prop(self, "include_service_worker")
        
        # Materials
        box = layout.box()
        box.label(text="Materials:", icon='MATERIAL')
        box.prop(self, "use_mixins")
        
        # Custom CSS
        box = layout.box()
        box.label(text="Custom CSS:", icon='TEXT')
        box.prop(self, "include_custom_css")
        
        # Export format
        box = layout.box()
        box.label(text="Export Format:", icon='FILE_ARCHIVE')
        box.prop(self, "export_as_zip")
