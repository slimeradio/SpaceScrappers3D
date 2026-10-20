"""Independent reopen validation for MA-W07 and its authored parts."""
import bpy,bmesh,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write
BID='MA-W07';folder=ROOT/'Blocks'/BID
results=[]
for index in range(1,4):
    pid=f'{BID}-P{index:02}';base=ROOT/'Parts'/pid
    meta=json.loads((base/'part.json').read_text())
    assert json.loads((base/'validation.json').read_text())['checked_before_assembly']
    bpy.ops.wm.open_mainfile(filepath=str(base/(pid+'.blend')))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert objects
    for o in objects:
        assert all(math.isfinite(v) for p in o.data.vertices for v in p.co)
        bm=bmesh.new();bm.from_mesh(o.data)
        assert all(e.is_manifold for e in bm.edges),o.name
        assert bm.calc_volume(signed=True)>0,o.name
        assert all(f.calc_area()>1e-10 for f in bm.faces)
        bm.free();assert o.data.materials and all(o.data.materials)
        evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        assert all(math.isfinite(v) for p in mesh.vertices for v in p.co)
        assert len(mesh.polygons)>0;evaluated.to_mesh_clear()
    for m in meta['mounts']:assert 'socket.'+m['id'] in bpy.data.objects
    for p in meta['functional_points']:
        assert p['node'] in bpy.data.objects
        assert abs(Vector(p['direction']).length-1)<1e-6
    assert (base/'Previews/perspective.png').stat().st_size>1000
    results.append(dict(id=pid,reopened=True,mesh_count=len(objects),closed_manifold_positive_volume=True,finite_evaluated_geometry=True,materials_and_sockets_resolved=True))
ass=json.loads((folder/'assembly.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(folder/(BID+'.blend')))
assert not bpy.data.libraries
assert ass['catalog_grid']==[1,1] and ass['catalog_id']=='point-defense-turret'
assert len(ass['instances'])==4 and ass['exports']==[]
for inst in ass['instances']:
    o=bpy.data.objects[inst['id']];assert o.parent.name==inst['parent']
    assert all(abs(a-b)<1e-6 for a,b in zip(o.location,inst['translation']))
    assert all(abs(a-1)<1e-6 for a in o.scale)
    meta=json.loads((ROOT/'Parts'/inst['part_id']/'part.json').read_text())
    assert meta['version']==inst['version']
    assert (folder/inst['source']).resolve().exists()
assert hashlib.sha256((ROOT/'Parts/MA-P06/MA-P06.blend').read_bytes()).hexdigest()==ass['reused_source_sha256']['MA-P06']
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
rest_connections=[]
for c in ass['connections']:
    parent_inst=next(i for i in ass['instances'] if i['id']==c['parent_instance'])
    child_inst=next(i for i in ass['instances'] if i['id']==c['child_instance'])
    pm=json.loads((ROOT/'Parts'/parent_inst['part_id']/'part.json').read_text());cm=json.loads((ROOT/'Parts'/child_inst['part_id']/'part.json').read_text())
    ps=next(s for s in pm['mounts'] if s['id']==c['parent_socket']);cs=next(s for s in cm['mounts'] if s['id']==c['child_socket'])
    po=bpy.data.objects[c['parent_instance']];co=bpy.data.objects[c['child_instance']]
    pos1=po.matrix_world@Vector(ps['position']);pos2=co.matrix_world@Vector(cs['position'])
    assert (pos1-pos2).length<1e-5,c
    for key in ['forward','up']:
        v1=(po.matrix_world.to_3x3()@Vector(ps[key])).normalized();v2=(co.matrix_world.to_3x3()@Vector(cs[key])).normalized()
        assert v1.dot(v2)>.99999
    rest_connections.append(dict(parent=c['parent_instance'],child=c['child_instance'],position_error=(pos1-pos2).length,orientation_aligned=True))
samples=[]
for frame in [1,30,42,60,90,120]:
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    yaw=math.degrees(bpy.data.objects['Yaw'].rotation_euler.z);elev=math.degrees(bpy.data.objects['Elevation'].rotation_euler.x)
    assert abs(yaw)<=60.00001 and -18.00001<=elev<=8.00001
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    lowest=min((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)
    assert lowest>=-1e-5
    muzzle=bpy.data.objects['SingleMachinegun'].matrix_world@Vector((0,-2.16,0))
    assert muzzle.z>.5
    samples.append(dict(frame=frame,yaw_degrees=yaw,elevation_degrees=elev,muzzle_world=list(muzzle),minimum_z=lowest))
for f in ['perspective.png','top.png','grayscale-top.png']:assert (folder/'Previews'/f).stat().st_size>1000
mesh_count=len(meshes);triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
write(folder/'validation.json',dict(checks_passed=True,id=BID,independent_reopen=True,parts=results,instance_count=4,mesh_count=mesh_count,base_triangles=triangles,rest_socket_connections=rest_connections,animation_samples=samples,single_barrel_and_muzzle=True,external_libraries=[],reused_source_unchanged=True,preview_files=['perspective.png','top.png','grayscale-top.png'],glb_generated=False,game_validation=False,limitations='Authored geometry and motion verified. No engine import, collider, LOD or collision simulation; intended overlaps at structural joints.'))
print('MA-W07_VERIFIED',mesh_count,triangles)
