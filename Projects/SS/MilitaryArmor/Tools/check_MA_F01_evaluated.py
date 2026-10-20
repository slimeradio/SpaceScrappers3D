import bpy,json
from pathlib import Path
root=Path('D:/Codex/SpaceScrappers3D/Projects/SS/MilitaryArmor')
for pid in ['MA-F01-P01','MA-F01-P02','MA-F01-P03','MA-F01-P04','MA-P06']:
 bpy.ops.wm.open_mainfile(filepath=str(root/'Parts'/pid/(pid+'.blend')))
 issues=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();bad=sum(t.area<1e-10 for t in m.loop_triangles)
  if bad:issues.append((o.name,bad))
  e.to_mesh_clear()
 print('EVALUATED',pid,issues,flush=True)
