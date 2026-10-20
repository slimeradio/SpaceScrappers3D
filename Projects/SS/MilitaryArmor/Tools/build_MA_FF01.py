import sys,math,json,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
helper=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py')
node=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in ['mount','inspect','preview']],type_ignores=[]),str(helper),'exec'))
baseinspect=inspect
def inspect():
 r=baseinspect()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert all(math.isfinite(v) for vert in me.vertices for v in vert.co);ev.to_mesh_clear()
 r['source_normals_consistent']=True;r['evaluated_coordinates_finite']=True
 return r
bid='MA-FF01';folder=ROOT/'Blocks'/bid;cid='fuel-factory-3x5';title='Фабрика топлива 3×5'
design='Последовательная технологическая линия: высокий ступенчатый рабочий объём с кольцевым воротником, низкая поперечная рабочая камера и конечный продольный барабан с боковыми насосными головами. Разные высоты и открытые промежутки, защищённый связующий коллектор. Не набор одинаковых кассет или крышек.'
reuse='MA-FG01-R2-P02 v2.0 (1.28×2.19×1.35 BU) повторно использовать как конечный барабан; MA-FG01-R2-P03 v2.0 (0.68×0.64×0.845 BU) повторно использовать дважды как боковые головы. Исходные root sockets и теги совпадают, масштаб 1. MA-FG01-R2-P01/P04 рассчитаны на компактный квадрат 3×3 и не покрывают продольную линию. MA-F01-R2-P01/P02/P03 производят компактную поперечную композицию, не длинную линию. MA-FT01-P02 и обручи MA-FT01-P03, изученные в MA-FT02, являются закрытыми ёмкостями хранения и повторят образ бака; не используются. Kits отсутствует. Новые P01: открытая рама с посадками; P02: высокий ступенчатый рабочий объём; P03: низкая поперечная камера; P04: защищённая трасса коллектора.'
def finish(p,sockets):
 bpy.context.view_layer.update();gate=inspect();p.save(mounts=sockets,notes='Static fuel factory art candidate. Uniform procedural PBR. No file textures, UV dependency or animations. No recipe, output or capacity claims; BU physical scale unspecified.')
 f=ROOT/'Parts'/p.pid;d=json.loads((f/'part.json').read_text());d['attachment_areas']=[dict(id=m['id']+'-area',role=m['role'],shape='logical-point-plane',dimensions=[.01,.01],parent='part',position=m['position'],forward=m['forward'],up=m['up'],compatibility=m['compatibility'],allowed_rotations_degrees=[0],restrictions='unit scale, exact full socket pose') for m in sockets];write(f/'part.json',d);write(f/'geometry-validation.json',dict(**gate,validated_before_assembly=True))
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(f,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.5,450)
 write(f/'README.md',f'# {p.pid} v1.0\n\n{p.title}. Самостоятельный редактируемый Blender, процедурные PBR-материалы и эмиссия перечислены в part.json. Файловых текстур и зависимости от UV нет. Статическая модель, единичный масштаб, полные логические sockets и области. Геометрия и нормали проверены до сборки — geometry-validation.json. Отдельные top/perspective в Previews. GLB не создавался.\n')
if '--verify' not in sys.argv:
 write(folder/'composition-plan.md',f'# {bid} — план состава до моделирования\n\nКаталог {cid}: {title}; визуальная заготовка, игрового XML нет. Входные ресурсы, рецепт, производительность не заданы.\n\n{design}\n\n{reuse}\n\nУсловные BU, правая система, +Z вверх, -Y вперёд. Сетка 3×5 не метры. Сначала новые отдельные исходники, немедленная геометрическая проверка, затем сборка. Все экземпляры unit scale.\n')
 if '--assembly-only' not in sys.argv:
  p=Part(bid+'-P01','Открытая рама технологической линии')
  for x in [-2.12,2.12]:p.panel('Long structural runner',(x,0,.14),(.29,7.8,.28),'Armor',.12,.015)
  for y,w in [(3.05,4.0),(1.4,4.0),(-.48,4.1),(-2.7,4.1),(-3.7,4.4)]:
   p.panel('Transverse support',(0,y,.19),(w,.32,.38),'Titanium',.10,.015)
  for x,y,w,d in [(-.55,2.35,2.1,2.15),(0,-.35,3.7,1.24),(-.70,-2.55,1.32,2.18),(1.30,-2.55,.9,2.0)]:p.panel('Specific process saddle',(x,y,.28),(w,d,.20),'Armor',.13,.012)
  finish(p,[mount('root',(0,0,0),'MilitaryArmor.fuel-factory.frame'),mount('tower',(-.55,2.35,.38),'MilitaryArmor.fuel-factory.tower'),mount('chamber',(0,-.35,.38),'MilitaryArmor.fuel-factory.chamber'),mount('drum',(-.70,-2.55,.38),'MilitaryArmor.engine-room.drum'),mount('pumpF',(1.30,-3.0,.38),'MilitaryArmor.engine-room.pump'),mount('pumpB',(1.30,-2.0,.38),'MilitaryArmor.engine-room.pump'),mount('routes',(0,0,0),'MilitaryArmor.fuel-factory.routes')])
  p=Part(bid+'-P02','Ступенчатый рабочий объём линии')
  p.cyl('Faceted working column',(0,0,1.08),.82,2.16,'Titanium',verts=12)
  for z,r in [(.22,.91),(1.05,.94),(1.87,.88)]:p.ring('Split shielding collar',(0,0,z),r,r-.13,.15,mat='Ceramic',verts=12)
  p.cyl('Shoulder',(0,0,2.10),.68,.23,'Armor',verts=12)
  p.cyl('Narrow upper stage',(.10,0,2.36),.42,.35,'Steel',verts=10)
  p.cyl('Sealed upper head',(.10,0,2.57),.49,.11,'Ceramic',verts=10)
  for x in [-.79,.79]:p.panel('Vertical protective rib',(x,0,1.13),(.16,.46,1.87),'Armor',.06,.009)
  p.panel('Offset transfer shoulder',(1.05,.05,.92),(.61,1.30,1.22),'Armor',.14,.012)
  p.panel('Shoulder inspection face',(1.05,.05,1.55),(.47,1.01,.065),'Ceramic',.10,.008)
  p.box('Recessed diagnostics',(-.06,-.81,1.51),(.28,.04,.16),'Dark',.008)
  p.box('Small status index',(-.06,-.84,1.51),(.13,.025,.04),'Signal',.002)
  finish(p,[mount('root',(0,0,0),'MilitaryArmor.fuel-factory.tower')])
  p=Part(bid+'-P03','Поперечная защищённая рабочая камера')
  p.section('Transverse stepped chamber',[(-.58,0,.50,3.60,.83,.14),(-.42,0,.65,3.60,1.12,.20),(.40,0,.65,3.36,1.12,.20),(.58,0,.46,3.15,.80,.16)],'Armor',.015)
  for x in [-1.32,0,1.32]:p.panel('Raised chamber reinforcement',(x,0,1.23),(.21,.91,.14),'Ceramic',.055,.009)
  for x in [-.70,.70]:p.panel('Protected chamber inspection face',(x,.04,1.23),(.91,.64,.07),'Titanium',.11,.006)
  for x in [-1.70,1.70]:p.cyl('Sealed chamber coupling',(x,0,.66),.29,.26,'Steel',axis='X',verts=12)
  p.panel('Narrow embedded process indicator',(.64,-.18,1.275),(.32,.05,.025),'Signal',.009,.002)
  finish(p,[mount('root',(0,0,0),'MilitaryArmor.fuel-factory.chamber')])
  p=Part(bid+'-P04','Связующий защищённый коллектор линии')
  p.box('Main shielded route',(1.68,.24,.62),(.23,5.70,.23),'Titanium',.020)
  for y in [2.35,-.35,-2.0,-3.0]:
   end=-.55 if y==2.35 else 0 if y==-.35 else 1.30
   p.box('Transverse process link',((1.68+end)/2,y,.62),(1.68-end+.12,.19,.19),'Steel',.015)
   p.cyl('Closed vertical transfer',(end,y,.85),.13,.47,'Titanium',verts=12)
  p.box('Lower drum connection',(.47,-3.05,.62),(1.71,.19,.19),'Steel',.015)
  for y in [2.95,1.55,.60,-1.20,-2.60]:p.panel('Armored line bridge',(1.68,y,.83),(.44,.32,.14),'Armor',.07,.008)
  finish(p,[mount('root',(0,0,0),'MilitaryArmor.fuel-factory.routes')])
 a=Assembly(bid,cid,[3,5],title);connections=[]
 a.instance('LineStructure',bid+'-P01')
 for iid,pid,pos,sock in [('TallWorkingStage',bid+'-P02',(-.55,2.35,.38),'tower'),('CrossProcessChamber',bid+'-P03',(0,-.35,.38),'chamber'),('FinalProcessDrum','MA-FG01-R2-P02',(-.70,-2.55,.38),'drum'),('FrontTransferHead','MA-FG01-R2-P03',(1.30,-3.0,.38),'pumpF'),('RearTransferHead','MA-FG01-R2-P03',(1.30,-2.0,.38),'pumpB'),('ShieldedRouting',bid+'-P04',(0,0,0),'routes')]:
  a.instance(iid,pid,loc=pos);connections.append(dict(parent_instance='LineStructure',parent_socket=sock,child_instance=iid,child_socket='root'))
 bpy.context.view_layer.update();inspect()
 write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=bid,version='1.0',title=title,catalog_id=cid,catalog_grid=[3,5],catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes=design))
 bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(bid+'.blend')))
 preview(folder,(0,0,1.30),10.6,900,True)
 write(folder/'README.md',f'# {bid} — {title}\n\n{design}\n\nЧетыре новые самостоятельные детали MA-FF01-P01…P04; два готовых источника машинного отделения v2.0 используются без изменений и масштаба: MA-FG01-R2-P02 один раз и MA-FG01-R2-P03 два раза. Всего 7 экземпляров. Исходник MA-FF01.blend, состав assembly.json, анализ состава composition-plan.md.\n\nПредпросмотры Previews/top.png, perspective.png, top-grayscale.png. Каждая новая деталь проверена до сборки. Независимое повторное открытие всех исходников и сборки, геометрия, нормали, материалы, версии, полные позы и семантика sockets — validation.json.\n\nЭто визуальная заготовка каталога без игрового XML; ресурсы, рецепт, производительность не определены. Нет утверждения о конкретном химическом процессе. Условные BU, сетка 3×5 не метры. Статика; процедурные PBR, файловых текстур и зависимости от UV нет. Перекрытия коллекторов, уплотнений, обойм и опор являются намеренными посадками; открытые промежутки сохраняются. GLB не создавался, интеграция в игру не выполнялась.\n')
else:
 a=json.loads((folder/'assembly.json').read_text());parts={};checks=[]
 for pid in sorted(set(i['part_id'] for i in a['instances'])):
  p=ROOT/'Parts'/pid;d=json.loads((p/'part.json').read_text());parts[pid]=d;bpy.ops.wm.open_mainfile(filepath=str(p/d['source']));gate=inspect()
  for m in d['mounts']:
   o=bpy.data.objects.get('socket.'+m['id']);assert o and (o.location-Vector(m['position'])).length<1e-6
  if pid.startswith(bid):assert json.loads((p/'geometry-validation.json').read_text())['validated_before_assembly']
  checks.append(dict(id=pid,version=d['version'],geometry=gate))
 bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')));gate=inspect();instances={i['id']:i for i in a['instances']};results=[]
 for i in a['instances']:
  o=bpy.data.objects.get(i['id']);assert o and o['part_id']==i['part_id'] and o['part_version']==i['version']==parts[i['part_id']]['version'];assert o.parent.name==i['parent'];assert (o.location-Vector(i['translation'])).length<1e-6;assert all(abs(v-1)<1e-6 for v in o.scale);assert (folder/i['source']).resolve().exists()
 for c in a['connections']:
  pi=instances[c['parent_instance']];ci=instances[c['child_instance']];pm=next(m for m in parts[pi['part_id']]['mounts'] if m['id']==c['parent_socket']);cm=next(m for m in parts[ci['part_id']]['mounts'] if m['id']==c['child_socket']);po=bpy.data.objects[pi['id']];co=bpy.data.objects[ci['id']]
  pos=(po.matrix_world@Vector(pm['position'])-co.matrix_world@Vector(cm['position'])).length
  fwd=(po.matrix_world.to_3x3()@Vector(pm['forward'])-co.matrix_world.to_3x3()@Vector(cm['forward'])).length;up=(po.matrix_world.to_3x3()@Vector(pm['up'])-co.matrix_world.to_3x3()@Vector(cm['up'])).length;compat=bool(set(pm['compatibility'])&set(cm['compatibility']));assert max(pos,fwd,up)<1e-6 and compat
  results.append(dict(**c,position_error=pos,forward_error=fwd,up_error=up,semantic_compatibility=compat))
 write(folder/'validation.json',dict(id=bid,checks_passed=True,independent_reopen=True,source_parts=checks,assembly_geometry=gate,connections=results,instance_count=len(a['instances']),new_part_count=4,reused_source_count=2,unit_scale=True,dependency_paths_resolved=True,no_glb_generated=True,game_validation=False))
 print('VERIFIED',bid,flush=True)
