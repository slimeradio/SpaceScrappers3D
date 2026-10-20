"""Bind pre-fit XML geometry to stable model point IDs, once, before metadata/bake."""
from pathlib import Path
import sys,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parent))
from floor_fit import ROOT,BACKUP,read,write
profile=read(BACKUP/'SpriteBake/profile.json')
definitions={}
for p in (BACKUP/'GameDefinitions').rglob('*.definition.xml'):
    e=ET.parse(p).getroot()
    if e.tag in ('Block','ReactorBlock'):definitions[e.get('Name')]=e
for bid,spec in profile['blocks'].items():
    a=read(ROOT/spec['assembly']);old=read(BACKUP/'Metadata'/(bid+'.json'));points=old['frames']['damage0']['points'];d=definitions[a['catalog_id']]
    def match(tag,subset):
        candidates=list(subset);bindings=[]
        for node in tag:
            xy=[float(node.get('X')),float(node.get('Y'))]
            p=next(p for p in candidates if all(abs(p['position_cells'][i]-xy[i])<1e-5 for i in (0,1)))
            candidates.remove(p);bindings.append((node,p))
        assert not candidates,(bid,'unbound functional point');return bindings
    if d.find('Drill') is not None:
        bindings=match(d.findall('Drill/Head'),[p for p in points if p['id'].endswith('/functional_points/tool-axis')])
        a['floor_fit']['drill_head_order']=[p['id'] for n,p in bindings]
        a['floor_fit']['drill_radii_cells']={p['id']:float(n.get('Radius'))*spec['bu_per_cell']*a['floor_fit']['uniform_scale'] for n,p in bindings}
    if d.find('Thrusters') is not None:
        bindings=match(d.findall('Thrusters/Thruster/Position'),[p for p in points if p['id'].endswith('/functional_points/thrust')])
        a['floor_fit']['thruster_point_order']=[p['id'] for n,p in bindings]
    write(ROOT/spec['assembly'],a)
print('Stable drill radius/head and thrust bindings stored in floor-fit metadata.')
