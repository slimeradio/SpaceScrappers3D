"""Rebase only reactor radial foot geometry, then refresh only its dependent assembly."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from redesign_RHSS import finish,assemble
from weapon_batch_core import ROOT,Part
pid='MA-R01-R2-P01';folder=ROOT/'Parts'/pid;meta=json.loads((folder/'part.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(folder/(pid+'.blend')))
for o in list(bpy.context.scene.objects):
 if o.type!='MESH':continue
 if o.name.startswith('Radial outer shield foot'):
  # Original generator used world-baked panel vertices with local rotation.
  # Rebase only if still at the old zero origin, preserving editable faces.
  if o.location.length<1e-6:
   center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
   for v in o.data.vertices:v.co-=center
   o.location=center
# Existing socket empties are rebuilt from the unchanged declared socket data.
for o in list(bpy.context.scene.objects):
 if o.type=='EMPTY':bpy.data.objects.remove(o,do_unlink=True)
m=Part.__new__(Part);m.pid=pid;m.title=meta['name'];m.version='2.0';m.coll=bpy.data.collections[pid]
finish(m,meta['mounts'])
desc=json.loads((ROOT/'Blocks'/'MA-R01'/'assembly.json').read_text())['notes']
assemble('MA-R01',[('Annular-shield',pid,(0,0,0)),('Containment-vessel','MA-R01-R2-P02',(0,0,.28))],desc)
print('INCREMENTAL_REACTOR_FIXED',flush=True)
