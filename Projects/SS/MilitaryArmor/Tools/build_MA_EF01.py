import sys,ast,json,math,bpy,bmesh
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
helper=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py');module=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ['mount','inspect','preview']],type_ignores=[]),str(helper),'exec'))
BID='MA-EF01';folder=ROOT/'Blocks'/BID
write(folder/'composition-plan.md','''# MA-EF01 — топливный двигатель 2×3: план до моделирования

Каталог fuel-thruster-2x3: visual-only, игрового XML нет. Тяга, расход, ресурсы, механика и физический масштаб не заданы. Правая система +Z вверх; -Y выход, +Y тяга; BU условные, сетка не метры.

Изучены MA-E01-P01…P05 и MA-E02-P01…P03: одиночная камера и тройная рама рассчитаны на иные диаметры и места сопряжений. Большое сопло нельзя растянуть без искажения толщины и интерфейсов. Создать MA-EF01-P01 — явный крупный вариант защищённой камеры с продольным питающим трактом и отдельными посадочными опорами; MA-EF01-P02 — глубокое расширяющееся полое сопло с фасетными термосекциями. Готовый MA-E01-P05 v1.0 подходит как небольшой сервисный картридж и используется в единичном масштабе. Старые исходники не изменять.

Силуэт: одно глубокое расширяющееся сопло впереди; сзади узкая высокая защищённая камера, закрытый питающий канал и стреловидные бронесекции по бокам. Это топливный двигатель, в отличие от широкой низкой электрической апертуры ионного семейства. Без пламени, автомобильных решёток и большой универсальной крышки. Новые детали проверять до сборки, сохранить отдельные previews. GLB не создавать.
''')
def finish(p,sockets,points=None):
 bpy.context.view_layer.update();gate=inspect()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges),o.name;bm.free()
 gate['source_normals_consistent']=True;gate['validated_before_assembly']=True
 for d in points or []:
  o=bpy.data.objects.new('point.'+d['id'],None);p.coll.objects.link(o);o.location=d['position'];o['direction']=d['direction'];o['role']=d['role']
 p.save(mounts=sockets,points=points,notes='Static source; unit scale. Procedural PBR; no image textures or UV dependency; no plume. Physical BU scale and gameplay parameters unspecified.')
 pf=ROOT/'Parts'/p.pid;data=json.loads((pf/'part.json').read_text());data['attachment_areas']=[dict(id=s['id']+'-area',role=s['role'],shape='logical-point-plane',dimensions=[.01,.01],parent='part',position=s['position'],forward=s['forward'],up=s['up'],compatibility=s['compatibility'],allowed_scale=[1,1,1],allowed_rotations_degrees=[0]) for s in sockets]
 write(pf/'part.json',data);write(pf/'geometry-validation.json',gate)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],4.2,450)
 write(pf/'README.md',f'# {p.pid} v1.0\n\n{p.title}. Редактируемый Blender, процедурные PBR материалы и эмиссия в part.json. Полные позы креплений, области и функциональные точки в метаданных. Статика, unit scale; BU условные. Немедленный gate geometry-validation.json до сборки. Отдельные Previews/top.png и perspective.png. GLB не создавался.\n')
if '--assembly-only' not in sys.argv:
 p=Part('MA-EF01-P01','Крупная защищённая камера с питающим трактом')
 for x in [-.66,.66]:
  p.panel('Separated hull mounting keel',(x,.55,.11),(.27,2.02,.22),'Titanium',.07,.009)
  p.section('Swept armored chamber guard', [(-.30,x,.83,.22,.83,.05),(.45,x,.96,.33,1.17,.10),(1.35,x*.73,.77,.26,.78,.07)],'Ceramic',.01)
 p.cyl('Protected combustion pressure vessel',(0,.40,1.0),.49,1.27,'Titanium',axis='Y',verts=16)
 p.ring('Nozzle coupling seat',(0,-.24,1),.48,.28,.15,'Y','Armor',16)
 p.section('Closed dorsal pressure shield',[(-.20,0,1.44,.50,.15,.045),(.55,0,1.60,.62,.21,.07),(1.20,0,1.27,.46,.18,.045)],'Armor',.009)
 p.section('Protected propellant feed channel',[(.80,0,.71,.51,.50,.09),(1.37,0,.60,.65,.59,.12),(1.56,0,.56,.47,.39,.08)],'Armor',.009)
 p.panel('Recessed propellant interface',(0,1.58,.58),(.31,.035,.20),'Dark',.03,.003)
 for x in [-.09,.09]:p.cyl('Sealed propellant connector',(x,1.61,.58),.053,.08,'Steel',axis='Y',verts=12)
 p.panel('Service cartridge seat',(0,.64,1.723),(.49,.38,.045),'Dark',.08,.003)
 for x in [-.52,.52]:p.box('Narrow chamber diagnostic',(x,.42,1.19),(.022,.19,.025),'Signal',.003)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.fuel-thruster.hull'),mount('bell',(0,-.25,1),'MilitaryArmor.fuel-thruster.large-bell'),mount('service',(0,.64,1.745),'MilitaryArmor.engine.accessory')])
 p=Part('MA-EF01-P02','Полое глубокое расширяющееся топливное сопло')
 n=20;profiles=[(0,.40),(-.32,.43),(-.80,.62),(-1.45,.92),(-1.45,.82),(-.80,.52),(-.32,.33),(0,.30)]
 v=[(r*math.cos(i*2*math.pi/n),y,r*math.sin(i*2*math.pi/n)) for y,r in profiles for i in range(n)];faces=[]
 for k in range(len(profiles)):
  q=(k+1)%len(profiles)
  for i in range(n):j=(i+1)%n;faces.append((k*n+i,k*n+j,q*n+j,q*n+i))
 o=p.mesh('Continuous hollow expansion wall',v,faces,'Titanium',.003);o.data.materials.append(p.mats['Dark'])
 for f in o.data.polygons:
  if f.index>=4*n:f.material_index=1
 p.ring('Exposed ceramic exit lip',(0,-1.45,0),.94,.82,.075,'Y','Ceramic',20)
 p.ring('Deep annular throat index',(0,-.13,0),.327,.303,.06,'Y','Signal',20)
 # Four narrow external thermal petals preserve the visible dark hollow.
 for angle in [math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4]:
  c,s=math.cos(angle),math.sin(angle)
  p.section('Detached-looking armored thermal petal',[(-.24,c*.44,s*.44,.16,.13,.03),(-.73,c*.64,s*.64,.19,.17,.04),(-1.27,c*.86,s*.86,.14,.13,.025)],'Ceramic',.004)
 points=[dict(id='thrust',role='thrust',parent='part',node='point.thrust',position=[0,0,0],direction=[0,1,0],up=[0,0,1]),dict(id='exhaust',role='exhaust',parent='part',node='point.exhaust',position=[0,-1.50,0],direction=[0,-1,0],up=[0,0,1])]
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.fuel-thruster.large-bell')],points)
a=Assembly(BID,'fuel-thruster-2x3',[2,3],'Топливный двигатель 2×3')
a.instance('PressureHousing','MA-EF01-P01');a.instance('ExpansionBell','MA-EF01-P02',loc=(0,-.25,1));a.instance('ServiceCartridge','MA-E01-P05',loc=(0,.64,1.745))
connections=[dict(parent_instance='PressureHousing',parent_socket='bell',child_instance='ExpansionBell',child_socket='root'),dict(parent_instance='PressureHousing',parent_socket='service',child_instance='ServiceCartridge',child_socket='root')]
bpy.context.view_layer.update();inspect()
write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id=a.catalog_id,catalog_grid=a.grid,catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Hollow deep bell, protected chamber and feed tract. Thrust +Y/exhaust -Y authoring only; no gameplay mapping or performance values.'))
bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
preview(folder,(0,-.05,.87),4.55,800,True)
write(folder/'README.md','''# MA-EF01 — топливный двигатель 2×3

Глубокое одиночное полое сопло расширяется к выходу. За ним защищённая камера, стреловидные бронесекции и закрытый питающий тракт; корпус сужается к кормовому интерфейсу. Тёмная внутренняя стенка и малая кольцевая диагностика горловины; декоративного пламени нет. Форма отличается от широкой электрической апертуры ионного двигателя.

MA-EF01.blend — исходник; assembly.json — состав и соединения; composition-plan.md — анализ повторного использования. Две новые детали MA-EF01-P01/P02 v1.0 и готовый MA-E01-P05 v1.0: три экземпляра, единичный масштаб. Старые исходники не изменены. Новые детали проверены до сборки; независимое открытие всех источников и сборки в validation.json. Previews/top.png, perspective.png и top-grayscale.png.

Правая система +Z вверх; -Y выход струи, +Y тяга. Функциональные точки авторинга находятся в сопле; игровые координаты не определялись. BU условные, клетки не метры. Каталог visual-only, игрового XML нет: тяга, расход и ресурсы не задавались. Статическая визуальная модель без анимаций. Процедурные PBR материалы, без файловых текстур/UV-зависимости; бирюзовая эмиссия только диагностика. Сопряжения оболочек намеренно заглублены; LOD и коллайдеров нет. GLB и игровая интеграция не выполнялись.
''')
print('BUILT MA-EF01',flush=True)
