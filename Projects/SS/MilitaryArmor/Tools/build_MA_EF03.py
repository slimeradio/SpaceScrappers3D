import sys,ast,json,math,bpy,bmesh
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
for filename,names in [('redesign_MA_B01_I01_FG01.py',['mount','inspect','preview']),('build_MA_EF01.py',['finish'])]:
 helper=Path(__file__).with_name(filename);mod=ast.parse(helper.read_text(encoding='utf8'));exec(compile(ast.Module(body=[n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(helper),'exec'))
BID='MA-EF03';folder=ROOT/'Blocks'/BID
write(folder/'composition-plan.md','''# MA-EF03 — план до моделирования

Каталог fuel-thruster-3x4, визуальный топливный двигатель 3×4, игрового XML нет. BU условные; сетка не метры. Правая система +Z вверх, -Y выхлоп, +Y тяга. Статика без анимации и пламени; тяга/расход/ресурсы не определялись.

MA-EF01-P02 v1.0 подходит: два независимых глубоких полых сопла, исходный размер и единичный масштаб, без копирования исходника. MA-E01-P05 v1.0 подходит для небольшого сервисного узла с существующей полной позой root. Корпус MA-EF01-P01 рассчитан на одну ось, растягивание не создаёт двух камер: новый MA-EF03-P01 — двухкамерная силовая рама с защищённым кормовым распределителем. Остальные двигательные корпуса не подходят интерфейсам парных больших сопел.

Силуэт: парные крупные круглые выходы, глубокая седловина между продольными камерами; сзади корпус сужается к единому защищённому распределителю. По бокам камер отдельные стреловидные бронесекции. Сопла — ведущие объёмы; сервисный картридж подчинённый. Полностью иной образ, чем широкая низкая электрическая апертура ионной серии. Новый корпус проверить немедленно до сборки, готовые сопла и сервисный источник проверить до использования. GLB не генерировать.
''')
if '--assembly-only' not in sys.argv:
 p=Part('MA-EF03-P01','Двухкамерный силовой корпус с кормовым распределителем')
 for x in [-1.01,1.01]:
  p.panel('Separate longitudinal hull bearer',(x,.58,.13),(.54,2.42,.26),'Titanium',.09,.012)
  p.cyl('Independent protected pressure chamber',(x,.30,1.07),.48,1.38,'Titanium',axis='Y',verts=20)
  p.ring('Bell coupling seat',(x,-.37,1.07),.48,.28,.15,'Y','Armor',20)
  p.section('Dorsal chamber shield',[(-.32,x,1.51,.57,.21,.06),(.44,x,1.65,.64,.25,.07),(1.07,x*.95,1.41,.48,.19,.05)],'Ceramic',.008)
  s=1 if x>0 else -1
  p.section('Swept outboard armor',[(-.39,x+s*.48,.91,.22,.56,.06),(.46,x+s*.55,1.02,.29,.93,.08),(1.31,x+s*.30,.68,.23,.55,.06)],'Ceramic',.008)
  p.section('Protected converging propellant branch',[(.92,x,.80,.40,.43,.06),(1.47,x*.60,.73,.43,.42,.07),(1.66,x*.22,.71,.35,.39,.06)],'Armor',.008)
  p.panel('Small chamber diagnostics',(x, .70,1.795),(.18,.08,.025),'Signal',.025,.002)
 p.panel('Rear armored common manifold',(0,1.52,.61),(1.72,.74,.75),'Armor',.17,.012)
 p.section('Central manifold hood',[(1.20,0,1.07,.72,.24,.06),(1.67,0,1.11,.93,.27,.07),(1.92,0,.79,.59,.19,.04)],'Ceramic',.008)
 p.panel('Recessed rear feed interface',(0,1.905,.59),(.53,.035,.27),'Dark',.045,.003)
 for x in [-.15,.15]:p.cyl('Recessed sealed feed port',(x,1.932,.59),.065,.055,'Steel',axis='Y',verts=12)
 p.panel('Small service seat',(0,1.51,1.275),(.49,.38,.04),'Dark',.06,.003)
 sockets=[mount('root',(0,0,0),'MilitaryArmor.fuel-thruster.hull'),mount('bellL',(-1.01,-.38,1.07),'MilitaryArmor.fuel-thruster.large-bell'),mount('bellR',(1.01,-.38,1.07),'MilitaryArmor.fuel-thruster.large-bell'),mount('service',(0,1.51,1.295),'MilitaryArmor.engine.accessory')]
 finish(p,sockets)
# Preflight reused parts before dependent assembly.
for pid in ['MA-EF01-P02','MA-E01-P05']:
 pm=json.loads((ROOT/'Parts'/pid/'part.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts'/pid/pm['source']));inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
a=Assembly(BID,'fuel-thruster-3x4',[3,4],'Топливный двигатель 3×4')
a.instance('TwinPressureHousing','MA-EF03-P01')
a.instance('ExpansionBellL','MA-EF01-P02',loc=(-1.01,-.38,1.07));a.instance('ExpansionBellR','MA-EF01-P02',loc=(1.01,-.38,1.07))
a.instance('ServiceCartridge','MA-E01-P05',loc=(0,1.51,1.295))
connections=[dict(parent_instance='TwinPressureHousing',parent_socket=s,child_instance=c,child_socket='root') for s,c in [('bellL','ExpansionBellL'),('bellR','ExpansionBellR'),('service','ServiceCartridge')]]
bpy.context.view_layer.update();inspect()
write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id=a.catalog_id,catalog_grid=a.grid,catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Twin hollow deep bells, independently armored pressure chambers, converging aft feed manifold; unit-scale source references. Static authoring-only functional directions: exhaust -Y, thrust +Y. No gameplay parameters.'))
bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
preview(folder,(0,.03,1.0),5.55,800,True)
write(folder/'README.md','''# MA-EF03 — топливный двигатель 3×4

Две независимые защищённые камеры питают два глубоких полых расширяющихся сопла. Между ними открытая седловина, сзади сходящиеся защищённые каналы и компактный общий распределитель. Общий облик топливного семейства сохранён; это двухкамерная компоновка, а не растянутый исходный двигатель.

MA-EF03.blend — редактируемая сборка. assembly.json — стабильные экземпляры/версии и полные соединения, composition-plan.md — анализ повторного использования. Новая деталь MA-EF03-P01 v1.0; повторно использованы два экземпляра MA-EF01-P02 v1.0 и один MA-E01-P05 v1.0, единичный масштаб. Предыдущие исходники не изменены. Новый корпус проверен до сборки; повторно используемые источники проверены до загрузки в сборку. validation.json — независимое открытие источников и сборки.

Previews/top.png, perspective.png и top-grayscale.png. Правая система +Z вверх, -Y выхлоп, +Y тяга. Функциональные точки находятся в каждом сопле; направления нормализованы. BU условные, размер клетки не приравнивается метрам. Визуальная заготовка без игрового XML: сила тяги, расход и ресурсы не заданы. Процедурные PBR материалы, небольшие диагностические области эмиссии; файловые текстуры и UV не нужны. Анимации, пламя, игровые коллайдеры и LOD не добавлялись. Стыки камер, сопел, бронекожухов и коллекторных каналов намеренно заглублены. GLB не создавались, интеграция в игру не выполнялась.
''')
print('BUILT',BID,flush=True)
