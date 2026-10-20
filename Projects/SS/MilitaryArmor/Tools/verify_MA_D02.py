import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1]
def write(p,d):p.write_bytes((json.dumps(d,indent=2,ensure_ascii=False)+'\n').replace('\n','\r\n').encode())
def meshcheck():
 rows=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  assert all(e.is_manifold and e.is_contiguous for e in bm.edges),o.name
  assert bm.calc_volume(signed=True)>1e-9,o.name
  bm.free();assert len(o.data.materials)>0
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
  assert all(t.area>1e-10 for t in me.loop_triangles),o.name
  assert all(math.isfinite(c) for v in me.vertices for c in v.co)
  rows.append(dict(object=o.name,vertices=len(me.vertices),triangles=len(me.loop_triangles)));ev.to_mesh_clear()
 return rows
reports=[];metadata={}
for pid in ['MA-D02-P01','MA-D01-P02','MA-D01-P03']:
 folder=ROOT/'Parts'/pid;d=json.loads((folder/'part.json').read_text());metadata[pid]=d
 assert d['scale_policy']=='unit only'
 bpy.ops.wm.open_mainfile(filepath=str(folder/d['source']));bpy.context.view_layer.update();rows=meshcheck()
 for s in d['mounts']:
  o=bpy.data.objects[s['node']];assert o['socket_id']==s['id']
  assert (o.location-Vector(s['position'])).length<1e-6 and o.rotation_euler.to_matrix()==Matrix.Identity(3)
  assert abs(Vector(s['forward']).dot(Vector(s['up'])))<1e-6
 for m in d['materials']:
  assert m['id'] in bpy.data.materials
  for name in m['surfaces']:assert name in bpy.data.objects and bpy.data.materials[m['id']] in list(bpy.data.objects[name].data.materials)
 reports.append(dict(id=pid,passed=True,mesh_count=len(rows),geometry=rows))
folder=ROOT/'Blocks/MA-D02';d=json.loads((folder/'assembly.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(folder/'MA-D02.blend'));bpy.context.view_layer.update();rows=meshcheck();inst={i['id']:i for i in d['instances']}
for i in d['instances']:
 assert (folder/i['source']).resolve().exists() and i['version']==metadata[i['part_id']]['version']
 o=bpy.data.objects[i['id']]
 assert list(o.scale)==[1,1,1] and (o.location-Vector(i['translation'])).length<1e-6
 assert o['part_id']==i['part_id'] and o['part_version']==i['version'] and o.parent.name==i['parent']
 assert all(abs(x-y)<1e-6 for x,y in zip(o.rotation_euler,i['rotation_euler_xyz']))
for c in d['connections']:
 pair=[];ss=[]
 for iid,sid in [(c['parent_instance'],c['parent_socket']),(c['child_instance'],c['child_socket'])]:
  part=metadata[inst[iid]['part_id']];s=next(m for m in part['mounts'] if m['id']==sid);ss.append(s)
  o=bpy.data.objects[iid+'::socket.'+sid];assert o['socket_id']==sid;pair.append(o.matrix_world)
 assert set(ss[0]['compatibility']) & set(ss[1]['compatibility'])
 delta=pair[0].inverted()@pair[1]
 assert delta.translation.length<1e-6 and delta.to_quaternion().angle<1e-6
# Tool axes and short spindle/coupling are authoring-only data.
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[j] for v in p),max(v[j] for v in p)] for j in range(3)]
for side in ['left','right']:
 shaft=bpy.data.objects['drive-'+side+'::Short torque spindle'];coupling=bpy.data.objects['cutter-'+side+'::Rear torque coupling']
 a,b=bounds(shaft),bounds(coupling);assert all(min(a[j][1],b[j][1])-max(a[j][0],b[j][0])>0 for j in range(3))
 point=metadata['MA-D01-P03']['functional_points'][0]
 assert point['direction']==[0,-1,0] and point['up']==[0,0,1] and not point['gameplay_contract']
 assert (bpy.data.objects['cutter-'+side].matrix_world.to_3x3()@Vector(point['direction'])-Vector((0,-1,0))).length<1e-6
# Full source cutting head bounds remain separated in X.
l=bounds(bpy.data.objects['cutter-left::Rear mechanical lock ring']);r=bounds(bpy.data.objects['cutter-right::Rear mechanical lock ring']);assert r[0][0]>l[0][1]
assert not d['animations'] and not d['exports']
expected=sum(next(r['mesh_count'] for r in reports if r['id']==i['part_id']) for i in d['instances']);assert len(rows)==expected
write(folder/'independent-validation.json',dict(passed=True,reopened_sources_and_assembly=True,parts=reports,assembly_mesh_count=len(rows),socket_pose_and_semantic_compatibility=True,shaft_coupling_overlap=True,unit_scale=True,versions_resolved=True,no_zero_area_evaluated_triangles=True,authoring_tool_axes=True,game_validation=False))
print('MA_D02_INDEPENDENT_VERIFY_PASS',len(rows))