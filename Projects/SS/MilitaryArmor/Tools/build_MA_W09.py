"""MA-W09 short heavy shotgun turret; standalone checked parts, no exports."""
import bpy,bmesh,sys,math,json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import weapon_batch_core as core
ROOT=core.ROOT; write=core.write

def socket(sid,pos,role):
 return {'id':sid,'role':role,'position':list(pos),'forward':[0,-1,0],'up':[0,0,1],'compatible_role':role,'compatibility':[role],'allowed_scale':[1,1,1],'node':'socket.'+sid}

def geometry(objects=None):
 out=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in (objects if objects is not None else bpy.context.scene.objects):
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  d={'name':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'positive_volume':bm.calc_volume(signed=True)>0,'normals_consistent':all(e.is_contiguous for e in bm.edges)};bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();d['evaluated_zero_area_triangles']=sum(t.area<1e-10 for t in me.loop_triangles);d['finite']=all(math.isfinite(c) for v in me.vertices for c in v.co);ev.to_mesh_clear()
  assert not d['nonmanifold_edges'] and not d['zero_area_faces'] and d['positive_volume'] and d['normals_consistent'] and not d['evaluated_zero_area_triangles'] and d['finite'],d
  assert o.data.materials and all(m for m in o.data.materials),o.name
  out.append(d)
 assert out
 return out

def previews(folder):
 scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
 pts=[o.matrix_world@Vector(p) for o in scene.objects if o.type=='MESH' for p in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);target=(lo+hi)/2
 scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
  for d in prefs.devices:d.use=d.type=='OPTIX'
  scene.cycles.device='GPU'
 except Exception:pass
 scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('MA-W09 review world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
 tmp=[]
 for off,power,size in [((3,-5,8),1500,5),((-5,-1,5),1100,5),((2,5,6),1800,4)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(off));o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();tmp.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';tmp.append(cam)
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 for name,direction in [('perspective',Vector((1,-1,1.41421356)).normalized()),('top',Vector((0,0,1))),('top-grayscale',Vector((0,0,1)))]:
  cam.location=target+direction*20;cam.rotation_euler=(0,0,0) if name.startswith('top') else (-direction).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();local=[cam.matrix_world.inverted()@p for p in pts];cam.data.ortho_scale=max(max(p.x for p in local)-min(p.x for p in local),max(p.y for p in local)-min(p.y for p in local))*1.23
  saved=[]
  if name.endswith('grayscale'):
   for m in bpy.data.materials:
    if not m.use_nodes:continue
    p=m.node_tree.nodes.get('Principled BSDF')
    if not p:continue
    saved.append((p,tuple(p.inputs['Base Color'].default_value),tuple(p.inputs['Emission Color'].default_value)))
    for key in ['Base Color','Emission Color']:
     col=p.inputs[key].default_value;v=.2126*col[0]+.7152*col[1]+.0722*col[2];p.inputs[key].default_value=(v,v,v,col[3])
  scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
  for p,col,em in saved:p.inputs['Base Color'].default_value=col;p.inputs['Emission Color'].default_value=em
 for o in tmp:bpy.data.objects.remove(o,do_unlink=True)

def cradle(c):
 c.section('Low dense receiver cradle',[(-1.25,0,.25,1.65,.44,.15),(-.85,0,.48,2.75,.80,.22),(.85,0,.48,2.75,.80,.22),(1.50,0,.36,1.88,.60,.17)],'Dark')
 for s in [-1,1]:
  c.section('Short angular trunnion cheek',[(-1.38,s*1.05,.50,.34,.55,.12),(-.75,s*1.22,.65,.48,.86,.17),(.60,s*1.18,.66,.48,.88,.17),(1.28,s*.93,.47,.32,.57,.11)],'Ceramic')
  c.cyl('Sealed elevation pivot',(s*1.20,-.45,.70),.32,.22,'Titanium',axis='X',verts=24)
  c.cyl('Angular pivot lid',(s*1.33,-.45,.70),.26,.055,'Armor',axis='X',verts=8)
  c.box('Flush drive index',(s*1.374,-.45,.70),(.014,.10,.10),'Signal',.003)
 c.panel('Rear armored brow',(0,1.0,1.12),(1.68,.74,.14),'Armor',.22)
 c.panel('Optic landing',(0,1.0,1.215),(.86,.72,.05),'Titanium',.10)

def gun(c):
 c.section('Massive locking breech',[(-.20,0,.02,1.65,.95,.25),(.35,0,.04,1.78,1.06,.27),(1.1,0,.02,1.58,.94,.24),(1.48,0,0,1.12,.65,.17)],'Titanium')
 c.panel('Thick breech ceramic cap',(0,.63,.60),(1.38,1.32,.16),'Ceramic',.25)
 c.panel('Breech inset',(0,.63,.69),(.62,.64,.045),'Dark',.12)
 for y in [.40,.63,.86]:c.box('Lock status slit',(0,y,.716),(.30,.035,.009),'Signal',.002)
 # One hollow bore; rings are coaxial wall segments, never eight pellet barrels.
 c.ring('Short shotgun barrel',(0,-1.0,0),.57,.36,1.70,'Y','Titanium',verts=32)
 c.ring('Broad eight-sided muzzle collar',(0,-1.92,0),.70,.36,.30,'Y','Ceramic',verts=8)
 c.ring('Inset muzzle wear rim',(0,-2.082,0),.45,.36,.035,'Y','Steel',verts=32)
 for y in [-.48,-.95,-1.42]:c.ring('Short segmented heat shroud',(0,y,0),.63,.575,.20,'Y','Armor',verts=8)
 for s in [-1,1]:
  c.cyl('Closed recoil cylinder',(s*.70,-.12,-.48),.15,1.26,'Dark',axis='Y',verts=16)
  c.cyl('Inset recoil slide',(s*.70,-.87,-.48),.075,.35,'Steel',axis='Y',verts=16)
 c.panel('Breech rear locking plate',(0,1.48,0),(.98,.12,.55),'Armor',.14)

def magazine(c):
 c.cyl('Single lateral feed cassette',(0,0,0),.66,.64,'Titanium',axis='X',verts=12)
 c.cyl('Magazine armored outer face',(.35,0,0),.60,.09,'Ceramic',axis='X',verts=12)
 c.cyl('Recessed loading lock',(.403,0,0),.27,.025,'Dark',axis='X',verts=8)
 c.cyl('Magazine center seal',(.421,0,0),.13,.018,'Steel',axis='X',verts=8)
 for i in range(6):
  ang=2*math.pi*i/6;y=.43*math.sin(ang);z=.43*math.cos(ang)
  o=c.box('Magazine radial lock',( .414,y,z),(.027,.075,.17),'Armor',.014);o.rotation_euler.x=-ang
 for o in bpy.context.scene.objects:
  for mod in o.modifiers:
   if mod.type=='BEVEL':mod.width=min(mod.width,.002)
 c.box('Magazine diagnostic',(.438,0,.43),(.012,.13,.035),'Signal',.003)
 c.panel('Protected feed throat',(-.46,0,0),(.32,.64,.49),'Dark',.10)

def main():
 specs=[('MA-W09-P01','Dense shotgun cradle',cradle,[socket('bottom',(0,0,0),'yaw'),socket('elevation',(0,-.45,.70),'elevation'),socket('magazine',(1.22,.65,.52),'feed'),socket('optic',(0,1,1.24),'accessory')]),('MA-W09-P02','Short broad single-bore shotgun',gun,[socket('root',(0,0,0),'elevation')]),('MA-W09-P03','Lateral shotgun feed cassette',magazine,[socket('root',(-.62,0,0),'feed')])]
 for pid,title,fn,mounts in specs:
  if (ROOT/'Parts'/pid/'geometry-validation.json').exists():continue
  c=core.Part(pid,title);fn(c);checks=geometry()
  points=[{'id':'shoot','node':'socket.root','role':'muzzle','position':[0,-2.11,0],'forward':[0,-1,0],'direction':[0,-1,0],'up':[0,0,1]}] if pid.endswith('P02') else []
  c.save(mounts,points,notes='Unit scale. Uniform PBR procedural materials; no file textures or UV dependence. Standalone source validated before assembly.')
  write(ROOT/'Parts'/pid/'geometry-validation.json',{'checks_passed':True,'validated_before_assembly':True,'meshes':checks});previews(ROOT/'Parts'/pid/'Previews')
 a=core.Assembly('MA-W09','shotgun-turret',[1,2],'Short heavy single-bore shotgun turret')
 a.instance('Hardpoint','MA-W06-P01');yaw=a.node('Yaw',a.root,(0,0,1));a.instance('Cradle','MA-W09-P01',yaw)
 elev=a.node('Elevation',yaw,(0,-.45,.70));recoil=a.node('Recoil',elev);a.instance('Gun','MA-W09-P02',recoil)
 a.instance('Magazine','MA-W09-P03',yaw,(1.84,.65,.52));a.instance('Optic','MA-P07',yaw,(0,1,1.24))
 a.animate_rotation(yaw,'Z',[(1,0),(30,-70),(60,0),(90,70),(120,0)])
 a.animate_rotation(elev,'X',[(1,0),(30,-10),(60,5),(90,-10),(120,0)])
 a.animate_location(recoil,'Y',[(1,0),(40,0),(43,.16),(53,0),(120,0)])
 scene=bpy.context.scene;scene.frame_end=120;scene.frame_set(1);bpy.context.view_layer.update();folder=ROOT/'Blocks/MA-W09';checks=geometry()
 connections=[{'parent_instance':'Hardpoint','parent_socket':'yaw','child_instance':'Cradle','child_socket':'bottom'},{'parent_instance':'Cradle','parent_socket':'elevation','child_instance':'Gun','child_socket':'root'},{'parent_instance':'Cradle','parent_socket':'magazine','child_instance':'Magazine','child_socket':'root'},{'parent_instance':'Cradle','parent_socket':'optic','child_instance':'Optic','child_socket':'bottom'}]
 meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':'MA-W09','version':'1.0','title':a.title,'catalog_id':'shotgun-turret','catalog_grid':[1,2],'axes':core.AXES,'instances':a.instances,'nodes':[{'id':o.name,'parent':o.parent.name if o.parent else None,'translation':list(o.location),'rotation_euler_xyz':list(o.rotation_euler),'scale':list(o.scale)} for o in a.nodes],'connections':connections,'animations':{'fps':scene.render.fps,'frame_range':[1,120],'channels':a.clips,'demonstration_only':True},'functional_points':[{'id':'shoot','part_instance':'Gun','part_point':'shoot'}],'catalog_contract':{'barrel_count':1,'projectiles_per_shot':8,'firing_arc_degrees':140,'rotate_speed_degrees_per_second':120,'pivot_grid':[.5,1]},'exports':[],'notes':'Catalog grid is not BU metres. Yaw arc ±70 matches catalog. Elevation and recoil are artistic demonstration only. One barrel and eight pellets, not eight barrels. Colliders, LOD and engine integration unspecified.'}
 write(folder/'assembly.json',meta);bpy.ops.wm.save_as_mainfile(filepath=str(folder/'MA-W09.blend'));previews(folder/'Previews')
 write(folder/'README.md','# MA-W09 — Турель-дробовик\n\nКороткий широкий полый ствол с восьмигранным дульным поясом, массивная казённая часть, низкая люлька и один боковой магазин. Один физический ствол, 8 дробин по каталогу; размер 1×2, дуга 140°.\n\nИсходник MA-W09.blend. Новые детали MA-W09-P01/P02/P03 v1.0; фундамент MA-W06-P01 v1.0 и лидар MA-P07 v1.3 повторно использованы без изменений и масштаба. Состав и sockets: assembly.json и composition-plan.md. Превью: Previews/perspective.png, top.png, top-grayscale.png.\n\nАнимация yaw ±70°; elevation и отдача служат демонстрацией авторинга. Физический масштаб BU, LOD, коллайдеры и игровой экспорт не согласованы. GLB не создавался. Игровая интеграция не проверялась.')
 print('BUILT MA-W09',flush=True)
if __name__=='__main__':main()
