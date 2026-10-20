"""Independent reopen verification, separate from source generator."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write

def meshcheck(o):
 bm=bmesh.new();bm.from_mesh(o.data);c=dict(mesh=o.name,source_nonmanifold=sum(not e.is_manifold for e in bm.edges),inconsistent_edges=sum(e.is_manifold and not e.is_contiguous for e in bm.edges),zero_area_faces=sum(f.calc_area()<1e-10 for f in bm.faces),signed_volume=bm.calc_volume(signed=True));bm.free()
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();c.update(evaluated_zero_area_triangles=sum(t.area<1e-10 for t in me.loop_triangles),evaluated_triangles=len(me.loop_triangles),finite=all(math.isfinite(c) for v in me.vertices for c in v.co),materials=all(m is not None for m in me.materials) and bool(me.materials));ev.to_mesh_clear()
 assert c['source_nonmanifold']==c['inconsistent_edges']==c['zero_area_faces']==c['evaluated_zero_area_triangles']==0 and c['signed_volume']>0 and c['finite'] and c['materials'],str(c)
 return c

def verify(bid):
 folder=ROOT/'Blocks'/bid;meta=json.loads((folder/'assembly.json').read_text());parts={};results=[]
 assert meta['version']=='2.0' and not meta['exports'] and not meta['animations']
 for pid in sorted({i['part_id'] for i in meta['instances']}):
  p=ROOT/'Parts'/pid;d=json.loads((p/'part.json').read_text());parts[pid]=d;assert d['version']=='2.0' and d['axes']==meta['axes']
  assert json.loads((p/'geometry-validation.json').read_text())['checks_passed'];bpy.ops.wm.open_mainfile(filepath=str(p/d['source']));bpy.context.view_layer.update();checks=[meshcheck(o) for o in bpy.context.scene.objects if o.type=='MESH'];assert checks
  assert d['scale_policy']=='unit only' and not d['animations'] and not d['functional_points']
  for s in d['mounts']:
   assert s['parent']=='part' and s['compatibility'] and s['allowed_scale']==[1,1,1]
   assert abs(Vector(s['forward']).length-1)<1e-6 and abs(Vector(s['up']).length-1)<1e-6 and abs(Vector(s['forward']).dot(Vector(s['up'])))<1e-6
   assert (bpy.data.objects['socket.'+s['id']].location-Vector(s['position'])).length<1e-6
  actual={o.name for o in bpy.context.scene.objects if o.type=='MESH'}
  assert actual=={name for m in d['materials'] for name in m['surfaces']}
  for material in d['materials']:
   for name in material['surfaces']:assert any(slot.material.name==material['id'] for slot in bpy.data.objects[name].material_slots)
  if bid in ['MA-H01','MA-SP01']:assert not d['emission']
  for name in ['top','perspective']:assert (p/'Previews'/(name+'.png')).stat().st_size>3000
  results.append(dict(id=pid,source_reopened=True,meshes=checks))
 bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')));bpy.context.view_layer.update();instances={i['id']:i for i in meta['instances']};connections=[]
 for i in meta['instances']:
  d=parts[i['part_id']];assert d['version']==i['version'] and (folder/i['source']).resolve()==(ROOT/'Parts'/i['part_id']/d['source']).resolve()
  assert (folder/i['source']).is_file();o=bpy.data.objects[i['id']]
  assert o['part_id']==i['part_id'] and o['part_version']==i['version'] and o.parent.name==i['parent']
  assert (o.location-Vector(i['translation'])).length<1e-6 and (Vector(o.rotation_euler)-Vector(i['rotation_euler_xyz'])).length<1e-6 and all(abs(s-1)<1e-6 for s in o.scale)
 def socket(i,sid):return next(s for s in parts[i['part_id']]['mounts'] if s['id']==sid)
 def pose(i,s):
  mat=bpy.data.objects[i['id']].matrix_world;return mat@Vector(s['position']),(mat.to_3x3()@Vector(s['forward'])).normalized(),(mat.to_3x3()@Vector(s['up'])).normalized()
 for c in meta['connections']:
  a,b=instances[c['parent_instance']],instances[c['child_instance']];sa,sb=socket(a,c['parent_socket']),socket(b,c['child_socket']);assert set(sa['compatibility'])&set(sb['compatibility']);pa,fa,ua=pose(a,sa);pb,fb,ub=pose(b,sb)
  check=dict(connection=c,position_error=(pa-pb).length,forward_dot=fa.dot(fb),up_dot=ua.dot(ub),semantic_compatibility=True)
  assert check['position_error']<1e-5 and check['forward_dot']>.99999 and check['up_dot']>.99999;connections.append(check)
 checks=[meshcheck(o) for o in bpy.context.scene.objects if o.type=='MESH'];assert len(checks)==sum(len(next(p for p in results if p['id']==i['part_id'])['meshes']) for i in meta['instances'])
 assert bpy.context.scene.unit_settings.system=='NONE' and not bpy.context.scene.view_layers[0].material_override
 for name in ['top','perspective','top-grayscale']:assert (folder/'Previews'/(name+'.png')).stat().st_size>3000
 pts=[o.matrix_world@Vector(v) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.bound_box];bounds={'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}
 write(folder/'validation.json',dict(id=bid,version='2.0',checks_passed=True,verification='Independent process reopened every standalone source and final assembly; source manifold/face orientation/positive volume, evaluated zero-area triangles/finite/materials, metadata surfaces, saved sockets and full world socket poses plus semantic compatibility; dependency versions, parents, unit scales and axes checked.',standalone_parts=results,connections=connections,assembly_meshes=checks,instance_count=len(instances),resolved_parts=sorted(parts),bounds_BU=bounds,preview_views=['top','perspective','top-grayscale'],glb_generated=False,game_validation=False,collision_LOD_validation=False,notes='All static: no animated poses. Designed nested enclosure surfaces, cell laminates and seated supports intentionally contact or overlap. No BU-to-metre conversion. Source material override is absent; grayscale is review only.'))
 print('VERIFIED',bid,flush=True)

for bid in ['MA-H01','MA-SP01','MA-R01','MA-S01']:verify(bid)
