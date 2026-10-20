import bpy,json,sys,math,tempfile,struct
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly

for bid in ['MA-W01','MA-W02']:
    folder=ROOT/'Blocks'/bid
    data=json.loads((folder/'assembly.json').read_text(encoding='utf8'))
    validation=json.loads((folder/'validation.json').read_text(encoding='utf8'))
    part_checks=[]
    for pid in sorted(set(i['part_id'] for i in data['instances'])):
        part_folder=ROOT/'Parts'/pid
        pd=json.loads((part_folder/'part.json').read_text(encoding='utf8'))
        bpy.ops.wm.open_mainfile(filepath=str(part_folder/(pid+'.blend')))
        meshes=[o for o in bpy.data.collections[pid].objects if o.type=='MESH']
        check=dict(id=pid,reopened=True,mesh_count=len(meshes),materials_assigned=all(len(o.data.materials)>0 for o in meshes),degenerate_faces=sum(p.area<1e-10 for o in meshes for p in o.data.polygons),dependency_libraries=[l.filepath for l in bpy.data.libraries],unit_object_scales=all(all(abs(v-1)<1e-5 for v in o.scale) for o in meshes))
        assert check['mesh_count'] and check['materials_assigned'] and not check['degenerate_faces'] and check['unit_object_scales']
        part_checks.append(check)
    bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')))
    scene=bpy.context.scene
    samples=[]
    for f in [1,35,60,80,120]:
        scene.frame_set(f);bpy.context.view_layer.update()
        samples.append(dict(frame=f,elevation_degrees=math.degrees(bpy.data.objects['Elevation'].rotation_euler.x),azimuth_degrees=math.degrees(bpy.data.objects['Azimuth'].rotation_euler.z),mesh_count=sum(o.type=='MESH' for o in scene.objects),finite=all(math.isfinite(v) for o in scene.objects for row in o.matrix_world for v in row)))
    assert all(s['finite'] for s in samples)
    scene.frame_set(1)
    reviewer=Assembly.__new__(Assembly);reviewer.bid=bid
    reviewer.review(path=Path(tempfile.gettempdir())/(bid+'-top-review.png'),view=(0,-.1,16),target=(0,-.8,0),scale=11 if bid=='MA-W01' else 6.5,resolution=600)
    camera=scene.camera;camera.location=(10,-14,10) if bid=='MA-W01' else (7,-11,7)
    camera.rotation_euler=(Vector((0,-1.8,1.5) if bid=='MA-W01' else (0,-.1,1.1))-camera.location).to_track_quat('-Z','Y').to_euler()
    for frame in [35,80]:
        scene.frame_set(frame)
        scene.render.filepath=str(Path(tempfile.gettempdir())/(bid+'-pose-'+str(frame)+'.png'))
        bpy.ops.render.render(write_still=True)
    # Verify actual exported GLB independently in a new scene.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(folder/'Exports'/(bid+'.glb')))
    imported=list(bpy.context.scene.objects)
    meshes=[o for o in imported if o.type=='MESH']
    required=['Azimuth','Elevation']+(['Recoil0','Recoil1','Recoil2'] if bid=='MA-W01' else ['ContinuousEmitter'])
    assert all(name in bpy.data.objects for name in required)
    assert meshes and bpy.data.actions
    assert all(len(o.data.materials)>0 for o in meshes)
    check=dict(source_reopened=True,part_checks=part_checks,pose_samples=samples,glb_imported_in_Blender=True,imported_mesh_count=len(meshes),imported_material_count=len(bpy.data.materials),imported_action_count=len(bpy.data.actions),required_nodes_preserved=required,external_images=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath],part_instance_scales_unit=all(i['scale']==[1,1,1] for i in data['instances']),visual_review=['final hero in TEMP','top view in TEMP','elevation extremes frame35 and frame80 in TEMP'],game_validation=False)
    assert not check['external_images']
    validation.update(check);write(folder/'validation.json',validation)
    print('VERIFIED_FINAL '+bid+' '+str(len(meshes))+' meshes '+str(len(bpy.data.actions))+' actions')
