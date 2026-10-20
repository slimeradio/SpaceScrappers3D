"""Explicit floor kit and uniform, point-preserving body placement for MilitaryArmor."""
from pathlib import Path
import json,sys,math,shutil,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parents[2]
BACKUP=ROOT/'Versions/FloorFitBefore'
CORNER=.12
MARGIN=.08
FRAME=.06

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    text=obj if isinstance(obj,str) else json.dumps(obj,indent=2,ensure_ascii=False)
    p.write_bytes((text.replace('\r\n','\n').rstrip()+'\n').replace('\n','\r\n').encode('utf-8'))

def backup(p):
    target=BACKUP/p.relative_to(ROOT)
    if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    return target

def contour(w,h,e):
    if e.get('Type')=='Armor':
        coords=list(map(float,e.find('Colliders/ConvexCollider').get('Data').split()))
        points=[(coords[i]-w/2,coords[i+1]-h/2) for i in range(0,len(coords),2)]
    else:points=[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]
    area=sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))
    return points if area>0 else points[::-1]

def plan(game):
    profile=read(ROOT/'SpriteBake/profile.json');records={}
    definitions={}
    for p in Path(game,'Assets/Definitions').rglob('*.definition.xml'):
        e=ET.parse(p).getroot()
        if e.tag in ('Block','ReactorBlock'):definitions[e.get('Name')]=e
    exclusions={
      'MA-D01':['cutting-head'],'MA-D02':['cutter-left','cutter-right'],
      'MA-D03':['cutter-port','cutter-center','cutter-starboard'],
      'MA-E01':['Nozzle'],'MA-E02':['Nozzle0','Nozzle1','Nozzle2'],
      'MA-EF01':['ExpansionBell'],'MA-EF02':['ExpansionBell'],
      'MA-EF03':['ExpansionBellL','ExpansionBellR'],
      'MA-EF04':['ExpansionBellL','ExpansionBellR','ExpansionBellU'],
      'MA-T01':['Barrel.L','Barrel.R'],
      'MA-W01':['Accelerator0','Accelerator1','Accelerator2'],
      'MA-W02':['ContinuousEmitter'],'MA-W03':['BarrelLeft','BarrelRight'],
      'MA-W05':['ScatterAperture'],'MA-W06':['SplitRail'],
      'MA-W07':['SingleMachinegun'],'MA-W09':['Gun'],'MA-W10':['FocusAperture'],
    }
    for bid,spec in profile['blocks'].items():
        p=ROOT/spec['assembly'];a=read(backup(p));backup(ROOT/spec['source'])
        ids=[i['id'] for i in a['instances']]
        excluded=exclusions.get(bid,[])
        if bid.startswith('MA-H0'):excluded=[i for i in ids if i.startswith(('Fin-','RadiatingBlade-'))]
        assert set(excluded)<=set(ids),(bid,excluded)
        refs=[i for i in ids if i not in excluded];assert refs
        w,h=a['catalog_grid'];poly=contour(w,h,definitions[a['catalog_id']])
        shape='wedge' if len(poly)==3 else 'rect'
        fid=f'MA-FLOOR-{shape}-{w}x{h}'
        records[bid]=dict(floor=fid,polygon=poly,grid=[w,h],body_instances=refs,protrusion_instances=excluded)
        write(p.parent/'floor-plan.md',f'# Floor и размер {bid}\n\nFloor {fid}: поверхность Color1, рамка Color2. Угол {CORNER} клетки, рамка {FRAME}, margin {MARGIN}. Геометрия floor параметрическая, углы не масштабируются. Корпус: {", ".join(refs)}. Разрешённые выступы: {", ".join(excluded) or "нет"}. Единственный равномерный ModelFit переносит также узлы, анимации и функциональные точки. Существующие детали и клипы повторно используются; новые механизмы/повреждения не создаются. GLB не создаётся.\n')
    backup(ROOT/'SpriteBake/profile.json')
    write(ROOT/'floor-fit.json',dict(schema='MilitaryArmor.FloorFit/1',corner_cells=CORNER,frame_cells=FRAME,margin_cells=MARGIN,blocks=records))

if __name__=='__main__' and '--plan' in sys.argv:
    plan(sys.argv[sys.argv.index('--game')+1])
