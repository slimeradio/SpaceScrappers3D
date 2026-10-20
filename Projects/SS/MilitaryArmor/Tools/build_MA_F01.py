import sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-F01'; FOLDER=ROOT/'Blocks'/BID

def mount(i,p,role='production-interface',forward=(0,-1,0)):
 return {'id':i,'role':role,'parent':'part','position':list(p),'forward':list(forward),'up':[0,0,1],'compatibility':['MilitaryArmor.production.'+role]+(['MilitaryArmor.service-cartridge.v1'] if role=='accessory' else []),'allowed_scale':[1,1,1]}

def check_geometry(pid):
 checks=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  bad_edges=sum(not e.is_manifold for e in bm.edges);bad_faces=sum(f.calc_area()<1e-10 for f in bm.faces);volume=bm.calc_volume(signed=True)
  checks.append({'mesh':o.name,'vertices':len(bm.verts),'faces':len(bm.faces),'nonmanifold_edges':bad_edges,'zero_area_faces':bad_faces,'signed_volume':volume,'materials_valid':len(o.data.materials)>0 and all(m is not None for m in o.data.materials),'pass':not bad_edges and not bad_faces and volume>0})
  bm.free()
 result={'id':pid,'stage':'immediate part geometry validation before assembly','checks':checks,'checks_passed':bool(checks) and all(c['pass'] and c['materials_valid'] for c in checks)}
 write(ROOT/'Parts'/pid/'geometry-validation.json',result)
 assert result['checks_passed'],str(result)

def preview(folder,center,scale):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('MA-F01 review world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
 target=Vector(center);added=[]
 for loc,power,size in [((1,-4,7),1500,5),((-4,-1,4),1100,4),((3,5,5),1800,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=scale;scene.camera=camera;added.append(camera)
 folder=folder/'Previews';folder.mkdir(parents=True,exist_ok=True)
 for name,offset in [('perspective',(5,-7,6)),('top',(0,0,8))]:
  camera.location=target+Vector(offset);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def save_part(m,mounts):
 # The geometry gate executes before saving/review and any dependent block assembly.
 check_geometry(m.pid)
 m.save(mounts=mounts,notes='Static production enclosure; authoring BU only. Procedural uniform PBR, no UV or file texture dependency. No invented gameplay ports or animations.')
 p=ROOT/'Parts'/m.pid/'part.json';data=json.loads(p.read_text());data['attachment_areas']=[{'id':'root-plane','role':mounts[0]['role'],'parent':m.pid,'shape':'plane','size':[.1,.1],'position':mounts[0]['position'],'forward':mounts[0]['forward'],'up':[0,0,1],'restrictions':'Full socket pose alignment; unit scale; no arbitrary rotation','compatibility':mounts[0]['compatibility']}];write(p,data)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];center=[(a+b)/2 for a,b in zip(lo,hi)];scale=max(hi[i]-lo[i] for i in range(3))*1.65
 preview(ROOT/'Parts'/m.pid,center,scale)

write(FOLDER/'composition-plan.md','''# MA-F01 — производственный блок 2×1

Каталог refinery-2x1: производственные мощности и переработка предметов. Это закрытая производственная кассета, без выдуманной плавильной камеры или игровых функций. Размер сетки 2×1; BU условные, не метры.

Проверка библиотеки до моделирования: MA-P06 v1.3 подходит по габаритам (0.74×0.60×0.08 BU), материалам и accessory-креплению: первоначально выбран для повторного использования в единичном масштабе. Независимая проверка выявила вырожденные треугольники его фасок, поэтому итоговая сборка использует совместимый общий вариант MA-R01-P05 v1.0 с исправленными фасками; исходник MA-P06 не изменён. MA-P07 — оптический лидар, производственному назначению не нужен. MA-W01-P02 — кольцевой привод диаметром более 4 BU; не подходит для корпуса. Сопла и камеры MA-E01/MA-E02 не соответствуют закрытому производственному модулю. Бронеплиты MA-A01…MA-A04 не имеют объёма промышленного кожуха; их деформация потребовала бы несовместимого масштаба.

Новые детали: MA-F01-P01 — двухместное силовое шасси; MA-F01-P02 — герметичная производственная кассета (два экземпляра); MA-F01-P03 — стреловидный боковой кожух (два повёрнутых экземпляра); MA-F01-P04 — утопленный межсекционный силовой мост. Каждая деталь проходит отдельную геометрическую проверку до сборки, сохраняется в Blender с процедурными материалами и самостоятельными top/perspective превью.

Оси +Z вверх, -Y вперёд, правая система; все экземпляры имеют единичный масштаб. Крепления логические, без дополнительных болтов. Статика, без анимаций. Все исходники редактируемые; GLB не создаётся.
''')

m=Part('MA-F01-P01','Production two-cell structural chassis')
m.panel('Recessed hull gasket',(0,0,.055),(3.82,1.72,.11),'Dark',.22,.008)
m.panel('Graphite load deck',(0,0,.16),(3.74,1.66,.18),'Titanium',.25,.015)
for x in [-.88,.88]:m.panel('Cassette seating bed',(x,0,.28),(1.57,1.26,.10),'Armor',.20,.01)
for x in [-1.65,1.65]:
 m.panel('Flush end interface',(x,0,.26),(.28,.94,.10),'Titanium',.09,.006)
 m.box('Recessed power socket',(x,0,.316),(.15,.36,.012),'Dark',.004)
sockets=[mount('hull',(0,0,0),'hull'),mount('cassette-L',(-.88,0,.33),'cassette'),mount('cassette-R',(.88,0,.33),'cassette'),mount('shoulder-front',(0,-.68,.24),'shoulder'),mount('shoulder-back',(0,.68,.24),'shoulder',(0,1,0)),mount('bridge',(0,0,.26),'bridge')]
save_part(m,sockets)

m=Part('MA-F01-P02','Sealed process cassette')
m.panel('Lower pressure enclosure',(0,0,.19),(1.49,1.10,.38),'Armor',.19,.016)
m.section('Faceted process hood',[(-.53,0,.35,1.28,.32,.10),(-.34,0,.40,1.42,.48,.14),(.34,0,.40,1.42,.48,.14),(.53,0,.35,1.28,.32,.10)],'Ceramic',.012)
m.panel('Dorsal service gasket',(0,0,.65),(.91,.80,.035),'Dark',.13,.004)
m.panel('Dorsal service plate',(0,0,.675),(.85,.74,.025),'Titanium',.12,.004)
for side in [-1,1]:
 m.box('Enclosed diagnostic recess',(side*.716,0,.38),(.018,.48,.085),'Dark',.003)
 m.box('Limited diagnostic slit',(side*.728,-.04,.38),(.008,.23,.013),'Signal',.002)
for y in [-.414,.414]:m.box('Top panel seam',(0,y,.641),(.61,.012,.009),'Dark',.002)
save_part(m,[mount('root',(0,0,0),'cassette'),mount('service',(0,0,.69),'accessory')])

m=Part('MA-F01-P03','Swept production shoulder guard')
points=[(-1.85,-.02),(-1.59,-.20),(-.46,-.27),(0,-.20),(.46,-.27),(1.59,-.20),(1.85,-.02),(1.60,.15),(-1.60,.15)]
m.slab('Dark inset shoulder structure',points,0,.34,'Armor',.01)
for side in [-1,1]:
 pts=[(side*x,y) for x,y in [(.13,-.17),(1.53,-.14),(1.77,-.015),(1.50,.11),(.37,.11)]]
 m.slab('Swept ceramic shoulder',pts,.30,.13,'Ceramic',.01)
 m.stripe('Diagonal titanium brace',(side*.26,.105,.11),(side*1.54,.105,.32),.065,'Titanium')
 m.panel('Flush shoulder end cap',(side*1.60,-.03,.18),(.20,.20,.23),'Titanium',.06,.006)
save_part(m,[mount('root',(0,0,0),'shoulder')])

m=Part('MA-F01-P04','Intercell power spine')
m.panel('Recessed intercell base',(0,0,.12),(.29,1.30,.24),'Dark',.07,.008)
m.section('Protected bridge', [(-.61,0,.19,.28,.20,.065),(-.37,0,.41,.29,.36,.07),(.37,0,.41,.29,.36,.07),(.61,0,.19,.28,.20,.065)],'Titanium',.008)
m.panel('Intercell ceramic crown',(0,0,.605),(.25,.86,.055),'Ceramic',.06,.006)
for y in [-.22,0,.22]:m.panel('Recessed bridge diagnostic',(0,y,.638),(.12,.035,.008),'Signal',.012,.002)
save_part(m,[mount('root',(0,0,0),'bridge')])

# Dependent stage starts only after all four standalone geometry gates passed.
a=Assembly(BID,'refinery-2x1',[2,1],'Производственный блок')
a.instance('Chassis','MA-F01-P01')
for label,x in [('L',-.88),('R',.88)]:
 a.instance('Cassette.'+label,'MA-F01-P02',loc=(x,0,.33));a.instance('Service.'+label,'MA-R01-P05',loc=(x,0,1.02))
a.instance('Shoulder.Front','MA-F01-P03',loc=(0,-.68,.24));a.instance('Shoulder.Back','MA-F01-P03',loc=(0,.68,.24),rot=(0,0,math.pi));a.instance('IntercellBridge','MA-F01-P04',loc=(0,0,.26))
connections=[]
for src,dst,root in [('cassette-L','Cassette.L','root'),('cassette-R','Cassette.R','root'),('shoulder-front','Shoulder.Front','root'),('shoulder-back','Shoulder.Back','root'),('bridge','IntercellBridge','root')]:connections.append({'parent_instance':'Chassis','parent_socket':src,'child_instance':dst,'child_socket':root})
for s in ['L','R']:connections.append({'parent_instance':'Cassette.'+s,'parent_socket':'service','child_instance':'Service.'+s,'child_socket':'bottom'})
scene=bpy.context.scene;scene.frame_end=1;scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Editable Blender authoring asset. Static closed production module, no invented gameplay mechanism or game integration. No GLB generated.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.50),5.3)
write(FOLDER/'README.md','''# MA-F01 — производственный блок

Каталог refinery-2x1, 2×1. Закрытая двухсекционная производственная кассета MilitaryArmor 1.3: светлые гранёные крышки, стреловидные бронеплечи, графитовый каркас и защищённый центральный силовой мост. Бирюзовая эмиссия ограничена диагностическими пазами и сервисными индикаторами.

Исходник MA-F01.blend. Состав и логические соединения — assembly.json. План — composition-plan.md. Превью — Previews/top.png и Previews/perspective.png. Четыре новые самостоятельные детали MA-F01-P01…P04 и два экземпляра готового сервисного картриджа MA-R01-P05 v1.0; всего восемь экземпляров пяти деталей. Исходники деталей находятся в Parts/, собственные детали снабжены part.json, geometry-validation.json и двумя превью. Общий картридж имеет отдельный validation.json.

Материалы: процедурный PBR Armor/Ceramic/Titanium/Dark/Signal; без файловых текстур и UV-зависимости. Все масштабы единичные. Анимаций нет. BU условные, физический масштаб не согласован; 2×1 — размер сетки каталога. Метаданные относятся к авторингу Blender, не являются игровым контрактом. GLB не создавался; установка, коллайдеры, LOD и проверка в игре не входят в этот ассет.
''')
print('MA_F01_BUILT',flush=True)
