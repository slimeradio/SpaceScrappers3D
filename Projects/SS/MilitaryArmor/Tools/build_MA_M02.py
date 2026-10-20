import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-M02';FOLDER=ROOT/'Blocks'/BID

def scan():
 checks=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles()
  c={'object':o.name,'nonmanifold_source_edges':bad,'signed_volume':volume,'evaluated_triangles':len(me.loop_triangles),'zero_area_triangles':sum(t.area<1e-11 for t in me.loop_triangles),'finite':all(math.isfinite(x) for v in me.vertices for x in v.co),'materials':bool(o.data.materials) and all(s.material is not None for s in o.material_slots)}
  c['passed']=not bad and volume>0 and not c['zero_area_triangles'] and c['finite'] and c['materials'];checks.append(c);ev.to_mesh_clear()
 assert checks and all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
 return {'checks_passed':True,'checked_before_assembly':True,'objects':checks}

def mount(i,p,role):
 return {'id':i,'node':'socket.'+i,'parent':None,'role':role,'position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':['MilitaryArmor.service-cartridge.v1' if role=='accessory' else 'MilitaryArmor.industrial-mining.'+role],'allowed_scale':[1,1,1]}

def preview(folder,center,scale):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=10;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Industrial mining review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
 added=[];target=Vector(center)
 for loc,power,size in [((2,-5,8),1800,5),((-4,-1,5),1500,4),((3,5,7),2200,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 folder=folder/'Previews';folder.mkdir(parents=True,exist_ok=True)
 for name,offset in [('perspective',(6,-8,8)),('top',(0,0,10))]:
  cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def save(m,mounts,points=None):
 # Cap bevels conservatively on narrow cooling and optical elements.
 for o in m.coll.objects:
  for mod in o.modifiers:
   if mod.type=='BEVEL':mod.width=min(mod.width,.001)
 for point in points or []:
  node=bpy.data.objects.new(point['node'],None);m.coll.objects.link(node);node.location=point['position'];node.empty_display_size=.08;node['functional_point_id']=point['id']
 report=scan();write(ROOT/'Parts'/m.pid/'geometry-validation.json',report)
 m.save(mounts=mounts,points=points,notes='Static industrial optical process assembly. Procedural PBR; no file texture or UV dependencies. BU physical scale unspecified.')
 pf=ROOT/'Parts'/m.pid;data=json.loads((pf/'part.json').read_text());r=mounts[0]
 data['attachment_areas']=[{'id':'root-plane','parent':None,'role':r['role'],'shape':'logical-plane','dimensions':[.08,.08],'position':r['position'],'forward':r['forward'],'up':r['up'],'compatibility':r['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]}];write(pf/'part.json',data)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.45)

write(FOLDER/'composition-plan.md','''# MA-M02 — промышленный добывающий лазер 1×3

Каталог mining-laser-industrial: добывает руду с астероидов и переносит её в доступный груз; увеличенные дальность и скорость. Сетка 1×3 не задаёт метры или габариты меша. Фиксированный оптический промышленный тракт, без придуманного наведения, башни, механического бура и постоянного луча. Функциональная точка -Y является авторингом Blender, не отображением XML MuzzleX/Y.

До моделирования проверена библиотека MilitaryArmor. MA-R01-P05 v1.0: исправленный сервисный картридж 0.74×0.60×0.08 BU, совпадает по палитре и креплению, повторно использовать единичным масштабом. MA-E01-P04 v1.0: отдельная термопанель примерно 0.10×1.11×0.46 BU, вертикальный профиль короткого двигателя не даёт длинного закрытого охлаждения оптического тракта; не растягивать. MA-W04-P03 v1.0: четырёхканальная поперечная пусковая балка 3.98×2.01×0.76 BU, назначение/геометрия не совместимы с лазерной оптикой. MA-F01-P03 v1.0: широкое поперечное бронеплечо 3.69×0.42×0.43 BU, не подходит продольному промышленному корпусу без недопустимого масштаба.

Создать четыре новые детали: MA-M02-P01 — продольное низкое силовое шасси с закрытыми диагональными опорами; MA-M02-P02 — модуль оптического тракта с полыми кольцами и тёмным технологическим сердечником (три экземпляра); MA-M02-P03 — широкая фасетная защищённая апертура с глубоко посаженной линзой; MA-M02-P04 — продольная кассета из шести закрытых теплообменных секций (два экземпляра).

Восемь стабильных экземпляров, единичный масштаб. Полные socket poses, семантическая совместимость. Каждую новую деталь проверить и сохранить до сборки. Правая система +Z вверх, -Y вперёд; исходники Blender, GLB не создавать.
''')

m=Part('MA-M02-P01','Industrial mining longitudinal support chassis')
m.panel('Graphite hull gasket',(0,0,.045),(1.73,5.55,.09),'Dark',.26,.001)
m.panel('Longitudinal pressure shell',(0,0,.20),(1.63,5.42,.27),'Armor',.25,.001)
m.panel('Cold ceramic service deck',(0,0,.355),(1.53,5.25,.09),'Ceramic',.23,.001)
for x in [-.43,.43]:
 m.section('Swept closed optic support',[(-2.15,x,.48,.19,.15,.03),(-1.65,x,.58,.19,.37,.035),(1.58,x,.58,.19,.37,.035),(1.94,x,.48,.19,.15,.03)],'Titanium',.001)
m.panel('Rear service seat',(0,2.08,.41),(.84,.73,.03),'Dark',.10,.001)
sockets=[mount('hull',(0,0,0),'hull'),mount('aperture',(0,-2.18,.96),'aperture'),mount('service',(0,2.08,.43),'accessory')]
for i,y in enumerate([-1.25,0,1.25]):sockets.append(mount('optic'+str(i),(0,y,.96),'optic'))
for i,x in enumerate([-.70,.70]):sockets.append(mount('cooling'+str(i),(x,0,.43),'cooling'))
save(m,sockets)

m=Part('MA-M02-P02','Industrial mining sealed optical process cell')
m.cyl('Dark sealed optical process core',(0,0,0),.29,.97,'Dark','Y',24)
for y in [-.43,.43]:
 m.ring('Titanium optical alignment ring',(0,y,0),.37,.295,.11,'Y','Titanium',24)
 m.ring('Pale segmented optic crown',(0,y-.002,0),.395,.369,.075,'Y','Ceramic',12)
for x in [-.235,.235]:
 m.box('Closed power return channel',(x,0,.255),(.07,.85,.09),'Titanium',.001)
m.panel('Recessed narrow diagnostic window',(0,0,.293),(.13,.52,.014),'Optic',.025,.001)
m.panel('Cell serial index',(0,.32,.298),(.12,.025,.012),'Signal',.005,.001)
save(m,[mount('root',(0,0,0),'optic')])

m=Part('MA-M02-P03','Industrial mining protected broad optical aperture')
m.ring('Graphite aperture pressure body',(0,0,0),.57,.395,.38,'Y','Armor',12)
m.ring('Pale faceted aperture shell',(0,-.045,0),.60,.49,.24,'Y','Ceramic',12)
m.ring('Recessed titanium lens bezel',(0,-.195,0),.49,.385,.075,'Y','Titanium',24)
m.cyl('Deep seated mining optical lens',(0,-.155,0),.382,.018,'Optic','Y',32)
m.ring('Lens ceramic perimeter',(0,-.169,0),.36,.342,.014,'Y','Steel',32)
points=[{'id':'mining-emitter','node':'point.mining-emitter','parent':None,'role':'mining-laser-emission','position':[0,-.235,0],'forward':[0,-1,0],'up':[0,0,1],'direction_semantics':'outgoing optical axis; authoring only; not mapped to XML MuzzleX/Y'}]
save(m,[mount('root',(0,0,0),'aperture')],points)

m=Part('MA-M02-P04','Industrial mining six-section enclosed heat exchanger')
m.panel('Closed longitudinal coolant manifold',(0,0,.07),(.28,3.80,.14),'Titanium',.08,.001)
for i in range(6):
 y=(i-2.5)*.58
 m.section('Faceted enclosed thermal segment %d'%i,[(y-.25,0,.15,.31,.16,.035),(y-.16,0,.29,.35,.43,.055),(y+.19,0,.24,.34,.31,.045)],'Ceramic',.001)
 m.panel('Dark thermal ceramic insert %d'%i,(0,y+.01,.51),(.16,.19,.014),'Dark',.035,.001)
 m.panel('Inset thermal diagnostic %d'%i,(0,y-.14,.504),(.07,.025,.012),'Optic',.005,.001)
save(m,[mount('root',(0,0,0),'cooling')])

a=Assembly(BID,'mining-laser-industrial',[1,3],'Промышленный добывающий лазер')
a.instance('Chassis','MA-M02-P01')
connections=[]
for i,y in enumerate([-1.25,0,1.25]):
 iid='OpticCell'+str(i);a.instance(iid,'MA-M02-P02',loc=(0,y,.96));connections.append({'parent':'Chassis','socket':'optic'+str(i),'child':iid,'child_socket':'root'})
a.instance('Aperture','MA-M02-P03',loc=(0,-2.18,.96));connections.append({'parent':'Chassis','socket':'aperture','child':'Aperture','child_socket':'root'})
for i,x in enumerate([-.70,.70]):
 iid='Cooling'+str(i);a.instance(iid,'MA-M02-P04',loc=(x,0,.43));connections.append({'parent':'Chassis','socket':'cooling'+str(i),'child':iid,'child_socket':'root'})
a.instance('Service','MA-R01-P05',loc=(0,2.08,.43));connections.append({'parent':'Chassis','socket':'service','child':'Service','child_socket':'bottom'})
bpy.context.scene.frame_end=1;bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'functional_points':[{'id':'mining-emitter','instance':'Aperture','part_point':'mining-emitter','position_block':[0,-2.415,.96],'forward_block':[0,-1,0],'up_block':[0,0,1],'authoring_only':True}],'animations':[],'exports':[],'notes':'Fixed industrial mining optics; no permanent beam. Distinct three-cell optical path and six-section enclosed twin cooling banks. BU unspecified; no engine mapping.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')));preview(FOLDER,(0,0,.7),6.9)
write(FOLDER/'README.md','''# MA-M02 — промышленный добывающий лазер

Каталог mining-laser-industrial, сетка 1×3. MilitaryArmor 1.3: три последовательные оптические ячейки на длинном низком шасси, широкая глубоко посаженная апертура и две продольные кассеты из шести закрытых теплообменников. Холодные фасетные оболочки, титановые оптические кольца, графитовый силовой тракт, ограниченная бирюзовая эмиссия линзы и диагностики. Это фиксированный добывающий лазер; движения, башни и постоянного луча нет.

Исходник MA-M02.blend; состав assembly.json; план composition-plan.md. Предпросмотры Previews/top.png и Previews/perspective.png. Четыре новые детали MA-M02-P01…P04, сервисный картридж MA-R01-P05 v1.0 использован без изменений; восемь экземпляров. Каждая новая деталь отдельно сохранена, проверена до сборки и имеет два предпросмотра.

Логические крепления с полной позой и семантической совместимостью, единичный масштаб. Точка mining-emitter: локально в апертуре (0,-0.235,0), в сборке (0,-2.415,0.96), направление -Y, верх +Z. Это авторинг Blender, не контракт XML MuzzleX/Y.

Процедурные PBR, без файловых текстур и обязательной UV. Физический размер BU не согласован. validation.json создаётся независимым повторным открытием всех зависимых Blender-исходников и сборки. GLB не создавались. Игровой экспорт, установка, LOD и коллайдеры не входят в текущий ассет.
''')
print('MA_M02_BUILT',flush=True)
