import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);s=d if isinstance(d,str) else json.dumps(d,ensure_ascii=False,indent=2);p.write_bytes((s.rstrip()+'\n').replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def original(p):
 old=p.parent/'Versions'/'1.0.0.json'
 if not old.exists():save(old,read(p))
 return read(old)
def lathe(i,profile,pos,mat,axis='Y',segments=48):return dict(id=i,shape='lathe',profile=profile,segments=segments,axis=axis,position=pos,material=mat)
def box(i,pos,size,mat='armor',rad=.006):return dict(id=i,shape='roundedBox',position=pos,size=size,material=mat,radius=rad)
def wedge(i,outline,pos,h,mat='armor',top=.8):return dict(id=i,shape='loft',outline=outline,position=pos,levels=[dict(z=-h/2,scale=[.92,.92]),dict(z=-h/2+.015,scale=[1,1]),dict(z=h/2-.035,scale=[top,top]),dict(z=h/2,scale=[top*.96,top*.96])],material=mat)
def measure(g):
 if g['shape']=='roundedBox':lo=[-v/2 for v in g['size']];hi=[v/2 for v in g['size']]
 elif g['shape']=='loft':
  pts=[[x*l['scale'][0],y*l['scale'][1],l['z']] for x,y in g['outline'] for l in g['levels']];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
 elif g['shape']=='lathe':
  radius=max(p[0] for p in g['profile']);axis={'X':0,'Y':1,'Z':2}[g.get('axis','Y')];lo=[-radius]*3;hi=[radius]*3;lo[axis]=min(p[1] for p in g['profile']);hi[axis]=max(p[1] for p in g['profile'])
 elif g['shape']=='profile':
  bevel=g.get('bevel',0);lo=[min(p[0] for p in g['outline'])-bevel,min(p[1] for p in g['outline'])-bevel,-g['depth']/2-bevel];hi=[max(p[0] for p in g['outline'])+bevel,max(p[1] for p in g['outline'])+bevel,g['depth']/2+bevel]
 else:raise ValueError(g['shape'])
 return [[lo[k]+g['position'][k] for k in range(3)],[hi[k]+g['position'][k] for k in range(3)]]
def update(pid,g,note):
 path=R/'Parts'/pid/'part.json';p=original(path);p['version']='1.1.0';p['geometry']=g;p['materialSlots']=sorted({v['material'] for v in g});p['emission']=[dict(id=v['id'],geometry=v['id'],material='cyan',color='#25bfff',intensity=2.5,intensityUnit='Three.js multiplier',defaultEnabled=True) for v in g if v['material']=='cyan'];bs=[measure(v) for v in g];lo=[min(b[0][k] for b in bs) for k in range(3)];hi=[max(b[1][k] for b in bs) for k in range(3)];p['bounds']=dict(min=lo,max=hi,size=[hi[k]-lo[k] for k in range(3)]);p['revisionNotes']=note;save(path,p)
 save(path.parent/'README.md',f'# {pid} — {p["title"]}\n\nВерсия 1.1.0. '+note+'\n\nРедактируемый источник part.json; прежний источник Versions/1.0.0.json. Материалы прежней общей библиотеки, процедурное PBR и голубая эмиссия, отдельные растровые текстуры не используются. Правая система координат, +Z вверх, +Y вперёд, model units; масштаб 1. Сокеты, локальные оси, функциональные точки сохранены. Самостоятельных анимаций нет.\n')
 return p
# Artillery: replace boxlike barrel, collar and frontal hull with continuous revolved engineering forms.
p=original(R/'Parts/CHT-W01-BARREL/part.json')
g=[lathe('forged-breech',[[.047,0],[.116,0],[.137,.045],[.137,.26],[.116,.33],[.080,.40],[.047,.40],[.047,0]],[0,0,0],'graphite'),lathe('white-recoil-jacket',[[.138,.06],[.156,.10],[.156,.26],[.133,.34],[.118,.34],[.138,.25],[.138,.06]],[0,0,0],'armor'),lathe('tapered-steel-tube',[[.048,.32],[.077,.32],[.078,.40],[.066,.52],[.061,1.31],[.081,1.36],[.081,1.42],[.048,1.42],[.048,.32]],[0,0,0],'edge'),lathe('profiled-open-muzzle-brake',[[.049,1.31],[.084,1.31],[.113,1.37],[.113,1.42],[.085,1.45],[.085,1.51],[.125,1.55],[.125,1.61],[.106,1.654],[.049,1.654],[.049,1.31]],[0,0,0],'graphite'),lathe('muzzle-armored-rim',[[.107,1.59],[.129,1.59],[.129,1.625],[.109,1.65],[.107,1.65],[.107,1.59]],[0,0,0],'armor')]
for s in [-1,1]:g.append(box('breech-charge-'+str(s),[s*.157,.18,0],[.009,.12,.024],'cyan',.002))
update('CHT-W01-BARREL',g,'Прежние прямоугольные казённик и ствол заменены профилированными телами вращения: коническая переходная часть, длинная труба, ступенчатый дульный тормоз и открытый сквозной канал радиуса .047–.049. Дульная точка [0,1.654,0] сохранена; внутренних чёрных заглушек нет.')
p=original(R/'Parts/CHT-W01-HEAD/part.json');g=[v for v in p['geometry'] if not v['id'].startswith(('main-glacis','recoil-shoulder','recoil-armor','central-nose','nose-glass'))]
g.append(wedge('cast-tapered-glacis',[[-.73,-.84],[.73,-.84],[.83,-.55],[.76,.06],[.44,.46],[.14,.58],[-.14,.58],[-.44,.46],[-.76,.06],[-.83,-.55]],[0,0,.265],.35,top=.78))
for s in [-1,1]:
 g.append(lathe('cast-gun-mantlet-'+str(s),[[.12,-.05],[.185,-.05],[.195,.035],[.178,.13],[.145,.20],[.119,.20],[.12,-.05]],[s*.254,.31,.38],'armor'))
 g.append(lathe('trunnion-cap-'+str(s),[[0,0],[.13,0],[.15,.025],[.15,.055],[.12,.08],[0,.08],[0,0]],[s*.90-.04,-.01,.32],'graphite',axis='X'))
g.append(box('forward-optic',[0,.46,.34],[.12,.026,.065],'glass'))
update('CHT-W01-HEAD',g,'Перед башни заменён выраженным литым клином со сходящимися скулами. Прямоугольные передние воротники заменены коническими масками орудий, по бортам добавлены цапфы. Крепления и палубная компоновка сохранены.')
# Sniper: narrow arrowhead carrying body and planar open frames around actual rails.
p=original(R/'Parts/CHT-W02-HEAD/part.json');g=[v for v in p['geometry'] if not v['id'].startswith(('slender-keel','tapered-hull','side-swept','nose-collar'))]
outline=[[-.18,-.86],[.18,-.86],[.36,-.50],[.28,-.12],[.115,.42],[0,.52],[-.115,.42],[-.28,-.12],[-.36,-.50]]
g.extend([wedge('arrowhead-keel',outline,[0,0,.10],.20,'graphite',.88),wedge('swept-bearing-shell',outline,[0,0,.26],.24,'armor',.68),lathe('nose-accelerator-cradle',[[.08,-.12],[.16,-.12],[.19,-.06],[.17,.04],[.12,.09],[.08,.09],[.08,-.12]],[0,.31,.31],'graphite')])
update('CHT-W02-HEAD',g,'Несущий корпус заменён длинным стреловидным клином с острым носом и расширением под казёнником. Тупой прямоугольный воротник заменён конической опорой ускорителя.')
p=original(R/'Parts/CHT-W02-BARREL/part.json');g=[v for v in p['geometry'] if not v['id'].startswith(('rail-armor','coil-','muzzle-prong','breech-top'))]
for s in [-1,1]:
 # Upper open frame, mechanically tied at both ends to lower contact rails.
 out=[[-.055,.18],[.055,.18],[.065,.36],[.052,1.46],[.015,1.78],[-.043,1.78],[-.060,1.40]]
 holes=[[[-.027,.38],[.025,.38],[.020,.81],[-.025,.81]],[[-.024,.94],[.021,.94],[.012,1.38],[-.025,1.47]]]
 g.append(dict(id='open-tension-frame-'+str(s),shape='profile',outline=out,holes=holes,depth=.09,bevel=.004,position=[s*.166,0,.095],material='armor'))
 for j,y in enumerate([.34,.88,1.48]):g.append(lathe(f'coil-mount-{s}-{j}',[[0,-.045],[.055,-.045],[.064,-.02],[.064,.02],[.055,.045],[0,.045],[0,-.045]],[s*.14,y,0],'graphite',axis='Z',segments=16))
update('CHT-W02-BARREL',g,'Внешние прямоугольные кожухи и повторяющиеся коробки заменены двумя открытыми натяжными рамами с большими сквозными окнами; плоские контактные рельсы и центральный свободный канал сохранены. Опоры — гранёные катушки. Это один ускоритель с двумя направляющими, не два ствола. Дульная точка сохранена.')
p=original(R/'Parts/CHT-W02-PACK/part.json');g=[wedge('capacitor-saddle',[[-.20,-.23],[.20,-.23],[.22,-.16],[.17,.22],[-.17,.22],[-.22,-.16]],[0,0,.025],.05,'graphite',.95)]
for s in [-1,1]:
 g.extend([lathe('ceramic-capacitor-'+str(s),[[0,-.21],[.064,-.21],[.081,-.17],[.081,.14],[.063,.21],[0,.21],[0,-.21]],[s*.10,0,.115],'armor'),lathe('capacitor-terminal-'+str(s),[[0,.14],[.084,.14],[.084,.17],[.069,.22],[0,.22],[0,.14]],[s*.10,0,.115],'edge'),lathe('capacitor-state-'+str(s),[[.082,-.105],[.084,-.105],[.084,-.082],[.082,-.082],[.082,-.105]],[s*.10,0,.115],'cyan')])
g.append(box('central-power-bus',[0,0,.058],[.035,.33,.06],'graphite'))
update('CHT-W02-PACK',g,'Прямоугольная электронная кассета заменена парой керамических цилиндрических конденсаторов с коническими торцами в стреловидном седле. Голубая индикация — изолирующие кольца накопителей; крепление кассеты сохранено.')
for bid in ['CHT-W01','CHT-W02']:
 path=R/'Blocks'/bid/'assembly.json';a=original(path);a['version']='1.1.0'
 for i in a['instances']:
  d=read((path.parent/i['source']).resolve());i['partVersion']=d['version']
 save(path,a)
 readme=path.parent/'README.md';s=readme.read_text(encoding='utf-8');s=s.split('\n\n## Ревизия форм')[0];save(readme,s+'\n\n## Ревизия форм 1.1.0\n\n'+('Профилированные полые артиллерийские стволы, конические казённики и дульные тормоза заменили прямоугольные кожухи. Литой клиновидный перед башни и цапфы связывают новую геометрию с назначением.' if bid=='CHT-W01' else 'Главные новые формы: стреловидный несущий клин, открытые натяжные рамы рельсов с окнами и цилиндрические конденсаторы вместо коробчатой кассеты.')+' Общая компоновка, палитра, количество стволов, сокеты, дульные точки и наведение сохранены. Прежние редактируемые JSON находятся в Versions/1.0.0.json соответствующих папок. Источник ревизии Tools/revise_forms_w01_w02.py применяется поверх версии1.0.0; новых вариантов блоков и просмотрщиков нет.\n')
 plan=path.parent/'composition-plan.md';s=plan.read_text(encoding='utf-8').split('\n\n## Ревизия форм')[0];save(plan,s+'\n\n## Ревизия форм 1.1.0\n\n'+('HEAD и BARREL — новые параметрические формы версии1.1.0: литой клин, цапфы, конические маски и полый профилированный ствол. BASE и PACK повторно используются1.0.0.' if bid=='CHT-W01' else 'HEAD, BARREL и PACK заменены параметрическими формами версии1.1.0: клин, рамы с окнами, конденсаторы. BASE повторно используется1.0.0.')+' Крепления и масштаб совместимы, материалов извне нет.\n')
 print(bid,'revised assembly and parts saved; versions pinned')
