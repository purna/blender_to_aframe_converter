# Blender to A-Frame Converter

A Blender addon that exports Blender scenes to A-Frame HTML format for WebVR/WebXR experiences.

## Features

- **Primitive Shapes**: Automatically converts Blender meshes to A-Frame primitives (box, sphere, cylinder, cone, torus, plane, circle)
- **Text Objects**: Export Blender text objects as `<a-text>` elements
- **Lighting**: Export Blender lights with full properties (type, color, intensity)
- **Cameras**: Export Blender cameras with look-controls and WASD movement
- **Environment**: Built-in environment presets (yavapai, forest, moon, etc.)
- **Materials**: Converts Principled BSDF materials to A-Frame materials
- **Sky Colors**: Multiple sky color options
- **Fog**: Optional fog effects
- **Custom CSS**: Add custom styling
- **Web App**: Export as a PWA with manifest and service worker

## Installation

1. Download or clone this repository
2. Open Blender
3. Go to **Edit > Preferences > Add-ons**
4. Click **Install** and select the `zip` file
5. Enable the addon by checking the box next to "Blender to A-Frame Converter"

## Usage

### Basic Export

1. Create or open a Blender scene
2. Add primitive objects (cubes, spheres, cylinders, etc.)
3. Optionally add:
   - Text objects (will become `<a-text>`)
   - Lights (Point, Sun, Spot)
   - Cameras
4. Go to **File > Export > A-Frame (.html)**
5. Configure export settings (see below)
6. Choose export location and click **Export A-Frame**

### Export Settings

#### Project Settings
- **Project Name**: Name for your project
- **Export as ZIP**: Bundle all files into a ZIP archive

#### A-Frame Settings
- **A-Frame Version**: Select which A-Frame version to use (default: 1.7.1)
- **Include Custom CSS**: Add custom stylesheet

#### Environment
- **Include Environment**: Enable/disable the environment component
- **Environment Preset**: Choose from presets like:
  - arches, contact, default, eos, forest, goldmine, goaland, joshuatree, moon, osiris, poison, starry, threetowers, touch, trek, yavapai
- **Sky Color**: Select background/sky color

#### Fog
- **Enable Fog**: Add atmospheric fog
- **Fog Color**: Choose fog color
- **Fog Density**: Set fog density (0.01 default)

#### Advanced
- **Export Lights**: Include light objects
- **Enable Shadows**: Enable shadow casting
- **Camera Controls**: Configure look and WASD controls
- **Enable Cursor**: Add VR cursor to camera

## Supported Blender Objects

| Blender Object | A-Frame Element |
|----------------|-----------------|
| Mesh (Cube) | `<a-box>` |
| Mesh (Sphere) | `<a-sphere>` |
| Mesh (Cylinder) | `<a-cylinder>` |
| Mesh (Cone) | `<a-cone>` |
| Mesh (Torus) | `<a-torus>` |
| Mesh (Plane) | `<a-plane>` |
| Mesh (Circle) | `<a-circle>` |
| Text | `<a-text>` |
| Point Light | `<a-entity light="type: point">` |
| Sun Light | `<a-entity light="type: directional">` |
| Spot Light | `<a-entity light="type: spot">` |
| Camera | `<a-camera>` |

## Output Files

The exporter creates:
- `index.html` - Main A-Frame scene
- `style.css` - Custom styles (if enabled)
- `manifest.json` - Web app manifest (for PWA)
- `sw.js` - Service worker (for offline support)
- `assets/` - Folder for exported assets

## Viewing Your Export

### Local Server (Recommended)
The exported HTML file needs to be served via a local web server to work properly due to browser security restrictions:

1. Open a terminal in the export folder
2. Run: `python -m http.server 8000`
3. Open browser to `http://localhost:8000`

Or use the "Start Local Server" option in the export dialog.

### File Protocol (Limited)
You can also open the HTML file directly in a browser, but some features (like external assets) may not work due to CORS restrictions.

## Requirements

- Blender 3.0 or higher
- Web browser with WebGL support
- For VR: WebXR-compatible browser and headset

## Troubleshooting

### Objects not appearing
- Make sure objects are visible in Blender
- Check that objects are not in a hidden collection

### Materials not exporting
- Use Principled BSDF shader nodes
- Ensure materials are assigned to objects

### Lights not working
- Check that "Export Lights" is enabled in settings
- Verify light intensity is set appropriately

### Console errors
- Open browser developer tools (F12)
- Check for JavaScript errors
- Ensure you're running via a local server, not file://


## Other
This is an alternative Blender add-on simplifies the process of exporting your 3D scenes into interactive web experiences using A-Frame, a popular web framework for building virtual reality (VR) and augmented reality (AR) experiences. It creates a  GLB (binary glTF) file for the scene and an HTML file that displays the objects in a scene. It is more orginal to the Blender file but I just wanted something that could be editable in html for my students.
- [Blender to A-Frame Exporter ](https://daydevthailand.gumroad.com/l/aframeexporter)

## License

MIT License

## Credits

- [A-Frame](https://aframe.io/) - WebVR framework
- [A-Frame Environment Component](https://github.com/c-frame/aframe-environment-component) - Environment presets
