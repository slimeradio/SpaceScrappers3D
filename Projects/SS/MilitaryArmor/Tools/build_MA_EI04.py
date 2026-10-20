import sys,json,bpy,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model,socket,finish,preview,inspect
BID='MA-EI04';folder=ROOT/'Blocks'/BID;tag='MilitaryArmor.ion'
apertures=[('ElectrodeLeftLow',-1.80,1.02),('ElectrodeRightLow',1.80,1.02),('ElectrodeLeftHigh',-1.80,2.82),('ElectrodeRightHigh',1.80,2.82)]
write(folder/'composition-plan.md','''# MA-EI04 — состав до моделирования

Каталог ion-thruster-4x6: визуальная заготовка без игрового XML. Сетка 4×6, не метры. +Z вверх, -Y выход, +Y тяга; BU условные. Без игровых параметров, постоянной струи и анимации.

Проверены MA-EI01-P01/P02, MA-EI02-P01 и MA-E01-P05: готовые корпуса короткие и узкие, unit-only; растяжение меняет конструкцию и не допускается. Новая MA-EI04-P01 v2.0 — широкий раскрытый четырёхлучевой силовой тракт с продольными изолированными шинами, двумя задними преобразователями и поперечными седлами. MA-EI01-P02 v2.0 использовать без изменения четыре раза: две апертуры в ширину и два яруса. MA-E01-P05 v1.0 использовать один раз с единичным масштабом; это второстепенный сервисный узел. Топливные глубокие колокола не подходят плоскому электродному фасаду. Других новых деталей не требуется.

Каждая деталь проходит немедленный gate до сборки; reused sources повторно открываются без перезаписи. Все экземпляры единичного масштаба с полными позами sockets. GLB не создавать.
''')
if '--assembly-only' not in sys.argv:
 m=Model('MA-EI04-P01','Four-lane exposed ion conversion tract with twin rear transformers')
 for x in [-3.48,-1.04,1.04,3.48]:
  outward=1 if x>0 else -1
  inner=abs(x)<2
  m.section('Long conversion beam',[(-4.35,x,.49,.34 if inner else .46,.62,.09),(-3.15,x,.62,.40 if inner else .57,.82,.11),(1.9,x,.54,.40 if inner else .54,.66,.10),(4.6,x*.81,.48,.53,.63,.11)],'Titanium' if inner else 'Armor')
  m.section('Insulated dorsal rail',[(-3.55,x,.99,.28,.10,.025),(-2.65,x,1.10,.31,.12,.025),(1.75,x,.94,.31,.11,.025),(3.5,x*.88,.87,.32,.11,.025)],'Ceramic')
  for y in [-2.65,-1.35,-.05,1.25]:
   m.panel('Discrete power-bus isolator',(x,y,.77),(.63,.18,.23),'Steel',.045)
 for side in [-1,1]:
  x=side*1.8
  m.section('Rear transformer body',[(2.5,x,.62,2.5,.99,.20),(3.6,x,.84,2.65,1.34,.23),(4.8,x,.58,2.32,.85,.19)],'Armor')
  m.panel('Transformer ceramic crest',(x,3.65,1.58),(1.85,.88,.14),'Ceramic',.13)
  for off in [-.55,0,.55]:
   m.panel('Recessed transformer cooling notch',(x+off,4.81,.60),(.19,.08,.38),'Dark',.025)
  m.section('Aperture outer support',[(-4.30,side*3.45,1.90,.25,3.58,.06),(-3.99,side*3.45,1.90,.36,3.58,.075),(-3.62,side*3.44,1.74,.32,3.18,.07)],'Titanium')
  m.panel('Pylon ceramic flank',(side*3.65,-4.0,2.03),(.12,.46,2.65),'Ceramic',.045)
 # Three transverse saddles connect each flat aperture, while all exit channels stay forward.
 for z in [.22,1.92,3.62]:
  m.panel('Continuous cross-aperture saddle',(0,-4.13,z),(7.10,.30,.15),'Titanium',.04)
 m.panel('Central vertical field separator',(0,-4.13,1.92),(.18,.29,3.55),'Titanium',.035)
 for y in [-2.8,-.2,2.35]:
  m.panel('Low transverse power tie',(0,y,.22),(6.95,.22,.20),'Titanium',.045)
 m.panel('Service coupling bridge',(0,3.66,.91),(1.0,.64,.19),'Titanium',.08)
 mounts=[socket('hull',(0,0,0),tag+'.hull'),socket('service',(0,3.66,1.005),'MilitaryArmor.engine.accessory')]
 for iid,x,z in apertures:mounts.append(socket(iid,(x,-4.30,z),tag+'.aperture'))
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
 finish(m,mounts)
for pid in ['MA-EI04-P01','MA-EI01-P02','MA-E01-P05']:
 p=ROOT/'Parts'/pid;bpy.ops.wm.open_mainfile(filepath=str(p/(pid+'.blend')));check=inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
 if pid=='MA-EI04-P01':check['source_reopened_before_assembly']=True;check['source_normals_consistent']=True;write(p/'geometry-validation.json',check)
a=Assembly(BID,'ion-thruster-4x6',[4,6],'Ионный двигатель 4×6')
a.instance('OpenPowerTract','MA-EI04-P01')
cons=[]
for iid,x,z in apertures:
 a.instance(iid,'MA-EI01-P02',loc=(x,-4.30,z));cons.append({'parent_instance':'OpenPowerTract','parent_socket':iid,'child_instance':iid,'child_socket':'root'})
a.instance('ServiceCartridge','MA-E01-P05',loc=(0,3.66,1.005));cons.append({'parent_instance':'OpenPowerTract','parent_socket':'service','child_instance':'ServiceCartridge','child_socket':'root'})
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':cons,'animations':[],'exports':[],'notes':'Four shallow electrode apertures, open four-lane conversion tract; +Y thrust/-Y exhaust authoring only. Physical BU unspecified. No gameplay tuning or permanent plume.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();inspect();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,(0,.10,1.60),13.0,800,True)
write(folder/'README.md','''# MA-EI04 — ионный двигатель 4×6

Четыре плоские электродные апертуры (144 открытых канала) образуют широкий двухъярусный фасад. От него отходят четыре раскрытые изолированные силовые шины к двум задним преобразователям; между шинами видны глубокие открытые промежутки. Конструкция узнаётся без цвета: тонкая сетчатая стенка и открытые продольные тракты, без топливных колоколов и постоянной струи.

MA-EI04.blend — редактируемый источник; assembly.json — стабильные экземпляры, версии и позы; composition-plan.md — решение до моделирования. Новая MA-EI04-P01 v2.0; повторно использованы MA-EI01-P02 v2.0 (четыре раза) и MA-E01-P05 v1.0. Шесть экземпляров из трёх источников, масштаб единичный. Общие исходники не менялись.

Previews/top.png, perspective.png, top-grayscale.png. Новая деталь отдельно сохранена, проверена до сборки, имеет материалы, sockets и собственные previews. Статика, процедурные PBR, файловых текстур и UV-зависимости нет. Эмиссия ограничена диагностикой готовых деталей.

Каталог ion-thruster-4x6: visual-only без игрового XML, параметров тяги/расхода/ресурсов. BU условные; +Z вверх, -Y выход, +Y тяга — авторинг. GLB, игровые коллайдеры/LOD и интеграция не выполнялись. validation.json — независимое повторное открытие всех sources и сборки, exhaust-clearance.json — свободные выходные лучи. Контакты рам с седлами и шин с изоляторами намеренны.
''')
print('BUILT MA-EI04',flush=True)