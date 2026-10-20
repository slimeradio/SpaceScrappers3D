import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector,Matrix
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-FG01';FOLDER=ROOT/'Blocks'/BID

def scan():
 checks=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles()
  c={'object':o.name,'nonmanifold_source_edges':bad,'signed_volume':volume,'evaluated_triangles':len(me.loop_triangles),'zero_area_triangles':sum(t.area<1e-11 for t in me.loop_triangles),'finite':all(math.isfinite(c) for v in me.vertices for c in v.co),'materials':bool(o.data.materials) and all(s.material for s in o.material_slots)}
  c['passed']=not bad and volume>0 and not c['zero_area_triangles'] and c['finite'] and bool(c['materials']);c['materials']=bool(c['materials']);checks.append(c);ev.to_mesh_clear()
 assert checks and all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
 return {'checks_passed':True,'checked_before_assembly':True,'objects':checks}

def mount(i,p,role):
 return {'id':i,'node':'socket.'+i,'parent':None,'role':role,'position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':['MilitaryArmor.service-cartridge.v1' if role=='accessory' else 'MilitaryArmor.fuel-production.'+role],'allowed_scale':[1,1,1]}

def preview(folder,center,scale):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Fuel production review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
 added=[];target=Vector(center)
 for loc,power,size in [((1,-4,7),1300,5),((-4,-1,4),1000,4),((3,5,5),1700,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 folder=folder/'Previews';folder.mkdir(parents=True,exist_ok=True)
 for name,offset in [('perspective',(5,-7,6)),('top',(0,0,8))]:
  cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def save(m,mounts):
 report=scan();write(ROOT/'Parts'/m.pid/'geometry-validation.json',report)
 m.save(mounts=mounts,notes='Static closed fuel-production installation component; no invented intake reagent or consumption mechanism. Procedural PBR; no file texture or UV dependencies.')
 pf=ROOT/'Parts'/m.pid;data=json.loads((pf/'part.json').read_text());r=mounts[0]
 data['attachment_areas']=[{'id':'root-plane','parent':None,'role':r['role'],'shape':'logical-plane','dimensions':[.08,.08],'position':r['position'],'forward':r['forward'],'up':r['up'],'compatibility':r['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]}];write(pf/'part.json',data)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65)

write(FOLDER/'composition-plan.md','''# MA-FG01 — план машинного отделения 3×3

Каталог engine-room, тип FuelGenerator: производство ресурса «Топливо» для двигателей. До 40 единиц/с по каталогу; входное потребление энергии/предметов не задано, реагенты и механику не выдумываем. Закрытая топливопроизводящая установка, не двигатель и не реактор. Размер 3×3 — клетки, не метры; BU условные.

Проверена библиотека MilitaryArmor: MA-R01-P05 v1.0 (0.74×0.60×0.08 BU) подходит как утопленный сервисный картридж, повторно используем без изменений. MA-B01-P03 (0.44×3.31×0.67) слишком короткое плечо при единичном масштабе; MA-F01-P02 (1.49×1.10×0.69) — короткая кассета и другие крепления; MA-B01-P01 (3.9×3.9×0.84) — батарейная платформа с иной посадкой. Бронеплиты не заменяют герметичные технологические корпуса; двигатель и реактор содержат неверные функциональные признаки. Масштаб этих деталей ограничен единичным. Наборы Kits не требуются.

Создать четыре новые детали: MA-FG01-P01 квадратное закрытое основание с пятью технологическими посадками; P02 удлинённая герметичная производственная камера (два экземпляра); P03 стреловидный бортовой защитный кожух (два экземпляра); P04 закрытый распределительный узел с двумя каналами (один экземпляр). Повторно использовать MA-R01-P05 на узле. Семь экземпляров, единичные масштабы, без движения. Полные socket position/forward/up и семантическая совместимость.

Каждую деталь отдельно сохранить, проверить manifold/positive volume/normals/finite/evaluated zero-area/materials и подготовить top/perspective до сборки. Исходники Blender, метаданные авторинга, без GLB.
''')

m=Part('MA-FG01-P01','Fuel production sealed square foundation')
m.panel('Pressure sealed foundation',(0,0,.065),(5.65,5.65,.13),'Dark',.40,.003)
m.panel('Structural graphite core',(0,0,.20),(5.50,5.50,.25),'Armor',.38,.004)
m.panel('Titanium process deck',(0,0,.335),(4.65,4.94,.10),'Titanium',.32,.003)
for x in [-1.10,1.10]:m.panel('Production chamber recessed seat',(x,.45,.394),(1.82,3.54,.018),'Dark',.20,.001)
m.panel('Distribution seat',(0,-1.95,.394),(3.87,.85,.018),'Dark',.16,.001)
sockets=[mount('hull',(0,0,0),'hull'),mount('chamber-left',(-1.10,.45,.40),'chamber'),mount('chamber-right',(1.10,.45,.40),'chamber'),mount('guard-left',(-2.40,0,.32),'guard'),mount('guard-right',(2.40,0,.32),'guard'),mount('distribution',(0,-1.95,.40),'distribution')]
save(m,sockets)

m=Part('MA-FG01-P02','Sealed elongated fuel production chamber')
m.panel('Closed chamber lower pressure body',(0,0,.34),(1.66,3.40,.68),'Armor',.28,.004)
m.section('Closed multi-facet process capsule',[(-1.62,0,.70,1.24,.60,.18),(-1.28,0,.82,1.68,.84,.20),(1.15,0,.82,1.68,.84,.20),(1.60,0,.69,1.24,.58,.16)],'Titanium',.003)
for y in [-1.00,0,1.00]:
 m.panel('Segmented ceramic pressure crown',(0,y,1.245),(1.42,.86,.14),'Ceramic',.18,.003)
 m.panel('Inset transverse seam',(0,y,1.319),(1.06,.032,.012),'Dark',.010,.001)
m.panel('Recessed chamber diagnostic',(0,-1.42,.99),(.38,.18,.024),'Dark',.04,.001)
m.panel('Small diagnostic index',(0,-1.42,1.006),(.16,.040,.008),'Signal',.008,.0005)
save(m,[mount('root',(0,0,0),'chamber')])

m=Part('MA-FG01-P03','Swept protective longitudinal process shoulder')
m.section('Closed diagonal shoulder frame',[(-2.50,0,.11,.30,.22,.06),(-1.52,0,.36,.56,.72,.14),(1.40,0,.36,.56,.72,.14),(2.48,0,.11,.28,.22,.06)],'Armor',.003)
m.section('Cold faceted swept shoulder armor',[(-2.39,0,.23,.32,.22,.05),(-1.45,0,.69,.58,.22,.07),(1.32,0,.69,.58,.22,.07),(2.36,0,.22,.30,.22,.05)],'Ceramic',.003)
for y in [-1.25,1.25]:
 m.stripe('Closed diagonal load path',(-.20,y-.40,.13),(.20,y+.40,.50),.09,'Titanium')
save(m,[mount('root',(0,0,0),'guard')])

m=Part('MA-FG01-P04','Closed protected fuel distribution node')
m.panel('Distribution pressure body',(0,0,.22),(3.72,.74,.44),'Titanium',.18,.003)
m.panel('Distribution ceramic armor',(0,0,.475),(3.48,.66,.10),'Ceramic',.16,.002)
for x in [-1.10,1.10]:
 m.panel('Recessed enclosed distribution channel',(x,0,.532),(.64,.37,.024),'Dark',.07,.001)
 m.panel('Protected channel cover',(x,0,.549),(.49,.24,.014),'Armor',.045,.001)
 m.panel('Minimal distribution index',(x,-.235,.535),(.13,.024,.010),'Signal',.006,.0005)
m.panel('Cartridge recessed landing',(0,0,.534),(.81,.65,.018),'Dark',.12,.001)
save(m,[mount('root',(0,0,0),'distribution'),mount('service',(0,0,.544),'accessory')])

# The assembly begins only after all four independent geometry gates and previews.
a=Assembly(BID,'engine-room',[3,3],'Машинное отделение')
a.instance('Foundation','MA-FG01-P01')
a.instance('Chamber.Left','MA-FG01-P02',loc=(-1.10,.45,.40))
a.instance('Chamber.Right','MA-FG01-P02',loc=(1.10,.45,.40))
a.instance('Guard.Left','MA-FG01-P03',loc=(-2.40,0,.32))
a.instance('Guard.Right','MA-FG01-P03',loc=(2.40,0,.32))
a.instance('Distribution','MA-FG01-P04',loc=(0,-1.95,.40))
a.instance('Service','MA-R01-P05',loc=(0,-1.95,.944))
connections=[{'parent_instance':'Foundation','parent_socket':s,'child_instance':i,'child_socket':'root'} for s,i in [('chamber-left','Chamber.Left'),('chamber-right','Chamber.Right'),('guard-left','Guard.Left'),('guard-right','Guard.Right'),('distribution','Distribution')]]+[{'parent_instance':'Distribution','parent_socket':'service','child_instance':'Service','child_socket':'bottom'}]
bpy.context.scene.frame_end=1;bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Closed fuel resource production unit. No invented intake reagent, energy consumption or engine mechanism. Seven static unit-scale instances, four new parts and reused corrected service cartridge.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')));preview(FOLDER,(0,0,.85),8.2)
write(FOLDER/'README.md','''# MA-FG01 — машинное отделение 3×3

Каталог engine-room, FuelGenerator: производит ресурс «Топливо» для двигателей корабля. В каталоге не задано входное потребление энергии/предметов; модель не добавляет реагенты или механику. Закрытая производственная установка с двумя удлинёнными технологическими камерами и передним распределительным узлом. Тяжёлая броня, стреловидные плечи, закрытые диагональные опоры, утопленный сервис. Без сопел, автомобильного мотора и реакторной геометрии.

MA-FG01.blend — редактируемая сборка, assembly.json — семь стабильных экземпляров и логические крепления, composition-plan.md — исходный план. Четыре новые детали MA-FG01-P01…P04 и повторно использованный MA-R01-P05 v1.0. Отдельные исходники, процедурные материалы и top/perspective каждой детали в Parts/. Предпросмотры сборки Previews/top.png и Previews/perspective.png.

До сборки каждая новая деталь проверена отдельно: manifold source edges, положительный ориентированный объём, finite coordinates, ненулевые evaluated triangles и материалы. Независимый verifier повторно открывает пять исходников и сборку; отчёт validation.json. Полные socket position/forward/up, единичный масштаб, статика без анимаций. Логические области крепления не являются физическими болтами.

Процедурные PBR Armor/Ceramic/Titanium/Dark/Signal; файловые текстуры и UV не нужны. Правая система, +Z вверх, -Y вперёд, BU условные. GLB не генерируется. Метаданные — контракт авторинга Blender. Игровой экспорт, установка, LOD, коллайдеры и физический масштаб не входят в результат.
''')
for n in range(1,5):
 pid=f'MA-FG01-P{n:02}'
 write(ROOT/'Parts'/pid/'README.md',f'# {pid}\n\nРедактируемый исходник {pid}.blend. Материалы, эмиссия, оси, ограничения масштаба, полные логические sockets и области — part.json. Отдельная немедленная проверка geometry-validation.json до сборки. Предпросмотры Previews/top.png и Previews/perspective.png. Процедурные PBR, без файловых текстур/UV, без анимаций. Статическая деталь MilitaryArmor 1.3, BU условные; GLB не создавался.\n')
print('MA_FG01_BUILT',flush=True)