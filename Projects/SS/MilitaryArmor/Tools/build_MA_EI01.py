"""Ion 2x3: flat electrode aperture, source-only authoring."""
import sys,math,json,bpy,bmesh
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model,socket,finish,preview,inspect
BID='MA-EI01'; folder=ROOT/'Blocks'/BID;tag='MilitaryArmor.ion'
write(folder/'composition-plan.md','''# MA-EI01 — ионный двигатель 2×3

Каталог ion-thruster-2x3: визуальная заготовка без игрового XML. Сетка 2×3, BU условные, не метры. +Z вверх, -Y выход, +Y тяга; это ориентиры авторинга, не контракт двигателя игры. Без заданных тяги, энергопотребления, ресурсов, анимации и постоянной струи.

До моделирования просмотрены MA-E01/E02, их камеры, сопла, термопанель и MA-E01-P05 v1.0. Полые колокола предназначены для другого конструктивного образа и здесь не подходят. Термопанель MA-E01-P04 узкая и короткая, unit-only; масштабирование не подходит. Сервисный картридж MA-E01-P05 подходит как малый вспомогательный узел с тем же посадочным интерфейсом MilitaryArmor.engine.accessory. Использовать без изменения и масштабирования.

Новые детали: MA-EI01-P01 v2.0 — раздвоенный силовой корпус с открытым центральным каналом и задним поперечным преобразовательным узлом. MA-EI01-P02 v2.0 — широкая плоская электродная апертура, короткая несущая рама, неглубокие шестигранные проходы и внутренние электроды. Два семейных узла объединены полными позами sockets. Решётка не является перекрашенным соплом: нет глубокой расширяющейся камеры. Открытые электроды и плечевой профиль определяют индивидуальность без цвета.

Каждая новая деталь отдельно сохраняется и проверяется немедленно до сборки; источники повторно открываются. GLB не создавать, прежние sources не пересобирать.
''')
def gate(m,mounts):
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges),o.name;bm.free()
 finish(m,mounts)
if '--assembly-only' not in sys.argv:
 m=Model('MA-EI01-P01','Split ion power housing with open dorsal channel')
 # Slim forked rails, a broad blade at the aperture, and a taller rear bridge.
 for s in [-1,1]:
  m.section('Swept insulated power rail',[(-1.55,s*1.15,.48,.62,.66,.16),(-.83,s*1.20,.55,.69,.83,.18),(.75,s*1.16,.48,.61,.68,.15),(2.20,s*.89,.39,.48,.48,.12)],'Armor')
  m.section('Long light ceramic shoulder',[(-1.20,s*1.19,.92,.55,.15,.045),(-.60,s*1.23,1.04,.54,.16,.045),(.63,s*1.19,.90,.46,.16,.04),(1.78,s*.97,.66,.36,.12,.035)],'Ceramic')
  m.section('Recessed inner power bus',[(-1.20,s*.80,.54,.10,.24,.025),(.75,s*.80,.48,.12,.24,.025),(1.91,s*.70,.41,.12,.24,.025)],'Steel')
  for y in [-.65,.10,.85]:m.panel('Inset power rail isolator',(s*1.17,y,.99 if y<.3 else .83),(.26,.20,.06),'Titanium',.035)
 m.panel('Low front cross saddle',(0,-1.42,.22),(3.0,.40,.36),'Titanium',.10)
 m.section('Rear conversion bridge',[(1.37,0,.53,2.05,.80,.18),(1.85,0,.62,1.98,.94,.21),(2.22,0,.47,1.65,.63,.16)],'Armor')
 m.panel('Conversion dorsal cover',(0,1.78,1.10),(1.45,.62,.12),'Ceramic',.15)
 m.panel('Rear interface recess',(0,2.24,.43),(1.25,.07,.27),'Dark',.055)
 for x in [-.36,0,.36]:m.cyl('Protected electrical coupling',(x,2.29,.43),.095,.10,'Titanium',axis='Y',verts=16)
 for y in [-.75,.05,.82]:m.panel('Recessed transverse field link',(0,y,.23),(1.45,.12,.16),'Titanium',.035)
 mounts=[socket('hull',(0,0,0),tag+'.hull'),socket('aperture',(0,-1.62,1.00),tag+'.aperture'),socket('service',(0,1.78,1.16),'MilitaryArmor.engine.accessory')]
 gate(m,mounts)
 m=Model('MA-EI01-P02','Shallow broad electric electrode grid with open hexagonal channels')
 # The rim is four overlapping closed solids, no recessed bell or nozzle throat.
 for x in [-1.58,1.58]:
  m.section('Swept side electrode cheek',[(-.45,x,0,.24,1.54,.07),(-.09,x,0,.30,1.64,.08),(.20,x,0,.23,1.42,.06)],'Ceramic')
 for z in [-.73,.73]:m.box('Straight aperture frame',(0,-.14,z),(3.10,.30,.18),'Titanium')
 # Flat array with shallow concavity: individual annular channels remain open along -Y.
 for row in range(4):
  z=(row-1.5)*.31
  for col in range(9):
   x=(col-4)*.315+(row%2)*.06-.03
   y=-.22+.032*(x*x)
   m.ring('Hexagonal electrode channel',(x,y,z),.173,.135,.15,axis='Y',mat='Steel',verts=6)
   m.ring('Recessed ceramic cell isolator',(x,y+.12,z),.169,.133,.045,axis='Y',mat='Titanium',verts=6)
 # Very small diagnostics, outside exhaust openings.
 for s in [-1,1]:m.box('Field diagnostic index',(s*1.59,-.475,.25),(.065,.015,.09),'Optic')
 pts=[{'id':'thrust','role':'thrust','parent':'part','node':'point.thrust','position':[0,0,0],'direction':[0,1,0],'up':[0,0,1]}, {'id':'exhaust','role':'exhaust','parent':'part','node':'point.exhaust','position':[0,-.55,0],'direction':[0,-1,0],'up':[0,0,1]}]
 # finish immediately gates the new standalone source before the dependent assembly.
 gate(m,[socket('root',(0,0,0),tag+'.aperture')])
 p=ROOT/'Parts'/m.pid;pm=json.loads((p/'part.json').read_text());pm['functional_points']=pts;pm['notes']='Static flat electrode grid; open -Y channels. No plume, animation or gameplay parameters. Shallow cells are not a bell nozzle.';write(p/'part.json',pm)
 bpy.ops.wm.open_mainfile(filepath=str(p/(m.pid+'.blend')))
 coll=bpy.data.collections[m.pid]
 for pt in pts:
  o=bpy.data.objects.new(pt['node'],None);coll.objects.link(o);o.location=pt['position'];o['direction']=pt['direction'];o['role']=pt['role'];o['up']=pt['up']
 bpy.ops.wm.save_as_mainfile(filepath=str(p/(m.pid+'.blend')))
# Fresh reopen gate, including unmodified reused library source.
for pid in ['MA-EI01-P01','MA-EI01-P02','MA-E01-P05']:
 p=ROOT/'Parts'/pid;bpy.ops.wm.open_mainfile(filepath=str(p/(pid+'.blend')));check=inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
 if pid.startswith('MA-EI01-'):check['source_reopened_before_assembly']=True;check['source_normals_consistent']=True;write(p/'geometry-validation.json',check)
a=Assembly(BID,'ion-thruster-2x3',[2,3],'Ионный двигатель 2×3')
a.instance('SplitPowerHousing','MA-EI01-P01');a.instance('ElectrodeAperture','MA-EI01-P02',loc=(0,-1.62,1));a.instance('ServiceCartridge','MA-E01-P05',loc=(0,1.78,1.16))
cons=[{'parent_instance':'SplitPowerHousing','parent_socket':'aperture','child_instance':'ElectrodeAperture','child_socket':'root'},{'parent_instance':'SplitPowerHousing','parent_socket':'service','child_instance':'ServiceCartridge','child_socket':'root'}]
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':cons,'animations':[],'exports':[],'notes':'Flat open electrode aperture, split power rails; +Y thrust/-Y exhaust authoring only. Physical BU unspecified; no gameplay tuning or permanent plume.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();inspect();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,(0,.05,.73),6.1,800,True)
write(folder/'README.md','''# MA-EI01 — ионный двигатель 2×3

Широкая плоская электродная апертура с 36 открытыми шестигранными каналами, короткая светлая рама и раздвоенный силовой корпус с глубоким открытым продольным каналом. Задний преобразовательный мост связывает плечи; сервисный картридж остаётся небольшим второстепенным элементом. Неглубокая решётка отличается конструкцией от глубокого колокола топливных двигателей, в том числе без цвета. Постоянной струи нет.

Исходник MA-EI01.blend, точные экземпляры/версии/позы assembly.json, план до моделирования composition-plan.md. Новые MA-EI01-P01/P02 v2.0; повторно использован без изменения MA-E01-P05 v1.0. Три единичных экземпляра из трёх исходников. Каждая новая деталь имеет самостоятельный Blender-исходник, part.json, procedural PBR, top/perspective и немедленный геометрический gate до сборки.

Предпросмотры: Previews/top.png, perspective.png и top-grayscale.png. Серый материал временный, исходные материалы сохранены. Небольшая эмиссия Optic на диагностических индексах апертуры и Signal готового сервисного картриджа; эмиттер струи отсутствует. Анимации, файловые текстуры и UV-зависимость отсутствуют.

Каталог ion-thruster-2x3 visual-only без игрового XML. BU условные; +Z вверх, -Y выход, +Y тяга — ориентиры авторинга. Сила/расход/ресурсы/метрический размер не заданы. GLB не создавался; игровая интеграция, коллайдеры/LOD не выполнялись. Независимая повторная проверка sources/assembly записана в validation.json. Прилегания несущих рам, стенок каналов и задних шин намеренны.
''')
print('BUILT MA-EI01',flush=True)
