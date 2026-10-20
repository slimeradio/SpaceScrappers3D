"""Cargo source authoring; individual evaluated geometry gates; no GLB."""
import sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-F02'; FOLDER=ROOT/'Blocks'/BID

def mount(i,p,tag):
 return {'id':i,'role':tag.split('.')[-1],'parent':'part','position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':[tag],'allowed_scale':[1,1,1]}

def inspect():
 checks=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  c={'mesh':o.name,'source_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'source_zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'source_inconsistent_normals':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'signed_volume':bm.calc_volume(signed=True)};bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();c.update(evaluated_triangles=len(me.loop_triangles),zero_area_triangles=sum(t.area<1e-10 for t in me.loop_triangles),finite=all(math.isfinite(v) for p in me.vertices for v in p.co),materials_resolved=bool(o.material_slots) and all(s.material for s in o.material_slots));ev.to_mesh_clear()
  c['pass']=not c['source_nonmanifold_edges'] and not c['source_zero_area_faces'] and not c['source_inconsistent_normals'] and c['signed_volume']>0 and not c['zero_area_triangles'] and c['finite'] and c['materials_resolved'];checks.append(c)
 result={'checks_passed':bool(checks) and all(c['pass'] for c in checks),'meshes':checks,'validated_before_assembly':True}
 assert result['checks_passed'],str(result)
 return result

def preview(folder,target,scale,res=650):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=res;scene.render.resolution_y=res;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('MA-F02 review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
 added=[];target=Vector(target)
 for loc,power,size in [((2,-5,8),1500,5),((-4,-1,5),1100,4),((3,5,6),1800,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 (folder/'Previews').mkdir(parents=True,exist_ok=True)
 for name,off in [('top',(0,0,8)),('perspective',(5,-7,6))]:
  cam.location=target+Vector(off);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/'Previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def finish(m,mounts):
 check=inspect();m.save(mounts=mounts,notes='Static base production enclosure; uniform procedural PBR. No file textures, UV dependency or animated mechanism. BU are not metres.')
 p=ROOT/'Parts'/m.pid;d=json.loads((p/'part.json').read_text())
 d['attachment_areas']=[{'id':s['id']+'-seat','parent':'part','role':s['role'],'shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts]
 write(p/'part.json',d);write(p/'geometry-validation.json',check)
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65,450)
 write(p/'README.md',f'# {m.pid} v1.0\n\n{m.title}. Редактируемый исходник {m.pid}.blend; part.json содержит материалы, эмиссию и полные логические крепления. Все масштабы единичные. Геометрия проверена до сборки: geometry-validation.json. Отдельные виды Previews/top.png и perspective.png. Статическая деталь, процедурный PBR, без файловых текстур и UV-зависимости. GLB не создавался.\n')

write(FOLDER/'composition-plan.md',"""# MA-F02 — производственный блок базы 2×1

Каталог refinery-base, 2×1: производственные мощности по заказам, Units=4. Число Units — игровой параметр, не число деталей геометрии. BU условные. Статика, без выдуманных механизмов и анимаций.

Проверка библиотеки до моделирования:

| Потребность | Источник v1.0 | Решение |
|---|---|---|
| Двухместное шасси | MA-F01-P01, 3.82×1.72 BU | Повторно использовать без масштаба, посадки ±0.88 X |
| Производственная кассета слева | MA-F01-P02, 1.49×1.10×0.69 BU | Повторно использовать, штатная cassette-посадка |
| Низкий сервисный отсек справа | MA-F01-P02 | Новая MA-F02-P01: исходная высокая крыша не подходит ступенчатой сервисной зоне, деформация исходника недопустима |
| Стреловидные борта | MA-F01-P03 | Два готовых экземпляра на штатных shoulder-посадках |
| Межсекционный защищённый мост | MA-F01-P04 | Повторно использовать штатную bridge-посадку |
| Сервисные картриджи | MA-R01-P05 | Два готовых исправленных источника с service-cartridge.v1; дефектный MA-P06 не использовать |

Отличие от MA-F01: высокая производственная кассета слева, низкая ступенчатая сервисная палуба справа; картриджи разнесены по высоте. Новая деталь проверяется отдельно до сборки. Полные логические крепления, +Z вверх, -Y вперёд, единичный масштаб. Процедурные материалы. GLB не создавать.
""")
if '--assembly-only' not in sys.argv:
 m=Part('MA-F02-P01','Низкая сервисная кассета производственного блока базы')
 m.panel('Sealed lower service enclosure',(0,0,.17),(1.49,1.10,.34),'Armor',.19,.012)
 m.panel('Recessed stepped service gasket',(0,0,.345),(1.36,.98,.035),'Dark',.15,.004)
 for x in [-.55,.55]:
  m.panel('Swept ceramic service shoulder',(x,0,.395),(.30,1.02,.16),'Ceramic',.075,.006)
  m.panel('Dorsal titanium inset',(x,0,.48),(.13,.59,.018),'Titanium',.03,.002)
 m.panel('Protected central service platform',(0,0,.405),(.81,.71,.09),'Titanium',.1,.006)
 m.panel('Cartridge seal',(0,0,.453),(.75,.61,.006),'Dark',.09,.001)
 for y in [-.49,.49]:
  m.panel('Closed service end plate',(0,y,.24),(1.24,.13,.25),'Titanium',.04,.005)
  m.box('Recessed end index',(0,y+math.copysign(.068,y),.27),(.54,.008,.036),'Dark',.001)
  for x in [-.17,.17]:m.box('Limited service diagnosis',(x,y+math.copysign(.074,y),.27),(.064,.006,.012),'Signal',.001)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.production.cassette'),mount('service',(0,0,.46),'MilitaryArmor.service-cartridge.v1')])

# Assembly follows the immediate standalone geometry gate.
a=Assembly(BID,'refinery-base',[2,1],'Производственный блок базы 2×1')
a.instance('Chassis','MA-F01-P01')
a.instance('ProcessCassette','MA-F01-P02',loc=(-.88,0,.33))
a.instance('ServiceBay','MA-F02-P01',loc=(.88,0,.33))
a.instance('Service.Process','MA-R01-P05',loc=(-.88,0,1.02))
a.instance('Service.Base','MA-R01-P05',loc=(.88,0,.79))
a.instance('Shoulder.Front','MA-F01-P03',loc=(0,-.68,.24))
a.instance('Shoulder.Back','MA-F01-P03',loc=(0,.68,.24),rot=(0,0,math.pi))
a.instance('IntercellBridge','MA-F01-P04',loc=(0,0,.26))
connections=[]
for s,c in [('cassette-L','ProcessCassette'),('cassette-R','ServiceBay'),('shoulder-front','Shoulder.Front'),('shoulder-back','Shoulder.Back'),('bridge','IntercellBridge')]:connections.append({'parent_instance':'Chassis','parent_socket':s,'child_instance':c,'child_socket':'root'})
for p,c in [('ProcessCassette','Service.Process'),('ServiceBay','Service.Base')]:connections.append({'parent_instance':p,'parent_socket':'service','child_instance':c,'child_socket':'bottom'})
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Static asymmetric base production enclosure. Catalog Units=4 is not a mesh count. No invented gameplay mechanism, no GLB or integration.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.50),4.9,850)
write(FOLDER/'README.md',"""# MA-F02 — производственный блок базы

MilitaryArmor 1.3, refinery-base, 2×1. Закрытая высокая производственная кассета слева и низкая ступенчатая сервисная палуба справа; сервисные картриджи расположены на разной высоте. Светлые стреловидные борта, графитовый каркас, защищённый центральный мост. Новая компоновка сохраняет родство производственного семейства. Units=4 остаётся параметром каталога, не числом механизмов.

Исходник MA-F02.blend. План — composition-plan.md; экземпляры и соединения — assembly.json; независимая проверка — validation.json. Виды — Previews/top.png и Previews/perspective.png. Одна новая деталь MA-F02-P01 v1.0; пять готовых источников MA-F01-P01…P04 и MA-R01-P05. Восемь экземпляров. Прежние исходники не изменены.

Процедурный PBR Armor/Ceramic/Titanium/Dark/Signal; файловых текстур и UV-зависимости нет. Эмиссия диагностическая. Крепления логические с полной позой; масштабы единичные. Анимаций нет. Уплотнения и посадки намеренно контактируют. Новая деталь проверена до сборки: source manifold, согласованные нормали, положительный объём, finite, ноль вырожденных evaluated-треугольников, материалы.

BU условные, физический масштаб не согласован. Метаданные — авторинг Blender. GLB не создавался; игровая интеграция, коллайдеры и LOD не выполнялись.
""")
print('MA_F02_BUILT',flush=True)