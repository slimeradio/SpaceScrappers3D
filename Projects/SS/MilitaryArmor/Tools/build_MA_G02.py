"""Cargo source authoring; individual evaluated geometry gates; no GLB."""
import sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-G02'; FOLDER=ROOT/'Blocks'/BID

def mount(i,p,tag):
 return {'id':i,'role':tag.split('.')[-1],'parent':'part','position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':[tag],'allowed_scale':[1,1,1]}

def inspect():
 checks=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  c={'mesh':o.name,'source_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'source_inconsistent_normal_edges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'source_zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)};bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();c.update(evaluated_triangles=len(me.loop_triangles),zero_area_triangles=sum(t.area<1e-10 for t in me.loop_triangles),finite=all(math.isfinite(v) for p in me.vertices for v in p.co),materials_resolved=bool(o.material_slots) and all(s.material for s in o.material_slots));ev.to_mesh_clear()
  c['pass']=not c['source_nonmanifold_edges'] and not c['source_zero_area_faces'] and not c['source_inconsistent_normal_edges'] and c['signed_volume']>0 and not c['zero_area_triangles'] and c['finite'] and c['materials_resolved'];checks.append(c)
 result={'checks_passed':bool(checks) and all(c['pass'] for c in checks),'meshes':checks,'validated_before_assembly':True}
 assert result['checks_passed'],str(result)
 return result

def preview(folder,target,scale,res=650):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=res;scene.render.resolution_y=res;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Cargo review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
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
 check=inspect();m.save(mounts=mounts,notes='Static garage authoring part; uniform procedural PBR. No file textures, UV dependency or animated mechanism. BU are not metres.')
 p=ROOT/'Parts'/m.pid;d=json.loads((p/'part.json').read_text())
 d['attachment_areas']=[{'id':s['id']+'-seat','parent':'part','role':s['role'],'shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts]
 write(p/'part.json',d);write(p/'geometry-validation.json',check)
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65,450)
 write(p/'README.md',f'# {m.pid} v1.0\n\n{m.title}. Редактируемый исходник {m.pid}.blend; part.json содержит материалы, эмиссию и полные логические крепления. Все масштабы единичные. Геометрия проверена до сборки: geometry-validation.json. Отдельные виды Previews/top.png и perspective.png. Статическая деталь, процедурный PBR, без файловых текстур и UV-зависимости. GLB не создавался.\n')


if '--assembly-only' not in sys.argv:
 m=Part('MA-G02-P01','Reinforced base garage superstructure')
 m.panel('Lower pressure body',(0,.12,.32),(1.46,1.05,.64),'Armor',.14,.008)
 m.panel('Raised base block',(0,.31,.70),(1.23,.69,.42),'Titanium',.11,.008)
 m.panel('Upper shield',(0,.30,.93),(1.30,.76,.08),'Ceramic',.13,.006)
 for x in [-.72,.72]:
  m.section('Swept base buttress',[(-.35,x,.30,.22,.57,.05),(.13,x,.49,.25,.93,.06),(.65,x,.39,.22,.73,.05)],'Ceramic',.006)
  m.panel('Recessed flank liner',(x,.24,.38),(.24,.51,.43),'Dark',.055,.004)
  m.panel('Protected flank plate',(x,.22,.40),(.27,.37,.34),'Armor',.06,.006)
 m.panel('Bridge seat',(0,.29,.984),(.90,.59,.028),'Steel',.07,.003)
 m.panel('Rear service inset',(0,.658,.40),(.79,.018,.40),'Dark',.05,.002)
 m.panel('Rear service cover',(0,.674,.40),(.59,.018,.26),'Titanium',.035,.002)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.garage.housing'),mount('shipyard',(0,.29,1.0),'MilitaryArmor.base-yard.bridge')])
 m=Part('MA-G02-P02','Stationary armoured shipyard service bridge')
 m.panel('Recessed work bed',(0,0,.04),(.96,.64,.08),'Titanium',.09,.005)
 m.panel('Protected diagnostic field',(0,-.06,.087),(.55,.40,.014),'Dark',.04,.001)
 for x in [-.41,.41]:
  m.section('Service bridge power ridge',[(-.37,x,.16,.20,.30,.04),(-.07,x,.25,.21,.47,.04),(.34,x,.21,.19,.39,.04)],'Armor',.006)
  m.panel('Swept ridge shield',(x,.015,.40),(.15,.56,.075),'Ceramic',.045,.004)
  for y in [-.22,.04,.24]:m.panel('Section break',(x,y,.445),(.10,.025,.012),'Titanium',.004,.001)
 m.panel('Rear bridge backbone',(0,.26,.18),(.75,.15,.28),'Steel',.05,.005)
 m.panel('Cartridge recess',(0,.14,.105),(.68,.45,.022),'Titanium',.06,.002)
 for x in [-.27,.27]:m.box('Recessed diagnostic index',(x,-.23,.099),(.05,.08,.008),'Signal',.001)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.base-yard.bridge'),mount('service',(0,.12,.12),'MilitaryArmor.service-cartridge.v1')])
a=Assembly(BID,'garage-base',[1,1],'Базовый гараж с верфью 1×1')
a.instance('Foundation','MA-G01-P01');a.instance('Portal','MA-G01-P02',loc=(0,-.40,.22));a.instance('BaseSuperstructure','MA-G02-P01',loc=(0,.20,.22));a.instance('ShipyardBridge','MA-G02-P02',loc=(0,.49,1.22));a.instance('Diagnostic','MA-R01-P05',loc=(0,.61,1.34))
connections=[{'parent_instance':'Foundation','parent_socket':'portal','child_instance':'Portal','child_socket':'root'},{'parent_instance':'Foundation','parent_socket':'housing','child_instance':'BaseSuperstructure','child_socket':'root'},{'parent_instance':'BaseSuperstructure','parent_socket':'shipyard','child_instance':'ShipyardBridge','child_socket':'root'},{'parent_instance':'ShipyardBridge','parent_socket':'service','child_instance':'Diagnostic','child_socket':'bottom'}]
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Base garage with shipyard. Capacity4096 is capacity, not ship count. BU and ship scale unspecified. Static authoring; no invented motion.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.76),3.2,850)
write(FOLDER/'README.md','''# MA-G02 — базовый гараж с верфью 1×1

MilitaryArmor 1.3; каталог garage-base. Защищённый гаражный доступ -Y на готовой платформе; усиленный ступенчатый корпус, диагональные стационарные опоры и верхний сервисный мост верфи. Capacity4096 — вместимость, не количество кораблей. Сетка 1×1 не задаёт физические метры или размер кораблей. Base=true; Shipyard; Range12 сохранены как сведения каталога, не реализованные игровые механизмы модели.

Редактируемый MA-G02.blend; assembly.json содержит пять стабильных экземпляров и четыре семантических соединения. Новые самостоятельные MA-G02-P01 и P02; повторно использованы MA-G01-P01, MA-G01-P02 и исправленный MA-R01-P05 v1.0. Все масштабы единичные. composition-plan.md объясняет выбор. Previews/top.png и perspective.png — виды сверху и в объёме.

Статическая модель. Процедурный PBR Armor/Ceramic/Titanium/Steel/Dark/Signal; файловых текстур и UV-зависимости нет, эмиссия ограничена утопленной диагностикой. Силовые опоры, уплотнение платформы, бронекожухи и посадочные места намеренно контактируют и перекрываются как слои конструкции. Новые части проверены до сборки; независимое повторное открытие всех исходников и полные позиции/ориентации sockets записаны в validation.json. Логические крепления не изображены видимыми вспомогательными мешами.

BU условные, JSON — контракт авторинга Blender. GLB не генерировались. Игровая установка, коллайдеры и LOD не выполнялись.
''')
print('MA_G02_BUILT',flush=True)