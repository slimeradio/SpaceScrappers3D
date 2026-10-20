"""MA-W08 single-channel rocket turret. Source parts gated before assembly; no exports."""
import sys,math,json,hashlib
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,Part,Assembly,AXES,write
from redesign_compute_production import inspect
BID='MA-W08';folder=ROOT/'Blocks'/BID
class Model(Part):
 def finish(self,o,name,mat,bevel=0):return super().finish(o,name,mat,0)
def sock(i,pos,role):return {'id':i,'parent':'part','role':role,'position':list(pos),'forward':[0,-1,0],'up':[0,0,1],'compatible_role':role,'allowed_scale':[1,1,1]}
def review(p,target,scale,gray=False,res=640):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
  for dev in prefs.devices:dev.use=dev.type=='OPTIX'
  scene.cycles.device='GPU'
 except Exception:pass
 scene.render.resolution_x=res;scene.render.resolution_y=res;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.06,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
 t=Vector(target);added=[]
 for loc,power,size in [((2,-5,8),1500,5),((-4,-1,5),1100,4),((3,5,6),1800,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 (p/'Previews').mkdir(parents=True,exist_ok=True)
 for name,off in [('top',(0,0,10)),('perspective',(7,-7,9.899494936611665))]:
  cam.location=t+Vector(off);cam.rotation_euler=(0,0,0) if name=='top' else (t-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(p/'Previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
 if gray:
  mat=bpy.data.materials.new('Temporary gray');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.33,.33,.33,1);scene.view_layers[0].material_override=mat;cam.location=t+Vector((0,0,10));cam.rotation_euler=(0,0,0);scene.render.filepath=str(p/'Previews/top-grayscale.png');bpy.ops.render.render(write_still=True);scene.view_layers[0].material_override=None
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def savepart(m,mounts,points=[]):
 check=inspect();m.save(mounts=mounts,points=points,notes='MilitaryArmor single-channel rocket authoring; editable procedural PBR, no file textures, no UV dependency; static source part, no GLB.')
 p=ROOT/'Parts'/m.pid;meta=json.loads((p/'part.json').read_text());meta['attachment_areas']=[]
 for pt in points:
  o=bpy.data.objects.new('point.'+pt['id'],None);m.coll.objects.link(o);o.location=pt['position'];o['direction']=pt['direction'];o['up']=pt['up'];o['role']=pt['role']
 bpy.ops.wm.save_as_mainfile(filepath=str(p/(m.pid+'.blend')))
 write(p/'part.json',meta);write(p/'geometry-validation.json',check)
 lo=meta['bounds_local']['min'];hi=meta['bounds_local']['max'];review(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.3,res=500)
 write(p/'README.md',f'# {m.pid} v1.0\n\n{m.title}. Редактируемый самостоятельный источник. Геометрия проверена до сборки; geometry-validation.json. Крепления, PBR и эмиссия в part.json; без файловых текстур/UV. Статичная деталь, BU условные, единичный масштаб; без GLB. Previews/top.png и perspective.png.\n')

def main():
 write(folder/'composition-plan.md','''# MA-W08 — ракетная турель 1×3

Каталог rocket-turret: один rocket-barrel, один ShootPosition, ProjectilesPerShot=1. Полный азимут 360°, скорость XML 90°/с. Pivot XML (0.5,0.5) остаётся в координатах игровой сетки; его перевод в BU не установлен. BU условные, +Z вверх, -Y вперёд. Один открытый центральный пусковой канал; две закрытые запасные кассеты не являются стволами. Нет самостоятельных залпов и выдуманного наведения по высоте.

До моделирования проверены MA-W05-P01/P02/P03, MA-W06-P01/P02/P03, MA-P06 и MA-P07 v1.3. Артиллерийские люльки и ускорители не подходят прямому ракетному каналу; их изменение либо масштабирование нарушит исходные unit-only интерфейсы. Новые MA-W08-P01 — узкий разнесённый опорный киль с полным поворотным венцом; MA-W08-P02 — один длинный открытый ракетный канал и защищённый замок сзади; MA-W08-P03 — закрытая продольная запасная кассета (два экземпляра). Повторно использовать MA-P06 (сервисный картридж) и MA-P07 (лидар) v1.3 без изменения и масштаба.

Каждая новая деталь сохраняется, немедленно проверяется и рендерится до сборки. Сборка экземплярами, логические sockets с полной ориентацией; yaw-only анимация демонстрирует все 360° за 4с. LOD, коллайдеры, физический масштаб, маппинг XML→BU и интеграция не определены. GLB не создавать.
''')
 if '--assembly-only' not in sys.argv:
  m=Model('MA-W08-P01','Narrow split rocket-turret support keel')
  for x in [-.64,.64]:
   m.section('Separated hull anchor spar',[(-2.62,x,.12,.30,.20,.06),(-1.99,x,.21,.37,.34,.08),(2.39,x,.21,.37,.34,.08),(2.72,x,.12,.27,.20,.06)],'Armor')
   for y in [-2.14,2.14]:m.panel('Low ceramic anchor pad',(x,y,.41),(.38,.70,.10),'Ceramic',.08)
  for y in [-1.72,1.71]:m.box('Recessed transverse tie',(0,y,.15),(1.13,.23,.19),'Titanium')
  m.cyl('Protected azimuth drive',(0,.46,.35),.72,.39,'Dark',verts=40)
  m.ring('Continuous 360 degree bearing',(0,.46,.56),.79,.58,.19,mat='Steel',verts=40)
  m.cyl('Sealed bearing crown',(0,.46,.665),.60,.08,'Titanium',verts=40)
  savepart(m,[sock('hull',(0,0,0),'hull'),sock('yaw',(0,.46,.72),'yaw')])
  m=Model('MA-W08-P02','Single open polygonal rocket launch canister')
  # Central open tube: one actual projectile channel, front is -Y.
  m.ring('Long octagonal launch tube',(0,-.36,.56),.48,.37,4.62,axis='Y',mat='Titanium',verts=8)
  for y in [-2.68,-2.39,-1.26,.07,1.96]:
   m.ring('External canister reinforcing collar',(0,y,.56),.55,.475,.14,axis='Y',mat='Armor',verts=8)
  m.ring('Bright open muzzle seal',(0,-2.79,.56),.51,.375,.10,axis='Y',mat='Ceramic',verts=8)
  # Rear closure is behind the firing origin. Forward aperture is unobstructed.
  m.cyl('Closed rear rocket chamber',(0,2.02,.56),.46,.15,'Dark',axis='Y',verts=8)
  m.section('Tapered rear locking breech',[(1.48,0,.57,1.02,.93,.20),(2.03,0,.57,1.02,.93,.20),(2.35,0,.51,.60,.61,.15)],'Armor')
  m.panel('Rear service shelf',(0,1.74,1.08),(.89,.76,.12),'Ceramic',.12)
  for x in [-.28,.28]:
   m.box('Lower launch support',(x,.11,.11),(.15,2.57,.20),'Dark')
   for y in [-1.77,-.60,.58]:m.panel('Segmented upper canister armor',(x,y,1.028),(.25,.91,.12),'Ceramic',.07)
  for x in [-.68,.68]:m.box('Reserve cassette coupling',(x,.33,.48),(.27,2.64,.20),'Steel')
  m.panel('Forward optic seat',(0,-1.70,1.12),(.83,.74,.10),'Titanium',.09)
  m.box('Small chamber state index',(.46,1.42,.90),(.023,.19,.07),'Optic')
  pts=[{'id':'shoot','role':'muzzle','parent':'part','node':'point.shoot','position':[0,-2.86,.56],'direction':[0,-1,0],'forward':[0,-1,0],'up':[0,0,1]}]
  savepart(m,[sock('root',(0,0,0),'yaw'),sock('reserve-left',(-.74,.33,.48),'reserve'),sock('reserve-right',(.74,.33,.48),'reserve'),sock('service',(0,1.74,1.14),'accessory'),sock('optic',(0,-1.70,1.17),'accessory')],pts)
  m=Model('MA-W08-P03','Sealed elongated reserve rocket cassette')
  m.section('Closed spare rocket cassette',[(-1.90,0,.04,.29,.39,.07),(-1.63,0,.07,.40,.51,.10),(1.28,0,.07,.40,.51,.10),(1.70,0,.00,.28,.37,.07)],'Armor')
  for y in [-1.32,-.39,.54]:
   m.section('Spare cassette ceramic shell',[(y-.37,0,.34,.37,.12,.03),(y+.28,0,.34,.37,.12,.03)],'Ceramic')
   m.box('Recessed cassette division',(0,y+.36,.33),(.26,.06,.07),'Dark')
  m.panel('Blind faceted nose cap',(0,-1.82,.25),(.25,.21,.10),'Steel',.04)
  m.panel('Rear release lock',(0,1.39,.28),(.23,.31,.06),'Titanium',.04)
  savepart(m,[sock('root',(0,0,0),'reserve')])
 # Reopen and gate all source parts before assembly dependency.
 for pid in ['MA-W08-P01','MA-W08-P02','MA-W08-P03','MA-P06','MA-P07']:
  p=ROOT/'Parts'/pid;bpy.ops.wm.open_mainfile(filepath=str(p/(pid+'.blend')))
  for ob in list(bpy.context.scene.objects):
   if ob.type=='MESH' and ob.name=='Studio floor':bpy.data.objects.remove(ob,do_unlink=True)
  check=inspect()
  if pid.startswith(BID):check['source_reopened_before_assembly']=True;write(p/'geometry-validation.json',check)
 a=Assembly(BID,'rocket-turret',[1,3],'Ракетная турель 1×3')
 a.instance('HullKeel','MA-W08-P01');yaw=a.node('Yaw',a.root,(0,.46,.72));a.instance('SingleLauncher','MA-W08-P02',yaw)
 a.instance('SpareLeft','MA-W08-P03',yaw,(-.74,.33,.48));a.instance('SpareRight','MA-W08-P03',yaw,(.74,.33,.48))
 a.instance('Service','MA-P06',yaw,(0,1.74,1.14));a.instance('Lidar','MA-P07',yaw,(0,-1.70,1.17))
 a.animate_rotation(yaw,'Z',[(1,0),(31,90),(61,180),(91,270),(121,360)])
 # Linear 30fps*4s demonstration matches 90deg/s XML; no gameplay coupling implied.
 scene=bpy.context.scene;scene.render.fps=30;scene.frame_end=121
 for act in bpy.data.actions:
  for slot in act.slots:
   for layer in act.layers:
    for strip in layer.strips:
     try:
      for fc in strip.channelbag(slot).fcurves:
       for key in fc.keyframe_points:key.interpolation='LINEAR'
     except Exception:pass
 scene.frame_set(1);bpy.context.view_layer.update();inspect()
 cons=[{'parent_instance':'HullKeel','parent_socket':'yaw','child_instance':'SingleLauncher','child_socket':'root','motion_node':'Yaw','axis':[0,0,1],'range_degrees':[0,360]}]
 for iid,sid in [('SpareLeft','reserve-left'),('SpareRight','reserve-right'),('Service','service'),('Lidar','optic')]:cons.append({'parent_instance':'SingleLauncher','parent_socket':sid,'child_instance':iid,'child_socket':'bottom' if iid in ['Service','Lidar'] else 'root'})
 meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':'rocket-turret','catalog_grid':[1,3],'axes':AXES,'instances':a.instances,'nodes':[{'id':o.name,'parent':o.parent.name if o.parent else None,'translation':list(o.location),'rotation_euler_xyz':list(o.rotation_euler),'scale':list(o.scale)} for o in a.nodes],'connections':cons,'animations':{'fps':30,'frame_range':[1,121],'channels':a.clips,'interpolation':'LINEAR','demonstration_only':True},'functional_contract':{'active_barrel_count':1,'projectiles_per_shot':1,'muzzle_instance':'SingleLauncher','muzzle_point':'shoot','yaw_arc_degrees':360,'yaw_speed_degrees_per_second':90,'elevation':'none; catalog does not establish 3D elevation','reserve_cassettes':'closed visual stores; no independent firing points','xml_pivot':[.5,.5],'xml_to_BU_mapping':'unspecified; yaw BU pivot is authoring only'},'exports':[],'notes':'Procedural authoring source. No GLB, game installation, collider or LOD; physical scale unspecified. Central launch bore is open; spare cassettes are visibly closed.'}
 write(folder/'assembly.json',meta);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));review(folder,(0,-.10,1.02),7.15,True,res=900)
 write(folder/'README.md','''# MA-W08 — ракетная турель 1×3

Один длинный открытый восьмигранный ракетный пусковой канал, две закрытые запасные кассеты, короткий задний замок и разнесённый узкий опорный киль. Свой узнаваемый силуэт: нет пулемётных стволов или сегментов ускорителя. Сервисный картридж и лидар повторно использованы без изменения.

MA-W08.blend — редактируемый источник, assembly.json — стабильные экземпляры, версии, движения и связи logical sockets. Новые MA-W08-P01/P02/P03 v1.0; повторно использованы MA-P06/MA-P07 v1.3. Шесть экземпляров из пяти деталей. Каждая новая деталь отдельно сохранена, проверена и имеет top/perspective до сборки. Previews/top.png, perspective.png и top-grayscale.png.

Каталог rocket-turret: один ствол и одна точка пуска, ProjectilesPerShot=1. Две закрытые кассеты не являются действующими стволами. Азимут 360°, демонстрация 90°/с; высотное наведение не добавлено. XML pivot (0.5,0.5) не переводился в BU: игровое преобразование не согласовано. Странное имя Turret laser-beam-turret в исходном XML не менялось. Процедурные PBR, ограниченная эмиссия диагностики; файловых текстур/UV нет. BU условные, LOD/коллайдеры/игровая интеграция не выполнялись. GLB не создавался. Независимая повторная проверка — validation.json.
''')
 print('BUILT MA-W08',flush=True)
if __name__=='__main__':
 if '--part-previews-only' in sys.argv:
  for pid in ['MA-W08-P01','MA-W08-P02','MA-W08-P03']:
   p=ROOT/'Parts'/pid;pm=json.loads((p/'part.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(p/pm['source']));lo=pm['bounds_local']['min'];hi=pm['bounds_local']['max'];review(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.3,res=500)
 else:main()
