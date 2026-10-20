import sys,math,json,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
helper=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py')
node=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in ['mount','inspect','preview']],type_ignores=[]),str(helper),'exec'))
BID='MA-I04'; folder=ROOT/'Blocks'/BID

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
 write(pf/'README.md',f'# {p.pid} v1.0\n\nЦельный широкий корпус с двумя полосами по три люка, центральным силовым хребтом и диагональными контрфорсами. Редактируемый Blender. Процедурные PBR, без файловых текстур/UV и эмиссии. Статика; BU условные. Полные sockets и области в part.json; единичный масштаб. Геометрия немедленно проверена до сборки. Top/perspective PNG; GLB нет.\n')


HATCHES=[(side+str(j),x,y) for side,x in [('L',-1.68),('R',1.68)] for j,y in enumerate([-2.05,0,2.05])]
if '--verify' not in sys.argv:
 write(folder/'composition-plan.md','# MA-I04 — план до моделирования\n\nКаталог cargo-4x4: грузовой контейнер 4×4, visual-only без XML. Вместимость и механизмы не определены. Семейство MA-I01 v2, MA-I02, MA-I03: единый грузовой объём и крупные люки. Две полосы по три люка, цельная широкая крыша, центральный силовой хребет и диагональные боковые контрфорсы.\n\nПовторное использование: MA-I01-R2-P02 v2.0 — 6 готовых люков 2.87×1.29 BU, unit scale; MA-I01-R2-P03 v2.0 — две торцевые направляющие 3.87 BU, unit scale. Материалы и неподвижные sockets совместимы. Корпуса MA-I01-R2-P01 / MA-I02-P01 / MA-I03-P01 не подходят по ширине и схеме посадок: новый MA-I04-P01 7.18×7.08 BU. Новый корпус, не растянутый прежний меш. Грузовые крышки не превращать в отдельные батарейные кассеты. Зазоры люков X=0.49, Y=0.76 BU.\n\nПравая система, +Z вверх, -Y вперёд. BU условные; сетка не метры. Сначала standalone geometry gate, затем сборка экземплярами. Статика; GLB запрещён.\n')
 if '--assembly-only' not in sys.argv:
  p=Part('MA-I04-P01','Цельный широкий контейнер с двумя зонами загрузки')
  p.panel('Continuous chamfered cargo hull',(0,0,.98),(7.18,7.08,1.96),'Armor',.55,.020)
  p.panel('Continuous armored roof',(0,0,2.035),(6.84,6.72,.15),'Titanium',.38,.012)
  for x in [-1.68,1.68]:
   for y in [-2.05,0,2.05]:p.panel('Wide loading aperture seal',(x,y,2.15),(3.03,1.45,.08),'Dark',.18,.008)
  p.panel('Central cargo roof backbone',(0,0,2.18),(.26,6.45,.15),'Steel',.08,.009)
  for y in [-1.025,1.025]:p.panel('Roof cross brace',(0,y,2.15),(6.65,.22,.16),'Titanium',.055,.009)
  for side in [-1,1]:
   p.panel('Low roof edge',(side*3.29,0,2.10),(.32,6.25,.18),'Ceramic',.09,.010)
   for y in [-2.78,-1.39,0,1.39,2.78]:
    o=p.box('Diagonal full-height load buttress',(side*3.48,y,1.03),(.23,.30,2.08),'Titanium',.010);o.rotation_euler.y=side*.13
    p.panel('Buttress roof cap',(side*3.43,y,2.20),(.48,.40,.18),'Ceramic',.09,.009)
   p.box('Long recessed handling channel',(side*3.595,0,.84),(.03,5.98,.24),'Dark',.004)
  for y in [-3.37,3.37]:
   p.panel('Broad end reinforced sill',(0,y,.22),(6.84,.35,.36),'Titanium',.11,.012)
   p.box('Deep end handling recess',(0,y*1.056,1.02),(5.85,.035,.32),'Dark',.005)
   for x in [-2.73,2.73]:p.panel('End vertical protector',(x,y,1.08),(.33,.35,1.74),'Ceramic',.10,.010)
  sockets=[mount('root',(0,0,0),'MilitaryArmor.cargo.hull')]
  for k,x,y in HATCHES:sockets.append(mount('hatch'+k,(x,y,2.19),'MilitaryArmor.cargo.wide-hatch'))
  for k,y in [('F',-3.56),('B',3.56)]:sockets.append(mount('rail'+k,(0,y,.16),'MilitaryArmor.cargo.rail'))
  finish(p,sockets)
 a=Assembly(BID,'cargo-4x4',[4,4],'Грузовой контейнер 4×4');a.instance('Structure','MA-I04-P01');connections=[]
 for k,x,y in HATCHES:
  iid='LoadingHatch'+k;a.instance(iid,'MA-I01-R2-P02',loc=(x,y,2.19));connections.append(dict(parent_instance='Structure',parent_socket='hatch'+k,child_instance=iid,child_socket='root'))
 for k,y in [('F',-3.56),('B',3.56)]:
  iid='CargoRail'+k;a.instance(iid,'MA-I01-R2-P03',loc=(0,y,.16));connections.append(dict(parent_instance='Structure',parent_socket='rail'+k,child_instance=iid,child_socket='root'))
 bpy.context.view_layer.update();inspect()
 write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title='Грузовой контейнер 4×4',catalog_id='cargo-4x4',catalog_grid=[4,4],catalog_status='visual-only; no game XML',axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Continuous wide cargo volume, twin loading lanes with six access hatches, central spine and diagonal buttresses. Static authoring concept; no capacity or mechanisms specified.'))
 bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
 preview(folder,(0,0,1.15),11.8,800,True)
 write(folder/'README.md','# MA-I04 — грузовой контейнер 4×4\n\nЦельный широкий контейнер: две полосы по три крупных загрузочных люка, центральный силовой хребет, торцевые усиления и диагональные контрфорсы. Компоновка сохраняет грузовое семейство и отличается от открытой гребёнки батареи.\n\n9 экземпляров, 3 источника: новый MA-I04-P01 v1.0; 6 люков MA-I01-R2-P02 v2.0 и 2 направляющие MA-I01-R2-P03 v2.0 повторно использованы без изменений и масштаба.\n\nРедактируемый MA-I04.blend; assembly.json, composition-plan.md, validation.json. Previews/top.png, perspective.png, top-grayscale.png. Процедурные PBR без файловых текстур/UV; эмиссия только в индексах готовых люков. Статическая visual-only модель без XML, вместимости, анимаций и игрового экспорта. GLB не создавался; BU не метры.\n')

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
 write(folder/'validation.json',dict(id=BID,checks_passed=True,independent_reopen=True,source_parts=checks,assembly_geometry=gate,connections=results,instance_count=len(a['instances']),unit_scale=True,dependency_paths_resolved=True,hatch_gap_x_BU=.49,hatch_gap_y_BU=.76,gasket_gap_x_BU=.33,gasket_gap_y_BU=.60,side_cap_to_hatch_clearance_BU=.075,roof_backbone_to_crossbrace_top_difference_BU=.025,no_glb_generated=True,game_validation=False))
 print('VERIFIED',BID,flush=True)
