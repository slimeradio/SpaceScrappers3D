"""MA-HS03 stepped triple thermal bank; standalone source-only build."""
import sys,json,bpy,bmesh,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model,socket,finish,preview,inspect
BID='MA-HS03';folder=ROOT/'Blocks'/BID
tag='MilitaryArmor.r2.thermal'; ys=[(j-3.5)*.57 for j in range(8)]
banks=[(-1.82,.21),(0,.53),(1.82,.21)]
write(folder/'composition-plan.md','''# MA-HS03 — накопитель тепла 3×3

Каталог heat-store-3x3: визуальная заготовка без игрового XML, сетка 3×3. BU условные, не метры; правая система +Z вверх, -Y вперёд. Теплоёмкость, температура и функциональный контур не определяются.

Решение до моделирования: просмотрены текущие MA-HS01 v2 и MA-HS02, их детали и метаданные. Семейный признак — толстые гранёные кольца изоляции с глубокими промежутками, отдельное ложе и защищённый коллектор. Не применять прежние прямоугольные кассеты v1.

Повторно использовать MA-HS01-R2-P02 v2.0: 24 единичных экземпляра, три банки по восемь колец. Центральная банка поднята, образуя ступенчатый поперечный профиль и глубокие продольные проходы. Подходящие материал, геометрия, mounts section; исходник не изменять. Это увеличение числа секций и банков, а не растяжение исходника.

Создать MA-HS03-P01 v2.0 — трёхканальное ступенчатое изолированное ложе с тремя цельными сердечниками. Существующее MA-HS02-P01 имеет два канала, недостаточную длину и unit-only; масштабирование непригодно. Создать MA-HS03-P02 v2.0 — трёхуровневый защищённый задний коллектор с независимыми подводами; MA-HS02-P02 рассчитан на два канала и не подходит позиции поднятой банки. Универсальные сервисные картриджи/поддон не нужны.

Новые детали сохранять и проверять немедленно до сборки; standalone previews и материалы обязательны. Статика без эмиссии и анимации. GLB не создавать, старые исходники не пересобирать.
''')
if '--assembly-only' not in sys.argv:
 # Source-only helper finish calls source/evaluated geometry gate before save/preview.
 m=Model('MA-HS03-P01','Stepped triple-bank insulated bed with three continuous protected cores')
 for bank,(x,zbase) in enumerate(banks):
  zoff=zbase-.21
  m.panel('Independent insulated bed',(x,0,.22+zoff),(1.38,4.65,.32),'Titanium',.18)
  m.cyl('Protected continuous thermal core',(x,0,.83+zoff),.49,4.48,'Dark',axis='Y',verts=24)
  for dx in [-.63,.63]:
   m.section('Faceted isolated runner',[(-2.37,x+dx,.19+zoff,.22,.26,.05),(-2.12,x+dx,.18+zoff,.28,.30,.06),(2.12,x+dx,.18+zoff,.28,.30,.06),(2.37,x+dx,.19+zoff,.22,.26,.05)],'Armor')
  for y in [-2.25,2.25]:
   m.cyl('Inset protected core endcap',(x,y,.83+zoff),.44,.10,'Titanium',axis='Y',verts=24)
   m.ring('End insulation lip',(x,y,.83+zoff),.51,.41,.12,axis='Y',mat='Ceramic',verts=24)
 # Narrow raised supports under the central bank make the step structurally legible.
 for y in [-1.65,0,1.65]:
  m.panel('Raised central insulated support',(0,y,.26),(.94,.36,.42),'Armor',.07)
 # Two submerged cross-ties connect the separate runners without a universal pallet.
 for y in [-1.45,1.45]:m.panel('Recessed transverse tie',(0,y,.13),(4.85,.22,.20),'Titanium',.06)
 mounts=[socket('hull',(0,0,0),tag+'.hull'),socket('collector',(0,0,0),tag+'.triple-collector')]
 for b,(x,z) in enumerate(banks):
  for j,y in enumerate(ys):mounts.append(socket(f'bank-{b}-section-{j}',(x,y,z),tag+'.section'))
 finish(m,mounts)
 m=Model('MA-HS03-P02','Stepped protected return collector for three insulated banks')
 m.panel('Rear protected return bridge',(0,2.47,.47),(5.12,.27,.32),'Titanium',.08)
 for b,(x,z) in enumerate(banks):
  off=z-.21
  m.panel('Rear isolated collector shoe',(x,2.39,.57+off),(.56,.45,.38),'Armor',.09)
  m.cyl('Short protected bank return',(x,2.29,.83+off),.14,.30,'Steel',axis='Y',verts=16)
  m.panel('Broad ceramic return shield',(x,2.49,.80+off),(.66,.33,.13),'Ceramic',.07)
  if b==1:m.panel('Raised bank collector step',(x,2.47,.72),(.32,.23,.65),'Titanium',.05)
 # Offset cover strips leave a deliberate shallow central service groove.
 for x in [-1.08,1.08]:m.panel('Recessed return shielding',(x,2.48,.65),(1.02,.34,.12),'Armor',.05)
 finish(m,[socket('root',(0,0,0),tag+'.triple-collector')])
# Reopen every source and complete normal-consistency gate before dependent assembly.
for pid in ['MA-HS03-P01','MA-HS03-P02','MA-HS01-R2-P02']:
 p=ROOT/'Parts'/pid
 bpy.ops.wm.open_mainfile(filepath=str(p/(pid+'.blend')))
 check=inspect()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  assert all(e.is_contiguous for e in bm.edges),o.name
  bm.free()
 check['source_normals_consistent']=True
 check['standalone_source_reopened_before_assembly']=True
 if pid.startswith('MA-HS03-'):write(p/'geometry-validation.json',check)
a=Assembly(BID,'heat-store-3x3',[3,3],'Накопитель тепла 3×3 — визуальная заготовка')
a.instance('TripleThermalBed','MA-HS03-P01');con=[]
for b,(x,z) in enumerate(banks):
 for j,y in enumerate(ys):
  iid=f'ThermalRing-B{b}-{j}';a.instance(iid,'MA-HS01-R2-P02',loc=(x,y,z));con.append({'parent_instance':'TripleThermalBed','parent_socket':f'bank-{b}-section-{j}','child_instance':iid,'child_socket':'root'})
a.instance('TripleCollector','MA-HS03-P02');con.append({'parent_instance':'TripleThermalBed','parent_socket':'collector','child_instance':'TripleCollector','child_socket':'root'})
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'notes':'Three stepped thermal banks, 24 unchanged v2 insulation rings. New bed and protected rear collector. No gameplay parameters, emission or physical metric scale.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();inspect();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,(0,.12,1.0),8.25,800,True)
write(folder/'README.md','''# MA-HS03 — накопитель тепла 3×3

Три продольные банки по восемь массивных гранёных колец изоляции. Средняя банка поднята: ступенчатый поперечный профиль и глубокие проходы видны сверху и в объёме. Отдельный задний защищённый коллектор объединяет компоновку. Это семейное развитие MA-HS01 v2 / MA-HS02; исходное кольцо не растянуто. Толстая изоляция и глубокие канавки отличают накопитель от тонких обручей топливных баков.

Исходник [MA-HS03.blend](MA-HS03.blend), точные версии и экземпляры assembly.json, предварительный план composition-plan.md. Новые MA-HS03-P01/P02 v2.0; готовое MA-HS01-R2-P02 v2.0 используется 24 раза. Итого 26 экземпляров из трёх исходных деталей.

Самостоятельные детали имеют Blender-исходники, процедурные PBR-материалы, полный metadata-контракт креплений, top/perspective previews и немедленную проверку до сборки. validation.json создаётся отдельным процессом с повторным открытием всех деталей и сборки. Проверяются manifold, нормали, положительный объём, отсутствие вырожденных source/evaluated граней, конечные координаты, материалы, версии и полные позы совместимых sockets. Все экземпляры единичного масштаба.

Предпросмотры Previews/top.png, perspective.png, top-grayscale.png. Серый материал применяется временно только при рендере. Исходные материалы сохранены.

Каталог visual-only без игрового XML. BU условные; не заданы теплоёмкость, температуры или функциональный контур. Без эмиссии, анимации, файловых текстур и UV-зависимости. GLB не создавался, игровая установка/проверка, коллайдеры/LOD не входят в работу. Контакты колец с ложем и сердечником, опор с поперечными связями и задние сопряжения намеренны. Старые исходники не менялись.
''')
print('BUILT MA-HS03',flush=True)