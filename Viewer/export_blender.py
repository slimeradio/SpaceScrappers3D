"""Generate viewer derivatives only; never save changes to authoring .blend files.
Run with Blender --background --python Viewer/export_blender.py.
"""
import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def export(source, target):
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    scene.frame_set(scene.frame_start)
    # Preserve the animated instance parent and materialize its collection beneath it.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in scene.objects:
        if obj.instance_type == 'COLLECTION':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    if bpy.context.selected_objects:
        bpy.ops.object.duplicates_make_real(use_base_parent=True, use_hierarchy=True)
    # Export visible geometry and transform parents; omit camera rigs and authoring markers.
    bpy.ops.object.select_all(action='DESELECT')
    keep = set()
    for obj in scene.objects:
        if obj.type in {'MESH', 'FONT', 'CURVE'} and not obj.hide_render and not obj.name.startswith('Studio '):
            keep.add(obj)
            parent = obj.parent
            while parent:
                keep.add(parent)
                parent = parent.parent
    for obj in keep:
        obj.hide_set(False)
        obj.select_set(True)
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', use_selection=True,
        export_apply=True, export_animations=True, export_animation_mode='SCENE',
        export_frame_range=True, export_force_sampling=True, export_cameras=False,
        export_lights=False, export_extras=True)
    print('VIEWER_EXPORTED ' + str(target), flush=True)

if __name__ == '__main__':
    for style in ['MilitaryArmor', 'ChunkyModular']:
        base = ROOT / 'Projects/SS' / style
        out = base / 'Exports/Viewer'
        if style == 'MilitaryArmor':
            export(base / 'Blocks/MA-T01/MA-T01.blend', out / 'MA-T01.glb')
        for source in sorted((base / 'Parts').glob('*/*.blend')):
            export(source, out / (source.stem + '.glb'))
    print('VIEWER_EXPORT_COMPLETE', flush=True)
