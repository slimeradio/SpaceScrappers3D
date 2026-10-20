import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from weapon_batch_core import ROOT,write
pid='MA-F01-P02';folder=ROOT/'Parts'/pid
meta=json.loads((folder/'part.json').read_text());service=next(m for m in meta['mounts'] if m['id']=='service');service['compatibility'].append('MilitaryArmor.service-cartridge.v1')
meta['attachment_areas'].append({'id':'service-plane','role':'accessory','parent':pid,'shape':'plane','size':[.74,.60],'position':service['position'],'forward':service['forward'],'up':service['up'],'restrictions':'Full socket pose alignment; unit scale','compatibility':service['compatibility']})
write(folder/'part.json',meta)
bpy.ops.wm.open_mainfile(filepath=str(folder/(pid+'.blend')));bpy.context.preferences.filepaths.save_version=0;bpy.data.objects['socket.service']['compatibility']='MilitaryArmor.service-cartridge.v1';bpy.ops.wm.save_as_mainfile(filepath=str(folder/(pid+'.blend')))
folder=ROOT/'Blocks'/'MA-F01';bpy.ops.wm.open_mainfile(filepath=str(folder/'MA-F01.blend'));bpy.context.preferences.filepaths.save_version=0
for label in ['L','R']:bpy.data.objects['Cassette.'+label+'::socket.service']['compatibility']='MilitaryArmor.service-cartridge.v1'
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'MA-F01.blend'))
