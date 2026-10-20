import bpy, json, math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];block=root/'Blocks/MA-T01'

def write(p,d):p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf8'))

def adjust():
    for o in bpy.data.objects:
        if o.get('detail_seating_revision')==1:continue
        if o.name.startswith('Flank recessed fastener'):o.location.x+=math.copysign(.04,o.location.x)
        if o.name.startswith('Armor weld bead'):
            for s in o.data.splines:
                for p in s.bezier_points:
                    shift=math.copysign(.03,p.co.x);p.co.x+=shift;p.handle_left.x+=shift;p.handle_right.x+=shift
        if o.type=='FONT' and o.data.body=='03':o.location.y=-.60
        o['detail_seating_revision']=1
    bpy.context.view_layer.update()

counts={}
for i in range(1,9):
    pid=f'MA-P{i:02}';folder=root/'Parts'/pid
    bpy.ops.wm.open_mainfile(filepath=str(folder/f'{pid}.blend'))
    if i==3:adjust()
    geometry=bpy.data.collections[pid]
    data=json.loads((folder/'part.json').read_text(encoding='utf8'))
    renderables=[o for o in geometry.objects if o.type in ('MESH','FONT','CURVE','CURVE')]
    counts[pid]=len(renderables)
    for m in data['materials']:
        m['surfaces']=[o.name for o in renderables if any(slot and slot.name==m['id'] for slot in o.data.materials)]
    pts=[o.matrix_world@Vector(c) for o in renderables if o.type=='MESH' for c in o.bound_box]
    data['bounds_local']={'min':[min(p[j] for p in pts) for j in range(3)],'max':[max(p[j] for p in pts) for j in range(3)]}
    data['geometry_objects']=len(renderables);write(folder/'part.json',data)
    if i==3:
        bpy.ops.wm.save_as_mainfile(filepath=str(folder/f'{pid}.blend'))
        bpy.context.scene.render.filepath=str(folder/'Previews'/f'{pid}.png');bpy.ops.render.render(write_still=True)

bpy.ops.wm.open_mainfile(filepath=str(block/'MA-T01.blend'));adjust();scene=bpy.context.scene
elev=[]
for f in range(1,141):scene.frame_set(f);elev.append(-math.degrees(bpy.data.objects['Elevation'].rotation_euler.x))
scene.frame_set(1)
data=json.loads((block/'validation.json').read_text(encoding='utf8'))
data.update({'reopened_in_Blender':True,'revision':'1.1','part_renderable_counts':counts,'external_libraries':[x.filepath for x in bpy.data.libraries],'file_images':[x.filepath for x in bpy.data.images if x.source=='FILE' and x.filepath],'elevation_sampled_degrees':[min(elev),max(elev)],'resolved_instances':sum(o.instance_type=='COLLECTION' and o.instance_collection is not None for o in scene.objects)})
data['source_checks_passed']=(not data['missing_dependencies'] and not data['external_libraries'] and not data['file_images'] and min(elev)>=-8.01 and max(elev)<=25.01 and data['resolved_instances']==12)
write(block/'validation.json',data);assert data['source_checks_passed']
bpy.ops.wm.save_as_mainfile(filepath=str(block/'MA-T01.blend'))
cam=scene.camera
for frame,name,view,target,scale,res in [(1,'hero',(8,-11,8),(0,-.55,1.65),9,1100),(1,'top',(0,-.85,14),(0,-.85,0),9.2,800),(1,'rear',(-8,8,6),(0,0,1.6),9,800),(35,'elevation-max',(9,-10,7),(0,0,1.6),9,800),(70,'elevation-min',(9,-10,7),(0,0,1.6),9,800),(105,'combined',(9,-10,7),(0,0,1.6),9,800)]:
    scene.frame_set(frame);cam.location=view;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.resolution_x=res;scene.render.resolution_y=res;scene.cycles.samples=24 if name=='hero' else 16
    scene.render.filepath=str(block/f'Previews/MA-T01-{name}.png');bpy.ops.render.render(write_still=True)
print('DETAIL_VERIFIED',json.dumps(data),flush=True)
