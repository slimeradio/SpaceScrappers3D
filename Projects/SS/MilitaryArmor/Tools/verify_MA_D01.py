import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
def write(p,d):p.write_bytes((json.dumps(d,indent=2,ensure_ascii=False)+'\n').replace('\n','\r\n').encode())
def meshcheck():
 rows=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  assert all(e.is_manifold and e.is_contiguous for e in bm.edges),o.name
  assert bm.calc_volume(signed=True)>1e-9,o.name
  bm.free()
  assert len(o.data.materials)>0
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
  assert all(t.area>1e-10 for t in me.loop_triangles),o.name
  assert all(math.isfinite(c) for v in me.vertices for c in v.co)
  rows.append(dict(object=o.name,vertices=len(me.vertices),triangles=len(me.loop_triangles)))
  ev.to_mesh_clear()
 return rows
reports=[];metadata={}
for pid in ['MA-D01-P01','MA-D01-P02','MA-D01-P03']:
 folder=ROOT/'Parts'/pid;d=json.loads((folder/'part.json').read_text());metadata[pid]=d
 assert d['scale_policy']=='unit only'
 bpy.ops.wm.open_mainfile(filepath=str(folder/d['source']));bpy.context.view_layer.update()
 rows=meshcheck()
 for s in d['mounts']:
  o=bpy.data.objects[s['node']]
  assert (o.location-Vector(s['position'])).length<1e-6
  assert o.rotation_euler.to_matrix()==__import__('mathutils').Matrix.Identity(3)
  assert abs(Vector(s['forward']).dot(Vector(s['up'])))<1e-6
 for m in d['materials']:
  assert m['id'] in bpy.data.materials
  for name in m['surfaces']:assert name in bpy.data.objects and bpy.data.materials[m['id']] in list(bpy.data.objects[name].data.materials)
 reports.append(dict(id=pid,passed=True,mesh_count=len(rows),geometry=rows))
folder=ROOT/'Blocks'/'MA-D01';d=json.loads((folder/'assembly.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(folder/'MA-D01.blend'));bpy.context.view_layer.update()
rows=meshcheck()
inst={i['id']:i for i in d['instances']}
for i in d['instances']:
 assert (folder/i['source']).resolve().exists()
 assert i['version']==metadata[i['part_id']]['version']
 o=bpy.data.objects[i['id']]
 assert list(o.scale)==[1,1,1] and (o.location-Vector(i['translation'])).length<1e-6
 assert o['part_id']==i['part_id'] and o['part_version']==i['version']
for c in d['connections']:
 pair=[];ss=[]
 for iid,sid in [(c['parent_instance'],c['parent_socket']),(c['child_instance'],c['child_socket'])]:
  part=metadata[inst[iid]['part_id']];s=next(m for m in part['mounts'] if m['id']==sid);ss.append(s)
  o=bpy.data.objects[iid+'::'+s['node']];pair.append(o.matrix_world)
 assert set(ss[0]['compatibility']) & set(ss[1]['compatibility'])
 delta=pair[0].inverted()@pair[1]
 assert delta.translation.length<1e-6 and delta.to_quaternion().angle<1e-6
# Coupling physically overlaps the source shaft along the common tool axis.
shaft=bpy.data.objects['reduction-drive::Short torque spindle'];coupling=bpy.data.objects['cutting-head::Rear torque coupling']
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[j] for v in p),max(v[j] for v in p)] for j in range(3)]
a,b=bounds(shaft),bounds(coupling)
assert all(min(a[j][1],b[j][1])-max(a[j][0],b[j][0])>0 for j in range(3))
assert not d['animations'] and not d['exports']
assert len(rows)==sum(r['mesh_count'] for r in reports)
write(folder/'independent-validation.json',dict(passed=True,reopened_sources_and_assembly=True,parts=reports,assembly_mesh_count=len(rows),socket_pose_and_semantic_compatibility=True,shaft_coupling_overlap=True,unit_scale=True,versions_resolved=True,no_zero_area_evaluated_triangles=True,game_validation=False))
print('MA-D01_INDEPENDENT_VERIFY_PASS',len(rows))
