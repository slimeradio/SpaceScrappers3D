"""Cargo source authoring; individual evaluated geometry gates; no GLB."""
import sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-SP01'; FOLDER=ROOT/'Blocks'/BID

def mount(i,p,tag):
 return {'id':i,'role':tag.split('.')[-1],'parent':'part','position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':[tag],'allowed_scale':[1,1,1]}

def inspect():
 checks=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  c={'mesh':o.name,'source_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'source_zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'source_inconsistent_normals':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'signed_volume':bm.calc_volume(signed=True)};bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();c.update(evaluated_triangles=len(me.loop_triangles),zero_area_triangles=sum(t.area<1e-10 for t in me.loop_triangles),finite=all(math.isfinite(v) for p in me.vertices for v in p.co),materials_resolved=bool(o.material_slots) and all(s.material for s in o.material_slots));ev.to_mesh_clear()
  c['pass']=not c['source_nonmanifold_edges'] and not c['source_zero_area_faces'] and not c['source_inconsistent_normals'] and c['signed_volume']>0 and not c['zero_area_triangles'] and c['finite'] and c['materials_resolved'];checks.append(c)
 result={'checks_passed':bool(checks) and all(c['pass'] for c in checks),'meshes':checks,'validated_before_assembly':True}
 assert result['checks_passed'],str(result)
 return result

def preview(folder,target,scale,res=650):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=res;scene.render.resolution_y=res;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Photovoltaic review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
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
 check=inspect();m.save(mounts=mounts,notes='Static photovoltaic cassette authoring part; uniform procedural PBR. No file textures, UV dependency or animated mechanism. BU are not metres.')
 p=ROOT/'Parts'/m.pid;d=json.loads((p/'part.json').read_text())
 d['attachment_areas']=[{'id':s['id']+'-seat','parent':'part','role':s['role'],'shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts]
 write(p/'part.json',d);write(p/'geometry-validation.json',check)
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65,450)
 write(p/'README.md',f'# {m.pid} v1.0\n\n{m.title}. Редактируемый исходник {m.pid}.blend; part.json содержит материалы, эмиссию и полные логические крепления. Все масштабы единичные. Геометрия проверена до сборки: geometry-validation.json. Отдельные виды Previews/top.png и perspective.png. Статическая деталь, процедурный PBR, без файловых текстур и UV-зависимости. GLB не создавался.\n')



m=Part('MA-SP01-P01','Protected photovoltaic cassette with discrete collecting cells')
pv=bpy.data.materials.new('Photovoltaic');pv.use_nodes=True
shader=pv.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.016,.043,.105,1);shader.inputs['Metallic'].default_value=.45;shader.inputs['Roughness'].default_value=.26
m.mats['Photovoltaic']=pv
m.panel('Cassette substrate',(0,0,.025),(.60,.56,.05),'Titanium',.045,.002)
m.panel('Insulating collector field',(0,0,.058),(.548,.508,.016),'Dark',.032,.001)
for x in [-.283,.283]:m.panel('Pale lateral protector',(x,0,.079),(.025,.468,.05),'Ceramic',.008,.001)
for y in [-.257,.257]:m.panel('Pale transverse protector',(0,y,.074),(.528,.022,.042),'Ceramic',.006,.001)
for col,x in enumerate([-.17,0,.17]):
 for row,y in enumerate([-.156,0,.156]):
  m.panel('PV-cell-%d-%d'%(col,row),(x,y,.078),(.158,.144,.020),'Photovoltaic',.016,.001)
  for dx in [-.039,.039]:m.box('Cell contact track',(x+dx,y,.089),(.003,.124,.002),'Steel',0)
for y in [-.232,.232]:m.box('Protected collector bus',(0,y,.080),(.49,.006,.008),'Titanium',0)
finish(m,[mount('root',(0,0,0),'MilitaryArmor.radiator.tile')])
p=ROOT/'Parts'/m.pid;meta=json.loads((p/'part.json').read_text());meta['mechanical_interface_note']='radiator.tile denotes reuse of the existing cassette seat, not thermal gameplay; photovoltaic part provides no invented electricity values';write(p/'part.json',meta)
a=Assembly(BID,'solar-1x2',[1,2],'Солнечная панель 1×2 — визуальная заготовка')
a.instance('Carrier','MA-H01-P01');connections=[]
for col,x in enumerate([-.34,.34]):
 for row,y in enumerate([-.93,-.31,.31,.93]):
  iid='Collector-%d-%d'%(col,row);a.instance(iid,'MA-SP01-P01',loc=(x,y,.20));connections.append({'parent_instance':'Carrier','parent_socket':'tile-%d-%d'%(col,row),'child_instance':iid,'child_socket':'root','semantic':'mechanical cassette seat reused for photovoltaic collector'})
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual concept; no game XML','axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Static photovoltaic concept. No invented power or illumination mechanics; no deployment. Reused carrier unchanged at unit scale. No emission. Intentional layered cassette contacts.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.22),4.7,850)
write(FOLDER/'README.md','''# MA-SP01 — солнечная панель 1×2

MilitaryArmor 1.3. Каталог solar-1x2: визуальная заготовка без игрового XML. Восемь кассет по девять отдельных холодно-синих фотоэлектрических ячеек с тонкими контактными дорожками и защищёнными шинами. Светлая броневая рама и графитовый несущий корпус. Отличие от MA-H01: сетка отдельных светоприёмных ячеек и коллекторные дорожки; боковые термопанели радиатора отсутствуют.

MA-SP01.blend — редактируемая сборка. Новая деталь MA-SP01-P01 v1.0 ×8; готовая MA-H01-P01 v1.0 ×1 используется без изменения. Девять экземпляров, восемь соединений, все масштабы единичные. Полные позиции и ориентации sockets сохранены. Название radiator.tile обозначает совместимое механическое посадочное место, а не игровую тепловую механику. Неиспользуемые sockets рамы допустимы.

Процедурный PBR: Photovoltaic, Ceramic, Titanium, Dark, Steel. Файловых текстур, UV-зависимости, эмиссии и анимаций нет. Номинальная мощность и механика освещения не придуманы. Слои кассеты и примыкание дорожек намеренные, все меши замкнутые.

composition-plan.md — выбор деталей; geometry-validation.json новой детали получен до сборки. validation.json — независимое повторное открытие источников и сборки. Previews/top.png и perspective.png — виды сверху и в объёме. BU условные, физический масштаб не согласован. GLB, игровой экспорт, LOD, коллайдеры и интеграция не выполнялись.
''')
print('MA_SP01_BUILT',flush=True)
