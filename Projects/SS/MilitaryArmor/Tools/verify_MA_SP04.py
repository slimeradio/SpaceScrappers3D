"""Independent reopened-source verification of MA-SP04."""
import sys,bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector,Euler
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write
IDS=['MA-SP04'];cache={}

def geometry():
 bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();out=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  nonmanifold=sum(not e.is_manifold for e in bm.edges);zero=sum(f.calc_area()<1e-10 for f in bm.faces);volume=bm.calc_volume(signed=True)
  # Every shared manifold edge must be traversed in opposite directions.
  consistent=all(e.is_contiguous for e in bm.edges);bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();tri_zero=sum(t.area<1e-10 for t in me.loop_triangles);finite=all(math.isfinite(c) for v in me.vertices for c in v.co);ev.to_mesh_clear()
  assert not nonmanifold and not zero and volume>0 and consistent and not tri_zero and finite,o.name
  assert o.data.materials and all(m is not None for m in o.data.materials),o.name
  out.append({'mesh':o.name,'nonmanifold_edges':nonmanifold,'source_zero_area_faces':zero,'signed_volume':volume,'normals_consistent':consistent,'evaluated_zero_area_triangles':tri_zero,'finite':finite,'materials_resolved':True})
 assert out
 return out

for bid in IDS:
 folder=ROOT/'Blocks'/bid;meta=json.loads((folder/'assembly.json').read_text());assert meta['version']=='2.0';sources=[]
 for pid in sorted(set(i['part_id'] for i in meta['instances'])):
  p=ROOT/'Parts'/pid;pm=json.loads((p/'part.json').read_text());assert pm['version']=='2.0';assert pm['axes']==meta['axes'];assert pm['scale_policy']=='unit only'
  assert json.loads((p/'geometry-validation.json').read_text())['validated_before_assembly']
  if pid not in cache:
   bpy.ops.wm.open_mainfile(filepath=str(p/pm['source']));checks=geometry()
   if pid=='MA-SP04-P01':
    assert pm['emission']==[]
    cells=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('PV-row-')]
    traces=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('Trace-row-')]
    assert len(cells)==36 and len(traces)==36
    def element_bounds(o):
     out=[]
     for g in o.vertex_groups:
      pts=[o.matrix_world@v.co for v in o.data.vertices if any(e.group==g.index for e in v.groups)]
      assert pts
      out.append((Vector([min(v[k] for v in pts) for k in range(3)]),Vector([max(v[k] for v in pts) for k in range(3)])))
     return out
    cb=[p for o in cells for p in element_bounds(o)]
    tb=[p for o in traces for p in element_bounds(o)]
    assert len(cb)==576 and len(tb)==1152
    for lo,hi in tb:
     assert any(lo.x>a.x and hi.x<b.x and lo.y>a.y and hi.y<b.y and lo.z<b.z and hi.z>b.z for a,b in cb)
    for lo,hi in cb:
     assert abs((hi.x-lo.x)-.391)<1e-5 and abs((hi.y-lo.y)-.262)<1e-5
     assert lo.z<.066 and hi.z>.066
     # All cell corners stay inside the chamfered dielectric outline.
     for x in [lo.x,hi.x]:
      for y in [lo.y,hi.y]:assert abs(x)<3.53 and abs(y)<5.33 and abs(x)+abs(y)<8.33
   assert bpy.context.scene.unit_settings.system=='NONE'
   for mat in pm['materials']:
    assert mat['id'] in bpy.data.materials
    for surface in mat['surfaces']:assert surface in bpy.data.objects
   for name in ['top','perspective']:assert (p/'Previews'/(name+'.png')).stat().st_size>5000
   for s in pm['mounts']:
    assert abs(Vector(s['forward']).length-1)<1e-6 and abs(Vector(s['up']).length-1)<1e-6
    assert abs(Vector(s['forward']).dot(Vector(s['up'])))<1e-6
    assert (bpy.data.objects['socket.'+s['id']].location-Vector(s['position'])).length<1e-6
   cache[pid]={'id':pid,'version':pm['version'],'source_reopened':True,'geometry':checks,'previews_present':True}
  sources.append(cache[pid])
 bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')));bpy.context.view_layer.update();meshes=geometry();inst={i['id']:i for i in meta['instances']}
 assert bpy.context.scene.unit_settings.system=='NONE'
 for i in meta['instances']:
  node=bpy.data.objects[i['id']];pm=json.loads((ROOT/'Parts'/i['part_id']/'part.json').read_text())
  assert pm['version']==i['version'] and node['part_version']==i['version']
  assert (folder/i['source']).resolve().exists()
  assert node.parent.name==i['parent']
  assert (node.location-Vector(i['translation'])).length<1e-6
  assert (Vector(node.rotation_euler)-Vector(i['rotation_euler_xyz'])).length<1e-6
  assert all(abs(v-1)<1e-6 for v in node.scale)
 def mount(i,sid):return next(s for s in json.loads((ROOT/'Parts'/i['part_id']/'part.json').read_text())['mounts'] if s['id']==sid)
 def pose(i,s):
  mat=bpy.data.objects[i['id']].matrix_world
  return mat@Vector(s['position']),(mat.to_3x3()@Vector(s['forward'])).normalized(),(mat.to_3x3()@Vector(s['up'])).normalized()
 connections=[]
 for c in meta['connections']:
  a=inst[c['parent_instance']];b=inst[c['child_instance']];sa=mount(a,c['parent_socket']);sb=mount(b,c['child_socket']);pa,fa,ua=pose(a,sa);pb,fb,ub=pose(b,sb)
  assert set(sa['compatibility']) & set(sb['compatibility'])
  assert (pa-pb).length<1e-6 and fa.dot(fb)>.99999 and ua.dot(ub)>.99999
  connections.append({'connection':c,'distance':(pa-pb).length,'forward_dot':fa.dot(fb),'up_dot':ua.dot(ub),'semantic_compatibility':True})
 assert len(connections)==len(inst)-1
 supports=[i for i in inst.values() if i['part_id']=='MA-SP01-R2-P01']
 assert len(supports)==6
 support_meta=json.loads((ROOT/'Parts'/'MA-SP01-R2-P01'/'part.json').read_text())
 low=Vector(support_meta['bounds_local']['min']);high=Vector(support_meta['bounds_local']['max'])
 for support in supports:
  sl=low+Vector(support['translation']);sh=high+Vector(support['translation'])
  for x in [sl.x,sh.x]:
   for y in [sl.y,sh.y]:assert abs(x)<3.6 and abs(y)<5.4 and abs(x)+abs(y)<8.45
 for j,a in enumerate(supports):
  for b in supports[j+1:]:
   al=low+Vector(a['translation']);ah=high+Vector(a['translation']);bl=low+Vector(b['translation']);bh=high+Vector(b['translation'])
   assert any(ah[k]<bl[k] or bh[k]<al[k] for k in range(3)),(a['id'],b['id'])
 for name in ['top','perspective','top-grayscale']:assert (folder/'Previews'/(name+'.png')).stat().st_size>5000
 assert not meta['exports'] and not meta['animations']
 write(folder/'validation.json',{'id':bid,'version':'2.0','checks_passed':True,'verification':'Independent Blender process reopened all standalone parts and final assembly. Source manifoldness, consistent normals, positive volume, zero-area source faces and evaluated triangles, finite coordinates and assigned materials checked. Full world socket poses, semantic compatibility, version/source paths and unit instance scales checked.','standalone_parts':sources,'assembly_meshes':meshes,'connections':connections,'instance_count':len(inst),'resolved_parts':sorted(set(i['part_id'] for i in inst.values())),'preview_views':['top','perspective','top-grayscale'],'grayscale_override_temporary':True,'passive_cell_count':576,'trace_count':1152,'trace_cell_contact_verified':True,'support_pair_nonintersection_verified':True,'support_outline_containment_verified':True,'glb_generated':False,'game_validation':False,'collision_LOD_validation':False,'notes':'Static authoring model. Designed intersections at seats, pressure shields, thermal connections and service mounts are intentional. Physical BU scale unspecified.'})
 print('VERIFIED',bid,flush=True)
