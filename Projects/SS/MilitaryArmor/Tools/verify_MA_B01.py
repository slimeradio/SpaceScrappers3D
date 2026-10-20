"""Reopen and verify MA-B01 editable sources; no export or rebuild."""
import sys,json,math,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write
from mathutils import Vector
import bpy
F=ROOT/'Blocks'/'MA-B01'
a=json.loads((F/'assembly.json').read_text(encoding='utf8'))
def inspect():
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];dep=bpy.context.evaluated_depsgraph_get();n=zero=nonmanifold=0
    for obj in meshes:
        ev=obj.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();n+=len(me.loop_triangles);zero+=sum(t.area<1e-10 for t in me.loop_triangles)
        bm=bmesh.new();bm.from_mesh(me);nonmanifold+=sum(not e.is_manifold for e in bm.edges);bm.free()
        assert all(math.isfinite(c) for v in me.vertices for c in v.co)
        assert me.materials and all(m for m in me.materials)
        ev.to_mesh_clear()
    return {'meshes':len(meshes),'triangles':n,'zero_area_triangles':zero,'nonmanifold_edges':nonmanifold,'finite':True,'materials_resolved':True}
parts={}
for pid in sorted(set(i['part_id'] for i in a['instances'])):
    p=ROOT/'Parts'/pid
    bpy.ops.wm.open_mainfile(filepath=str(p/(pid+'.blend')))
    c=inspect();parts[pid]=c
    assert c['meshes']>0
    if pid.startswith('MA-B01'):
        assert c['zero_area_triangles']==0 and c['nonmanifold_edges']==0
        assert json.loads((p/'validation.json').read_text(encoding='utf8'))['validated_before_assembly']
        assert (p/'Previews'/(pid+'.png')).exists()
bpy.ops.wm.open_mainfile(filepath=str(F/'MA-B01.blend'))
bpy.context.view_layer.update();geometry=inspect();sockets=[]
for con in a['connections']:
    ip=next(i for i in a['instances'] if i['id']==con['parent']);ic=next(i for i in a['instances'] if i['id']==con['child'])
    p=json.loads((ROOT/'Parts'/ip['part_id']/'part.json').read_text(encoding='utf8'));c=json.loads((ROOT/'Parts'/ic['part_id']/'part.json').read_text(encoding='utf8'))
    sp=next(s for s in p['mounts'] if s['id']==con['socket']);sc=next(s for s in c['mounts'] if s['id']==con['child_socket'])
    if con['child']=='Service': assert 'MilitaryArmor.service-cartridge.v1' in sp['compatibility'] and 'MilitaryArmor.service-cartridge.v1' in sc['compatibility']
    pm=bpy.data.objects[ip['id']].matrix_world;cm=bpy.data.objects[ic['id']].matrix_world
    error=(pm@Vector(sp['position'])-cm@Vector(sc['position'])).length
    aligned=error<1e-5 and all((pm.to_3x3()@Vector(sp[k])-cm.to_3x3()@Vector(sc[k])).length<1e-5 for k in ['forward','up'])
    assert aligned,con
    sockets.append(dict(con,aligned=True,position_error_BU=error))
for i in a['instances']:
    assert (F/i['source']).resolve().exists()
    assert bpy.data.objects[i['id']]['part_version']==i['version']
    assert all(abs(v-1)<1e-6 for v in bpy.data.objects[i['id']].scale)
assert geometry['zero_area_triangles']==0 and geometry['nonmanifold_edges']==0
assert not bpy.data.actions
assert (F/'Previews/perspective.png').exists() and (F/'Previews/top.png').exists()
assert not list(F.rglob('*.glb'))
write(F/'validation.json',{'id':'MA-B01','checks_passed':True,'source_reopened':True,'new_parts_geometry_checked_before_assembly':True,'part_sources_reopened':parts,'assembly_geometry':geometry,'socket_alignment':sockets,'instance_count':len(a['instances']),'new_unique_parts':4,'reused_parts':['MA-R01-P05 v1.0 (compatible repaired variant of MA-P06 v1.3)'],'source_links_resolved':True,'unit_scale':True,'static_no_animations':True,'no_GLB_generated':True,'visual_review':['Previews/perspective.png','Previews/top.png'],'intersections':'Module bodies seat on cassette; armored lids and shoulders clear at visible seams. Intended bedding overlaps only, visual review. No boolean assembly union.','game_validation':False,'limits':['Authoring BU physical scale unspecified','No game integration, LOD or collision contract']})
print('MA_B01_SOURCE_VERIFIED',flush=True)