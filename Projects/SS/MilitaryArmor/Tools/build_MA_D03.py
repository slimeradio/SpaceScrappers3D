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
BID='MA-D03';FOLDER=ROOT/'Blocks'/BID
write(FOLDER/'composition-plan.md','# MA-D03 composition plan\n\nVisual-only catalog rotary-drill-3x5; no XML. Reuse unchanged unit-scale MA-D01-P02 drive and MA-D01-P03 head v1.0 three times each. New MA-D03-P01 heavy three-channel frame needed: existing frames lack three bearing positions and long aft distribution. Center tool leads .45 BU. +Z up, -Y tool direction, conditional BU. Static/no gameplay rates or animation. Gate frame before assembly.\n')
p=Part('MA-D03-P01','Heavy three-spindle longitudinal drill frame')
for side in [-1,1]:
 x=side*2.82
 p.section('Outboard beam '+str(side),[(-2.7,x,.30,.32,.48,.09),(3.9,x,.30,.44,.48,.11),(5.65,side*2.45,.36,.42,.62,.10)],'Armor',.02)
 p.section('Upper ceramic rail '+str(side),[(-2.55,x,.60,.23,.10,.03),(3.9,x,.60,.31,.10,.03),(5.47,side*2.48,.72,.29,.10,.03)],'Ceramic',.008)
 p.stripe('Elevated aft diagonal '+str(side),(x,2.7,.56),(side*2.12,5.4,1.4),.24,'Titanium')
 p.panel('Rear hull foot '+str(side),(side*2.42,5.45,.22),(.62,.66,.44),'Titanium',.1)
p.box('Rear load bridge',(0,5.4,.42),(4.95,.52,.72),'Armor',.035)
p.box('Upper distribution bridge',(0,5.3,1.28),(4.50,.65,.40),'Titanium',.035)
p.box('Forward crosshead',(0,-2.2,.26),(5.8,.45,.40),'Titanium',.025)
p.box('Middle crossmember',(0,2.0,.30),(5.40,.46,.40),'Titanium',.025)
mounts=[socket('hull',(0,0,0),'hull')]
for name,x,lead in [('port',-1.8,0),('center',0,-.45),('starboard',1.8,0)]:
 dy=.2+lead;cy=dy-2.23
 p.box('Longitudinal lower drive bed '+name,(x,0,.19),(.38,5.30,.28),'Titanium',.018)
 p.box('Drive sole '+name,(x,dy,.3),(1.45,1.60,.32),'Titanium',.025)
 p.box('Bearing transverse foot '+name,(x,cy+.30,.32),(1.50,.38,.26),'Titanium',.018)
 p.ring('Bearing saddle '+name,(x,cy+.30,.95),.46,.28,.34,'Y','Ceramic')
 for side in [-1,1]:p.stripe('Bearing stay '+name+str(side),(x+side*.70,cy+.32,.43),(x+side*.31,cy+.30,.96),.18,'Titanium')
 p.section('Protected distribution housing '+name,[(1.42,x,.63,.80,.76,.17),(3.85,x,.78,1.10,1.06,.23),(5.24,x,.82,.85,.94,.20)],'Armor',.025)
 p.panel('Transmission upper shell '+name,(x,3.65,1.335),(.70,1.42,.12),'Ceramic',.12)
 p.cyl('Rear transmission cap '+name,(x,5.32,.85),.35,.22,'Titanium','Y',16)
 for y in [2.2,2.8,4.6]:p.box('Recessed seam '+name+str(y),(x,y,1.19),(.6,.05,.025),'Dark',.003)
 for side in [-1,1]:p.stripe('Thrust diagonal '+name+str(side),(x+side*.50,1.82,.48),(x+side*.40,3.55,1.04),.15,'Titanium')
 mounts.extend([socket('drive-'+name,(x,dy,.65),'drive'),socket('cutter-'+name,(x,cy,.95),'cutter')])
finish(p,mounts)
for pid in ['MA-D03-P01','MA-D01-P02','MA-D01-P03']:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts'/pid/(pid+'.blend')));check_scene()
a=Assembly(BID,'rotary-drill-3x5',[3,5],'Heavy three-spindle mechanical drill 3x5');a.instance('heavy-load-frame','MA-D03-P01')
connections=[]
for name,x,lead in [('port',-1.8,0),('center',0,-.45),('starboard',1.8,0)]:
 for role,pid,y,z in [('drive','MA-D01-P02',.20+lead,.65),('cutter','MA-D01-P03',.20+lead-2.23,.95)]:
  iid=role+'-'+name;a.instance(iid,pid,loc=(x,y,z))
  connections.append(dict(parent_instance='heavy-load-frame',parent_socket=iid,child_instance=iid,child_socket='root',compatibility='MilitaryArmor.drill.'+role,position_error=0,rotation_error_degrees=0,scale=[1,1,1]))
for o in bpy.context.scene.objects:
 if o.type=='EMPTY' and 'socket_id' in o and o.parent:o.name=o.parent.name+'::socket.'+o['socket_id']
write(FOLDER/'assembly.json',dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id=a.catalog_id,catalog_grid=a.grid,axes=AXES,instances=a.instances,connections=connections,animations=[],exports=[],notes='Static visual-only authoring; no gameplay XML, scale, speed or performance contract. Three staggered mechanical heads, no beam or muzzle.'))
gate=check_scene();write(FOLDER/'validation.json',dict(passed=True,parts_validated_before_assembly=True,instance_count=7,new_parts=['MA-D03-P01'],reused_parts=['MA-D01-P02','MA-D01-P03'],objects=gate,game_validation=False,glb_generated=False))
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,12.8,(0,1.0,.9))
img=bpy.data.images.load(str(FOLDER/'Previews/top.png'),check_existing=False);pixels=list(img.pixels[:])
for i in range(0,len(pixels),4):
 g=.2126*pixels[i]+.7152*pixels[i+1]+.0722*pixels[i+2];pixels[i:i+3]=[g,g,g]
img.pixels[:]=pixels;img.filepath_raw=str(FOLDER/'Previews/top-grayscale.png');img.file_format='PNG';img.save()
write(FOLDER/'README.md','# MA-D03 — Механический бур 3×5\n\nТри зубчатые конические головки, центральная вынесена вперёд. Длинная открытая силовая рама с тремя распределительными кожухами, диагоналями и кормовым мостом. Три готовых редуктора и три готовых инструмента не растянуты.\n\nКаталог rotary-drill-3x5, визуальная заготовка без игрового XML. Условные BU, +Z вверх, -Y направление инструмента. Новая MA-D03-P01 v1.0; MA-D01-P02 и MA-D01-P03 v1.0 использованы по три раза без изменений. Семь стабильных экземпляров с единичным масштабом. Полные позы совместимых креплений. Статика без анимаций. Процедурные материалы без файловых текстур/UV; штатные небольшие индексы приводов светятся.\n\nИсходник MA-D03.blend; Previews/top.png, perspective.png, top-grayscale.png. Новая деталь проверена до сборки. Независимый verifier повторно открывает источники и сборку, проверяет валы/муфты и оси инструмента. Нет GLB, игровых параметров, LOD, коллайдеров или установки в игру.\n')
print('MA_D03_BUILD_COMPLETE')
