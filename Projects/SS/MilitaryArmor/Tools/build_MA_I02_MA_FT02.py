import sys,math,json,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
# Read-only helper reuse; execute function definitions only, never old build entry points.
helper=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py')
node=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in ['mount','inspect','preview']],type_ignores=[]),str(helper),'exec'))
IDS=['MA-I02','MA-FT02']
if any(x.startswith('--only=') for x in sys.argv):IDS=[next(x.split('=',1)[1] for x in sys.argv if x.startswith('--only='))]
DESIGN={
'MA-I02':('cargo-2x2','Грузовой контейнер 2×2','Квадратный цельный грузовой объём с парой крупных загрузочных люков и двумя внешними направляющими. Семейство MA-I01, без аккумуляторных кассет.','MA-I01-R2-P02 v2.0: повторно использовать 2 люка 2.87×1.29 BU без масштаба. MA-I01-R2-P03 v2.0: повторно использовать 2 направляющие длиной 3.87 BU. MA-I01-R2-P01 не подходит: корпус 3.66×1.61 BU не закрывает квадратную компоновку; создать MA-I02-P01. Батарейные детали и универсальные сервисные крышки не использовать.'),
'MA-FT02':('fuel-tank-2x2','Бак топлива 2×2','Две раздельные продольные ёмкости с обручами на поперечных опорах. Открытые промежутки и видимые торцы сосудов различают бак и цельный контейнер.','MA-FT01-P02 v1.0 повторно использовать 2 ёмкости 1.24×2.66 BU. MA-FT01-P03 v1.0 повторно использовать 4 обруча, исходный размер без масштаба. MA-FT01-P01 узок для двух сосудов и имеет лишнюю площадку сервисной крышки; создать MA-FT02-P01: раздельные поперечные опоры и низкий защищённый коллектор. MA-R01-P05 не использовать.')}

def finish(p,sockets):
 bpy.context.view_layer.update();gate=inspect()
 p.save(mounts=sockets,notes='Static MilitaryArmor authoring concept. Procedural PBR, no file textures or UV dependency. No animation or game mechanics. BU physical scale unspecified.')
 folder=ROOT/'Parts'/p.pid;d=json.loads((folder/'part.json').read_text())
 d['attachment_areas']=[dict(id=m['id']+'-area',role=m['role'],shape='logical-point-plane',dimensions=[.01,.01],parent='part',position=m['position'],forward=m['forward'],up=m['up'],compatibility=m['compatibility'],restrictions='unit scale, exact full socket pose') for m in sockets]
 write(folder/'part.json',d);write(folder/'geometry-validation.json',dict(**gate,validated_before_assembly=True))
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(folder,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.55,450)
 write(folder/'README.md',f'# {p.pid} v1.0\n\n{p.title}. Самостоятельный редактируемый Blender, процедурные PBR-материалы из part.json; без файловых текстур и UV, эмиссия отсутствует. Полные логические sockets и области, unit scale, статическая модель. Геометрический gate немедленно до сборки: geometry-validation.json; отдельные top/perspective PNG. GLB не создавался.\n')

if '--verify' not in sys.argv:
 for bid in IDS:
  cid,title,design,reuse=DESIGN[bid];folder=ROOT/'Blocks'/bid
  write(folder/'composition-plan.md',f'# {bid} — план до моделирования\n\nКаталог {cid}: визуальная заготовка, сетка 2×2, игрового XML нет. Вместимость и механика не задаются. {design}\n\nАнализ библиотеки: {reuse}\n\nПравая система, +Z вверх, -Y вперёд; условные BU, клетки не метры. Единичный масштаб. Сначала самостоятельная деталь и geometry gate, затем экземпляры готовых источников, полные позы креплений и независимое открытие.\n')
 if '--assembly-only' not in sys.argv:
  p=Part('MA-I02-P01','Квадратный силовой корпус контейнера')
  p.panel('Continuous square cargo volume',(0,0,.64),(3.66,3.58,1.28),'Armor',.22,.016)
  for x in [-1.67,1.67]:
   for y in [-1.60,1.60]:p.panel('Reinforced cargo corner',(x,y,.69),(.28,.29,1.38),'Ceramic',.07,.009)
  for x in [-1.23,0,1.23]:
   for y in [-1.75,1.75]:p.box('Cargo transverse stiffener',(x,y,.66),(.13,.12,1.17),'Titanium',.009)
  for y in [-.83,.83]:p.panel('Large hatch gasket',(0,y,1.30),(3.01,1.44,.07),'Dark',.17,.008)
  p.box('Structural roof divider',(0,0,1.31),(3.31,.18,.10),'Titanium',.009)
  for x in [-1.81,1.81]:p.box('Recessed side handling channel',(x,0,.70),(.025,2.72,.18),'Dark',.003)
  finish(p,[mount('root',(0,0,0),'MilitaryArmor.cargo.hull'),mount('hatchF',(0,-.83,1.335),'MilitaryArmor.cargo.wide-hatch'),mount('hatchB',(0,.83,1.335),'MilitaryArmor.cargo.wide-hatch'),mount('railF',(0,-1.78,.16),'MilitaryArmor.cargo.rail'),mount('railB',(0,1.78,.16),'MilitaryArmor.cargo.rail')])
  p=Part('MA-FT02-P01','Парные опоры ёмкостей с защищённым коллектором')
  for y in [-.75,.60]:
   p.panel('Independent transverse load bearer',(0,y,.12),(3.50,.30,.24),'Armor',.09,.012)
   for x in [-.87,.87]:p.panel('Tank saddle',(x,y,.24),(1.27,.38,.25),'Titanium',.11,.008)
  for x in [-1.57,1.57]:p.panel('Narrow longitudinal tie',(x,-.15,.11),(.15,2.90,.22),'Steel',.045,.008)
  p.panel('Protected front transfer header',(0,-1.48,.39),(2.99,.34,.43),'Armor',.10,.009)
  for x in [-.87,.87]:
   p.cyl('Recessed end coupling',(x,-1.57,.49),.18,.22,'Titanium',axis='Y',verts=12)
   p.cyl('Sealed transfer cap',(x,-1.70,.49),.125,.06,'Steel',axis='Y',verts=12)
  p.panel('Small central inspection cover',(0,-1.48,.625),(.42,.23,.045),'Titanium',.04,.004)
  finish(p,[mount('root',(0,0,0),'MilitaryArmor.fuel-tank.hull'),mount('leftVessel',(-.87,0,.31),'MilitaryArmor.fuel-tank.vessel'),mount('rightVessel',(.87,0,.31),'MilitaryArmor.fuel-tank.vessel')])
 for bid in IDS:
  cid,title,design,reuse=DESIGN[bid];a=Assembly(bid,cid,[2,2],title);connections=[]
  def add(i,pid,pos=(0,0,0),parent_i=None,ps=None,cs='root'):
   a.instance(i,pid,loc=pos)
   if parent_i:connections.append(dict(parent_instance=parent_i,parent_socket=ps,child_instance=i,child_socket=cs))
  add('Structure',bid+'-P01')
  if bid=='MA-I02':
   for name,y in [('F',-.83),('B',.83)]:add('LoadingHatch'+name,'MA-I01-R2-P02',(0,y,1.335),'Structure','hatch'+name)
   for name,y in [('F',-1.78),('B',1.78)]:add('CargoRail'+name,'MA-I01-R2-P03',(0,y,.16),'Structure','rail'+name)
  else:
   for label,x in [('left',-.87),('right',.87)]:
    add(label+'Vessel','MA-FT01-P02',(x,0,.31),'Structure',label+'Vessel')
    for label2,y in [('front',-.70),('rear',.65)]:add(label+'Hoop'+label2,'MA-FT01-P03',(x,y,.87),label+'Vessel','band-'+label2)
  folder=ROOT/'Blocks'/bid;bpy.context.view_layer.update();inspect()
  write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=bid,version='1.0',title=title,catalog_id=cid,catalog_grid=[2,2],catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes=design))
  bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(bid+'.blend')))
  preview(folder,(0,-.02,.71),5.45,800,True)
  write(folder/'README.md',f'# {bid} — {title}\n\n{design}\n\n{len(a.instances)} экземпляров готовых деталей, только 1 новый источник {bid}-P01; остальные источники повторно используются без изменения и масштаба. Анализ состава composition-plan.md; исходник {bid}.blend и assembly.json. Проверки validation.json; Previews/top.png, perspective.png, top-grayscale.png.\n\nВизуальная заготовка каталога без игрового XML, вместимость и механика не заданы. BU условные, сетка 2×2 не метры. Статика, процедурные PBR-материалы; без файловых текстур/UV. Контакты опор, уплотнений и обручей конструктивно намеренны. GLB не создавался, игровой интеграции нет.\n')
else:
 for bid in IDS:
  folder=ROOT/'Blocks'/bid;a=json.loads((folder/'assembly.json').read_text());parts={};checks=[]
  for pid in sorted(set(i['part_id'] for i in a['instances'])):
   p=ROOT/'Parts'/pid;d=json.loads((p/'part.json').read_text());parts[pid]=d;bpy.ops.wm.open_mainfile(filepath=str(p/d['source']));gate=inspect()
   for obj in bpy.context.scene.objects:
    if obj.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(obj.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert all(math.isfinite(v) for vert in me.vertices for v in vert.co);ev.to_mesh_clear()
   gate['source_normals_consistent']=True;gate['evaluated_coordinates_finite']=True
   for m in d['mounts']:
    o=bpy.data.objects.get('socket.'+m['id']);assert o and (o.location-Vector(m['position'])).length<1e-6
   checks.append(dict(id=pid,version=d['version'],geometry=gate))
  bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')));gate=inspect();instances={i['id']:i for i in a['instances']};results=[]
  for i in a['instances']:
   o=bpy.data.objects.get(i['id']);assert o and o['part_id']==i['part_id'] and o['part_version']==i['version']==parts[i['part_id']]['version'];assert o.parent.name==i['parent'];assert (o.location-Vector(i['translation'])).length<1e-6;assert all(abs(v-1)<1e-6 for v in o.scale);assert (folder/i['source']).resolve().exists()
  for c in a['connections']:
   pi=instances[c['parent_instance']];ci=instances[c['child_instance']];pm=next(m for m in parts[pi['part_id']]['mounts'] if m['id']==c['parent_socket']);cm=next(m for m in parts[ci['part_id']]['mounts'] if m['id']==c['child_socket']);po=bpy.data.objects[pi['id']];co=bpy.data.objects[ci['id']]
   pos=(po.matrix_world@Vector(pm['position'])-co.matrix_world@Vector(cm['position'])).length
   fwd=(po.matrix_world.to_3x3()@Vector(pm['forward'])-co.matrix_world.to_3x3()@Vector(cm['forward'])).length;up=(po.matrix_world.to_3x3()@Vector(pm['up'])-co.matrix_world.to_3x3()@Vector(cm['up'])).length;compat=bool(set(pm['compatibility'])&set(cm['compatibility']));assert max(pos,fwd,up)<1e-6 and compat
   results.append(dict(**c,position_error=pos,forward_error=fwd,up_error=up,semantic_compatibility=compat))
  write(folder/'validation.json',dict(id=bid,checks_passed=True,independent_reopen=True,source_parts=checks,assembly_geometry=gate,connections=results,instance_count=len(a['instances']),unit_scale=True,dependency_paths_resolved=True,no_glb_generated=True,game_validation=False))
  print('VERIFIED',bid,flush=True)