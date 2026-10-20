"""Check saved source and GLB, render sampled native animation for review."""
import bpy, json, sys, struct, importlib.util, math
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
STYLE=HERE.parent.parent
OUT=STYLE/'Exports'/'CM-T01'
spec=importlib.util.spec_from_file_location('cm_build',HERE/'build_turret.py')
build=importlib.util.module_from_spec(spec); spec.loader.exec_module(build)
part_checks={}
bpy.ops.wm.open_mainfile(filepath=str(STYLE/'Parts'/'cm-handle-folding'/'cm-handle-folding.blend'))
bpy.context.scene.frame_set(1)
feet={o.name:o.matrix_world.translation.copy() for o in bpy.context.scene.objects if 'hinge mounting shoe' in o.name}
bpy.context.scene.frame_set(31); bpy.context.view_layer.update()
assert abs(bpy.context.scene.objects['fold_joint'].rotation_euler.y-math.radians(75))<1e-5
assert all((bpy.context.scene.objects[name].matrix_world.translation-pos).length<1e-6 for name,pos in feet.items())
part_checks['folding_handle']='hinge reaches 75 degrees while mounting feet stay fixed'
bpy.ops.wm.open_mainfile(filepath=str(STYLE/'Parts'/'cm-barrel'/'cm-barrel.blend'))
brake=bpy.context.scene.objects['ported octagonal muzzle brake'].evaluated_get(bpy.context.evaluated_depsgraph_get())
assert not brake.ray_cast(Vector((-.65,-2.73,0)),Vector((1,0,0)),distance=1.30)[0]
assert brake.ray_cast(Vector((-.65,-2.73,.25)),Vector((1,0,0)),distance=1.30)[0]
part_checks['barrel_ports']='ray passes through side vent, adjacent structural wall remains solid'
bpy.ops.wm.open_mainfile(filepath=str(HERE/'CM-T01.blend'))
scene=bpy.context.scene
assembly=json.loads((HERE/'assembly.json').read_text(encoding='utf-8'))
assert len(assembly['instances'])==22
assert assembly['version']=='2.0.0'
assert not any(token in o.name for o in scene.objects for token in ('side identification','service stencil','side SS marking','side brand'))
assert scene.objects['joint_elevation'].parent==scene.objects['joint_yaw']
assert scene.objects['muzzle_left'].parent==scene.objects['barrel_left']
assert scene.objects['barrel_left'].parent==scene.objects['joint_elevation']
report={'native':{},'glb':{},'part_checks':part_checks,'notes':['Source/GLB checks and rendered poses; no live game acceptance.']}
assert scene.objects['collar_left'].parent==scene.objects['barrel_left']
assert scene.objects['collar_right'].parent==scene.objects['barrel_right']
for pid in build.BUILDERS:
    p=STYLE/'Parts'/pid
    m=json.loads((p/'part.json').read_text(encoding='utf-8'))
    assert (p/m['source']).is_file() and (p/'preview.png').is_file()
    assert m['materials'] and m['sockets']
    for socket in m['sockets']+m['functional_points']:
        assert abs(Vector(socket['forward']).length-1)<1e-6
        assert abs(Vector(socket['up']).length-1)<1e-6
        assert abs(Vector(socket['forward']).dot(Vector(socket['up'])))<1e-6
    for dep in m['dependencies']: assert (p/dep).is_file()

packed={}
for o in scene.objects:
    if o.type!='MESH' or o.name=='Studio floor': continue
    for slot in o.material_slots:
        if not slot.material or not slot.material.use_nodes: continue
        for node in slot.material.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                assert node.image.packed_file is not None, node.image.name
                packed[node.image.name]=list(node.image.size)
base=scene.objects['deck'].matrix_world.copy()
poses=[]
for f in [1,31,44,53,61,91,120]:
    scene.frame_set(f); bpy.context.view_layer.update()
    assert (scene.objects['deck'].matrix_world.translation-base.translation).length<1e-6
    points={}
    for side in ['left','right']:
        obj=scene.objects['muzzle_'+side]
        expected=scene.objects['barrel_'+side].matrix_world@Vector((0,-3.40,0))
        assert (obj.matrix_world.translation-expected).length<1e-5
        assert obj.matrix_world.translation.z>0
        points[side]=list(obj.matrix_world.translation)
    if f==44: assert abs(scene.objects['barrel_left'].location.y-(-1.404+.14))<1e-5
    if f==53: assert abs(scene.objects['barrel_right'].location.y-(-1.404+.14))<1e-5
    poses.append({'frame':f,'muzzles':points})
report['native']={'part_files_verified':len(build.BUILDERS),'instances':len(assembly['instances']),'packed_textures':packed,'poses':poses,'hierarchy':'verified','recoil_endpoints':'verified'}
scene.frame_set(1)
cam=scene.camera; cam.location=(7,-10,6.8)
cam.rotation_euler=(Vector((0,-.9,1.7))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=8.7
scene.render.resolution_x=640; scene.render.resolution_y=640
scene.cycles.samples=16; scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type!='CPU'
    if any(d.use for d in prefs.devices): scene.cycles.device='GPU'
except Exception: pass
frames=[1,7,13,19,25,31,37,42,44,48,51,53,57,61,67,73,79,85,91,97,103,109,115,120]
folder=OUT/'animation-frames'; folder.mkdir(parents=True,exist_ok=True)
for f in frames:
    scene.frame_set(f); scene.render.filepath=str(folder/f'{f:03d}.png')
    bpy.ops.render.render(write_still=True)
    print('ANIMATION_FRAME '+str(f),flush=True)
build.js(OUT/'animation-frames.json',{'frames':frames,'fps':30,'render':'Cycles 16 samples, 640px, denoised'})

# Inspect binary references, combined clip and a real Blender re-import.
blob=(OUT/'CM-T01.glb').read_bytes(); magic,version,size=struct.unpack_from('<4sII',blob)
assert magic==b'glTF' and version==2 and size==len(blob)
n,kind=struct.unpack_from('<II',blob,12)
doc=json.loads(blob[20:20+n]); assert kind==0x4e4f534a
assert len(doc['animations'][0]['channels'])==4
assert all('bufferView' in im for im in doc['images'])
assert not any('uri' in buf for buf in doc['buffers'])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'CM-T01.glb'))
bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
native_check=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
assert len(meshes)==native_check['mesh_objects']
lo,hi=build.bounds(meshes)
native=assembly['rest_bounds']
assert (lo-Vector(native['min'])).length<.003,(list(lo),native['min'])
assert (hi-Vector(native['max'])).length<.003,(list(hi),native['max'])
report['glb']={'reimport_meshes':len(meshes),'embedded_images':len(doc['images']),'materials':len(doc['materials']),
    'animations':[{'name':a['name'],'channels':len(a['channels'])} for a in doc['animations']],
    'rest_bounds_match_native':True,'self_contained':True,'bytes':len(blob)}
build.js(OUT/'review.json',report)
print('REVIEW_PASSED',flush=True)
