import sys,math,json,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
helper=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py')
node=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in ['mount','inspect','preview']],type_ignores=[]),str(helper),'exec'))
BID='MA-I03'; folder=ROOT/'Blocks'/BID

def finish(p,sockets):
 bpy.context.view_layer.update();gate=inspect()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
 p.save(mounts=sockets,notes='Static cargo family, procedural PBR; no UV/file textures. No emission in hull. No gameplay mechanism. BU unspecified physical scale.')
 pf=ROOT/'Parts'/p.pid;d=json.loads((pf/'part.json').read_text())
 d['attachment_areas']=[dict(id=m['id']+'-area',role=m['role'],shape='logical-point-plane',dimensions=[.01,.01],parent='part',position=m['position'],forward=m['forward'],up=m['up'],compatibility=m['compatibility'],restrictions='unit scale; exact full pose') for m in sockets]
 write(pf/'part.json',d);write(pf/'geometry-validation.json',dict(**gate,source_normals_consistent=True,validated_before_assembly=True))
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.55,450)
 write(pf/'README.md',f'# {p.pid} v1.0\n\nШирокий ступенчатый корпус контейнера с боковыми силовыми контрфорсами, тремя посадками грузовых люков и двумя посадками направляющих. Редактируемый Blender. Процедурные PBR, без файловых текстур/UV и эмиссии. Статика; BU условные. Полные sockets и области в part.json; единичный масштаб. Геометрия немедленно проверена до сборки. Top/perspective PNG; GLB нет.\n')

if '--verify' not in sys.argv:
 write(folder/'composition-plan.md','# MA-I03 — план состава до моделирования\n\nКаталог cargo-3x3, грузовой контейнер 3×3; визуальная заготовка без игрового XML. Вместимость и механизмы не заданы. Семья цельных контейнеров MA-I01 v2 / MA-I02: широкие загрузочные люки, грузовые направляющие и силовые рёбра. Новый вариант отличается широким ступенчатым объёмом, тремя загрузочными секциями вдоль центральной полосы и парными диагональными контрфорсами по бортам. Это не масштабированная копия 2×2.\n\nПовторно использовать MA-I01-R2-P02 v2.0: 3 готовых люка 2.87×1.29 BU без масштаба; расстояние между люками 0.36 BU, уплотнения и силовые разделители разнесены. Повторно использовать MA-I01-R2-P03 v2.0: две направляющие длиной 3.87 BU у торцов без масштаба. Корпуса MA-I01-R2-P01 и MA-I02-P01 не подходят размером и посадками: создать один MA-I03-P01, новый корпус 5.48×5.38 BU. Батарейные детали и сервисный восьмигранник не использовать.\n\nКоординаты: правая система, +Z вверх, -Y вперёд; BU не метры, размер сетки не физический масштаб. Сначала standalone source и геометрический gate, затем экземпляры сохранённых источников. Статический source-only Blender; GLB не создавать.\n')
 if '--assembly-only' not in sys.argv:
  p=Part('MA-I03-P01','Широкий грузовой корпус с диагональными силовыми рёбрами')
  p.panel('Continuous broad cargo volume',(0,0,.81),(5.48,5.38,1.62),'Armor',.35,.018)
  # Raised central access strip bounded by lower side shoulders.
  p.panel('Central loading spine',(0,0,1.68),(3.26,5.02,.20),'Titanium',.20,.010)
  for y in [-1.65,0,1.65]:p.panel('Individual loading aperture gasket',(0,y,1.80),(3.03,1.45,.08),'Dark',.18,.008)
  for y in [-.825,.825]:p.box('Roof crossmember between access hatches',(0,y,1.79),(3.15,.12,.16),'Steel',.008)
  for s in [-1,1]:
   # Wide load distributing shoulders and angled buttresses give 3x3 its own structure.
   p.panel('Broad lowered cargo shoulder',(s*2.10,0,1.58),(.94,4.67,.18),'Ceramic',.16,.010)
   for y in [-1.83,-.61,.61,1.83]:
    o=p.box('Diagonal side load buttress',(s*2.55,y,.88),(.20,.29,1.75),'Titanium',.008);o.rotation_euler.y=s*.19
    p.panel('Roof buttress cap',(s*2.39,y,1.725),(.49,.33,.16),'Steel',.065,.009)
   p.box('Long recessed side handling channel',(s*2.744,0,.78),(.035,4.30,.23),'Dark',.004)
  for y in [-2.54,2.54]:p.panel('Wide cargo access sill',(0,y,.20),(5.30,.27,.28),'Titanium',.08,.010)
  sockets=[mount('root',(0,0,0),'MilitaryArmor.cargo.hull')]
  for k,y in [('F',-1.65),('M',0),('B',1.65)]:sockets.append(mount('hatch'+k,(0,y,1.84),'MilitaryArmor.cargo.wide-hatch'))
  for k,y in [('F',-2.67),('B',2.67)]:sockets.append(mount('rail'+k,(0,y,.16),'MilitaryArmor.cargo.rail'))
  finish(p,sockets)
 a=Assembly(BID,'cargo-3x3',[3,3],'Грузовой контейнер 3×3');a.instance('Structure','MA-I03-P01');connections=[]
 for k,y in [('F',-1.65),('M',0),('B',1.65)]:
  iid='LoadingHatch'+k;a.instance(iid,'MA-I01-R2-P02',loc=(0,y,1.84));connections.append(dict(parent_instance='Structure',parent_socket='hatch'+k,child_instance=iid,child_socket='root'))
 for k,y in [('F',-2.67),('B',2.67)]:
  iid='CargoRail'+k;a.instance(iid,'MA-I01-R2-P03',loc=(0,y,.16));connections.append(dict(parent_instance='Structure',parent_socket='rail'+k,child_instance=iid,child_socket='root'))
 bpy.context.view_layer.update();inspect()
 write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title='Грузовой контейнер 3×3',catalog_id='cargo-3x3',catalog_grid=[3,3],catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Broad stepped cargo volume, central triple loading access and diagonal side buttresses. Static authoring concept; no capacity or mechanisms specified.'))
 bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
 preview(folder,(0,0,1.0),8.5,800,True)
 write(folder/'README.md','# MA-I03 — грузовой контейнер 3×3\n\nШирокий цельный грузовой объём со ступенчатой крышей, центральной полосой из трёх загрузочных люков, боковыми диагональными контрфорсами и наружными направляющими. Семейство MA-I01/MA-I02, без батарейных кассет и универсальной сервисной крышки.\n\n6 экземпляров, 3 уникальных источника: новый MA-I03-P01 v1.0 и повторно используемые MA-I01-R2-P02/P03 v2.0 без изменений/масштаба. composition-plan.md; MA-I03.blend; assembly.json; validation.json. Previews: top.png, perspective.png, top-grayscale.png.\n\nСтатическая визуальная заготовка каталога cargo-3x3 без игрового XML; вместимость и механика не заданы. Условные BU, сетка не метры. Процедурные PBR, без файловых текстур/UV; ограниченная эмиссия только в готовых индексах люков. GLB нет, игровой интеграции нет.\n')
else:
 a=json.loads((folder/'assembly.json').read_text());parts={};checks=[]
 for pid in sorted(set(i['part_id'] for i in a['instances'])):
  pf=ROOT/'Parts'/pid;d=json.loads((pf/'part.json').read_text());parts[pid]=d;bpy.ops.wm.open_mainfile(filepath=str(pf/d['source']));gate=inspect()
  for o in bpy.context.scene.objects:
   if o.type!='MESH':continue
   bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges);bm.free()
   ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert all(math.isfinite(v) for vert in me.vertices for v in vert.co);ev.to_mesh_clear()
  for m in d['mounts']:
   o=bpy.data.objects.get('socket.'+m['id']);assert o and (o.location-Vector(m['position'])).length<1e-6
  checks.append(dict(id=pid,version=d['version'],geometry=gate,source_normals_consistent=True,evaluated_finite=True))
 bpy.ops.wm.open_mainfile(filepath=str(folder/(BID+'.blend')));gate=inspect();instances={i['id']:i for i in a['instances']};results=[]
 for i in a['instances']:
  o=bpy.data.objects.get(i['id']);assert o and o['part_id']==i['part_id'] and o['part_version']==i['version']==parts[i['part_id']]['version'];assert o.parent.name==i['parent'];assert (o.location-Vector(i['translation'])).length<1e-6;assert (Vector(o.rotation_euler)-Vector(i['rotation_euler_xyz'])).length<1e-6;assert all(abs(v-1)<1e-6 for v in o.scale);assert (folder/i['source']).resolve().exists()
 for c in a['connections']:
  pi=instances[c['parent_instance']];ci=instances[c['child_instance']];pm=next(m for m in parts[pi['part_id']]['mounts'] if m['id']==c['parent_socket']);cm=next(m for m in parts[ci['part_id']]['mounts'] if m['id']==c['child_socket']);po=bpy.data.objects[pi['id']];co=bpy.data.objects[ci['id']]
  pos=(po.matrix_world@Vector(pm['position'])-co.matrix_world@Vector(cm['position'])).length;fw=(po.matrix_world.to_3x3()@Vector(pm['forward'])-co.matrix_world.to_3x3()@Vector(cm['forward'])).length;up=(po.matrix_world.to_3x3()@Vector(pm['up'])-co.matrix_world.to_3x3()@Vector(cm['up'])).length;compat=bool(set(pm['compatibility'])&set(cm['compatibility']));assert max(pos,fw,up)<1e-6 and compat
  results.append(dict(**c,position_error=pos,forward_error=fw,up_error=up,semantic_compatibility=compat))
 write(folder/'validation.json',dict(id=BID,checks_passed=True,independent_reopen=True,source_parts=checks,assembly_geometry=gate,connections=results,instance_count=len(a['instances']),unit_scale=True,dependency_paths_resolved=True,hatch_gap_BU=.36,gasket_gap_BU=.20,no_glb_generated=True,game_validation=False))
 print('VERIFIED',BID,flush=True)
