import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,write,ROOT

def socket(id,pos,role='structural'):
    return dict(id=id,position=pos,role=role,forward=[0,-1,0],up=[0,0,1])

p=Part('MA-W04-P01','Bastion / diamond launch hardpoint')
plan=[(-1.03,-1.15),(1.03,-1.15),(1.94,-.29),(1.94,.56),(.83,1.17),(-.83,1.17),(-1.94,.56),(-1.94,-.29)]
p.slab('Diamond installation keel',[(x*.94,y*.94) for x,y in plan],0,.21,'Dark',.035)
p.slab('Wide missile hardpoint',plan,.21,.28,'Armor',.035)
p.ring('Azimuth track',(0,0,.57),1.08,.82,.17,'Z','Titanium',48)
for s in [-1,1]:
    p.slab('Swept lateral ceramic blade',[(s*.95,-.97),(s*1.20,-.94),(s*1.82,-.24),(s*1.82,.39),(s*1.55,.42),(s*1.39,-.16)],.49,.09,'Ceramic')
    p.stripe('Diagonal interface line',(s*1.16,-.90,.59),(s*1.73,-.26,.59),.022)
    p.panel('Rear power cassette',(s*1.25,.56,.53),(.62,.43,.09),'Titanium',.16)
    for y in [.45,.60]:p.box('Power connection stripe',(s*1.25,y,.581),(.32,.022,.012),'Signal',.003)
p.save([socket('mount.root',[0,0,0]),socket('mount.azimuth',[0,0,.66],'azimuth')])

p=Part('MA-W04-P02','Bastion / launch spine yaw drive')
p.cyl('Low profile rotation drum',(0,0,.11),.83,.22,'Titanium',verts=20)
p.section('Arrowhead structural spine',[(-.75,0,.24,.48,.33,.11),(-.12,0,.51,.86,.80,.22),(.65,0,.43,1.04,.71,.20),(.94,0,.31,.62,.46,.13)],'Armor')
p.section('Dorsal ceramic crest',[(-.63,0,.44,.35,.08,.025),(-.08,0,.94,.60,.09,.025),(.65,0,.82,.68,.09,.025),(.88,0,.53,.42,.08,.025)],'Ceramic')
for s in [-1,1]:
    p.cyl('Launch elevation journal',(s*.53,-.05,.70),.245,.19,'Titanium','X',16)
    p.ring('Launch elevation encoder',(s*.63,-.05,.70),.19,.16,.018,'X','Signal',32)
    p.section('Tapered sealed power conduit',[(.12,s*.52,.28,.21,.25,.07),(.64,s*.51,.28,.26,.24,.07),(.87,s*.37,.23,.20,.16,.05)],'Titanium')
p.save([socket('mount.root',[0,0,0]),socket('mount.elevation',[0,-.05,.70],'elevation'),socket('mount.service',[0,.39,.885],'accessory')])

p=Part('MA-W04-P03','Bastion / four-channel transverse launch beam')
p.section('Transverse torsion box',[(-.28,0,0,3.49,.28,.08),(.30,0,0,3.40,.42,.12)],'Titanium')
p.panel('Upper beam split armor',(0,.08,.24),(3.45,.48,.08),'Armor',.21)
p.section('Aft optical cantilever',[(.29,0,.12,.45,.26,.08),(.88,0,.28,.52,.26,.08),(1.53,0,.35,.80,.24,.08)],'Armor')
p.panel('Rear sensor docking plane',(0,1.23,.51),(.83,.66,.08),'Ceramic',.16)
for x in [-1.275,-.425,.425,1.275]:
    p.panel('Launch cassette keyed saddle',(x,-.02,.12),(.60,.64,.12),'Dark',.14)
    p.box('Cassette power contact',(x,.32,.10),(.26,.055,.035),'Signal',.008)
for s in [-1,1]:
    p.section('Swept beam end shield',[(-.45,s*1.84,.08,.25,.28,.07),(.28,s*1.84,.15,.30,.47,.10),(.56,s*1.67,.13,.18,.30,.05)],'Ceramic')
p.save([socket('mount.root',[0,0,0])]+[socket('mount.cell.'+str(i),[x,-.03,.26],'missile-cell') for i,x in enumerate([-1.275,-.425,.425,1.275])]+[socket('mount.lidar',[0,1.23,.55],'accessory')])

p=Part('MA-W04-P04','Bastion / armored single missile launch cell')
# Mouth is a genuinely open rectangular channel, built from four separate wall surfaces.
p.section('Cell rear pressure bulkhead',[(.46,0,.05,.66,.63,.16),(.81,0,.05,.50,.45,.14)],'Titanium')
for s in [-1,1]:
    p.section('Swept launch cell sidewall',[(-1.35,s*.29,.045,.13,.47,.04),(-.75,s*.34,.08,.15,.68,.045),(.43,s*.32,.08,.16,.64,.045)],'Armor')
    p.section('Ceramic side shell',[(-1.24,s*.35,.07,.065,.32,.02),(-.67,s*.425,.10,.07,.48,.02),(.43,s*.405,.09,.065,.42,.02)],'Ceramic',.007)
    p.stripe('Cell side status trace',(s*.463,-.52,.14),(s*.444,.25,.14),.015)
    p.section('Independent guide rail',[(-1.23,s*.20,-.025,.035,.045,.01),(.51,s*.20,-.025,.035,.045,.01)],'Titanium',.004)
p.section('Cell roof armor',[(-1.35,0,.30,.50,.11,.035),(-.70,0,.445,.69,.13,.04),(.47,0,.425,.65,.12,.035),(.80,0,.25,.47,.10,.03)],'Armor')
p.section('Dorsal launch shield',[(-1.15,0,.37,.36,.045,.014),(-.66,0,.525,.52,.045,.014),(.34,0,.50,.48,.045,.014)],'Ceramic',.008)
p.section('Launch cradle floor',[(-1.35,0,-.20,.52,.10,.03),(-.68,0,-.27,.68,.12,.035),(.48,0,-.25,.62,.12,.035)],'Titanium')
# A dark recessed missile with a pointed nose sits inside the launch tube.
p.cyl('Recessed missile body',(0,-.03,.06),.158,.83,'Dark','Y',24)
p.section('Armored missile nose',[(-.83,0,.06,.025,.025,.006),(-.57,0,.06,.28,.28,.08),(-.40,0,.06,.31,.31,.09)],'Titanium',.008)
p.box('Readiness optical slit',(0,-.49,.515),(.18,.085,.015),'Signal',.004)
p.box('Rear cell identification strip',(0,.665,.30),(.21,.055,.013),'Warning',.003)
p.save([socket('mount.root',[0,0,0],'missile-cell')],points=[dict(id='launch',position=[0,-1.40,.05],direction=[0,-1,0],up=[0,0,1])],notes='One genuine open launch channel with recessed inert missile; four instances create the four catalogue barrels.')

a=Assembly('MA-W04','fleet-rocket-bastion',[3,3],'Bastion — four-channel armored missile launcher')
a.instance('DiamondFoundation','MA-W04-P01')
yaw=a.node('Azimuth',a.root,(0,0,.66))
a.instance('LaunchSpine','MA-W04-P02',yaw)
el=a.node('Elevation',yaw,(0,-.05,.70))
a.instance('TransverseBeam','MA-W04-P03',el)
for i,x in enumerate([-1.275,-.425,.425,1.275]):a.instance('LaunchCell'+str(i),'MA-W04-P04',el,(x,-.03,.26))
a.instance('Lidar','MA-P07',el,(0,1.23,.55))
a.instance('ServiceCartridge','MA-P06',yaw,(0,.39,.885))
a.animate_rotation(yaw,'Z',[(1,0),(30,-35),(60,0),(90,35),(120,0)])
a.animate_rotation(el,'X',[(1,-8),(30,-35),(60,-16),(90,-48),(120,-8)])
a.save('Four functional launch channels in one horizontal battery. Azimuth and elevation are authoring demonstrations; physical scale and integration remain unspecified.')
write(ROOT/'Blocks/MA-W04/README.md','# MA-W04 / Bastion\n\nЧетырёхканальная ракетная установка. Каталог: fleet-rocket-bastion, 3x3 клетки. Широкая ромбическая опора, центральный силовой позвоночник и четыре отдельных клиновидных контейнера в горизонтальной линии. Открытые каналы с утопленными ракетами, короткие броневые направляющие и закрытый привод.\n\nНовые самостоятельные детали: MA-W04-P01…P04 v1.0. Повторно использованы MA-P06/P07 v1.3. Состав и крепления — assembly.json/part.json. Исходник MA-W04.blend; производный экспорт Exports/MA-W04.glb. GLB содержит реальные меши, PBR, иерархию и демонстрационную анимацию.\n\nBU, +Z вверх, -Y вперёд; клетки не метры. Исходники редактируемые, масштаб экземпляров единичный. Игровая интеграция, LOD и коллайдеры не выполнялись. Промежуточные варианты и рендеры не сохранялись.')
a.review(view=(7,-10,7),target=(0,-.25,1.1),scale=6.1)
