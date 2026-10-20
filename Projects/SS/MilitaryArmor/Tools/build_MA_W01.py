import sys, math, json, struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,write,ROOT
import bpy

BID='MA-W01'
def sock(i,pos,role='structural'):
    return dict(id=i,role=role,position=pos,forward=[0,-1,0],up=[0,0,1])

p=Part(BID+'-P01','Battleship swept foundation')
outline=[(-2.35,-2.7),(2.35,-2.7),(3.2,-1.65),(3.05,1.7),(1.65,2.65),(-1.65,2.65),(-3.05,1.7),(-3.2,-1.65)]
p.slab('Sealed hardpoint keel',outline,0,.28,'Dark')
p.slab('Faceted load spreader',[(x*.98,y*.98) for x,y in outline],.28,.38,'Armor')
p.slab('Upper interface deck',[(x*.87,y*.87) for x,y in outline],.66,.12,'Titanium')
for s in [-1,1]:
    p.slab('Swept ceramic outrigger',[(s*1.6,-2.43),(s*2.27,-2.43),(s*3.0,-1.5),(s*2.97,-.6),(s*2.55,-.65)],.52,.32,'Ceramic')
    p.slab('Rear docking wing',[(s*1.5,2.4),(s*2.8,1.55),(s*2.79,.75),(s*2.38,.9),(s*1.25,1.95)],.5,.27,'Ceramic')
    p.stripe('Hardpoint diagnostic', (s*2.08,-2.36,.86),(s*2.83,-1.5,.86),.025)
    for j in range(4):p.panel('Recessed power connector',(s*2.84,-.23+j*.31,.83),(.19,.2,.035),'Dark',.06)
p.ring('Bearing foundation seal',(0,0,.84),2.03,1.76,.14,'Z','Dark',64)
p.save(mounts=[sock('bottom',[0,0,0]),sock('azimuth',[0,0,.86])])

p=Part(BID+'-P02','Battleship azimuth direct drive')
p.cyl('Sealed annular direct drive',(0,0,.21),1.9,.42,'Dark',verts=64)
p.ring('Lower precision race',(0,0,.08),1.98,1.7,.12,verts=64)
p.ring('Upper torque seat',(0,0,.42),1.91,1.62,.14,verts=64)
for i in range(16):
    a=i*math.tau/16;o=p.panel('Motor shield',(1.86*math.cos(a),1.86*math.sin(a),.25),(.29,.51,.22),'Armor',.12);o.rotation_euler.z=a
    o=p.box('Index window',(1.976*math.cos(a),1.976*math.sin(a),.24),(.018,.14,.025),'Signal',.003);o.rotation_euler.z=a
p.save(mounts=[sock('bottom',[0,0,0]),sock('capsule',[0,0,.48])])

p=Part(BID+'-P03','Three-channel orbital armor capsule')
p.section('Sealed central pressure frame',[(-1.65,0,.66,3.8,.84,.25),(-.5,0,.74,4.4,1.25,.35),(1.7,0,.63,3.6,1.1,.32),(2.12,0,.49,2.35,.63,.2)],'Dark')
for s in [-1,1]:
    p.section('Swept armored shoulder',[(-2.15,s*1.97,.75,.6,.62,.22),(-.5,s*2.1,.91,.95,1.3,.3),(1.55,s*1.72,.76,.77,1.16,.29),(2.15,s*1.34,.58,.45,.64,.17)],'Ceramic',.035)
    p.section('Shoulder dorsal spine',[(-1.64,s*2.01,1.11,.36,.18,.05),(-.3,s*2.08,1.58,.56,.18,.07),(1.56,s*1.68,1.34,.4,.13,.05)],'Armor')
    p.stripe('Recessed shoulder index',(s*2.36,-.15,1.02),(s*1.98,1.33,1.02),.023)
    for y in [.1,.5,.9,1.3]:p.panel('Closed thermal tile',(s*1.1,y,1.36),(.48,.29,.035),'Titanium',.08)
p.section('Roof armored bridge',[(-.35,0,1.28,3.4,.21,.09),(.55,0,1.42,3.1,.26,.09),(1.61,0,1.2,2.8,.20,.09)],'Armor')
p.panel('Rear energy interface',(0,1.89,.71),(1.7,.19,.47),'Titanium',.16)
for x in [-.56,0,.56]:p.box('Sealed rear transfer',(x,2.003,.75),(.33,.014,.048),'Signal',.004)
p.save(mounts=[sock('bottom',[0,0,0]),sock('elevation',[0,-.8,.88]),sock('service',[0,1.05,1.37],'accessory'),sock('lidar',[0,.05,1.56],'accessory')])

p=Part(BID+'-P04','Triple-gun elevation cradle')
p.section('Cross-axis elevation bridge',[(-.55,0,0,3.58,.65,.19),(.36,0,0,3.4,.7,.2)],'Titanium')
for x in [-1.15,0,1.15]:
    p.section('Independent recoil sleeve',[(-.7,x,0,.97,.73,.2),(.31,x,0,.9,.65,.19)],'Armor')
    p.ring('Recoil sleeve seal',(x,-.72,0),.36,.29,.12,'Y','Steel')
for x in [-1.98,1.98]:
    p.cyl('Trunnion enclosed joint',(x,0,0),.43,.27,'Titanium','X')
    p.ring('Elevation position encoder',(x*1.065,0,0),.33,.29,.018,'X','Signal')
p.save(mounts=[sock('pivot',[0,0,0])]+[sock('gun'+str(i),[x,-.6,0]) for i,x in enumerate([-1.15,0,1.15])])

p=Part(BID+'-P05','Segmented battleship projectile accelerator')
p.cyl('Recoil barrel spine',(0,-1.85,0),.232,3.7,'Titanium','Y',48)
p.section('Breech casing',[(.35,0,0,.65,.62,.16),(-.65,0,0,.66,.64,.18),(-1.1,0,0,.45,.43,.12)],'Armor')
for j in range(5):
    y=-1.05-j*.61
    p.section('Octagonal accelerator segment',[(y+.18,0,0,.52,.54,.14),(y-.15,0,0,.50,.50,.14),(y-.23,0,0,.39,.4,.10)],'Ceramic')
    p.box('Accelerator upper conductor',(0,y,.276),(.22,.27,.022),'Titanium',.006)
    p.box('Accelerator index',(0,y-.09,.29),(.12,.055,.013),'Signal',.003)
for s in [-1,1]:
    p.stripe('Longitudinal rail',(s*.25,-.95,.12),(s*.19,-3.8,.12),.045,'Steel')
p.ring('Muzzle annulus',(0,-4.04,0),.31,.19,.39,'Y','Titanium',32)
p.ring('Muzzle armor lip',(0,-4.25,0),.33,.19,.09,'Y','Ceramic',32)
p.ring('Muzzle deep throat',(0,-3.83,0),.229,.19,.13,'Y','Dark',32)
p.save(mounts=[sock('receiver',[0,0,0])],points=[dict(id='muzzle',position=[0,-4.30,0],direction=[0,-1,0],up=[0,0,1])])

a=Assembly(BID,'fleet-artillery-battleship',[4,4],'Линкорная трёхствольная артиллерия')
a.instance('Foundation',BID+'-P01')
az=a.node('Azimuth',a.root,(0,0,.86))
a.instance('AzimuthDrive',BID+'-P02',az)
h=a.instance('Capsule',BID+'-P03',az,(0,0,.48))
el=a.node('Elevation',h,(0,-.8,.88))
a.instance('TripleCradle',BID+'-P04',el)
for i,x in enumerate([-1.15,0,1.15]):
    r=a.node('Recoil'+str(i),el,(x,-.6,0));a.instance('Accelerator'+str(i),BID+'-P05',r)
    a.animate_location(r,'Y',[(1,-.6),(21+i*8,-.6),(24+i*8,-.31),(39+i*8,-.6),(120,-.6)])
a.instance('ServiceCartridge','MA-P06',h,(0,1.05,1.37))
a.instance('LidarBlade','MA-P07',h,(0,.05,1.56))
a.animate_rotation(az,'Z',[(1,0),(60,100),(120,0)])
a.animate_rotation(el,'X',[(1,-7),(35,-25),(80,5),(120,-7)])
notes='Style MilitaryArmor 1.3. Three physical projectile channels; 4x4 catalog grid is not metric mesh size. BU, scale unspecified. Demonstration aiming/recoil only. No collider, LOD or game integration.'
a.save(notes=notes)
write(ROOT/'Blocks'/BID/'README.md','# MA-W01 — линкорная артиллерия\n\nТри отдельных сегментированных снарядных ускорителя, закрытая люлька и стреловидная многогранная бронекапсула. Исходники пяти новых деталей находятся в Parts/MA-W01-P01..05; MA-P06 и MA-P07 версии 1.3 повторно использованы без изменений.\n\nMA-W01.blend — редактируемая сборка; Exports/MA-W01.glb — окончательная модель для просмотрщика с материалами и демонстрационной анимацией. assembly.json хранит состав, иерархию и локальные позы. PLAN.md содержит предварительный план состава.\n\n'+notes)
a.review(view=(10,-14,10),target=(0,-1.8,1.5),scale=11,resolution=800)
print('FINAL_BLOCK_COMPLETED '+BID)
