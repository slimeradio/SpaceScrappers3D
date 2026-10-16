import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
for offset,rid in zip([-5.3,0,5.3],['MF-01_Aureole','MF-02_Kurenai','MF-03_Obsidian']):
    with bpy.data.libraries.load(str(ROOT/'Blocks'/rid/(rid+'.blend')),link=False) as (src,dst): dst.scenes=[src.scenes[0]]
    imported=dst.scenes[0]
    for c in imported.collection.children:
        scene.collection.children.link(c)
        for o in c.objects:
            if o.parent is None: o.location.x+=offset
    bpy.data.scenes.remove(imported)
    bpy.ops.object.text_add(location=(offset,-.8,-.2),rotation=(1.570796,0,0))
    text=bpy.context.object; text.data.body=rid.split('_')[1].upper(); text.data.align_x='CENTER'; text.data.size=.32; text.data.extrude=.001
bpy.ops.mesh.primitive_plane_add(size=200); floor=bpy.context.object
m=bpy.data.materials.new('Ground'); m.diffuse_color=(.025,.035,.05,1); m.use_nodes=True
shader=m.node_tree.nodes.get('Principled BSDF'); shader.inputs['Base Color'].default_value=(.025,.035,.05,1); shader.inputs['Roughness'].default_value=.45; shader.inputs['Metallic'].default_value=.2; floor.data.materials.append(m)
floor.location.z=-.22
scene.world=bpy.data.worlds.new('Gallery world'); scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.23,1)
for p,e,size in [((2,-8,13),5000,10),((-9,-4,8),3500,8),((2,6,12),5500,9)]:
    bpy.ops.object.light_add(type='AREA',location=p); o=bpy.context.object; o.data.energy=e; o.data.size=size; o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(6,-27,10)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=17.9; scene.camera=cam
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True; scene.render.resolution_x=2100; scene.render.resolution_y=1100; scene.render.resolution_percentage=100; scene.view_settings.view_transform='AgX'; scene.render.filepath=str(ROOT/'lineup.png')
bpy.ops.render.render(write_still=True)
print('GALLERY_OK')
