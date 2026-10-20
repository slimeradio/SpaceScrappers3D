"""Cargo source authoring; individual evaluated geometry gates; no GLB."""
import sys, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-H01'; FOLDER=ROOT/'Blocks'/BID

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
 check=inspect();m.save(mounts=mounts,notes='Static radiator authoring part; uniform procedural PBR. No file textures, UV dependency or animated mechanism. BU are not metres.')
 p=ROOT/'Parts'/m.pid;d=json.loads((p/'part.json').read_text())
 d['attachment_areas']=[{'id':s['id']+'-seat','parent':'part','role':s['role'],'shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts]
 write(p/'part.json',d);write(p/'geometry-validation.json',check)
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65,450)
 write(p/'README.md',f'# {m.pid} v1.0\n\n{m.title}. Редактируемый исходник {m.pid}.blend; part.json содержит материалы, эмиссию и полные логические крепления. Все масштабы единичные. Геометрия проверена до сборки: geometry-validation.json. Отдельные виды Previews/top.png и perspective.png. Статическая деталь, процедурный PBR, без файловых текстур и UV-зависимости. GLB не создавался.\n')



if '--assembly-only' not in sys.argv:
 m=Part('MA-H01-P01','Armoured radiator frame and protected manifolds')
 m.panel('Foundation',(0,0,.08),(1.8,3.6,.16),'Armor',.22,.009)
 m.panel('Panel well',(0,0,.17),(1.43,2.68,.04),'Dark',.16,.004)
 m.panel('Central protected manifold',(0,0,.235),(.14,2.82,.15),'Titanium',.04,.005)
 for y in [-1.52,1.52]:
  m.panel('Closed terminal manifold',(0,y,.235),(1.50,.32,.17),'Titanium',.09,.006)
  m.panel('Terminal armoured cap',(0,y,.34),(1.47,.28,.06),'Ceramic',.08,.004)
 for x in [-.79,.79]:
  m.section('Swept load shoulder',[(-1.69,x,.18,.20,.20,.04),(-1.25,x,.25,.21,.34,.04),(1.25,x,.25,.21,.34,.04),(1.69,x,.18,.20,.20,.04)],'Ceramic',.005)
 mounts=[mount('hull',(0,0,0),'MilitaryArmor.radiator.hull')]
 for col,x in enumerate([-.34,.34]):
  for row,y in enumerate([-.93,-.31,.31,.93]):mounts.append(mount('tile-%d-%d'%(col,row),(x,y,.20),'MilitaryArmor.radiator.tile'))
 for side,x in enumerate([-.76,.76]):
  for j,y in enumerate([-.62,.62]):mounts.append(mount('thermal-%d-%d'%(side,j),(x,y,.37),'MilitaryArmor.engine.thermal'))
 finish(m,mounts)
 m=Part('MA-H01-P02','Recessed nonemissive radiative tile')
 m.panel('Titanium tile support',(0,0,.035),(.60,.56,.07),'Titanium',.045,.003)
 m.panel('Dark radiative ceramic',(0,0,.078),(.54,.50,.016),'Dark',.037,.002)
 for x in [-.277,.277]:m.panel('Protected tile rim',(x,0,.083),(.024,.46,.025),'Ceramic',.007,.001)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.radiator.tile')])
a=Assembly(BID,'radiator-1x2',[1,2],'Радиатор 1×2 — визуальная заготовка')
a.instance('Frame','MA-H01-P01');connections=[]
for col,x in enumerate([-.34,.34]):
 for row,y in enumerate([-.93,-.31,.31,.93]):
  iid='Tile-%d-%d'%(col,row);a.instance(iid,'MA-H01-P02',loc=(x,y,.20));connections.append({'parent_instance':'Frame','parent_socket':'tile-%d-%d'%(col,row),'child_instance':iid,'child_socket':'root'})
for side,x in enumerate([-.76,.76]):
 for j,y in enumerate([-.62,.62]):
  iid='Thermal-%d-%d'%(side,j);a.instance(iid,'MA-E01-P04',loc=(x,y,.37));connections.append({'parent_instance':'Frame','parent_socket':'thermal-%d-%d'%(side,j),'child_instance':iid,'child_socket':'root'})
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual concept; no game XML','axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Static concept radiator; no invented heat mechanics or gameplay values. BU physical scale unspecified. No emission.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.32),4.7,850)
write(FOLDER/'README.md',"""# MA-H01 — радиатор 1×2

MilitaryArmor 1.3. radiator-1x2 — визуальная заготовка без игрового XML. Статическое радиационное поле из восьми широких тёмных плиток, защищённые боковые термопанели, центральная силовая магистраль и закрытые торцевые коллекторы. Без эмиссии и раскладных механизмов. Числа теплоотвода и игровые характеристики не задавались.

Редактируемый MA-H01.blend. Две новые детали MA-H01-P01/P02; четыре экземпляра готовой MA-E01-P04 v1.0. Всего 13 экземпляров, 12 соединений, масштабы единичные. composition-plan.md — подбор деталей.

Процедурные PBR Armor/Ceramic/Titanium/Dark, без файловых текстур и UV-зависимости. Полные позы логических sockets; JSON — авторинг Blender. Прилегание плиток к раме, бронеплеч к основанию и коллекторов к магистрали намеренное. Рама предоставляет engine.thermal seats без правки старой детали.

Previews/top.png и perspective.png — виды сверху и в объёме. Новые детали проходят geometry-validation.json до сборки; validation.json — независимое повторное открытие всех источников и сборки. GLB не создавался. Игровой экспорт, коллайдеры, LOD и интеграция не выполнялись; BU не имеют метрического масштаба.
""")
print('MA_H01_BUILT',flush=True)
