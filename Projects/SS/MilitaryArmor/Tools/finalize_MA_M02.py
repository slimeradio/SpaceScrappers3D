import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from weapon_batch_core import ROOT
pid='MA-M02-P03';pf=ROOT/'Parts'/pid
bpy.ops.wm.open_mainfile(filepath=str(pf/(pid+'.blend')))
meta=json.loads((pf/'part.json').read_text());point=meta['functional_points'][0]
if point['node'] not in bpy.data.objects:
 o=bpy.data.objects.new(point['node'],None);bpy.data.collections[pid].objects.link(o);o.location=point['position'];o.empty_display_size=.08;o['functional_point_id']=point['id'];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(pf/(pid+'.blend')))
bf=ROOT/'Blocks'/'MA-M02';bpy.ops.wm.open_mainfile(filepath=str(bf/'MA-M02.blend'))
if 'Aperture::'+point['node'] not in bpy.data.objects:
 o=bpy.data.objects.new('Aperture::'+point['node'],None);bpy.context.scene.collection.objects.link(o);o.parent=bpy.data.objects['Aperture'];o.location=point['position'];o.empty_display_size=.08;o['functional_point_id']=point['id'];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(bf/'MA-M02.blend'))
print('MA_M02_FUNCTIONAL_NODE_SAVED')
