"""Functional form revision of final W05/W06 sources, preserving all interfaces."""
import json, math, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    s=v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def backup(p):
    old=read(p);target=p.parent/'Versions'/f'{old["version"]}.json'
    if old['version']=='1.0.0' and not target.exists():write(target,old)
    return old

def lathe(id,pos,profile,mat='armor',axis='Y'):
    return dict(id=id,shape='lathe',position=pos,profile=profile,segments=48,axis=axis,material=mat)

def blade(id,outline,mat='armor',depth=.065):
    return dict(id=id,shape='profile',outline=outline,holes=[],depth=depth,bevel=.004,position=[0,0,0],rotationEulerXYZ=[0,math.pi/2,math.pi/2],material=mat)

def points(g):
    if g['shape']=='loft':v=[[x*l['scale'][0],y*l['scale'][1],l['z']] for l in g['levels'] for x,y in g['outline']]
    elif g['shape']=='lathe':
        v=[]
        for r,a in g['profile']:
            for i in range(g.get('segments',48)):
                t=i*2*math.pi/g.get('segments',48);x,y=r*math.cos(t),r*math.sin(t)
                v.append([x,a,y] if g['axis']=='Y' else [x,y,a] if g['axis']=='Z' else [a,x,y])
    elif g['shape']=='profile':
        # Conservative bevel envelope; depth centered about local Z.
        b=g.get('bevel',0);xs=[p[0] for p in g['outline']];ys=[p[1] for p in g['outline']]
        v=[[x,y,z] for x in [min(xs)-b,max(xs)+b] for y in [min(ys)-b,max(ys)+b] for z in [-g['depth']/2-b,g['depth']/2+b]]
    else:v=[[x*g['size'][0]/2,y*g['size'][1]/2,z*g['size'][2]/2] for x in [-1,1] for y in [-1,1] for z in [-1,1]]
    a,b,c=g.get('rotationEulerXYZ',[0,0,0]);ca,sa=math.cos(a),math.sin(a);cb,sb=math.cos(b),math.sin(b);cc,sc=math.cos(c),math.sin(c)
    out=[]
    for x,y,z in v:
        x,y=x*cc-y*sc,x*sc+y*cc;x,z=x*cb+z*sb,-x*sb+z*cb;y,z=y*ca-z*sa,y*sa+z*ca
        out.append([x+g['position'][0],y+g['position'][1],z+g['position'][2]])
    return out

def save(p):
    vs=[v for g in p['geometry'] for v in points(g)];lo=[min(v[k] for v in vs) for k in range(3)];hi=[max(v[k] for v in vs) for k in range(3)]
    p['bounds']=dict(min=lo,max=hi,size=[hi[k]-lo[k] for k in range(3)])
    p['version']='1.1.0';p['materialSlots']=sorted({g['material'] for g in p['geometry']})
    p['emission']=[dict(id=g['id'],material=g['material'],defaultEnabled=True,intensityUnit='Three.js multiplier',color='#25bfff' if g['material']=='cyan' else '#1686bf',intensity=2.5 if g['material']=='cyan' else .65) for g in p['geometry'] if g['material'] in ('cyan','glass')]
    write(ROOT/'Parts'/p['id']/'part.json',p)

modified=[]
for id in ['CHT-W05-BASE','CHT-W05-CASSETTE','CHT-W06-OPTIC','CHT-W06-RADIATOR']:
    path=ROOT/'Parts'/id/'part.json';p=backup(path)
    # Always derive from the immutable initial source; reruns remain reproducible.
    original=path.parent/'Versions/1.0.0.json'
    p=read(original)
    if id=='CHT-W05-BASE':
        p['geometry']=[g for g in p['geometry'] if g['id']!='bearing-platform']
        p['geometry'].append(lathe('profiled-yaw-bearing',[0,0,0],[[.33,.28],[.49,.28],[.54,.31],[.54,.35],[.47,.395],[.33,.395],[.33,.28]],'edge','Z'))
        note='Опорный подшипник заменён настоящим кольцевым профилем вращения с наклонным буртом; палуба сохранена.'
    elif id=='CHT-W05-CASSETTE':
        p['geometry']=[g for g in p['geometry'] if g['id'] not in ['missile-body','missile-nose']]
        p['geometry'].append(lathe('missile-round-body-and-ogive',[0,0,.25],[[0,-.3],[.085,-.3],[.104,-.265],[.104,.25],[.1,.32],[.082,.38],[.052,.445],[.014,.49],[0,.5]],'edge'))
        # Small continuous white ogive section; exactly aligned to the exposed rocket.
        p['geometry'].append(lathe('missile-white-ogive',[0,0,.25],[[.1005,.316],[.097,.34],[.08,.386],[.05,.449],[.013,.494],[0,.504],[0,.316],[.1005,.316]],'armor'))
        note='Прямоугольная пусковая кассета сохранена. Внутри — цилиндрическая ракета с профилированным коническим носом; квадратная декоративная ракета удалена.'
    elif id=='CHT-W06-OPTIC':
        p['geometry']=[
            lathe('conical-optical-shroud',[0,0,.15],[[.14,-.29],[.18,-.29],[.205,-.21],[.245,.12],[.278,.255],[.278,.31],[.26,.34],[.224,.34],[.224,.3],[.227,.255],[.2,.12],[.15,-.21],[.14,-.29]],'armor'),
            lathe('dark-inner-optical-barrel',[0,0,.15],[[.15,-.23],[.19,-.23],[.213,.245],[.213,.305],[.192,.305],[.17,.2],[.135,-.23],[.15,-.23]],'graphite'),
            lathe('front-metal-optical-bezel',[0,0,.15],[[.213,.285],[.228,.285],[.24,.305],[.24,.325],[.226,.337],[.213,.337],[.213,.285]],'edge'),
            lathe('convex-emitting-lens',[0,0,.15],[[0,.29],[.19,.29],[.19,.308],[.17,.317],[.13,.326],[.075,.333],[0,.337]],'glass'),
            lathe('cyan-optical-annulus',[0,0,.15],[[.193,.308],[.202,.308],[.202,.321],[.193,.321],[.193,.308]],'cyan'),
            lathe('lens-emitting-center',[0,0,.15],[[0,.336],[.07,.332],[.075,.334],[.04,.338],[0,.339]],'cyan')]
        note='Коробчатая оптика полностью заменена полым коническим кожухом вращения, круглым металлическим ободом и выпуклой линзой. Один функциональный луч сохранён, muzzle перед центром линзы.'
    else:
        rail=next(g for g in p['geometry'] if g['id']=='coolant-rail')
        p['geometry']=[rail]
        outlines=[
            [[-.56,.1],[-.23,.1],[-.18,.37],[-.31,.86],[-.46,.95],[-.55,.77]],
            [[-.18,.1],[.13,.1],[.19,.32],[.06,.71],[-.055,.79],[-.16,.59]],
            [[.2,.1],[.52,.1],[.58,.25],[.43,.53],[.32,.6],[.22,.42]]]
        for i,o in enumerate(outlines):
            p['geometry'].append(blade(f'swept-radiator-sail-{i}',o))
            # Thin darker heat-spreader follows the polygon, not rectangular stickers.
            cx=sum(v[0] for v in o)/len(o);cy=sum(v[1] for v in o)/len(o)
            inner=[[cx+(x-cx)*.68,cy+(y-cy)*.76] for x,y in o]
            dark=blade(f'sail-heat-spreader-{i}',inner,'graphite',.009);dark['position']=[.039,0,0];p['geometry'].append(dark)
            tip=blade(f'sail-cyan-tip-{i}',[[o[3][0]-.025,o[3][1]-.025],[o[4][0]-.014,o[4][1]-.027],[o[4][0]+.014,o[4][1]],[o[3][0]+.01,o[3][1]]],'cyan',.069)
            p['geometry'].append(tip)
        note='Ряд одинаковых прямоугольных столбиков заменён тремя неравными стреловидными лопастями с наклонными кромками и глубокими сквозными промежутками. Тёмные теплоотводящие вставки повторяют профиль лопастей.'
    save(p);modified.append(id)
    readme=path.parent/'README.md';text=readme.read_text(encoding='utf-8').split('\nИзменение формы 1.1.0:')[0].rstrip().replace('1.0.0','1.1.0')+'\n'
    write(readme,text+'\nИзменение формы 1.1.0: '+note+' Исходник 1.0.0 сохранён в Versions/1.0.0.json.\n')

for bid in ['CHT-W05','CHT-W06']:
    path=ROOT/'Blocks'/bid/'assembly.json';a=backup(path);a['version']='1.1.0'
    for i in a['instances']:
        if i['partId'] in modified:i['partVersion']='1.1.0'
    write(path,a)
    detail=('Цилиндрические ракеты с коническими головными частями в прежних четырёх квадратных кассетах. Профилированный кольцевой подшипник опоры.' if bid=='CHT-W05' else 'Круглая выпуклая линза и полый конический оптический кожух; радиаторы состоят из трёх стреловидных лопастей разной высоты.')
    for name in ['README.md','composition-plan.md']:
        p=path.parent/name;text=p.read_text(encoding='utf-8').split('\nОбновление формы 1.1.0:')[0].rstrip()+'\n'
        text=text.replace('один большой квадратный излучатель','один большой круглый излучатель').replace('единственным большим квадратным излучателем','единственным большим круглым излучателем')
        write(p,text+'\nОбновление формы 1.1.0: '+detail+' Состав и крепления сохранены; новые формы заменяют прежние доминирующие объёмы.\n')
    v=read(path.parent/'validation.json');v['formRevision']='1.1.0';v['geometryBounds']='recomputed with rotational profiles and bevel envelope';v['functionalInterfaces']='unchanged: same sockets, muzzle count/poses, yaw axis and range';write(path.parent/'validation.json',v)
mesh_check=r'''
import fs from 'node:fs';
import {geometry,T} from './Viewer/geometry.js';
const root='Projects/SS/CorporateHiTech';
let count=0;
for(const id of ['CHT-W05-BASE','CHT-W05-CASSETTE','CHT-W06-OPTIC','CHT-W06-RADIATOR']){
 const path=`${root}/Parts/${id}/part.json`,p=JSON.parse(fs.readFileSync(path,'utf8')),old=JSON.parse(fs.readFileSync(`${root}/Parts/${id}/Versions/1.0.0.json`,'utf8'));
 if(JSON.stringify(p.attachments)!==JSON.stringify(old.attachments)||JSON.stringify(p.functionalPoints)!==JSON.stringify(old.functionalPoints))throw Error('Interface drift '+id);
 const bound=new T.Box3();
 for(const g of p.geometry){
  const geo=geometry(g),pos=geo.attributes.position,norm=geo.attributes.normal,uv=geo.attributes.uv;
  const m=new T.Matrix4().compose(new T.Vector3(...g.position),new T.Quaternion().setFromEuler(new T.Euler(...(g.rotationEulerXYZ||[0,0,0]))),new T.Vector3(1,1,1));
  for(let i=0;i<pos.count;i++){
   const v=new T.Vector3().fromBufferAttribute(pos,i).applyMatrix4(m);if(![v.x,v.y,v.z,norm.getX(i),norm.getY(i),norm.getZ(i),uv.getX(i),uv.getY(i)].every(Number.isFinite))throw Error('Nonfinite vertex '+g.id);bound.expandByPoint(v);
  }count++;geo.dispose();
 }
 p.bounds={min:bound.min.toArray(),max:bound.max.toArray(),size:bound.getSize(new T.Vector3()).toArray()};
 fs.writeFileSync(path,(JSON.stringify(p,null,2)+'\n').replace(/\n/g,'\r\n'));
}
console.log('Validated actual Viewer geometry, UVs, normals, exact bounds and unchanged interfaces:',count,'primitives.');
'''
subprocess.run(['node','--input-type=module','-e',mesh_check],cwd=ROOT.parents[2],check=True)
for bid in ['CHT-W05','CHT-W06']:
    path=ROOT/'Blocks'/bid/'validation.json';v=read(path);v['geometryBounds']='exact transformed mesh vertices from Viewer/geometry.js';v['geometryAttributes']='all primitive positions, normals and UVs finite';write(path,v)
print('Revised four parts and both assemblies to 1.1.0; immutable 1.0.0 JSON preserved. Muzzles and sockets unchanged.')
