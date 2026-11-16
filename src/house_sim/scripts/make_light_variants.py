"""Generate lighting variants of the house world (domain randomisation)."""
import os
import xml.etree.ElementTree as ET

WORLDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds')
SRC = os.path.join(WORLDS, 'small_house.world')

# scale:   multiplier for indoor lamp brightness
# color:   RGB tint of the lamps
# ambient: global ambient light (0 = black, 1 = full)
# sun:     direction of sunlight through the windows, or None = no sun
VARIANTS = {
    'dim':      dict(scale=0.4, color=(1.0, 1.0, 1.0),  ambient=0.15, sun=None),
    'warm':     dict(scale=1.0, color=(1.0, 0.8, 0.55), ambient=0.3,  sun=None),
    'daylight': dict(scale=0.6, color=(1.0, 1.0, 1.0),  ambient=0.5,  sun=(-0.5, 0.3, -0.8)),
}


def fmt(values):
    return ' '.join(f'{v:.3f}' for v in values)


for name, v in VARIANTS.items():
    tree = ET.parse(SRC)
    world = tree.getroot().find('world')

    # 1. Scale and tint every lamp
    for light in world.findall('light'):
        d = light.find('diffuse')
        r, g, b, a = map(float, d.text.split())
        cr, cg, cb = v['color']
        d.text = fmt((r * v['scale'] * cr, g * v['scale'] * cg, b * v['scale'] * cb, a))

    # 2. Global ambient light
    scene = world.find('scene')
    if scene is None:
        scene = ET.SubElement(world, 'scene')
    ambient = scene.find('ambient')
    if ambient is None:
        ambient = ET.SubElement(scene, 'ambient')
    ambient.text = fmt((v['ambient'],) * 3 + (1.0,))

    # 3. Optional sun (the ceiling blocks it, so it only enters through windows)
    if v['sun'] is not None:
        sun = ET.SubElement(world, 'light', name='sun', type='directional')
        ET.SubElement(sun, 'cast_shadows').text = '1'
        ET.SubElement(sun, 'pose').text = '0 0 10 0 0 0'
        ET.SubElement(sun, 'diffuse').text = '0.9 0.9 0.85 1'
        ET.SubElement(sun, 'specular').text = '0.2 0.2 0.2 1'
        ET.SubElement(sun, 'direction').text = fmt(v['sun'])

    # 4. Separate output folder for this variant's images
    world.find(".//sensor[@name='boundingbox_camera']/camera/save/path").text = \
        f'/ros2_ws/datasets/raw_{name}'

    out = os.path.join(WORLDS, f'small_house_{name}.world')
    tree.write(out, encoding='utf-8', xml_declaration=True)
    print(f'Wrote {out}')
