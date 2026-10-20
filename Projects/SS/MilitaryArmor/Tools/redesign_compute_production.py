"""Functional silhouette redesign; standalone geometry gates precede assembly. No exports."""
import bpy,bmesh,json,sys,math,shutil,os
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
IDS=['MA-HS01','MA-C01','MA-F01','MA-F02']

class Model(Part):
 def __init__(self,pid,title):super().__init__(pid,title,'2.0')
 def finish(self,o,name,mat,bevel=0):return super().finish(o,name,mat,0)

def socket(i,p,tag):
 return {'id':i,'role':tag.split('.')[-1],'parent':'part','position':list(p),'forward':[0,-1,0],'up':[0,0,1],'compatibility':[tag],'allowed_scale':[1,1,1]}

def inspect():
 bpy.context.view_layer.update();out=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  r={'mesh':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)};bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();r.update(evaluated_triangles=len(me.loop_triangles),zero_area_triangles=sum(t.area<1e-10 for t in me.loop_triangles),finite=all(math.isfinite(c) for v in me.vertices for c in v.co),materials_resolved=bool(o.material_slots) and all(s.material for s in o.material_slots));ev.to_mesh_clear()
  r['pass']=not r['nonmanifold_edges'] and not r['zero_area_faces'] and r['signed_volume']>0 and not r['zero_area_triangles'] and r['finite'] and r['materials_resolved'];out.append(r)
 assert out and all(r['pass'] for r in out),str(out)
 return {'checks_passed':True,'validated_before_assembly':True,'meshes':out}

def preview(folder,target,scale,res=650,gray=False):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=res;scene.render.resolution_y=res;scene.render.resolution_percentage=100
 world=bpy.data.worlds.new('Review world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.06,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
 target=Vector(target);added=[]
 for loc,power,size in [((2,-5,8),1400,5),((-4,-1,5),1000,4),((3,5,6),1700,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 (folder/'Previews').mkdir(parents=True,exist_ok=True)
 for name,off in [('top',(0,0,8)),('perspective',(5,-7,6))]:
  cam.location=target+Vector(off);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/'Previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
 if gray:
  clay=bpy.data.materials.new('Temporary uniform gray silhouette');clay.use_nodes=True;bs=clay.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.32,.32,1);bs.inputs['Roughness'].default_value=.7
  scene.view_layers[0].material_override=clay
  cam.location=target+Vector((0,0,8));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/'Previews'/'top-grayscale.png');bpy.ops.render.render(write_still=True);scene.view_layers[0].material_override=None
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def finish(m,mounts):
 if '--heat-correction' in sys.argv and m.pid=='MA-HS01-R2-P03':return
 check=inspect();m.save(mounts=mounts,notes='Functional identity revision 2.0. Static editable geometry, procedural PBR, no file textures, no animation. Physical BU scale unspecified. No GLB.')
 p=ROOT/'Parts'/m.pid;meta=json.loads((p/'part.json').read_text());meta['attachment_areas']=[{'id':s['id']+'-seat','parent':'part','role':s['role'],'shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts];write(p/'part.json',meta);write(p/'geometry-validation.json',check)
 lo=meta['bounds_local']['min'];hi=meta['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.55,420)
 write(p/'README.md',f'# {m.pid} v2.0\n\n{m.title}. Самостоятельный редактируемый Blender-исходник; геометрия проверена ДО сборки (geometry-validation.json). Полные крепления и процедурные PBR-материалы в part.json; файловых текстур и UV-зависимости нет. Статика. Единичный масштаб. BU условные. Previews/top.png и perspective.png. GLB не создавался.\n')

def archive_and_plan():
 plans={
 'MA-HS01':('Накопитель тепла 1×1','Цельный цилиндрический термосердечник на изолированных опорах, три массивных кольца теплоизоляции с глубокими промежутками, без прямоугольных кассет и крышек; отдельный П-образный тепловой коллектор. Габарит 1.8×1.8 BU соответствует прежней визуальной сетке, BU не метры.','Старые MA-HS01-P01/P02 — тонкая рама и три аккумуляторные кассеты; не подходят новой массивной форме. MA-E01-P04 — боковой щиток двигателя, не тепловой коллектор. Создать новые MA-HS01-R2-P01 несущий изолированный канал, P02 массивное 16-гранное теплоизоляционное кольцо (3 экземпляра), P03 П-образный коллектор. Старые источники не меняются.'),
 'MA-C01':('Программируемый блок 2×1','Асимметричная L-образная вычислительная стойка, матрица 3×2 мелких низких кассет, задняя коммуникационная спина и отдельный наклонный диагностический пульт. Ступенчатый верхний силуэт, а не закрытый грузовой ящик.','MA-C01-P01/P02/P03 и MA-R01-P05 проверены: закрытый ящик и бронеплечи противоречат заданию. Масштабированием не получить L-образную вычислительную архитектуру. Создать MA-C01-R2-P01 L-образную spine, P02 сменную вычислительную кассету (6 экземпляров), P03 наклонный узел диагностики/разъёмов. Старые источники не менять.'),
 'MA-F01':('Производственный блок 2×1','Направленная технологическая линия: широкий приём слева, круглая защищённая рабочая камера в центре, узкая выдача справа. Поперечный мост на двух опорах, камера остаётся видна сверху. Это художественная интерпретация производства без добавления игровой механики.','MA-F01-P01/P02/P03/P04 и общий MA-R01-P05 проверены: два одинаковых прямоугольных люка с поддоном не подходят. Создать MA-F01-R2-P01 направленное основание с приёмом/выдачей, P02 круглая камера, P03 технологический мост. Эти новые детали повторно использовать в MA-F02 без изменения.'),
 'MA-F02':('Производственный блок базы 2×1','Семейная производственная линия MA-F01, собственная ступенчатая сервисная башня базы на задней стороне. Отличие не требует ломать узнаваемость производственного семейства.','Повторно использовать MA-F01-R2-P01/P02/P03 v2.0, единичный масштаб, те же socket poses. MA-F02-P01 v1.0 — низкий закрытый service bay; по силуэту не подходит. Создать MA-F02-R2-P01 ступенчатый сервисный узел с защищёнными подключениями. Базовая линия геометрически не пересобирается.')}
 for bid,(title,shape,reuse) in plans.items():
  src=ROOT/'Blocks'/bid;dst=ROOT/'Versions'/'FunctionalIdentity-before'/'Blocks'/bid
  if not dst.exists():
   shutil.copytree(src,dst)
   am=json.loads((dst/'assembly.json').read_text())
   for i in am['instances']:i['source']=os.path.relpath(ROOT/'Parts'/i['part_id']/(i['part_id']+'.blend'),dst).replace('\\','/')
   am['archive_note']='Original Blender source and part library preserved; source paths adjusted for archive location only.';write(dst/'assembly.json',am)
   write(dst/'archive-note.md','Исходный .blend скопирован без изменения. Старые Parts остаются по прежним ID/версиям, встроенные Blender-данные сохранены. Только относительные source-ссылки assembly.json исправлены для нового расположения архива. Старый validation — историческое свидетельство.\n')
  write(src/'composition-plan.md',f'# {bid} — {title}, переделка v2.0\n\n{shape}\n\nПроверка библиотеки и решение ДО моделирования: {reuse}\n\nОси +Z вверх, -Y вперёд, правая система. Все экземпляры в единичном масштабе. Новые детали проходят source/evaluated gate и сохраняются отдельно до сборки. Общий восьмигранный картридж не используется. GLB не создавать.\n')

def make_heat():
 tag='MilitaryArmor.r2.thermal'
 m=Model('MA-HS01-R2-P01','Deep insulated heat-store bed')
 m.box('Dense thermal spine',(0,0,.24),(1.12,1.55,.36),'Titanium')
 m.cyl('Continuous insulated thermal core',(0,0,.83),.49,1.5,'Dark',axis='Y',verts=24)
 for x in [-.61,.61]:m.section('Stepped insulated runner',[(-.88,x,.18,.26,.3,.06),(-.64,x,.19,.31,.34,.07),(.64,x,.19,.31,.34,.07),(.88,x,.18,.26,.3,.06)],'Armor')
 mounts=[socket('hull',(0,0,0),tag+'.hull')]
 for j,y in enumerate([-.57,0,.57]):mounts.append(socket('section-'+str(j),(0,y,.21),tag+'.section'))
 mounts.append(socket('collector',(0,0,0),tag+'.collector'));finish(m,mounts)
 m=Model('MA-HS01-R2-P02','Massive insulated thermal section with broad faceted shoulders')
 m.ring('Massive faceted insulation ring',(0,0,.62),.78,.50,.38,axis='Y',mat='Armor',verts=16)
 for y in [-.175,.175]:m.ring('Insulation ceramic edge',(0,y,.62),.79,.53,.035,axis='Y',mat='Ceramic',verts=16)
 for x in [-.68,.68]:m.box('Thermal ring saddle',(x,0,.16),(.18,.36,.26),'Titanium')
 finish(m,[socket('root',(0,0,0),tag+'.section')])
 m=Model('MA-HS01-R2-P03','Protected U-shaped thermal collector')
 for x in [-.86,.86]:
  m.box('Collector riser',(x,0,.51),(.13,1.5,.18),'Steel')
  for y in [-.57,0,.57]:m.cyl('Thermal neck',(x*.9,y,.5),.10,.21,'Titanium',axis='X',verts=16)
 m.box('Collector return',(0,.77,.5),(1.8,.16,.18),'Titanium')
 for x in [-.5,.5]:m.panel('Return insulation',(x,.77,.61),(.66,.24,.10),'Armor',.06)
 finish(m,[socket('root',(0,0,0),tag+'.collector')])

def make_compute():
 tag='MilitaryArmor.r2.compute'
 m=Model('MA-C01-R2-P01','L-shaped compute backplane with elevated left tower')
 m.panel('Communication backbone',(0,.59,.27),(3.5,.41,.46),'Armor',.13)
 m.panel('Inset rear bus',(0,.58,.51),(2.8,.18,.035),'Titanium',.04)
 for x in [-1.2,-.65,-.1]:
  for y in [-.35,.15]:m.box('Compute cassette support',(x,y,.13),(.46,.41,.16),'Titanium')
 m.panel('Left compute tower',(-1.56,-.08,.52),(.35,1.30,.89),'Armor',.08)
 m.panel('Diagnostic plinth',(1.05,-.06,.17),(.97,1.1,.22),'Armor',.13)
 mounts=[socket('hull',(0,0,0),tag+'.hull')]
 for j,(x,y) in enumerate([(x,y) for x in [-1.2,-.65,-.1] for y in [-.35,.15]]):mounts.append(socket('blade-'+str(j),(x,y,.21),tag+'.blade'))
 mounts.append(socket('diagnostic',(1.05,-.09,.28),tag+'.diagnostic'));finish(m,mounts)
 m=Model('MA-C01-R2-P02','Compact removable compute cassette with recessed die and connectors')
 m.panel('Compute cassette shield',(0,0,.18),(.44,.36,.34),'Ceramic',.055)
 m.box('Backplane contact',(0,.16,.1),(.30,.09,.16),'Titanium')
 m.panel('Recessed compute die',(0,0,.36),(.28,.21,.025),'Dark',.035)
 m.box('Recessed diagnostic slot',(0,-.185,.18),(.25,.018,.12),'Dark')
 m.box('Compute status',(.1,-.198,.2),(.045,.015,.025),'Optic')
 finish(m,[socket('root',(0,0,0),tag+'.blade')])
 m=Model('MA-C01-R2-P03','Sloped diagnostic console and recessed programming connectors')
 m.section('Tapered control console',[(-.53,0,.21,.83,.39,.08),(-.2,0,.36,.83,.65,.08),(.42,0,.36,.74,.65,.08)],'Armor')
 m.panel('Inset diagnostic surface',(0,.13,.705),(.57,.45,.025),'Dark',.055)
 for j in range(4):m.box('Diagnostic register',(-.17+j*.11,.13,.722),(.055,.30,.009),'Steel')
 m.panel('Deep connector trough',(0,-.31,.445),(.59,.2,.025),'Dark',.035)
 for x in [-.20,-.07,.07,.20]:m.box('Recessed data connector',(x,-.31,.464),(.065,.12,.02),'Titanium')
 m.box('Program link indicator',(.27,.1,.723),(.025,.25,.013),'Signal')
 finish(m,[socket('root',(0,0,0),tag+'.diagnostic')])

def make_production():
 tag='MilitaryArmor.r2.production'
 m=Model('MA-F01-R2-P01','Directed production bed with asymmetric intake and delivery zones')
 m.panel('Central process bed',(-.2,0,.13),(1.65,1.52,.22),'Armor',.20)
 m.panel('Wide intake zone',(-1.22,0,.15),(1.05,1.58,.18),'Titanium',.16)
 m.panel('Narrow delivery zone',(1.2,0,.15),(1.12,.93,.18),'Titanium',.12)
 for y in [-.65,.65]:m.box('Protected intake side',(-1.25,y,.35),(.91,.16,.34),'Ceramic')
 for j,x in enumerate([-1.53,-1.30,-1.07]):m.box('Inset intake separator',(x,0,.26),(.06,1.13,.07),'Steel')
 for y in [-.39,.39]:m.box('Delivery guide',(1.21,y,.30),(1.08,.11,.25),'Ceramic')
 for x in [.88,1.15,1.42]:m.box('Delivery segmentation',(x,0,.26),(.045,.62,.06),'Steel')
 mounts=[socket('hull',(0,0,0),tag+'.hull'),socket('chamber',(-.12,0,.24),tag+'.chamber'),socket('bridge',(.25,0,0),tag+'.bridge'),socket('base-service',(.99,.67,.2),tag+'.base-service')];finish(m,mounts)
 m=Model('MA-F01-R2-P02','Circular protected processing chamber with nested pressure shells')
 m.cyl('Pressure vessel',(0,0,.31),.59,.6,'Titanium',verts=24)
 m.ring('Heavy lower shielding',(0,0,.16),.69,.59,.24,mat='Armor',verts=24)
 m.ring('Faceted chamber shielding',(0,0,.5),.68,.51,.30,mat='Ceramic',verts=24)
 m.cyl('Inset working cover',(0,0,.59),.49,.12,'Dark',verts=24)
 m.ring('Protected process rim',(0,0,.66),.5,.39,.08,mat='Steel',verts=24)
 m.cyl('Central process seal',(0,0,.62),.32,.08,'Titanium',verts=24)
 for x in [-.64,.64]:m.box('Process throat',(x,0,.21),(.23,.5,.22),'Armor')
 finish(m,[socket('root',(0,0,0),tag+'.chamber')])
 m=Model('MA-F01-R2-P03','Transverse technological bridge with open-sided chamber access')
 for y in [-.77,.77]:
  m.panel('Bridge foot',(0,y,.18),(.4,.22,.3),'Armor',.04)
  m.box('Closed bridge upright',(0,y,.69),(.24,.18,.88),'Titanium')
 m.panel('High technological crosshead',(0,0,1.14),(.37,1.72,.24),'Ceramic',.07)
 m.box('Crosshead inset',(0,0,1.27),(.16,1.12,.025),'Titanium')
 m.box('Small process index',(0,-.37,1.29),(.07,.2,.015),'Signal')
 finish(m,[socket('root',(0,0,0),tag+'.bridge')])
 m=Model('MA-F02-R2-P01','Stepped base production service tower')
 m.panel('Service tower lower shell',(0,0,.36),(1.16,.27,.7),'Armor',.07)
 m.panel('Tall service spine',(-.29,0,.77),(.49,.31,.64),'Ceramic',.065)
 m.panel('Lower service spine',(.27,0,.59),(.47,.31,.40),'Ceramic',.065)
 for x,z in [(-.29,1.11),(.27,.81)]:m.box('Recessed service crown',(x,0,z),(.26,.17,.025),'Titanium')
 for x in [-.38,-.12,.12,.38]:m.box('Protected rear connection',(x,-.155,.39),(.1,.05,.25),'Dark')
 finish(m,[socket('root',(0,0,0),tag+'.base-service')])

def assemble(bid):
 old=json.loads((ROOT/'Versions'/'FunctionalIdentity-before'/'Blocks'/bid/'assembly.json').read_text());a=Assembly(bid,old['catalog_id'],old['catalog_grid'],old['title']);con=[]
 if bid=='MA-HS01':
  a.instance('ThermalBed','MA-HS01-R2-P01')
  for j,y in enumerate([-.57,0,.57]):
   iid='ThermalSection-'+str(j);a.instance(iid,'MA-HS01-R2-P02',loc=(0,y,.21));con.append({'parent_instance':'ThermalBed','parent_socket':'section-'+str(j),'child_instance':iid,'child_socket':'root'})
  a.instance('HeatCollector','MA-HS01-R2-P03');con.append({'parent_instance':'ThermalBed','parent_socket':'collector','child_instance':'HeatCollector','child_socket':'root'});target=(0,0,.82);scale=3.15
 elif bid=='MA-C01':
  a.instance('Backplane','MA-C01-R2-P01')
  for j,(x,y) in enumerate([(x,y) for x in [-1.2,-.65,-.1] for y in [-.35,.15]]):
   iid='ComputeBlade-'+str(j);a.instance(iid,'MA-C01-R2-P02',loc=(x,y,.21));con.append({'parent_instance':'Backplane','parent_socket':'blade-'+str(j),'child_instance':iid,'child_socket':'root'})
  a.instance('Diagnostics','MA-C01-R2-P03',loc=(1.05,-.09,.28));con.append({'parent_instance':'Backplane','parent_socket':'diagnostic','child_instance':'Diagnostics','child_socket':'root'});target=(0,.04,.5);scale=4.65
 else:
  a.instance('ProductionBed','MA-F01-R2-P01');a.instance('ProcessChamber','MA-F01-R2-P02',loc=(-.12,0,.24));a.instance('TechnologicalBridge','MA-F01-R2-P03',loc=(.25,0,0))
  con=[{'parent_instance':'ProductionBed','parent_socket':'chamber','child_instance':'ProcessChamber','child_socket':'root'},{'parent_instance':'ProductionBed','parent_socket':'bridge','child_instance':'TechnologicalBridge','child_socket':'root'}]
  if bid=='MA-F02':a.instance('BaseServiceTower','MA-F02-R2-P01',loc=(.99,.67,.2));con.append({'parent_instance':'ProductionBed','parent_socket':'base-service','child_instance':'BaseServiceTower','child_socket':'root'})
  target=(0,0,.64);scale=4.8
 folder=ROOT/'Blocks'/bid;meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':bid,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':old.get('catalog_status','catalog definition; authoring model only'),'axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'notes':'Functional silhouette redesign v2.0. Static authoring interpretation only; no new mechanics or gameplay parameters. Old source archived. No GLB.'};write(folder/'assembly.json',meta)
 bpy.context.scene.frame_end=1;bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(bid+'.blend')));preview(folder,target,scale,800,True)
 write(folder/'README.md',f'# {bid} — {a.title}, v2.0\n\nНовая индивидуальная конструкция, описанная в composition-plan.md. Редактируемый исходник {bid}.blend; состав и точные версии в assembly.json.\n\nДетали: '+', '.join(sorted(set(i['part_id']+' v'+i['version'] for i in a.instances)))+'. Каждая новая деталь прошла геометрический gate ДО сборки, сохранены самостоятельные top/perspective.\n\nСборка: Previews/top.png, perspective.png и top-grayscale.png (временный единый серый материал только при рендере, материалы исходника сохранены). validation.json создаёт независимая повторная проверка исходников и сборки. Все экземпляры единичного масштаба; полные позы и семантическая совместимость sockets проверены.\n\nВерсия до переделки: ../../Versions/FunctionalIdentity-before/Blocks/'+bid+'/. Старые детали не изменены. Статика, без анимаций, файловых текстур и UV-зависимости; процедурные PBR-материалы. BU условные, не метры. GLB не создавались. Игровая интеграция, коллайдеры и LOD не выполнялись. Контакты опор, оболочек и защищённых подключений намеренны.\n')
 print('ASSEMBLED',bid,flush=True)

if __name__=='__main__':
 if '--heat-correction' in sys.argv:
  make_heat();assemble('MA-HS01');sys.exit(0)
 if '--assemblies-only' not in sys.argv:
  archive_and_plan();make_heat();make_compute();make_production()
 for bid in IDS:assemble(bid)
