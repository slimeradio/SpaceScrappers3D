import sys,json,math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from weapon_batch_core import Part,Assembly,ROOT,AXES,write
ref=Path(__file__).with_name('build_MA_D01.py').read_text(encoding='utf-8-sig')
exec(ref.split("p=Part('MA-D01-P01'")[0])
_base_check_scene=check_scene
def check_scene():
 rows=_base_check_scene()
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   bm=bmesh.new();bm.from_mesh(o.data)
   assert all(e.is_contiguous for e in bm.edges),o.name
   bm.free()
 return rows
BID='MA-D02';FOLDER=ROOT/'Blocks'/BID
write(FOLDER/'composition-plan.md','# MA-D02 composition plan\n\nCatalog rotary-drill-2x3: visual-only mechanical drill. Reuse MA-D01-P02 v1.0 drive and MA-D01-P03 v1.0 cutter twice each at unit scale. Single MA-D01-P01 frame is incompatible with two spindles; create MA-D02-P01 twin-spindle cradle with two bearing seats, broad aft crossmember, outer load rails and protected central spine. No duplication of compatible drives/cutters. Two head centers at X +/-1 BU have clearance. BU is not metres. Static authoring, +Z up, -Y tool forward. Gate new source before assembly; no edits to original D01 parts.\n')
p=Part('MA-D02-P01','Twin-spindle load cradle with broad aft crossmember')
for s in [-1,1]:
 p.section('Outer load rail '+str(s),[(-.95,s*1.76,.23,.24,.44,.05),(1.9,s*1.76,.23,.32,.44,.07),(2.55,s*1.56,.23,.27,.44,.05)],'Armor',.018)
 p.section('Upper ceramic rail '+str(s),[(-.80,s*1.76,.50,.18,.09,.02),(1.82,s*1.76,.50,.23,.09,.02),(2.43,s*1.58,.50,.18,.09,.02)],'Ceramic',.008)
 p.panel('Rear hull foot '+str(s),(s*1.53,2.36,.18),(.46,.40,.30),'Titanium',.09)
 p.ring('Spindle support '+str(s),(s*1.0,-.73,.95),.46,.28,.34,'Y','Ceramic')
 p.stripe('Outboard bearing strut '+str(s),(s*1.73,-.85,.42),(s*1.30,-.73,.93),.17,'Titanium')
 p.stripe('Inboard bearing strut '+str(s),(s*.39,-.80,.39),(s*.70,-.73,.93),.17,'Titanium')
 p.box('Protected drive sole '+str(s),(s*1.0,1.15,.28),(1.65,.44,.38),'Titanium',.02)
p.box('Heavy aft crossmember',(0,2.34,.25),(3.35,.32,.43),'Armor',.025)
p.box('Forward load crossmember',(0,-.59,.24),(3.60,.34,.35),'Titanium',.02)
p.section('Central protected distribution spine',[(-.45,0,.35,.38,.48,.09),(1.95,0,.35,.58,.48,.12),(2.45,0,.31,.42,.40,.08)],'Armor',.018)
p.panel('Central upper removable cover',(0,.7,.62),(.35,1.70,.10),'Ceramic',.1)
for y in [-.22,.31,.84,1.37]:p.box('Recessed spine seam '+str(y),(0,y,.674),(.28,.026,.016),'Dark',.002)
mounts=[socket('hull',(0,0,0),'hull')]
for name,s in [('left',-1),('right',1)]:mounts += [socket('drive-'+name,(s*1.0,1.2,.65),'drive'),socket('cutter-'+name,(s*1.0,-1.03,.95),'cutter')]
finish(p,mounts)
for pid in ['MA-D02-P01','MA-D01-P02','MA-D01-P03']:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts'/pid/(pid+'.blend')));check_scene()
a=Assembly(BID,'rotary-drill-2x3',[2,3],'Twin mechanical mining drill 2x3');a.instance('twin-load-frame','MA-D02-P01')
connections=[]
for name,s in [('left',-1),('right',1)]:
 for role,pid,y,z in [('drive','MA-D01-P02',1.2,.65),('cutter','MA-D01-P03',-1.03,.95)]:
  iid=role+'-'+name;a.instance(iid,pid,loc=(s*1.0,y,z))
  connections.append(dict(parent_instance='twin-load-frame',parent_socket=iid,child_instance=iid,child_socket='root',compatibility='MilitaryArmor.drill.'+role,position_error=0,rotation_error_degrees=0,scale=[1,1,1]))
for o in bpy.context.scene.objects:
 if o.type=='EMPTY' and 'socket_id' in o and o.parent:o.name=o.parent.name+'::socket.'+o['socket_id']
write(FOLDER/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id=a.catalog_id,catalog_grid=a.grid,axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Static visual-only authoring; no gameplay XML, scale, speed or performance contract. Two separate mechanical heads, no beam or muzzle.'))
gate=check_scene();write(FOLDER/'validation.json',dict(passed=True,parts_validated_before_assembly=True,instance_count=5,new_parts=['MA-D02-P01'],reused_parts=['MA-D01-P02','MA-D01-P03'],objects=gate,game_validation=False,glb_generated=False))
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,7.3,(0,-.03,.9))
img=bpy.data.images.load(str(FOLDER/'Previews/top.png'),check_existing=False);pixels=list(img.pixels[:])
for i in range(0,len(pixels),4):
 g=.2126*pixels[i]+.7152*pixels[i+1]+.0722*pixels[i+2];pixels[i:i+3]=[g,g,g]
img.pixels[:]=pixels;img.filepath_raw=str(FOLDER/'Previews/top-grayscale.png');img.file_format='PNG';img.save()
write(FOLDER/'README.md','# MA-D02 — Механический бур 2×3\n\nДва отдельных конических шнека со сменными зубьями, два закрытых редуктора, широкая силовая траверса и наружные опорные полозья. Общий облик семейства MA-D01 сохранён; широкая двухвальная компоновка не получена растяжением одиночного бура.\n\nКаталог: rotary-drill-2x3. Визуальная заготовка без игрового XML; производительность и физический масштаб не заданы. +Z вверх, -Y направление инструмента; BU условные. Исходник: MA-D02.blend. Новая деталь MA-D02-P01; MA-D01-P02 и MA-D01-P03 версии 1.0 повторно использованы по два раза без изменения. Пять экземпляров, единичный масштаб, полные локальные позы креплений. Статика без анимаций, искр и лучей. Процедурные материалы Blender; нет файловых текстур или UV. Эмиссия — небольшие штатные диагностические индексы приводов.\n\nПредпросмотры: Previews/top.png, perspective.png, top-grayscale.png. Проверки исходников выполнены до сборки, независимая проверка повторно открывает все .blend. GLB не генерировался. Игровой экспорт, коллайдеры и LOD не входят в текущий авторинг.\n')
print('MA_D02_BUILD_COMPLETE')