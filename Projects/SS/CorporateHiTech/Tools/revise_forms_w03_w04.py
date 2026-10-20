"""Replace dominant box forms with functional profiled housings, final revision 1.1."""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    text=(json.dumps(data,ensure_ascii=False,indent=2)+'\n') if not isinstance(data,str) else data
    path.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def archive(path):
    target=path.parent/'Versions/1.0.0.json'
    if not target.exists():write(target,read(path))
def lathe(id,p,profile,mat='armor',axis='Y'):
    return dict(id=id,shape='lathe',position=p,profile=profile,segments=48,axis=axis,material=mat)
def profile(id,p,outline,depth,mat='armor',holes=None,rotation=None):
    g=dict(id=id,shape='profile',position=p,outline=outline,holes=holes or [],depth=depth,bevel=.004,material=mat)
    if rotation:g['rotationEulerXYZ']=rotation
    return g
def box(id,p,size,mat):return dict(id=id,shape='roundedBox',position=p,size=size,radius=.003,material=mat)
def update(pid,fn,lo,hi,note):
    path=ROOT/'Parts'/pid/'part.json';archive(path);d=read(path);fn(d)
    d['version']='1.1.0';d['bounds']=dict(min=lo,max=hi,size=[round(b-a,6) for a,b in zip(lo,hi)])
    d['materialSlots']=sorted({g['material'] for g in d['geometry']})
    d['emission']=[dict(id=g['id'],geometry=g['id'],material='cyan',color='#25bfff',intensity=2.5,intensityUnit='Three.js multiplier',defaultEnabled=True) for g in d['geometry'] if g['material']=='cyan']
    write(path,d)
    write(path.parent/'README.md',f'# {pid} — {d["title"]}\n\nВерсия 1.1.0. {note}\n\nИсходник part.json: правая система, +Y вперёд, +Z вверх, model-unit, единичный масштаб. Сохранены все sockets, направления и функциональные точки. Параметрические lathe/profile/loft являются редактируемой геометрией. Белое покрытие armor, graphite/rubber механика, edge кромки, cyan эмиссия 2.5. Процедурное PBR, SharedTextures через общий просмотрщик; исходных растровых карт нет. Самостоятельных анимаций нет. Предыдущий JSON в Versions/1.0.0.json — архив, не альтернативный блок.\n')

def w03_barrel(d):
    # Continuous annular contours describe actual bores and conical adapters.
    d['geometry']=[
        lathe('profiled-cooling-jacket',[0,0,0],[[.099,.015],[.119,.055],[.119,.17],[.092,.23],[.092,.78],[.107,.84],[.107,.925],[.080,.958],[.065,.958],[.065,.82],[.059,.22],[.074,.015],[.099,.015]],'graphite'),
        lathe('white-breech-shroud',[0,0,0],[[.121,.012],[.145,.065],[.145,.145],[.123,.215],[.106,.215],[.125,.14],[.125,.065],[.104,.012],[.121,.012]],'armor'),
        lathe('tapered-muzzle-sleeve',[0,0,0],[[.112,.815],[.128,.85],[.128,.92],[.103,.974],[.075,.974],[.071,.946],[.089,.916],[.105,.85],[.099,.815],[.112,.815]],'armor'),
        lathe('open-metal-muzzle',[0,0,0],[[.103,.964],[.105,.990],[.074,.990],[.074,.964],[.103,.964]],'edge'),
        lathe('recessed-bore-wall',[0,0,0],[[.065,.65],[.068,.974],[.060,.974],[.057,.65],[.065,.65]],'rubber')]
    # Keep two genuine longitudinal cooling/power rails attached to the round jacket.
    for sign in [-1,1]:
        d['geometry'] += [box(f'jacket-rail-{sign}',[sign*.081,.51,.063],[.032,.57,.046],'edge'),box(f'rail-emission-{sign}',[sign*.083,.51,.090],[.017,.43,.008],'cyan')]

def w03_side(d):
    arch=[[-.39,.065],[-.37,.25],[-.29,.365],[-.20,.405],[.14,.405],[.27,.35],[.365,.20],[.39,.075],[.28,.025],[.22,.18],[.13,.25],[-.17,.25],[-.25,.16],[-.27,.025]]
    d['geometry']=[profile('arched-feed-shell',[0,0,0],arch,.27,'armor',rotation=[math.pi/2,math.pi/2,0]),
      lathe('feed-spindle',[0,-.015,.145],[[.075,-.145],[.125,-.115],[.145,-.07],[.145,.07],[.125,.115],[.075,.145],[0,.145],[0,-.145],[.075,-.145]],'graphite','X'),
      profile('feed-underbridge',[0,0,.025],[[-.12,-.32],[.12,-.32],[.14,.23],[.09,.32],[-.09,.32],[-.14,.23]],.035,'edge'),
      box('feed-charge-line',[0,-.025,.412],[.035,.30,.008],'cyan')]

def w03_hull(d):
    # Replace the broad rectangular rear receiver shell with a swept armoured casting.
    d['geometry']=[g for g in d['geometry'] if g['id'] not in ['receiver','rear-power-pack','rear-service-cap']]
    outline=[[-.28,-.69],[.28,-.69],[.39,-.53],[.42,-.16],[.35,.12],[.23,.25],[-.23,.25],[-.35,.12],[-.42,-.16],[-.39,-.53]]
    d['geometry'].append(dict(id='swept-receiver-casting',shape='loft',position=[0,0,0],outline=outline,levels=[dict(z=.13,scale=[.92,.96]),dict(z=.20,scale=[1,1]),dict(z=.32,scale=[.94,.96]),dict(z=.425,scale=[.77,.88])],material='armor'))
    d['geometry'].append(profile('rear-service-brow',[0,-.68,.30],[[-.24,-.12],[.24,-.12],[.26,.02],[.17,.11],[-.17,.11],[-.26,.02]],.10,'graphite'))

def w04_barrel(d):
    # One true circular open channel: eight pellets do not require eight holes.
    d['geometry']=[
      lathe('conical-shotgun-body',[0,0,0],[[.225,-.012],[.29,.065],[.29,.23],[.267,.42],[.249,.575],[.215,.60],[.193,.60],[.177,.45],[.173,.12],[.165,-.012],[.225,-.012]],'graphite'),
      lathe('white-tapered-shroud',[0,0,0],[[.295,.075],[.308,.12],[.308,.24],[.277,.42],[.256,.56],[.231,.59],[.216,.59],[.239,.55],[.258,.40],[.286,.23],[.280,.12],[.275,.075],[.295,.075]],'armor'),
      lathe('open-choke-rim',[0,0,0],[[.237,.569],[.245,.598],[.228,.61],[.195,.61],[.193,.59],[.213,.576],[.237,.569]],'edge'),
      lathe('dark-inner-bore',[0,0,0],[[.174,.12],[.193,.59],[.184,.59],[.164,.12],[.174,.12]],'rubber')]
    for sign in [-1,1]:
        d['geometry'] += [profile(f'underslung-guide-{sign}',[sign*.23,.23,-.20],[[-.035,-.25],[.035,-.25],[.041,.14],[.02,.23],[-.02,.23],[-.041,.14]],.065,'edge'),box(f'choke-status-{sign}',[sign*.26,.31,.14],[.014,.18,.02],'cyan')]

def w04_side(d):
    # A curved swept shield with a through ventilation slot, replacing three stacked boxes.
    outline=[[-.07,-.39],[.055,-.40],[.13,-.35],[.18,-.25],[.20,-.10],[.19,.10],[.15,.27],[.07,.39],[-.055,.37],[-.145,.23],[-.19,.05],[-.17,-.17],[-.12,-.32]]
    hole=[[-.055,-.17],[-.065,.10],[-.025,.22],[.025,.23],[.055,.10],[.06,-.13],[.02,-.21],[-.025,-.21]]
    d['geometry']=[profile('swept-vented-shoulder',[0,0,.235],outline,.18,'armor',[hole]),
      profile('curved-wing-foundation',[0,0,.08],[[-.12,-.33],[.08,-.35],[.15,-.22],[.17,.06],[.08,.33],[-.05,.35],[-.15,.15],[-.16,-.12]],.12,'graphite'),
      profile('rear-shoulder-ridge',[0,-.24,.34],[[-.075,-.10],[.06,-.10],[.10,.02],[.05,.11],[-.06,.10],[-.10,.01]],.045,'edge'),
      box('wing-status',[.105,-.12,.335],[.022,.15,.008],'cyan')]

def main():
    update('CHT-W03-HULL',w03_hull,[-.43,-.83,0],[.43,.36,.52],'Основная белая оболочка заменена сужающимся литым корпусом; задний узел профилирован.')
    update('CHT-W03-BARREL',w03_barrel,[-.15,0,-.15],[.15,.995,.15],'Настоящий круглый открытый канал, профилированный кожух охлаждения, конические переходы и продольные рельсы заменяют прямоугольный ствол. Дульная точка сохранена.')
    update('CHT-W03-SIDE',w03_side,[-.15,-.40,0],[.15,.40,.42],'Арочная силовая кассета с открытым поднутрением и видимым шпинделем подачи вместо стопки коробок.')
    update('CHT-W04-BARREL',w04_barrel,[-.315,-.03,-.315],[.315,.615,.315],'Один настоящий круглый раскрытый канал с коническим кожухом, открытым металлическим чоком и глубокой внутренней стенкой заменяет сегментную коробчатую раму.')
    update('CHT-W04-SIDE',w04_side,[-.205,-.405,0],[.205,.405,.37],'Плавно профилированное плечо с настоящим сквозным вентиляционным отверстием заменяет три коробчатых уровня брони.')
    for bid in ['CHT-W03','CHT-W04']:
        ap=ROOT/'Blocks'/bid/'assembly.json';archive(ap);a=read(ap);a['version']='1.1.0'
        for n in a['instances']:
            if n['partId'].startswith(bid):n['partVersion']=read((ap.parent/n['source']).resolve())['version']
        write(ap,a)
        readme=ap.parent/'README.md';text=readme.read_text(encoding='utf-8')
        text+='\nРедакция 1.1.0: доминирующие коробчатые формы заменены функциональными профилями. '+('Два круглых открытых ствольных кожуха с коническими переходами; арочные кассеты со шпинделями подачи; сужающийся литой приёмник.' if bid=='CHT-W03' else 'Один большой круглый открытый канал с коническим переходом и металлическим чоком; широкие плавно профилированные плечи со сквозными вентиляционными щелями.')+' Компоновка, палитра, точки крепления, число каналов и наведение сохранены. Предыдущие JSON архивированы в Versions/1.0.0.json, альтернативные зарегистрированные блоки и отдельные превью не создавались.\n'
        write(readme,text)
        plan=ap.parent/'composition-plan.md';write(plan,plan.read_text(encoding='utf-8')+'\n## Редакция форм 1.1.0\n\nВарианты существующих собственных деталей: lathe с замкнутым кольцевым профилем для настоящих открытых каналов и конических переходов; profile для арочных/плавных силовых оболочек. Точки крепления и единичный масштаб сохранены. P01/P02 неизменны. Геометрия заменяет старые коробки, а не добавляет случайный декор.\n')
        report=dict(block=bid,revision='1.1.0',refs=True,sockets=True,functionalMuzzles=[],previousVersion='Versions/1.0.0.json',visualVerification='delegated to final common viewer check')
        nodes={n['id']:n for n in a['instances']};defs={}
        for n in a['instances']:
            p=(ap.parent/n['source']).resolve();d=read(p);defs[n['id']]=d
            assert d['version']==n['partVersion']
            if n['attachment']:
                at=n['attachment'];ps=next(s for s in defs[n['parent']]['attachments'] if s['id']==at['parentSocket']);cs=next(s for s in d['attachments'] if s['id']==at['childSocket'])
                assert all(abs(ps['position'][i]-cs['position'][i]-n['translation'][i])<1e-8 for i in range(3))
                assert all(abs(ps['normal'][i]+cs['normal'][i])<1e-8 for i in range(3));assert ps['up']==cs['up']
            if any(fp['role']=='projectile-muzzle' for fp in d['functionalPoints']):report['functionalMuzzles'].append(n['id'])
        assert len(report['functionalMuzzles'])==(2 if bid=='CHT-W03' else 1)
        write(ap.parent/'source-validation.json',report)
        print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
