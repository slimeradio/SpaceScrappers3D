import bpy, json, math
from pathlib import Path
root=Path(__file__).resolve().parents[1];block=root/'Blocks/MA-T01'
counts={};facets={}
for i in range(1,9):
    pid=f'MA-P{i:02}'
    bpy.ops.wm.open_mainfile(filepath=str(root/'Parts'/pid/f'{pid}.blend'))
    objs=bpy.data.collections[pid].objects
    counts[pid]=sum(o.type in ('MESH','FONT','CURVE') for o in objs)
    facets[pid]=sum(o.get('shape_revision')=='1.2 / faceted' for o in objs)
bpy.ops.wm.open_mainfile(filepath=str(block/'MA-T01.blend'))
scene=bpy.context.scene;angles=[]
for f in range(1,141):
    scene.frame_set(f);angles.append(-math.degrees(bpy.data.objects['Elevation'].rotation_euler.x))
scene.frame_set(1)
d=json.loads((block/'validation.json').read_text(encoding='utf8'))
d.update({'revision':'1.2','reopened_in_Blender':True,'part_renderable_counts':counts,'faceted_mesh_counts':facets,'resolved_instances':sum(o.instance_type=='COLLECTION' and o.instance_collection is not None for o in scene.objects),'external_libraries':[x.filepath for x in bpy.data.libraries],'file_images':[x.filepath for x in bpy.data.images if x.source=='FILE' and x.filepath],'elevation_sampled_degrees':[min(angles),max(angles)]})
d['source_checks_passed']=not d['missing_dependencies'] and not d['external_libraries'] and not d['file_images'] and d['resolved_instances']==12 and min(angles)>=-8.01 and max(angles)<=25.01 and facets['MA-P03']>0 and facets['MA-P01']>0
(block/'validation.json').write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf8'))
assert d['source_checks_passed'];print(json.dumps(d,indent=2))
