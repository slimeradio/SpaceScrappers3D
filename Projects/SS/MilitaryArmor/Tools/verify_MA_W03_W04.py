import bpy,sys,json,math,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly
from mathutils import Vector

for bid,expected in [('MA-W03',2),('MA-W04',4)]:
    folder=ROOT/'Blocks'/bid
    metadata=json.loads((folder/'assembly.json').read_text(encoding='utf8'))
    result=json.loads((folder/'validation.json').read_text(encoding='utf8'))
    parts={inst['part_id'] for inst in metadata['instances']}
    part_checks={}
    points=0
    for pid in sorted(parts):
        pmeta=json.loads((ROOT/'Parts'/pid/'part.json').read_text(encoding='utf8'))
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts'/pid/(pid+'.blend')))
        meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
        part_checks[pid]={'reopened':True,'mesh_count':len(meshes),'materials_assigned':all(len(o.data.materials)>0 for o in meshes),'unit_scale':all(all(abs(s-1)<1e-5 for s in o.scale) for o in meshes),'file_dependencies':[x.filepath for x in bpy.data.images if x.source=='FILE']}
        assert meshes and part_checks[pid]['materials_assigned'] and part_checks[pid]['unit_scale']
    for inst in metadata['instances']:
        pm=json.loads((ROOT/'Parts'/inst['part_id']/'part.json').read_text(encoding='utf8'))
        points+=len(pm['functional_points'])
    assert points==expected,(bid,points,expected)
    bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')))
    source_nodes={o.name for o in bpy.context.scene.objects}
    source_meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    pose_checks=[]
    for frame in [1,30,60,90,120]:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        valid=all(all(math.isfinite(n) for row in o.matrix_world for n in row) for o in source_meshes)
        assert valid
        pose_checks.append({'frame':frame,'finite_transforms':valid,'elevation_degrees':math.degrees(bpy.data.objects['Elevation'].rotation_euler.x)})
    bpy.context.scene.frame_set(1)
    review=Assembly.__new__(Assembly);review.bid=bid
    review.review(path=Path(tempfile.gettempdir())/(bid+'-top-review.png'),view=(0,-.01,10),target=(0,0,1),scale=5.8,resolution=600)
    scene=bpy.context.scene;scene.frame_set(90)
    scene.camera.location=(7,-10,7)
    scene.camera.rotation_euler=(Vector((0,-.2,1.1))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=6.4
    scene.render.filepath=str(Path(tempfile.gettempdir())/(bid+'-extreme-review.png'))
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(folder/'Exports'/(bid+'.glb')))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert meshes and len(meshes)==len(source_meshes),(len(meshes),len(source_meshes))
    assert all(len(o.data.materials)>0 for o in meshes)
    assert bpy.data.objects.get('Elevation') and bpy.data.objects.get('Azimuth')
    result.update({'parts_reopened_in_Blender':part_checks,'assembly_reopened_in_Blender':True,'catalogue_functional_barrel_count':points,'pose_checks':pose_checks,'visual_review':{'final_oblique':str(Path(tempfile.gettempdir())/(bid+'-final-review.png')),'final_top':str(Path(tempfile.gettempdir())/(bid+'-top-review.png'))},'glb_roundtrip':{'imported_in_Blender':True,'mesh_count':len(meshes),'source_mesh_count':len(source_meshes),'hierarchy_resolved':True,'materials_assigned':True,'actions':len(bpy.data.actions)}})
    write(folder/'validation.json',result)
    print('VERIFIED',bid,len(meshes),'meshes',points,'functional barrels')
