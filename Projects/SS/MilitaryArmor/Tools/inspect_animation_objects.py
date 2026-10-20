import bpy,json
from pathlib import Path
r=Path(r'D:/Codex/SpaceScrappers3D/Projects/SS/MilitaryArmor')
ids=['MA-FG01-R2-P02','MA-FG01-R2-P03','MA-FF01-P02','MA-FF01-P03','MA-D01-P03','MA-HS01-R2-P01','MA-FT01-P02','MA-B01-R2-P02']
rows={}
for pid in ids:
 p=r/'Parts'/pid/(pid+'.blend')
 if not p.exists():continue
 bpy.ops.wm.open_mainfile(filepath=str(p))
 rows[pid]=[{'name':o.name,'type':o.type,'loc':list(o.location),'dim':list(o.dimensions),'materials':[s.material.name for s in o.material_slots if s.material]} for o in bpy.context.scene.objects]
(r/'Tools'/'animation-object-inspection.json').write_text(json.dumps(rows,indent=2),encoding='utf8',newline='\r\n')