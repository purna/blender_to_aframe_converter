"""
A-Frame Exporter - Scene Conversion Module

This module handles the conversion of Blender scenes to A-Frame HTML format.
"""

import bpy
import os
import math
import json
from mathutils import Matrix

# Mapping of Blender object types to A-Frame entities
BLENDER_TO_AFRAME_PRIMITIVES = {
    'MESH': 'a-box',
    'CURVE': 'a-entity',
    'SURFACE': 'a-entity',
    'META': 'a-entity',
    'FONT': 'a-text',
    'ARMATURE': 'a-entity',
    'LATTICE': 'a-entity',
    'EMPTY': 'a-entity',
    'LIGHT': None,  # Handled separately
    'CAMERA': None,  # Handled separately
}

# Mapping of Blender primitive mesh types to A-Frame primitives
MESH_TO_AFRAME = {
    'box': 'a-box',
    'sphere': 'a-sphere',
    'cylinder': 'a-cylinder',
    'cone': 'a-cone',
    'torus': 'a-torus',
    'plane': 'a-plane',
    'circle': 'a-circle',
    'uv_sphere': 'a-sphere',
    'ico_sphere': 'a-sphere',
    'cube': 'a-box',
}


def get_blender_object_type(obj):
    """Get the Blender object type."""
    return obj.type


def convert_location(loc):
    """Convert Blender location to A-Frame format."""
    # Blender uses Z-up, A-Frame uses Y-up
    # We need to rotate coordinates: X->X, Y->Z, Z->Y
    return f"{loc.x:.4f} {loc.z:.4f} {-loc.y:.4f}"


def convert_rotation(rot, degrees=True):
    """Convert Blender rotation to A-Frame format."""
    # Blender uses radians or degrees, A-Frame uses degrees
    # Convert from Z-up to Y-up coordinate system
    if degrees:
        rx = math.degrees(rot.x)
        ry = math.degrees(rot.y)
        rz = math.degrees(rot.z)
    else:
        rx = rot.x
        ry = rot.y
        rz = rot.z
    
    # Apply coordinate system transformation
    # A-Frame rotation order is XYZ
    return f"{-rx:.2f} {rz:.2f} {-ry:.2f}"


def convert_scale(scale):
    """Convert Blender scale to A-Frame format."""
    return f"{scale.x:.4f} {scale.z:.4f} {scale.y:.4f}"


def convert_color(color):
    """Convert RGB color to hex."""
    r = int(color[0] * 255)
    g = int(color[1] * 255)
    b = int(color[2] * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


# Additional A-Frame component scripts to include
AFRAME_COMPONENT_SCRIPTS = {
    'environment': 'https://unpkg.com/aframe-environment-component@1.3.3/dist/aframe-environment-component.min.js',
    'extras': 'https://unpkg.com/aframe-extras@7.0.0/dist/aframe-extras.min.js',
    'physics': 'https://unpkg.com/aframe-physics-system@1.4.0/dist/aframe-physics-system.min.js',
    'particle-system': 'https://unpkg.com/aframe-particle-system-component@1.0.x/dist/aframe-particle-system-component.min.js',
    'event-set': 'https://unpkg.com/aframe-event-set-component@5.0.0/dist/aframe-event-set-component.min.js',
    'super-hands': 'https://unpkg.com/super-hands@3.0.4/dist/super-hands.min.js',
    'teleport-controls': 'https://unpkg.com/aframe-teleport-controls@0.3.x/dist/aframe-teleport-controls.min.js',
}

# Material library storage
MATERIAL_LIBRARY = {}

# Texture library storage
TEXTURE_LIBRARY = {}

# Animation tracking
ANIMATION_TRACKS = []

def get_material_id(material):
    """Generate a unique ID for a material."""
    # Replace spaces and dots with underscores to create valid CSS selectors
    name = material.name.lower().replace(' ', '_').replace('.', '_')
    return f"mat_{name}"


def get_texture_id(image):
    """Generate a unique ID for a texture."""
    if image is None:
        return None
    name = image.name.lower().replace(' ', '_').replace('.', '_')
    return f"tex_{name}"


def convert_material(obj, use_mixins=True):
    """Convert Blender material to A-Frame material properties or mixin."""
    if not obj.data.materials:
        return ""
    
    mat = obj.data.materials[0]
    mat_id = get_material_id(mat)
    
    if not mat.use_nodes:
        # Legacy materials
        if mat.diffuse_color:
            return f'color="{convert_color(mat.diffuse_color)}"'
        return ""
    
    # Node-based materials
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Find the Principled BSDF
    principled = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            principled = node
            break
    
    if not principled:
        return ""
    
    # Extract material properties
    props = []
    
    # Check for texture connected to Base Color
    base_color_input = principled.inputs.get('Base Color')
    if base_color_input and hasattr(base_color_input, 'links') and base_color_input.links:
        texture_node = base_color_input.links[0].from_node
        if texture_node and texture_node.type == 'TEX_IMAGE':
            if texture_node.image:
                tex_id = get_texture_id(texture_node.image)
                TEXTURE_LIBRARY[tex_id] = {
                    'image': texture_node.image,
                    'filepath': texture_node.image.filepath
                }
                props.append(f'src: #{tex_id}')
                print(f"DEBUG: Found texture: {tex_id} - {texture_node.image.filepath}")
                # Also get color if available
                try:
                    if hasattr(texture_node, 'inputs') and texture_node.inputs.get('Color'):
                        tex_color = texture_node.inputs['Color'].default_value
                        if tex_color and len(tex_color) >= 3:
                            props.append(f'color: {convert_color(tex_color[:3])}')
                except:
                    pass
    
    # Base color - with safety check (only if not using texture)
    if 'src:' not in '; '.join(props):
        try:
            base_color_input = principled.inputs.get('Base Color')
            if base_color_input is not None:
                color = base_color_input.default_value
                if color:
                    props.append(f'color: {convert_color(color[:3])}')
        except Exception:
            pass
    
    # Metalness - with safety check
    try:
        metallic_input = principled.inputs.get('Metallic')
        if metallic_input is not None and metallic_input.default_value > 0:
            props.append(f'metalness: {metallic_input.default_value:.2f}')
    except Exception:
        pass
    
    # Roughness - with safety check
    try:
        roughness_input = principled.inputs.get('Roughness')
        if roughness_input is not None and roughness_input.default_value > 0:
            props.append(f'roughness: {roughness_input.default_value:.2f}')
    except Exception:
        pass
    
    # Opacity/Transparency - with safety check
    try:
        alpha_input = principled.inputs.get('Alpha')
        if alpha_input is not None and alpha_input.default_value < 1:
            props.append(f'opacity: {alpha_input.default_value:.2f}')
            props.append('transparent: true')
    except Exception:
        pass
    
    # Emission (for glowing materials) - with safety check for different Blender versions
    try:
        emission_input = principled.inputs.get('Emission')
        if emission_input is not None:
            emission_val = emission_input.default_value
            if len(emission_val) >= 3 and emission_val[3] > 0:
                emission_strength_input = principled.inputs.get('Emission Strength')
                if emission_strength_input is not None:
                    emission_strength = emission_strength_input.default_value
                    props.append(f'emissiveIntensity: {emission_strength:.2f}')
                emission_color = emission_val
                props.append(f'emissive: {convert_color(emission_color[:3])}')
    except Exception:
        pass  # Emission not available in this Blender version
    
    if not props:
        return ""
    
    # Check if we have a texture
    has_texture = any('src:' in prop for prop in props)
    
    # If we have a texture, use inline material to ensure texture is applied
    # Otherwise use mixin for better performance
    if has_texture:
        # Use inline material with texture
        mat_str = '; '.join(props)
        return f'material="{mat_str}"'
    elif use_mixins:
        # Store in material library for mixin
        MATERIAL_LIBRARY[mat_id] = {
            'shader': 'standard',
            'props': props
        }
        return f'mixin="{mat_id}"'
    else:
        # Inline material
        mat_str = '; '.join(props)
        return f'material="{mat_str}"'


def get_mesh_primitive(obj):
    """Determine the A-Frame primitive based on mesh data."""
    if not obj.data or obj.type != 'MESH':
        return 'a-box'  # Default
    
    mesh = obj.data
    
    # Check for custom shape/animation
    if obj.data.shape_keys:
        return 'a-entity'  # Animated meshes need custom handling
    
    # Try to get the mesh type from Blender object data
    # Blender stores primitive type in obj.data.type
    mesh_type = getattr(mesh, 'type', None)
    if mesh_type and mesh_type in MESH_TO_AFRAME:
        return MESH_TO_AFRAME[mesh_type]
    
    # Also check by object name pattern as fallback (for objects created from primitives)
    obj_name = obj.name.lower()
    
    # Check for standard primitives by name pattern
    if 'sphere' in obj_name or 'icosphere' in obj_name or 'uv_sphere' in obj_name:
        return 'a-sphere'
    if 'torus' in obj_name:
        return 'a-torus'
    if 'cylinder' in obj_name:
        return 'a-cylinder'
    if 'cone' in obj_name:
        return 'a-cone'
    if 'plane' in obj_name:
        return 'a-plane'
    if 'circle' in obj_name:
        return 'a-circle'
    if 'cube' in obj_name or 'box' in obj_name:
        return 'a-box'
    
    # Check for standard primitives by topology
    vertices = len(mesh.vertices)
    polygons = len(mesh.polygons)
    
    # Box/Cube detection (8 vertices, 6 faces)
    if vertices == 8 and polygons == 6:
        return 'a-box'
    
    # Plane detection (4 vertices, 1 face)
    if vertices == 4 and polygons == 1:
        return 'a-plane'
    
    # Circle detection
    if vertices >= 32 and polygons == 1:
        return 'a-circle'
    
    # Sphere detection
    if vertices > 100:
        return 'a-sphere'
    
    # Cylinder detection
    if vertices >= 20 and polygons >= 3:
        return 'a-cylinder'
    
    # Default to box
    return 'a-box'


def convert_text_to_aframe(obj):
    """Convert a Blender text object to A-Frame text entity."""
    if obj.type != 'FONT':
        return None
    
    text_obj = obj.data
    
    attrs = []
    text_props = []
    
    # Position
    attrs.append(f'position="{convert_location(obj.location)}"')
    
    # Rotation
    if obj.rotation_mode == 'QUATERNION':
        euler = obj.rotation_quaternion.to_euler()
        attrs.append(f'rotation="{convert_rotation(euler)}"')
    else:
        attrs.append(f'rotation="{convert_rotation(obj.rotation_euler)}"')
    
    # Scale
    attrs.append(f'scale="{convert_scale(obj.scale)}"')
    
    # Text content
    text_value = text_obj.body if hasattr(text_obj, 'body') else obj.name
    text_props.append(f'value: {text_value}')
    
    # Text color
    text_color = '#FFFFFF'
    if text_obj.materials:
        mat = text_obj.materials[0]
        if hasattr(mat, 'diffuse_color'):
            text_color = convert_color(mat.diffuse_color)
    text_props.append(f'color: {text_color}')
    
    # Text alignment - default to left
    align = getattr(text_obj, 'align', 'left')
    text_props.append(f'align: {align}')
    
    # Font size (width for A-Frame text)
    width = getattr(text_obj, 'size', 1.0)
    text_props.append(f'width: {width * 10}')
    
    # Build text component
    text_component = '; '.join(text_props)
    attrs.append(f'text="{text_component}"')
    
    # Add object name as ID
    attrs.append(f'id="{obj.name}"')
    attrs.append(f'name="{obj.name}"')
    
    element = f"<a-text {' '.join(attrs)}></a-text>"
    
    return element

def get_geometry_attributes(obj):
    """Extract geometry attributes for A-Frame primitives."""
    if not obj.data or obj.type != 'MESH':
        return ""
    
    mesh = obj.data
    
    # Get dimensions
    dims = obj.dimensions
    if dims.x > 0 or dims.y > 0 or dims.z > 0:
        # Map to appropriate attributes based on primitive
        primitive = get_mesh_primitive(obj)
        
        attrs = []
        
        if primitive == 'a-box':
            # Box dimensions
            attrs.append(f'width="{dims.x:.4f}"')
            attrs.append(f'height="{dims.z:.4f}"')
            attrs.append(f'depth="{dims.y:.4f}"')
        
        elif primitive == 'a-sphere':
            # Sphere radius (approximate)
            radius = max(dims.x, dims.y, dims.z) / 2
            attrs.append(f'radius="{radius:.4f}"')
        
        elif primitive == 'a-cylinder':
            # Cylinder
            radius = max(dims.x, dims.y) / 2
            attrs.append(f'radius="{radius:.4f}"')
            attrs.append(f'height="{dims.z:.4f}"')
        
        elif primitive == 'a-plane':
            # Plane
            attrs.append(f'width="{dims.x:.4f}"')
            attrs.append(f'height="{dims.y:.4f}"')
        
        return " ".join(attrs)
    
    return ""


def convert_object_to_aframe(obj, export_lights=True, shadow_enabled=True):
    """Convert a Blender object to A-Frame entity."""
    obj_type = get_blender_object_type(obj)
    
    print(f"DEBUG: Converting object {obj.name}, type: {obj_type}, export_lights: {export_lights}")
    
    # Skip cameras (handled separately)
    if obj_type == 'CAMERA':
        return None
    
    # Handle lights if enabled
    if obj_type == 'LIGHT' and export_lights:
        print(f"DEBUG: Processing light {obj.name}")
        light_result = convert_light_to_aframe(obj)
        print(f"DEBUG: Light result: {light_result}")
        return light_result
    
    # Skip non-mesh objects for now (could be extended)
    if obj_type not in ('MESH', 'CURVE', 'SURFACE', 'FONT', 'LIGHT'):
        # Convert as generic entity
        return convert_generic_entity(obj)
    
    # Handle text objects
    if obj_type == 'FONT':
        return convert_text_to_aframe(obj)
    
    # Get primitive type
    primitive = get_mesh_primitive(obj)
    
    # Build the A-Frame element
    attrs = []
    
    # Position
    attrs.append(f'position="{convert_location(obj.location)}"')
    
    # Rotation
    if obj.rotation_mode == 'QUATERNION':
        # Convert quaternion to euler
        euler = obj.rotation_quaternion.to_euler()
        attrs.append(f'rotation="{convert_rotation(euler)}"')
    else:
        attrs.append(f'rotation="{convert_rotation(obj.rotation_euler)}"')
    
    # Scale
    attrs.append(f'scale="{convert_scale(obj.scale)}"')
    
    # Geometry attributes
    geom_attrs = get_geometry_attributes(obj)
    if geom_attrs:
        attrs.append(geom_attrs)
    
    # Material/Color
    mat_props = convert_material(obj)
    if mat_props:
        attrs.append(mat_props)
    
    # Add object name as ID for reference
    attrs.append(f'id="{obj.name}"')
    
    # Name attribute
    attrs.append(f'name="{obj.name}"')
    
    # Visibility
    if not obj.visible_get():
        attrs.append('visible="false"')
    
    # Shadow properties
    if shadow_enabled:
        # Check if object should cast/receive shadows
        if hasattr(obj, 'display_type'):
            if obj.display_type != 'WIRE':
                attrs.append('shadow="cast: true; receive: true"')
    
    # Build element string
    element = f"<{primitive} {' '.join(attrs)}></{primitive}>"
    
    return element


def convert_generic_entity(obj):
    """Convert a generic Blender object to A-Frame entity."""
    attrs = []
    
    # Position
    attrs.append(f'position="{convert_location(obj.location)}"')
    
    # Rotation
    if obj.rotation_mode == 'QUATERNION':
        euler = obj.rotation_quaternion.to_euler()
        attrs.append(f'rotation="{convert_rotation(euler)}"')
    else:
        attrs.append(f'rotation="{convert_rotation(obj.rotation_euler)}"')
    
    # Scale
    attrs.append(f'scale="{convert_scale(obj.scale)}"')
    
    # Name
    attrs.append(f'id="{obj.name}"')
    attrs.append(f'name="{obj.name}"')
    
    element = f"<a-entity {' '.join(attrs)}></a-entity>"
    
    return element


def convert_light_to_aframe(obj, shadows_enabled=True):
    """Convert a Blender light to A-Frame entity with comprehensive light component.
    
    A-Frame Light Component Reference:
    https://aframe.io/docs/1.7.0/components/light.html
    """
    try:
        light = obj.data
        light_type = light.type
    except Exception as e:
        print(f"Error getting light data: {e}")
        return None
    
    attrs = []
    light_props = []
    
    # Position
    try:
        attrs.append(f'position="{convert_location(obj.location)}"')
    except Exception:
        pass
    
    # Rotation (for spot/directional lights)
    try:
        if obj.rotation_mode == 'QUATERNION':
            euler = obj.rotation_quaternion.to_euler()
            attrs.append(f'rotation="{convert_rotation(euler)}"')
        else:
            attrs.append(f'rotation="{convert_rotation(obj.rotation_euler)}"')
    except Exception:
        pass
    
    # Light type mapping
    aframe_light_type = {
        'POINT': 'point',
        'SUN': 'directional',
        'SPOT': 'spot',
        'AREA': 'area',
    }.get(light_type, 'point')
    
    light_props.append(f'type: {aframe_light_type}')
    
    # Color
    try:
        light_props.append(f'color: {convert_color(light.color[:3])}')
    except Exception:
        light_props.append('color: #ffffff')
    
    # Intensity - A-Frame defaults: point/spot=1, directional=0.5, area=0
    # Blender: Point/Spot = energy (typically 1-1000), Sun = strength (typically 0-10)
    # We'll use higher intensity values to make scenes brighter
    try:
        intensity = light.energy
        if light_type == 'SUN':
            # Sun lights in Blender are often 1-5 strength, but we need higher for A-Frame
            # A-Frame directional lights need intensity around 1.0-2.0 for good brightness
            intensity = intensity * 1.5  # Boost sun intensity
        elif light_type in ('POINT', 'SPOT'):
            # Point/spot lights: Blender uses energy, A-Frame uses intensity directly
            # Scale to reasonable range (A-Frame defaults to 1.0)
            intensity = min(intensity / 50, 3.0)  # Scale down but allow up to 3.0
        elif light_type == 'AREA':
            intensity = min(intensity / 100, 2.0)
        light_props.append(f'intensity: {intensity:.2f}')
    except Exception:
        light_props.append('intensity: 1.5')
    
    # Distance (for point/spot lights) - A-Frame default: 0 (infinite)
    if light_type in ('POINT', 'SPOT'):
        try:
            if hasattr(light, 'cutoff_distance') and light.cutoff_distance > 0:
                light_props.append(f'distance: {light.cutoff_distance:.2f}')
        except Exception:
            pass
    
    # Spotlight specific properties - with safety checks
    if light_type == 'SPOT':
        try:
            # Angle - A-Frame expects full angle, Blender has half angle
            if hasattr(light, 'spot_size') and light.spot_size > 0:
                full_angle = math.degrees(light.spot_size)
                light_props.append(f'angle: {full_angle:.2f}')
            # Penumbra - A-Frame range 0-1
            if hasattr(light, 'spot_blend') and light.spot_blend > 0:
                light_props.append(f'penumbra: {light.spot_blend:.2f}')
                # Penumbra angle (A-Frame 1.4.0+)
                light_props.append(f'penumbraAngle: {light.spot_blend * 45:.2f}')
        except Exception:
            pass
    
    # Shadows (A-Frame 1.0.0+) - with safety checks
    try:
        if shadows_enabled and hasattr(light, 'use_shadow') and light.use_shadow:
            light_props.append('castShadow: true')
            if hasattr(light, 'shadow_bias'):
                light_props.append(f'shadowBias: {light.shadow_bias * 1000:.4f}')
            if hasattr(light, 'shadow_clip_end'):
                light_props.append(f'shadowCameraBottom: {light.shadow_clip_end * -1:.2f}')
                light_props.append(f'shadowCameraLeft: {light.shadow_clip_end * -1:.2f}')
                light_props.append(f'shadowCameraRight: {light.shadow_clip_end:.2f}')
                light_props.append(f'shadowCameraTop: {light.shadow_clip_end:.2f}')
                light_props.append(f'shadowCameraFar: {light.shadow_clip_end:.2f}')
            if hasattr(light, 'shadow_clip_start'):
                light_props.append(f'shadowCameraNear: {light.shadow_clip_start:.4f}')
            if hasattr(light, 'shadow_map_size'):
                light_props.append(f'shadowMapHeight: {light.shadow_map_size}')
                light_props.append(f'shadowMapWidth: {light.shadow_map_size}')
    except Exception:
        pass
    
    # Enable/disable
    light_props.append('enabled: true')
    
    # Build light component string
    light_component = '; '.join(light_props)
    
    attrs.append(f'light="{light_component}"')
    
    # Add light helper visualizer (optional - commented by default)
    # attrs.append('light="type: ambient; intensity: 0.3"')
    
    element = f"<a-entity {' '.join(attrs)}></a-entity>"
    
    return element


def convert_camera_to_aframe(
    obj, 
    use_as_look_controls=True,
    look_controls_options=None,
    wasd_controls_options=None,
    enable_cursor=False,
    cursor_options=None
):
    """Convert a Blender camera to A-Frame camera entity with full component support.
    
    A-Frame Look Controls Reference:
    https://aframe.io/docs/1.7.0/components/look-controls.html
    
    A-Frame WASD Controls Reference:
    https://aframe.io/docs/1.7.0/components/wasd-controls.html
    
    A-Frame Cursor Component Reference:
    https://aframe.io/docs/1.7.0/components/cursor.html
    """
    camera = obj.data
    
    attrs = []
    
    # Position
    attrs.append(f'position="{convert_location(obj.location)}"')
    
    # Rotation
    if obj.rotation_mode == 'QUATERNION':
        euler = obj.rotation_quaternion.to_euler()
        attrs.append(f'rotation="{convert_rotation(euler)}"')
    else:
        attrs.append(f'rotation="{convert_rotation(obj.rotation_euler)}"')
    
    # Camera properties
    camera_props = []
    
    # FOV
    if camera.type == 'PERSP':
        fov_deg = camera.angle_x * 180 / math.pi
        camera_props.append(f'fov: {fov_deg:.1f}')
    elif camera.type == 'ORTHO':
        camera_props.append('fov: 80')  # Ortho doesn't map directly
    
    # Near/far planes
    camera_props.append(f'near: {camera.clip_start:.4f}')
    camera_props.append(f'far: {camera.clip_end:.2f}')
    
    # Aspect ratio
    # camera_props.append(f'aspect: {camera.width / camera.height:.2f}')
    
    # Build camera component if we have props
    if camera_props:
        attrs.append(f'camera="{ "; ".join(camera_props)}"')
    
    # Look Controls
    if use_as_look_controls:
        look_defaults = {
            'enabled': 'true',
            'pointerLockEnabled': 'false',
            'magicWindowTrackingEnabled': 'true',
            'hmdEnabled': 'true',
            'reverseMouseDrag': 'false',
            'touchEnabled': 'true',
            'rotationThreshold': '0.1',
            'minAzimuthAngle': '-Infinity',
            'maxAzimuthAngle': 'Infinity',
            'minPolarAngle': '0',
            'maxPolarAngle': '180',
        }
        
        # Merge with user options
        if look_controls_options:
            look_defaults.update(look_controls_options)
        
        look_str = '; '.join([f'{k}: {v}' for k, v in look_defaults.items()])
        attrs.append(f'look-controls="{look_str}"')
        
        # WASD Controls
        wasd_defaults = {
            'enabled': 'true',
            'acceleration': '65',
            'fly': 'false',
            'reverseWASD': 'false',
            'adEnabled': 'true',
            'wsEnabled': 'true',
            'qsEnabled': 'true',
        }
        
        if wasd_controls_options:
            wasd_defaults.update(wasd_controls_options)
        
        wasd_str = '; '.join([f'{k}: {v}' for k, v in wasd_defaults.items()])
        attrs.append(f'wasd-controls="{wasd_str}"')
    
    # Cursor (for interaction)
    if enable_cursor:
        cursor_defaults = {
            'enabled': 'true',
            'rayOrigin': 'mouse',
            'fuse': 'false',
            'fuseTimeout': '1500',
            'showLine': 'false',
            'downEvents': '[]',
            'upEvents': '[]',
            'worldThrottledEvents': 'true',
        }
        
        if cursor_options:
            cursor_defaults.update(cursor_options)
        
        cursor_str = '; '.join([f'{k}: {v}' for k, v in cursor_defaults.items()])
        
        # Add cursor as child entity (attached to camera for gaze/click interaction)
        cursor_entity = f'<a-entity cursor="{cursor_str}" position="0 0 -1" geometry="primitive: ring; radiusInner: 0.02; radiusOuter: 0.03" material="color: white; shader: flat; opacity: 0.5"></a-entity>'
        
        # Wrap camera with cursor
        attrs.append('id="camera"')
        attrs.append('name="main-camera"')
        
        element = f"<a-entity {' '.join(attrs)}>{cursor_entity}</a-entity>"
        return element
    
    # Name and ID
    attrs.append(f'id="{obj.name}"')
    attrs.append(f'name="{obj.name}"')
    
    element = f"<a-camera {' '.join(attrs)}></a-camera>"
    
    return element


def export_custom_css(export_dir, custom_css=""):
    """Export custom CSS file.
    
    Custom CSS allows styling the A-Frame scene and UI elements.
    """
    default_css = """/* A-Frame Scene Custom Styles */

/* Scene container styles */
.a-scene {
  /* Ensure full viewport */
}

/* Remove VR button styling if needed */
.a-enter-vr {
  /* Customize VR button */
}

/* Hide stats panel if desired */
a-scene[stats="false"] {
  /* stats are not enabled */
}

/* Custom entity styling */
.custom-entity {
  /* Add custom classes for specific objects */
}

/* Animation overlay styles */
.animation-overlay {
  pointer-events: none;
}

/* Loading screen customization */
.a-loader {
  background: #000;
}

/* UI overlay styles */
.ui-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999;
}

.ui-overlay > * {
  pointer-events: auto;
}

/* Interactive element states */
.interactive:hover {
  /* Hover effect for interactive elements */
}

.interactive:active {
  /* Active/click effect */
}

/* Disable default cursor in VR */
.a-grab-cursor {
  /* Customize grab cursor */
}

/* Loading screen */
.a-loading-screen {
  background-color: #212121;
}

.a-loading-screen .loader {
  border-color: #ff6b6b transparent transparent transparent;
}
"""
    
    # Use custom CSS if provided, otherwise use default
    css_content = custom_css if custom_css else default_css
    
    output_path = os.path.join(export_dir, "style.css")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    return output_path


def generate_material_mixins():
    """Generate A-Frame mixin definitions for materials."""
    if not MATERIAL_LIBRARY:
        return ""
    
    mixins = []
    for mat_id, mat_data in MATERIAL_LIBRARY.items():
        props_str = '; '.join(mat_data['props'])
        shader = mat_data.get('shader', 'standard')
        mixin = f'    <a-mixin id="{mat_id}" material="shader: {shader}; {props_str}"></a-mixin>'
        mixins.append(mixin)
    
    return '\n'.join(mixins)


def generate_texture_assets():
    """Generate A-Frame asset items for textures."""
    if not TEXTURE_LIBRARY:
        return ""
    
    assets = []
    for tex_id, tex_data in TEXTURE_LIBRARY.items():
        image = tex_data.get('image')
        if image:
            # Get the filename from the image
            filename = os.path.basename(image.filepath) if image.filepath else f"{tex_id}.jpg"
            asset = f'        <img id="{tex_id}" src="assets/{filename}" crossorigin="anonymous">'
            assets.append(asset)
    
    return '\n'.join(assets)


def export_scene_to_html(
    context,
    export_dir,
    report,
    include_environment=True,
    environment_preset='yavapai',
    export_lights=True,
    shadows_enabled=True,
    camera_as_look_controls=True,
    enable_cursor=False,
    aframe_version='1.7.1',
    fog_enabled=False,
    fog_color='#97a288',
    fog_density=0.01,
    include_custom_css=False,
    custom_css="",
    use_mixins=True,
    sky_color='#87CEEB'
):
    """Export the Blender scene to A-Frame HTML."""
    
    # Clear material library for fresh export
    global MATERIAL_LIBRARY
    MATERIAL_LIBRARY = {}
    
    # Clear texture library for fresh export
    global TEXTURE_LIBRARY
    TEXTURE_LIBRARY = {}
    
    try:
        scene = context.scene
    except Exception as e:
        report({'ERROR'}, f"Failed to get scene: {e}")
        return None
    
    # Get all visible objects - with error handling
    try:
        objects = [obj for obj in scene.objects if obj.visible_get()]
    except Exception as e:
        report({'WARNING'}, f"Error getting visible objects: {e}")
        objects = []
    
    # Separate cameras and regular objects
    cameras = [obj for obj in objects if obj.type == 'CAMERA']
    regular_objects = [obj for obj in objects if obj.type != 'CAMERA']
    
    # Build the A-Frame scene content
    scene_elements = []
    
    # Add objects - with error handling per object
    for obj in regular_objects:
        try:
            element = convert_object_to_aframe(obj, export_lights, shadows_enabled)
            if element:
                scene_elements.append(element)
        except Exception as e:
            print(f"Error converting object {obj.name}: {e}")
            continue
    
    # Add camera (use active camera or first camera)
    active_camera = scene.camera
    camera_added = False
    
    if active_camera:
        try:
            camera_element = convert_camera_to_aframe(
                active_camera, 
                use_as_look_controls=camera_as_look_controls,
                enable_cursor=enable_cursor
            )
            if camera_element:
                scene_elements.append('<!-- Camera -->')
                scene_elements.append(camera_element)
                camera_added = True
        except Exception as e:
            print(f"Error converting active camera: {e}")
    
    # If no camera was added, create a default camera
    if not camera_added and cameras:
        # Use first available camera
        try:
            camera_element = convert_camera_to_aframe(
                cameras[0], 
                use_as_look_controls=camera_as_look_controls,
                enable_cursor=enable_cursor
            )
            if camera_element:
                scene_elements.append('<!-- Camera -->')
                scene_elements.append(camera_element)
                camera_added = True
        except Exception as e:
            print(f"Error converting camera: {e}")
    
    # If still no camera, add a default camera
    if not camera_added:
        # Add a default camera at a reasonable viewing position
        scene_elements.append('<!-- Camera -->')
        default_camera = '<a-camera position="0 1.6 5" look-controls wasd-controls></a-camera>'
        scene_elements.append(default_camera)
    
    # Add ambient light to ensure scene isn't too dark if no other lights
    # This is a fallback - users should export their lights for better control
    ambient_light = '<!-- Lights -->\n<a-entity light="type: ambient; intensity: 0.4; color: #ffffff"></a-entity>'
    scene_elements.insert(0, ambient_light)
    
    # Build fog attribute
    fog_attr = ""
    if fog_enabled:
        # Fog types: exponential, linear
        fog_attr = f'fog="type: exponential; color: {fog_color}; density: {fog_density}"'
    
    # Generate material mixins
    mixins_html = generate_material_mixins()
    
    # Generate texture assets
    texture_assets_html = generate_texture_assets()
    
    # Environment component
    env_element = ""
    if include_environment and environment_preset != 'none':
        ground_color = "#445"
        # Generate environment entity with a-sky as child element
        # Use "distant" lighting to simulate sun, but allow scene lights to work
        env_element = f'''
    <a-entity environment="preset: {environment_preset}; groundColor: {ground_color}; skyColor: {sky_color}; grid: none; skyType: atmosphere; lighting: distant">
      <a-entity class="environment" position="" light="" visible=""></a-entity>
      <a-entity rotation="" class="environmentGround environment" visible="" scale="" shadow=""></a-entity>
      <a-entity class="environmentDressing environment" visible=""></a-entity>
      <a-sky radius="200" theta-length="110" class="environment" material="" visible="" geometry="" scale=""></a-sky>
    </a-entity>'''
    
    # Combine all elements
    scene_content = '\n    '.join(scene_elements)
    
    # CSS link
    css_link = ""
    if include_custom_css:
        css_link = '  <link rel="stylesheet" href="style.css">'
    
    # Generate the HTML
    # Add background color to scene from UI settings
    background_attr = f'background="color: {sky_color}"'
    
    html_content = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Blender Scene Export</title>
  <meta name="theme-color" content="#ff6b6b">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="manifest" href="manifest.json">
{css_link}
  <script src="https://aframe.io/releases/{aframe_version}/aframe.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.2/anime.min.js"></script>
  <script src="https://unpkg.com/aframe-environment-component@1.3.3/dist/aframe-environment-component.min.js"></script>
  <!-- Additional A-Frame extras -->
  <script src="https://unpkg.com/aframe-extras@7.0.0/dist/aframe-extras.min.js"></script>
</head>
<body>
 <!-- Scene -->
  <a-scene 
    stats="false" 
    {background_attr}
    keyboard-shortcuts="enterVR: false; screenshot: true; record: false" 
    screenshot="fps: 60; quality: 92" 
    xr-mode-ui="enabled: true" 
    device-orientation-permission-ui="enabled: true" 
    renderer="colorManagement: true; physicallyCorrectLights: true; antialias: true; alpha: false; powerPreference: high-performance"
    {fog_attr}>
    
    <!-- Material Mixins and Texture Assets -->
    <a-assets>
{mixins_html}

{texture_assets_html}
    </a-assets>
    
    <!-- Scene Objects (Shapes) -->
    {scene_content}
    
    <!-- Environment -->
    {env_element}
    
    <!-- UI -->
    <canvas class="a-canvas a-grab-cursor a-mouse-cursor-hover" data-aframe-canvas="true" data-engine="three.js r173" width="1056" height="1576"></canvas></a-scene>
</body>
</html>'''
    
    # Write to file
    output_path = os.path.join(export_dir, "index.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    report({'INFO'}, f"Exported index.html to {output_path}")
    
    # Export custom CSS if enabled
    if include_custom_css:
        export_custom_css(export_dir, custom_css)
        report({'INFO'}, f"Exported style.css to {os.path.join(export_dir, 'style.css')}")
    
    return output_path


def export_manifest(export_dir, project_name, theme_color, background_color):
    """Export the web app manifest."""
    
    manifest = {
        "name": f"{project_name} - VR Experience",
        "short_name": project_name,
        "description": "A-Frame VR experience exported from Blender",
        "start_url": "./index.html",
        "display": "standalone",
        "background_color": background_color,
        "theme_color": theme_color,
        "orientation": "any",
        "icons": [
            {
                "src": "assets/icon-192.svg",
                "sizes": "192x192",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            },
            {
                "src": "assets/icon-512.svg",
                "sizes": "512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ],
        "categories": [
            "entertainment",
            "games"
        ],
        "lang": "en",
        "scope": "./",
        "prefer_related_applications": False
    }
    
    output_path = os.path.join(export_dir, "manifest.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return output_path


def export_service_worker(export_dir, project_name):
    """Export the service worker file."""
    
    cache_name = f"{project_name.replace(' ', '-').lower()}-v1"
    
    sw_content = f'''// Service Worker for {project_name} VR Experience
const CACHE_NAME = '{cache_name}';
const urlsToCache = [
  './',
  './index.html',
  './manifest.json',
  './style.css'
];

// Install event - cache resources
self.addEventListener('install', event => {{
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {{
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      }})
      .catch(err => {{
        console.log('Cache install failed:', err);
      }})
  );
}});

// Activate event - clean up old caches
self.addEventListener('activate', event => {{
  event.waitUntil(
    caches.keys().then(cacheNames => {{
      return Promise.all(
        cacheNames.map(cacheName => {{
          if (cacheName !== CACHE_NAME) {{
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }}
        }})
      );
    }})
  );
}});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {{
  event.respondWith(
    caches.match(event.request)
      .then(response => {{
        // Return cached version or fetch from network
        if (response) {{
          return response;
        }}
        return fetch(event.request);
      }})
      .catch(() => {{
        // If both fail, return offline page for navigation requests
        if (event.request.mode === 'navigate') {{
          return caches.match('./index.html');
        }}
      }})
  );
}});
'''
    
    output_path = os.path.join(export_dir, "sw.js")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sw_content)
    
    return output_path


def export_object_as_glb(context, obj, export_dir, report):
    """Export a complex Blender object as GLB file for A-Frame.
    
    This is used for objects that cannot be represented as primitives.
    """
    import bpy
    
    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select the object
    obj.select_set(True)
    context.view_layer.objects.active = obj
    
    # Create a temporary collection for export
    temp_collection = bpy.data.collections.new("temp_export")
    bpy.context.scene.collection.children.link(temp_collection)
    temp_collection.objects.link(obj)
    
    # Remove from other collections
    for coll in obj.users_collection:
        if coll != temp_collection:
            coll.objects.unlink(obj)
    
    # Export as GLB
    glb_filename = f"{obj.name}.glb"
    glb_path = os.path.join(export_dir, "assets", glb_filename)
    
    try:
        bpy.ops.export_scene.gltf(
            filepath=glb_path,
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_materials='EXPORT',
            export_colors=True,
            export_cameras=False,
            export_lights=False,
        )
        report({'INFO'}, f"Exported {obj.name} as GLB")
        return glb_path
    except Exception as e:
        report({'ERROR'}, f"Failed to export {obj.name} as GLB: {e}")
        return None
    finally:
        # Restore original collections
        for coll in bpy.data.collections:
            if coll != temp_collection and obj not in coll.objects:
                try:
                    coll.objects.link(obj)
                except:
                    pass
        
        # Remove temp collection
        bpy.data.collections.remove(temp_collection)


def convert_sound_to_aframe(obj):
    """Convert Blender sound to A-Frame sound component.
    
    Supports: autoplay, loop, volume, positional, refDistance, rolloffFactor
    """
    # Check for sound strip in video sequence editor or speaker object
    if obj.type == 'SPEAKER':
        speaker = obj.data
        
        sound_attrs = []
        
        # Source file
        if speaker.sound:
            sound_attrs.append(f'src: {speaker.sound.filepath}')
        
        # Volume
        sound_attrs.append(f'volume: {speaker.volume:.2f}')
        
        # Loop
        sound_attrs.append(f'loop: {speaker.loop}')
        
        # Autoplay
        sound_attrs.append(f'autoplay: {speaker.autoplay}')
        
        # Positional audio settings
        sound_attrs.append('positional: true')
        sound_attrs.append(f'refDistance: 1')
        sound_attrs.append(f'rolloffFactor: 1')
        
        sound_str = '; '.join(sound_attrs)
        return f'sound="{sound_str}"'
    
    return ""


def convert_animation_to_aframe(obj):
    """Convert Blender animation to A-Frame animation component.
    
    Supports: property, to, dur, easing, loop, dir, delay, elasticity
    """
    if not obj.animation_data or not obj.animation_data.action:
        return ""
    
    action = obj.animation_data.action
    
    # Get animation properties
    animations = []
    
    for fcurve in action.fcurves:
        # Get the property path
        data_path = fcurve.data_path
        array_index = fcurve.array_index
        
        # Map to A-Frame property
        aframe_property = data_path
        if 'location' in data_path:
            if array_index == 0:
                aframe_property = 'position.x'
            elif array_index == 1:
                aframe_property = 'position.z'  # Y-up conversion
            elif array_index == 2:
                aframe_property = 'position.y'
        elif 'rotation_euler' in data_path:
            if array_index == 0:
                aframe_property = 'rotation.x'
            elif array_index == 1:
                aframe_property = 'rotation.z'
            elif array_index == 2:
                aframe_property = 'rotation.y'
        elif 'scale' in data_path:
            if array_index == 0:
                aframe_property = 'scale.x'
            elif array_index == 1:
                aframe_property = 'scale.z'
            elif array_index == 2:
                aframe_property = 'scale.y'
        
        # Get keyframe values
        if fcurve.keyframe_points:
            start = fcurve.keyframe_points[0].co.x
            end = fcurve.keyframe_points[-1].co.x
            dur = (end - start) * 1000  # Convert to ms
            
            # Get start and end values
            start_val = fcurve.keyframe_points[0].co.y
            end_val = fcurve.keyframe_points[-1].co.y
            
            anim_str = f'property: {aframe_property}; from: {start_val:.4f}; to: {end_val:.4f}; dur: {dur:.0f}; easing: easeInOutQuad; loop: true'
            animations.append(anim_str)
    
    return animations


def convert_video_to_aframe(obj):
    """Convert Blender image with video to A-Frame video component."""
    # Check for image sequence or video texture
    # This would need to check material nodes for movie files
    return ""


def convert_physics_to_aframe(obj, physics_type='static'):
    """Convert Blender object to physics body.
    
    physics_type: 'static', 'dynamic', or 'kinematic'
    """
    attrs = []
    
    if physics_type == 'static':
        attrs.append('static-body')
    elif physics_type == 'dynamic':
        attrs.append('dynamic-body')
        attrs.append('mass: 1')
    elif physics_type == 'kinematic':
        attrs.append('kinematic-body')
    
    # Get collision shape from object
    if obj.type == 'MESH':
        # Use mesh for collision
        pass
    
    return ' '.join(attrs)


def get_required_component_scripts(include_environment=True, include_physics=False, include_particles=False):
    """Get the list of required A-Frame component scripts."""
    scripts = [
        f'  <script src="https://aframe.io/releases/1.7.1/aframe.min.js"></script>',
        f'  <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.2/anime.min.js"></script>',
    ]
    
    if include_environment:
        scripts.append(f'  <script src="{AFRAME_COMPONENT_SCRIPTS["environment"]}"></script>')
    
    scripts.append(f'  <script src="{AFRAME_COMPONENT_SCRIPTS["extras"]}"></script>')
    
    if include_physics:
        scripts.append(f'  <script src="{AFRAME_COMPONENT_SCRIPTS["physics"]}"></script>')
    
    if include_particles:
        scripts.append(f'  <script src="{AFRAME_COMPONENT_SCRIPTS["particle-system"]}"></script>')
    
    return '\n'.join(scripts)
