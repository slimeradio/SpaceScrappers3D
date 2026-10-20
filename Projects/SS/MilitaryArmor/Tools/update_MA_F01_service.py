from pathlib import Path
import json
p=Path(__file__).resolve().parent/'build_MA_F01.py'
exec(compile(p.read_text().split("write(FOLDER/'composition-plan.md'")[0],str(p),'exec'))
meta=json.loads((FOLDER/'assembly.json').read_text())
a=Assembly(BID,meta['catalog_id'],meta['catalog_grid'],meta['title'])
for i in meta['instances']:
 a.instance(i['id'],'MA-R01-P05' if i['part_id']=='MA-P06' else i['part_id'],loc=i['translation'],rot=i['rotation_euler_xyz'])
meta['instances']=a.instances
meta['notes']+=' Service cartridge uses compatible MA-R01-P05 v1.0, an explicitly validated MA-P06 bevel-corrected variant; original unchanged.'
write(FOLDER/'assembly.json',meta)
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.50),5.3)
print('MA_F01_SERVICE_UPDATED_NO_OTHER_PART_REBUILD')
