"""MilitaryArmor functional identity revision: four independent source families; no exports."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES

def socket(sid,pos,tag):
 return dict(id=sid,role=tag.split('.')[-1],parent='part',position=list(pos),forward=[0,-1,0],up=[0,0,1],compatibility=[tag],allowed_scale=[1,1,1])

def gate():
 bpy.context.view_layer.update();checks=[];deps=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  c=dict(mesh=o.name,nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),inconsistent_edges=sum(e.is_manifold and not e.is_contiguous for e in bm.edges),zero_area_faces=sum(f.calc_area()<1e-10 for f in bm.faces),signed_volume=bm.calc_volume(signed=True));bm.free()
  ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();c.update(evaluated_triangles=len(me.loop_triangles),evaluated_zero_area_triangles=sum(t.area<1e-10 for t in me.loop_triangles),finite=all(math.isfinite(c) for v in me.vertices for c in v.co),materials_resolved=bool(me.materials) and all(m is not None for m in me.materials));ev.to_mesh_clear()
  c['pass']=c['nonmanifold_edges']==c['inconsistent_edges']==c['zero_area_faces']==c['evaluated_zero_area_triangles']==0 and c['signed_volume']>0 and c['finite'] and c['materials_resolved'];checks.append(c)
 result=dict(checks_passed=bool(checks) and all(c['pass'] for c in checks),meshes=checks,validated_before_assembly=True)
 assert result['checks_passed'],str(result)
 return result

def preview(folder,assembly=False):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=6
 scene.render.resolution_x=scene.render.resolution_y=720 if assembly else 420;scene.render.resolution_percentage=100
 pts=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' for v in o.bound_box]
 low=Vector([min(p[i] for p in pts) for i in range(3)]);high=Vector([max(p[i] for p in pts) for i in range(3)]);target=(low+high)/2;scale=max(high-low)*1.4
 world=bpy.data.worlds.new('Temporary source review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6;scene.world=world
 added=[]
 for offset,power in [((1,-2,3),1500),((-2,-1,2),1200),((1,2,3),1800)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(offset)*scale*.7);o=bpy.context.object;o.data.energy=power*scale*scale/15;o.data.size=scale;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
 (folder/'Previews').mkdir(parents=True,exist_ok=True)
 for name,off in [('top',(0,0,8)),('perspective',(5,-7,6))]:
  cam.location=target+Vector(off)*scale;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/'Previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
 if assembly:
  # Neutral clay override evaluates recognition without any source color/emission cues.
  grey=bpy.data.materials.new('TEMP neutral grey');grey.use_nodes=True;grey.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.34,.34,.34,1);grey.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65
  scene.view_layers[0].material_override=grey;cam.location=target+Vector((0,0,8))*scale;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/'Previews'/'top-grayscale.png');bpy.ops.render.render(write_still=True);scene.view_layers[0].material_override=None;bpy.data.materials.remove(grey)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None

def finish(m,sockets):
 # Tiny edge relief preserves exact planar silhouettes without collapsed bevel triangles.
 for o in m.coll.objects:
  for mod in o.modifiers:
   if mod.type=='BEVEL':mod.width=min(mod.width,.001)
 check=gate();m.save(mounts=sockets,notes='Functional identity v2.0. Static procedural PBR; no file textures or UV dependency. No animation or gameplay mechanism. BU conditional.')
 folder=ROOT/'Parts'/m.pid;data=json.loads((folder/'part.json').read_text())
 data['attachment_areas']=[dict(id=s['id']+'-seat',parent='part',role=s['role'],shape='logical-point-plane',dimensions=[.08,.08],position=s['position'],forward=s['forward'],up=s['up'],compatibility=s['compatibility'],allowed_scale=[1,1,1],allowed_rotations_degrees=[0]) for s in sockets]
 write(folder/'part.json',data);write(folder/'geometry-validation.json',check)
 write(folder/'README.md',f'# {m.pid} v2.0\n\n{m.title}. Самостоятельный редактируемый {m.pid}.blend; процедурные PBR, материалы и эмиссия перечислены в part.json. Файловых текстур и UV-зависимости нет. Статичная деталь: анимаций нет. Полные логические крепления и области, unit scale, +Z вверх, -Y вперёд; BU условны. geometry-validation.json получен до включения в блок. Previews/top.png, perspective.png. GLB не создаётся.\n')
 preview(folder)

def plan(bid,title,rows):
 write(ROOT/'Blocks'/bid/'composition-plan.md',f'# {bid} — план функциональной переделки 2.0\n\n{title}. Оси +Z вверх, -Y вперёд; unit scale; BU условные. Каталожная сетка не равна метрам. Никаких новых игровых механизмов или анимаций.\n\n| Узел | Проверенный существующий кандидат | Решение и причина |\n|---|---|---|\n'+rows+'\n\nСначала самостоятельные детали R2 v2.0: исходник, материалы, полные sockets, проверка source/evaluated mesh и два превью. Затем экземпляры в сборке. Старые Parts не изменяются. Архив исходного блока: ../../Versions/FunctionalIdentity-before/Blocks/'+bid+'/; его исторические ссылки README рассчитаны от исходного Blocks/'+bid+', неизменённые старые Parts сохранены по прежним путям. Источники Blender содержат встроенную геометрию и материалы. GLB не создаётся.\n')

def assemble(bid,instances,description):
 folder=ROOT/'Blocks'/bid;old=json.loads((folder/'assembly.json').read_text());a=Assembly(bid,old['catalog_id'],old['catalog_grid'],old['title']);connections=[]
 for iid,pid,loc in instances:a.instance(iid,pid,loc=loc)
 base=instances[0][0]
 for iid,pid,loc in instances[1:]:connections.append(dict(parent_instance=base,parent_socket=iid,child_instance=iid,child_socket='root'))
 bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update();gate()
 data=dict(schema='MilitaryArmor.BlenderAuthoring/1',id=bid,version='2.0',title=old['title'],catalog_id=old['catalog_id'],catalog_grid=old['catalog_grid'],axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes=description)
 if bid in ['MA-H01','MA-SP01']:data['catalog_status']='visual concept; no game XML'
 write(folder/'assembly.json',data);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(bid+'.blend')))
 preview(folder,True)
 write(folder/'README.md',f'# {bid} — функциональная переделка 2.0\n\n{description}\n\nРедактируемый {bid}.blend. Все детали — отдельные неизменяемые источники Parts/*-R2-P*/ v2.0; состав, версии, полные позы и совместимость logical sockets: assembly.json / part.json. Старые детали сохранены. Сетка каталога {old["catalog_grid"]}; BU условны, +Z вверх, -Y вперёд, правая система. Масштабы экземпляров единичные. Статичная конструкция, анимаций нет.\n\nПроцедурные PBR без файловых текстур и UV-зависимости. Геометрия каждого источника проверена ДО сборки. validation.json — независимое повторное открытие источников и сборки, source/evaluated geometry, версии, ссылки, полные позы и совместимость sockets. Виды Previews/top.png, perspective.png; top-grayscale.png — нейтральный clay override, исходные материалы не изменены.\n\nПрилегание вложенных оболочек, тонких облицовок и опор намеренное. Полые пространства между секциями открыты. Исторический блок сохранён в Versions/FunctionalIdentity-before/Blocks/{bid}; старые Parts сохранены по исходным путям. Новые GLB не создавались. Игровая интеграция, коллайдеры и LOD не выполнялись.\n')

def radiator():
 bid='MA-H01';tag='MilitaryArmor.r2.radiator.fin'
 plan(bid,'Радиатор 1×2: гребёнка пространственных излучающих лопастей вокруг узкого продольного коллектора', '| Коллектор | MA-H01-P01 v1.0: широкий поддон и общая рама solar | Новая MA-H01-R2-P01: узкая магистраль, торцевые коллекторы, без поддона |\n| Излучающая поверхность | MA-H01-P02 / MA-E01-P04: закрытые плоские кассеты | Новая MA-H01-R2-P02: единая поперечная тонкая лопасть, открытые промежутки, 9 unit instances |')
 m=Part('MA-H01-R2-P01','Narrow protected radiator collector with transverse fin seats','2.0')
 m.panel('Collector keel',(0,0,.16),(.33,3.54,.32),'Titanium',.10,.003)
 m.panel('Upper closed manifold',(0,0,.37),(.23,3.36,.16),'Ceramic',.07,.003)
 for y in [-1.65,1.65]:
  m.panel('Return header',(0,y,.28),(.72,.30,.30),'Armor',.09,.003)
  for x in [-.21,.21]:m.cyl('Closed return coupling',(x,y,.46),.065,.12,'Steel',verts=16)
 for y in [-1.35,1.35]:m.panel('Underframe hull shoe',(0,y,.055),(.65,.35,.11),'Armor',.08,.003)
 seats=[socket('hull',(0,0,0),'MilitaryArmor.r2.radiator.hull')]
 for i in range(9):seats.append(socket(f'Fin-{i}',(0,-1.20+i*.30,.27),tag))
 finish(m,seats)
 m=Part('MA-H01-R2-P02','Swept transverse radiating blade with raised edge ribs','2.0')
 points=[(-.90,-.075),(-.62,-.13),(-.20,-.09),(.20,-.09),(.62,-.13),(.90,-.075),(.90,.075),(.62,.13),(.20,.09),(-.20,.09),(-.62,.13),(-.90,.075)]
 m.slab('Two sided radiative blade',points,0,.34,'Dark',.001)
 for x in [-.86,-.57,.57,.86]:m.box('Vertical radiation rib',(x,0,.185),(.024,.15,.39),'Titanium',.001)
 m.panel('Collector interface',(0,0,.19),(.27,.20,.38),'Steel',.03,.001)
 finish(m,[socket('root',(0,0,0),tag)])
 assemble(bid,[('Collector','MA-H01-R2-P01',(0,0,0))]+[(f'Fin-{i}','MA-H01-R2-P02',(0,-1.20+i*.30,.27)) for i in range(9)],'Радиатор: открытая гребёнка девяти высоких поперечных излучающих лопастей и узкий продольный коллектор. Зубчатый контур и глубокие сквозные промежутки отличают его от сплошного тонкого солнечного поля. Без эмиссии. Визуальная заготовка без игрового XML; параметры теплоотвода не задавались.')

def solar():
 bid='MA-SP01';tag='MilitaryArmor.r2.solar.field'
 plan(bid,'Солнечная панель 1×2: тонкое цельное фотоэлектрическое поле со скошенными торцами на двух поперечных опорах', '| Опоры | MA-H01-P01 v1.0: тяжёлая радиаторная рама | Новая MA-SP01-R2-P01: две лёгкие поперечины и нижняя узкая спина; общий корпус с радиатором убран |\n| Фотоэлектрическое поле | MA-SP01-P01 v1.0: мелкая кассета 0.6×0.56 | Новая MA-SP01-R2-P02: тонкое сплошное поле 1.8×3.6 со скошенными торцами и 44 ячейками; без эмиссии |')
 m=Part('MA-SP01-R2-P01','Twin solar truss shoes and narrow underside backbone','2.0')
 m.box('Underside backbone',(0,0,.09),(.16,2.85,.18),'Titanium',.003)
 for y in [-1.0,1.0]:
  m.panel('Hull shoe',(0,y,.045),(.40,.44,.09),'Armor',.09,.003)
  m.box('Slender crossbeam',(0,y,.20),(1.56,.075,.09),'Steel',.003)
  for x in [-.64,.64]:m.box('Field support',(x,y,.25),(.10,.12,.11),'Titanium',.003)
 finish(m,[socket('hull',(0,0,0),'MilitaryArmor.r2.solar.hull'),socket('Photovoltaic-field',(0,0,.30),tag)])
 m=Part('MA-SP01-R2-P02','Single thin photovoltaic sail with tapered terminals','2.0')
 m.panel('Thin chamfered substrate',(0,0,.026),(1.80,3.60,.052),'Titanium',.36,.001)
 # Large contiguous surface, small cell seams instead of separate heavy cassettes.
 m.panel('Continuous dielectric field',(0,0,.059),(1.70,3.48,.014),'Dark',.34,.001)
 for row in range(12):
  y=-1.43+row*.26
  for col in range(4):
   x=-.585+col*.39
   if abs(y)>1.3 and abs(x)>.5:continue
   o=m.panel('Nonemissive photovoltaic cell',(x,y,.073),(.371,.242,.016),'Optic',.018,.001)
   # Optic reused as passive surface: no emissive shader for solar.
   m.mats['Optic'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=0
   for dx in [-.105,0,.105]:m.box('Fine collector trace',(x+dx,y,.083),(.007,.22,.003),'Steel',.0003)
 for x in [-.85,.85]:m.box('Thin edge protection',(x,0,.072),(.035,2.86,.058),'Ceramic',.001)
 finish(m,[socket('root',(0,0,0),tag)])
 assemble(bid,[('Solar-truss','MA-SP01-R2-P01',(0,0,0)),('Photovoltaic-field','MA-SP01-R2-P02',(0,0,.30))],'Солнечная панель: единое тонкое поле пассивных фотоэлементов, скошенные торцы, тонкая кромка и две поперечные опоры под полем. Сплошной спокойный силуэт противопоставлен открытой гребёнке радиатора. Без эмиссии и раскладных механизмов. Визуальная заготовка без игрового XML, мощность не задавалась.')

def reactor():
 bid='MA-R01';tag='MilitaryArmor.r2.reactor.vessel'
 plan(bid,'Реактор 4×4: центральная цельная камера, концентрическое экранирование и радиальные силовые связи', '| Основание | MA-R01-P01 v1.0: квадратное шасси | Новая MA-R01-R2-P01: кольцевой низкий экран с восемью радиальными опорами, круговой силуэт |\n| Камера | MA-R01-P02 v1.0 / MA-R01-P05: прежний корпус с главной восьмигранной крышкой | Новая MA-R01-R2-P02: высокая закрытая ступенчатая камера, кольца и радиальные рёбра. Общий картридж не используется |')
 m=Part('MA-R01-R2-P01','Annular reactor shield and eight radial load braces','2.0')
 m.ring('Massive continuous outer shield',(0,0,.38),3.35,2.62,.50,mat='Armor',verts=64)
 m.ring('Pale shielding crown',(0,0,.67),3.26,2.82,.17,mat='Ceramic',verts=64)
 m.cyl('Sealed containment floor',(0,0,.14),2.83,.28,'Titanium',verts=64)
 for i in range(8):
  angle=i*math.pi/4;d=Vector((math.cos(angle),math.sin(angle),0))
  m.stripe('Radial buttress',d*1.60+Vector((0,0,.40)),d*3.52+Vector((0,0,.18)),.27,'Steel')
  center=d*3.24+Vector((0,0,.20));o=m.panel('Radial outer shield foot',center,(.68,.62,.40),'Ceramic',.13,.003)
  # Panels have baked coordinates; rebase before local orientation.
  for v in o.data.vertices:v.co-=center
  o.location=center;o.rotation_euler.z=angle
 finish(m,[socket('hull',(0,0,0),'MilitaryArmor.r2.reactor.hull'),socket('Containment-vessel',(0,0,.28),tag)])
 m=Part('MA-R01-R2-P02','Sealed axial reactor chamber with concentric shielding bands','2.0')
 m.cyl('Whole central containment drum',(0,0,.91),1.80,1.82,'Titanium',verts=64)
 m.cyl('Upper sealed pressure dome',(0,0,1.88),1.53,.28,'Ceramic',verts=64)
 m.cyl('Central integral closure',(0,0,2.08),1.18,.12,'Armor',verts=64)
 for z,r in [(.20,1.98),(.58,1.91),(1.20,1.91),(1.64,1.98)]:m.ring('Continuous circumferential shield',(0,0,z),r,1.77,.15,mat='Ceramic',verts=64)
 for i in range(12):
  angle=i*math.pi/6;d=Vector((math.cos(angle),math.sin(angle),0))
  o=m.box('Axial containment rib',d*1.78+Vector((0,0,.93)),(.18,.22,1.60),'Steel',.003);o.rotation_euler.z=angle
  if i%3==0:
   o=m.box('Recessed diagnostic index',d*1.883+Vector((0,0,.91)),(.018,.085,.28),'Signal',.001);o.rotation_euler.z=angle
 finish(m,[socket('root',(0,0,0),tag)])
 assemble(bid,[('Annular-shield','MA-R01-R2-P01',(0,0,0)),('Containment-vessel','MA-R01-R2-P02',(0,0,.28))],'Реактор: высокая цельная цилиндрическая камера в концентрическом кольцевом экране, восемь радиальных силовых опор и вертикальные рёбра удержания. Центральная камера доминирует в силуэте; повторяющиеся грузовые коробки и общая сервисная крышка исключены. Бирюзовая эмиссия ограничена четырьмя малыми диагностическими индексами. Внешняя модель не задаёт топливо или новые игровые параметры.')

def auction():
 bid='MA-S01';tag='MilitaryArmor.r2.auction.console'
 plan(bid,'Аукцион 1×1: направленный консольный терминал, широкий наклонный интерфейс как главный объём', '| Опора | MA-N01-P01 / MA-S01-P02: квадратное шасси и бронеплечи | Новая MA-S01-R2-P01: узкая задняя стойка и расходящиеся передние опоры; форма терминала вместо ящика |\n| Интерфейс | MA-S01-P01: низкий сервисный интерфейс | Новая MA-S01-R2-P02: большой наклонный защищённый дисплей с нижней панелью; общий картридж MA-R01-P05 не используется |')
 m=Part('MA-S01-R2-P01','Directional terminal pedestal with open forward support forks','2.0')
 m.panel('Rear anchoring shoe',(0,.52,.12),(.84,.62,.24),'Armor',.16,.003)
 m.section('Sloped cantilever neck',[(.12,0,.48,.37,.76,.05),(.67,0,.63,.54,.96,.08)],'Titanium',.003)
 for x in [-.55,.55]:
  m.stripe('Open angled support',(x,-.73,.10),(x*.4,.46,.33),.14,'Steel')
  m.panel('Forward hull pad',(x,-.70,.08),(.32,.39,.16),'Armor',.08,.003)
 finish(m,[socket('hull',(0,0,0),'MilitaryArmor.r2.auction.hull'),socket('Interface-console',(0,-.08,.78),tag)])
 m=Part('MA-S01-R2-P02','Wide inclined protected auction interface and input apron','2.0')
 # Form a sloped screen plane rising towards the rear; orientation stays built into standalone geometry.
 shell=m.panel('Wide shielded display body',(0,0,.07),(1.72,1.13,.15),'Ceramic',.18,.003);shell.rotation_euler.x=math.radians(23)
 inset=m.panel('Deep continuous interface recess',(0,-.016,.155),(1.48,.85,.035),'Dark',.10,.001);inset.rotation_euler.x=math.radians(23)
 # Coherent screen slab with broad outlined interface areas, no fake text.
 face=m.panel('Main trading display',(0,.00,.185),(1.31,.68,.018),'Optic',.045,.001);face.rotation_euler.x=math.radians(23)
 m.mats['Optic'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.32
 for x in [-.63,.63]:m.panel('Edge tactile control',(x,-.57,-.10),(.16,.23,.07),'Titanium',.04,.001)
 m.panel('Input apron',(0,-.64,-.14),(1.28,.25,.09),'Armor',.07,.001)
 for x in [-.36,0,.36]:m.panel('Recessed input zone',(x,-.65,-.087),(.26,.14,.012),'Dark',.025,.001)
 finish(m,[socket('root',(0,0,0),tag)])
 assemble(bid,[('Pedestal','MA-S01-R2-P01',(0,0,0)),('Interface-console','MA-S01-R2-P02',(0,-.08,.78))],'Блок аукциона базы: широкий наклонный интерфейс доминирует над открытой передней развилкой опор и узкой задней консольной стойкой. Отчётливая направленность -Y и Т-образный силуэт сверху, без грузовой крышки и бронеплеч. Только умеренная эмиссия интерфейса; без надписей и фиктивных торговых данных. Модель не меняет условия появления рынка или игровые правила.')

if __name__=='__main__':
 targets=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['MA-H01','MA-SP01','MA-R01','MA-S01']
 for bid,fn in [('MA-H01',radiator),('MA-SP01',solar),('MA-R01',reactor),('MA-S01',auction)]:
  if bid in targets:fn();print('BUILT',bid,flush=True)
