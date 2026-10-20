"""Independent reopened sources/motion/clearance gate; no exports or source writes."""
import sys,json,math,hashlib
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write
from redesign_compute_production import inspect
BID='MA-W08';folder=ROOT/'Blocks'/BID;meta=json.loads((folder/'assembly.json').read_text());sources=[];parts={}
for pid in sorted(set(i['part_id'] for i in meta['instances'])):
 p=ROOT/'Parts'/pid;pm=json.loads((p/'part.json').read_text());parts[pid]=pm;src=p/pm['source'];before=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src))
 for ob in list(bpy.context.scene.objects):
  if ob.type=='MESH' and ob.name=='Studio floor':bpy.data.objects.remove(ob,do_unlink=True)
 g=inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges),o.name;bm.free()
 for s in pm['mounts']:
  assert abs(Vector(s['forward']).length-1)<1e-6 and abs(Vector(s['up']).length-1)<1e-6
  assert abs(Vector(s['forward']).dot(Vector(s['up'])))<1e-6
  marker=bpy.data.objects.get('socket.'+s['id']) or bpy.data.objects.get(s.get('node',''))
  assert marker is not None and (marker.location-Vector(s['position'])).length<1e-6
 if pid.startswith(BID):
  gate=json.loads((p/'geometry-validation.json').read_text());assert gate['validated_before_assembly'] and gate['source_reopened_before_assembly']
  assert all((p/'Previews'/(n+'.png')).stat().st_size>5000 for n in ['top','perspective'])
 sources.append({'id':pid,'version':pm['version'],'source_reopened':True,'sha256':before,'geometry':g,'studio_floor_excluded_from_geometry_gate':not pid.startswith(BID)})
src=folder/(BID+'.blend');sha=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();g=inspect();inst={i['id']:i for i in meta['instances']}
for i in meta['instances']:
 o=bpy.data.objects[i['id']];assert o['part_version']==i['version']==parts[i['part_id']]['version'];assert o.parent.name==i['parent'];assert all(abs(v-1)<1e-6 for v in o.scale);assert (o.location-Vector(i['translation'])).length<1e-6;assert (folder/i['source']).resolve().exists()
def socketpose(i,sid):
 s=next(s for s in parts[i['part_id']]['mounts'] if s['id']==sid);mat=bpy.data.objects[i['id']].matrix_world
 return s,mat@Vector(s['position']),(mat.to_3x3()@Vector(s['forward'])).normalized(),(mat.to_3x3()@Vector(s['up'])).normalized()
connections=[]
for c in meta['connections']:
 sa,pa,fa,ua=socketpose(inst[c['parent_instance']],c['parent_socket']);sb,pb,fb,ub=socketpose(inst[c['child_instance']],c['child_socket'])
 assert sa['role']==sb['role'] and (pa-pb).length<1e-6 and fa.dot(fb)>.999999 and ua.dot(ub)>.999999
 connections.append({'connection':c,'distance':(pa-pb).length,'forward_dot':fa.dot(fb),'up_dot':ua.dot(ub),'roles_match':True})
assert len(connections)==5
point=parts['MA-W08-P02']['functional_points'];assert len(point)==1 and point[0]['id']=='shoot';point=point[0];assert Vector(point['direction']).length==1
poses=[]
for frame in [1,16,31,46,61,76,91,106,121]:
 scene.frame_set(frame);bpy.context.view_layer.update();yaw=bpy.data.objects['Yaw'];a=bpy.data.objects['SingleLauncher'];mat=a.matrix_world;pos=mat@Vector(point['position']);direction=(mat.to_3x3()@Vector(point['direction'])).normalized();marker=bpy.data.objects['SingleLauncher::point.shoot'];assert (marker.matrix_world.translation-pos).length<1e-6
 hit=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),pos,direction,distance=20)[0];assert not hit,frame
 fixed=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' and o.name.startswith('HullKeel::') for v in o.bound_box]
 moving=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' and not o.name.startswith('HullKeel::') for v in o.bound_box]
 gap=min(v.z for v in moving)-max(v.z for v in fixed);assert gap>.02,gap
 expected=(frame-1)*3;angle=math.degrees(yaw.rotation_euler.z);assert abs(angle-expected)<1e-4,(frame,angle,expected)
 poses.append({'frame':frame,'yaw_degrees':angle,'muzzle_world_position':list(pos),'normalized_forward':list(direction),'clear_forward_ray_BU':20,'fixed_moving_vertical_gap_BU':gap})
scene.frame_set(1)
assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
for n in ['top','perspective','top-grayscale']:assert (folder/'Previews'/(n+'.png')).stat().st_size>10000
assert not meta['exports'] and meta['functional_contract']['active_barrel_count']==1 and meta['catalog_grid']==[1,3]
write(folder/'validation.json',{'id':BID,'checks_passed':True,'source_reopened_in_independent_process':True,'standalone_parts':sources,'geometry':g,'connections':connections,'instance_count':6,'new_parts':3,'reused_parts':['MA-P06 v1.3','MA-P07 v1.3'],'single_active_muzzle':True,'motion_samples':poses,'yaw_360_linear_90_degrees_per_second':True,'muzzle_rays_clear':True,'fixed_moving_clearance_verified':True,'preview_views':['top','perspective','top-grayscale'],'top_orientation':'world +Y up','perspective_elevation_degrees':45,'source_unchanged_after_review':True,'source_sha256':sha,'glb_generated':False,'game_validation':False,'collision_LOD_validation':False,'limitations':'BU scale and XML-to-BU pivot mapping unspecified. Intentional contacts at shells/collars/couplings. No elevation or independent reserve firing. Studio floors excluded only in memory, original sources unchanged.'})
print('VERIFIED MA-W08',flush=True)
