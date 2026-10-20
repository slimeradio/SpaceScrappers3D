"""MA-W12 guided single-channel missile turret; parts first, no export."""
import sys,math,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,Assembly,AXES,write
from build_MA_W08 import Model,sock,review,savepart
from redesign_compute_production import inspect
BID='MA-W12';folder=ROOT/'Blocks'/BID
PIDS=['MA-W12-P01','MA-W12-P02','MA-W08-P01','MA-W08-P03','MA-P06','MA-P07']
def main():
 write(folder/'composition-plan.md','''# MA-W12 — турель самонаводящихся ракет 1×3

Каталог seeking-rocket-turret: один seeking-rocket-barrel, одна ShootPosition, ProjectilesPerShot=1, полный азимут 360°, 90°/с. Самонаведение относится к ракете; никаких дополнительных подвижных стволов, высотного наведения или игровых характеристик не добавляется. XML pivot (0.5,0.5) остаётся игровой величиной, преобразование в условные BU не определено.

Проверена библиотека MA-W08: P01 узкий киль и P03 закрытая запасная кассета подходят семейству и используются при единичном масштабе без изменения. MA-P06 и MA-P07 v1.3 подходят сервису и лидару, также reuse без изменения. MA-W08-P02 — голая круглая пусковая труба без направляющей электроники; изменение общего источника нарушило бы существующую сборку. Создать MA-W12-P01 — один широкий открытый канал с длинными боковыми коробами управления и разнесёнными направляющими. Создать MA-W12-P02 — крупная приподнятая поперечная оптическая вилка с двумя утопленными объективами, единым центральным блоком и боковыми выступами. Отличие от W08 читается в силуэте и сером верхнем виде, без зависимости от цвета.

Новые детали проверяются отдельно и после повторного открытия ДО сборки. Затем семь экземпляров из шести источников, логические sockets с позициями и полной ориентацией. Только yaw, линейная демонстрация полного оборота за 4с. Все источники editable Blender, процедурный PBR, без файловых текстур и UV-зависимости. GLB, игровые XML, LOD и коллайдеры не создаются. Неподвижная рама отделена вертикальным зазором от всего вращающегося узла.
''')
 if '--assembly-only' not in sys.argv:
  m=Model('MA-W12-P01','Guided missile launch channel with longitudinal control saddles')
  m.ring('Single hexagonal guided missile bore',(0,-.35,.60),.49,.36,4.64,axis='Y',mat='Titanium',verts=8)
  m.ring('One clear launch aperture',(0,-2.73,.60),.56,.36,.16,axis='Y',mat='Ceramic',verts=8)
  m.cyl('Sealed rear chamber',(0,2.02,.60),.48,.15,'Dark',axis='Y',verts=8)
  for x in [-.47,.47]:
   m.section('Long protected control conduit',[(-2.55,x,.61,.19,.37,.04),(-2.18,x,.61,.28,.50,.06),(1.52,x,.61,.28,.50,.06),(2.12,x,.61,.21,.39,.05)],'Armor')
   for y in [-1.83,-.77,.29,1.35]:m.panel('Control conduit segmented ceramic cover',(x,y,.90),(.23,.86,.10),'Ceramic',.04)
   m.box('Recessed conduit longitudinal slot',(x*1.31,-.3,.65),(.024,3.48,.09),'Dark')
   m.box('Channel basal saddle',(x,.22,.105),(.18,2.67,.19),'Titanium')
  m.section('Broad sloped guidance breech',[(1.38,0,.60,1.28,.88,.17),(2.02,0,.60,1.28,.88,.17),(2.38,0,.53,.74,.70,.17)],'Armor')
  m.panel('Rear service seat',(0,1.83,1.09),(.82,.62,.10),'Steel',.08)
  m.panel('Guidance mast foundation',(0,-.41,1.03),(1.26,1.20,.13),'Titanium',.09)
  for x in [-.77,.77]:m.box('Closed reserve attachment bridge',(x,.33,.48),(.34,2.62,.18),'Steel')
  pts=[{'id':'shoot','role':'muzzle','parent':'part','node':'point.shoot','position':[0,-2.84,.60],'direction':[0,-1,0],'forward':[0,-1,0],'up':[0,0,1]}]
  savepart(m,[sock('root',(0,0,0),'yaw'),sock('reserve-left',(-.85,.33,.48),'reserve'),sock('reserve-right',(.85,.33,.48),'reserve'),sock('guidance',(0,-.41,1.095),'guidance'),sock('service',(0,1.83,1.14),'accessory')],pts)
  m=Model('MA-W12-P02','Elevated fork-shaped optical missile guidance bridge')
  for x in [-.48,.48]:m.section('Armored guidance fork riser',[(-.51,x,.20,.27,.40,.05),(.27,x,.20,.27,.40,.05)],'Titanium')
  m.panel('Broad transverse faceted optical crown',(0,-.20,.57),(1.85,.87,.39),'Armor',.17)
  for x in [-.65,.65]:
   m.section('Extended forward optical hood',[(-.90,x,.57,.46,.40,.08),(-.63,x,.60,.52,.46,.09),(.10,x,.60,.52,.46,.09)],'Ceramic')
   m.cyl('Recessed black optical well',(x,-.918,.57),.155,.05,'Dark',axis='Y',verts=16)
   m.ring('Protective optical aperture ring',(x,-.951,.57),.13,.096,.025,axis='Y',mat='Steel',verts=16)
   m.cyl('Guidance objective',(x,-.956,.57),.093,.016,'Optic',axis='Y',verts=24)
  m.panel('Separate central guidance processor',(0,-.11,.83),(.55,.53,.19),'Ceramic',.07)
  for x in [-.15,.15]:m.box('Fine processor recessed channel',(x,-.11,.935),(.045,.29,.025),'Dark')
  m.panel('Rear lidar mounting shelf',(0,.27,.72),(.85,.34,.08),'Titanium',.05)
  savepart(m,[sock('root',(0,0,0),'guidance'),sock('lidar',(0,.27,.76),'accessory')])
 sources=[]
 for pid in PIDS:
  p=ROOT/'Parts'/pid;source=p/(pid+'.blend');sha=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source))
  for ob in list(bpy.context.scene.objects):
   if ob.type=='MESH' and ob.name=='Studio floor':bpy.data.objects.remove(ob,do_unlink=True)
  check=inspect();sources.append({'id':pid,'sha256':sha})
  if pid.startswith(BID):check['source_reopened_before_assembly']=True;write(p/'geometry-validation.json',check)
 a=Assembly(BID,'seeking-rocket-turret',[1,3],'Турель самонаводящихся ракет 1×3')
 a.instance('HullKeel','MA-W08-P01');yaw=a.node('Yaw',a.root,(0,.46,.72));a.instance('SingleLauncher','MA-W12-P01',yaw)
 a.instance('SpareLeft','MA-W08-P03',yaw,(-.85,.33,.48));a.instance('SpareRight','MA-W08-P03',yaw,(.85,.33,.48))
 g=a.instance('Guidance','MA-W12-P02',yaw,(0,-.41,1.095));a.instance('Lidar','MA-P07',g,(0,.27,.76));a.instance('Service','MA-P06',yaw,(0,1.83,1.14))
 a.animate_rotation(yaw,'Z',[(1,0),(31,90),(61,180),(91,270),(121,360)])
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
 for iid,sid in [('SpareLeft','reserve-left'),('SpareRight','reserve-right'),('Service','service'),('Guidance','guidance')]:cons.append({'parent_instance':'SingleLauncher','parent_socket':sid,'child_instance':iid,'child_socket':'bottom' if iid=='Service' else 'root'})
 cons.append({'parent_instance':'Guidance','parent_socket':'lidar','child_instance':'Lidar','child_socket':'bottom'})
 meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':'seeking-rocket-turret','catalog_grid':[1,3],'axes':AXES,'instances':a.instances,'source_sha256':sources,'nodes':[{'id':o.name,'parent':o.parent.name if o.parent else None,'translation':list(o.location),'rotation_euler_xyz':list(o.rotation_euler),'scale':list(o.scale)} for o in a.nodes],'connections':cons,'animations':{'fps':30,'frame_range':[1,121],'channels':a.clips,'interpolation':'LINEAR','demonstration_only':True},'functional_contract':{'active_barrel_count':1,'projectiles_per_shot':1,'muzzle_instance':'SingleLauncher','muzzle_point':'shoot','yaw_arc_degrees':360,'yaw_speed_degrees_per_second':90,'elevation':'none; catalog does not establish 3D elevation','reserve_cassettes':'closed visual stores; no independent firing points','guidance':'fixed optical guidance fork; missile seeking is catalog projectile behavior, not an extra animated weapon','xml_pivot':[.5,.5],'xml_to_BU_mapping':'unspecified; yaw BU pivot is authoring only'},'exports':[],'notes':'Editable authoring only; no game integration, GLB, LOD or colliders. Physical scale unspecified.'}
 write(folder/'assembly.json',meta);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));review(folder,(0,-.1,1.38),7.25,True,res=900)
 write(folder/'README.md','''# MA-W12 — турель самонаводящихся ракет 1×3

Один открытый канал с продольными бронированными коробами управления; над ним широкая оптическая вилка с двумя отдельными защищёнными объективами. Вилка и разнесённые длинные направляющие отличают управляемый вариант от MA-W08 даже в сером верхнем виде. Общий узкий киль и закрытые запасные кассеты сохраняют родство ракетного семейства.

MA-W12.blend — редактируемая сборка, assembly.json — стабильные экземпляры и трансформы sockets. Новые MA-W12-P01/P02 v1.0; повторно использованы MA-W08-P01/P03 v1.0, MA-P06/MA-P07 v1.3 без изменения и масштаба. Семь экземпляров из шести источников. Новые детали отдельно проверены и имеют самостоятельные top/perspective до сборки. Превью блока: Previews/perspective.png (45°/45°), top.png (+Y вверх), top-grayscale.png.

Каталог seeking-rocket-turret: один Barrel, одна точка пуска, ProjectilesPerShot=1. Азимут 360°, демонстрация 90°/с, высотное наведение не добавляется. Оптические окна и закрытые запасные кассеты не являются стволами. BU условные; маппинг pivot XML→BU, LOD, коллайдеры и интеграция не определены. Процедурные PBR, без файловых текстур/UV. GLB не создавался. Независимая проверка validation.json.
''')
 print('BUILT MA-W12',flush=True)
if __name__=='__main__':main()
