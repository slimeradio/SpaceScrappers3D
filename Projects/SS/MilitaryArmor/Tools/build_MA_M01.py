import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-M01'; FOLDER=ROOT/'Blocks'/BID

def scan():
 checks=[]; dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles()
  c={'object':o.name,'nonmanifold_source_edges':bad,'positive_volume':vol,'finite':all(math.isfinite(x) for v in me.vertices for x in v.co),'zero_area_triangles':sum(t.area<1e-11 for t in me.loop_triangles),'materials':bool(o.data.materials) and all(s.material is not None for s in o.material_slots)}
  c['passed']=not bad and vol>0 and c['finite'] and not c['zero_area_triangles'] and c['materials'];checks.append(c);ev.to_mesh_clear()
 assert checks and all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
 return {'checked_before_assembly':True,'checks_passed':True,'objects':checks}

def mount(i,p,role):
 return {'id':i,'node':'socket.'+i,'parent':None,'role':role,'position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':['MilitaryArmor.service-cartridge.v1' if role=='accessory' else 'MilitaryArmor.mining-small.'+role],'allowed_scale':[1,1,1]}

def preview(folder,center,scale):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Mining laser review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
 added=[];target=Vector(center)
 for loc,power,size in [((2,-5,7),1300,5),((-4,-1,4),1000,4),((3,5,5),1700,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 folder=folder/'Previews';folder.mkdir(parents=True,exist_ok=True)
 for name,offset in [('perspective',(5,-8,7)),('top',(0,0,8))]:
  cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def save(m,mounts,points=None):
 # Small chamfers are explicit; do not trust bevel overlap clamping on thin surfaces.
 for o in m.coll.objects:
  for mod in o.modifiers:
   if mod.type=='BEVEL':mod.width=min(mod.width,.001)
 report=scan();pf=ROOT/'Parts'/m.pid;write(pf/'geometry-validation.json',report)
 m.save(mounts=mounts,points=points,notes='Static mining optical equipment. Editable separate solids; uniform procedural PBR, no file texture or UV dependency. No beam mesh.')
 data=json.loads((pf/'part.json').read_text());r=mounts[0];data['attachment_areas']=[{'id':'root-plane','parent':None,'role':r['role'],'shape':'logical-plane','dimensions':[.08,.08],'position':r['position'],'forward':r['forward'],'up':r['up'],'compatibility':r['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]}];write(pf/'part.json',data)
 lo=data['bounds_local']['min'];hi=data['bounds_local']['max'];preview(pf,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.35)

write(FOLDER/'composition-plan.md','''# MA-M01 — малый добывающий лазер 1×3

Каталог mining-laser-small: снимает рудное покрытие астероида и переносит добычу в доступный груз; требует питание и свободное место. Каталожные дальность/скорость/расход остаются справочными, модель их не меняет. Размер 1×3 — клетки, не метры. BU условные; +Z вверх, -Y вперёд.

Проверены существующие MilitaryArmor детали: MA-W02-P01 — боевой лазерный корпус шириной 2.46 BU, не соответствует узкому рабочему силуэту; MA-E02-P02 — тяговая камера с сопловой геометрией, не оптическая головка; MA-N01-P03 — короткая наклонная опора радиопанели, не продольная оболочка. Их масштабирование изменило бы функцию/пропорции. MA-R01-P05 v1.0, 0.74×0.60×0.08 BU, подходит как сервисный картридж и используется без изменений. MA-P06 не используется.

Создать MA-M01-P01 — узкое закрытое шасси с утопленным сервисным местом; MA-M01-P02 — защищённую оптическую головку с короткой апертурой и линзой; MA-M01-P03 — длинную стреловидную тепловую оболочку, используемую дважды без зеркалирования. Новые детали сначала сохраняются и проверяются отдельно; затем 5 экземпляров готовых источников с единичным масштабом. Логические крепления сохраняют позицию/forward/up, совместимость и область посадки.

Фиксированный компактный рабочий лазер, не пушка/дрель; без турели, наведения, анимаций и постоянного луча. Бирюзовая эмиссия только слабая оптика и малые сервисные индексы. Функциональная точка authoring-emitter имеет локальную позицию и нормализованные направления; это не игровой mapping MuzzleX/Y. Blender-only, GLB не генерировать.
''')

m=Part('MA-M01-P01','Small mining laser protected longitudinal chassis')
m.panel('Sealed graphite base',(0,0,.075),(1.62,5.12,.15),'Dark',.20,.001)
m.section('Protected optical spine',[(-2.48,0,.26,1.16,.36,.08),(-1.9,0,.38,1.30,.60,.12),(1.85,0,.38,1.30,.60,.12),(2.42,0,.24,1.10,.32,.08)],'Armor',.001)
m.panel('Cold rear cap',(0,1.78,.706),(1.12,1.02,.05),'Ceramic',.14,.001)
m.panel('Cartridge recess',(0,1.75,.737),(.82,.69,.014),'Dark',.07,.001)
for x in [-.29,.29]:
 m.panel('Protected optical channel',(x,-.15,.704),(.20,2.36,.05),'Titanium',.045,.001)
m.panel('Diagnostic index',(0,.74,.716),(.18,.035,.018),'Signal',.006,.001)
save(m,[mount('hull',(0,0,0),'hull'),mount('optic',(0,-1.70,1.16),'optic'),mount('left',(-.66,-.10,.20),'shoulder'),mount('right',(.66,-.10,.20),'shoulder'),mount('service',(0,1.75,.746),'accessory')])

if '--chassis-only' not in sys.argv:
 m=Part('MA-M01-P02','Recessed work optic with protected aperture')
 # The aperture is a short hollow assembly, deliberately unlike a weapon barrel.
 m.ring('Outer faceted protective bezel',(0,-.20,0),.49,.385,.52,axis='Y',mat='Ceramic',verts=12)
 m.ring('Titanium internal aperture',(0,-.43,0),.386,.295,.08,axis='Y',mat='Titanium',verts=24)
 m.cyl('Dark optical backing',(0,-.18,0),.305,.045,'Dark',axis='Y',verts=32)
 m.cyl('Recessed blue work lens',(0,-.216,0),.285,.025,'Optic',axis='Y',verts=32)
 m.ring('Lens retainer',(0,-.24,0),.317,.278,.04,axis='Y',mat='Steel',verts=24)
 for x in [-.43,.43]:
  m.box('Protected emitter side shoe',(x,-.06,-.20),(.14,.42,.24),'Armor',.001)
 point={'id':'authoring-emitter','node':None,'parent':None,'role':'mining-beam-origin','space':'part-local','position':[0,-.49,0],'forward':[0,-1,0],'up':[0,0,1],'notes':'Authoring only; no established conversion to catalog MuzzleX/MuzzleY; no beam geometry.'}
 save(m,[mount('root',(0,0,0),'optic')],[point])
 
 m=Part('MA-M01-P03','Small mining laser swept thermal armor')
 m.section('Closed thermal shoulder',[(-1.91,0,.08,.17,.17,.035),(-1.25,0,.19,.30,.39,.065),(.95,0,.22,.29,.44,.065),(1.62,0,.10,.23,.20,.045)],'Titanium',.001)
 m.section('Cold swept armor shell',[(-1.83,0,.20,.19,.18,.035),(-1.18,0,.40,.34,.25,.055),(.93,0,.43,.33,.28,.055),(1.54,0,.25,.25,.18,.04)],'Ceramic',.001)
 for y in [-.80,-.24,.32,.88]:
  m.panel('Flush dark thermal tile',(0,y,.579),(.21,.39,.014),'Dark',.035,.001)
 save(m,[mount('root',(0,0,0),'shoulder')])
 
 
a=Assembly(BID,'mining-laser-small',[1,3],'Малый добывающий лазер')
a.instance('Chassis','MA-M01-P01');a.instance('Optic','MA-M01-P02',loc=(0,-1.70,1.16));a.instance('LeftThermal','MA-M01-P03',loc=(-.66,-.10,.20));a.instance('RightThermal','MA-M01-P03',loc=(.66,-.10,.20));a.instance('Service','MA-R01-P05',loc=(0,1.75,.746))
connections=[{'parent':'Chassis','socket':s,'child':c,'child_socket':t} for s,c,t in [('optic','Optic','root'),('left','LeftThermal','root'),('right','RightThermal','root'),('service','Service','bottom')]]
bpy.context.scene.frame_end=1;bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'functional_points':[{'id':'mining-emitter','instance':'Optic','part_point':'authoring-emitter','position_block':[0,-2.19,1.16],'forward_block':[0,-1,0],'up_block':[0,0,1],'scope':'Blender authoring; no game mapping'}],'animations':[],'exports':[],'notes':'Static working laser, protected optical path, no visible beam. Part sources checked before assembly. Physical scale unspecified.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')));preview(FOLDER,(0,0,.40),6.1)
write(FOLDER/'README.md','''# MA-M01 — малый добывающий лазер

Каталог mining-laser-small, сетка 1×3. Узкий рабочий лазер MilitaryArmor 1.3: закрытый продольный оптический тракт, короткая защищённая линза спереди, две стреловидные тепловые оболочки и утопленный задний сервисный картридж. Графит, холодная светлая броня, титан; слабая оптическая и минимальная диагностическая эмиссия. Без механической дрели, боевого ствола, турели и постоянного луча.

Редактируемый исходник MA-M01.blend, состав assembly.json, предварительный план composition-plan.md. Три новые самостоятельные детали MA-M01-P01…P03, повторно использован MA-R01-P05 v1.0; 5 экземпляров. Каждая новая деталь имеет part.json, geometry-validation.json и Previews/top.png + perspective.png. Масштабы единичные, полные логические крепления и области посадки; анимации отсутствуют.

Функциональный authoring-emitter в локальной системе оптической детали, вычисленное положение блока [0,-2.19,1.16], вперёд [0,-1,0], вверх [0,0,1]. Игровое соответствие MuzzleX/Y не установлено. Все точки — метаданные авторинга Blender.

Процедурные PBR-материалы; файловые текстуры и UV не требуются. BU условные. Предпросмотры сборки Previews/top.png и perspective.png. Независимый verifier повторно открывает источники и сборку, отчёт validation.json. GLB не создавался. Игровая установка, LOD, коллайдеры и runtime-проверки не выполнялись.
''')
print('MA_M01_BUILT',flush=True)
