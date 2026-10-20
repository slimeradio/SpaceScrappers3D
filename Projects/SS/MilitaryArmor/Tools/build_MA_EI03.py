import sys,json,math,bpy,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model,socket,finish,preview,inspect
BID='MA-EI03';folder=ROOT/'Blocks'/BID;tag='MilitaryArmor.ion'
write(folder/'composition-plan.md','''# MA-EI03 — ионный двигатель 1×2

Каталог ion-thruster-1x2: visual-only без игрового XML. Сетка 1×2 не метры. Авторинг +Z вверх, -Y выход, +Y тяга. Без тяги/расхода/ресурсов/анимации/постоянной струи.

До моделирования проверены MA-EI01-P01/P02 v2.0, MA-EI02-P01 v2.0, MA-E01-P05 v1.0. Готовые широкие апертуры и двухъярусный корпус не подходят компактному 1×2; уменьшение масштаба сожмёт каналы, а масштаб источников unit-only. Создать явный компактный вариант MA-EI03-P02 v2.0: 4×4 неглубоких каналов того же диаметра и шага, укороченная рама. Новый MA-EI03-P01 v2.0 — короткие защищённые боковые шины, открытая спина и задний преобразователь. Сервисный картридж MA-E01-P05 v1.0 помещается на задней крышке, повторно использовать без масштаба и изменения источника. Топливные колокола не подходят плоской электродной архитектуре.

Новые детали отдельно сохраняются и немедленно проверяются до сборки. GLB не создавать. Старые детали не пересобирать.
''')

def gate(m,mounts):
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges),o.name;bm.free()
 finish(m,mounts)

if '--assembly-only' not in sys.argv:
 m=Model('MA-EI03-P01','Compact protected ion power fork')
 for s in [-1,1]:
  m.section('Compact swept power cheek',[(-1.02,s*.76,.43,.32,.57,.08),(-.40,s*.78,.48,.37,.69,.09),(.63,s*.73,.42,.32,.55,.08),(1.45,s*.57,.33,.28,.39,.07)],'Armor')
  m.section('Short ceramic shoulder',[(-.78,s*.78,.77,.28,.12,.03),(-.27,s*.79,.88,.29,.13,.035),(.60,s*.74,.75,.25,.11,.025),(1.19,s*.61,.56,.21,.10,.02)],'Ceramic')
  m.box('Protected inner bus',(s*.56,.15,.40),(.10,1.65,.17),'Steel')
  for y in [-.25,.37]:m.panel('Field isolator',(s*.78,y,.86 if y<0 else .79),(.17,.14,.04),'Titanium',.025)
 m.panel('Front electrode seat',(0,-1.04,.20),(1.85,.29,.29),'Titanium',.06)
 m.section('Rear compact conversion bridge',[(.86,0,.40,1.40,.60,.12),(1.23,0,.46,1.44,.72,.13),(1.57,0,.33,1.14,.46,.09)],'Armor')
 m.panel('Conversion cover',(0,1.19,.84),(.89,.45,.10),'Ceramic',.075)
 m.panel('Rear connector recess',(0,1.59,.34),(.88,.065,.20),'Dark',.035)
 for x in [-.24,0,.24]:m.cyl('Inset electrical connector',(x,1.63,.34),.065,.075,'Titanium',axis='Y',verts=16)
 for y in [-.4,.2,.7]:m.box('Exposed transverse field link',(0,y,.19),(.98,.09,.11),'Titanium')
 gate(m,[socket('hull',(0,0,0),tag+'.hull'),socket('aperture',(0,-1.12,.91),tag+'.aperture.compact'),socket('service',(0,1.19,.89),'MilitaryArmor.engine.accessory')])
 m=Model('MA-EI03-P02','Compact 4x4 shallow electrode aperture; unchanged cell pitch')
 for x in [-.86,.86]:m.section('Compact ceramic aperture cheek',[(-.45,x,0,.17,1.49,.04),(-.10,x,0,.21,1.59,.05),(.16,x,0,.17,1.39,.04)],'Ceramic')
 for z in [-.73,.73]:m.box('Compact aperture crossbar',(0,-.13,z),(1.66,.27,.17),'Titanium')
 for row in range(4):
  z=(row-1.5)*.31
  for col in range(4):
   x=(col-1.5)*.315+(row%2)*.06-.03;y=-.22+.032*x*x
   m.ring('Hexagonal electrode channel',(x,y,z),.173,.135,.15,axis='Y',mat='Steel',verts=6)
   m.ring('Recessed ceramic cell isolator',(x,y+.12,z),.169,.133,.045,axis='Y',mat='Titanium',verts=6)
 for s in [-1,1]:m.box('Field diagnostic index',(s*.86,-.475,.25),(.05,.015,.08),'Optic')
 gate(m,[socket('root',(0,0,0),tag+'.aperture.compact')])
 p=ROOT/'Parts'/m.pid;pm=json.loads((p/'part.json').read_text());pts=[{'id':'thrust','role':'thrust','parent':'part','node':'point.thrust','position':[0,0,0],'direction':[0,1,0],'up':[0,0,1]},{'id':'exhaust','role':'exhaust','parent':'part','node':'point.exhaust','position':[0,-.55,0],'direction':[0,-1,0],'up':[0,0,1]}];pm['functional_points']=pts;pm['notes']='Explicit compact variant: 4x4 unchanged size channels. Static flat aperture; no bell, no plume or gameplay parameters.';write(p/'part.json',pm)
 bpy.ops.wm.open_mainfile(filepath=str(p/(m.pid+'.blend')))
 for pt in pts:
  o=bpy.data.objects.new(pt['node'],None);bpy.data.collections[m.pid].objects.link(o);o.location=pt['position'];o['direction']=pt['direction'];o['up']=pt['up'];o['role']=pt['role']
 bpy.ops.wm.save_as_mainfile(filepath=str(p/(m.pid+'.blend')))
for pid in ['MA-EI03-P01','MA-EI03-P02','MA-E01-P05']:
 p=ROOT/'Parts'/pid;bpy.ops.wm.open_mainfile(filepath=str(p/(pid+'.blend')));check=inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
 if pid.startswith('MA-EI03-'):check['source_reopened_before_assembly']=True;check['source_normals_consistent']=True;write(p/'geometry-validation.json',check)
a=Assembly(BID,'ion-thruster-1x2',[1,2],'Ионный двигатель 1×2')
a.instance('CompactPowerHousing','MA-EI03-P01');a.instance('ElectrodeAperture','MA-EI03-P02',loc=(0,-1.12,.91));a.instance('ServiceCartridge','MA-E01-P05',loc=(0,1.19,.89))
cons=[{'parent_instance':'CompactPowerHousing','parent_socket':'aperture','child_instance':'ElectrodeAperture','child_socket':'root'},{'parent_instance':'CompactPowerHousing','parent_socket':'service','child_instance':'ServiceCartridge','child_socket':'root'}]
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':cons,'animations':[],'exports':[],'notes':'Compact 4x4 flat electrode aperture; unchanged cell pitch, unit scales. +Y thrust/-Y exhaust authoring only. Physical BU unspecified.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();inspect();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,(0,.14,.72),4.6,800,True)
write(folder/'README.md','''# MA-EI03 — ионный двигатель 1×2

Компактная плоская апертура из 16 открытых шестигранных каналов с прежним диаметром и шагом. Укороченный раскрытый силовой корпус, светлые боковые щёки, низкие поперечные шины и задний преобразователь. Это малый вариант ионного семейства; глубокого топливного колокола и постоянной струи нет. Функциональная форма читается без цвета.

MA-EI03.blend — редактируемый исходник. assembly.json содержит стабильные экземпляры, версии, пути, единичные позы и полные связи sockets. composition-plan.md фиксирует решение до моделирования. Новые MA-EI03-P01/P02 v2.0; повторно использован MA-E01-P05 v1.0. Три экземпляра из трёх источников без изменения общих деталей.

Previews/top.png, perspective.png, top-grayscale.png. Каждая новая деталь имеет standalone blend, part.json, README, top/perspective и geometry-validation.json до сборки. Процедурные материалы, ограниченная диагностическая эмиссия; файловых текстур, UV-зависимости и анимаций нет. Функциональные точки и направления — только авторинг.

Каталог ion-thruster-1x2 — visual-only без игрового XML; BU условные, не метры. +Z вверх, -Y выход, +Y тяга. Сила, расход и ресурсы не назначены. GLB не создавались. Независимая проверка сохранённых sources и сборки в validation.json; выходные лучи в exhaust-clearance.json. Посадки корпуса/рамы и соединения стенок ячеек намеренны. Игровая интеграция, LOD и коллайдеры не выполнялись.
''')
print('BUILT MA-EI03',flush=True)
