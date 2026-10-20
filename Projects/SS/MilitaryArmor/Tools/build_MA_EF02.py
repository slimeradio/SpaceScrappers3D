import sys,ast,json,math,bpy,bmesh
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
helper=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py');module=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ['mount','inspect','preview']],type_ignores=[]),str(helper),'exec'))
helper=Path(__file__).with_name('build_MA_EF01.py');module=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='finish'],type_ignores=[]),str(helper),'exec'))
BID='MA-EF02';folder=ROOT/'Blocks'/BID
write(folder/'composition-plan.md','''# MA-EF02 — топливный двигатель 1×2: план состава

Каталог fuel-thruster-1x2 — visual-only, без XML. BU условные, размеры сетки не метры. +Z вверх, -Y выхлоп, +Y тяга. Тяга/расход/ресурсы и игровые механизмы не задаются.

Изучены MA-EF01 и MA-E01, их детали и интерфейсы. MA-EF01-P01/P02 слишком велики и имеют иной посадочный диаметр; масштабировать их нельзя. Сопло MA-E01-P03 v1.0 уже имеет подходящие компактные размеры 0.76×0.71×0.76 BU, реальную открытую полость и функциональные точки: повторно использовать без изменений в единичном масштабе. MA-E01-P05 v1.0 — подходящий малый сервисный картридж 0.44×0.33 BU, повторно использовать. Исходники обеих деталей перед сборкой открыты и проверены.

MA-E01-P01/P02 предназначены для старой кассетной компоновки: корпус имеет полную нижнюю плиту и расширенную камеру с отдельными термоэкранами. Создать явный вариант MA-EF02-P01: узкий защищённый тракт с двумя раздельными опорами, малой камерой и открытым с боков соплом. Новый корпус сохраняет характер топливного семейства EF01, но без крупной круглой крышки и широких плеч. Новую деталь проверить сразу до сборки. Статика, без пламени и выдуманных анимаций. GLB не создавать.
''')
if '--assembly-only' not in sys.argv:
 p=Part('MA-EF02-P01','Компактная защищённая камера и питающий тракт')
 for x in [-.29,.29]:
  p.panel('Separated narrow hull bearer',(x,.32,.08),(.17,1.25,.16),'Titanium',.04,.004)
  p.section('Tapered pressure guard',[(-.20,x,.42,.13,.38,.03),(.18,x,.55,.20,.57,.04),(.78,x*.70,.42,.16,.32,.03)],'Ceramic',.005)
 p.cyl('Protected compact pressure vessel',(0,.20,.49),.24,.91,'Titanium',axis='Y',verts=16)
 p.ring('Bell receiver',(0,-.26,.49),.255,.14,.08,'Y','Armor',16)
 p.section('Closed propellant supply tract',[(.42,0,.34,.30,.35,.055),(.85,0,.31,.38,.40,.065),(.98,0,.29,.27,.28,.045)],'Armor',.005)
 p.section('Raised dorsal pressure shield',[(-.13,0,.71,.30,.12,.03),(.18,0,.83,.43,.18,.04),(.58,0,.75,.34,.12,.025)],'Armor',.005)
 p.panel('Compact service landing',(0,.19,.923),(.46,.35,.035),'Dark',.045,.002)
 p.panel('Recessed supply connector',(0,.995,.30),(.22,.025,.13),'Dark',.02,.002)
 for x in [-.065,.065]:p.cyl('Sealed feed connector',(x,1.015,.30),.033,.05,'Steel',axis='Y',verts=12)
 for x in [-.244,.244]:p.box('Small chamber diagnostic',(x,.13,.61),(.012,.12,.016),'Signal',.002)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.fuel-thruster.hull'),mount('bell',(0,-.28,.49),'MilitaryArmor.engine.nozzle'),mount('service',(0,.19,.9405),'MilitaryArmor.engine.accessory')])
a=Assembly(BID,'fuel-thruster-1x2',[1,2],'Топливный двигатель 1×2')
a.instance('PressureHousing','MA-EF02-P01');a.instance('ExpansionBell','MA-E01-P03',loc=(0,-.28,.49));a.instance('ServiceCartridge','MA-E01-P05',loc=(0,.19,.9405))
connections=[dict(parent_instance='PressureHousing',parent_socket='bell',child_instance='ExpansionBell',child_socket='chamber'),dict(parent_instance='PressureHousing',parent_socket='service',child_instance='ServiceCartridge',child_socket='root')]
bpy.context.view_layer.update();inspect()
write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id=a.catalog_id,catalog_grid=a.grid,catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Compact fuel pressure chamber with reused hollow bell; exhaust -Y / thrust +Y; authoring metadata only.'))
bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
preview(folder,(0,.03,.47),2.8,800,True)
write(folder/'README.md','''# MA-EF02 — топливный двигатель 1×2

Узкая защищённая камера на раздельных опорах, сужающийся питающий тракт и глубокое открытое сопло. Компактный член топливного семейства EF01; полость сохраняется и в уменьшенном силуэте, в отличие от плоской электрической апертуры ионного семейства. Постоянного пламени нет.

MA-EF02.blend — редактируемая сборка; assembly.json — стабильные экземпляры, версии и полные позы соединений. Одна новая деталь MA-EF02-P01 v1.0; повторно используются MA-E01-P03 и MA-E01-P05 v1.0 без изменений и масштабирования. Всего 3 экземпляра. План решения о reuse — composition-plan.md. Независимая проверка — validation.json. Previews/top.png, perspective.png, top-grayscale.png.

Правая система +Z вверх, -Y выхлоп и +Y тяга; точки находятся в исходнике сопла и в экземпляре ExpansionBell. BU условные, сетка не метры. Каталог visual-only без XML: сила тяги и расход не задавались. Статичная авторская модель, без LOD/коллайдеров/игровой интеграции. Процедурные PBR, без файловых текстур и UV-зависимости; эмиссия — только малая диагностика. Сопряжения корпуса, защищённой камеры и посадочного кольца намеренно заглублены. GLB не создавались.
''')
print('BUILT MA-EF02',flush=True)