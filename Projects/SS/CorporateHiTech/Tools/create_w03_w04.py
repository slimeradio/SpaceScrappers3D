"""Final authoring sources for Cyclone and Assault; isolated CorporateHiTech scope."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.0.0'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n' if not isinstance(value, str) else value
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8'))

def box(id, p, s, mat='armor', rot=None):
    g = dict(id=id, shape='roundedBox', position=p, size=s, radius=min(.009, min(s)/5), material=mat)
    if rot: g['rotationEulerXYZ'] = rot
    return g

def outline(w, d, c):
    x,y=w/2,d/2
    return [[-x+c,-y],[x-c,-y],[x,-y+c],[x,y-c],[x-c,y],[-x+c,y],[-x,y-c],[-x,-y+c]]

def plate(id, p, s, mat='armor', taper=.86, cut=.045, rot=None):
    w,d,h=s
    g=dict(id=id, shape='loft', position=p, outline=outline(w,d,min(cut,w/3,d/3)), levels=[dict(z=-h/2,scale=[.95,.95]),dict(z=-h/2+.012,scale=[1,1]),dict(z=h/2-.012,scale=[1,1]),dict(z=h/2,scale=[taper,taper])], material=mat)
    if rot: g['rotationEulerXYZ']=rot
    return g

def socket(id,p,n,up=(0,1,0),compatible='',role='mechanical'):
    return dict(id=id,position=p,normal=n,up=list(up),compatible=compatible,role=role,parentNode='root')

def part(id,title,geo,attachments,lo,hi,points=None,aliases=None):
    data=dict(schema='cht-authoring-part/1',id=id,version=VERSION,project='SS',style='CorporateHiTech',title=title,source='part.json',units='model-unit',handedness='right',up='+Z',forward='+Y',origin=[0,0,0],pivot=[0,0,0],restPose=dict(translation=[0,0,0],rotationEulerXYZ=[0,0,0],scale=[1,1,1]),scaling=dict(uniformOnly=True,allowedRange=[1,1]),geometry=geo,materialLibrary='../../Materials/materials.json',materialSlots=sorted(set(g['material'] for g in geo)),texturing=dict(method='uniform procedural PBR; optional SharedTextures via existing viewer box-projection UV',rasterTextures=[],uvRequired=False),emission=[dict(id=g['id'],geometry=g['id'],material='cyan',color='#25bfff',intensity=2.5,intensityUnit='Three.js multiplier',defaultEnabled=True) for g in geo if g['material']=='cyan'],attachments=attachments,attachmentAreas=[],functionalPoints=points or [],animations=[],bounds=dict(min=lo,max=hi,size=[round(b-a,6) for a,b in zip(lo,hi)]))
    if aliases: data['compatibilityAliases']=aliases
    write(ROOT/'Parts'/id/'part.json',data)
    write(ROOT/'Parts'/id/'README.md',f'# {id} — {title}\n\nВерсия {VERSION}. Редактируемая параметрическая геометрия: part.json. +Z вверх, +Y вперёд, правая система, model-unit (не метры). Единичный масштаб.\n\nБелое процедурное покрытие armor, тёмная механика graphite/rubber, металлические кромки edge и отдельные голубые emissive-полосы cyan (2.5). Исходные растровые карты не нужны; выбор SharedTextures доступен в общем просмотрщике. Логические sockets и functionalPoints не входят в видимую геометрию. Самостоятельных анимаций нет.\n')
    return data

def instance(id,pid,parent,p,ps=None,cs='base'):
    v=VERSION if pid.startswith('CHT-W') else '1.1.0'
    return dict(id=id,partId=pid,partVersion=v,source=f'../../Parts/{pid}/part.json',parent=parent,translation=p,rotationEulerXYZ=[0,0,0],scale=[1,1,1],attachment=dict(parentSocket=ps,childSocket=cs) if ps else None)

def ring(geo,id,y,rx,rz,width,mat='edge'):
    # Eight individually bevelled segments form a true open aperture, no capped cylinder.
    for k in range(8):
        a=k*math.pi/4
        b=(k+1)*math.pi/4
        x1,z1=rx*math.cos(a),rz*math.sin(a)
        x2,z2=rx*math.cos(b),rz*math.sin(b)
        length=math.hypot(x2-x1,z2-z1)
        geo.append(box(f'{id}-{k}',[(x1+x2)/2,y,(z1+z2)/2],[length+.012,width,.025],mat,[0,-math.atan2(z2-z1,x2-x1),0]))

def make():
    with (ROOT.parent/'Catalog/blocks.csv').open(encoding='utf-8-sig',newline='') as f:
        rows={r['ID']:r for r in csv.DictReader(f)}
    specs=[('CHT-W03','fleet-minigun-cyclone',240,2,'Cyclone — двухканальный скорострельный пулемёт'),('CHT-W04','fleet-shotgun-assault',180,1,'Assault — широкий штурмовой дробовик')]
    for bid,cid,speed,count,title in specs:
        write(ROOT/'Blocks'/bid/'composition-plan.md',f'# План состава {bid}\n\nКаталог: {cid}, сетка 2×2 клетки; клетки не метры и не граница меша. Стволов: {count}; дуга 360°, скорость {speed}°/с.\n\n| Деталь | Решение | Совместимость и причина |\n|---|---|---|\n| CHT-P01 1.1.0 | Повторно использовать | Гранёное основание и bearing подходят; масштаб 1 |\n| CHT-P02 1.1.0 | Повторно использовать | Поворотный узел, base к P01.bearing; head к интерфейсу P03.base |\n| {bid}-HULL | Создать новую | Корпус с интерфейсом P03.base и характерным силуэтом этого оружия |\n| {bid}-BARREL | Создать новую | Открытый гранёный канал, functionalPoint muzzle; число экземпляров по CSV |\n| {bid}-SIDE | Создать новую | Отдельная боковая броня/подача, не соответствует старым узким щекам P04 |\n| {bid}-SIGHT | Создать новую | Отдельная низкая оптика, привязка к собственному корпусу |\n\nСначала закончить четыре детали каждого блока, затем собрать экземпляры. Общие материалы неизменны; процедурное PBR и геометрическая эмиссия. Внешние стили и проекты не использовать. Промежуточные модели/HTML/превью по запросу пользователя не создавать.\n')

    # W03: narrow elongated twin rails, stepped rear receiver, tall independent side feed pods.
    bid='CHT-W03'; h=[]
    h += [plate('receiver-keel',[0,-.16,.125],[.86,1.03,.25],'graphite'),plate('receiver',[0,-.20,.29],[.84,.94,.30]),plate('raised-spine',[0,-.31,.46],[.18,.65,.12],cut=.035),plate('rear-power-pack',[0,-.69,.24],[.53,.23,.29],'graphite'),plate('rear-service-cap',[0,-.69,.40],[.56,.24,.07]),plate('front-split-support',[0,.22,.25],[.83,.25,.28],'graphite')]
    for side in [-1,1]:
        h += [plate(f'roof-step-{side}',[side*.27,-.25,.46],[.22,.71,.075]),box(f'roof-light-{side}',[side*.27,-.25,.505],[.022,.45,.009],'cyan'),plate(f'front-saddle-{side}',[side*.254,.17,.34],[.30,.29,.30],'edge')]
    for k in range(6): h.append(box(f'back-vent-{k}',[0,-.812,.20+k*.032],[.34,.016,.012],'rubber'))
    att=[socket('base',[0,0,0],[0,0,-1],compatible='CHT-P02.head',role='head-in'),socket('sight',[0,-.17,.52],[0,0,1],compatible=bid+'-SIGHT.base')]
    for sign,name in [(-1,'L'),(1,'R')]:
        att += [socket('barrel-'+name,[sign*.254,.25,.33],[0,1,0],up=(0,0,1),compatible=bid+'-BARREL.base'),socket('side-'+name,[sign*.53,-.28,.18],[0,0,1],compatible=bid+'-SIDE.base')]
    part(bid+'-HULL','Cyclone: узкий составной приёмник',h,att,[-.43,-.83,0],[.43,.345,.52],aliases=['CHT-P03.base'])
    g=[plate('barrel-core',[0,.46,0],[.145,.145,.92],'graphite',.96,.025,[-math.pi/2,0,0]),plate('rear-shroud',[0,.12,0],[.235,.235,.24],'armor',.92,.04,[-math.pi/2,0,0]),plate('front-collar',[0,.88,0],[.23,.23,.13],'armor',.92,.045,[-math.pi/2,0,0])]
    for sx in [-1,1]:
        g += [box(f'longitudinal-rail-{sx}',[sx*.105,.51,.07],[.035,.67,.06],'edge'),box(f'rail-light-{sx}',[sx*.109,.52,.105],[.017,.42,.008],'cyan')]
        for k in range(5): g.append(box(f'vent-{sx}-{k}',[sx*.124,.21+k*.11,0],[.015,.045,.067],'rubber'))
    ring(g,'open-muzzle',.971,.10,.10,.042)
    # Recessed black polygon is behind the open frame and visibly reads as bore depth.
    g.append(dict(id='bore-depth',shape='cylinder',position=[0,.942,0],radius=.074,radiusTop=.074,depth=.006,segments=8,axis='Y',material='rubber'))
    part(bid+'-BARREL','Cyclone: один скорострельный канал',g,[socket('base',[0,0,0],[0,-1,0],up=(0,0,1),compatible=bid+'-HULL.barrel-L|'+bid+'-HULL.barrel-R')],[-.133,0,-.12],[.133,.992,.12],[dict(id='muzzle',role='projectile-muzzle',parentNode='root',position=[0,.995,0],direction=[0,1,0],up=[0,0,1],coordinateSpace='local')])
    g=[plate('feed-core',[0,0,.15],[.29,.64,.30],'graphite'),plate('feed-upper-armor',[0,-.015,.32],[.32,.59,.13]),plate('front-angle',[0,.30,.18],[.27,.15,.29]),plate('rear-angle',[0,-.31,.18],[.27,.16,.25]),box('feed-status',[0,-.015,.39],[.02,.35,.009],'cyan')]
    for k in range(5):g.append(box(f'feed-fin-{k}',[0,-.19+k*.085,.015],[.22,.028,.025],'edge'))
    part(bid+'-SIDE','Cyclone: бронекассета подачи',g,[socket('base',[0,0,0],[0,0,-1],compatible=bid+'-HULL.side-L|'+bid+'-HULL.side-R')],[-.16,-.39,0],[.16,.375,.395])
    g=[plate('sight-base',[0,0,.035],[.19,.21,.07],'graphite'),plate('optics-hood',[0,0,.09],[.23,.23,.085]),box('optical-window',[0,.118,.086],[.14,.008,.035],'glass'),box('rangefinder-light',[0,.124,.119],[.07,.007,.008],'cyan')]
    part(bid+'-SIGHT','Cyclone: низкий дальномер',g,[socket('base',[0,0,0],[0,0,-1],compatible=bid+'-HULL.sight')],[-.115,-.115,0],[.115,.128,.135])

    # W04: wide low manta-like cheeks and one broad short aperture; different silhouette.
    bid='CHT-W04';h=[plate('broad-keel',[0,-.08,.10],[1.18,.97,.20],'graphite'),plate('low-receiver',[0,-.13,.245],[1.12,.85,.27],taper=.76,cut=.13),plate('center-hood',[0,-.16,.415],[.47,.75,.13],cut=.10),plate('rear-wedge',[0,-.59,.22],[.86,.27,.25]),plate('chin-keel',[0,.30,.12],[.62,.43,.16],'graphite')]
    for sign in [-1,1]:
        h += [plate(f'shoulder-{sign}',[sign*.42,-.16,.36],[.27,.70,.12],cut=.075),box(f'angular-light-{sign}',[sign*.39,-.06,.427],[.035,.40,.008],'cyan'),plate(f'rear-lock-{sign}',[sign*.36,-.65,.35],[.18,.21,.09],'edge')]
    for k in range(5):h.append(box(f'rear-vent-{k}',[(k-2)*.12,-.73,.21],[.065,.015,.10],'rubber'))
    att=[socket('base',[0,0,0],[0,0,-1],compatible='CHT-P02.head',role='head-in'),socket('barrel',[0,.28,.27],[0,1,0],up=(0,0,1),compatible=bid+'-BARREL.base'),socket('sight',[0,-.21,.48],[0,0,1],compatible=bid+'-SIGHT.base')]
    for sign,name in [(-1,'L'),(1,'R')]:att.append(socket('side-'+name,[sign*.68,-.06,.11],[0,0,1],compatible=bid+'-SIDE.base'))
    part(bid+'-HULL','Assault: широкий низкий корпус',h,att,[-.59,-.745,0],[.59,.515,.48],aliases=['CHT-P03.base'])
    g=[plate('short-chamber',[0,.18,0],[.63,.39,.36],'graphite',.9,.07),plate('upper-cowl',[0,.24,.17],[.65,.48,.10],cut=.07),plate('lower-cowl',[0,.22,-.17],[.56,.45,.09],cut=.07)]
    # One broad hexagonal/octal firing channel, no false extra barrels for the eight pellets.
    ring(g,'muzzle-body',.49,.305,.19,.17,'armor')
    ring(g,'muzzle-lip',.585,.275,.16,.035,'edge')
    g.append(plate('bore-depth',[0,.485,0],[.44,.245,.008],'rubber',.95,.045,[-math.pi/2,0,0]))
    for sign in [-1,1]:
        g += [box(f'side-skid-{sign}',[sign*.31,.23,0],[.055,.36,.17],'edge'),box(f'side-status-{sign}',[sign*.343,.24,.02],[.009,.18,.025],'cyan')]
        for k in range(3):g.append(box(f'chamber-slot-{sign}-{k}',[sign*.24,.12+k*.10,.223],[.095,.025,.009],'rubber'))
    part(bid+'-BARREL','Assault: единый широкий канал',g,[socket('base',[0,0,0],[0,-1,0],up=(0,0,1),compatible=bid+'-HULL.barrel')],[-.35,-.015,-.215],[.35,.61,.228],[dict(id='muzzle',role='projectile-muzzle',parentNode='root',position=[0,.61,0],direction=[0,1,0],up=[0,0,1],coordinateSpace='local')])
    g=[plate('wing-underlay',[0,0,.09],[.33,.80,.18],'graphite',.87,.08),plate('swept-wing',[0,0,.22],[.39,.77,.20],taper=.70,cut=.095),plate('wing-cap',[0,-.14,.34],[.23,.36,.09],cut=.065),box('wing-index',[0,-.12,.389],[.025,.21,.008],'cyan')]
    for k in range(4):g.append(box(f'cooling-slit-{k}',[0,.08+k*.07,.326],[.17,.018,.009],'rubber'))
    part(bid+'-SIDE','Assault: широкая бронещека',g,[socket('base',[0,0,0],[0,0,-1],compatible=bid+'-HULL.side-L|'+bid+'-HULL.side-R')],[-.195,-.4,0],[.195,.4,.394])
    g=[plate('sensor-foot',[0,0,.025],[.25,.24,.05],'graphite'),plate('sensor-cap',[0,0,.07],[.32,.25,.07]),box('horizontal-optic',[0,.13,.065],[.235,.009,.027],'glass'),box('sensor-line',[0,.136,.092],[.19,.008,.008],'cyan')]
    part(bid+'-SIGHT','Assault: широкая оптическая планка',g,[socket('base',[0,0,0],[0,0,-1],compatible=bid+'-HULL.sight')],[-.16,-.125,0],[.16,.14,.108])

    # Assembly only after every detail is complete and saved.
    for bid,cid,speed,count,title in specs:
        nodes=[instance('foundation','CHT-P01',None,[0,0,0]),instance('yaw','CHT-P02','foundation',[0,0,.23],'bearing'),instance('head',bid+'-HULL','yaw',[0,0,.14],'head')]
        nodes[1]['joint']=dict(type='revolute',axis=[0,0,1],rangeDegrees=[0,360],continuous=True,restDegrees=0)
        if count==2:
            for sign,name in [(-1,'L'),(1,'R')]:
                nodes += [instance('barrel-'+name,bid+'-BARREL','head',[sign*.254,.25,.33],'barrel-'+name),instance('side-'+name,bid+'-SIDE','head',[sign*.53,-.28,.18],'side-'+name)]
            nodes.append(instance('sight',bid+'-SIGHT','head',[0,-.17,.52],'sight'))
        else:
            nodes.append(instance('barrel',bid+'-BARREL','head',[0,.28,.27],'barrel'))
            for sign,name in [(-1,'L'),(1,'R')]:nodes.append(instance('side-'+name,bid+'-SIDE','head',[sign*.68,-.06,.11],'side-'+name))
            nodes.append(instance('sight',bid+'-SIGHT','head',[0,-.21,.48],'sight'))
        data=dict(schema='cht-authoring-assembly/1',id=bid,version=VERSION,title=title,catalogId=cid,catalogReference='../../../Catalog/blocks.csv',catalogGrid=[2,2],catalogRotationPivot=[1,1],units='model-unit',scaleNote='Model units are not metres or catalogue cells. Barrel count and catalogue X offsets retained; visual muzzle lengths are authored independently of gameplay ShootPosition Y=1.55. No gameplay integration.',up='+Z',forward='+Y',instances=nodes,animations=[dict(id='yaw-demo',node='yaw',axis=[0,0,1],rangeDegrees=[0,360],durationSeconds=360/speed,loop=True,interpolation='LINEAR',gameplaySource=f'catalog RotateSpeedDegreesPerSecond={speed}',restDegrees=0)],catalogSnapshot=rows[cid])
        write(ROOT/'Blocks'/bid/'assembly.json',data)
        write(ROOT/'Blocks'/bid/'README.md',f'# {bid} — {title}\n\nФинальный корпоративный вариант: белые гранёные бронепанели, небольшие фаски, голубые полосы эмиссии. '+('Длинный узкий двухканальный узел с продольными рельсами и отдельными кассетами подачи.' if count==2 else 'Низкий широкий корпус с разнесёнными бронекрыльями и одним крупным коротким дульным отверстием.')+f'\n\nКаталог {cid}: 2×2 клетки, Стволов: {count}, 360° наведение, {speed}°/с. '+('Имя minigun не означает шесть выдуманных стволов: каталог содержит ровно два независимых канала.' if count==2 else 'Восемь дробин за выстрел из одного ствола, а не восемь стволов.')+'\n\nСостав: неизменные CHT-P01/P02 1.1.0 и четыре новые самостоятельные детали '+bid+'-HULL, -BARREL, -SIDE, -SIGHT 1.0.0. Их part.json содержат геометрию, материалы, эмиссию, logical sockets и функциональные дульные точки. assembly.json хранит экземпляры и вращение вокруг Z. Новый head-in явно совместим с интерфейсом CHT-P03.base без правки общей детали.\n\nУсловные model-unit не считаются метрами/клетками. Визуальная длина стволов отличается от ShootPosition каталога; значения gameplay хранятся в полном catalogSnapshot без изменения баланса. Источники редактируемы; производные экспорты размещает общий просмотрщик в Exports/. Нет игровых коллайдеров, LOD или установки в игру. Промежуточные варианты, HTML и отдельный просмотрщик не создавались.\n')
    validate()

def validate():
    report=[]
    for bid,expected in [('CHT-W03',2),('CHT-W04',1)]:
        ap=ROOT/'Blocks'/bid/'assembly.json'; a=json.loads(ap.read_text(encoding='utf-8')); nodes={n['id']:n for n in a['instances']}; defs={}
        muzzles=[]
        for n in a['instances']:
            p=(ap.parent/n['source']).resolve(); assert p.exists(),p
            d=json.loads(p.read_text(encoding='utf-8'));defs[n['id']]=d
            assert d['id']==n['partId'] and d['version']==n['partVersion']
            assert (p.parent/d['materialLibrary']).resolve().exists()
            assert len({g['id'] for g in d['geometry']})==len(d['geometry'])
            assert all(g['shape'] in ['loft','roundedBox','cylinder','torus'] for g in d['geometry'])
            if n['attachment']:
                pd=defs[n['parent']]; at=n['attachment']; ps=next(s for s in pd['attachments'] if s['id']==at['parentSocket']);cs=next(s for s in d['attachments'] if s['id']==at['childSocket'])
                assert all(abs(ps['position'][i]-cs['position'][i]-n['translation'][i])<1e-7 for i in range(3)),n['id']
                assert all(abs(ps['normal'][i]+cs['normal'][i])<1e-7 for i in range(3))
                assert ps['up']==cs['up']
            for fp in d['functionalPoints']:
                if fp['role']=='projectile-muzzle':muzzles.append(n['id'])
        assert len(muzzles)==expected
        row=a['catalogSnapshot'];assert row['Стволы_XML'].count('<Barrel Name=')==expected
        report.append(dict(block=bid,instances=len(nodes),distinctParts=len(set(n['partId'] for n in nodes.values())),functionalMuzzles=muzzles,refs=True,sockets=True,catalogueBarrels=expected,animationDuration=a['animations'][0]['durationSeconds']))
    write(ROOT/'Blocks/CHT-W03/source-validation.json',report[0]);write(ROOT/'Blocks/CHT-W04/source-validation.json',report[1])
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':make()
