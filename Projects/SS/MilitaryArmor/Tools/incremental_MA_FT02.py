import sys,ast,json
from pathlib import Path
path=Path(__file__).with_name('build_MA_I02_MA_FT02.py')
sys.path.insert(0,str(path.parent))
# Definitions/imports only. Never execute build entry points.
tree=ast.parse(path.read_text(encoding='utf8'))
body=[]
for n in tree.body:
 if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef)):body.append(n)
 elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and (getattr(n.value.func,'id','')=='exec' or isinstance(n.value.func,ast.Attribute)):body.append(n)
 elif isinstance(n,ast.Assign) and any(getattr(t,'id','') in ['helper','node'] for t in n.targets):body.append(n)
exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'))
pid='MA-FT02-P01';folder=ROOT/'Parts'/pid;d=json.loads((folder/'part.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(folder/d['source']))
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Narrow longitudinal tie'):
  for v in o.data.vertices:v.co.y=-1.60 if v.co.y<0 else 1.30
  o.data.update()
for o in list(bpy.data.objects):
 if o.type=='EMPTY' and o.name.startswith('socket.'):bpy.data.objects.remove(o,do_unlink=True)
p=Part.__new__(Part);p.pid=pid;p.title=d['name'];p.version=d['version'];p.coll=bpy.data.collections[pid]
finish(p,d['mounts'])
print('Incremental tie extension, source + gate + previews done.')