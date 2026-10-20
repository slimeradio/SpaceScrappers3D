"""Fixed single-channel rocket launcher: standalone part gate then assembly; no GLB."""
import sys,json,hashlib
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,Assembly,write,AXES
from build_MA_W08 import Model,sock,savepart,review
from redesign_compute_production import inspect
BID='MA-W11';folder=ROOT/'Blocks'/BID
PIDS=['MA-W11-P01','MA-W08-P02','MA-W08-P03','MA-P06']

def main():
 write(folder/'composition-plan.md','''# MA-W11 — курсовая ракетная установка 1×3

Каталог rocket-launcher: один rocket-barrel, ShootPosition (0,1), ProjectilesPerShot=1. Нулевая дуга наведения и нулевая скорость поворота: поворачивается кораблём. XML pivot (0.5,2.5) не переводится в BU; соответствие сетки и BU не согласовано. +Z вверх, -Y вперёд, единичный масштаб.

Проверены MA-W08-P01/P02/P03, MA-P06 и MA-P07: готовый одинарный открытый канал MA-W08-P02 v1.0, закрытые запасные кассеты MA-W08-P03 v1.0 (два экземпляра) и сервис MA-P06 v1.3 подходят без изменений и масштаба. Опорный киль MA-W08-P01 с вращающимся венцом непригоден для курсового оружия. MA-P07 не требуется: дополнительное турельное наведение не изображается. Создать MA-W11-P01 v1.0 — широкую низкую неподвижную силовую раму с длинными наружными щеками и открытыми диагональными связями, без кругового постамента.

Новая рама создаётся, сохраняется и проверяется как самостоятельная деталь, с отдельными превью, ДО сборки. Все источники повторно открываются и проверяются. Пусковой канал и закрытые кассеты сохраняют родство с ракетным семейством, но широкая разнесённая рама и отсутствие поворотного узла отличают курсовую установку сверху и в объёме. Файловые текстуры/UV не нужны: процедурные PBR. Эмиссия рамы отсутствует. Анимаций нет. LOD/коллайдеры/игровой экспорт не входят в задачу; GLB не генерируется.
''')
 reused={p:hashlib.sha256((ROOT/'Parts'/p/(p+'.blend')).read_bytes()).hexdigest() for p in PIDS if not p.startswith(BID)}
 if '--assembly-only' not in sys.argv:
  m=Model('MA-W11-P01','Fixed launch cradle with splayed hull cheeks')
  for side in [-1,1]:
   x=side*1.05
   m.section('Long fixed exterior cheek',[(-2.67,x,.18,.31,.32,.07),(-2.10,x,.25,.45,.43,.09),(1.92,x,.25,.45,.43,.09),(2.61,x,.14,.30,.25,.05)],'Armor')
   for y in [-1.95,-.65,.65,1.95]:
    m.panel('Separated ceramic cheek cap',(x,y,.49),(.38,.92,.10),'Ceramic',.08)
   # Diagonal braces visible in top view, forming fixed triangular hull ties.
   for y in [-1.64,1.58]:
    m.stripe('Diagonal fixed hull brace',(side*.23,y-.32,.27),(side*.99,y+.31,.27),.16,'Steel')
   m.box('Recessed inner launch support',(side*.28,.11,.30),(.17,2.57,.22),'Titanium')
  for y in [-1.56,1.64]:m.box('Fixed transverse hull tie',(0,y,.16),(1.90,.24,.18),'Dark')
  m.panel('Rear tapered hardpoint',(0,2.30,.23),(1.65,.55,.20),'Armor',.18)
  savepart(m,[sock('hull',(0,0,0),'hull'),sock('fixed-launcher',(0,0,.40),'yaw')])
  pm=json.loads((ROOT/'Parts'/m.pid/'part.json').read_text());pm['notes']='Fixed static hull cradle. Socket role yaw is retained solely for compatibility with existing launcher root; no rotation node, bearing or animation. Procedural PBR, no emission, no textures or UV dependency.';write(ROOT/'Parts'/m.pid/'part.json',pm)
 # Mandatory reopened source gate precedes all assembly work.
 for pid in PIDS:
  p=ROOT/'Parts'/pid;bpy.ops.wm.open_mainfile(filepath=str(p/(pid+'.blend')))
  for o in list(bpy.context.scene.objects):
   if o.name=='Studio floor' and o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
  g=inspect()
  if pid.startswith(BID):g['source_reopened_before_assembly']=True;write(p/'geometry-validation.json',g)
 a=Assembly(BID,'rocket-launcher',[1,3],'Курсовая ракетная установка 1×3')
 a.instance('FixedFrame','MA-W11-P01')
 launch=a.instance('FixedLauncher','MA-W08-P02',loc=(0,0,.40))
 a.instance('ReserveLeft','MA-W08-P03',launch,(-.74,.33,.48))
 a.instance('ReserveRight','MA-W08-P03',launch,(.74,.33,.48))
 a.instance('Service','MA-P06',launch,(0,1.74,1.14))
 connections=[{'parent_instance':'FixedFrame','parent_socket':'fixed-launcher','child_instance':'FixedLauncher','child_socket':'root','constraint':'fixed; no rotational DOF'}]
 for iid,sid in [('ReserveLeft','reserve-left'),('ReserveRight','reserve-right'),('Service','service')]:connections.append({'parent_instance':'FixedLauncher','parent_socket':sid,'child_instance':iid,'child_socket':'bottom' if iid=='Service' else 'root'})
 bpy.context.scene.frame_end=1;bpy.context.view_layer.update();geometry=inspect()
 meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':'rocket-launcher','catalog_grid':[1,3],'axes':AXES,'instances':a.instances,'nodes':[{'id':o.name,'parent':o.parent.name if o.parent else None,'translation':list(o.location),'rotation_euler_xyz':list(o.rotation_euler),'scale':list(o.scale)} for o in a.nodes],'connections':connections,'animations':[],'functional_contract':{'active_barrel_count':1,'projectiles_per_shot':1,'muzzle_instance':'FixedLauncher','muzzle_point':'shoot','yaw_arc_degrees':0,'yaw_speed_degrees_per_second':0,'elevation':'none','aiming':'ship rotation only','reserve_cassettes':'sealed visual stores; no independent firing points','xml_pivot':[.5,2.5],'xml_to_BU_mapping':'unspecified; BU placement is authoring only'},'exports':[],'reused_source_sha256':reused,'notes':'Static fixed-hull launcher. Root socket role yaw belongs to reused source interface, not a movable bearing. No game XML edits, GLB, physical scale, colliders or LOD.'}
 write(folder/'assembly.json',meta);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
 review(folder,(0,-.10,.82),7.35,True,res=900)
 write(folder/'README.md','''# MA-W11 — курсовая ракетная установка 1×3

Один открытый восьмигранный канал закреплён на широкой низкой силовой раме. Длинные наружные щёки с раздельными керамическими плитами и диагональные связи передают усилие прямо в корпус. Кругового постамента и оси поворота нет; устройство наводится кораблём. Закрытые боковые запасные кассеты не являются стволами.

Исходник MA-W11.blend; метаданные assembly.json. Новая MA-W11-P01 v1.0, повторно использованы MA-W08-P02/P03 v1.0 и MA-P06 v1.3 без изменений. Пять экземпляров из четырёх источников; полные логические sockets и стабильные IDs. Новая деталь отдельно сохранена и проверена до сборки. Независимая проверка — validation.json. Previews/perspective.png (45°/45°), top.png (+Y вверх), top-grayscale.png.

Каталог rocket-launcher: один ствол и одна точка запуска, ProjectilesPerShot=1, нулевая дуга/скорость поворота. XML pivot (0.5,2.5) не преобразован в BU. Анимаций нет. Процедурные PBR; без файловых текстур и UV-зависимости. BU условные. Игровая интеграция, коллайдеры и LOD не выполнялись. GLB не создавались.
''')
 for pid,sha in reused.items():assert hashlib.sha256((ROOT/'Parts'/pid/(pid+'.blend')).read_bytes()).hexdigest()==sha
 print('BUILT MA-W11',flush=True)
if __name__=='__main__':main()
