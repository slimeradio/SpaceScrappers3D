import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_MA_R01 import inspect
from weapon_batch_core import ROOT
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts/MA-P06/MA-P06.blend'))
print(inspect())
d=bpy.context.evaluated_depsgraph_get()
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(d);m=e.to_mesh();m.calc_loop_triangles();bad=[t.area for t in m.loop_triangles if t.area<1e-11]
 if bad:print(o.name,len(bad),[(v.name,v.type,getattr(v,'width',None)) for v in o.modifiers])
 e.to_mesh_clear()