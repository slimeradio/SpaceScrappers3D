import json,csv,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 s=json.dumps(x,ensure_ascii=False,indent=2) if not isinstance(x,str) else x
 p.write_bytes((s.rstrip()+'\n').replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
def box(i,p,s,m='armor',r=.012):return dict(id=i,shape='roundedBox',position=p,size=s,radius=r,material=m)
def loft(i,p,w,l,h,m='armor',cut=.12,top=.85):
 a,b=w/2,l/2;c=min(cut,a*.7,b*.7)
 return dict(id=i,shape='loft',position=p,outline=[[-a+c,-b],[a-c,-b],[a,-b+c],[a,b-c],[a-c,b],[-a+c,b],[-a,b-c],[-a,-b+c]],levels=[dict(z=-h/2,scale=[.94,.94]),dict(z=-h/2+.018,scale=[1,1]),dict(z=h/2-.018,scale=[1,1]),dict(z=h/2,scale=[top,top])],material=m)
def socket(i,p,n,compat):return dict(id=i,role=i,position=p,normal=n,up=[0,1,0] if n[2] else [0,0,1],compatible=compat,parentNode='root')
def part(pid,title,g,att,fp=[]):
 mins=[1e9]*3;maxs=[-1e9]*3
 for a in g:
  if a['shape']=='roundedBox':lo=[-x/2 for x in a['size']];hi=[x/2 for x in a['size']]
  else:
   pts=[[p[0]*k['scale'][0],p[1]*k['scale'][1],k['z']] for k in a['levels'] for p in a['outline']];lo=[min(p[j] for p in pts) for j in range(3)];hi=[max(p[j] for p in pts) for j in range(3)]
  for j in range(3):mins[j]=min(mins[j],lo[j]+a['position'][j]);maxs[j]=max(maxs[j],hi[j]+a['position'][j])
 d=dict(schema='cht-authoring-part/1',id=pid,version='1.0.0',project='SS',style='CorporateHiTech',title=title,source='part.json',units='model-unit',handedness='right',up='+Z',forward='+Y',origin=[0,0,0],pivot=[0,0,0],restPose=dict(translation=[0,0,0],rotationEulerXYZ=[0,0,0],scale=[1,1,1]),scaling=dict(uniformOnly=True,allowedRange=[1,1]),geometry=g,materialLibrary='../../Materials/materials.json',materialSlots=sorted(set(x['material'] for x in g)),texturing=dict(method='uniform procedural PBR; model-unit box projection',rasterTextures=[],uvRequired=False),emission=[dict(id=x['id'],geometry=x['id'],material='cyan',color='#25bfff',intensity=2.5,intensityUnit='Three.js multiplier',defaultEnabled=True) for x in g if x['material']=='cyan'],attachments=att,attachmentAreas=[],functionalPoints=fp,animations=[],bounds=dict(min=mins,max=maxs,size=[maxs[j]-mins[j] for j in range(3)]))
 write(ROOT/'Parts'/pid/'part.json',d)
 write(ROOT/'Parts'/pid/'README.md',f'# {pid} — {title}\n\nРедактируемый источник: part.json, версия 1.0.0. +Z вверх, +Y вперёд; условные единицы. Положительный единичный масштаб. Материалы общей библиотеки: '+', '.join(d['materialSlots'])+'. Процедурное гладкое PBR-покрытие, проекция по коробке; файловых текстур нет. Голубая эмиссия обозначена отдельными геометрическими поверхностями. Крепления и функциональные ориентиры сохранены в JSON. Собственных анимаций нет.\n')
 return d
def inst(i,p,parent,t,ps=None,cs='base'):
 return dict(id=i,partId=p,partVersion='1.0.0',source=f'../../Parts/{p}/part.json',parent=parent,translation=t,rotationEulerXYZ=[0,0,0],scale=[1,1,1],attachment=dict(parentSocket=ps,childSocket=cs) if ps else None)
rows={r['ID']:r for r in csv.DictReader((ROOT.parent/'Catalog'/'blocks.csv').open(encoding='utf-8-sig',newline=''))}
for num,cat in [(1,'fleet-artillery-cruiser'),(2,'sniper-turret')]:
 bid=f'CHT-W{num:02d}';prefix=bid+'-';isart=num==1
 write(ROOT/'Blocks'/bid/'composition-plan.md',f'# План состава {bid}\n\nКаталог: {cat}; '+('3×4 клетки, два ствола, 360°, 45°/с.' if isart else '1×2 клетки, один ствол, 90°, 45°/с.')+' Клетки не трактуются как метры.\n\nПроверены CHT-P01–P07 версии 1.1.0: их размеры, короткие лазерные кожухи, ширина корпуса и крепления не подходят выбранному силуэту. Новые BASE (палубная платформа), HEAD (поворотный бронекорпус), BARREL (артиллерийский ствол / двухрельсовый ускоритель), PACK (казённый модуль / конденсатор) — отдельные детали 1.0.0. Материалы существующей библиотеки используются повторно. Деталь BARREL '+('повторяется дважды' if isart else 'содержит две рельсы одного ствола')+'. Сначала создаются детали, затем сборка. Общие детали не меняются.\n')
 # Base has low layered angular deck and inset octagonal rotary platform.
 w,l=(1.95,1.65) if isart else (.82,1.16)
 g=[loft('deck-gasket',[0,0,.035],w,l,.07,'rubber'),loft('white-plinth',[0,0,.115],w*.98,l*.98,.14,cut=.19),loft('rotor-dark',[0,0,.223],w*.70,l*.70,.08,'graphite',cut=.21),loft('rotor-cap',[0,0,.275],w*.65,l*.65,.045,'edge',cut=.20)]
 for s in [-1,1]:
  g.extend([box(f'deck-inlay-{s}',[s*w*.32,0,.19],[.025,l*.5,.009],'cyan',.002),loft(f'deck-outrigger-{s}',[s*w*.39,-l*.31,.17],w*.17,l*.25,.09,cut=.06)])
 base=part(prefix+'BASE','Широкая артиллерийская палубная платформа' if isart else 'Узкая восьмигранная палубная опора',g,[socket('deck',[0,0,0],[0,0,-1],'deck'),socket('bearing',[0,0,.3],[0,0,1],prefix+'HEAD.base')])
 # Revolving body, broad cruiser housing or slender arrowhead.
 if isart:
  g=[loft('lower-keel',[0,-.23,.12],1.65,1.50,.24,'graphite',.22),loft('main-glacis',[0,-.23,.28],1.68,1.43,.37,cut=.27,top=.78),loft('aft-turret-roof',[0,-.56,.50],1.33,.65,.16,cut=.18,top=.83),loft('central-nose',[0,.34,.24],.30,.40,.22,cut=.08),box('nose-glass',[0,.54,.30],[.15,.012,.08],'glass')]
  for s in [-1,1]:
   g.extend([loft(f'cheek-{s}',[s*.76,-.19,.30],.25,1.02,.37,cut=.09),loft(f'cheek-top-{s}',[s*.71,-.25,.49],.20,.72,.065,cut=.07),box(f'cheek-light-{s}',[s*.77,-.12,.530],[.025,.45,.012],'cyan',.002),loft(f'recoil-shoulder-{s}',[s*.254,.29,.37],.37,.47,.33,'graphite',.10),loft(f'recoil-armor-{s}',[s*.254,.26,.51],.38,.40,.08,cut=.07)])
  for k in range(6):g.append(box(f'rear-grille-{k}',[0,-.934,.22+k*.039],[.80,.018,.018],'graphite',.002))
  barrelpos=[[-.254,.44,.38],[.254,.44,.38]];packpos=[0,-.74,.57]
 else:
  g=[loft('slender-keel',[0,-.23,.11],.54,1.25,.22,'graphite',.12),loft('tapered-hull',[0,-.25,.27],.66,1.23,.30,cut=.19,top=.72),loft('rear-spine',[0,-.55,.44],.18,.52,.13,cut=.05),box('spine-inlay',[0,-.55,.511],[.025,.36,.009],'cyan',.002),loft('nose-collar',[0,.28,.27],.39,.29,.31,'graphite',.08)]
  for s in [-1,1]:
   g.extend([loft(f'side-swept-{s}',[s*.31,-.38,.27],.14,.69,.23,cut=.06),box(f'shoulder-light-{s}',[s*.30,-.31,.39],[.018,.36,.012],'cyan',.002)])
  barrelpos=[[0,.38,.31]];packpos=[0,-.60,.50]
 att=[socket('base',[0,0,0],[0,0,-1],prefix+'BASE.bearing'),socket('pack',packpos,[0,0,1],prefix+'PACK.base')]
 for j,p in enumerate(barrelpos):att.append(socket(f'barrel-{j}',p,[0,1,0],prefix+'BARREL.base'))
 head=part(prefix+'HEAD','Двухорудийный бронекорпус крейсера' if isart else 'Стреловидный корпус рельсовой турели',g,att)
 # Guns in local Y, asymmetry in secondary shapes but symmetric functional barrel.
 if isart:
  g=[loft('breech-lower',[0,.18,0],.26,.52,.23,'graphite',.07),loft('breech-upper',[0,.19,.14],.27,.47,.08,cut=.05),box('steel-barrel',[0,.86,0],[.118,1.36,.118],'edge',.012),loft('sleeve-a',[0,.49,0],.21,.44,.19,cut=.05),loft('sleeve-b',[0,.88,0],.175,.29,.16,cut=.045),loft('muzzle-brake',[0,1.48,0],.24,.32,.22,'graphite',.06),box('muzzle-inset',[0,1.644,0],[.125,.012,.13],'rubber',.006)]
  for s in [-1,1]:
   g.extend([box(f'brake-jaw-{s}',[s*.09,1.51,.045],[.075,.27,.17],'armor'),box(f'brake-light-{s}',[s*.094,1.58,.136],[.028,.11,.008],'cyan',.002),box(f'barrel-charge-{s}',[s*.108,.40,.025],[.008,.30,.025],'cyan',.002)])
  for y in [.69,1.10]:g.append(loft(f'reinforcing-collar-{y}',[0,y,0],.16,.08,.155,'graphite',.03))
  muzzle=[0,1.654,0]
 else:
  g=[loft('accelerator-breech',[0,.15,0],.34,.49,.27,'graphite',.08),loft('breech-top',[0,.13,.146],.29,.39,.05,cut=.06),box('central-vacuum-channel',[0,.83,-.06],[.075,1.27,.07],'rubber',.005)]
  for s in [-1,1]:
   g.extend([box(f'rail-metal-{s}',[s*.108,.93,0],[.075,1.52,.13],'edge'),loft(f'rail-armor-{s}',[s*.145,.77,.07],.12,1.12,.10,cut=.04),box(f'rail-blue-{s}',[s*.066,.96,.045],[.013,1.30,.018],'cyan',.002),loft(f'muzzle-prong-{s}',[s*.11,1.68,.015],.145,.24,.20,cut=.05),box(f'muzzle-tip-{s}',[s*.11,1.805,.015],[.10,.012,.11],'graphite')])
   for j,y in enumerate([.36,.65,.94,1.23]):g.append(box(f'coil-{s}-{j}',[s*.154,y,-.035],[.065,.075,.18],'graphite',.004))
  g.extend([box('rear-bridge',[0,.28,.10],[.30,.10,.065],'armor'),box('forward-bridge',[0,1.36,-.082],[.30,.10,.04],'armor')]);muzzle=[0,1.82,0]
 fp=[dict(id='muzzle',role='projectile-origin',parentNode='root',coordinateSystem='local',position=muzzle,direction=[0,1,0],up=[0,0,1])]
 barrel=part(prefix+'BARREL','Длинный артиллерийский ствол с дульным тормозом' if isart else 'Один ускоритель с двумя разделёнными рельсами',g,[socket('base',[0,0,0],[0,-1,0],prefix+'HEAD.barrel-*')],fp)
 # Removable recharge / electronics cassette with stepped body, cooling vanes and optic.
 pw,pl=(.65,.38) if isart else (.37,.47)
 g=[loft('cassette-core',[0,0,.06],pw,pl,.12,'graphite',.07),loft('cassette-cap',[0,-.02,.145],pw*.94,pl*.90,.09,cut=.06),box('optic-mount',[0,pl*.45,.10],[pw*.48,.07,.13],'rubber'),box('optic-window',[0,pl*.49,.10],[pw*.38,.012,.065],'glass')]
 for j in range(5):g.append(box(f'cooling-louver-{j}',[0,-pl*.38+j*pl*.14,.212],[pw*.72,.024,.018],'edge',.003))
 for s in [-1,1]:g.append(box(f'charge-status-{s}',[s*pw*.38,0,.197],[.018,pl*.50,.008],'cyan',.002))
 pack=part(prefix+'PACK','Кассета управления огнём' if isart else 'Высоковольтная кассета ускорителя',g,[socket('base',[0,0,0],[0,0,-1],prefix+'HEAD.pack')])
 # Parts completed before assembly.
 instances=[inst('foundation',base['id'],None,[0,0,0]),inst('yaw',head['id'],'foundation',[0,0,.3],'bearing'),inst('power-pack',pack['id'],'yaw',packpos,'pack')]
 for j,p in enumerate(barrelpos):instances.append(inst(f'barrel-{j}',barrel['id'],'yaw',p,f'barrel-{j}'))
 instances[1]['joint']=dict(type='revolute',axis=[0,0,1],rangeDegrees=[0,360] if isart else [-45,45],continuous=isart,restDegrees=0)
 row=rows[cat]
 a=dict(schema='cht-authoring-assembly/1',id=bid,version='1.0.0',title='Citadel — крейсерская артиллерия' if isart else 'Needle — снайперская рельсовая турель',catalogId=cat,catalogReference='../../../Catalog/blocks.csv',catalogGrid=[3,4] if isart else [1,2],catalogRotationPivot=[1.5,2] if isart else [.5,1],units='model-unit',up='+Z',forward='+Y',scaleNote='Stylized model units, not metres or grid cells. Barrel count and lateral offsets preserve catalogue; visual long barrels extend forward beyond catalogue ShootPosition. Runtime mapping required.',instances=instances,animations=[dict(id='yaw-demo',node='yaw',axis=[0,0,1],rangeDegrees=[0,360] if isart else [-45,45],durationSeconds=8 if isart else 2,loop=isart,interpolation='LINEAR',restDegrees=0,gameplaySource='catalog RotateSpeedDegreesPerSecond=45')],catalogSnapshot=row)
 write(ROOT/'Blocks'/bid/'assembly.json',a)
 write(ROOT/'Blocks'/bid/'README.md',f'# {bid} — '+a['title']+'\n\nФинальная параметрическая сборка assembly.json. Каталог '+cat+'; '+('два независимых артиллерийских ствола, сетка 3×4, полный круг 360°, 45°/с (8 секунд).' if isart else 'один ствол из двух рельсовых направляющих, сетка 1×2, сектор −45…45°, 45°/с (2 секунды).')+'\n\nЧетыре новые переиспользуемые детали 1.0.0: '+', '.join(prefix+x for x in ['BASE','HEAD','BARREL','PACK'])+'. Белая многослойная броня, графитовые зазоры, голубые эмиссивные каналы, металлические направляющие. Все детали имеют материалы, ограничение масштаба, сокеты; дульная точка хранится в BARREL. Сборка и сокеты совпадают в исходной позе; дочерние элементы следуют за yaw. Самостоятельных анимаций деталей нет.\n\nПравая система координат, +Z вверх, +Y вперёд. Model units — условные авторские единицы, не метры; игровые клетки не задают размер меша. Стволы намеренно визуально удлинены; X артиллерии ±0.254 сохранены, визуальная координата дул по Y отличается от каталога. Игровую интеграцию и mapping координат нужно выполнить отдельно. LOD и игровые коллайдеры в задачу не включены. Промежуточных кандидатов, отдельного просмотрщика и preview-файлов не создавалось; экспорт выполняется общим инструментом.\n')
 # Validate resolved refs, exact socket alignment in rest pose, versions and emission.
 defs={p['id']:p for p in [base,head,barrel,pack]}
 for i in instances:
  d=defs[i['partId']];assert (ROOT/'Blocks'/bid/i['source']).resolve().is_file();assert d['version']==i['partVersion']
  if i['attachment']:
   par=next(x for x in instances if x['id']==i['parent']);pd=defs[par['partId']]
   ps=next(s for s in pd['attachments'] if s['id']==i['attachment']['parentSocket']);cs=next(s for s in d['attachments'] if s['id']==i['attachment']['childSocket'])
   assert all(abs(ps['position'][k]-i['translation'][k]-cs['position'][k])<1e-8 for k in range(3));assert sum(ps['normal'][k]*cs['normal'][k] for k in range(3))==-1;assert ps['up']==cs['up']
 print(bid, len(instances),'instances',sum(len(p['geometry']) for p in defs.values()),'unique geometry shapes; refs, versions and sockets PASS')
