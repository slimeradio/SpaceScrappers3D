import sys, json, math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
BID='MA-D01'
FOLDER=ROOT/'Blocks'/BID

def socket(i,pos,role):
 return dict(id=i,node='socket.'+i,parent=None,role=role,position=list(pos),forward=[0,-1,0],up=[0,0,1],compatibility=['MilitaryArmor.drill.'+role],allowed_scale=[1,1,1])

def check_scene():
 rows=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free()
  dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
  zero=sum(t.area<1e-10 for t in me.loop_triangles);finite=all(math.isfinite(c) for v in me.vertices for c in v.co);tri=len(me.loop_triangles)
  assert bad==0 and vol>1e-9 and zero==0 and finite and len(o.data.materials)>0,(o.name,bad,vol,zero)
  rows.append(dict(object=o.name,nonmanifold=bad,signed_volume=vol,evaluated_triangles=tri,zero_area=zero,finite=finite))
  ev.to_mesh_clear()
 assert rows
 return rows

def preview(folder,scale,center):
 a=object.__new__(Assembly);a.bid=BID
 before=set(bpy.data.objects)
 a.review(folder/'Previews'/'perspective.png',view=(6,-9,7),target=center,scale=scale,resolution=720)
 for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
 a.review(folder/'Previews'/'top.png',view=(0,center[1],12),target=center,scale=scale,resolution=720)
 for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)

def finish(p,mounts,points=None):
 gate=check_scene()
 p.save(mounts=mounts,points=points,notes='MilitaryArmor mechanical drill visual authoring; static rest pose; unit-scale only; procedural PBR, no UV or file textures; no gameplay contract.')
 folder=ROOT/'Parts'/p.pid
 meta=json.loads((folder/'part.json').read_text())
 meta['project']='SS';meta['style']='MilitaryArmor'
 meta['attachment_areas']=[dict(id='root-plane',parent=None,role=mounts[0]['role'],shape='logical-plane',dimensions=[.04,.04],position=mounts[0]['position'],forward=[0,-1,0],up=[0,0,1],compatibility=mounts[0]['compatibility'],allowed_scale=[1,1,1],allowed_rotations_degrees=[0])]
 write(folder/'part.json',meta);write(folder/'geometry-validation.json',dict(passed=True,checked_before_assembly=True,objects=gate))
 bounds=meta['bounds_local'];center=[(a+b)/2 for a,b in zip(bounds['min'],bounds['max'])];scale=max(b-a for a,b in zip(bounds['min'],bounds['max']))*1.3
 preview(folder,scale,center)

p=Part('MA-D01-P01','Open twin-rail drill load frame')
# Two separated rails; no universal octagonal base.
for s in [-1,1]:
 p.section('Load rail '+str(s),[(-1.0,s*.64,.22,.24,.42,.06),(1.95,s*.64,.22,.30,.42,.07),(2.55,s*.48,.22,.24,.42,.06)],'Armor',.018)
 p.section('Rail ceramic upper '+str(s),[(-.82,s*.64,.47,.19,.08,.02),(1.82,s*.64,.47,.23,.08,.02),(2.43,s*.49,.47,.17,.08,.02)],'Ceramic',.009)
 p.stripe('Diagonal spindle brace '+str(s),(s*.64,-.82,.38),(s*.35,-.60,.9),.16,'Titanium')
 p.panel('Aft hull attachment '+str(s),(s*.48,2.38,.18),(.40,.38,.30),'Titanium')
p.box('Aft transverse beam',(0,2.34,.20),(1.23,.27,.35),'Dark',.02)
p.box('Motor cradle transverse beam',(0,1.15,.26),(1.3,.36,.35),'Dark',.02)
p.ring('Front spindle support',(0,-.73,.95),.46,.28,.34,'Y','Ceramic')
p.box('Protected lower collector',(0,-.35,.23),(.66,.56,.24),'Titanium',.025)
finish(p,[socket('hull',(0,0,0),'hull'),socket('drive',(0,1.2,.65),'drive'),socket('cutter',(0,-1.03,.95),'cutter')])

p=Part('MA-D01-P02','Sealed reduction drive and short spindle')
p.section('Reduction casing',[(-.62,0,.18,.93,.96,.19),(.36,0,.28,1.05,1.16,.22),(.91,0,.14,.82,.86,.18)],'Armor',.025)
p.panel('Aft drive maintenance shell',(0,.56,.84),(.65,.51,.10),'Ceramic',.16)
for s in [-1,1]:
 p.cyl('Closed reduction bearing '+str(s),(s*.52,.04,.25),.36,.12,'Titanium','X',16)
 p.cyl('Bearing armour '+str(s),(s*.59,.04,.25),.28,.05,'Ceramic','X',12)
 p.box('Sealed coolant gallery '+str(s),(s*.4,.70,.24),(.13,.35,.33),'Dark',.015)
 for y in [-.26,.0,.26]:p.box('Drive seam '+str(s)+' '+str(y),(s*.535,y,.65),(.026,.14,.025),'Titanium',.004)
p.cyl('Short torque spindle',(0,-1.22,.3),.245,1.45,'Steel','Y',32)
p.ring('Spindle retaining collar',(0,-1.56,.3),.30,.247,.10,'Y','Titanium')
p.box('Drive recessed diagnostic',(0,.92,.32),(.29,.02,.10),'Dark',.004)
p.box('Drive single status index',(0,.936,.32),(.15,.012,.025),'Signal',.002)
finish(p,[socket('root',(0,0,0),'drive')])

p=Part('MA-D01-P03','Tapered three-flute mechanical cutting head')
# Rear plane y=0; tool points -Y; core closes at both ends, no muzzle.
N=48
v=[]
for y,r in [(0,.58),(-.18,.69),(-1.35,.25),(-1.6,.11)]:
 v.extend((r*math.cos(i*2*math.pi/N),y,r*math.sin(i*2*math.pi/N)) for i in range(N))
f=[tuple(range(N-1,-1,-1)),tuple(range(3*N,4*N))]
for j in range(3):
 for i in range(N):k=(i+1)%N;f.append((j*N+i,j*N+k,(j+1)*N+k,(j+1)*N+i))
p.mesh('Closed tapered tool core',v,f,'Titanium',0)
p.cyl('Rear torque coupling',(0,.16,0),.246,.36,'Titanium','Y',32)
p.ring('Rear mechanical lock ring',(0,-.035,0),.70,.56,.12,'Y','Steel',32)
# Three watertight raised helical blades, separate editable solids.
for blade in range(3):
 verts=[];steps=36
 for i in range(steps+1):
  t=i/steps;y=-.18-1.25*t;r=.69-.45*t;angle=blade*2*math.pi/3+t*math.pi*1.45
  for rad,da in [(r-.015,-.07),(r+.15,-.07),(r+.15,.07),(r-.015,.07)]:
   verts.append((rad*math.cos(angle+da),y,rad*math.sin(angle+da)))
 faces=[(3,2,1,0),tuple(range(steps*4,steps*4+4))]
 for j in range(steps):
  for k in range(4):faces.append((4*j+k,4*j+(k+1)%4,4*(j+1)+(k+1)%4,4*(j+1)+k))
 p.mesh('Helical cutting flight '+str(blade),verts,faces,'Steel',0)
 for i in range(6):
  t=(i+.25)/6;y=-.18-1.25*t;r=.69-.45*t;ang=blade*2*math.pi/3+t*math.pi*1.45
  o=p.box('Replaceable carbide tooth '+str(blade)+' '+str(i),((r+.16)*math.cos(ang),y,(r+.16)*math.sin(ang)),(.16,.20,.14),'Ceramic',.01)
  o.rotation_euler.y=-ang
p.cyl('Blunt central breaker',(0,-1.61,0),.135,.16,'Steel','Y',8)
finish(p,[socket('root',(0,0,0),'cutter')],[dict(id='tool-axis',role='authoring-tool-axis-only',parent=None,position=[0,-1.69,0],direction=[0,-1,0],up=[0,0,1],coordinate_space='part-local',gameplay_contract=False)])

# Dependency gate is on disk before assembly; append saved parts, never construct in assembly.
a=Assembly(BID,'rotary-drill-1x3',[1,3],'Mechanical mining drill 1x3')
a.instance('load-frame','MA-D01-P01')
a.instance('reduction-drive','MA-D01-P02',loc=(0,1.2,.65))
a.instance('cutting-head','MA-D01-P03',loc=(0,-1.03,.95))
for o in bpy.context.scene.objects:
 if o.type=='EMPTY' and 'socket_id' in o and o.parent:
  o.name=o.parent.name+'::socket.'+o['socket_id']
connections=[]
for iid,mount in [('reduction-drive','drive'),('cutting-head','cutter')]:
 connections.append(dict(parent_instance='load-frame',parent_socket=mount,child_instance=iid,child_socket='root',position_error=0,rotation_error_degrees=0,scale=[1,1,1],compatibility='MilitaryArmor.drill.'+mount))
write(FOLDER/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id=a.catalog_id,catalog_grid=a.grid,axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Static visual-only mechanical mining tool. Grid is not a metre contract; no XML, productivity or effects supplied.'))
check=check_scene();write(FOLDER/'validation.json',dict(passed=True,parts_validated_before_assembly=True,instances=3,objects=check,game_validation=False,glb_generated=False))
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,6.9,(0,-.03,.85))
# Grayscale image compositor for identity review.
img=bpy.data.images.load(str(FOLDER/'Previews'/'top.png'),check_existing=False)
pixels=list(img.pixels[:])
for i in range(0,len(pixels),4):
 g=.2126*pixels[i]+.7152*pixels[i+1]+.0722*pixels[i+2];pixels[i:i+3]=[g,g,g]
img.pixels[:]=pixels;img.filepath_raw=str(FOLDER/'Previews'/'top-grayscale.png');img.file_format='PNG';img.save()
write(FOLDER/'README.md','# MA-D01 — Механический бур 1×3\n\nКаталог: rotary-drill-1x3, визуальная заготовка без игрового XML. Назначение выражено открытой несущей рамой, защищённым редуктором и широким коническим режущим шнеком с тремя винтовыми гребнями и сменными зубьями. Нет лазерного канала или пушечного среза.\n\nИсходник: MA-D01.blend. Три отдельные редактируемые детали MA-D01-P01, P02, P03 версии 1.0; экземпляры с единичным масштабом, логические крепления полностью совмещены по позиции и ориентации. +Z вверх, -Y рабочее направление, BU условные. Статическая исходная поза, анимаций нет. Ось инструмента — ориентир авторинга, не игровой контракт.\n\nПредпросмотры: Previews/top.png, perspective.png, top-grayscale.png. Процедурные материалы Blender; файловых текстур и UV нет; эмиссия только небольшого индикатора привода. В каждом part.json перечислены поверхности, материалы и крепления. Проверки геометрии выполнены до сборки. Производительность добычи, коллайдеры, LOD и игровой экспорт не заданы. GLB не создавался.\n')
print('MA-D01_BUILD_COMPLETE')
