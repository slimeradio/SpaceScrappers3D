"""Independent reopened MA-W11 authoring validation; no source mutation/export."""
import sys,json,hashlib,math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write
from redesign_compute_production import inspect
BID='MA-W11';folder=ROOT/'Blocks'/BID;meta=json.loads((folder/'assembly.json').read_text());parts={};sources=[]
for pid in sorted(set(i['part_id'] for i in meta['instances'])):
 p=ROOT/'Parts'/pid;pm=json.loads((p/'part.json').read_text());parts[pid]=pm;src=p/pm['source'];sha=hashlib.sha256(src.read_bytes()).hexdigest()
 if pid in meta['reused_source_sha256']:assert sha==meta['reused_source_sha256'][pid]
 bpy.ops.wm.open_mainfile(filepath=str(src))
 for o in list(bpy.context.scene.objects):
  if o.name=='Studio floor' and o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
 g=inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges),o.name;bm.free()
 for s in pm['mounts']:
  f,u=Vector(s['forward']),Vector(s['up']);assert abs(f.length-1)<1e-6 and abs(u.length-1)<1e-6 and abs(f.dot(u))<1e-6
  marker=bpy.data.objects.get('socket.'+s['id']) or bpy.data.objects.get(s.get('node',''));assert marker and (marker.location-Vector(s['position'])).length<1e-6
 if pid.startswith(BID):
  gate=json.loads((p/'geometry-validation.json').read_text());assert gate['checks_passed'] and gate['validated_before_assembly'] and gate['source_reopened_before_assembly']
  assert not pm['emission'] and not pm['animations']
  for name in ['top','perspective']:assert (p/'Previews'/(name+'.png')).stat().st_size>5000
 assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
 sources.append({'id':pid,'version':pm['version'],'sha256':sha,'source_reopened':True,'geometry':g})
src=folder/(BID+'.blend');sha=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;bpy.context.view_layer.update();g=inspect();inst={i['id']:i for i in meta['instances']}
for i in meta['instances']:
 o=bpy.data.objects[i['id']];assert o['part_id']==i['part_id'] and o['part_version']==i['version']==parts[i['part_id']]['version'];assert o.parent.name==i['parent'];assert (o.location-Vector(i['translation'])).length<1e-6;assert all(abs(s-1)<1e-6 for s in o.scale);assert (folder/i['source']).resolve().exists()
assert len(inst)==5 and not meta['animations'] and not bpy.data.actions
assert all(not o.animation_data for o in scene.objects)
def pose(i,sid):
 s=next(s for s in parts[i['part_id']]['mounts'] if s['id']==sid);mat=bpy.data.objects[i['id']].matrix_world
 return s,mat@Vector(s['position']),(mat.to_3x3()@Vector(s['forward'])).normalized(),(mat.to_3x3()@Vector(s['up'])).normalized()
connections=[]
for c in meta['connections']:
 sa,pa,fa,ua=pose(inst[c['parent_instance']],c['parent_socket']);sb,pb,fb,ub=pose(inst[c['child_instance']],c['child_socket'])
 assert sa['role']==sb['role'] and (pa-pb).length<1e-6 and fa.dot(fb)>.999999 and ua.dot(ub)>.999999
 connections.append({'connection':c,'distance':(pa-pb).length,'forward_dot':fa.dot(fb),'up_dot':ua.dot(ub),'roles_match':True})
assert len(connections)==4
points=parts['MA-W08-P02']['functional_points'];assert len(points)==1;point=points[0];mat=bpy.data.objects['FixedLauncher'].matrix_world;pos=mat@Vector(point['position']);direction=(mat.to_3x3()@Vector(point['direction'])).normalized();marker=bpy.data.objects['FixedLauncher::point.shoot']
assert (marker.matrix_world.translation-pos).length<1e-6 and (direction-Vector((0,-1,0))).length<1e-6
assert not scene.ray_cast(bpy.context.evaluated_depsgraph_get(),pos,direction,distance=20)[0]
assert not scene.ray_cast(bpy.context.evaluated_depsgraph_get(),pos-direction*.5,direction,distance=.5)[0]
# Ring/collar/brace contacts are intentional. Verify reserve cassettes clear the frame.
frame=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' and o.name.startswith('FixedFrame::') for v in o.bound_box]
reserves=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' and o.name.startswith(('ReserveLeft::','ReserveRight::')) for v in o.bound_box]
reserve_gap=min(v.z for v in reserves)-max(v.z for v in frame);assert reserve_gap>.04,reserve_gap
for n in ['top','perspective','top-grayscale']:assert (folder/'Previews'/(n+'.png')).stat().st_size>10000
assert not meta['exports'] and meta['functional_contract']['active_barrel_count']==1 and meta['functional_contract']['yaw_arc_degrees']==0 and meta['catalog_grid']==[1,3]
assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
write(folder/'validation.json',{'id':BID,'checks_passed':True,'source_reopened_in_independent_process':True,'standalone_parts':sources,'geometry':g,'connections':connections,'instance_count':5,'new_parts':1,'reused_parts':['MA-W08-P02 v1.0','MA-W08-P03 v1.0','MA-P06 v1.3'],'single_active_muzzle':True,'muzzle_position_BU':list(pos),'muzzle_forward':list(direction),'forward_clearance_BU':20,'bore_clearance_behind_muzzle_BU':.5,'reserve_frame_vertical_gap_BU':reserve_gap,'static_no_animations':True,'preview_views':['top','perspective','top-grayscale'],'top_orientation':'world +Y up; identity camera rotation','perspective_elevation_degrees':45,'perspective_azimuth_degrees':45,'source_unchanged_after_review':True,'reused_source_hashes_unchanged':True,'source_sha256':sha,'glb_generated':False,'game_validation':False,'collision_LOD_validation':False,'limitations':'BU scale and XML-to-BU mapping unspecified. Intentional shell/collar/support contacts. Fixed source interface role yaw does not imply rotation. No game integration, colliders or LOD.'})
print('VERIFIED MA-W11',flush=True)
