"""Rebuild the final CorporateHiTech Bastion and Helion editable assets."""
import csv, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = {r['ID']:r for r in csv.DictReader((ROOT.parent/'Catalog/blocks.csv').open(encoding='utf-8-sig'))}

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(data, str): data=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    path.write_bytes(data.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))

def box(id,pos,size,mat='armor',r=.008,rot=None):
    d=dict(id=id,shape='roundedBox',position=pos,size=size,radius=r,material=mat)
    if rot:d['rotationEulerXYZ']=rot
    return d

def hull(id,pos,size,mat='armor',top=.8,cut=.08,rot=None):
    w,l,h=size; x=w/2;y=l/2;c=min(cut,x*.7,y*.7)
    d=dict(id=id,shape='loft',position=pos,outline=[[-x+c,-y],[x-c,-y],[x,-y+c],[x,y-c],[x-c,y],[-x+c,y],[-x,y-c],[-x,-y+c]],levels=[dict(z=-h/2,scale=[.94,.94]),dict(z=-h/2+.012,scale=[1,1]),dict(z=h/2-.016,scale=[1,1]),dict(z=h/2,scale=[top,top])],material=mat)
    if rot:d['rotationEulerXYZ']=rot
    return d

def socket(id,pos,normal,compatible,role='mount'):
    return dict(id=id,role=role,position=pos,normal=normal,up=[0,1,0] if abs(normal[2]) else [0,0,1],parentNode='root',compatible=compatible)

def bounds(geo):
    points=[]
    for g in geo:
        if g['shape']=='loft': vs=[[x*v['scale'][0],y*v['scale'][1],v['z']] for v in g['levels'] for x,y in g['outline']]
        else:vs=[[x*g['size'][0]/2,y*g['size'][1]/2,z*g['size'][2]/2] for x in [-1,1] for y in [-1,1] for z in [-1,1]]
        a,b,c=g.get('rotationEulerXYZ',[0,0,0]);ca,sa=math.cos(a),math.sin(a);cb,sb=math.cos(b),math.sin(b);cc,sc=math.cos(c),math.sin(c)
        for x,y,z in vs:
            # Three.js Euler XYZ = Rx Ry Rz.
            x,y=x*cc-y*sc,x*sc+y*cc
            x,z=x*cb+z*sb,-x*sb+z*cb
            y,z=y*ca-z*sa,y*sa+z*ca
            points.append([x+g['position'][0],y+g['position'][1],z+g['position'][2]])
    lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    return dict(min=lo,max=hi,size=[hi[i]-lo[i] for i in range(3)])

PARTS={}
def part(id,title,geo,sockets,functions=None):
    slots=sorted(set(g['material'] for g in geo))
    d=dict(schema='cht-authoring-part/1',id=id,version='1.0.0',project='SS',style='CorporateHiTech',title=title,source='part.json',units='model-unit',handedness='right',up='+Z',forward='+Y',origin=[0,0,0],pivot=[0,0,0],restPose=dict(translation=[0,0,0],rotationEulerXYZ=[0,0,0],scale=[1,1,1]),scaling=dict(uniformOnly=True,allowedRange=[1,1]),geometry=geo,materialLibrary='../../Materials/materials.json',materialSlots=slots,texturing=dict(method='uniform procedural PBR; viewer box-projected UV for optional SharedTextures',rasterTextures=[],uvRequired=False),emission=[dict(id=g['id'],material=g['material'],defaultEnabled=True,intensityUnit='Three.js multiplier',color='#25bfff' if g['material']=='cyan' else '#1686bf',intensity=2.5 if g['material']=='cyan' else .65) for g in geo if g['material'] in ('cyan','glass')],attachments=sockets,attachmentAreas=[],functionalPoints=functions or [],animations=[],bounds=bounds(geo))
    PARTS[id]=d;write(ROOT/'Parts'/id/'part.json',d)
    write(ROOT/'Parts'/id/'README.md',f'# {id} — {title}\n\nРедактируемая параметрическая деталь 1.0.0. +Z вверх, +Y вперёд, model-unit, единичный масштаб. Материалы: '+', '.join(slots)+'. Процедурный PBR, растровых зависимостей нет; SharedTextures назначаются в общем просмотрщике. Голубые области имеют эмиссию из общей библиотеки. Крепления и функциональные точки находятся в part.json; логические маркеры не являются мешами. Самостоятельной анимации нет.\n')

def inst(id,p,parent=None,pos=None,ps=None):
    return dict(id=id,partId=p,partVersion='1.0.0',source=f'../../Parts/{p}/part.json',parent=parent,translation=pos or [0,0,0],rotationEulerXYZ=[0,0,0],scale=[1,1,1],attachment=dict(parentSocket=ps,childSocket='base') if parent else None)

def assembly(id,cat,title,instances,speed,description):
    row=CAT[cat]
    next(i for i in instances if i['id']=='yaw')['joint']=dict(type='revolute',axis=[0,0,1],pivot=[0,0,0],rangeDegrees=[0,360],speedDegreesPerSecond=speed)
    d=dict(schema='cht-authoring-assembly/1',id=id,version='1.0.0',title=title,catalogId=cat,catalogReference='../../../Catalog/blocks.csv',catalogGrid=[int(row['Ширина_клеток']),int(row['Высота_клеток'])],catalogRotationPivot=[1.5,1.5] if id=='CHT-W05' else [.5,.5],units='model-unit',up='+Z',forward='+Y',scaleNote='Catalogue grid cells are not metres; visual dimensions are authoring model units. Muzzle XY offsets relative to catalogue pivot are preserved.',instances=instances,animations=[dict(id='yaw-demo',node='yaw',axis=[0,0,1],rangeDegrees=[0,360],durationSeconds=360/speed,loop=True,interpolation='LINEAR',gameplaySource=f'catalog RotateSpeedDegreesPerSecond={speed}',restDegrees=0)],catalogSnapshot=row)
    write(ROOT/'Blocks'/id/'assembly.json',d)
    write(ROOT/'Blocks'/id/'README.md',f'# {id} — {title}\n\n{description}\n\nКаталог: `{cat}`, сетка {row["Размер_сетки_без_поворота"]} клеток; клетки не метры. Дуга 360°, скорость {speed}°/с. Исходная геометрия в Parts/*/part.json; сборка в assembly.json. Основание неподвижно; yaw вращает все дочерние узлы. Масштаб экземпляров единичный.\n\nДетали: '+', '.join(sorted(set(i['partId'] for i in instances)))+'.\n\nБелая многослойная броня, тёмные технологические швы, голубая эмиссия, процедурное покрытие. Существующий просмотрщик поддерживает SharedTextures. Игровой баланс не изменяется. Это авторский ассет, не игровой формат; коллайдеры и LOD не заданы каталогом. Производные экспорты хранятся отдельно в Exports/.\n')

def plan(id,text):write(ROOT/'Blocks'/id/'composition-plan.md',text)

# Plans precede all geometry and assemblies.
plan('CHT-W05','# Состав Bastion\n\nКаталог fleet-rocket-bastion: 3x3, четыре пусковых канала, 360°, 45°/с. Четыре muzzle X=-0.731,-0.244,0.244,0.731 и Y=0.55 относительно pivot.\n\nПроверены CHT-P01..P07: основание и корпус слишком малы для четырёхканальной широкой установки; двойные лазерные эмиттеры не совместимы. Новые отдельные детали: W05-BASE — широкое шестиугольное основание; W05-YAW — поворотный мост с четырьмя интерфейсами; W05-CASSETTE — открытая бронированная ракетная кассета, четыре экземпляра; W05-SENSOR — центральная мачта; W05-POWER — задняя силовая секция. Все крепления Z-ориентированы, origin в монтажной точке. Полный каталог сохраняется в сборке, игровые значения не интерпретируются как DPS.\n')
plan('CHT-W06','# Состав Helion\n\nКаталог continuous-laser-turret: 1x3, один continuous-emitter, 360°, 90°/с; muzzle X=0,Y=0.5 относительно pivot.\n\nПроверены CHT-P01..P07: геометрия короткой двухствольной установки не подходит узкому длинному оптическому копью. Новые детали: W06-BASE — узкий опорный постамент; W06-YAW — вращающийся силовой позвоночник; W06-OPTIC — один большой оптический излучатель; W06-RADIATOR — высокие разрезные теплоотводящие пластины, два экземпляра; W06-CAPACITOR — задняя силовая кассета. Не создавать дополнительные функциональные дульные точки. Стыки и интерфейсы единичного масштаба Z-ориентированы.\n')

# Bastion: low wide deck with four independent visibly hollow launch canisters.
g=[hull('under-deck',[0,0,.07],[2.3,1.8,.14],'graphite',.95,.25),hull('armored-deck',[0,0,.2],[2.14,1.65,.2],top=.88,cut=.27),hull('bearing-platform',[0,0,.34],[1.2,1.15,.12],'edge',.88,.25)]
for x in [-.9,.9]:
    for y in [-.58,.58]:g += [hull(f'foot-{x}-{y}',[x,y,.1],[.4,.45,.2],top=.9),box(f'index-{x}-{y}',[x,y,.206],[.16,.035,.009],'cyan')]
part('CHT-W05-BASE','Bastion: широкая опорная палуба',g,[socket('yaw',[0,0,.4],[0,0,1],'CHT-W05-YAW.base')])
g=[hull('bridge',[0,-.22,.15],[1.95,1.25,.3],'graphite',.9,.2),hull('front-shield',[0,.23,.19],[1.88,.33,.3],top=.82),hull('central-spine',[0,-.27,.42],[.22,1.03,.26],top=.75)]
for x in [-1,1]:g += [hull(f'wing-{x}',[x*.96,-.32,.27],[.27,.87,.35],top=.72),box(f'wing-light-{x}',[x*1.03,-.29,.454],[.022,.55,.012],'cyan')]
s=[socket('base',[0,0,0],[0,0,-1],'CHT-W05-BASE.yaw')]
for i,x in enumerate([-.731,-.244,.244,.731]):s.append(socket(f'launcher-{i}',[x,-.15,.34],[0,0,1],'CHT-W05-CASSETTE.base'))
s += [socket('sensor',[0,-.63,.55],[0,0,1],'CHT-W05-SENSOR.base'),socket('power',[0,-.9,.18],[0,0,1],'CHT-W05-POWER.base')]
part('CHT-W05-YAW','Bastion: поворотный мост',g,s)
g=[hull('rear-shell',[0,-.53,.26],[.442,.34,.5],top=.88,cut=.08),hull('floor',[0,.03,.045],[.43,1.34,.09],'graphite',.96,.05)]
# Square chamber assembled from rails; aperture is genuinely open, not a painted face.
for sign in [-1,1]:
    g += [hull(f'side-wall-{sign}',[sign*.192,.02,.29],[.058,1.3,.44],top=.96,cut=.018),hull(f'roof-half-{sign}',[sign*.103,.02,.512],[.21,1.29,.08],top=.9,cut=.025),box(f'guide-light-{sign}',[sign*.144,.48,.085],[.014,.36,.012],'cyan'),box(f'mouth-side-{sign}',[sign*.194,.675,.29],[.075,.05,.51],'edge'),box(f'roof-seam-{sign}',[sign*.19,-.15,.555],[.016,.53,.009],'cyan')]
for z in [.045,.535]:g.append(box(f'mouth-crossbar-{z}',[0,.675,z],[.44,.05,.07],'armor'))
g += [box('chamber-dark-back',[0,-.365,.285],[.32,.018,.35],'rubber'),hull('missile-body',[0,.03,.25],[.23,.67,.24],'edge',.86,.055),hull('missile-nose',[0,.405,.25],[.23,.24,.18],'armor',.3,.055,rot=[-math.pi/2,0,0]),box('ready-light',[0,-.31,.555],[.15,.09,.01],'cyan')]
part('CHT-W05-CASSETTE','Bastion: одиночная открытая ракетная кассета',g,[socket('base',[0,0,0],[0,0,-1],'CHT-W05-YAW.launcher-*')],[dict(id='muzzle',role='missile-launch',parentNode='root',position=[0,.7,.29],direction=[0,1,0],up=[0,0,1],coordinateSpace='part-local')])
g=[hull('mast',[0,0,.2],[.17,.22,.4],'graphite',.75),hull('sensor-head',[0,0,.42],[.31,.32,.18],top=.84),box('sensor-window',[0,.162,.43],[.19,.015,.07],'glass'),box('roof-line',[0,0,.515],[.11,.16,.009],'cyan')]
part('CHT-W05-SENSOR','Bastion: командная оптическая мачта',g,[socket('base',[0,0,0],[0,0,-1],'CHT-W05-YAW.sensor')])
g=[hull('power',[0,0,.19],[1.45,.38,.38],'graphite',.86),hull('power-cap',[0,0,.38],[1.35,.34,.08],top=.88)]
for i in range(9):g.append(box(f'vent-{i}',[-.54+i*.135,-.198,.2],[.055,.022,.21],'edge'))
g.append(box('rear-index',[0,-.211,.33],[.63,.012,.025],'cyan'))
part('CHT-W05-POWER','Bastion: задний силовой коллектор',g,[socket('base',[0,0,0],[0,0,-1],'CHT-W05-YAW.power')])
ii=[inst('foundation','CHT-W05-BASE'),inst('yaw','CHT-W05-YAW','foundation',[0,0,.4],'yaw')]
for i,x in enumerate([-.731,-.244,.244,.731]):ii.append(inst(f'launcher-{i}','CHT-W05-CASSETTE','yaw',[x,-.15,.34],f'launcher-{i}'))
ii += [inst('sensor','CHT-W05-SENSOR','yaw',[0,-.63,.55],'sensor'),inst('power','CHT-W05-POWER','yaw',[0,-.9,.18],'power')]
assembly('CHT-W05','fleet-rocket-bastion','Bastion / четырёхкассетная ракетная башня',ii,45,'Широкая приземистая установка: четыре открытых квадратных ракетных канала, независимые бронекассеты, высокий центральный датчик и задняя силовая гребёнка. Ровно четыре функциональных дульных точки; видимые ракеты — декоративные заполнители. SeekMissile, урон 850, дальность 420 — исходные значения каталога, без пересчёта в DPS.')

# Helion: narrow long spine and tall separated cooling sails, a single square optic.
g=[hull('sole',[0,0,.06],[.9,1.2,.12],'graphite',.93,.15),hull('sloped-plinth',[0,0,.2],[.78,1.06,.23],top=.65,cut=.17),hull('neck',[0,0,.37],[.46,.53,.18],'edge',.88)]
for sign in [-1,1]:g.append(box(f'edge-index-{sign}',[sign*.31,.04,.316],[.02,.48,.01],'cyan'))
part('CHT-W06-BASE','Helion: узкий постамент',g,[socket('yaw',[0,0,.46],[0,0,1],'CHT-W06-YAW.base')])
g=[hull('keel',[0,-.55,.12],[.49,1.95,.24],'graphite',.8,.1),hull('long-white-spine',[0,-.53,.3],[.41,1.86,.21],top=.66,cut=.1),box('dorsal-line',[0,-.56,.408],[.034,1.35,.012],'cyan'),hull('optic-neck',[0,.08,.29],[.44,.4,.3],'edge',.83)]
s=[socket('base',[0,0,0],[0,0,-1],'CHT-W06-BASE.yaw'),socket('optic',[0,.16,.3],[0,0,1],'CHT-W06-OPTIC.base'),socket('power',[0,-1.22,.31],[0,0,1],'CHT-W06-CAPACITOR.base')]
for sign in [-1,1]:s.append(socket(f'radiator-{sign}',[sign*.28,-.68,.21],[0,0,1],'CHT-W06-RADIATOR.base'))
part('CHT-W06-YAW','Helion: длинный силовой позвоночник',g,s)
g=[hull('optic-body',[0,-.08,.15],[.48,.46,.42],'graphite',.84),hull('optic-dorsal',[0,-.03,.38],[.4,.49,.07],top=.8)]
for sign in [-1,1]:
    g += [hull(f'lens-jaw-{sign}',[sign*.243,.16,.15],[.08,.42,.44],top=.8,cut=.018),box(f'jaw-light-{sign}',[sign*.275,.13,.15],[.012,.22,.15],'cyan')]
for z in [-.055,.355]:g.append(box(f'aperture-frame-{z}',[0,.315,z],[.49,.05,.07],'armor'))
g += [box('lens-inset',[0,.282,.15],[.35,.015,.32],'glass'),box('lens-core',[0,.296,.15],[.24,.012,.21],'cyan'),box('lens-split',[0,.305,.15],[.012,.007,.22],'edge')]
part('CHT-W06-OPTIC','Helion: один мощный непрерывный излучатель',g,[socket('base',[0,0,0],[0,0,-1],'CHT-W06-YAW.optic')],[dict(id='muzzle',role='continuous-beam',parentNode='root',position=[0,.34,.15],direction=[0,1,0],up=[0,0,1],coordinateSpace='part-local')])
g=[hull('coolant-rail',[0,0,.06],[.12,1.21,.12],'edge',.88,cut=.035)]
# Four tall swept sails with genuine gaps. Not a solid rectangular box.
for i in range(4):
    y=-.44+i*.29;height=.46+(3-i)*.11
    g += [hull(f'sail-{i}',[0,y,.1+height/2],[.075,.235,height],'armor',.56,cut=.025,rot=[-.14,0,0]),box(f'sail-core-{i}',[.041,y,.11+height*.44],[.014,.16,height*.59],'graphite'),box(f'sail-light-{i}',[0,y+.038,.1+height],[.04,.14,.012],'cyan')]
part('CHT-W06-RADIATOR','Helion: разрезная радиаторная гребёнка',g,[socket('base',[0,0,0],[0,0,-1],'CHT-W06-YAW.radiator-*')])
g=[hull('capacitor',[0,0,.16],[.48,.5,.32],'graphite',.88),hull('capacitor-lid',[0,-.02,.34],[.46,.45,.09],top=.85)]
for sign in [-1,1]:g += [hull(f'flank-cap-{sign}',[sign*.22,0,.2],[.07,.42,.24],top=.75),box(f'charge-{sign}',[sign*.263,0,.2],[.008,.23,.035],'cyan')]
for i in range(5):g.append(box(f'rear-fin-{i}',[-.15+i*.075,-.26,.17],[.028,.07,.21],'edge'))
part('CHT-W06-CAPACITOR','Helion: накопитель и силовой хвост',g,[socket('base',[0,0,0],[0,0,-1],'CHT-W06-YAW.power')])
ii=[inst('foundation','CHT-W06-BASE'),inst('yaw','CHT-W06-YAW','foundation',[0,0,.46],'yaw'),inst('optic','CHT-W06-OPTIC','yaw',[0,.16,.3],'optic'),inst('power','CHT-W06-CAPACITOR','yaw',[0,-1.22,.31],'power')]
for sign in [-1,1]:ii.append(inst(f'radiator-{sign}','CHT-W06-RADIATOR','yaw',[sign*.28,-.68,.21],f'radiator-{sign}'))
assembly('CHT-W06','continuous-laser-turret','Helion / непрерывный лазер',ii,90,'Узкое длинное оптическое копьё с единственным большим квадратным излучателем и двумя высокими разрезными радиаторными гребнями. Силуэт продольный и высокий, отличен от широкой ракетной палубы. Один muzzle, ContinuousBeam, урон 200 и дальность 100 из каталога; значение урона не является уроном обычного выстрела.')

# Source validation: all references, versions, materials, poses, socket compatibility.
for bid in ['CHT-W05','CHT-W06']:
    a=json.loads((ROOT/'Blocks'/bid/'assembly.json').read_text(encoding='utf-8')); nodes={i['id']:i for i in a['instances']}; checks=[]
    for i in a['instances']:
        p=PARTS[i['partId']]; assert p['version']==i['partVersion'];assert (ROOT/'Blocks'/bid/i['source']).resolve().exists()
        assert all(g['material'] in json.loads((ROOT/'Materials/materials.json').read_text()) for g in p['geometry'])
        if i['parent']:
            pp=PARTS[nodes[i['parent']]['partId']];ps=next(s for s in pp['attachments'] if s['id']==i['attachment']['parentSocket']);cs=next(s for s in p['attachments'] if s['id']=='base')
            assert all(abs(ps['position'][k]-i['translation'][k]-cs['position'][k])<1e-8 for k in range(3));assert sum(ps['normal'][k]*cs['normal'][k] for k in range(3))==-1
        checks.append(i['id'])
    muzzles=[]
    for i in a['instances']:
        for f in PARTS[i['partId']]['functionalPoints']:
            pos=f['position'][:];node=i
            while node:
                pos=[pos[k]+node['translation'][k] for k in range(3)];node=nodes.get(node['parent'])
            muzzles.append(dict(instance=i['id'],position=pos,direction=f['direction']))
    assert len(muzzles)==(4 if bid=='CHT-W05' else 1)
    expected_y=.55 if bid=='CHT-W05' else .5
    assert all(abs(m['position'][1]-expected_y)<1e-8 for m in muzzles)
    write(ROOT/'Blocks'/bid/'validation.json',dict(referenceAndSocketChecks='passed',instances=checks,muzzles=muzzles,animation=dict(node='yaw',rangeDegrees=[0,360],durationSeconds=a['animations'][0]['durationSeconds']),bounds='computed from parameter vertices including rotations',visualAcceptance='Root agent performs final shared-viewer inspection and glTF export; no intermediate variants generated.'))
print('Created 10 independent parts, Bastion: 8 instances / 4 muzzles; Helion: 6 instances / 1 muzzle. References and socket poses passed.')
