"""Two final MilitaryArmor thruster assemblies; no presentation variants."""
import sys, math, json, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part, Assembly, ROOT, write
import bpy

def socket(i,pos,role='engine-interface',forward=(0,-1,0)):
    return {'id':i,'position':list(pos),'role':role,'forward':list(forward),'up':[0,0,1],'compatibility':['MilitaryArmor.engine.'+role],'restrictions':'unit scale; local authoring frame'}

def source(m,sockets,notes='',thrust=False,length=0):
    if m.pid=='MA-E01-P02':
        for s in sockets:
            if s['id']=='thermal-L':s['up']=[0,0,-1]
    points=[]
    if thrust:
        points=[{'id':'thrust','role':'thrust','node':'point.thrust','position':[0,0,0],'direction':[0,1,0],'up':[0,0,1]},{'id':'exhaust','role':'exhaust','node':'point.exhaust','position':[0,-length,0],'direction':[0,-1,0],'up':[0,0,1]}]
        for point in points:
            o=bpy.data.objects.new(point['node'],None);m.coll.objects.link(o);o.location=point['position'];o.empty_display_size=.06;o['role']=point['role'];o['direction']=point['direction'];o['up']=point['up']
    m.save(mounts=sockets,points=points,notes=notes)
    path=ROOT/'Parts'/m.pid/'part.json';data=json.loads(path.read_text(encoding='utf8'))
    data['attachment_areas']=[{'id':'interface-plane','role':sockets[0]['role'],'parent':m.pid,'shape':'logical-plane','position':sockets[0]['position'],'forward':sockets[0]['forward'],'up':[0,0,1],'allowed_rotations_degrees':[0],'compatibility':sockets[0]['compatibility'],'restrictions':'Align complete socket pose; no nonunit scale'}]
    write(path,data)

def nozzle(pid,r,length,title):
    m=Part(pid,title)
    # Hollow twelve-sector bell: inner and outer frusta with a real open mouth.
    n=12;v=[];faces=[]
    profiles=[(0,r*.64),(-length*.40,r*.73),(-length,r),(-length,r*.78),(-length*.40,r*.51),(0,r*.43)]
    for y,rad in profiles:
        v.extend((rad*math.cos(i*2*math.pi/n+math.pi/12),y,rad*math.sin(i*2*math.pi/n+math.pi/12)) for i in range(n))
    for k in range(len(profiles)-1):
        for i in range(n):j=(i+1)%n;faces.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    for i in range(n):j=(i+1)%n;faces.append(((len(profiles)-1)*n+i,(len(profiles)-1)*n+j,j,i))
    bell=m.mesh('Faceted open expansion bell',v,faces,'Titanium',.004)
    bell.data.materials.append(m.mats['Dark'])
    for p in bell.data.polygons:
        if p.index>=3*n:p.material_index=1
    m.ring('Ceramic mouth rim',(0,-length,0),r*1.025,r*.79,length*.055,'Y','Ceramic',12)
    m.ring('Recessed energized throat',(0,-length*.20,0),r*.55,r*.44,length*.07,'Y','Signal',24)
    # Deep throat remains dark; blue emission comes only from the annular wall.
    m.cyl('Deep combustion chamber',(0,.025,0),r*.43,.035,'Dark','Y',24)
    for a in [math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4]:
        x,z=math.cos(a),math.sin(a)
        rail=m.section('Segmented thermal petal',[(0,x*r*.66,z*r*.66,r*.31,r*.22,r*.06),(-length*.35,x*r*.79,z*r*.79,r*.34,r*.25,r*.07),(-length*.83,x*r*.98,z*r*.98,r*.30,r*.18,r*.05)],'Ceramic',.006)
    source(m,[socket('chamber',[0,0,0],'nozzle')],'Open nozzle. Thrust +Y, exhaust -Y. Emission is an idle authoring indicator, no plume mesh.',True,length)

plans={
'MA-E01':('# MA-E01 — средний двигатель\n\nКаталог thruster-med, 1×2, один источник тяги. Вытянутый силовой кожух, крупное полое сопло и боковые термопанели.\n\nСостав до моделирования: MA-E01-P01 новая несущая кассета; MA-E01-P02 новая камера; MA-E01-P03 новый большой вариант сопла; MA-E01-P04 новая термопанель (два повёрнутых экземпляра). MA-E01-P05 новый компактный сервисный картридж: готовый MA-P06 версии1.3 не подходит по ширине, масштабирование не используется. Детали оружия и брони по геометрии/интерфейсам не заменяют камеру и сопло.\n\nВсе экземпляры единичного масштаба, +Z вверх, -Y выход струи, +Y тяга. BU условные; игровые размеры и сила не пересчитываются. Неподвижная конструкция, без выдуманных клипов и постоянного пламени.\n'),
'MA-E02':('# MA-E02 — малый тройной двигатель\n\nКаталог thruster-small-3way, 3×2, три сонаправленных источника. Широкая низкая питающая рама с тремя одинаковыми камерами/соплами.\n\nСостав до моделирования: MA-E02-P01 новая трёхканальная рама; MA-E02-P02 новая компактная камера (три экземпляра); MA-E02-P03 явный малый параметрический вариант сопла (три экземпляра), масштабирование большого исходника не используется. Готовый MA-E01-P05 повторно используется как общий компактный сервисный картридж.\n\nВсе экземпляры единичного масштаба, +Z вверх, -Y струя, +Y тяга. Название 3way не означает три различных направления. BU условные; игра не меняется. Неподвижная конструкция, постоянного пламени нет.\n')}
for bid,plan in plans.items():write(ROOT/'Blocks'/bid/'composition-plan.md',plan)

m=Part('MA-E01-P01','Средний двигатель — силовая кассета')
m.slab('Lower recessed hull interface',[(-.43,-.62),(.43,-.62),(.50,.57),(.34,.96),(-.34,.96),(-.50,.57)],0,.13,'Dark')
m.section('Angular structural spine',[(-.58,0,.23,.70,.28,.09),(.38,0,.31,.94,.48,.14),(.92,0,.27,.68,.38,.11)],'Titanium')
m.panel('Aft fuel interface',(0,.76,.47),(.62,.32,.07),'Ceramic',.09)
m.box('Recessed fuel manifold',(0,.954,.28),(.43,.028,.15),'Dark',.018)
for x in [-.12,.12]:m.box('Fuel coupling',(x,.976,.28),(.08,.025,.09),'Titanium',.008)
source(m,[socket('hull',[0,0,0],'hull'),socket('chamber',[0,-.12,.46],'chamber')],'Enclosed fuel interfaces; logical hull mounting does not add visible bolts.')

m=Part('MA-E01-P02','Средний двигатель — камера сгорания')
m.section('Pressurized engine casing',[(-.48,0,0,.61,.61,.15),(-.24,0,0,.90,.78,.19),(.40,0,.03,.86,.68,.18),(.80,0,.02,.56,.51,.12)],'Armor')
m.section('Dorsal ceramic shell',[(-.37,0,.31,.48,.10,.03),(-.13,0,.42,.64,.12,.04),(.50,0,.43,.48,.10,.03),(.73,0,.27,.33,.07,.02)],'Ceramic')
for s in [-1,1]:
    m.box('Lateral thermal recess',(s*.452,.11,.02),(.018,.47,.13),'Dark',.003)
    m.box('Chamber diagnostics',(s*.465,.18,.02),(.012,.18,.018),'Signal',.003)
source(m,[socket('root',[0,0,0],'chamber'),socket('nozzle',[0,-.48,0],'nozzle'),socket('thermal-L',[-.43,.05,.05],'thermal'),socket('thermal-R',[.43,.05,.05],'thermal'),socket('service',[0,.30,.48],'accessory')])
nozzle('MA-E01-P03',.37,.65,'Средний двигатель — большое сопло')
m=Part('MA-E01-P04','Средний двигатель — гранёная термопанель')
m.section('Swept thermal shield',[(-.48,0,0,.045,.25,.01),(-.21,0,.05,.09,.46,.02),(.35,0,.04,.09,.44,.02),(.63,0,-.01,.045,.24,.01)],'Ceramic',.005)
for y in [-.16,.03,.22]:m.box('Recessed radiator tile',(.052,y,.02),(.014,.12,.24),'Titanium',.006)
source(m,[socket('root',[0,0,0],'thermal')],'Two instances related by a proper 180 degree Y rotation; no negative scale.')
m=Part('MA-E01-P05','Средний двигатель — компактный сервисный картридж')
m.panel('Compact pressure seal',(0,0,.009),(.44,.33,.018),'Dark',.09,bevel=.001)
m.panel('Flush engine cartridge',(0,0,.026),(.40,.29,.020),'Titanium',.08,bevel=.002)
m.box('Service status inset',(0,-.06,.039),(.13,.018,.006),'Signal',.002)
source(m,[socket('root',[0,0,0],'accessory')],'Explicit compact variant: MA-P06 unit geometry is too wide for the medium engine roof; no implicit scaling.')

m=Part('MA-E02-P01','Тройной двигатель — распределительная рама')
m.slab('Wide hull interface',[(-1.42,-.64),(1.42,-.64),(1.48,.49),(1.20,.93),(-1.20,.93),(-1.48,.49)],0,.14,'Dark')
m.section('Three channel feed manifold',[(.18,0,.30,2.88,.36,.12),(.69,0,.34,2.91,.45,.14),(.94,0,.29,2.46,.31,.11)],'Armor')
m.panel('Dorsal service bridge',(0,.60,.59),(.83,.66,.08),'Ceramic',.18)
for x in [-1,0,1]:
    m.panel('Chamber saddle',(x,-.21,.20),(.69,.90,.15),'Titanium',.14)
    m.box('Fuel branch interface',(x,.959,.33),(.30,.035,.11),'Titanium',.014)
for s in [-1,1]:
    m.section('Swept manifold side cap',[(.02,s*1.31,.34,.15,.25,.04),(.58,s*1.37,.43,.15,.39,.05),(.89,s*1.13,.34,.14,.26,.04)],'Ceramic')
source(m,[socket('hull',[0,0,0],'hull')]+[socket('chamber'+str(i),[x,-.17,.46],'small-chamber') for i,x in enumerate([-1,0,1])]+[socket('service',[0,.60,.63],'accessory')])
m=Part('MA-E02-P02','Тройной двигатель — компактная тяговая камера')
m.section('Compact chamber', [(-.42,0,0,.43,.43,.11),(-.18,0,.02,.66,.56,.15),(.38,0,.04,.65,.51,.13),(.64,0,.02,.43,.38,.10)],'Armor')
m.section('Swept ceramic chamber cap',[(-.30,0,.22,.31,.07,.02),(-.08,0,.32,.44,.09,.025),(.41,0,.28,.39,.07,.02)],'Ceramic')
for s in [-1,1]:m.box('Side diagnostic aperture',(s*.332,.12,.04),(.015,.20,.025),'Signal',.004)
source(m,[socket('root',[0,0,0],'small-chamber'),socket('nozzle',[0,-.42,0],'nozzle')])
nozzle('MA-E02-P03',.255,.53,'Тройной двигатель — малое сопло')

a=Assembly('MA-E01','thruster-med',[1,2],'Средний двигатель')
a.instance('HullCassette','MA-E01-P01');a.instance('Chamber','MA-E01-P02',loc=(0,-.12,.46));a.instance('Nozzle','MA-E01-P03',loc=(0,-.60,.46))
a.instance('Thermal.R','MA-E01-P04',loc=(.43,-.07,.51));a.instance('Thermal.L','MA-E01-P04',loc=(-.43,-.07,.51),rot=(0,math.pi,0));a.instance('ServiceCartridge','MA-E01-P05',loc=(0,.18,.94))
a.save('Static thruster. One logical +Y force point and one -Y exhaust point on Nozzle. No gameplay tuning or physical scale conversion.',frame_end=1)
a.review(view=(4,-6,4),target=(0,-.10,.40),scale=3.45,resolution=800)

a=Assembly('MA-E02','thruster-small-3way',[3,2],'Малый тройной двигатель')
a.instance('FuelManifold','MA-E02-P01')
for i,x in enumerate([-1,0,1]):
    a.instance('Chamber'+str(i),'MA-E02-P02',loc=(x,-.17,.46));a.instance('Nozzle'+str(i),'MA-E02-P03',loc=(x,-.59,.46))
a.instance('ServiceCartridge','MA-E01-P05',loc=(0,.60,.63))
a.save('Three independent, parallel +Y thrust points. Three -Y exhaust points. 3way does not mean three different directions. Static source and viewer asset.',frame_end=1)
a.review(view=(5,-7,5),target=(0,-.05,.38),scale=4.45,resolution=900)
for bid,plan in plans.items():
    write(ROOT/'Blocks'/bid/'README.md',plan+'\nФинальные файлы: '+bid+'.blend, Exports/'+bid+'.glb. Состав — assembly.json, проверка — validation.json. Материалы процедурные PBR: Armor/Ceramic/Titanium/Dark и ограниченная бирюзовая эмиссия в горловине/диагностике. Файловых текстур нет. Собственные детали сохранены отдельно; Оба двигателя используют общий компактный картридж MA-E01-P05; прежние исходники не изменены. GLB — для просмотра, без установки в игру.\n')
print('ENGINES_BUILT',flush=True)
