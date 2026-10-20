import sys,ast,bpy,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT
from mathutils import Vector
h=Path(__file__).with_name('redesign_MA_B01_I01_FG01.py');m=ast.parse(h.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in m.body if isinstance(n,ast.FunctionDef) and n.name=='preview'],type_ignores=[]),str(h),'exec'))
p=ROOT/'Parts'/'MA-EF02-P01';bpy.ops.wm.open_mainfile(filepath=str(p/'MA-EF02-P01.blend'))
preview(p,(0,.35,.49),2.1,450)