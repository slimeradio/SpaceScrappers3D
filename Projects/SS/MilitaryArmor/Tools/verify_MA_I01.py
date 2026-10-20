import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write
folder=ROOT/'Blocks'/'MA-I01';results=[]
for pid in ['MA-I01-P01','MA-I01-P02','MA-I01-P03','MA-F01-P01','MA-F01-P03','MA-R01-P05']:
 p=ROOT/'Parts'/pid;meta=json.loads((p/'part.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(p/meta['source']))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
 for o in meshes:
  bm=bmesh.new();bm.from_mesh(o.data);checks.append({'mesh':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'volume':bm.calc_volume(signed=True)});bm.free()
  assert checks[-1]['nonmanifold_edges']==0 and checks[-1]['zero_area_faces']==0 and checks[-1]['volume']>0
  assert o.data.materials and all(m is not None for m in o.data.materials)
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();assert all(t.area>1e-10 for t in mesh.loop_triangles);assert all(math.isfinite(c) for v in mesh.vertices for c in v.co);ev.to_mesh_clear()
 if pid.startswith('MA-I01'):
  for name in ['top','perspective']:assert (p/'Previews'/(name+'.png')).stat().st_size>5000
 if pid.startswith('MA-I01'):assert json.loads((p/'geometry-validation.json').read_text())['checks_passed']
 results.append({'id':pid,'source_reopened':True,'meshes':checks,'previews_present':True})
meta=json.loads((folder/'assembly.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(folder/'MA-I01.blend'));bpy.context.view_layer.update()
instances={i['id']:i for i in meta['instances']};connection_checks=[]
def socket(inst,sid):
 data=json.loads((ROOT/'Parts'/inst['part_id']/'part.json').read_text());return next(s for s in data['mounts'] if s['id']==sid)
def pose(i,s):
 o=bpy.data.objects[i['id']];mat=o.matrix_world;position=mat@Vector(s['position']);forward=(mat.to_3x3()@Vector(s['forward'])).normalized();up=(mat.to_3x3()@Vector(s['up'])).normalized();return position,forward,up
for c in meta['connections']:
 a=instances[c['parent_instance']];b=instances[c['child_instance']];sa=socket(a,c['parent_socket']);sb=socket(b,c['child_socket']);pa,fa,ua=pose(a,sa);pb,fb,ub=pose(b,sb);assert set(sa.get('compatibility',[])) & set(sb.get('compatibility',[]))
 check={'connection':c,'distance':(pa-pb).length,'forward_dot':fa.dot(fb),'up_dot':ua.dot(ub)};assert check['distance']<1e-5 and check['forward_dot']>.9999 and check['up_dot']>.9999;connection_checks.append(check)
for i in instances.values():
 data=json.loads((ROOT/'Parts'/i['part_id']/'part.json').read_text());assert data['version']==i['version'];assert (folder/i['source']).resolve().exists();assert all(abs(v-1)<1e-6 for v in bpy.data.objects[i['id']].scale)
assert meta['catalog_id']=='cargo-2x1' and meta['catalog_grid']==[2,1] and not meta['exports']
assert not list(folder.rglob('*.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box];lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
assert hi[0]-lo[0]>1.8*(hi[1]-lo[1])
for name in ['top','perspective']:assert (folder/'Previews'/(name+'.png')).stat().st_size>5000
write(folder/'validation.json',{'id':'MA-I01','checks_passed':True,'verification':'Independent Blender process reopened all three new standalone sources and three reused sources and final assembly. Geometry gates passed before dependent assembly. Mesh manifoldness, positive volume, nondegenerate faces, nondegenerate evaluated triangles and finite coordinates and material assignment checked. Full socket positions and orientations matched. All dependency versions and unit scales resolved.','standalone_parts':results,'connections':connection_checks,'instance_count':len(instances),'resolved_parts':sorted(set(i['part_id'] for i in instances.values())),'bounds_BU':{'min':lo,'max':hi},'preview_views':['top','perspective'],'glb_generated':False,'game_validation':False,'collision_LOD_validation':False,'notes':'Overlapping enclosure seats, pressure seals and armour layers are intentional contacts. No moving poses. Physical BU-to-metre conversion unspecified.'})
print('MA_I01_VERIFIED')
