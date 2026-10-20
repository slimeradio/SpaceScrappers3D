import sys,json,math,csv,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import ROOT,write
BID='MA-S01';folder=ROOT/'Blocks'/BID

def scan():
 dep=bpy.context.evaluated_depsgraph_get();checks=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);winding=sum(len(e.link_loops)==2 and e.link_loops[0].vert==e.link_loops[1].vert for e in bm.edges);bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();c={'name':o.name,'triangles':len(me.loop_triangles),'zero_area_triangles':sum(t.area<1e-11 for t in me.loop_triangles),'nonmanifold_source_edges':bad,'signed_volume':volume,'inconsistent_winding_edges':winding,'finite':all(math.isfinite(c) for v in me.vertices for c in v.co),'materials':bool(o.data.materials) and all(s.material is not None for s in o.material_slots),'unit_scale':all(abs(s-1)<1e-6 for s in o.scale)}
  c['passed']=not bad and not winding and volume>0 and not c['zero_area_triangles'] and c['finite'] and c['materials'] and c['unit_scale'];checks.append(c);ev.to_mesh_clear()
 assert checks and all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
 return {'mesh_count':len(checks),'triangles':sum(c['triangles'] for c in checks),'zero_area_triangles':0,'checks_passed':True,'objects':checks}

doc=json.loads((folder/'assembly.json').read_text(encoding='utf8'));parts={};hashes={};metas={}
for pid in sorted(set(i['part_id'] for i in doc['instances'])):
 pf=ROOT/'Parts'/pid;src=pf/(pid+'.blend');meta=json.loads((pf/'part.json').read_text(encoding='utf8'));metas[pid]=meta
 bpy.ops.wm.open_mainfile(filepath=str(src));parts[pid]=scan();hashes[pid]=hashlib.sha256(src.read_bytes()).hexdigest()
 for s in meta['mounts']:
  assert s['node'] in bpy.data.objects
  assert (bpy.data.objects[s['node']].location-Vector(s['position'])).length<1e-5
  f,u=Vector(s['forward']),Vector(s['up']);assert abs(f.length-1)<1e-6 and abs(u.length-1)<1e-6 and abs(f.dot(u))<1e-6
 if pid.startswith('MA-S01-P'):
  pre=json.loads((pf/'geometry-validation.json').read_text(encoding='utf8'));assert pre['checked_before_assembly'] and pre['checks_passed']
  for name in ['top','perspective']:assert (pf/'Previews'/(name+'.png')).exists()
 assert meta['materials'] and not meta['animations']

bpy.ops.wm.open_mainfile(filepath=str(folder/(BID+'.blend')));geometry=scan();bpy.context.view_layer.update();byid={i['id']:i for i in doc['instances']};aligned=[]
for c in doc['connections']:
 pa,ch=byid[c['parent']],byid[c['child']];p=next(s for s in metas[pa['part_id']]['mounts'] if s['id']==c['socket']);q=next(s for s in metas[ch['part_id']]['mounts'] if s['id']==c['child_socket']);P=bpy.data.objects[pa['id']].matrix_world;C=bpy.data.objects[ch['id']].matrix_world
 e=(P@Vector(p['position'])-C@Vector(q['position'])).length;f=(P.to_3x3()@Vector(p['forward'])-C.to_3x3()@Vector(q['forward'])).length;u=(P.to_3x3()@Vector(p['up'])-C.to_3x3()@Vector(q['up'])).length
 assert max(e,f,u)<1e-5,(c,e,f,u);assert set(p['compatibility'])&set(q['compatibility']);aligned.append({**c,'position_error':e,'forward_error':f,'up_error':u,'checks_passed':True})
for i in doc['instances']:
 o=bpy.data.objects[i['id']];assert o['part_id']==i['part_id'] and o['part_version']==i['version'];assert (o.location-Vector(i['translation'])).length<1e-6;assert all(abs(s-1)<1e-6 for s in o.scale)
assert not any(o.animation_data and o.animation_data.action for o in bpy.context.scene.objects)
assert not list(folder.rglob('*.glb'))
row=next(r for r in csv.DictReader((ROOT.parent/'Catalog/blocks.csv').open(encoding='utf-8-sig',newline='')) if r['ID']==doc['catalog_id']);assert '1x1' in row.values()
for name in ['top','perspective']:assert (folder/'Previews'/(name+'.png')).exists()
for instance in doc['instances']:
 assert bpy.data.objects[instance['id']].parent.name==instance['parent']
for meta in metas.values():
 assert meta['attachment_areas'] and meta['scale_policy']=='unit only'
 assert not meta['functional_points']
write(folder/'validation.json',{'id':BID,'catalog_id':doc['catalog_id'],'catalog_grid':[1,1],'independent_verifier':'Tools/verify_MA_S01.py','source_reopened':True,'parts_reopened':parts,'part_sha256':hashes,'assembly_geometry':geometry,'socket_alignment':aligned,'preassembly_checks_verified':True,'instance_count':5,'new_parts':2,'reused_parts':['MA-N01-P01 v1.0','MA-R01-P05 v1.0'],'static_no_animation':True,'no_glb_created':True,'physical_scale':'BU unspecified','overlap_policy':'Separate manifold solids; intended sealed casing/armor seats and service contacts. No boolean union claimed.','game_validation':False,'checks_passed':True})
print('MA_S01_VERIFIED',geometry['mesh_count'],geometry['triangles'],len(aligned),flush=True)