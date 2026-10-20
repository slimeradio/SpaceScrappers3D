from pathlib import Path
import bpy
source=Path(__file__).with_name('build_MA_D01.py').read_text(encoding='utf-8-sig')
exec(source.split("p=Part('MA-D01-P01'")[0])
folder=ROOT/'Parts'/'MA-D01-P03'
bpy.ops.wm.open_mainfile(filepath=str(folder/'MA-D01-P03.blend'))
p=object.__new__(Part);p.pid='MA-D01-P03';p.title='Tapered three-flute mechanical cutting head';p.version='1.0';p.coll=bpy.data.collections[p.pid];p.mats={m.name:m for m in bpy.data.materials}
if 'Rear torque coupling' not in bpy.data.objects:p.cyl('Rear torque coupling',(0,.16,0),.246,.36,'Titanium','Y',32)
for o in list(p.coll.objects):
 if o.type=='EMPTY':bpy.data.objects.remove(o,do_unlink=True)
finish(p,[socket('root',(0,0,0),'cutter')],[dict(id='tool-axis',role='authoring-tool-axis-only',parent=None,position=[0,-1.69,0],direction=[0,-1,0],up=[0,0,1],coordinate_space='part-local',gameplay_contract=False)])
exec('# Dependency gate'+source.split('# Dependency gate',1)[1])
