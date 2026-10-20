"""Increase only collector spine cap thickness to avoid a coplanar terminal face."""
import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from redesign_RHSS import finish,assemble
from weapon_batch_core import ROOT,Part
pid='MA-H01-R2-P01';folder=ROOT/'Parts'/pid;meta=json.loads((folder/'part.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(folder/(pid+'.blend')))
o=bpy.data.objects['Upper closed manifold']
if max(v.co.z for v in o.data.vertices)<.44:
 for v in o.data.vertices:v.co.z=.37+(v.co.z-.37)*(.16/.12)
o=bpy.data.objects['Collector keel']
if max(v.co.y for v in o.data.vertices)>1.79:
 for v in o.data.vertices:v.co.y*=3.54/3.6
for o in list(bpy.context.scene.objects):
 if o.type=='EMPTY':bpy.data.objects.remove(o,do_unlink=True)
m=Part.__new__(Part);m.pid=pid;m.title=meta['name'];m.version='2.0';m.coll=bpy.data.collections[pid]
finish(m,meta['mounts'])
desc=json.loads((ROOT/'Blocks'/'MA-H01'/'assembly.json').read_text())['notes']
assemble('MA-H01',[('Collector',pid,(0,0,0))]+[(f'Fin-{i}','MA-H01-R2-P02',(0,-1.20+i*.30,.27)) for i in range(9)],desc)
print('INCREMENTAL_H01_FIXED',flush=True)
