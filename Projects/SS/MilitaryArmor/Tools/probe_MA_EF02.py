import bpy,bmesh,json
from pathlib import Path
r=Path('D:/Codex/SpaceScrappers3D/Projects/SS/MilitaryArmor')
for pid in ['MA-E01-P03','MA-E01-P05']:
 bpy.ops.wm.open_mainfile(filepath=str(r/'Parts'/pid/(pid+'.blend')))
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);print(pid,o.name,'nonmanifold',sum(not e.is_manifold for e in bm.edges),'normals',all(e.is_contiguous for e in bm.edges),'vol',bm.calc_volume(signed=True));bm.free()