import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,write,ROOT
BID='MA-W02'
def sock(i,pos,role='structural'):
    return dict(id=i,role=role,position=pos,forward=[0,-1,0],up=[0,0,1])

p=Part(BID+'-P01','Narrow continuous-laser hardpoint')
pts=[(-.75,-2.4),(.75,-2.4),(1.23,-1.58),(1.23,1.73),(.63,2.4),(-.63,2.4),(-1.23,1.73),(-1.23,-1.58)]
p.slab('Laser keel',pts,0,.25,'Dark')
p.slab('Elongated power spine',[(x*.95,y*.98) for x,y in pts],.25,.29,'Armor')
for s in [-1,1]:
    p.slab('Diagonal hardpoint wing',[(s*.64,-2.2),(s*.9,-1.95),(s*1.1,-1.3),(s*1.1,1.6),(s*.75,1.98),(s*.74,-1.3)],.43,.20,'Ceramic')
    p.stripe('Foundation optical index',(s*.72,-2.1,.66),(s*1.02,-1.4,.66),.018)
p.panel('High-density capacitor enclosure',(0,1.35,.64),(1.3,1.15,.37),'Titanium',.25)
for y in [.98,1.24,1.50,1.76]:p.panel('Capacitor dielectric tile',(0,y,.85),(1.09,.16,.055),'Armor',.065)
p.ring('Azimuth foundation',(0,-.42,.6),.92,.72,.16,'Z','Titanium')
p.save(mounts=[sock('bottom',[0,0,0]),sock('azimuth',[0,-.42,.68]),sock('service',[0,1.22,.90],'accessory')])

p=Part(BID+'-P02','Split optical azimuth fork')
p.cyl('Sealed laser direct drive',(0,0,.16),.86,.32,'Dark',verts=48)
p.ring('Laser azimuth encoder',(0,0,.25),.9,.82,.032,'Z','Signal',48)
p.panel('Rotating fork sill',(0,0,.4),(2.7,1.3,.24),'Titanium',.32)
for s in [-1,1]:
    p.section('Swept elevation pylon',[(-.56,s*1.13,.8,.39,.83,.14),(.05,s*1.14,.9,.51,1.25,.16),(.68,s*.99,.64,.39,.78,.13)],'Ceramic')
    p.cyl('Optical gimbal bearing',(s*1.09,-.05,1.13),.33,.18,'Titanium','X')
    p.ring('Gimbal encoder',(s*1.2,-.05,1.13),.26,.22,.015,'X','Optic')
p.save(mounts=[sock('bottom',[0,0,0]),sock('elevation',[0,-.05,1.13])])

p=Part(BID+'-P03','Continuous-beam optical chamber')
p.section('Optical pressure envelope',[(-1.0,0,0,1.76,1.48,.4),(-.48,0,.02,1.98,1.6,.47),(.6,0,.05,1.62,1.3,.36),(1.1,0,.04,1.16,.88,.25)],'Armor')
for s in [-1,1]:
    p.section('Floating ceramic prism shoulder',[(-.72,s*.77,.25,.40,.90,.15),(.4,s*.76,.36,.36,.78,.13),(.97,s*.51,.2,.29,.54,.09)],'Ceramic')
    p.stripe('Optical alignment trace',(s*.96,-.45,.29),(s*.78,.4,.52),.022)
p.section('Dorsal lens control shroud',[(-.43,0,.76,.92,.23,.07),(.57,0,.72,.85,.24,.07),(.88,0,.52,.52,.15,.04)],'Ceramic')
p.panel('Rear sensor pad',(0,.79,.56),(.85,.60,.11),'Titanium',.2)
p.save(mounts=[sock('pivot',[0,0,0]),sock('emitter',[0,-1,0]),sock('left-radiator',[-1.07,.35,-.03]),sock('right-radiator',[1.07,.35,-.03]),sock('lidar',[0,.73,.64],'accessory')])

p=Part(BID+'-P04','Single-aperture continuous laser emitter')
p.ring('Hexadecagonal armored aperture',(0,-.14,0),.76,.56,.30,'Y','Ceramic',16)
p.ring('Isolated focusing suspension',(0,-.31,0),.65,.53,.065,'Y','Dark',16)
p.ring('Nested optical conductor',(0,-.35,0),.57,.49,.065,'Y','Titanium',32)
p.ring('Lens perimeter glow',(0,-.392,0),.505,.479,.018,'Y','Signal',48)
p.cyl('Continuous beam focusing lens',(0,-.366,0),.477,.025,'Optic','Y',64)
p.cyl('Inner active lens',(0,-.383,0),.29,.017,'Optic','Y',48)
p.ring('Central focusing zone',(0,-.396,0),.23,.20,.012,'Y','Signal',48)
for i in range(8):
    a=i*math.tau/8
    x,z=.43*math.cos(a),.43*math.sin(a)
    o=p.box('Iris actuator',(x,-.406,z),(.105,.033,.045),'Titanium',.008);o.rotation_euler.y=-a
for s in [-1,1]:p.panel('Emitter lateral shield',(s*.63,-.08,0),(.22,.44,.71),'Armor',.10)
p.save(mounts=[sock('optical-input',[0,0,0])],points=[dict(id='continuous-emitter',position=[0,-.425,0],direction=[0,-1,0],up=[0,0,1])],notes='One broad optical aperture; no ballistic bore, recoil or projectile barrels.')

p=Part(BID+'-P05','Closed-loop radiative cooling wing')
p.section('Radiator thermal manifold',[(-.55,0,0,.3,.82,.1),(.25,0,-.06,.44,1.02,.13),(1.0,0,-.16,.30,.75,.11)],'Titanium')
for i in range(6):
    y=-.45+i*.24
    p.section('Radiative ceramic lamella',[(y,0,-.07,.90,.73,.19),(y+.09,0,-.07,.90,.73,.19)],'Armor')
    p.box('Thermal lamella edge',(0,y-.008,.3),(.63,.028,.033),'Ceramic',.008)
p.stripe('Coolant loop indicator',(0,-.48,.38),(0,.88,.31),.016,'Optic')
p.save(mounts=[sock('thermal-root',[0,0,0])])

a=Assembly(BID,'continuous-laser-turret',[1,3],'Турель непрерывного лазера')
a.instance('LaserFoundation',BID+'-P01')
a.instance('ServiceCartridge','MA-P06',a.root,(0,1.22,.90))
az=a.node('Azimuth',a.root,(0,-.42,.68))
a.instance('OpticalFork',BID+'-P02',az)
el=a.node('Elevation',az,(0,-.05,1.13))
head=a.instance('OpticalChamber',BID+'-P03',el)
a.instance('ContinuousEmitter',BID+'-P04',head,(0,-1,0))
a.instance('LeftRadiator',BID+'-P05',head,(-1.07,.35,-.03))
a.instance('RightRadiator',BID+'-P05',head,(1.07,.35,-.03))
a.instance('LidarBlade','MA-P07',head,(0,.73,.64))
a.animate_rotation(az,'Z',[(1,0),(60,110),(120,0)])
a.animate_rotation(el,'X',[(1,-9),(35,-27),(80,8),(120,-9)])
notes='Style MilitaryArmor 1.3. Exactly one continuous optical emitter; 1x3 catalog grid is not metric mesh size. BU, scale unspecified. Demonstration aiming only; no ballistic recoil. No collider, LOD or game integration.'
a.save(notes=notes)
write(ROOT/'Blocks'/BID/'README.md','# MA-W02 — турель непрерывного лазера\n\nОдна широкая оптическая апертура с фокусирующими линзами, закрытая поворотная вилка, два радиаторных крыла и вытянутая силовая база. Исходники пяти новых деталей находятся в Parts/MA-W02-P01..05; MA-P06 и MA-P07 версии 1.3 повторно использованы без изменений.\n\nMA-W02.blend — редактируемая сборка; Exports/MA-W02.glb — окончательная модель для просмотрщика с материалами и демонстрационной анимацией. assembly.json хранит состав, иерархию и локальные позы. PLAN.md содержит предварительный план состава.\n\n'+notes)
a.review(view=(7,-11,7),target=(0,-.1,1.1),scale=6.5,resolution=800)
print('FINAL_BLOCK_COMPLETED '+BID)
