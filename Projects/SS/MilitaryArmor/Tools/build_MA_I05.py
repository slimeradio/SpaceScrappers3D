import sys,math,json,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
helper=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py')
node=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in ['mount','inspect','preview']],type_ignores=[]),str(helper),'exec'))
BID='MA-I05'; folder=ROOT/'Blocks'/BID

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
 write(pf/'README.md',f'# {p.pid} v1.0\n\nЦельный широкий корпус с двумя полосами по четыре люка, приподнятым силовым хребтом и диагональными контрфорсами. Редактируемый Blender. Процедурные PBR, без файловых текстур/UV и эмиссии. Статика; BU условные. Полные sockets и области в part.json; единичный масштаб. Геометрия немедленно проверена до сборки. Top/perspective PNG; GLB нет.\n')


HATCHES=[(side+str(j),x,y) for side,x in [('L',-2.05),('R',2.05)] for j,y in enumerate([-3.075,-1.025,1.025,3.075])]
if '--verify' not in sys.argv:
 write(folder/'composition-plan.md','# MA-I05 — план до моделирования\n\nКаталог cargo-5x5: грузовой контейнер 5×5, visual-only без XML. Вместимость и механизмы не заданы. Семейство MA-I01 v2 / I02 / I03 / I04. Цельный корпус с двумя полосами по четыре загрузочных люка, широким приподнятым центральным силовым хребтом и диагональными боковыми контрфорсами. Узнаваемый грузовой объём, не батарейные кассеты.\n\nПовторно использовать MA-I01-R2-P02 v2.0 — 8 люков 2.87×1.29 BU; MA-I01-R2-P03 v2.0 — 4 направляющие 3.87 BU, по две на торец. Единичный масштаб; материалы, sockets и статика совместимы. Старые корпуса не подходят габаритами и посадками: создать MA-I05-P01 с корпусом 8.88×8.88 BU и новым силовым набором. Зазоры люков X=1.23, Y=0.76 BU.\n\n+Z вверх, -Y вперёд; BU условные, сетка не метры. Сначала отдельная деталь и geometry gate, затем сборка. Без анимаций/GLB/игровой интеграции.\n')
 if '--assembly-only' not in sys.argv:
  p=Part('MA-I05-P01','Цельный тяжёлый грузовой корпус с приподнятым хребтом')
  p.panel('Continuous heavy cargo hull',(0,0,1.18),(8.88,8.88,2.36),'Armor',.70,.022)
  p.panel('Continuous armored roof',(0,0,2.435),(8.54,8.50,.15),'Titanium',.50,.012)
  for k,x,y in HATCHES:p.panel('Wide loading aperture seal',(x,y,2.55),(3.03,1.45,.08),'Dark',.18,.008)
  p.panel('Raised central load distributing ridge',(0,0,2.69),(.78,8.16,.38),'Armor',.20,.015)
  p.panel('Continuous central protective crown',(0,0,2.90),(.90,7.80,.12),'Ceramic',.14,.010)
  for y in [-2.05,0,2.05]:
   for side in [-1,1]:p.panel('Roof transverse load tie',(side*2.11,y,2.56),(3.34,.22,.16),'Steel',.06,.009)
  for side in [-1,1]:
   p.panel('Cargo roof edge curb',(side*3.99,0,2.56),(.40,7.95,.22),'Ceramic',.11,.010)
   for y in [-3.55,-1.78,0,1.78,3.55]:
    o=p.box('Diagonal full height cargo buttress',(side*4.29,y,1.24),(.24,.38,2.50),'Titanium',.012);o.rotation_euler.y=side*.12
    p.panel('Buttress armored cap',(side*4.12,y,2.59),(.54,.50,.20),'Ceramic',.10,.010)
   p.box('Recessed long handling channel',(side*4.447,0,1.04),(.03,7.60,.27),'Dark',.005)
  for y in [-4.27,4.27]:
   p.panel('Heavy end sill',(0,y,.24),(8.58,.35,.40),'Titanium',.14,.012)
   p.box('Recessed end handling channel',(0,y*1.044,1.16),(7.40,.035,.35),'Dark',.005)
   for x in [-3.75,0,3.75]:p.panel('Vertical end load pillar',(x,y,1.38),(.42,.38,2.30),'Ceramic',.10,.012)
  sockets=[mount('root',(0,0,0),'MilitaryArmor.cargo.hull')]
  for k,x,y in HATCHES:sockets.append(mount('hatch'+k,(x,y,2.59),'MilitaryArmor.cargo.wide-hatch'))
  for side,x in [('L',-2.04),('R',2.04)]:
   for k,y in [('F',-4.46),('B',4.46)]:sockets.append(mount('rail'+side+k,(x,y,.18),'MilitaryArmor.cargo.rail'))
  finish(p,sockets)
 a=Assembly(BID,'cargo-5x5',[5,5],'Грузовой контейнер 5×5');a.instance('Structure','MA-I05-P01');connections=[]
 for k,x,y in HATCHES:
  iid='LoadingHatch'+k;a.instance(iid,'MA-I01-R2-P02',loc=(x,y,2.59));connections.append(dict(parent_instance='Structure',parent_socket='hatch'+k,child_instance=iid,child_socket='root'))
 for side,x in [('L',-2.04),('R',2.04)]:
  for k,y in [('F',-4.46),('B',4.46)]:
   iid='CargoRail'+side+k;a.instance(iid,'MA-I01-R2-P03',loc=(x,y,.18));connections.append(dict(parent_instance='Structure',parent_socket='rail'+side+k,child_instance=iid,child_socket='root'))
 bpy.context.view_layer.update();inspect()
 write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title='Грузовой контейнер 5×5',catalog_id='cargo-5x5',catalog_grid=[5,5],catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Continuous wide cargo volume, twin loading lanes with eight access hatches, raised central spine and diagonal buttresses. Static authoring concept; no capacity or mechanisms specified.'))
 bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
 preview(folder,(0,0,1.45),14.8,800,True)
 write(folder/'README.md','# MA-I05 — грузовой контейнер 5×5\n\nЦельный широкий контейнер: две полосы по четыре крупных загрузочных люка, приподнятый силовой хребет, торцевые усиления и диагональные контрфорсы. Компоновка сохраняет грузовое семейство и отличается от открытой гребёнки батареи.\n\n13 экземпляров, 3 источника: новый MA-I05-P01 v1.0; 8 люков MA-I01-R2-P02 v2.0 и 4 направляющие MA-I01-R2-P03 v2.0 повторно использованы без изменений и масштаба.\n\nРедактируемый MA-I05.blend; assembly.json, composition-plan.md, validation.json. Previews/top.png, perspective.png, top-grayscale.png. Процедурные PBR без файловых текстур/UV; эмиссия только в индексах готовых люков. Статическая visual-only модель без XML, вместимости, анимаций и игрового экспорта. GLB не создавался; BU не метры.\n')

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
 write(folder/'validation.json',dict(id=BID,checks_passed=True,independent_reopen=True,source_parts=checks,assembly_geometry=gate,connections=results,instance_count=len(a['instances']),unit_scale=True,dependency_paths_resolved=True,hatch_gap_x_BU=1.23,hatch_gap_y_BU=.76,gasket_gap_x_BU=1.07,gasket_gap_y_BU=.60,side_cap_to_hatch_clearance_BU=.365,roof_backbone_to_crossbrace_top_difference_BU=.32,no_glb_generated=True,game_validation=False))
 print('VERIFIED',BID,flush=True)
