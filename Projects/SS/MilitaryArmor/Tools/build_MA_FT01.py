import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-FT01';FOLDER=ROOT/'Blocks'/BID

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
 world=bpy.data.worlds.new('Fuel tank review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
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
 check=inspect();m.save(mounts=mounts,notes='Static protected fuel-storage concept. Uniform procedural PBR. No file textures, UV dependency or animated mechanism. BU are not metres. No gameplay capacity specified.')
 p=ROOT/'Parts'/m.pid;d=json.loads((p/'part.json').read_text())
 d['attachment_areas']=[{'id':s['id']+'-seat','parent':'part','role':s['role'],'shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts]
 write(p/'part.json',d);write(p/'geometry-validation.json',check)
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.65,450)
 write(p/'README.md',f'# {m.pid} v1.0\n\n{m.title}. Editable source {m.pid}.blend; part.json lists materials, no emission, full logical sockets and attachment areas. Static, unit scale, procedural PBR, no file textures or UV dependency. Geometry gate passed before assembly (geometry-validation.json). Previews/top.png and perspective.png. No GLB.\n')

if '--assembly-only' not in sys.argv:
 m=Part('MA-FT01-P01','Fuel tank narrow armoured load frame')
 m.panel('Armoured keel',(0,0,.09),(1.8,3.6,.18),'Armor',.22,.007)
 m.panel('Pressure cradle',(0,.12,.23),(1.38,2.88,.16),'Dark',.20,.005)
 for x in [-.77,.77]:
  m.section('Swept protected shoulder',[(-1.64,x,.22,.20,.26,.04),(-1.15,x,.38,.24,.48,.05),(1.26,x,.38,.24,.48,.05),(1.64,x,.23,.20,.28,.04)],'Ceramic',.004)
 for y in [-1.55,1.55]:
  m.panel('Closed load end',(0,y,.27),(1.45,.28,.26),'Titanium',.10,.005)
 m.panel('Service interface gasket',(0,-1.43,.415),(.83,.68,.03),'Dark',.12,.003)
 # Flush visual interface; not a functional gameplay pipe.
 for x in [-.50,.50]:
  m.panel('Buried transfer cover',(x,-1.42,.425),(.14,.38,.04),'Titanium',.035,.002)
 finish(m,[mount('hull',(0,0,0),'MilitaryArmor.fuel-tank.hull'),mount('vessel',(0,.15,.25),'MilitaryArmor.fuel-tank.vessel'),mount('service',(0,-1.43,.43),'MilitaryArmor.service-cartridge.v1')])
 m=Part('MA-FT01-P02','Single sealed longitudinal faceted storage vessel')
 m.section('Monolithic sealed tank',[(-1.35,0,.56,.48,.48,.15),(-1.08,0,.56,1.24,1.10,.28),(.96,0,.56,1.24,1.10,.28),(1.31,0,.56,.48,.48,.15)],'Titanium',.004)
 m.panel('Protected dorsal spine',(0,-.05,1.105),(.23,2.16,.07),'Armor',.08,.003)
 for x in [-.24,.24]:
  m.panel('Inset longitudinal seam',(x,-.05,1.116),(.035,1.70,.018),'Dark',.008,.001)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.fuel-tank.vessel'),mount('band-front',(0,-.70,.56),'MilitaryArmor.fuel-tank.band'),mount('band-rear',(0,.65,.56),'MilitaryArmor.fuel-tank.band')])
 m=Part('MA-FT01-P03','Faceted armour restraint hoop')
 # Chamfered rectangular cross section follows the vessel, rather than a round pipe collar.
 outer=[(-.45,-.60),(.45,-.60),(.70,-.30),(.70,.30),(.45,.60),(-.45,.60),(-.70,.30),(-.70,-.30)]
 inner=[(-.34,-.56),(.34,-.56),(.64,-.27),(.64,.27),(.34,.56),(-.34,.56),(-.64,.27),(-.64,-.27)]
 verts=[]
 for y,loop in [(-.105,outer),(.105,outer),(-.105,inner),(.105,inner)]:verts.extend((x,y,z) for x,z in loop)
 faces=[]
 for i in range(8):
  j=(i+1)%8;faces.extend([(i,j,8+j,8+i),(16+j,16+i,24+i,24+j),(8+i,8+j,24+j,24+i),(j,i,16+i,16+j)])
 m.mesh('Cold ceramic pressure hoop',verts,faces,'Ceramic',.002)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.fuel-tank.band')])

a=Assembly(BID,'fuel-tank-1x2',[1,2],'Бак топлива 1×2 — визуальная заготовка')
a.instance('Frame','MA-FT01-P01');a.instance('Vessel','MA-FT01-P02',loc=(0,.15,.25));connections=[{'parent_instance':'Frame','parent_socket':'vessel','child_instance':'Vessel','child_socket':'root'}]
for label,y in [('front',-.70),('rear',.65)]:
 iid='Hoop-'+label;a.instance(iid,'MA-FT01-P03',loc=(0,.15+y,.81));connections.append({'parent_instance':'Vessel','parent_socket':'band-'+label,'child_instance':iid,'child_socket':'root'})
a.instance('Service','MA-R01-P05',loc=(0,-1.43,.43));connections.append({'parent_instance':'Frame','parent_socket':'service','child_instance':'Service','child_socket':'bottom'})
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual concept; no game XML','axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'One enclosed elongated storage vessel, two faceted restraint hoops, swept protective cradle and recessed service interface. No invented capacity, fuel properties or transfer mechanics. Tiny emission only on reused service status patch.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.70),4.8,850)
write(FOLDER/'README.md','''# MA-FT01 — бак топлива 1×2

MilitaryArmor 1.3. Каталог fuel-tank-1x2: визуальная заготовка без игрового XML. Одна вытянутая герметичная ёмкость с суженными торцами, два светлых гранёных силовых обруча, защищённая опорная рама и утопленный сервисный интерфейс. Силуэт отличается от наборных ячеек батареи и плоского радиатора. Ёмкость, свойства топлива и скорости передачи не задавались.

Редактируемый MA-FT01.blend. Три новые детали MA-FT01-P01/P02/P03, один готовый сервисный картридж MA-R01-P05 v1.0. Всего пять экземпляров, четыре полных соединения, единичные масштабы. Подбор — composition-plan.md.

Материалы Armor/Ceramic/Titanium/Dark — процедурный PBR, без файловых текстур и UV-зависимости. Единственная эмиссия — штатная диагностическая метка готового картриджа. Анимаций нет. Перекрытия обручей с корпусом и бронеплеч с основанием являются посадочными контактами. BU условны; метрический масштаб не задан.

Previews/top.png и perspective.png. Детали проверены до сборки (geometry-validation.json), исходники повторно открыты отдельным процессом (validation.json). GLB не создавался. Игровая интеграция, коллайдеры и LOD не выполнялись.
''')
print('MA_FT01_BUILT',flush=True)