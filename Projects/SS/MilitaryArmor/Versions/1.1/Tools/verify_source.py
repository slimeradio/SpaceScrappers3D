import bpy, json, math
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parents[1]
block=root/'Blocks/MA-T01'
bpy.ops.wm.open_mainfile(filepath=str(root/'Parts/MA-P03/MA-P03.blend'))
for o in bpy.data.objects:
    if o.type=='FONT' and o.data.body=='ARMORED SYSTEMS':o.location.x=.95
bpy.ops.wm.save_as_mainfile(filepath=str(root/'Parts/MA-P03/MA-P03.blend'))
bpy.ops.wm.open_mainfile(filepath=str(block/'MA-T01.blend'))
for o in bpy.data.objects:
    if o.type=='FONT' and o.data.body=='ARMORED SYSTEMS':o.location.x=.95
scene=bpy.context.scene
poses=[]
for frame in range(1,141):
    scene.frame_set(frame)
    poses.append(-math.degrees(bpy.data.objects['Elevation'].rotation_euler.x))
scene.frame_set(1)
data=json.loads((block/'validation.json').read_text(encoding='utf-8'))
data['reopened_in_Blender']=True
data['external_libraries']=[x.filepath for x in bpy.data.libraries]
data['file_images']=[x.filepath for x in bpy.data.images if x.source=='FILE' and x.filepath]
data['elevation_sampled_degrees']=[min(poses),max(poses)]
data['resolved_instances']=sum(1 for o in scene.objects if o.instance_type=='COLLECTION' and o.instance_collection)
data['source_checks_passed']=(not data['missing_dependencies'] and not data['external_libraries'] and not data['file_images'] and min(poses)>=-8.01 and max(poses)<=25.01 and data['resolved_instances']==12)
(block/'validation.json').write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8'))
print(json.dumps(data,indent=2))
assert data['source_checks_passed']
bpy.ops.wm.save_as_mainfile(filepath=str(block/'MA-T01.blend'))
cam=scene.camera
scene.render.resolution_x=800;scene.render.resolution_y=800;scene.cycles.samples=16
cam.location=(0,-.85,14)
cam.rotation_euler=(Vector((0,-.85,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=9.2
scene.render.filepath=str(block/'Previews/MA-T01-top.png')
bpy.ops.render.render(write_still=True)
for frame,name,view in [(1,'rear',(-8,8,6)),(35,'elevation-max',(9,-10,7)),(70,'elevation-min',(9,-10,7)),(105,'combined',(9,-10,7))]:
    scene.frame_set(frame);cam.location=view
    cam.rotation_euler=(Vector((0,0,1.6))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=9
    scene.render.filepath=str(block/f'Previews/MA-T01-{name}.png')
    bpy.ops.render.render(write_still=True)
