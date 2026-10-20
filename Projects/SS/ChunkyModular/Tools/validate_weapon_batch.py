"""Read-only audit of final six weapons; writes the batch manifest, no render assets."""
import json, struct, hashlib, csv
from pathlib import Path

STYLE=Path(__file__).resolve().parent.parent
IDS=['fleet-minigun-cyclone','fleet-artillery-monitor','sniper-turret',
     'continuous-laser-turret','fleet-rocket-bastion','fleet-shotgun-fan']
LABELS=['Спаренный роторный пулемёт','Трёхствольная артиллерия','Снайперская рельсовая турель',
        'Турель непрерывного лазера','Четырёхканальная ракетная турель','Широкий одноствольный дробовик']
PREFIXES=('cm-cyclone-','cm-monitor-','cm-sniper-','cm-beam-','cm-bastion-','cm-fan-')

def read(path): return json.loads(path.read_text(encoding='utf-8'))

def inspect_glb(path):
    raw=path.read_bytes()
    magic,version,size=struct.unpack_from('<4sII',raw)
    assert (magic,version,size)==(b'glTF',2,len(raw)),path
    length,kind=struct.unpack_from('<II',raw,12); assert kind==0x4e4f534a
    doc=json.loads(raw[20:20+length])
    assert all('uri' not in item for item in doc.get('buffers',[])),path
    assert all('bufferView' in item for item in doc.get('images',[])),path
    assert doc.get('meshes') and doc.get('materials'),path
    return doc,hashlib.sha256(raw).hexdigest(),len(raw)

catalog={row['ID']:row for row in csv.DictReader((STYLE.parent/'Catalog'/'blocks.csv').open(encoding='utf-8-sig',newline=''))}
models=[]; new_parts=set(); reused=set(); checked=[]
for id,title in zip(IDS,LABELS):
    block=STYLE/'Blocks'/id; output=STYLE/'Exports'/id
    assembly=read(block/'assembly.json'); report=read(output/'validation.json')
    assert report['status']=='passed' and all(report['real_reimport'].values()),id
    assert assembly['catalog_id']==id and id in catalog
    assert len(assembly['functional_points'])==report['logical_muzzles']
    assert len({p['id'] for p in assembly['functional_points']})==report['logical_muzzles']
    assert len(assembly['sampled_poses'])==7
    doc,digest,size=inspect_glb(output/(id+'.glb'))
    assert sum('mesh' in node for node in doc['nodes'])==report['mesh_objects']
    assert doc.get('animations'),id
    source=block/(id+'.blend'); assert source.is_file() and source.stat().st_size>1000
    assert (block/'build.py').is_file() and (block/'PLAN.md').is_file()
    assert not list(block.glob('*.png')) and not list(output.glob('*.png'))
    for instance in assembly['instances']:
        pid=instance['part']; p=STYLE/'Parts'/pid; meta=read(p/'part.json')
        assert meta['id']==pid and meta['version']==instance['version']
        assert (p/meta['source']).is_file()
        if pid.startswith(PREFIXES):
            if pid not in new_parts: inspect_glb(STYLE/'Exports'/'Parts'/(pid+'.glb'))
            new_parts.add(pid)
            assert not list(p.glob('*.png')) and not list(p.glob('*.gif'))
            checked+=list(p.glob('*.json'))
        else: reused.add(pid)
    checked+=list(block.glob('*.md'))+list(block.glob('*.py'))+list(block.glob('*.json'))+list(output.glob('*.json'))
    models.append({'id':id,'name':title,'catalog_grid':assembly['catalog_grid_cells'],
        'glb':'../'+id+'/'+id+'.glb','source':'../../Blocks/'+id+'/'+id+'.blend',
        'assembly':'../../Blocks/'+id+'/assembly.json','validation':'../'+id+'/validation.json',
        'sha256':digest,'bytes':size,'instances':report['instances'],'triangles':report['triangles'],
        'logical_muzzles':report['logical_muzzles'],'real_reimport_passed':True})
assert len(models)==6 and len(new_parts)==34
assert len({m['sha256'] for m in models})==6
for path in checked:
    data=path.read_bytes(); assert b'\n' not in data.replace(b'\r\n',b''),'Non-CRLF: '+str(path)
manifest={'schema':'SS3D.weapon-batch/1','project':'SS','style':'ChunkyModular','models':models,
    'new_parts':sorted(new_parts),'reused_parts':sorted(reused),
    'authoring_axes':{'up':'+Z','forward':'-Y','units':'design_unit'},
    'glb_axes':'standard glTF Y-up; logical metadata retains named local source frames',
    'presentation_assets_created':False,'scope':'Final editable models and self-contained GLBs. No game integration.'}
dest=STYLE/'Exports'/'WeaponBatch-6'/'manifest.json'; dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2).replace('\n','\r\n')+'\r\n').encode('utf-8'))
print(json.dumps({'models':len(models),'new_parts':len(new_parts),'reused_parts':sorted(reused),
                  'total_triangles':sum(m['triangles'] for m in models),'status':'passed'},ensure_ascii=False))
