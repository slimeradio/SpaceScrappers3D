"""Review independent floor parts and fitted Blender sources without modifying them."""
from pathlib import Path
import sys,math
sys.path.insert(0,str(Path(__file__).resolve().parent))
from floor_fit import ROOT,read
import bpy
from mathutils import Vector

def preview(source,target,angle=False):
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene;scene.frame_set(1)
    for o in list(scene.objects):
        if o.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
    objects=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
    pts=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);center=(lo+hi)/2;extent=max(hi.x-lo.x,hi.y-lo.y,hi.z-lo.z)
    bpy.ops.object.camera_add(location=center+Vector((extent*.9,-extent*1.2,extent*1.5)) if angle else center+Vector((0,0,max(5,extent*2))))
    camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=extent*(1.8 if angle else 1.12);scene.camera=camera
    bpy.ops.object.light_add(type='AREA',location=center+Vector((-extent,-extent,extent*2+2)));lamp=bpy.context.object;lamp.data.energy=700;lamp.data.shape='DISK';lamp.data.size=extent*2;lamp.rotation_euler=(center-lamp.location).to_track_quat('-Z','Y').to_euler()
    scene.world=bpy.data.worlds.new('Floor review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.film_transparent=True
    scene.use_nodes=False;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(target);target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
    print('PREVIEW_OK',target,flush=True)

for fid in ('MA-FLOOR-rect-1x1','MA-FLOOR-rect-2x3','MA-FLOOR-wedge-1x2'):
    preview(ROOT/'Parts'/fid/(fid+'.blend'),ROOT/'Parts'/fid/'Previews/top.png')
    preview(ROOT/'Parts'/fid/(fid+'.blend'),ROOT/'Parts'/fid/'Previews/perspective.png',True)
for bid in ('MA-A03','MA-I02','MA-W06','MA-T01','MA-D03','MA-E02','MA-SP04'):
    preview(ROOT/'Blocks'/bid/(bid+'.blend'),ROOT/'Blocks'/bid/'Previews/floor-top.png')
    preview(ROOT/'Blocks'/bid/(bid+'.blend'),ROOT/'Blocks'/bid/'Previews/floor-perspective.png',True)
