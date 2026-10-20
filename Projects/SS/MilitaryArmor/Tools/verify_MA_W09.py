"""Independent Blender reopen acceptance for MA-W09, no exports."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_MA_W09 import geometry
from weapon_batch_core import ROOT,write
folder=ROOT/'Blocks/MA-W09';meta=json.loads((folder/'assembly.json').read_text());parts=[]
for pid in sorted(set(i['part_id'] for i in meta['instances'])):
 p=ROOT/'Parts'/pid;data=json.loads((p/'part.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(p/data['source']));checks=geometry(bpy.data.collections[pid].objects)
 if pid.startswith('MA-W09-'):assert bpy.context.scene.unit_settings.system=='NONE'
 for m in data['materials']:
  assert m['id'] in bpy.data.materials
  for name in m['surfaces']:assert name in bpy.data.objects
 for s in data['mounts']:
  assert abs(Vector(s['forward']).length-1)<1e-6 and abs(Vector(s['up']).length-1)<1e-6 and abs(Vector(s['forward']).dot(Vector(s['up'])))<1e-6
  node=bpy.data.objects.get(s.get('node','socket.'+s['id']))
  assert node and (node.location-Vector(s['position'])).length<1e-6
 if pid.startswith('MA-W09-'):
  assert json.loads((p/'geometry-validation.json').read_text())['validated_before_assembly']
  for name in ['top','perspective','top-grayscale']:assert (p/'Previews'/(name+'.png')).stat().st_size>5000
 parts.append({'id':pid,'version':data['version'],'source_reopened':True,'geometry':checks})
bpy.ops.wm.open_mainfile(filepath=str(folder/'MA-W09.blend'));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();meshes=geometry();instances={i['id']:i for i in meta['instances']}
for i in meta['instances']:
 o=bpy.data.objects[i['id']];pm=json.loads((ROOT/'Parts'/i['part_id']/'part.json').read_text())
 assert pm['version']==i['version']==o['part_version'];assert (folder/i['source']).resolve().exists()
 assert o.parent.name==i['parent'] and (o.location-Vector(i['translation'])).length<1e-6
 assert all(abs(v-1)<1e-6 for v in o.scale)
def mount(i,sid):return next(s for s in json.loads((ROOT/'Parts'/i['part_id']/'part.json').read_text())['mounts'] if s['id']==sid)
def pose(i,s):
 mat=bpy.data.objects[i['id']].matrix_world
 return mat@Vector(s['position']),(mat.to_3x3()@Vector(s['forward'])).normalized(),(mat.to_3x3()@Vector(s['up'])).normalized()
connections=[]
for c in meta['connections']:
 a=instances[c['parent_instance']];b=instances[c['child_instance']];sa=mount(a,c['parent_socket']);sb=mount(b,c['child_socket']);pa,fa,ua=pose(a,sa);pb,fb,ub=pose(b,sb)
 assert sa['role']==sb['role'] and (pa-pb).length<1e-6 and fa.dot(fb)>.99999 and ua.dot(ub)>.99999
 connections.append({'connection':c,'distance':(pa-pb).length,'forward_dot':fa.dot(fb),'up_dot':ua.dot(ub),'compatible_role':sa['role']})
assert len(connections)==len(instances)-1
poses=[]
for frame in [1,15,30,40,43,53,60,75,90,120]:
 scene.frame_set(frame);bpy.context.view_layer.update();geometry()
 yaw=bpy.data.objects['Yaw'];assert abs(yaw.rotation_euler.z)<=math.radians(70)+1e-5
 gun=bpy.data.objects['Gun'];pt=gun.matrix_world@Vector((0,-2.12,0));direction=(gun.matrix_world.to_3x3()@Vector((0,-1,0))).normalized();hits=[]
 # Rays begin in the muzzle opening and sample its cross-section, then travel forward.
 for x,z in [(0,0),(.20,0),(-.20,0),(0,.20),(0,-.20)]:
  origin=gun.matrix_world@Vector((x,-2.12,z));hit=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,direction,distance=8)[0];assert not hit,(frame,origin)
  hits.append({'origin':list(origin),'direction':list(direction),'clear_BU':8})
 poses.append({'frame':frame,'yaw_degrees':math.degrees(yaw.rotation_euler.z),'muzzle_position':list(pt),'muzzle_direction':list(direction),'sampled_muzzle_rays':hits})
scene.frame_set(1)
for name in ['top','perspective','top-grayscale']:assert (folder/'Previews'/(name+'.png')).stat().st_size>5000
assert meta['catalog_id']=='shotgun-turret' and meta['catalog_grid']==[1,2]
assert meta['catalog_contract']['barrel_count']==1 and meta['catalog_contract']['projectiles_per_shot']==8 and meta['catalog_contract']['firing_arc_degrees']==140
assert not meta['exports']
write(folder/'validation.json',{'id':'MA-W09','checks_passed':True,'source_reopened':True,'independent_Blender_process':True,'standalone_parts':parts,'assembly_geometry':meshes,'connections':connections,'source_parts_saved_and_validated_before_assembly':True,'instance_count':len(instances),'resolved_parts':sorted(set(i['part_id'] for i in instances.values())),'animation_poses':poses,'preview_views':['perspective','top','top-grayscale'],'grayscale_override_temporary':True,'muzzle_count':1,'catalog_projectiles_per_shot':8,'glb_generated':False,'game_validation':False,'collision_LOD_validation':False,'notes':'Sockets align at bind pose; gun socket follows elevation and recoil subsequently. Yaw catalog ±70deg; elevation/recoil artistic only. Designed seat/receiver/feed-throat intersections intentional; no broad boolean-intersection guarantee.'})
print('VERIFIED MA-W09',flush=True)
