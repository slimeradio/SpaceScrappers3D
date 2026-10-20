import bpy,json,hashlib,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Tools'));from weapon_batch_core import write
out=ROOT/'Scenes/DamageDemo';report=[]
for bid in ['MA-A01','MA-W01']:
    snapshots=[]
    for path in [out/bid/'damage66'/(bid+'-damage66.blend'),out/bid/'destroyed'/(bid+'-destroyed.blend')]:
        bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
        snapshots.append({o.name:([tuple(v.co) for v in o.data.vertices],[tuple(o.matrix_world@v.co) for v in o.data.vertices],tuple(o.scale)) for o in bpy.context.scene.objects if o.type=='MESH'})
    a,b=snapshots;assert a.keys()==b.keys()
    geometry=all(a[k][0]==b[k][0] for k in a);maxdiff=max(abs(x-y) for k in a for v,w in zip(a[k][1],b[k][1]) for x,y in zip(v,w))
    assert geometry and maxdiff<.0001,(bid,maxdiff)
    first={o.name:o.matrix_world.copy() for o in bpy.context.scene.objects if o.type=='MESH'}
    bpy.context.scene.frame_set(19);bpy.context.view_layer.update();assert all(math.isfinite(v) for o in bpy.context.scene.objects for row in o.matrix_world for v in row)
    bpy.context.scene.frame_set(37);bpy.context.view_layer.update();moved=sum((o.matrix_world.translation-first[o.name].translation).length>.01 for o in bpy.context.scene.objects if o.type=='MESH')
    assert moved==len(a)
    report.append({'id':bid,'mesh_count':len(a),'geometry_identical':geometry,'frame1_world_max_error':maxdiff,'moving_parts':moved,'intermediate_pose_finite':True})
write(out/'destruction-validation.json',report);print('DESTRUCTION_VALIDATED',report)
