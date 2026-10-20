import sys,json,math,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,AXES,write
IDS=['MA-B01','MA-I01','MA-FG01']
def mount(i,pos,tag):
 return dict(id=i,role=tag,parent='part',position=list(pos),forward=[0,-1,0],up=[0,0,1],compatibility=[tag],restrictions='unit scale; full pose')
def inspect():
 out=[]; dep=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data)
  c=dict(mesh=o.name,nonmanifold=sum(not e.is_manifold for e in bm.edges),source_degenerate=sum(f.calc_area()<1e-10 for f in bm.faces),signed_volume=bm.calc_volume(signed=True),finite=all(math.isfinite(v) for p in bm.verts for v in p.co));bm.free()
  ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();c['triangles']=len(me.loop_triangles);c['evaluated_degenerate']=sum(t.area<1e-10 for t in me.loop_triangles);ev.to_mesh_clear();c['materials']=bool(o.material_slots) and all(s.material for s in o.material_slots)
  c['pass']=c['nonmanifold']==0 and c['source_degenerate']==0 and c['signed_volume']>0 and c['finite'] and c['evaluated_degenerate']==0 and c['materials'];out.append(c)
 r=dict(checks_passed=bool(out) and all(x['pass'] for x in out),meshes=out);assert r['checks_passed'],r
 return r

def preview(folder,target,scale,res=600,gray=False):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_x=res;s.render.resolution_y=res;s.render.resolution_percentage=100
 s.world=bpy.data.worlds.new('Review');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.06,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
 added=[];target=Vector(target)
 for loc,power,size in [((2,-5,8),1800,5),((-4,-1,5),1400,4),((3,5,6),2100,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;s.camera=cam;added.append(cam);(folder/'Previews').mkdir(exist_ok=True)
 for name,off in [('top',(0,0,8)),('perspective',(5,-7,6))]:
  cam.location=target+Vector(off);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(folder/'Previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
 if gray:
  # Use compositing luminance; preserve actual source material contrast.
  
  saved=[]
  for material in bpy.data.materials:
   if not material.use_nodes:continue
   shader=material.node_tree.nodes.get('Principled BSDF')
   if not shader:continue
   for key in ['Base Color','Emission Color']:
    value=shader.inputs[key].default_value[:];saved.append((shader,key,value));luma=.2126*value[0]+.7152*value[1]+.0722*value[2];shader.inputs[key].default_value=(luma,luma,luma,value[3])
  bg=s.world.node_tree.nodes['Background'].inputs[0];bg.default_value=(.045,.045,.045,1)
  cam.location=target+Vector((0,0,8));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(folder/'Previews'/'top-grayscale.png');bpy.ops.render.render(write_still=True)
  for shader,key,value in saved:shader.inputs[key].default_value=value
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 s.camera=None

def finish(p,sockets):
 bpy.context.view_layer.update();check=inspect();p.save(mounts=sockets,notes='Functional identity redesign 2.0; static editable part, no gameplay mechanics, procedural PBR; no UV/file texture dependency.')
 folder=ROOT/'Parts'/p.pid;d=json.loads((folder/'part.json').read_text());d['attachment_areas']=[dict(id=m['id']+'-area',shape='logical-point-plane',dimensions=[.01,.01],parent='part',position=m['position'],forward=m['forward'],up=m['up'],compatibility=m['compatibility'],allowed_rotations_degrees=[0],restrictions='unit scale, exact full socket pose') for m in sockets];write(folder/'part.json',d);write(folder/'geometry-validation.json',dict(**check,validated_before_assembly=True))
 lo=d['bounds_local']['min'];hi=d['bounds_local']['max'];preview(folder,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.55,400)
 write(folder/'README.md',f'# {p.pid} v2.0\n\n{p.title}. Редактируемый Blender; процедурные PBR-материалы и эмиссия перечислены в part.json. Полные логические крепления и области, единичный масштаб. Статика; UV и файловые текстуры не используются. Геометрия проверена немедленно до сборки (geometry-validation.json). Previews/top.png и perspective.png. GLB не создавался.\n')

plans={
'MA-B01':('Батарея 4×4','battery-4x4',[4,4],'Гребенчатый силуэт: семь узких энергомодулей, открытые промежутки и два силовых распределителя. Общего поддона, крупных крышек и сервисного картриджа нет.','Старые MA-B01-P01/P02/P03/P04: закрытая плита, широкие кассеты и бронеплечи дают грузовой силуэт; не использовать. MA-R01-P05 не нужен. Новые R2-P01 две опорные балки с посадками; R2-P02 узкий пакет энергопластин; R2-P03 защищённая силовая шина.'),
'MA-I01':('Грузовой отсек с верфью 2×1','cargo-2x1',[2,1],'Единый высокий грузовой объём, один крупный загрузочный люк, две направляющие и поперечные силовые рёбра. Прямоугольный цельный силуэт противопоставлен батарейной гребёнке.','MA-F01-P01/P03 и MA-I01-P01/P02/P03 изучены: рассчитаны на две кассеты и центральную крышку. Масштабирование сохранит неверную компоновку; новые R2-P01 единый корпус, R2-P02 широкий люк, R2-P03 грузовая направляющая. MA-R01-P05 не использовать.'),
'MA-FG01':('Машинное отделение 3×3','engine-room',[3,3],'Асимметричный технологический силуэт: высокий продольный барабан слева, поперечный коллектор сзади и две малые насосные головы справа, защищённые магистрали между ними. Нет сетки одинаковых крышек.','Прежние MA-FG01-P01/P02/P03/P04/P05 и MA-R01-P05 не соответствуют новой некассетной композиции; новые R2-P01 коллектор/силовая опора, R2-P02 большой барабан, R2-P03 малая насосная голова, R2-P04 защищённые магистрали. Размеры других цилиндрических деталей не соответствуют посадкам; единичный масштаб без скрытой переделки общих исходников.')}
for bid,(title,cid,grid,design,reuse) in plans.items():
 folder=ROOT/'Blocks'/bid;archive=ROOT/'Versions'/'FunctionalIdentity-before'/'Blocks'/bid
 if not archive.exists():
  shutil.copytree(folder,archive)
  write(archive/'ARCHIVE.md','# Архив до переделки\n\nСохранены старые исходники, метаданные и PNG. Относительные ../../Parts/ в архивном assembly.json относятся к прежнему местоположению Blocks/<ID>; исходные версии деталей остались неизменными в MilitaryArmor/Parts. Сам blend содержит вложенные копии геометрии и открывается самостоятельно.\n')
 write(folder/'composition-plan.md',f'# {bid} — план 2.0 до моделирования\n\nКаталог {cid}, сетка {grid[0]}×{grid[1]}; клетки не метры. {design}\n\nАнализ повторного использования: {reuse}\n\nСохранить оси +Z вверх, -Y вперёд, правую систему; BU условные. Все новые R2-детали v2.0 с единичным масштабом. Предыдущие детали не изменять. Каждая новая деталь проходит геометрический gate и отдельные previews до сборки. Сборка статическая; направление верфи/производства означает только назначение каталога, не выдуманную анимацию.\n')

if '--verify' not in sys.argv and '--assembly-only' not in sys.argv:
 p=Part('MA-B01-R2-P01','Раздельные силовые опоры батареи','2.0')
 for y in [-1.45,1.45]:
  p.panel('Narrow foundation beam',(0,y,.13),(3.72,.34,.26),'Armor',.1,.015)
 for x in [-1.62,1.62]:p.box('Transverse tie',(x,0,.10),(.16,3.05,.20),'Titanium',.012)
 sockets=[mount('root',(0,0,0),'MilitaryArmor.battery.hull')]
 for i,x in enumerate([-1.38,-.92,-.46,0,.46,.92,1.38]):sockets.append(mount('blade'+str(i),(x,0,.26),'MilitaryArmor.battery.blade'))
 for name,y in [('front',-1.51),('rear',1.51)]:sockets.append(mount(name,(0,y,.26),'MilitaryArmor.battery.bus'))
 finish(p,sockets)
 p=Part('MA-B01-R2-P02','Узкий энергонакопительный модуль','2.0')
 p.panel('Energy blade',(0,0,.42),(.28,2.59,.84),'Titanium',.09,.015)
 for y in [-.86,-.28,.30,.88]:p.panel('Separated ceramic dielectric',(0,y,.46),(.33,.50,.68),'Ceramic',.055,.009)
 p.box('Recessed longitudinal bus',(0,0,.867),(.10,2.30,.05),'Dark',.006)
 for y in [-1.21,1.21]:
  p.cyl('Protected power contact',(0,y,.91),.10,.13,'Steel',verts=12)
  p.box('Diagnostic notch',(0,y*.85,.889),(.075,.09,.018),'Signal',.002)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.battery.blade')])
 p=Part('MA-B01-R2-P03','Поперечная силовая шина с защищёнными клеммами','2.0')
 p.panel('Bus shield',(0,0,.27),(3.67,.33,.54),'Armor',.12,.012)
 p.box('Power rail',(0,0,.57),(3.24,.15,.10),'Steel',.01)
 for x in [-1.38,-.92,-.46,0,.46,.92,1.38]:p.panel('Insulated terminal',(x,0,.68),(.24,.30,.18),'Ceramic',.045,.006)
 for x in [-1.68,1.68]:p.panel('End connector shield',(x,0,.43),(.31,.43,.69),'Titanium',.09,.012)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.battery.bus')])

 p=Part('MA-I01-R2-P01','Цельный силовой корпус грузового отсека','2.0')
 p.panel('Single cargo pressure volume',(0,0,.53),(3.66,1.61,1.06),'Armor',.20,.016)
 for x in [-1.27,0,1.27]:
  p.panel('Transverse armored rib',(x,0,.55),(.16,1.72,1.10),'Titanium',.06,.01)
 for y in [-.79,.79]:p.box('Recessed cargo side channel',(0,y,.59),(2.97,.025,.19),'Dark',.004)
 p.panel('Large loading aperture seal',(0,0,1.09),(2.96,1.39,.09),'Dark',.16,.009)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.cargo.hull'),mount('hatch',(0,0,1.13),'MilitaryArmor.cargo.wide-hatch'),mount('railF',(0,-.80,.16),'MilitaryArmor.cargo.rail'),mount('railB',(0,.80,.16),'MilitaryArmor.cargo.rail')])
 p=Part('MA-I01-R2-P02','Единый бронированный загрузочный люк','2.0')
 p.panel('One full-size loading hatch',(0,0,.09),(2.87,1.29,.18),'Ceramic',.17,.012)
 for x in [-1.13,1.13]:
  p.panel('Flush transverse latch',(x,0,.198),(.17,.90,.036),'Titanium',.04,.004)
  for y in [-.40,.40]:p.box('Recessed locking shoe',(x,y,.226),(.24,.13,.025),'Dark',.003)
 p.box('Long hatch access seam',(0,-.39,.186),(1.70,.025,.012),'Titanium',.002)
 for x in [-.69,.69]:p.box('Cargo latch index',(x,-.51,.187),(.14,.025,.014),'Signal',.002)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.cargo.wide-hatch')])
 p=Part('MA-I01-R2-P03','Наружная грузовая направляющая','2.0')
 p.panel('Cargo handling rail',(0,0,.15),(3.87,.18,.30),'Steel',.07,.008)
 for x in [-1.74,1.74]:p.panel('Rail end bumper',(x,0,.26),(.29,.30,.52),'Ceramic',.06,.009)
 for x in [-1.10,0,1.10]:p.box('Rail coupling foot',(x,0,-.04),(.26,.26,.16),'Titanium',.01)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.cargo.rail')])

 p=Part('MA-FG01-R2-P01','Распределительный коллектор машинного отделения','2.0')
 p.panel('Rear transverse collector',(0,.99,.31),(2.72,.59,.62),'Armor',.14,.015)
 p.panel('Left engine bearer',(-.73,-.17,.13),(.86,2.50,.26),'Titanium',.12,.012)
 p.panel('Right pump bearer',(.72,-.24,.12),(.78,2.12,.24),'Titanium',.11,.012)
 for x in [-1.03,-.38,.35,1.03]:
  p.cyl('Collector protected valve',(x,.99,.68),.15,.16,'Steel',verts=12)
  p.cyl('Collector valve cap',(x,.99,.78),.10,.06,'Dark',verts=12)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.engine-room.hull'),mount('drum',(-.73,-.22,.26),'MilitaryArmor.engine-room.drum'),mount('pumpF',(.72,-.86,.24),'MilitaryArmor.engine-room.pump'),mount('pumpB',(.72,.13,.24),'MilitaryArmor.engine-room.pump'),mount('pipes',(0,0,0),'MilitaryArmor.engine-room.pipes')])
 p=Part('MA-FG01-R2-P02','Продольный технологический барабан','2.0')
 p.cyl('Main machine vessel',(0,0,.62),.59,1.84,'Titanium',axis='Y',verts=16)
 for y in [-.84,-.40,.40,.84]:p.cyl('Armored circumferential collar',(0,y,.62),.64,.14,'Ceramic',axis='Y',verts=16)
 for y in [-.96,.96]:
  p.cyl('Protected end head',(0,y,.62),.43,.17,'Armor',axis='Y',verts=12)
  p.cyl('Axial coupling',(0,y*1.08,.62),.20,.12,'Steel',axis='Y',verts=12)
 p.panel('Dorsal mechanism cover',(0,0,1.25),(.44,1.43,.14),'Armor',.12,.012)
 p.box('Recessed status slit',(0,-.53,1.325),(.23,.10,.014),'Signal',.002)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.engine-room.drum')])
 p=Part('MA-FG01-R2-P03','Малая насосная голова','2.0')
 p.cyl('Pump body',(0,0,.28),.32,.56,'Armor',verts=12)
 p.cyl('Pump neck',(0,0,.63),.20,.15,'Steel',verts=12)
 p.cyl('Star head',(0,0,.77),.29,.15,'Ceramic',verts=8)
 p.panel('Pump side manifold',(.23,0,.32),(.26,.35,.39),'Titanium',.07,.009)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.engine-room.pump')])
 p=Part('MA-FG01-R2-P04','Защищённые технологические магистрали','2.0')
 # Square-section enclosed routes have deliberate mechanical continuity at junctions.
 for x in [-.13,.40,1.14]:
  p.box('Longitudinal protected line',(x,-.05,.46),(.15,1.88,.15),'Steel',.015)
 p.box('Transverse front manifold',(.51,-.97,.46),(1.42,.15,.15),'Titanium',.015)
 for x,y in [(-.13,.88),(.40,.88),(1.14,.88),(.40,-.86),(1.14,.13)]:
  p.cyl('Closed transfer riser',(x,y,.66),.11,.41,'Titanium',verts=12)
 for y in [-.63,.04,.66]:p.panel('Line protective bridge',(.50,y,.59),(1.48,.20,.12),'Armor',.04,.009)
 finish(p,[mount('root',(0,0,0),'MilitaryArmor.engine-room.pipes')])

def assemble(bid):
 title,cid,grid,design,reuse=plans[bid];a=Assembly(bid,cid,grid,title);connections=[]
 def add(i,suffix,pos=(0,0,0),sock=None):
  a.instance(i,bid+'-R2-'+suffix,loc=pos)
  if sock:connections.append(dict(parent_instance='Structure',parent_socket=sock,child_instance=i,child_socket='root'))
 add('Structure','P01')
 if bid=='MA-B01':
  for i,x in enumerate([-1.38,-.92,-.46,0,.46,.92,1.38]):add('EnergyBlade'+str(i),'P02',(x,0,.26),'blade'+str(i))
  add('FrontPowerBus','P03',(0,-1.51,.26),'front');add('RearPowerBus','P03',(0,1.51,.26),'rear')
 elif bid=='MA-I01':
  add('LoadingHatch','P02',(0,0,1.13),'hatch');add('FrontCargoRail','P03',(0,-.80,.16),'railF');add('RearCargoRail','P03',(0,.80,.16),'railB')
 else:
  add('MainMachineDrum','P02',(-.73,-.22,.26),'drum');add('ForwardPump','P03',(.72,-.86,.24),'pumpF');add('RearPump','P03',(.72,.13,.24),'pumpB');add('ProtectedTransferLines','P04',(0,0,0),'pipes')
 folder=ROOT/'Blocks'/bid;bpy.context.view_layer.update()
 write(folder/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=bid,version='2.0',title=title,catalog_id=cid,catalog_grid=grid,axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes=design+' Static authoring source; no new gameplay mechanics.'))
 bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(bid+'.blend')))
 preview(folder,(0,0,.65),5.0 if bid=='MA-B01' else 4.9 if bid=='MA-I01' else 4.2,800,True)
 write(folder/'README.md',f'# {bid} — {title}, v2.0\n\n{design}\n\nИсходник {bid}.blend, состав assembly.json, предварительный анализ composition-plan.md. {len(a.instances)} экземпляров, {len(set(x["part_id"] for x in a.instances))} новых R2-деталей v2.0; прежние общие источники не изменены. Архив предыдущей версии: ../../Versions/FunctionalIdentity-before/Blocks/{bid}.\n\nПроизводные Previews/top.png, perspective.png, top-grayscale.png. Проверки геометрии каждой детали выполнены до сборки. Независимое повторное открытие деталей и сборки, полные позы креплений, версии, материалы и единичные масштабы — validation.json.\n\nПроцедурные PBR-материалы, без файловых текстур и зависимости от UV. Статика без выдуманных анимаций. BU условные, сетка {grid[0]}×{grid[1]} не метры. Закрытые соединения, уплотнения, защитные кожухи и посадки намеренно касаются/перекрывают сопряжённые компоненты. GLB не создавался, игровая интеграция не выполнялась.\n')

if '--verify' not in sys.argv:
 for bid in IDS:assemble(bid)
else:
 for bid in IDS:
  folder=ROOT/'Blocks'/bid;a=json.loads((folder/'assembly.json').read_text());parts={};results=[]
  for pid in sorted(set(x['part_id'] for x in a['instances'])):
   d=json.loads((ROOT/'Parts'/pid/'part.json').read_text());parts[pid]=d;bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts'/pid/d['source']));results.append(dict(id=pid,geometry=inspect(),version=d['version']));assert d['version']=='2.0'
   for m in d['mounts']:
    o=bpy.data.objects.get('socket.'+m['id']);assert o and (o.location-Vector(m['position'])).length<1e-6
  bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')));geo=inspect();instances={i['id']:i for i in a['instances']}
  for i in a['instances']:
   o=bpy.data.objects.get(i['id']);assert o and o['part_id']==i['part_id'] and o['part_version']==i['version'];assert (o.location-Vector(i['translation'])).length<1e-6;assert all(abs(v-1)<1e-6 for v in o.scale);assert Path(folder/i['source']).exists();assert o.parent.name==i['parent']
  connection_results=[]
  for c in a['connections']:
   pi=instances[c['parent_instance']];ci=instances[c['child_instance']];pm=next(m for m in parts[pi['part_id']]['mounts'] if m['id']==c['parent_socket']);cm=next(m for m in parts[ci['part_id']]['mounts'] if m['id']==c['child_socket']);po=bpy.data.objects[pi['id']];co=bpy.data.objects[ci['id']]
   position_error=(po.matrix_world@Vector(pm['position'])-co.matrix_world@Vector(cm['position'])).length
   forward_error=(po.matrix_world.to_3x3()@Vector(pm['forward'])-co.matrix_world.to_3x3()@Vector(cm['forward'])).length;up_error=(po.matrix_world.to_3x3()@Vector(pm['up'])-co.matrix_world.to_3x3()@Vector(cm['up'])).length;compatible=bool(set(pm['compatibility'])&set(cm['compatibility']));assert max(position_error,forward_error,up_error)<1e-6 and compatible
   connection_results.append(dict(**c,position_error=position_error,forward_error=forward_error,up_error=up_error,semantic_compatibility=compatible))
  write(folder/'validation.json',dict(id=bid,version='2.0',checks_passed=True,independent_reopen=True,source_parts=results,assembly_geometry=geo,connections=connection_results,instance_count=len(a['instances']),stable_instance_ids=True,unit_scale=True,dependency_paths_resolved=True,no_glb_generated=True,game_validation=False))
  print('VERIFIED',bid,flush=True)
