from pathlib import Path
import json,csv

ROOT=Path(__file__).resolve().parents[1]
current=ROOT/'Blocks/CHT-T01/assembly.json'
if current.exists() and json.loads(current.read_text(encoding='utf-8')).get('version')!='1.0.0':
    raise SystemExit('This is the initial 1.0.0 seed generator. For the current revision use rework_v11.py; refusing to overwrite newer assets.')
def write(p,s):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
def js(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
write('README.md','''# SS / CorporateHiTech

Корпоративный Hi-Tech: гладкая белая броня, мягкие скругления, узкие тёмные стыки, голубая подсветка. Чистые обслуживаемые поверхности без повреждений и грубой внешней механики.

Тестовый блок: [CHT-T01](Blocks/CHT-T01/README.md). Изолированная библиотека деталей — Parts/. Чужие стили не использованы.

Техническое соглашение этого прототипа: правая система координат, +Z вверх, +Y вперёд, +X вправо; условные model units, не метры. Геометрия хранится параметрически в part.json и строится Three.js 0.170.0. Геометрия и материалы редактируются независимо от производного glTF. JSON — локальная авторская схема прототипа, не формат игры. Исходный pivot блока — центр основания на нижней плоскости. Экземпляры имеют положительный единичный масштаб. Текстуры процедурные: гладкое покрытие и отдельные геометрические полосы эмиссии, без растровых карт и UV-зависимого рисунка.

Просмотр: запустить Tools/serve.ps1, открыть http://127.0.0.1:8768/Blocks/CHT-T01/viewer.html. Нужен браузер с WebGL2. Все зависимости локальны. Модель доступна и как отдельный glTF в Exports/.
''')
materials={
 'armor':dict(color='#e8eff2',metalness=.28,roughness=.24),
 'edge':dict(color='#a7bac3',metalness=.78,roughness=.27),
 'graphite':dict(color='#172b36',metalness=.65,roughness=.3),
 'rubber':dict(color='#07121b',metalness=.12,roughness=.54),
 'cyan':dict(color='#54dcff',metalness=.16,roughness=.18,emissive='#25bfff',emissiveIntensity=2.5),
 'glass':dict(color='#125478',metalness=.6,roughness=.12,emissive='#1686bf',emissiveIntensity=.65)
}
js('Materials/materials.json',materials)
def box(n,p,s,m,r=.035):return dict(id=n,shape='roundedBox',position=p,size=s,radius=r,material=m)
def cyl(n,p,r,d,m,axis='Z',r2=None):return dict(id=n,shape='cylinder',position=p,radius=r,radiusTop=r if r2 is None else r2,depth=d,axis=axis,material=m)
def ring(n,p,r,t,m,axis='Z'):return dict(id=n,shape='torus',position=p,radius=r,tube=t,axis=axis,material=m)
def attachment(i,role,pos,normal,up,compat):return dict(id=i,role=role,position=pos,normal=normal,up=up,compatible=compat)
parts={}
def part(i,title,geom,attach,points=None):
    parts[i]=dict(schema='cht-authoring-part/1',id=i,version='1.0.0',project='SS',style='CorporateHiTech',title=title,source='part.json',units='model-unit',handedness='right',up='+Z',forward='+Y',origin=[0,0,0],pivot=[0,0,0],restPose=dict(translation=[0,0,0],rotationEulerXYZ=[0,0,0],scale=[1,1,1]),scaling=dict(uniformOnly=True,allowedRange=[1,1]),geometry=geom,materialLibrary='../../Materials/materials.json',materialSlots=sorted(set(g['material'] for g in geom)),texturing=dict(method='uniform procedural PBR',rasterTextures=[],uvRequired=False),emission=[dict(id=g['id'],material=g['material'],defaultEnabled=True,intensityUnit='Three.js multiplier') for g in geom if g['material'] in ['cyan','glass']],attachments=attach,attachmentAreas=[],functionalPoints=points or [],animations=[])

part('CHT-P01','Опорная платформа',[
 cyl('foot',[0,0,.075],.67,.15,'graphite'),cyl('ceramic-plinth',[0,0,.16],.64,.13,'armor',r2=.59),
 ring('seam',[0,0,.215],.568,.012,'rubber'),ring('status-halo',[0,0,.211],.605,.009,'cyan'),
 *[box('anchor-'+str(j),[x,y,.07],[.20,.21,.12],'armor',.025) for j,(x,y) in enumerate([(-.46,-.46),(.46,-.46),(-.46,.46),(.46,.46)])]
 ],[attachment('deck','deck-in',[0,0,0],[0,0,-1],[0,1,0],'deck'),attachment('bearing','bearing-out',[0,0,.23],[0,0,1],[0,1,0],'CHT-P02.base')])
part('CHT-P02','Поворотный подшипник',[
 cyl('hub',[0,0,.062],.43,.124,'graphite'),cyl('upper-race',[0,0,.115],.46,.052,'edge'),ring('light-ring',[0,0,.1],.433,.01,'cyan'),
 *[box('race-index-'+str(j),[x,y,.13],[.04,.05,.012],'rubber',.004) for j,(x,y) in enumerate([(-.32,-.22),(.32,-.22),(-.32,.22),(.32,.22)])]
 ],[attachment('base','bearing-in',[0,0,0],[0,0,-1],[0,1,0],'CHT-P01.bearing'),attachment('head','head-out',[0,0,.14],[0,0,1],[0,1,0],'CHT-P03.base')])
part('CHT-P03','Гладкий бронекорпус',[
 box('shadow-chassis',[0,-.22,.135],[1.12,.91,.27],'graphite',.085),
 box('main-shell',[0,-.25,.23],[1.08,.85,.34],'armor',.105),
 box('crown',[0,-.28,.413],[.63,.65,.075],'armor',.032),
 box('crown-inlay',[0,-.30,.454],[.026,.44,.008],'cyan',.003),
 box('front-mask',[0,.164,.22],[.85,.05,.22],'rubber',.018),
 *[box('rear-vent-'+str(j),[-.21+j*.084,-.679,.25],[.045,.012,.12],'graphite',.007) for j in range(6)]
 ],[attachment('base','head-in',[0,0,0],[0,0,-1],[0,1,0],'CHT-P02.head'),
 *[attachment('emitter-'+s,'emitter-out',[x,.08,.23],[0,1,0],[0,0,1],'CHT-P05.base') for s,x in [('L',-.254),('R',.254)]],
 *[attachment('cheek-'+s,'cheek-out',[x,-.24,.22],[0,0,1],[0,1,0],'CHT-P04.base') for s,x in [('L',-.565),('R',.565)]],
 attachment('sensor','sensor-out',[0,.08,.39],[0,0,1],[0,1,0],'CHT-P06.base'),attachment('service','service-out',[0,-.58,.42],[0,0,1],[0,1,0],'CHT-P07.base')])
part('CHT-P04','Боковая бронекапсула',[
 box('gasket',[0,0,0],[.16,.71,.25],'rubber',.045),box('cheek',[0,0,.035],[.18,.69,.27],'armor',.065),
 box('light-spine',[0,-.015,.177],[.025,.43,.01],'cyan',.004),box('front-tip',[0,.323,.018],[.11,.025,.13],'edge',.012)
 ],[attachment('base','cheek-in',[0,0,0],[0,0,-1],[0,1,0],'CHT-P03.cheek-*')])
part('CHT-P05','Лазерный эмиттер',[
 cyl('core',[0,.195,0],.105,.47,'graphite','Y'),
 box('ceramic-shroud',[0,.13,.065],[.285,.46,.21],'armor',.055),
 box('rail-seat',[0,.145,.177],[.077,.33,.018],'graphite',.008),box('rail-light',[0,.145,.188],[.026,.29,.009],'cyan',.003),
 cyl('muzzle-sleeve',[0,.39,0],.122,.16,'edge','Y'),cyl('dark-recess',[0,.474,0],.098,.012,'rubber','Y'),
 ring('lens-frame',[0,.479,0],.078,.011,'graphite','Y'),cyl('optical-lens',[0,.482,0],.065,.008,'glass','Y'),
 ring('aperture-glow',[0,.489,0],.058,.007,'cyan','Y'),cyl('iris',[0,.49,0],.026,.003,'cyan','Y')
 ],[attachment('base','emitter-in',[0,0,0],[0,-1,0],[0,0,1],'CHT-P03.emitter-*')],
 [dict(id='muzzle',role='beam-origin',position=[0,.49,0],direction=[0,1,0],up=[0,0,1],parent='part-root',space='part-local')])
part('CHT-P06','Оптический визир',[
 box('sensor-pedestal',[0,0,.012],[.16,.15,.024],'graphite',.01),box('sensor-shell',[0,.015,.072],[.17,.22,.12],'armor',.032),
 box('visor',[0,.129,.072],[.125,.012,.055],'graphite',.012),box('visor-glow',[0,.137,.072],[.09,.005,.022],'cyan',.006)
 ],[attachment('base','sensor-in',[0,0,0],[0,0,-1],[0,1,0],'CHT-P03.sensor')])
part('CHT-P07','Сервисная крышка',[
 box('seam',[0,0,0],[.39,.135,.018],'graphite',.018),box('lid',[0,0,.012],[.36,.11,.018],'armor',.014),
 *[cyl('fastener-'+str(j),[x,0,.024],.012,.006,'edge') for j,x in enumerate([-.145,.145])],box('status',[0,0,.024],[.09,.012,.005],'cyan',.002)
 ],[attachment('base','service-in',[0,0,0],[0,0,-1],[0,1,0],'CHT-P03.service')])

plan='# План состава CHT-T01\n\nБиблиотека нового стиля отсутствовала. Все детали новые, версия 1.0.0; геометрия других стилей не использована.\n\n| Деталь | Решение | Совместимость и причина |\n|---|---|---|\n'
for i,p in parts.items():plan+=f'| {i} — {p["title"]} | Создать новую | Собственные крепления CHT, гладкое белое покрытие; готовых деталей в стиле нет |\n'
write('Blocks/CHT-T01/composition-plan.md',plan)
for i,p in parts.items():
    lo=[float('inf')]*3;hi=[-float('inf')]*3
    for g in p['geometry']:
        if g['shape']=='roundedBox': ext=[x/2 for x in g['size']]
        elif g['shape']=='cylinder':
            r=max(g['radius'],g['radiusTop']);ext=[r,g['depth']/2,r] if g['axis']=='Y' else [r,r,g['depth']/2]
        else:
            r=g['radius']+g['tube'];ext=[r,g['tube'],r] if g['axis']=='Y' else [r,r,g['tube']]
        lo=[min(a,c-e) for a,c,e in zip(lo,g['position'],ext)]
        hi=[max(a,c+e) for a,c,e in zip(hi,g['position'],ext)]
    p['bounds']={'min':lo,'max':hi,'size':[b-a for a,b in zip(lo,hi)]}
    js(f'Parts/{i}/part.json',p)
instances=[]
def inst(i,p,parent,t,attach=None):instances.append(dict(id=i,partId=p,partVersion='1.0.0',source=f'../../Parts/{p}/part.json',parent=parent,translation=t,rotationEulerXYZ=[0,0,0],scale=[1,1,1],attachment=attach))
inst('foundation','CHT-P01',None,[0,0,0])
inst('yaw','CHT-P02','foundation',[0,0,.23],dict(parentSocket='bearing',childSocket='base'))
instances[-1]['joint']=dict(type='revolute',axis=[0,0,1],rangeDegrees=[0,360],continuous=True,restDegrees=0)
inst('head','CHT-P03','yaw',[0,0,.14],dict(parentSocket='head',childSocket='base'))
for s,x in [('L',-.565),('R',.565)]:inst('cheek-'+s,'CHT-P04','head',[x,-.24,.22],dict(parentSocket='cheek-'+s,childSocket='base'))
for s,x in [('L',-.254),('R',.254)]:inst('emitter-'+s,'CHT-P05','head',[x,.08,.23],dict(parentSocket='emitter-'+s,childSocket='base'))
inst('sensor','CHT-P06','head',[0,.08,.39],dict(parentSocket='sensor',childSocket='base'))
inst('service','CHT-P07','head',[0,-.58,.42],dict(parentSocket='service',childSocket='base'))
with (ROOT.parent/'Catalog/blocks.csv').open(encoding='utf-8-sig',newline='') as f:catalog=next(r for r in csv.DictReader(f) if r['ID']=='fleet-laser-twin')
js('Blocks/CHT-T01/assembly.json',dict(schema='cht-authoring-assembly/1',id='CHT-T01',version='1.0.0',catalogId='fleet-laser-twin',catalogReference='../../../Catalog/blocks.csv',catalogGrid=[2,2],catalogRotationPivot=[1,1],units='model-unit',scaleNote='No established metres per cell. XY catalog offsets preserved in visual rest pose except muzzle forward offset +0.02 model-unit for lens cap.',up='+Z',forward='+Y',instances=instances,animations=[dict(id='yaw-demo',node='yaw',axis=[0,0,1],rangeDegrees=[0,360],durationSeconds=3,loop=True,interpolation='LINEAR',gameplaySource='catalog RotateSpeedDegreesPerSecond=120',restDegrees=0)],catalogSnapshot=catalog))
write('Blocks/CHT-T01/README.md','''# CHT-T01 / Aster Twin

Тестовая двухствольная лазерная турель, корпоративный Hi-Tech. Каталожный ID: fleet-laser-twin; сетка 2×2, круговое наведение 360°, скорость 120°/с, два эмиттера. Игровой баланс не менялся.

Открыть viewer.html через Tools/serve.ps1. Перетаскивание — орбита, колесо — масштаб. Доступны вид сверху, разборка, выбор отдельных деталей и вращение турели. Точная геометрия создаётся из Parts/*/part.json; сборка и стабильные ссылки — assembly.json. Изменить параметры детали и перезагрузить просмотр. Два эмиттера и две боковины — экземпляры общих деталей, не копии геометрии исходника.

Состав: 7 самостоятельных деталей, 9 экземпляров. P01 платформа; P02 подшипник; P03 корпус; P04 боковая капсула ×2; P05 эмиттер ×2; P06 визир; P07 сервисная крышка. Принятые материалы и процедурное текстурирование — Materials/materials.json. Голубая эмиссия выполнена геометрическими вставками; файловых текстур нет.

Поворот вокруг +Z на подшипнике; весь верх следует за yaw. Наклон и отдача не добавлены: каталог их не задаёт. Дульные точки находятся в локальных данных P05. Каталожные позиции стволов ±0.254 по X соблюдены; визуальная передняя линза вынесена на 0.02 model-unit относительно каталожного Y=1.55. Масштаб клетки в метрах неизвестен; соответствие реальному коллайдеру не подтверждено. Габариты меша не равны размеру сетки.

Редактируемый источник: part.json + assembly.json + Tools/model.js. Производный экспорт: Exports/CHT-T01.gltf (PBR, эмиссия, иерархия и анимация yaw). Предпросмотры в Previews/, отдельные детали в Parts/*/Previews/. Статический glTF и авторские метаданные не являются игровым интеграционным форматом. LOD и игровые коллайдеры не создавались; в игре не проверено.
''')
write('Tools/serve.ps1',"& 'C:\\Users\\nebul\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' (Join-Path $PSScriptRoot 'serve.py')\n")
print('Created',len(parts),'parts;',len(instances),'instances')
