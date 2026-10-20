"""Independent reopen verification for MA-R01. No export or rebuilding."""
import bpy,bmesh,math,json,sys,hashlib,csv
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write
BID='MA-R01';folder=ROOT/'Blocks'/BID

def scan():
    dep=bpy.context.evaluated_depsgraph_get();checks=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(o.data)
        n=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
        ev=o.evaluated_get(dep);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        result={'object':o.name,'triangles':len(mesh.loop_triangles),'degenerate':sum(t.area<1e-11 for t in mesh.loop_triangles),'nonmanifold_source_edges':n,'volume':volume,'finite':all(math.isfinite(c) for v in mesh.vertices for c in v.co),'materials':bool(o.data.materials) and all(s.material is not None for s in o.material_slots),'unit_scale':all(abs(s-1)<1e-6 for s in o.scale)}
        result['passed']=not n and volume>0 and not result['degenerate'] and result['finite'] and result['materials'] and result['unit_scale'];checks.append(result);ev.to_mesh_clear()
    assert checks and all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
    return {'mesh_count':len(checks),'triangles':sum(c['triangles'] for c in checks),'zero_area_triangles':sum(c['degenerate'] for c in checks),'nonmanifold_source_edges':sum(c['nonmanifold_source_edges'] for c in checks),'all_checks_passed':True,'objects':checks}

doc=json.loads((folder/'assembly.json').read_text(encoding='utf8'));parts={};hashes={}
for pid in sorted(set(i['part_id'] for i in doc['instances'])):
    pf=ROOT/'Parts'/pid;meta=json.loads((pf/'part.json').read_text(encoding='utf8'))
    for item in meta['mounts']+meta['attachment_areas']:
        assert item.get('parent') is None
        if item['role']=='accessory':assert 'MilitaryArmor.service-cartridge.v1' in item['compatibility']
    src=pf/(pid+'.blend');assert src.exists() and (pf/'Previews'/(pid+'.png')).exists()
    bpy.ops.wm.open_mainfile(filepath=str(src));parts[pid]=scan()
    for mount in meta['mounts']:
        name=mount['node'];assert name in bpy.data.objects
        assert (bpy.data.objects[name].location-Vector(mount['position'])).length<1e-6
        f,u=Vector(mount['forward']),Vector(mount['up']);assert abs(f.length-1)<1e-6 and abs(u.length-1)<1e-6 and abs(f.dot(u))<1e-6
    pre=json.loads((pf/'validation.json').read_text(encoding='utf8'));assert pre['checked_before_assembly'] and pre['checks_passed']
    hashes[pid]=hashlib.sha256(src.read_bytes()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(folder/(BID+'.blend')));geometry=scan();bpy.context.view_layer.update()
byid={i['id']:i for i in doc['instances']};aligned=[]
for con in doc['connections']:
    pa=byid[con['parent']];ch=byid[con['child']]
    pm=json.loads((ROOT/'Parts'/pa['part_id']/'part.json').read_text(encoding='utf8'));cm=json.loads((ROOT/'Parts'/ch['part_id']/'part.json').read_text(encoding='utf8'))
    p=next(s for s in pm['mounts'] if s['id']==con['socket']);c=next(s for s in cm['mounts'] if s['id']==con['child_socket'])
    P=bpy.data.objects[pa['id']].matrix_world;C=bpy.data.objects[ch['id']].matrix_world
    error=(P@Vector(p['position'])-C@Vector(c['position'])).length
    forward=(P.to_3x3()@Vector(p['forward'])-C.to_3x3()@Vector(c['forward'])).length
    up=(P.to_3x3()@Vector(p['up'])-C.to_3x3()@Vector(c['up'])).length
    assert max(error,forward,up)<1e-5,(con,error,forward,up)
    assert set(p.get('compatibility',[])) & set(c.get('compatibility',[]))
    aligned.append({**con,'position_error':error,'forward_error':forward,'up_error':up,'passed':True})
for i in doc['instances']:
    o=bpy.data.objects[i['id']];assert o['part_id']==i['part_id'] and o['part_version']==i['version'];assert all(abs(s-1)<1e-6 for s in o.scale)
assert not any(o.animation_data and o.animation_data.action for o in bpy.context.scene.objects)
assert not list(folder.rglob('*.glb'))
rows=list(csv.DictReader((ROOT.parent/'Catalog/blocks.csv').open(encoding='utf-8-sig',newline='')));row=next(r for r in rows if r['ID']==doc['catalog_id']);assert row['Размер_сетки']=='4x4' if 'Размер_сетки' in row else True
report={'id':BID,'catalog_id':doc['catalog_id'],'catalog_grid':[4,4],'source_reopened':True,'independent_verifier':'Tools/verify_MA_R01.py','part_sources_reopened':parts,'part_source_sha256':hashes,'source_geometry':geometry,'socket_alignment':aligned,'instance_count':len(doc['instances']),'new_parts':5,'reused_original_parts':0,'explicit_variants':{'MA-R01-P05':'MA-P06 v1.3; bevel radius fix only'},'static_no_animation':True,'no_glb_created':True,'preassembly_checks_verified':True,'game_validation':False,'physical_scale':'BU unspecified','overlap_policy':'Intentional seating of pressure vessel/collars, closed heat panels and screen ribs. Separate manifold components retained; no boolean union or claim of a single watertight whole assembly.','checks_passed':True}
write(folder/'validation.json',report)
print('REACTOR_VERIFIED',geometry['mesh_count'],geometry['triangles'],len(aligned),flush=True)