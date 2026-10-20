import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector,Matrix
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-N01';FOLDER=ROOT/'Blocks'/BID

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
 return {'id':i,'node':'socket.'+i,'parent':None,'role':role,'position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':['MilitaryArmor.service-cartridge.v1' if role=='accessory' else 'MilitaryArmor.antenna.'+role],'allowed_scale':[1,1,1]}

def preview(folder,center,scale):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Antenna review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
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
 m.save(mounts=mounts,notes='Static protected communications module; no added gameplay mechanism. Procedural PBR; no file texture or UV dependencies.')
 pf=ROOT/'Parts'/m.pid;data=json.loads((pf/'part.json').read_text());r=mounts[0]
 data['attachment_areas']=[{'id':'root-plane','parent':None,'role':r['role'],'shape':'logical-plane','dimensions':[.08,.08],'position':r['position'],'forward':r['forward'],'up':r['up'],'compatibility':r['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]}];write(pf/'part.json',data)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65)

write(FOLDER/'composition-plan.md','''# MA-N01 — антенна 1×1

Каталог antenna-1x1: радиосвязь и доступ к инфраструктуре, раздельные приём/передача. Сетка 1×1, BU условные. Внешность передаёт назначение фиксированной защищённой апертурной панелью; движение и новые функции не добавлены.

До моделирования рассмотрены детали MilitaryArmor: MA-P07 v1.3 — оптический лидар 0.79×0.67×0.27 BU, не радиопанель, не используется; MA-E01-P01 — корпус двигателя, не подходит по форме и назначению; MA-A01-P01 — плоская броня 1×1, не содержит закрытых опор и корпуса связи, изменение масштаба не решит различие. MA-R01-P05 v1.0 — совместимый защищённый сервисный картридж 0.74×0.60×0.08 BU, используется без изменений и масштаба. Дефектный MA-P06 не используется.

Три новые детали: MA-N01-P01 — низкий гранёный корпус связи; MA-N01-P02 — защищённая фазированная панель с двадцатью тёмными ячейками и малым диагностическим индексом; MA-N01-P03 — закрытая парная диагональная опора. Каждая сохраняется отдельно с материалами и полными логическими креплениями, немедленно проверяется до сборки, получает top/perspective. Крепёж не подменяет sockets.

Четыре экземпляра, единичные масштабы, полное совмещение socket position/forward/up; статическая сборка. Правая система, +Z вверх, -Y вперёд. Исходники Blender; GLB не генерируется.
''')

m=Part('MA-N01-P01','Protected communications chassis')
m.panel('Hull pressure seal',(0,0,.045),(1.74,1.65,.09),'Dark',.24,.004)
m.panel('Graphite electronics housing',(0,0,.145),(1.65,1.56,.20),'Armor',.23,.006)
m.panel('Cold armor crown',(0,0,.25),(1.57,1.48,.07),'Ceramic',.22,.004)
for x in [-.63,.63]:
 m.panel('Inset flank',(x,.05,.292),(.17,.86,.025),'Titanium',.04,.002)
m.panel('Service recess',(0,-.43,.292),(.80,.68,.022),'Dark',.1,.002)
sockets=[mount('hull',(0,0,0),'hull'),mount('support',(0,.18,.285),'support'),mount('service',(0,-.43,.304),'accessory')]
save(m,sockets)

m=Part('MA-N01-P02','Protected phased communications aperture')
m.panel('Faceted panel back',(0,0,0),(1.45,1.12,.11),'Titanium',.19,.004)
m.panel('Cold ceramic aperture bezel',(0,0,.065),(1.41,1.08,.07),'Ceramic',.17,.003)
m.panel('Recessed radio aperture',(0,0,.104),(1.19,.86,.014),'Dark',.1,.001)
for row in range(4):
 for col in range(5):
  m.panel('Radio ceramic cell %d %d'%(row,col),((col-2)*.219,(row-1.5)*.193,.118),(.199,.171,.016),'Armor',.025,.001)
m.panel('Diagnostic index',(0,-.478,.108),(.15,.021,.009),'Signal',.005,.0005)
# Tilt all authored component objects together around the part origin, preserving separate editable meshes.
rot=Matrix.Rotation(math.radians(58),4,'X')
for o in m.coll.objects:o.matrix_world=rot@o.matrix_world
save(m,[mount('root',(0,0,0),'aperture')])

m=Part('MA-N01-P03','Closed diagonal aperture support')
for x in [-.49,.49]:
 m.section('Closed swept support',[(-.26,x,.07,.23,.14,.04),(.10,x,.25,.25,.48,.06),(.30,x,.31,.24,.58,.05)],'Titanium',.003)
 m.section('Faceted support armor',[(-.18,x,.16,.24,.16,.04),(.13,x,.34,.25,.39,.05),(.27,x,.36,.25,.43,.05)],'Ceramic',.003)
m.box('Protected transverse hinge',(0,.09,.56),(1.14,.20,.15),'Armor',.005)
save(m,[mount('root',(0,0,0),'support'),mount('aperture',(0,.04,.62),'aperture')])

a=Assembly(BID,'antenna-1x1',[1,1],'Антенна')
a.instance('Chassis','MA-N01-P01');a.instance('Support','MA-N01-P03',loc=(0,.18,.285));a.instance('Aperture','MA-N01-P02',loc=(0,.22,.905));a.instance('Service','MA-R01-P05',loc=(0,-.43,.304))
connections=[{'parent':'Chassis','socket':'support','child':'Support','child_socket':'root'},{'parent':'Support','socket':'aperture','child':'Aperture','child_socket':'root'},{'parent':'Chassis','socket':'service','child':'Service','child_socket':'bottom'}]
bpy.context.scene.frame_end=1;bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Static protected phased radio aperture; no game integration; physical BU unspecified. All part sources validated before assembly.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')));preview(FOLDER,(0,0,.68),2.8)
write(FOLDER/'README.md','''# MA-N01 — антенна

Каталог antenna-1x1, сетка 1×1. MilitaryArmor 1.3: защищённая фиксированная радиопанель с фасетной светлой окантовкой, тёмным полем ячеек и закрытой парной диагональной опорой. Графитовый низкий корпус и минимальная диагностическая эмиссия. Хлыстов, наружных поручней и автомобильных решёток нет.

Исходник MA-N01.blend; состав assembly.json; план composition-plan.md. Предпросмотры Previews/top.png и Previews/perspective.png. Три новые детали MA-N01-P01…P03 и повторно используемый MA-R01-P05 v1.0, четыре экземпляра. Каждая новая деталь сохранена отдельно в Parts/ с материалами, part.json, geometry-validation.json и двумя превью. Полные логические крепления, единичные масштабы, без анимации.

Процедурные PBR Armor/Ceramic/Titanium/Dark/Signal; файловые текстуры и UV не требуются. Физический масштаб BU не определён. Независимая проверка повторно открывает детали и сборку: validation.json. GLB не создавался. Метаданные — контракт авторинга Blender; игровой экспорт, установка, LOD и коллайдеры не входят в этот ассет.
''')
print('MA_N01_BUILT',flush=True)
