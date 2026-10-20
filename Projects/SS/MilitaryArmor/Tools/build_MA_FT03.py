"""MA-FT03: six unchanged fuel vessels on independent cradles; source only."""
import sys,ast,json,math,bpy,bmesh
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
helper=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py')
module=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ['mount','inspect','preview']],type_ignores=[]),str(helper),'exec'))
BID='MA-FT03';folder=ROOT/'Blocks'/BID
xs=[-1.65,0,1.65];ys=[-1.60,1.60]
write(folder/'composition-plan.md','''# MA-FT03 — бак топлива 3×3: план до моделирования

Каталог fuel-tank-3x3: визуальная заготовка без игрового XML; вместимость, давление, состав топлива и скорости передачи не заданы. +Z вверх, -Y вперёд; правая система, условные BU, клетки не метры.

Семейство MA-FT01/MA-FT02: суженные торцы герметичных продольных сосудов, светлые гранёные силовые обручи, раздельные опоры и низкий коллектор. Повторно использовать MA-FT01-P02 v1.0 (6 сосудов) и MA-FT01-P03 v1.0 (12 обручей), без изменения источников и масштаба. Три дорожки по две секции, открытая поперечная сервисная щель с коллектором между рядами. Квадратный вариант оправдан удвоением числа секций по длине, не растяжением старого бака.

MA-FT02-P01 рассчитан на два сосуда, его опоры и коллектор не подходят шести. Создать MA-FT03-P01 v1.0: четыре раздельные поперечные опоры, узкие нижние связи и центральный защищённый коллектор с шестью короткими присоединениями к внутренним торцам сосудов. Общего поддона, большой сервисной крышки, глубоких колец теплоаккумулятора и грузовых люков нет. Новую деталь проверить до сборки, затем открыть отдельно новым процессом. Статика, без анимаций и GLB.
''')
if '--assembly-only' not in sys.argv:
 p=Part('MA-FT03-P01','Six-vessel segmented fuel cradle and central transfer header')
 for y in [-2.30,-.95,.90,2.25]:
  p.panel('Independent transverse load bearer',(0,y,.12),(4.83,.28,.24),'Armor',.08,.010)
  for x in xs:p.panel('Individual vessel saddle',(x,y,.265),(1.29,.34,.23),'Titanium',.10,.008)
 for x in xs:p.panel('Narrow lower structural stringer',(x,0,.08),(.17,4.95,.16),'Steel',.04,.007)
 p.panel('Protected central transfer header',(0,0,.58),(4.05,.36,.50),'Armor',.10,.010)
 for x in xs:
  p.panel('Header support post',(x,0,.29),(.28,.30,.39),'Titanium',.06,.008)
  p.panel('Recessed valve housing',(x,0,.83),(.36,.33,.21),'Titanium',.07,.006)
  for y in [-.29,.29]:p.cyl('Short sealed end transfer coupling',(x,y,.87),.145,.40,'Steel',axis='Y',verts=12)
  p.panel('Small closed inspection slot',(x,-.025,.945),(.19,.17,.035),'Dark',.03,.003)
 sockets=[mount('root',(0,0,0),'MilitaryArmor.fuel-tank.hull')]
 for lane,x in enumerate(xs):
  for row,y in enumerate(ys):sockets.append(mount(f'vessel-{lane}-{row}',(x,y,.31),'MilitaryArmor.fuel-tank.vessel'))
 bpy.context.view_layer.update();gate=inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges),o.name;bm.free()
 gate['source_normals_consistent']=True;gate['validated_before_assembly']=True
 p.save(mounts=sockets,notes='Static authoring fuel cradle. Procedural PBR, no emission/file textures/UV dependency. No capacity, pressure, fuel properties or mechanics specified. BU physical scale unspecified.')
 pf=ROOT/'Parts'/p.pid;data=json.loads((pf/'part.json').read_text())
 data['attachment_areas']=[dict(id=s['id']+'-area',role=s['role'],shape='logical-point-plane',dimensions=[.01,.01],parent='part',position=s['position'],forward=s['forward'],up=s['up'],compatibility=s['compatibility'],allowed_scale=[1,1,1],allowed_rotations_degrees=[0]) for s in sockets]
 write(pf/'part.json',data);write(pf/'geometry-validation.json',gate)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],7.9,450)
 write(pf/'README.md','# MA-FT03-P01 v1.0\n\nРаздельные опоры шести топливных сосудов, узкие нижние связи, защищённый центральный распределитель и шесть коротких присоединений. Исходник MA-FT03-P01.blend; материалы, отсутствие эмиссии, full-pose sockets и области в part.json. Статика, unit scale, условные BU, процедурный PBR без UV и файловых текстур. Немедленный gate геометрии/нормалей до сборки в geometry-validation.json. Самостоятельные Previews/top.png и perspective.png. GLB не создавался.\n')
a=Assembly(BID,'fuel-tank-3x3',[3,3],'Бак топлива 3×3')
a.instance('CradleAndTransferHeader','MA-FT03-P01');connections=[]
for lane,x in enumerate(xs):
 for row,y in enumerate(ys):
  iid=f'Vessel-L{lane}-R{row}';a.instance(iid,'MA-FT01-P02',loc=(x,y,.31));connections.append(dict(parent_instance='CradleAndTransferHeader',parent_socket=f'vessel-{lane}-{row}',child_instance=iid,child_socket='root'))
  for name,off in [('front',-.70),('rear',.65)]:
   hid=iid+'-Hoop-'+name;a.instance(hid,'MA-FT01-P03',loc=(x,y+off,.87));connections.append(dict(parent_instance=iid,parent_socket='band-'+name,child_instance=hid,child_socket='root'))
bpy.context.view_layer.update();inspect()
write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id=a.catalog_id,catalog_grid=a.grid,catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Six unchanged longitudinal fuel vessels, twelve faceted restraint hoops, independent transverse cradles and central protected header. No capacity, pressure or transfer mechanics specified.'))
bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
preview(folder,(0,0,.72),8.4,800,True)
write(folder/'README.md','''# MA-FT03 — бак топлива 3×3

Шесть продольных ёмкостей с суженными торцами: три дорожки по две секции. Светлые силовые обручи, открытые боковины и видимые торцы сохраняют топливное семейство MA-FT01/MA-FT02. Между рядами — низкий защищённый распределитель; опоры раздельные, без поддона и крупной сервисной крышки. От теплоаккумулятора отличается продольными сосудами с тонкими обручами, от контейнера — открытыми промежутками и отсутствием грузовых люков.

Редактируемый MA-FT03.blend; состав assembly.json; план повторного использования composition-plan.md. 19 экземпляров: одна новая MA-FT03-P01 v1.0, шесть готовых MA-FT01-P02 v1.0 и двенадцать готовых MA-FT01-P03 v1.0. Исходники готовых деталей не изменены; единичный масштаб. Геометрия новой детали проверена немедленно до сборки. Независимое открытие исходников/сборки и полные позы креплений — validation.json.

Previews/top.png, perspective.png, top-grayscale.png. Статический концепт, процедурный PBR, без эмиссии, UV-зависимости и файловых текстур. Условные BU, сетка 3×3 не метры. Каталог visual-only без игрового XML; вместимость, давление и игровые свойства не задавались. Посадки сосудов, обручей и присоединений имеют намеренное заглубление; коллайдеры и LOD не создавались. GLB и игровая интеграция не выполнялись.
''')
print('BUILT MA-FT03',flush=True)
