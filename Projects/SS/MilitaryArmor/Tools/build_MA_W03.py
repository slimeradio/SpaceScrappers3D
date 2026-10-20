import sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,write,ROOT

def socket(id,pos,role='structural'):
    return dict(id=id,position=pos,role=role,forward=[0,-1,0],up=[0,0,1])

p=Part('MA-W03-P01','Cyclone / swept three-lobe hardpoint')
p.cyl('Recessed installation flange',(0,0,.12),1.18,.24,'Dark',verts=12)
p.cyl('Low direct-drive housing',(0,0,.34),.96,.35,'Armor',verts=16)
p.ring('Azimuth seat',(0,0,.56),.90,.67,.16,mat='Titanium')
for i in range(3):
    a=i*math.tau/3
    pts=[(-.30,-.54),(.30,-.54),(.51,-1.12),(.25,-1.49),(-.25,-1.49),(-.51,-1.12)]
    def spin(points):return [(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)) for x,y in points]
    p.slab('Swept radial load foot',spin(pts),.08,.31,'Armor',.028)
    p.slab('Ceramic tip shield',spin([(-.30,-.93),(.30,-.93),(.25,-1.37),(-.25,-1.37)]),.395,.06,'Ceramic')
    p.stripe('Dock state index',(-.19*math.cos(a)+1.40*math.sin(a),-.19*math.sin(a)-1.40*math.cos(a),.455),(.19*math.cos(a)+1.40*math.sin(a),.19*math.sin(a)-1.40*math.cos(a),.455),.018)
for i in range(12):
    a=i*math.tau/12
    o=p.box('Motor collar shield',(.94*math.cos(a),.94*math.sin(a),.36),(.18,.23,.16),'Titanium',.014);o.rotation_euler.z=a
p.save([socket('mount.root',[0,0,0]),socket('mount.azimuth',[0,0,.65],'azimuth')],notes='Three-load-path swept foundation; BU, no catalogue-cell conversion.')

p=Part('MA-W03-P02','Cyclone / bifurcated high-speed receiver')
p.cyl('Yaw torque drum',(0,0,.10),.72,.20,'Titanium',verts=16)
p.section('Swept central spine',[(-.35,0,.32,.74,.35,.12),(.45,0,.48,1.18,.64,.18),(.95,0,.39,.82,.46,.14)],'Armor')
p.panel('Dorsal ceramic spine',(0,.56,.835),(.77,.74,.08),'Ceramic',.22)
for s in [-1,1]:
    p.section('Forward fork',[(-.82,s*.77,.40,.29,.31,.09),(-.20,s*.79,.55,.39,.76,.11),(.58,s*.68,.53,.48,.65,.15)],'Armor')
    p.section('Swept fork ceramic outer skin',[(-.75,s*.84,.50,.13,.22,.045),(-.15,s*.90,.61,.18,.55,.05),(.54,s*.82,.63,.15,.38,.05)],'Ceramic')
    p.cyl('Sealed elevation journal',(s*.81,-.22,.69),.20,.11,'Titanium','X',16)
    p.ring('Elevation encoder',(s*.875,-.22,.69),.145,.123,.015,'X','Signal',24)
    p.stripe('Fork diagnostic strip',(s*.984,-.17,.60),(s*.92,.37,.67),.017)
    p.section('Rear coolant lobe',[(.50,s*.50,.30,.30,.28,.08),(.95,s*.47,.32,.30,.22,.07),(1.12,s*.32,.33,.18,.17,.05)],'Titanium')
p.save([socket('mount.root',[0,0,0]),socket('mount.elevation',[0,-.22,.69],'elevation'),socket('mount.service',[0,.48,.875],'accessory'),socket('mount.lidar',[0,-.01,.90],'accessory')])

p=Part('MA-W03-P03','Cyclone / twin rotor elevation bridge')
p.section('Twin bore elevation beam',[(-.26,0,0,1.35,.40,.11),(.30,0,0,1.30,.47,.13),(.51,0,0,.87,.34,.10)],'Titanium')
for x in [-.43,.43]:
    p.cyl('Sealed induction drive housing',(x,-.17,0),.325,.67,'Armor','Y',16)
    p.ring('Rotor bearing',(x,-.53,0),.315,.245,.10,'Y','Steel',32)
    p.ring('Rotor encoding ring',(x,-.59,0),.27,.253,.016,'Y','Signal',32)
    p.panel('Breech upper ceramic shield',(x,-.10,.315),(.48,.61,.065),'Ceramic',.14)
p.save([socket('mount.root',[0,0,0]),socket('mount.rotor.left',[-.43,-.55,0],'rotor'),socket('mount.rotor.right',[.43,-.55,0],'rotor')])

p=Part('MA-W03-P04','Cyclone / single-bore rotary induction barrel')
p.cyl('Central physical barrel',(0,-.80,0),.135,1.56,'Dark','Y',32)
p.ring('Open single physical bore',(0,-1.65,0),.20,.105,.18,'Y','Titanium',32)
p.cyl('Recessed bore darkness',(0,-1.45,0),.104,.012,'Dark','Y',32)
for y in [-.12,-.65,-1.25]:p.ring('Rotor structural annulus',(0,y,0),.277,.155,.11,'Y','Titanium',24)
for i in range(6):
    a=i*math.tau/6
    # These solid rails are heat spreaders; only the central aperture is a barrel.
    x,z=.205*math.cos(a),.205*math.sin(a)
    o=p.box('Solid swept heat-spreader blade',(x,-.80,z),(.09,1.25,.11),'Ceramic',.018);o.rotation_euler.y=-a
    x,z=.258*math.cos(a),.258*math.sin(a)
    o=p.box('Induction blade status insert',(x,-.70,z),(.025,.28,.025),'Signal',.004);o.rotation_euler.y=-a
p.ring('Forward faceted rotor band',(0,-1.44,0),.263,.177,.10,'Y','Steel',12)
p.save([socket('mount.root',[0,0,0],'rotor')],points=[dict(id='muzzle',position=[0,-1.75,0],direction=[0,-1,0],up=[0,0,1])],notes='One actual bore. Six solid peripheral cooling blades are not functional barrels; total assembly has two catalogue barrels.')

a=Assembly('MA-W03','fleet-minigun-cyclone',[2,2],'Cyclone — twin rotary point-defense turret')
a.instance('Foundation','MA-W03-P01')
yaw=a.node('Azimuth',a.root,(0,0,.65))
a.instance('Receiver','MA-W03-P02',yaw)
el=a.node('Elevation',yaw,(0,-.22,.69))
a.instance('ElevationBridge','MA-W03-P03',el)
for side,x in [('Left',-.43),('Right',.43)]:
    rotor=a.node('Rotor'+side,el,(x,-.55,0))
    a.instance('Barrel'+side,'MA-W03-P04',rotor)
    a.animate_rotation(rotor,'Y',[(1,0),(30,270),(60,540),(90,810),(120,1080)])
a.instance('ServiceCartridge','MA-P06',yaw,(0,.48,.875))
a.instance('Lidar','MA-P07',yaw,(0,-.01,.90))
a.animate_rotation(yaw,'Z',[(1,0),(30,-35),(60,0),(90,35),(120,0)])
a.animate_rotation(el,'X',[(1,0),(30,-28),(60,-12),(90,-40),(120,0)])
a.save('Two functional catalogue barrels. Rotor spin, elevation and azimuth are authoring demonstrations; gameplay timing and scale remain unspecified.')
write(ROOT/'Blocks/MA-W03/README.md','# MA-W03 / Cyclone\n\nСкорострельная двухствольная роторная турель. Каталог: fleet-minigun-cyclone, 2x2 клетки. Три стреловидные опоры, открытая раздвоенная вилка, два осевых ротора с закрытыми теплоотводящими лопастями и ровно двумя настоящими каналами стволов.\n\nНовые самостоятельные детали: MA-W03-P01…P04 v1.0. Повторно использованы MA-P06/P07 v1.3. Состав и локальные крепления — assembly.json/part.json. Исходник MA-W03.blend; производный экспорт Exports/MA-W03.glb. GLB содержит реальные меши, PBR, иерархию и демонстрационную анимацию.\n\nBU, +Z вверх, -Y вперёд; клетки не метры. Исходники редактируемые, масштаб экземпляров единичный. Игровая интеграция, LOD и коллайдеры не выполнялись. Промежуточные варианты и рендеры не сохранялись.')
a.review(view=(6,-9,6),target=(0,-.6,1.05),scale=5.5)
