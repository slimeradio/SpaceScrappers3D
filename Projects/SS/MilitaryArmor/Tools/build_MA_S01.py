import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-S01'; FOLDER=ROOT/'Blocks'/BID

def scan():
 checks=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);winding=sum(len(e.link_loops)==2 and e.link_loops[0].vert==e.link_loops[1].vert for e in bm.edges);bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles()
  c={'object':o.name,'nonmanifold_source_edges':bad,'signed_volume':vol,'inconsistent_winding_edges':winding,'finite':all(math.isfinite(x) for v in me.vertices for x in v.co),'zero_area_triangles':sum(t.area<1e-11 for t in me.loop_triangles),'materials':bool(o.data.materials) and all(s.material is not None for s in o.material_slots)}
  c['passed']=not bad and not winding and vol>0 and c['finite'] and not c['zero_area_triangles'] and c['materials'];checks.append(c);ev.to_mesh_clear()
 assert checks and all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
 return {'checked_before_assembly':True,'checks_passed':True,'objects':checks}

def mount(i,p,role,compat):
 return {'id':i,'node':'socket.'+i,'parent':None,'role':role,'position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':[compat],'allowed_scale':[1,1,1]}

def preview(folder,center,scale):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Auction terminal review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
 added=[];target=Vector(center)
 for loc,power,size in [((2,-5,7),1300,5),((-4,-1,4),1000,4),((3,5,5),1700,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 folder=folder/'Previews';folder.mkdir(parents=True,exist_ok=True)
 for name,offset in [('perspective',(5,-8,7)),('top',(0,0,8))]:
  cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def save(m,mounts):
 report=scan();pf=ROOT/'Parts'/m.pid;write(pf/'geometry-validation.json',report)
 m.save(mounts=mounts,notes='Static protected service trade terminal geometry. Procedural uniform PBR; no UV or image textures. No physical labels or screen text. No animation. Authoring interfaces only.')
 data=json.loads((pf/'part.json').read_text());r=mounts[0];data['attachment_areas']=[{'id':'root-plane','parent':None,'role':r['role'],'shape':'logical-plane','dimensions':[.08,.08],'position':r['position'],'forward':r['forward'],'up':r['up'],'compatibility':r['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]}];write(pf/'part.json',data)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.45)

write(FOLDER/'composition-plan.md','''# MA-S01 — блок аукциона базы 1×1

Каталог auction-base: роль Auction для торговой инфраструктуры. Сам тип не гарантирует появление рынка; модель не добавляет торговые правила или игровые параметры. Сетка 1×1 не определяет физические метры; BU условные, +Z вверх, -Y вперёд.

Проверены готовые детали MilitaryArmor. MA-N01-P01 v1.0 — квадратное защищённое коммуникационное шасси 1.74×1.65×0.3045 BU, единичный масштаб, подходит роли коммутационного терминала. Повторно использовать без изменений. Сервисный MA-R01-P05 v1.0 0.74×0.60×0.08 BU подходит готовому переднему гнезду шасси; повторно использовать. MA-C01-P02 — вычислительная кассета 3.10×1.10×0.79 BU, не подходит квадратной компоновке; не копировать и не масштабировать. MA-N01-P03 несёт радиопанель и не подходит низкому утопленному сервисному интерфейсу. MA-M01-P03 — длинная тепловая оболочка 3.53 BU, не подходит коротким защитным плечам. Kits отсутствует. MA-P06 не использовать.

Создать MA-S01-P01 — закрытый коммутационный терминал с утопленным пассивным интерфейсом, боковыми индексами и двумя логическими посадками; MA-S01-P02 — короткое стреловидное бронеплечо, 2 экземпляра. Сначала самостоятельные источники, материалы, metadata, geometry gate и два превью каждой детали; потом пять stable instances готовых деталей. Полные позиции, forward/up и совместимость сокетов. Без анимаций, надписей, фиктивного текста экрана, антенн и стволов. Не создавать GLB.
''')

m=Part('MA-S01-P01','Protected trade service interface')
m.panel('Sealed terminal bed',(0,.22,.045),(.99,.75,.09),'Dark',.11,.001)
m.section('Sloped sealed switching casing',[(-.15,0,.10,.95,.16,.035),(.02,0,.20,.95,.36,.065),(.48,0,.24,.95,.44,.065),(.58,0,.19,.88,.32,.045)],'Titanium',.001)
# Recessed top interface; blank passive face, no text or invented UI.
m.panel('Dark recessed interface well',(0,.24,.467),(.73,.44,.016),'Dark',.055,.001)
m.panel('Passive smoked interface insert',(0,.24,.479),(.55,.32,.012),'Armor',.04,.001)
for x in [-.405,.405]:
 m.panel('Raised cold interface side rail',(x,.23,.49),(.12,.55,.10),'Ceramic',.035,.001)
m.panel('Cold rear brow',(0,.505,.475),(.67,.11,.10),'Ceramic',.035,.001)
m.panel('Protected front interface lip',(0,-.045,.335),(.86,.11,.09),'Ceramic',.035,.001)
for x in [-.32,.32]:
 m.panel('Recessed status well',(x,.24,.482),(.07,.16,.012),'Dark',.015,.001)
 m.panel('Small cyan diagnostic',(x,.24,.493),(.024,.07,.010),'Signal',.005,.001)
sockets=[mount('root',(0,0,0),'support','MilitaryArmor.antenna.support'),mount('left',(-.65,-.02,0),'armor-shoulder','MilitaryArmor.trade.shoulder.v1'),mount('right',(.65,-.02,0),'armor-shoulder','MilitaryArmor.trade.shoulder.v1')]
save(m,sockets)

if '--interface-only' not in sys.argv:
 m=Part('MA-S01-P02','Short swept terminal armor shoulder')
 m.section('Closed diagonal shoulder',[(-.55,0,.10,.20,.20,.035),(-.30,0,.22,.25,.44,.055),(.38,0,.28,.27,.56,.060),(.59,0,.22,.21,.44,.045)],'Armor',.001)
 m.section('Cold swept armor cap',[(-.51,0,.20,.22,.12,.025),(-.23,0,.43,.28,.16,.035),(.38,0,.53,.30,.18,.04),(.56,0,.42,.23,.16,.03)],'Ceramic',.001)
 m.panel('Inset shoulder service seam',(0,.20,.624),(.13,.28,.014),'Titanium',.025,.001)
 save(m,[mount('root',(0,0,0),'armor-shoulder','MilitaryArmor.trade.shoulder.v1')])


a=Assembly(BID,'auction-base',[1,1],'Блок аукциона базы')
a.instance('Chassis','MA-N01-P01');a.instance('Terminal','MA-S01-P01',loc=(0,.18,.285));a.instance('LeftArmor','MA-S01-P02',loc=(-.65,.16,.285));a.instance('RightArmor','MA-S01-P02',loc=(.65,.16,.285));a.instance('Service','MA-R01-P05',loc=(0,-.43,.304))
connections=[{'parent':p,'socket':s,'child':c,'child_socket':q} for p,s,c,q in [('Chassis','support','Terminal','root'),('Terminal','left','LeftArmor','root'),('Terminal','right','RightArmor','root'),('Chassis','service','Service','bottom')]]
bpy.context.scene.frame_end=1;bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'functional_points':[],'animations':[],'exports':[],'notes':'Static protected trade service interface. Catalog Auction role does not itself guarantee market availability. Blender authoring only; no game integration.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')));preview(FOLDER,(0,0,.40),2.6)
write(FOLDER/'README.md','''# MA-S01 — блок аукциона базы

Каталог auction-base, сетка 1×1, роль Auction для торговой инфраструктуры. Сам тип не гарантирует рынок. Защищённый сервисный коммутационный терминал MilitaryArmor 1.3: низкое квадратное шасси, приподнятая задняя секция с утопленным пассивным интерфейсом, короткие стреловидные плечи и передний сервисный картридж. Графит, холодные светлые панели, сдержанная диагностика. Без надписей, текста на экране, антенн, стволов и анимаций.

MA-S01.blend — редактируемый источник; assembly.json — пять стабильных экземпляров с полными локальными позами и соединениями. Две новые самостоятельные детали MA-S01-P01 и MA-S01-P02, плечо повторяется дважды без зеркалирования. Готовые MA-N01-P01 v1.0 и MA-R01-P05 v1.0 использованы без изменений и с единичным масштабом. План composition-plan.md сохранён до моделирования.

Новые детали имеют part.json, geometry-validation.json, Previews/top.png и perspective.png. Процедурные PBR-материалы, файловые текстуры и UV не требуются. Новая эмиссия только два маленьких диагностических индекса интерфейса. Все крепления логические; анимации отсутствуют. Общие материалы и старые исходники не менялись.

Независимая проверка повторно открывает все использованные детали и сборку; validation.json. Предпросмотры сборки Previews/top.png и perspective.png. Размер BU условный, это авторинг Blender. GLB не создавался. Игровая установка, LOD, коллайдеры и runtime-проверка не выполнялись.
''')
print('MA_S01_BUILT',flush=True)