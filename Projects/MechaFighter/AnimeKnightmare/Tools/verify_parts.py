import bpy, bmesh, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
names=set()
for p in (root/'Blocks').glob('*/assembly.json'):
    names.update(i['part'] for i in json.loads(p.read_text(encoding='utf-8'))['instances'])
results={}
for name in sorted(names):
    p=root/'Parts'/name/(name+'.blend')
    with bpy.data.libraries.load(str(p),link=False) as (src,dst): dst.collections=[name]
    c=dst.collections[0]; errors=[]
    for o in c.objects:
        if o.type!='MESH': continue
        bm=bmesh.new(); bm.from_mesh(o.data)
        if any(not e.is_manifold for e in bm.edges): errors.append(o.name+': nonmanifold')
        if any(f.calc_area()<1e-9 for f in bm.faces): errors.append(o.name+': degenerate face')
        if bm.calc_volume(signed=True)<=0: errors.append(o.name+': inverted volume')
        if not o.data.materials: errors.append(o.name+': no material')
        bm.free()
    results[name]={'reopened_library':True,'objects':len(c.objects),'errors':errors}
    if errors: raise RuntimeError(str(errors))
(root/'part-reopen-validation.json').write_bytes((json.dumps(results,indent=2)+'\n').replace('\n','\r\n').encode())
print('PART_REOPEN_OK',len(results))
