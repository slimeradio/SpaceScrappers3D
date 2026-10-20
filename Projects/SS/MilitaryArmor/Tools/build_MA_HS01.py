"""Cargo source authoring; individual evaluated geometry gates; no GLB."""
import sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-HS01'; FOLDER=ROOT/'Blocks'/BID

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
 world=bpy.data.worlds.new('Radiator review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
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
 check=inspect();m.save(mounts=mounts,notes='Static heat-store authoring part; uniform procedural PBR. No file textures, UV dependency or animated mechanism. BU are not metres.')
 p=ROOT/'Parts'/m.pid;d=json.loads((p/'part.json').read_text())
 d['attachment_areas']=[{'id':s['id']+'-seat','parent':'part','role':s['role'],'shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts]
 write(p/'part.json',d);write(p/'geometry-validation.json',check)
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65,450)
 write(p/'README.md',f'# {m.pid} v1.0\n\n{m.title}. Редактируемый исходник {m.pid}.blend; part.json содержит материалы, эмиссию и полные логические крепления. Все масштабы единичные. Геометрия проверена до сборки: geometry-validation.json. Отдельные виды Previews/top.png и perspective.png. Статическая деталь, процедурный PBR, без файловых текстур и UV-зависимости. GLB не создавался.\n')



if '--assembly-only' not in sys.argv:
 m=Part('MA-HS01-P01','Protected thermal storage cradle and closed collectors')
 m.panel('Foundation',(0,0,.08),(1.8,1.8,.16),'Armor',.20,.008)
 m.panel('Recessed insulated bed',(0,0,.17),(1.44,1.55,.04),'Dark',.12,.003)
 for y in [-.76,.76]:
  m.panel('Closed thermal collector',(0,y,.28),(1.47,.25,.24),'Titanium',.07,.006)
  m.panel('Swept collector armor',(0,y,.405),(1.55,.26,.065),'Ceramic',.08,.004)
  m.panel('Inset collector identification',(0,y,.441),(.43,.14,.012),'Dark',.025,.001)
 mounts=[mount('hull',(0,0,0),'MilitaryArmor.heat-store.hull')]
 for j,x in enumerate([-.43,0,.43]):mounts.append(mount('cassette-'+str(j),(x,0,.19),'MilitaryArmor.heat-store.cassette'))
 for j,x in enumerate([-.79,.79]):mounts.append(mount('thermal-'+str(j),(x,-.075,.43),'MilitaryArmor.engine.thermal'))
 finish(m,mounts)
 m=Part('MA-HS01-P02','Sealed thermal storage cassette')
 m.panel('Thermal isolation seat',(0,0,.023),(.37,1.37,.046),'Dark',.065,.003)
 m.panel('Closed titanium vessel',(0,0,.18),(.35,1.34,.29),'Titanium',.075,.006)
 m.section('Faceted ceramic cassette shell',[(-.63,0,.28,.32,.21,.055),(-.43,0,.36,.35,.23,.055),(.43,0,.36,.35,.23,.055),(.63,0,.28,.32,.21,.055)],'Ceramic',.004)
 m.panel('Inset thermal spine',(0,0,.479),(.075,.79,.013),'Titanium',.019,.001)
 for y in [-.505,.505]:
  m.panel('Collector coupling',(0,y,.18),(.38,.17,.20),'Steel',.035,.004)
  m.panel('Dark coupling seal',(0,y,.296),(.25,.10,.027),'Dark',.022,.002)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.heat-store.cassette')])
a=Assembly(BID,'heat-store-1x1',[1,1],'Накопитель тепла 1×1 — визуальная заготовка')
a.instance('Cradle','MA-HS01-P01');connections=[]
for j,x in enumerate([-.43,0,.43]):
 iid='Cassette-'+str(j);a.instance(iid,'MA-HS01-P02',loc=(x,0,.19));connections.append({'parent_instance':'Cradle','parent_socket':'cassette-'+str(j),'child_instance':iid,'child_socket':'root'})
for j,x in enumerate([-.79,.79]):
 iid='Thermal-'+str(j);a.instance(iid,'MA-E01-P04',loc=(x,-.075,.43));connections.append({'parent_instance':'Cradle','parent_socket':'thermal-'+str(j),'child_instance':iid,'child_socket':'root'})
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual concept; no game XML','axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Closed protected heat-store concept. No invented capacity, temperature or gameplay behavior. BU physical scale unspecified. No emission.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.35),2.85,850)
write(FOLDER/'README.md',"""# MA-HS01 — накопитель тепла 1×1

MilitaryArmor 1.3. heat-store-1x1 — визуальная заготовка без игрового XML. Три закрытые термокассеты в защищённой раме, торцевые коллекторы и боковые термощитки. Без эмиссии, открытого ядра и анимаций. Теплоёмкость, температуры и игровая механика не задавались.

Редактируемый MA-HS01.blend. Две новые детали MA-HS01-P01/P02, повторно использованы два экземпляра MA-E01-P04 v1.0. Всего шесть экземпляров, пять соединений. Масштабы единичные, полные позы логических sockets и семантическая совместимость проверяются. composition-plan.md содержит анализ библиотеки до моделирования.

Процедурные PBR Armor/Ceramic/Titanium/Steel/Dark, без файловых текстур, UV-зависимости и эмиссии. geometry-validation.json каждой новой детали создан до сборки. validation.json — независимое повторное открытие трёх исходников и сборки. Контакты изоляционных опор, крышек и коллекторов намеренны.

Previews/top.png и perspective.png — сверху и в объёме. JSON описывает авторинг Blender. GLB не создавались; коллайдеры, LOD и игровая интеграция не выполнялись. BU не имеют установленного метрического масштаба.
""")
print('MA_HS01_BUILT',flush=True)