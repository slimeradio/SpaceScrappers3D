"""Cargo source authoring; individual evaluated geometry gates; no GLB."""
import sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-G01'; FOLDER=ROOT/'Blocks'/BID

def mount(i,p,tag):
 return {'id':i,'role':tag.split('.')[-1],'parent':'part','position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':[tag],'allowed_scale':[1,1,1]}

def inspect():
 checks=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  c={'mesh':o.name,'source_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'source_zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)};bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();c.update(evaluated_triangles=len(me.loop_triangles),zero_area_triangles=sum(t.area<1e-10 for t in me.loop_triangles),finite=all(math.isfinite(v) for p in me.vertices for v in p.co),materials_resolved=bool(o.material_slots) and all(s.material for s in o.material_slots));ev.to_mesh_clear()
  c['pass']=not c['source_nonmanifold_edges'] and not c['source_zero_area_faces'] and c['signed_volume']>0 and not c['zero_area_triangles'] and c['finite'] and c['materials_resolved'];checks.append(c)
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
 m=Part('MA-G01-P01','Compact garage docking platform')
 m.panel('Load foundation',(0,0,.11),(1.8,1.8,.22),'Armor',.18,.012)
 m.panel('Hull gasket',(0,0,.025),(1.68,1.68,.05),'Dark',.16,.005)
 m.panel('Inset apron',(0,-.56,.23),(1.18,.57,.02),'Titanium',.08,.002)
 for x in [-.45,.45]:m.panel('Alignment runner',(x,-.57,.26),(.085,.50,.04),'Steel',.02,.003)
 m.panel('Entry threshold',(0,-.80,.26),(1.20,.10,.04),'Ceramic',.025,.003)
 finish(m,[mount('hull',(0,0,0),'MilitaryArmor.garage.hull'),mount('portal',(0,-.40,.22),'MilitaryArmor.garage.portal'),mount('housing',(0,.20,.22),'MilitaryArmor.garage.housing')])
 m=Part('MA-G01-P02','Protected garage access portal')
 for x in [-.65,.65]:
  m.section('Swept portal shoulder',[(-.26,x,.37,.24,.74,.06),(-.08,x,.42,.29,.84,.07),(.15,x,.37,.24,.74,.06)],'Armor',.009)
  m.panel('Cold side armour',(x,-.18,.38),(.16,.20,.69),'Ceramic',.045,.007)
 m.panel('Portal crown',(0,-.02,.79),(1.35,.35,.16),'Ceramic',.08,.009)
 m.panel('Pressure backing',(0,.07,.37),(1.09,.16,.73),'Dark',.05,.006)
 for x in [-.265,.265]:
  m.panel('Recessed closed access leaf',(x,-.024,.375),(.51,.026,.64),'Titanium',.04,.003)
  m.panel('Flush capture pad',(x,-.043,.38),(.20,.018,.21),'Armor',.035,.002)
  m.box('Capture index',(x,-.056,.40),(.075,.008,.016),'Signal',.001)
 m.panel('Protected sill',(0,-.10,.035),(1.11,.28,.07),'Steel',.035,.005)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.garage.portal')])
 m=Part('MA-G01-P03','Garage rear pressure shell')
 m.panel('Rear shell',(0,.12,.34),(1.42,1.07,.68),'Armor',.16,.010)
 for x in [-.66,.66]:m.section('Diagonal reinforcement',[(-.35,x,.26,.20,.49,.05),(.20,x,.36,.20,.69,.05),(.63,x,.30,.20,.55,.05)],'Ceramic',.008)
 m.panel('Upper gasket',(0,.15,.692),(1.24,.89,.024),'Dark',.13,.003)
 m.panel('Dorsal shield',(0,.16,.735),(1.16,.80,.07),'Ceramic',.15,.007)
 m.panel('Cartridge seat',(0,.24,.789),(.76,.64,.038),'Titanium',.10,.004)
 m.panel('Rear closed seam',(0,.652,.30),(.69,.016,.33),'Dark',.055,.002)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.garage.housing'),mount('service',(0,.24,.81),'MilitaryArmor.service-cartridge.v1')])
a=Assembly(BID,'garage-ship',[1,1],'Корабельный гараж 1×1')
a.instance('Foundation','MA-G01-P01');a.instance('Portal','MA-G01-P02',loc=(0,-.40,.22));a.instance('Housing','MA-G01-P03',loc=(0,.20,.22));a.instance('Diagnostic','MA-R01-P05',loc=(0,.44,1.03))
connections=[{'parent_instance':'Foundation','parent_socket':'portal','child_instance':'Portal','child_socket':'root'},{'parent_instance':'Foundation','parent_socket':'housing','child_instance':'Housing','child_socket':'root'},{'parent_instance':'Housing','parent_socket':'service','child_instance':'Diagnostic','child_socket':'bottom'}]
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Compact garage node; Capacity512 means storage capacity, not ship count. No invented ship scale or animations.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.56),2.9,850)
write(FOLDER/'README.md',"""# MA-G01 — корабельный гараж 1×1

MilitaryArmor 1.3; garage-ship. Компактный защищённый гаражный узел: доковые направляющие, силовой портал с утопленным закрытым доступом, задний корпус с пониженной бронекрышей. Доступ обращён к -Y. Capacity512 — вместимость, не число кораблей. Масштаб кораблей и механика ворот не выдумывались.

Редактируемый MA-G01.blend; assembly.json — четыре стабильных экземпляра и три соединения. Три новые детали MA-G01-P01…P03, повторно использован MA-R01-P05 v1.0. composition-plan.md — выбор деталей; Previews/top.png и perspective.png — виды сверху и в объёме.

Процедурные PBR Armor/Ceramic/Titanium/Steel/Dark/Signal. Нет файловых текстур и UV-зависимости; эмиссия ограничена диагностикой. Статика, единичные масштабы, полные семантические sockets. Слои уплотнений и бронекожуха намеренно контактируют; портал накрывает переднюю кромку корпуса. Geometry gate каждой новой детали до сборки; независимое повторное открытие источников и сборки — validation.json.

BU условные, JSON — авторинг Blender. GLB не создавался. Игровая интеграция, коллайдеры и LOD не выполнялись.
""")
print('MA_G01_BUILT',flush=True)
