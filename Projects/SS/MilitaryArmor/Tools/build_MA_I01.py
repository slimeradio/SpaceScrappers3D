"""Cargo source authoring; individual evaluated geometry gates; no GLB."""
import sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-I01'; FOLDER=ROOT/'Blocks'/BID

def mount(i,p,tag):
 return {'id':i,'role':tag.split('.')[-1],'parent':'part','position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':[tag],'allowed_scale':[1,1,1]}

def inspect():
 checks=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  c={'mesh':o.name,'source_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'source_zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)};bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();c.update(evaluated_triangles=len(me.loop_triangles),zero_area_triangles=sum(t.area<1e-10 for t in me.loop_triangles),finite=all(math.isfinite(v) for p in me.vertices for v in p.co),materials_resolved=bool(o.material_slots) and all(s.material for s in o.material_slots));ev.to_mesh_clear()
  c['pass']=not c['source_nonmanifold_edges'] and not c['source_zero_area_faces'] and c['signed_volume']>0 and not c['zero_area_triangles'] and c['finite'] and c['materials_resolved'];checks.append(c)
 result={'checks_passed':bool(checks) and all(c['pass'] for c in checks),'meshes':checks,'validated_before_assembly':True}
 assert result['checks_passed'],str(result)
 return result

def preview(folder,target,scale,res=650):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=res;scene.render.resolution_y=res;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Cargo review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
 added=[];target=Vector(target)
 for loc,power,size in [((2,-5,8),1500,5),((-4,-1,5),1100,4),((3,5,6),1800,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 (folder/'Previews').mkdir(parents=True,exist_ok=True)
 for name,off in [('top',(0,0,8)),('perspective',(5,-7,6))]:
  cam.location=target+Vector(off);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/'Previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def finish(m,mounts):
 check=inspect();m.save(mounts=mounts,notes='Static cargo authoring part; uniform procedural PBR. No file textures, UV dependency or animated mechanism. BU are not metres.')
 p=ROOT/'Parts'/m.pid;d=json.loads((p/'part.json').read_text())
 d['attachment_areas']=[{'id':s['id']+'-seat','parent':'part','role':s['role'],'shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts]
 write(p/'part.json',d);write(p/'geometry-validation.json',check)
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65,450)
 write(p/'README.md',f'# {m.pid} v1.0\n\n{m.title}. Редактируемый исходник {m.pid}.blend; part.json содержит материалы, эмиссию и полные логические крепления. Все масштабы единичные. Геометрия проверена до сборки: geometry-validation.json. Отдельные виды Previews/top.png и perspective.png. Статическая деталь, процедурный PBR, без файловых текстур и UV-зависимости. GLB не создавался.\n')

write(FOLDER/'composition-plan.md','''# MA-I01 — грузовой отсек с верфью 2×1

Каталог cargo-2x1: добавляет вместимость инвентаря для предметов и содержит Shipyard для строительства по чертежам. Сетка 2×1 не определяет метрические габариты. Из каталога не следует открытый стапель, объём корабля или подвижный механизм, поэтому модель — защищённая грузовая кассета с ясным доступом. Никакой новой игровой механики.

План состава до моделирования:

| Назначение | Проверенная библиотека | Решение и совместимость |
|---|---|---|
| Двухместное шасси | MA-F01-P01 v1.0, 3.82×1.72 BU | Повторно использовать: подходящая сеточная пропорция, посадки ±0.88 X и единичный масштаб |
| Защищённые стреловидные борта | MA-F01-P03 v1.0 | Повторно использовать два экземпляра: штатные shoulder-front/back с поворотом 180° |
| Сервисный картридж | MA-R01-P05 v1.0 | Повторно использовать исправленный общий service-cartridge.v1. MA-P06 не использовать из-за дефекта фасок |
| Грузовой корпус | MA-F01-P02, MA-B01-P02 | Новая MA-I01-P01: прежние детали имеют цельные крыши, нужен отдельный читаемый грузовой люк; посадка совместима с существующим cassette socket |
| Утопленный грузовой люк | бронеплиты MA-A01…A04 | Новая MA-I01-P02: неподходящая форма и толщина плит потребовали бы запрещённого неравномерного масштаба; локальная посадка на грузовой корпус |
| Центральная сервисная спинка | MA-F01-P04 | Новая MA-I01-P03: нужна увеличенная высота для свободного доступа к грузовым люкам, без изменения общего моста |

Оси +Z вверх, -Y вперёд, правая система. Все детали самостоятельные, материалы PBR, логические sockets с полной ориентацией, единичный масштаб. Каждая новая деталь немедленно проходит проверку source manifoldness, evaluated triangles, finite, положительного объёма и материалов до сборки. Редактируемый Blender, отдельные top/perspective PNG; GLB не создаётся.
''')

if '--assembly-only' not in sys.argv:
 m=Part('MA-I01-P01','Грузовая герметичная кассета')
 m.panel('Pressure shell',(0,0,.30),(1.49,1.10,.60),'Titanium',.19,.012)
 m.panel('Upper recessed load gasket',(0,0,.606),(1.37,1.00,.035),'Dark',.16,.004)
 for x in [-.66,.66]:
  m.panel('Thick cargo cheek',(x,0,.40),(.15,1.02,.55),'Ceramic',.05,.008)
  m.box('Recessed side seam',(x+math.copysign(.078,x),0,.35),(.008,.69,.036),'Dark',.001)
 for y in [-.49,.49]:
  m.panel('End shoulder armour',(0,y,.29),(1.31,.13,.37),'Armor',.05,.006)
  m.box('Flush cargo lock strip',(0,y+math.copysign(.069,y),.32),(.53,.008,.07),'Dark',.001)
  for x in [-.20,.20]:m.box('Cargo access index',(x,y+math.copysign(.075,y),.32),(.07,.006,.014),'Signal',.001)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.production.cassette'),mount('hatch',(0,0,.625),'MilitaryArmor.cargo.hatch')])

 m=Part('MA-I01-P02','Утопленный бронированный грузовой люк')
 m.panel('Hatch pressure seal',(0,0,.015),(1.24,.91,.03),'Dark',.15,.003)
 m.panel('Faceted cargo hatch',(0,0,.060),(1.18,.85,.07),'Ceramic',.14,.006)
 m.panel('Recessed central access strip',(0,0,.099),(.18,.59,.009),'Titanium',.045,.001)
 m.box('Hatch separation seam',(0,0,.105),(.014,.48,.005),'Dark',.001)
 for x in [-.37,.37]:
  m.panel('Flush handless latch recess',(x,-.20,.099),(.21,.12,.009),'Dark',.03,.001)
  m.panel('Flush closed latch',(x,-.20,.106),(.14,.065,.008),'Titanium',.018,.001)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.cargo.hatch')])

 m=Part('MA-I01-P03','Центральная защищённая сервисная спинка')
 m.panel('Intercell structural beam',(0,0,.39),(.20,1.19,.78),'Armor',.05,.008)
 m.panel('Recessed dorsal service platform',(0,0,.845),(.79,.66,.13),'Titanium',.11,.008)
 m.panel('Dorsal socket gasket',(0,0,.912),(.75,.61,.008),'Dark',.09,.001)
 for y in [-.54,.54]:
  m.panel('Closed diagonal end cap',(0,y,.40),(.28,.16,.68),'Ceramic',.04,.005)
  m.box('Protected service diagnostic',(0,y+math.copysign(.084,y),.47),(.10,.008,.035),'Signal',.001)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.production.bridge'),mount('service',(0,0,.92),'MilitaryArmor.service-cartridge.v1')])

a=Assembly(BID,'cargo-2x1',[2,1],'Грузовой отсек с верфью 2×1')
a.instance('Chassis','MA-F01-P01')
for label,x in [('L',-.88),('R',.88)]:
 a.instance('Cargo.'+label,'MA-I01-P01',loc=(x,0,.33));a.instance('Hatch.'+label,'MA-I01-P02',loc=(x,0,.955))
a.instance('Shoulder.Front','MA-F01-P03',loc=(0,-.68,.24));a.instance('Shoulder.Back','MA-F01-P03',loc=(0,.68,.24),rot=(0,0,math.pi));a.instance('ServiceBridge','MA-I01-P03',loc=(0,0,.26));a.instance('ServiceCartridge','MA-R01-P05',loc=(0,0,1.18))
connections=[]
for s,c in [('cassette-L','Cargo.L'),('cassette-R','Cargo.R'),('shoulder-front','Shoulder.Front'),('shoulder-back','Shoulder.Back'),('bridge','ServiceBridge')]:connections.append({'parent_instance':'Chassis','parent_socket':s,'child_instance':c,'child_socket':'root'})
for label in ['L','R']:connections.append({'parent_instance':'Cargo.'+label,'parent_socket':'hatch','child_instance':'Hatch.'+label,'child_socket':'root'})
connections.append({'parent_instance':'ServiceBridge','parent_socket':'service','child_instance':'ServiceCartridge','child_socket':'bottom'})
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Static authoring source, catalog cargo inventory and Shipyard designation retained without invented shipbuilding scale or mechanism. No GLB or game integration.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.58),4.9,850)
write(FOLDER/'README.md','''# MA-I01 — грузовой отсек с верфью

MilitaryArmor 1.3; cargo-2x1, сетка 2×1. Две защищённые грузовые кассеты с отдельными утопленными люками, светлыми бронещёками и стреловидными бортами. Центральная сервисная спинка с диагностическим картриджем. Назначение Shipyard соответствует каталогу; размер и механика игровой верфи не выдумывались.

Исходник MA-I01.blend. Состав и логические соединения — assembly.json, план выбора деталей — composition-plan.md. Виды: Previews/top.png и Previews/perspective.png. Три новые детали MA-I01-P01…P03, повторно использованы MA-F01-P01, MA-F01-P03 и MA-R01-P05 v1.0. Всего девять экземпляров шести исходных деталей; каждый источник имеет собственные метаданные.

Процедурные PBR Armor/Ceramic/Titanium/Dark/Signal, без файловых текстур и UV-зависимости; эмиссия ограничена сервисной диагностикой. Статика, единичные масштабы. Крепления логические, полные позиции и ориентации. Заделки корпусов и уплотнения намеренно контактируют; люки закрыты, движение не задано. Все новые детали проверены до сборки, независимое повторное открытие исходников и сборки — validation.json.

BU условные, физический масштаб не согласован. Метаданные — авторинг Blender, не игровой контракт. GLB не генерировался. Игровая установка, коллайдеры, LOD и проверка в игре не выполнялись.
''')
print('MA_I01_BUILT',flush=True)
