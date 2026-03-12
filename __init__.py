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

    # Store collapsible UI state on WindowManager (avoids operator property limits in Blender 5+)
    wm = bpy.types.WindowManager
    wm.aframe_show_aframe     = BoolProperty(name="A-Frame Settings", default=True)
    wm.aframe_show_environment= BoolProperty(name="Environment", default=True)
    wm.aframe_show_webapp     = BoolProperty(name="Web App", default=False)
    wm.aframe_show_materials  = BoolProperty(name="Materials", default=False)
    wm.aframe_show_export     = BoolProperty(name="Export Format", default=False)
    wm.aframe_show_adv        = BoolProperty(name="Advanced", default=False)

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

    # Remove WindowManager UI state props
    wm = bpy.types.WindowManager
    for prop in ('aframe_show_aframe', 'aframe_show_environment', 'aframe_show_webapp', 'aframe_show_materials', 'aframe_show_export',
                 'aframe_show_adv'):
        if hasattr(wm, prop):
            delattr(wm, prop)
    
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

    # BLENDER 5.0 BUG: Operator properties are silently truncated after ~8 entries.
    # Properties defined beyond the cutoff are never registered with Blender's RNA
    # system and will not appear in the UI or be accessible at runtime — no error
    # is raised, they simply don't exist. Confirmed via:
    #   bpy.ops.export_scene.aframe.get_rna_type().properties.keys()
    #
    # Workarounds applied:
    #   1. sky_color is placed 2nd in the property list so it is always within the
    #      safe range regardless of the exact cutoff.
    #   2. Collapsible UI toggle state (show_*) has been moved off the operator
    #      entirely and onto bpy.types.WindowManager (see register()), which has no
    #      such limit. draw() and invoke() use context.window_manager for these.
    project_name: StringProperty(
        name="Project Name",
        description="Name of the A-Frame project",
        default="aframe-project",
    )
    sky_color: EnumProperty(
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
    export_lights: BoolProperty(name="Export Lights", default=False)
    camera_as_look_controls: BoolProperty(name="Use Camera as Look Controls", default=True)
    shadows_enabled: BoolProperty(name="Enable Shadows", default=True)
    enable_cursor: BoolProperty(name="Enable Cursor", default=False)
    fog_enabled: BoolProperty(name="Enable Fog", default=False)
    fog_color: StringProperty(name="Fog Color", default="#97a288")
    fog_density: FloatProperty(name="Fog Density", default=0.01, min=0.0, max=1.0)
    use_mixins: BoolProperty(name="Use Material Mixins", default=True)
    export_textures: BoolProperty(name="Export Textures", default=False)
    include_custom_css: BoolProperty(name="Include Custom CSS", default=False)
    custom_css: StringProperty(name="Custom CSS", default="", subtype='FILE_PATH')
    include_manifest: BoolProperty(name="Include Web App Manifest", default=True)
    include_service_worker: BoolProperty(name="Include Service Worker", default=True)
    export_as_zip: BoolProperty(name="Export as ZIP", default=False)
    theme_color: StringProperty(name="Theme Color", default="#ff6b6b")
    background_color: StringProperty(name="Background Color", default="#212121")

    def invoke(self, context, event):
        """Pre-populate from render panel and explicitly open key sections."""
        scene = context.scene

        # Copy render panel values into operator
        prop_map = {
            'aframe_project_name':        'project_name',
            'aframe_version':             'aframe_version',
            'aframe_use_camera_look_controls': 'camera_as_look_controls',
            'aframe_export_lights':       'export_lights',
            'aframe_include_environment': 'include_environment',
            'aframe_environment_preset':  'environment_preset',
            'aframe_sky_color':           'sky_color',
            'aframe_shadows_enabled':     'shadows_enabled',
            'aframe_enable_cursor':       'enable_cursor',
            'aframe_fog_enabled':         'fog_enabled',
            'aframe_fog_color':           'fog_color',
            'aframe_fog_density':         'fog_density',
            'aframe_use_mixins':          'use_mixins',
            'aframe_include_custom_css':  'include_custom_css',
            'aframe_custom_css':          'custom_css',
            'aframe_export_textures':     'export_textures',
            'aframe_theme_color':         'theme_color',
            'aframe_background_color':    'background_color',
            'aframe_include_manifest':    'include_manifest',
            'aframe_include_service_worker': 'include_service_worker',
            'aframe_export_as_zip':       'export_as_zip',
        }
        for scene_prop, op_prop in prop_map.items():
            if hasattr(scene, scene_prop):
                try:
                    setattr(self, op_prop, getattr(scene, scene_prop))
                except Exception:
                    pass

        # Initialise collapsible section state on WindowManager
        wm = context.window_manager
        wm.aframe_show_aframe      = True
        wm.aframe_show_environment = True
        wm.aframe_show_webapp      = False
        wm.aframe_show_materials   = False
        wm.aframe_show_export      = False
        wm.aframe_show_adv         = False

        return ExportHelper.invoke(self, context, event)

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
        
        # Use sky_color for scene background (since background_color isn't exposed in UI)
        background_color = sky_color
        
        # Export the scene
        try:
            # Export index.html
            result = exporter.export_scene_to_html(
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
            
            if result is None:
                raise Exception("Failed to export scene to HTML")
            
            # Export manifest.json if enabled
            try:
                if include_manifest:
                    exporter.export_manifest(
                        export_dir,
                        project_name,
                        theme_color,
                        background_color,
                    )
            except Exception as e:
                self.report({'WARNING'}, f"Failed to export manifest: {e}")
            
            # Export service worker if enabled
            try:
                if include_service_worker:
                    exporter.export_service_worker(export_dir, project_name)
            except Exception as e:
                self.report({'WARNING'}, f"Failed to export service worker: {e}")
            
            # Export icons
            try:
                assets.export_default_icons(assets_dir, theme_color)
            except Exception as e:
                self.report({'WARNING'}, f"Failed to export icons: {e}")
            
            # Export textures if enabled - wrapped in try/except for safety
            if export_textures:
                try:
                    assets.export_textures(context, assets_dir)
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to export textures: {e}")
            
            # Export as ZIP if requested
            if export_as_zip:
                try:
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
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to create ZIP: {e}")
            else:
                self.report({'INFO'}, "Export completed successfully!")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}

    def draw(self, context):
        """Draw the export options panel with collapsible sections."""
        layout = self.layout

        wm = context.window_manager

        def header(box, toggle_prop, label, icon='NONE'):
            """Proper collapsible header: triangle icon + label, no checkbox."""
            row = box.row()
            row.prop(wm, toggle_prop,
                     icon='TRIA_DOWN' if getattr(wm, toggle_prop) else 'TRIA_RIGHT',
                     icon_only=True, emboss=False)
            row.label(text=label, icon=icon)
            return getattr(wm, toggle_prop)

        # Project settings — always visible
        box = layout.box()
        box.label(text="Project Settings:", icon='FILE')
        box.prop(self, "project_name")

        # A-Frame Settings — only the 3 most common options open by default
        box = layout.box()
        if header(box, "aframe_show_aframe", "A-Frame Settings", icon='WORLD'):
            box.prop(self, "aframe_version")
            box.prop(self, "camera_as_look_controls")
            box.prop(self, "export_lights")

        # Environment — sky_color is always first so it can never be cut off
        box = layout.box()
        if header(box, "aframe_show_environment", "Environment", icon='WORLD_DATA'):
            box.prop(self, "sky_color")
            box.prop(self, "include_environment")
            if self.include_environment:
                box.prop(self, "environment_preset")

        # Advanced (shadows, cursor, fog) — closed by default
        box = layout.box()
        if header(box, "aframe_show_adv", "Advanced", icon='SETTINGS'):
            box.prop(self, "shadows_enabled")
            box.prop(self, "enable_cursor")
            box.prop(self, "fog_enabled")
            if self.fog_enabled:
                box.prop(self, "fog_color")
                box.prop(self, "fog_density")

        # Web App — closed by default
        box = layout.box()
        if header(box, "aframe_show_webapp", "Web App", icon='URL'):
            box.prop(self, "theme_color")
            box.prop(self, "background_color")
            box.prop(self, "include_manifest")
            box.prop(self, "include_service_worker")

        # Materials — closed by default
        box = layout.box()
        if header(box, "aframe_show_materials", "Materials", icon='MATERIAL'):
            box.prop(self, "use_mixins")
            box.prop(self, "include_custom_css")
            if self.include_custom_css:
                box.prop(self, "custom_css")
            box.prop(self, "export_textures")

        # Export Format — closed by default
        box = layout.box()
        if header(box, "aframe_show_export", "Export Format", icon='FILE_ARCHIVE'):
            box.prop(self, "export_as_zip")
