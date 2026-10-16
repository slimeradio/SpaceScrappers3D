"""Update sword orientation only; leave geometry and the other clips intact."""
import bpy, math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'Blocks/GM-Human/GM-Human.blend'))
scene=bpy.context.scene
for rig in [o for o in scene.objects if o.type=='ARMATURE']:
    for track in rig.animation_data.nla_tracks: track.mute=True
    action=next(t.strips[0].action for t in rig.animation_data.nla_tracks if t.name=='Sword_Attack')
    rig.animation_data.action=action
    for f in range(97,133):
        scene.frame_set(f)
        p=rig.pose.bones['sword']; p.rotation_euler.x=4*math.sin(math.pi*(f-97)/35)**2
        p.keyframe_insert(data_path='rotation_euler',frame=f,group=p.name)
    rig.animation_data.action=None
    for track in rig.animation_data.nla_tracks: track.mute=False
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
scene.frame_set(114); scene.render.filepath=str(root/'Previews/sword_strike.png'); bpy.ops.render.render(write_still=True)
