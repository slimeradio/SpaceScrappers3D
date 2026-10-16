"""Incremental authored accent update; reuse all unmodified part libraries.

MF_PARTS selects existing libraries receiving signature details.
MF_ONLY selects affected assemblies. Empty MF_PARTS rebuilds assemblies only.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'Tools'/'refine.py').read_text(encoding='utf-8')
exec(source.split('# Preserve unchanged weapon')[0])
checks=json.loads((ROOT/'part-validation-v2.json').read_text(encoding='utf-8'))
selected=set(filter(None,os.getenv('MF_PARTS','').split(',')))
names=['Sword','Cannon','Thruster','Claw','Shield','Wing']+[kind+'_'+v for v in ['A','K','O'] for kind in ['Core','Head','Shoulder','Arm','Leg','Skirt']]
for name in names:
    with bpy.data.libraries.load(str(ROOT/'Parts'/name/(name+'.blend')),link=False) as (src,dst): dst.collections=[name]
    parts[name]=dst.collections[0]
    if name in selected:
        current=parts[name]
        specialize(name[-1],name.split('_')[0]); complete(name)
write(ROOT/'part-validation-v2.json',checks)
exec(source[source.index('def put(part,'):])
