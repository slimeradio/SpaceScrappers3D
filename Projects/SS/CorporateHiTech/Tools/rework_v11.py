from pathlib import Path
import json,math
R=Path(__file__).resolve().parents[1]
def save(p,data):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True);s=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+'\n';p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
def box(i,p,s,m='armor',r=.006,rot=None):
    g=dict(id=i,shape='roundedBox',position=p,size=s,radius=r,material=m)
    if rot:g['rotationEulerXYZ']=rot
    return g
def cyl(i,p,r,d,m='graphite',seg=8,axis='Z',top=None):return dict(id=i,shape='cylinder',position=p,radius=r,radiusTop=r if top is None else top,depth=d,axis=axis,segments=seg,material=m)
def outline(w,d,c=.15):
    x,y=w/2,d/2;c=min(c,x*.8,y*.8)
    return [[-x+c,-y],[x-c,-y],[x,-y+c],[x,y-c],[x-c,y],[-x+c,y],[-x,y-c],[-x,-y+c]]
def loft(i,p,w,d,h,m='armor',cut=.10,top=.82):
    return dict(id=i,shape='loft',position=p,outline=outline(w,d,cut),levels=[dict(z=-h/2,scale=[.94,.94]),dict(z=-h*.24,scale=[1,1]),dict(z=h*.16,scale=[1,1]),dict(z=h/2,scale=[top,top])],material=m)
plan='''# План переработки CHT-T01 / 1.1.0

Запрос: намного больше форм, менее круглая турель. Сохранить корпоративную белую броню и голубую подсветку.

| Деталь | Решение | Изменение |
|---|---|---|
| CHT-P01 | Вариант 1.1.0 | Восьмигранное основание, раздельные трапециевидные опоры, крепёж, секторная подсветка |
| CHT-P02 | Вариант 1.1.0 | Гранёный верхний погон, технологические фиксаторы; тонкий круглый подшипник остаётся внутри |
| CHT-P03 | Вариант 1.1.0 | Составной корпус с наклонными гранями, раздельными панелями крыши и кормовыми блоками |
| CHT-P04 ×2 | Вариант 1.1.0 | Ломаная боковина, щели, наклонные жабры охлаждения и ступенчатая броня |
| CHT-P05 ×2 | Вариант 1.1.0 | Угловатый кожух, шестигранное дуло, прямоугольная оптика, боковые пластины |
| CHT-P06 | Вариант 1.1.0 | Клиновидный визир с отдельными окнами и верхним плавником |
| CHT-P07 | Вариант 1.1.0 | Скошенный сервисный люк с замками и раздельными индикаторами |

Крепления, pivots и единицы сохранены. Версии 1.0.0 сохранены в Parts/*/Versions/1.0.0.json; исходная сборка — Blocks/CHT-T01/Versions/1.0.0.json. Другие стили не использованы.
'''
save('Blocks/CHT-T01/composition-plan.md',plan)
G={}
G[1]=[
 loft('octagonal-plinth',[0,0,.095],1.34,1.34,.18,'graphite',.27,.94),
 loft('deck-armor',[0,0,.199],1.27,1.27,.05,'armor',.26,.92),
 cyl('center-bearing-seat',[0,0,.219],.46,.022,'edge',32),
]
for sx in [-1,1]:
 for sy in [-1,1]:
    tag=f'{sx}_{sy}';x,y=sx*.46,sy*.46
    G[1]+=[loft('anchor-'+tag,[x,y,.065],.34,.34,.13,'armor',.08,.75),cyl('anchor-bolt-'+tag,[x,y,.134],.025,.012,'graphite',6),box('anchor-notch-'+tag,[x,y+sy*.09,.134],[.075,.018,.007],'edge')]
for a in range(4):
    t=a*math.pi/2
    G[1]+=[box('status-sector-'+str(a),[.595*math.sin(t),.595*math.cos(t),.227],[.19,.012,.009],'cyan',.002,[0,0,-t]),box('deck-score-'+str(a),[.47*math.sin(t),.47*math.cos(t),.228],[.17,.012,.006],'rubber',.001,[0,0,-t])]
G[2]=[cyl('inner-bearing',[0,0,.055],.40,.11,'graphite',48),cyl('machined-race',[0,0,.102],.44,.046,'edge',32),loft('faceted-turntable',[0,0,.122],.92,.92,.036,'graphite',.24,.96)]
for a in range(8):
    t=a*math.pi/4;G[2]+=[box('race-lock-'+str(a),[.37*math.sin(t),.37*math.cos(t),.143],[.065,.07,.018],'edge',.002,[0,0,-t])]
G[3]=[
 loft('lower-keel',[0,-.22,.125],1.12,.94,.25,'graphite',.16,.88),
 loft('sloping-hull',[0,-.25,.247],1.1,.90,.305,'armor',.17,.77),
 loft('spine',[0,-.30,.414],.23,.60,.085,'armor',.06,.72),
 box('spine-light',[0,-.27,.460],[.022,.29,.006],'cyan',.002),
 loft('nose-keel',[0,.175,.16],.36,.28,.19,'graphite',.07,.7),
 loft('chin-armor',[0,.19,.155],.24,.24,.12,'armor',.05,.65),
 box('chin-slit',[0,.308,.158],[.12,.009,.018],'cyan',.002),
]
for s in [-1,1]:
    G[3]+=[loft('roof-plate-'+str(s),[s*.282,-.29,.400],.265,.61,.057,'armor',.06,.87),box('roof-seam-'+str(s),[s*.142,-.29,.424],[.014,.41,.008],'rubber',.002),
    loft('rear-power-'+str(s),[s*.38,-.65,.26],.24,.29,.23,'graphite',.05,.80),loft('rear-cowl-'+str(s),[s*.38,-.665,.365],.245,.28,.06,'armor',.05,.86),
    loft('front-collar-'+str(s),[s*.254,.09,.245],.35,.25,.27,'graphite',.055,.84),
    box('shoulder-index-'+str(s),[s*.48,-.18,.364],[.029,.11,.007],'cyan',.002,[0,s*.20,0])]
    for j in range(4):G[3]+=[box(f'rear-fin-{s}-{j}',[s*.38,-.798,.20+j*.035],[.15,.024,.013],'edge',.002)]
G[4]=[
 loft('inner-bracket',[0,0,0],.19,.85,.23,'graphite',.065,.85),
 loft('forward-armor',[0,.19,.054],.255,.40,.25,'armor',.08,.71),
 loft('rear-armor',[0,-.24,.055],.255,.32,.24,'armor',.06,.80),
 loft('central-bridge',[0,-.018,.107],.23,.10,.11,'edge',.02,.80),
 box('forward-strip',[0,.19,.182],[.024,.20,.007],'cyan',.002),box('aft-strip',[0,-.25,.179],[.022,.12,.007],'cyan',.002),
 loft('front-wedge',[0,.394,-.01],.17,.11,.14,'edge',.04,.58)
]
for sx in [-1,1]:
    G[4]+=[box('gill-bed-'+str(sx),[sx*.124,-.10,.025],[.012,.27,.105],'rubber',.002)]
    for j in range(5):G[4]+=[box(f'gill-{sx}-{j}',[sx*.133,-.20+j*.049,.037],[.021,.017,.112],'edge',.002,[.30,0,0])]
G[5]=[
 cyl('hex-core',[0,.20,0],.105,.48,'graphite',6,'Y'),
 loft('rear-receiver',[0,.065,.055],.30,.28,.24,'armor',.055,.82),
 loft('forward-shroud',[0,.265,.035],.25,.22,.21,'armor',.06,.72),
 box('separation',[0,.18,.04],[.255,.018,.19],'rubber',.002),
 box('upper-rail',[0,.14,.185],[.12,.37,.032],'graphite',.003),
 box('rail-light',[0,.13,.204],[.027,.26,.008],'cyan',.002),
 cyl('hex-muzzle',[0,.403,0],.137,.16,'edge',6,'Y'),
 cyl('recess',[0,.486,0],.113,.009,'rubber',6,'Y'),
 box('optics-bed',[0,.492,0],[.134,.007,.109],'glass',.004),
 box('slit-upper',[0,.498,.034],[.101,.005,.013],'cyan',.001),
 box('slit-lower',[0,.498,-.034],[.101,.005,.013],'cyan',.001),
 box('central-iris',[0,.499,0],[.043,.005,.035],'cyan',.002),
]
for sx in [-1,1]:
    G[5]+=[box('side-rail-'+str(sx),[sx*.148,.12,.037],[.023,.28,.07],'edge',.003),box('side-slot-'+str(sx),[sx*.162,.08,.038],[.006,.09,.021],'rubber',.001)]
    for j in range(3):G[5]+=[box(f'side-rib-{sx}-{j}',[sx*.158,.20+j*.042,.03],[.022,.015,.105],'graphite',.002)]
G[6]=[
 loft('sensor-foot',[0,0,.02],.17,.18,.04,'graphite',.03,.90),
 loft('angled-hood',[0,.015,.086],.19,.24,.12,'armor',.045,.64),
 box('optical-recess',[0,.136,.081],[.143,.012,.065],'rubber',.002),
 box('main-optic',[-.027,.144,.083],[.058,.005,.023],'cyan',.002),box('range-optic',[.047,.144,.083],[.018,.005,.023],'glass',.002),
 loft('roof-fin',[0,-.035,.17],.035,.115,.08,'edge',.009,.50),box('fin-tip',[0,-.035,.213],[.015,.055,.007],'cyan',.001)
]
G[7]=[
 loft('seam',[0,0,0],.4,.15,.02,'graphite',.032,.94),loft('angled-lid',[0,0,.02],.37,.125,.034,'armor',.03,.85),
 box('handle-recess',[0,-.012,.040],[.095,.033,.007],'rubber',.002),box('handle',[0,-.012,.047],[.062,.012,.009],'edge',.002)
]
for sx in [-1,1]:G[7]+=[box('latch-'+str(sx),[sx*.143,0,.046],[.032,.06,.015],'edge',.002),box('status-'+str(sx),[sx*.075,.033,.041],[.031,.009,.005],'cyan',.001)]
for n,geom in G.items():
    pid=f'CHT-P{n:02}';p=R/f'Parts/{pid}/part.json';d=json.loads(p.read_text(encoding='utf-8'))
    archive=R/f'Parts/{pid}/Versions/1.0.0.json'
    if not archive.exists():
        old=dict(d);old['materialLibrary']='../../../Materials/materials.json';save(archive.relative_to(R),old)
    d['version']='1.1.0';d['geometry']=geom;d['materialSlots']=sorted(set(g['material'] for g in geom));d['emission']=[dict(id=g['id'],material=g['material'],defaultEnabled=True,intensityUnit='Three.js multiplier') for g in geom if g['material'] in ['cyan','glass']]
    d.pop('bounds',None)
    if n==3:d['title']='Составной гранёный бронекорпус'
    if n==5:d['functionalPoints'][0]['position']=[0,.501,0]
    save(f'Parts/{pid}/part.json',d)
p=R/'Blocks/CHT-T01/assembly.json';d=json.loads(p.read_text(encoding='utf-8'))
if not (R/'Blocks/CHT-T01/Versions/1.0.0.json').exists():
    old=json.loads(json.dumps(d))
    for i in old['instances']:i['source']='../../../Parts/'+i['partId']+'/Versions/1.0.0.json'
    old['catalogReference']='../../../../Catalog/blocks.csv'
    save('Blocks/CHT-T01/Versions/1.0.0.json',old)
d['version']='1.1.0'
for i in d['instances']:i['partVersion']='1.1.0'
d['scaleNote']='Model units, not metres. Catalogue XY barrel X offsets preserved; visual muzzle Y=0.581 relative to pivot vs catalogue 0.55. No gameplay integration.'
save('Blocks/CHT-T01/assembly.json',d)
p=R/'README.md';s=p.read_text(encoding='utf-8').replace('мягкие скругления','гранёные составные формы, наклонные панели и небольшие фаски').replace('Модель доступна и как отдельный glTF в Exports/.','Модель доступна и как отдельный glTF в Blocks/CHT-T01/Exports/.');save('README.md',s)
print('Revision 1.1.0:',sum(len(x) for x in G.values()),'geometry elements in 7 reusable parts')
