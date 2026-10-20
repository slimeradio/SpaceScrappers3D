import sys,ast,json,math,bpy,bmesh
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
for filename,names in [('redesign_MA_B01_I01_FG01.py',['mount','inspect','preview']),('build_MA_EF01.py',['finish'])]:
 helper=Path(__file__).with_name(filename);mod=ast.parse(helper.read_text(encoding='utf8'));node=ast.Module(body=[n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
 if filename=='build_MA_EF01.py':
  node=ast.parse(ast.unparse(node).replace('4.2, 450','8.0, 550'))
 exec(compile(node,str(helper),'exec'))
BID='MA-EF04';folder=ROOT/'Blocks'/BID
axes=[('L',-1.08,1.04),('R',1.08,1.04),('U',0,2.95)]
write(folder/'composition-plan.md','''# MA-EF04 — план до моделирования

Каталог fuel-thruster-4x6, топливный двигатель 4×6; visual-only без игрового XML. BU условные, не метры. Правая система +Z вверх, -Y выхлоп, +Y тяга. Без тяговых чисел, расхода, пламени и анимаций.

MA-EF01-P02 v1.0 — готовое глубокое полое сопло; использовать три экземпляра без изменения исходника и без масштабирования. MA-E01-P05 v1.0 — готовый подчинённый сервисный узел, единичный масштаб. MA-EF03-P01 v1.0 — двухкамерная короткая рама, не подходит треугольной компоновке и длинному питающему тракту. Вместо растягивания создать MA-EF04-P01: тяжёлый трёхкамерный корпус с высоким центральным трактом, независимыми защищёнными каналами и продольными опорами. Детали других функциональных семейств не использовать.

Два нижних сопла и одно верхнее образуют треугольный кластер. Длинный кормовой силовой хребет расходится к трём камерам. Вид сверху: раздвоенный выход и центральный верхний канал, боковые защищённые магистрали. В объёме читается треугольник глубоких полостей. Отличается от плоской апертуры ионного семейства. Каждую новую деталь проверить немедленно до сборки, повторно используемые источники пройти preflight. GLB запрещён.
''')
if '--assembly-only' not in sys.argv:
 p=Part('MA-EF04-P01','Тяжёлый трёхкамерный корпус с длинным распределительным хребтом')
 for name,x,z in axes:
  p.cyl('Protected pressure chamber '+name,(x,.58,z),.48,1.75,'Titanium',axis='Y',verts=20)
  p.ring('Bell coupling '+name,(x,-.29,z),.48,.28,.15,'Y','Armor',20)
  p.section('Dorsal pressure shield '+name,[(-.20,x,z+.47,.53,.20,.05),(.62,x,z+.60,.65,.27,.06),(1.49,x*.95,z+.35,.48,.19,.04)],'Ceramic',.009)
  p.section('Independent closed branch '+name,[(1.20,x,z-.15,.43,.46,.07),(2.19,x*.80,z-.18,.48,.48,.07),(3.20,x*.40,1.29,.41,.47,.07),(3.55,x*.25,1.18,.38,.39,.06)],'Armor',.01)
  p.panel('Small pressure diagnostic '+name,(x,.85,z+.746),(.16,.09,.025),'Signal',.02,.002)
 for x in [-1.09,1.09]:
  p.panel('Heavy longitudinal hull bearer',(x,1.46,.15),(.52,4.22,.30),'Titanium',.10,.012)
  side=1 if x>0 else -1
  p.section('Swept outboard armor',[(-.24,x+side*.47,.92,.27,.71,.06),(.89,x+side*.57,1.05,.33,1.10,.09),(2.32,x+side*.30,.72,.29,.73,.07),(3.42,x*.7,.49,.22,.50,.05)],'Ceramic',.009)
 # Separate diagonal load paths support the high chamber; no slab across the nozzle mouths.
 for x in [-1.0,1.0]:
  p.section('Inclined upper chamber load path',[(.10,x,.61,.25,.32,.04),(.54,x*.57,1.54,.29,.35,.05),(.99,x*.15,2.75,.31,.40,.05)],'Titanium',.009)
 p.panel('Aft distributor body',(0,3.39,.79),(1.92,.94,1.17),'Armor',.20,.014)
 p.section('Long dorsal distribution spine',[(1.45,0,2.63,.56,.33,.06),(2.32,0,2.23,.67,.41,.07),(3.53,0,1.49,.78,.37,.06),(3.87,0,1.15,.56,.28,.05)],'Ceramic',.009)
 p.panel('Recessed aft feed panel',(0,3.878,.74),(.69,.045,.37),'Dark',.06,.004)
 for x in [-.19,.19]:p.cyl('Recessed sealed feed port',(x,3.905,.74),.095,.065,'Steel',axis='Y',verts=12)
 p.panel('Small service seat',(0,3.34,1.765),(.49,.38,.04),'Dark',.06,.003)
 sockets=[mount('root',(0,0,0),'MilitaryArmor.fuel-thruster.hull')]+[mount('bell'+n,(x,-.30,z),'MilitaryArmor.fuel-thruster.large-bell') for n,x,z in axes]+[mount('service',(0,3.34,1.785),'MilitaryArmor.engine.accessory')]
 finish(p,sockets)
for pid in ['MA-EF01-P02','MA-E01-P05']:
 pm=json.loads((ROOT/'Parts'/pid/'part.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts'/pid/pm['source']));inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
a=Assembly(BID,'fuel-thruster-4x6',[4,6],'Топливный двигатель 4×6')
a.instance('TriplePressureHousing','MA-EF04-P01')
for n,x,z in axes:a.instance('ExpansionBell'+n,'MA-EF01-P02',loc=(x,-.30,z))
a.instance('ServiceCartridge','MA-E01-P05',loc=(0,3.34,1.785))
connections=[dict(parent_instance='TriplePressureHousing',parent_socket='bell'+n,child_instance='ExpansionBell'+n,child_socket='root') for n,x,z in axes]+[dict(parent_instance='TriplePressureHousing',parent_socket='service',child_instance='ServiceCartridge',child_socket='root')]
bpy.context.view_layer.update();inspect()
write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id=a.catalog_id,catalog_grid=a.grid,catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Three deep hollow bells in triangular arrangement. Protected independent pressure chambers and elongated aft feed spine. Unit scale; exhaust -Y, thrust +Y.'))
bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
preview(folder,(0,1.04,1.90),7.7,850,True)
write(folder/'README.md','''# MA-EF04 — топливный двигатель 4×6

Три глубоких расширяющихся сопла собраны треугольником: два нижних и одно верхнее. Каждая камера защищена отдельно; длинный кормовой хребет распределяет питание по трём закрытым каналам. Диагональные связи поддерживают верхнюю камеру; между соплами остаются открытые промежутки. Без плоской ионной решётки и универсального поддона с крышками.

MA-EF04.blend — редактируемая сборка. Новая деталь MA-EF04-P01 v1.0, три готовых MA-EF01-P02 v1.0 и один MA-E01-P05 v1.0: пять экземпляров, все с единичным масштабом. Существующие исходники не изменены. composition-plan.md — план повторного использования, assembly.json — стабильные экземпляры, версии и соединения полных socket-поз. Новый корпус проверен до сборки; источники повторно используемых деталей прошли preflight. validation.json — независимое повторное открытие источников и сборки.

Предпросмотры: Previews/top.png, perspective.png, top-grayscale.png. Правая система +Z вверх; -Y выхлоп, +Y тяга. Функциональные точки у каждого сопла; направления нормализованы. BU условные, клетки не метры. Визуальная заготовка без игрового XML, тяга и расход не заданы. Процедурные PBR, малая диагностическая эмиссия; файловых текстур и UV-зависимости нет. Статика без пламени. Игровые LOD, коллайдеры и интеграция не выполнялись. Стыки силовых каналов и камер намеренно заглублены. GLB не создавались.
''')
print('BUILT',BID,flush=True)
