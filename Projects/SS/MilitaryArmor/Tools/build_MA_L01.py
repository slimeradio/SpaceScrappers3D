import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector,Matrix
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-L01';FOLDER=ROOT/'Blocks'/BID

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
 return {'id':i,'node':'socket.'+i,'parent':None,'role':role,'position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':['MilitaryArmor.service-cartridge.v1' if role=='accessory' else 'MilitaryArmor.corridor.'+role],'allowed_scale':[1,1,1]}

def preview(folder,center,scale):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Antenna review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
 added=[];target=Vector(center)
 for loc,power,size in [((1,-4,7),1300,5),((-4,-1,4),1000,4),((3,5,5),1700,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 folder=folder/'Previews';folder.mkdir(parents=True,exist_ok=True)
 for name,offset in [('perspective',(4,-7,3.1)),('top',(0,0,8))]:
  cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def save(m,mounts):
 report=scan();write(ROOT/'Parts'/m.pid/'geometry-validation.json',report)
 m.save(mounts=mounts,notes='Static open hull connector; no door or crew simulation. Procedural PBR; no file texture or UV dependencies.')
 pf=ROOT/'Parts'/m.pid;data=json.loads((pf/'part.json').read_text());r=mounts[0]
 data['attachment_areas']=[{'id':'root-plane','parent':None,'role':r['role'],'shape':'logical-plane','dimensions':[.08,.08],'position':r['position'],'forward':r['forward'],'up':r['up'],'compatibility':r['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]}];write(pf/'part.json',data)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65)

write(FOLDER/'composition-plan.md','''# MA-L01 — коридор 1×1

Каталог corridor-1x1: лёгкий конструкционный соединитель корпуса. Механика перемещения экипажа не задана. Сетка 1×1, BU условные, +Z вверх, -Y вперёд. Короткий открытый с двух торцов броневой проход без двери, подсветки и анимаций.

До моделирования проверены MA-A01-P01 v1.0: закрытая плита 1.0×1.0×0.28 BU, не образует настила и полости; MA-N01-P03 v1.0: диагональные радиоопоры 1.23×0.56×0.635 BU, не полая оболочка; MA-M01-P03 v1.0: длинная тепловая броня лазера, не тоннель. Масштабирование не превращает эти формы в проход, поэтому создаются отдельные конструкционные детали.

MA-L01-P01 — несущий настил; MA-L01-P02 — открытая снизу П-образная гранёная оболочка; MA-L01-P03 — П-образный торцевой воротник, два экземпляра. Сначала каждый исходник, материалы, sockets, области посадки и geometry gate, затем четыре экземпляра с единичным масштабом. Оба воротника одинаковы, без зеркалирования. Посадки проверяются по позиции и полной ориентации.

Палитра MilitaryArmor 1.3: графит, холодная светлая броня, тёмный титан. Без эмиссии и файловых текстур. Blender-only; GLB запрещён. Не задаются метры, коллайдеры, герметичность или игровая интеграция.
''')

def uprofile(m,name,outer,inner,length,mat):
 wo,ho,co=outer;wi,hi,ci=inner
 profile=[(-wo/2,0),(-wo/2,ho-co),(-wo/2+co,ho),(wo/2-co,ho),(wo/2,ho-co),(wo/2,0),(wi/2,0),(wi/2,hi-ci),(wi/2-ci,hi),(-wi/2+ci,hi),(-wi/2,hi-ci),(-wi/2,0)]
 n=len(profile);v=[(x,y,z) for y in [-length/2,length/2] for x,z in profile]
 f=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return m.mesh(name,v,f,mat,0)

m=Part('MA-L01-P01','Short connector structural deck')
m.panel('Faceted graphite load deck',(0,0,.075),(1.82,1.82,.15),'Armor',.16,.001)
m.panel('Inset passage tread',(0,0,.162),(1.24,1.72,.024),'Titanium',.06,.001)
for x in [-.68,.68]:m.panel('Cold floor edge',(x,0,.166),(.12,1.64,.032),'Ceramic',.025,.001)
for y in [-.61,-.30,0,.30,.61]:m.panel('Recessed tread seam',(0,y,.176),(1.05,.018,.006),'Dark',.004,0)
save(m,[mount('hull',(0,0,0),'hull'),mount('shell',(0,0,.15),'shell')])

m=Part('MA-L01-P02','Open U section armored connector shell')
uprofile(m,'Continuous graphite U shell',(1.72,1.35,.23),(1.27,1.12,.16),1.68,'Armor')
for x in [-.864,.864]:
 m.box('Cold flank shield',(x,0,.67),(.056,1.18,.70),'Ceramic',.001)
 m.box('Inset flank field',(x*1.035,0,.65),(.012,.82,.29),'Titanium',.001)
m.panel('Cold roof armor',(0,0,1.365),(1.15,1.18,.03),'Ceramic',.13,.001)
m.panel('Recessed roof field',(0,0,1.383),(.64,.83,.012),'Titanium',.08,.001)
save(m,[mount('root',(0,0,0),'shell'),mount('front',(0,-.80,0),'collar'),mount('rear',(0,.80,0),'collar')])

m=Part('MA-L01-P03','Open armored connector end collar')
uprofile(m,'Cold faceted open portal',(1.84,1.42,.27),(1.27,1.12,.16),.16,'Ceramic')
uprofile(m,'Dark inner portal liner',(1.34,1.18,.18),(1.27,1.12,.16),.174,'Titanium')
save(m,[mount('root',(0,0,0),'collar')])

a=Assembly(BID,'corridor-1x1',[1,1],'Коридор')
a.instance('Deck','MA-L01-P01');a.instance('Shell','MA-L01-P02',loc=(0,0,.15));a.instance('FrontCollar','MA-L01-P03',loc=(0,-.80,.15));a.instance('RearCollar','MA-L01-P03',loc=(0,.80,.15))
connections=[{'parent':'Deck','socket':'shell','child':'Shell','child_socket':'root'},{'parent':'Shell','socket':'front','child':'FrontCollar','child_socket':'root'},{'parent':'Shell','socket':'rear','child':'RearCollar','child_socket':'root'}]
bpy.context.scene.frame_end=1;bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'clear_passage_authoring':{'width':1.27,'height_above_deck':1.096,'axis':'Y','open_ends':True,'units':'BU; physical scale unspecified'},'notes':'Static lightweight hull connector, no crew mechanism, no door, no pressure or gameplay contract. Sources geometry-gated before assembly.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')));preview(FOLDER,(0,0,.73),2.75)
write(FOLDER/'README.md','''# MA-L01 — коридор

Каталог corridor-1x1, сетка 1×1. Короткий конструкционный соединитель MilitaryArmor 1.3: открытый с обоих торцов П-образный тоннель, гранёные броневые воротники, графитовый настил, холодные светлые боковые щиты и крыша. Без дверей, эмиссии, анимаций и придуманной механики экипажа.

Редактируемый MA-L01.blend; assembly.json; composition-plan.md. Новые самостоятельные MA-L01-P01, P02 и P03, четыре экземпляра: воротник повторён дважды. Все детали отдельно geometry-gated до сборки, имеют part.json и Previews/top.png + perspective.png. Полные локальные позы, совместимые sockets и области посадки; масштабы единичные, зеркалирования нет.

Материалы процедурные PBR Armor/Ceramic/Titanium/Dark, файловые текстуры и UV не нужны. BU условные: размер клетки не переводится в метры. Свободное отверстие 1.27 BU по ширине, 1.096 BU от настила до потолка; это художественные измерения, не игровой контракт.

Предпросмотры Previews/top.png и perspective.png. Независимый verifier повторно открывает каждую деталь и сборку, проверяет геометрию, ссылки, материалы, полные позы и совместимость креплений: validation.json. Отдельные замкнутые solids имеют намеренные посадочные контакты оболочки, настила и воротников; булево объединение не заявляется. GLB не создан, игровой экспорт, интеграция, коллайдеры, LOD и runtime-проверка не выполнялись.
''')
print('MA_L01_BUILT',flush=True)