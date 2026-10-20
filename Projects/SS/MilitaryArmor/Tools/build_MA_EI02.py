import sys,json,bpy,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model,socket,finish,preview,inspect
BID='MA-EI02';folder=ROOT/'Blocks'/BID;tag='MilitaryArmor.ion'
write(folder/'composition-plan.md','''# MA-EI02 — ионный двигатель 3×4

Каталог ion-thruster-3x4: visual-only без XML. Сетка 3×4 не метры; +Z вверх, -Y выход, +Y тяга. Без тяги/расхода/ресурсов/анимаций/струи.

До моделирования рассмотрены MA-EI01-P01/P02 v2.0, MA-E01-P05 v1.0 и топливные сопла MA-E01. Две готовые плоские апертуры MA-EI01-P02 использовать без масштаба и изменения источников, в двух ярусах. Малый сервисный картридж MA-E01-P05 повторно использовать с единичным масштабом. MA-EI01-P01 рассчитан на один ярус и короткий корпус; растяжение не подходит. Создать MA-EI02-P01 v2.0: раскрытый трёхлучевой силовой корпус, боковые подъёмные стойки и три поперечных седла. Топливные колокола не соответствуют ионной конструкции.

Каждый новый источник gate до сборки. Повторно используемые источники открыть и проверить без изменений. GLB не создавать.
''')
if '--assembly-only' not in sys.argv:
 m=Model('MA-EI02-P01','Twin-deck ion conversion fork and elevated field saddle')
 for side in [-1,1]:
  x=side*1.85
  m.section('Outboard swept conversion boom',[(-2.1,x,.55,.52,.8,.13),(-1.35,x,.68,.68,1.03,.16),(.7,x,.54,.70,.85,.17),(2.8,side*1.32,.39,.54,.57,.12)],'Armor')
  m.section('Pale outer insulation',[(-1.55,x,1.12,.48,.16,.045),(-.9,x,1.24,.55,.15,.04),(.6,x,1.03,.54,.14,.04),(2.5,side*1.40,.73,.35,.10,.025)],'Ceramic')
  m.section('Aperture lifting pylon',[(-2.13,side*1.75,1.64,.24,2.67,.06),(-1.91,side*1.75,1.64,.37,2.67,.08),(-1.57,side*1.78,1.51,.34,2.42,.07)],'Titanium')
  m.panel('Pylon outer ceramic shield',(side*1.92,-1.86,1.75),(.16,.41,2.47),'Ceramic',.06)
  for y in [-1.0,.1,1.2]:m.panel('Outboard bus isolator',(side*1.85,y,1.15 if y<.5 else .97),(.28,.19,.06),'Titanium',.035)
 m.section('Central power spine',[(-1.5,0,.29,.48,.43,.10),(.5,0,.31,.60,.46,.1),(2.8,0,.36,.77,.53,.12)],'Titanium')
 for z in [.22,1.81,3.45]:m.panel('Cross electrode saddle',(0,-1.93,z),(3.70,.30,.16),'Titanium',.045)
 m.section('Rear conversion wedge',[(1.75,0,.5,2.55,.81,.14),(2.5,0,.65,2.75,1.09,.17),(3.1,0,.40,2.38,.60,.14)],'Armor')
 m.panel('Rear conversion cover',(0,2.51,1.23),(1.65,.72,.12),'Ceramic',.13)
 for side in [-1,1]:
  m.panel('Protected output connector',(side*.86,3.11,.43),(.43,.12,.31),'Dark',.04)
  m.cyl('Inset rear coupling',(side*.86,3.19,.43),.10,.08,'Titanium',axis='Y',verts=16)
 mounts=[socket('hull',(0,0,0),tag+'.hull'),socket('aperture-low',(0,-2.10,1.0),tag+'.aperture'),socket('aperture-high',(0,-2.10,2.63),tag+'.aperture'),socket('service',(0,2.51,1.29),'MilitaryArmor.engine.accessory')]
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
 finish(m,mounts)
for pid in ['MA-EI02-P01','MA-EI01-P02','MA-E01-P05']:
 p=ROOT/'Parts'/pid;bpy.ops.wm.open_mainfile(filepath=str(p/(pid+'.blend')));check=inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
 if pid=='MA-EI02-P01':check['source_reopened_before_assembly']=True;check['source_normals_consistent']=True;write(p/'geometry-validation.json',check)
a=Assembly(BID,'ion-thruster-3x4',[3,4],'Ионный двигатель 3×4')
a.instance('SplitPowerHousing','MA-EI02-P01');a.instance('ElectrodeApertureLow','MA-EI01-P02',loc=(0,-2.10,1));a.instance('ElectrodeApertureHigh','MA-EI01-P02',loc=(0,-2.10,2.63));a.instance('ServiceCartridge','MA-E01-P05',loc=(0,2.51,1.29))
cons=[{'parent_instance':'SplitPowerHousing','parent_socket':'aperture-low','child_instance':'ElectrodeApertureLow','child_socket':'root'},{'parent_instance':'SplitPowerHousing','parent_socket':'aperture-high','child_instance':'ElectrodeApertureHigh','child_socket':'root'},{'parent_instance':'SplitPowerHousing','parent_socket':'service','child_instance':'ServiceCartridge','child_socket':'root'}]
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':cons,'animations':[],'exports':[],'notes':'Twin deck flat electrode aperture. Open fork; +Y thrust/-Y exhaust authoring only. Physical BU unspecified; no gameplay tuning or permanent plume.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();inspect();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,(0,.35,1.7),8.6,800,True)
write(folder/'README.md','''# MA-EI02 — ионный двигатель 3×4

Двухъярусная плоская электродная апертура: 72 открытых шестигранных канала на высоких боковых стойках. Новый открытый трёхлучевой корпус, низкая центральная шина и широкие стреловидные плечи. Неглубокие решётки отличают ионный двигатель от топливных колоколов без опоры на цвет. Постоянной струи нет.

MA-EI02.blend — редактируемый источник. assembly.json — экземпляры, версии и полные позы. composition-plan.md — решение до моделирования. Новая деталь MA-EI02-P01 v2.0; повторно использованы MA-EI01-P02 v2.0 (два яруса) и MA-E01-P05 v1.0. Четыре экземпляра из трёх источников, без масштаба и изменения общих деталей.

Previews/top.png, perspective.png, top-grayscale.png. Новая деталь имеет самостоятельный blend/part.json/README/top/perspective и немедленный geometry-validation.json до сборки. Процедурные материалы; файловых текстур, UV-зависимости и анимаций нет. Сдержанная эмиссия диагностических индексов; струя не моделируется.

Каталог ion-thruster-3x4 visual-only без игрового XML. BU условные; +Z вверх, -Y выход, +Y тяга — авторинг. Тяга/расход/ресурсы/метрический масштаб не заданы. GLB не создавались; игровая интеграция/LOD/коллайдеры не выполнялись. validation.json — независимое повторное открытие sources и сборки; exhaust-clearance.json — выходные лучи обоих ярусов. Контакты рам и силовых седел намеренны.
''')
print('BUILT MA-EI02',flush=True)
