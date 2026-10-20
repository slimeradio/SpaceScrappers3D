import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-C01'; FOLDER=ROOT/'Blocks'/BID

def mount(i,p,role,forward=(0,-1,0)):
 return {'id':i,'role':role,'parent':'part','position':list(p),'forward':list(forward),'up':[0,0,1],'compatibility':['MilitaryArmor.compute.'+role]+(['MilitaryArmor.service-cartridge.v1'] if role=='accessory' else []),'allowed_scale':[1,1,1]}

def geometry(pid):
 checks=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  c={'mesh':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True),'materials_valid':bool(o.data.materials) and all(m is not None for m in o.data.materials)};bm.free()
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();c['evaluated_zero_area_triangles']=sum(t.area<1e-10 for t in me.loop_triangles);c['finite']=all(math.isfinite(v) for p in me.vertices for v in p.co);ev.to_mesh_clear()
  c['pass']=not c['nonmanifold_edges'] and not c['zero_area_faces'] and not c['evaluated_zero_area_triangles'] and c['signed_volume']>0 and c['finite'] and c['materials_valid'];checks.append(c)
 result={'id':pid,'stage':'immediate standalone geometry gate before assembly','checks':checks,'checks_passed':bool(checks) and all(c['pass'] for c in checks)};write(ROOT/'Parts'/pid/'geometry-validation.json',result);assert result['checks_passed'],result

def preview(folder,center,scale):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=900;s.render.resolution_y=700;s.render.resolution_percentage=100
 world=bpy.data.worlds.new('Compute review world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;s.world=world
 t=Vector(center);added=[]
 for loc,power,size in [((1,-4,7),1500,5),((-4,-1,4),1100,4),((3,5,5),1800,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;s.camera=cam;added.append(cam)
 p=folder/'Previews';p.mkdir(parents=True,exist_ok=True)
 for name,offset in [('perspective',(5,-7,6)),('top',(0,0,8))]:
  cam.location=t+Vector(offset);cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(p/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 s.camera=None

def save(m,sockets):
 geometry(m.pid);m.save(mounts=sockets,notes='Static sealed compute enclosure. Blender authoring only, no invented gameplay connectors. Uniform procedural PBR; no UV or image textures. No animation.')
 path=ROOT/'Parts'/m.pid/'part.json';d=json.loads(path.read_text());d['attachment_areas']=[{'id':'root-plane','role':sockets[0]['role'],'parent':'part','shape':'logical-plane','dimensions':[.10,.10],'position':sockets[0]['position'],'forward':sockets[0]['forward'],'up':[0,0,1],'allowed_rotations_degrees':[0],'allowed_scale':[1,1,1],'compatibility':sockets[0]['compatibility']}];write(path,d)
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(ROOT/'Parts'/m.pid,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65)
 write(ROOT/'Parts'/m.pid/'README.md',f'# {m.pid} — {m.title}\n\nРедактируемый исходник {m.pid}.blend, метаданные part.json, немедленная геометрическая проверка geometry-validation.json. Отдельные виды Previews/top.png и Previews/perspective.png. Процедурные материалы: графит, титан, светлая керамика; бирюзовая диагностика только там, где перечислена в emission. Файловых текстур нет. Оси +Z вверх, -Y вперёд; BU условные, масштаб единичный, статика без анимаций. Крепления и области логические, полного совпадения поз. GLB не создавался.\n')

write(FOLDER/'composition-plan.md','''# MA-C01 — план программируемого блока 2×1

Каталог programmable-2x1: хранение и запуск клиентской Lua-программы через редактор; доступные действия ограничены API и серверными проверками. Модель обозначает защищённый вычислительный узел, не добавляет игровых функций. Сетка 2×1, BU не объявляются метрами.

До моделирования сравнены Parts выбранного стиля: MA-R01-P05 v1.0 — готовый низкий сервисный картридж 0.74×0.60×0.08 BU, PBR и общий тег MilitaryArmor.service-cartridge.v1, подходит в единичном масштабе, повторно использовать. Старый MA-P06 с дефектом фасок не использовать. MA-P07 — лидар, не соответствует вычислительному узлу. MA-F01-P01/P02 — промышленное шасси с двумя отдельными кассетами; для единого защищённого вычислительного объёма и иных посадочных креплений не подходят. Бронеплиты MA-A01…A04 плоские, не заменяют герметичный корпус. Приводы, кольца и сопла функционально не подходят. Kits не требуется.

Новые детали: MA-C01-P01 — компактное герметичное шасси, единый интерфейс кассеты и два интерфейса плеч; MA-C01-P02 — монолитный вычислительный сейф с тремя глухими секциями и узким защищённым диагностическим полем; MA-C01-P03 — стреловидное бронеплечо, два экземпляра с поворотом на 180°. MA-R01-P05 — готовая сервисная панель на сейфе. Все детали отдельно сохраняются и сразу проходят проверку до сборки: manifold source edges, положительный объём, конечные координаты, ненулевые evaluated triangles и материалы.

Статика без подвижных узлов; +Z вверх, -Y вперёд, правая система. Пять экземпляров четырёх деталей. Логические sockets проверяются по полной позе и совместимости. Исходники Blender, отдельные предпросмотры, GLB не генерируется.
''')

m=Part('MA-C01-P01','Sealed compute foundation')
m.panel('Pressure seal',(0,0,.05),(3.84,1.70,.10),'Dark',.23,.001)
m.panel('Titanium foundation',(0,0,.15),(3.72,1.62,.18),'Titanium',.22,.004)
m.panel('Compute cassette seat',(0,0,.27),(3.20,1.19,.12),'Armor',.18,.003)
for x in [-1.64,1.64]:
 m.panel('Shielded terminal cap',(x,0,.30),(.25,.82,.18),'Ceramic',.07,.002)
 m.panel('Recessed maintenance blank',(x,0,.397),(.13,.42,.014),'Dark',.035,.001)
save(m,[mount('hull',(0,0,0),'hull'),mount('vault',(0,0,.33),'vault'),mount('guard-front',(0,-.67,.23),'guard'),mount('guard-back',(0,.67,.23),'guard',(0,1,0))])

m=Part('MA-C01-P02','Armored compute vault')
m.panel('Sealed vault lower casing',(0,0,.16),(3.06,1.10,.32),'Armor',.17,.004)
m.section('Single protected vault',[(-.51,0,.32,2.86,.40,.12),(-.30,0,.40,3.10,.52,.15),(.30,0,.40,3.10,.52,.15),(.51,0,.32,2.86,.40,.12)],'Titanium',.003)
for x in [-.99,0,.99]:
 m.panel('Compute bank ceramic shield',(x,0,.69),(.88,.81,.14),'Ceramic',.12,.002)
 m.panel('Recessed shield seam',(x,.28,.765),(.62,.016,.012),'Dark',.004,.001)
# Narrow recessed diagnostics occupy only one end; no large external display.
m.panel('Diagnostic recess',(-1.14,-.18,.773),(.37,.24,.02),'Dark',.05,.001)
for x in [-1.25,-1.15,-1.05]:m.panel('Diagnostic cell',(x,-.18,.786),(.035,.12,.008),'Signal',.007,.0005)
m.panel('Service cartridge pressure seat',(.72,0,.776),(.82,.68,.02),'Dark',.12,.001)
save(m,[mount('root',(0,0,0),'vault'),mount('service',(.72,0,.787),'accessory')])

m=Part('MA-C01-P03','Swept compute shoulder')
pts=[(-1.86,.03),(-1.57,-.20),(-.63,-.26),(.12,-.17),(1.50,-.16),(1.83,.03),(1.56,.15),(-1.57,.15)]
m.slab('Shoulder structural backing',pts,0,.25,'Armor',.002)
for side in [-1,1]:
 pts=[(side*x,y) for x,y in [(.14,-.12),(.64,-.21),(1.49,-.15),(1.69,.02),(1.45,.11),(.36,.11)]]
 m.slab('Swept ceramic armor',pts,.24,.15,'Ceramic',.002)
 m.stripe('Diagonal enclosed support',(side*.35,.12,.07),(side*1.49,.12,.29),.06,'Titanium')
save(m,[mount('root',(0,0,0),'guard')])

# Only saved and individually checked parts are introduced below.
a=Assembly(BID,'programmable-2x1',[2,1],'Программируемый блок')
a.instance('Foundation','MA-C01-P01');a.instance('ComputeVault','MA-C01-P02',loc=(0,0,.33));a.instance('Guard.Front','MA-C01-P03',loc=(0,-.67,.23));a.instance('Guard.Back','MA-C01-P03',loc=(0,.67,.23),rot=(0,0,math.pi));a.instance('Service','MA-R01-P05',loc=(.72,0,1.117))
connections=[{'parent_instance':'Foundation','parent_socket':s,'child_instance':i,'child_socket':'root'} for s,i in [('vault','ComputeVault'),('guard-front','Guard.Front'),('guard-back','Guard.Back')]]+[{'parent_instance':'ComputeVault','parent_socket':'service','child_instance':'Service','child_socket':'bottom'}]
s=bpy.context.scene;s.frame_end=1;s.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Editable static programmable block authoring asset. No invented gameplay functions. GLB not generated.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')));preview(FOLDER,(0,0,.55),5.2)
write(FOLDER/'README.md','''# MA-C01 — программируемый блок 2×1

Каталог programmable-2x1. Защищённый вычислительный сейф MilitaryArmor 1.3: единый низкий корпус, три закрытые секции вычислительной кассеты, светлые стреловидные плечи и узкая утопленная бирюзовая диагностика. Без открытых плат, вентиляторов и выдуманных механизмов.

Редактируемый исходник MA-C01.blend. Состав/крепления — assembly.json, план — composition-plan.md, проверка — validation.json. Превью — Previews/top.png и Previews/perspective.png. Три новые детали MA-C01-P01…P03 и повторно использованный MA-R01-P05 v1.0, пять стабильных экземпляров. Каждая новая деталь имеет отдельный Blender-исходник, материалы, метаданные, геометрическую проверку и две самостоятельные иллюстрации.

Процедурные PBR Armor/Ceramic/Titanium/Dark/Signal, без внешних текстур и UV-зависимости. +Z вверх, -Y вперёд, правая система; BU условные. Все масштабы единичные, анимаций нет. Метаданные — контракт авторинга Blender. GLB не создавался; игра, коллайдеры, LOD и физический масштаб не проверялись.
''')
print('MA_C01_BUILT',flush=True)