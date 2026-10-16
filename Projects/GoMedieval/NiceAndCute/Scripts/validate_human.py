"""Reopen source, validate all animation frames, render small animation proof."""
import bpy, json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blocks/GM-Human/GM-Human.blend'))
s=bpy.context.scene
rigs=[o for o in s.objects if o.type=='ARMATURE']
assert len(rigs)==4
report={'reopened':True,'blender':bpy.app.version_string,'rigs':len(rigs),'fps':s.render.fps,'frames_checked':132,'clips':{},'textures':'Procedural solid materials; no external files','engine_acceptance':'Not performed'}
for rig in rigs:
    assert len(rig.pose.bones)==15
    assert len(rig.animation_data.nla_tracks)==3
    report['clips'][rig.name]=[{'name':t.name,'start':int(t.strips[0].frame_start),'end':int(t.strips[0].frame_end)} for t in rig.animation_data.nla_tracks]
    for f in range(1,133):
        s.frame_set(f)
        for p in rig.pose.bones: assert all(math.isfinite(v) for row in p.matrix for v in row)
    s.frame_set(1); first=[p.matrix.copy() for p in rig.pose.bones]
    s.frame_set(32); assert max(abs(a-b) for old,p in zip(first,rig.pose.bones) for ro,rn in zip(old,p.matrix) for a,b in zip(ro,rn))<1e-5
s.frame_set(66)
report['archery_hand_positions']={r.name:{side:list(r.pose.bones['fore.'+side].tail) for side in ['L','R']} for r in rigs}
# A portable contact strip makes the motion verifiable without any game integration.
s.render.resolution_x=760; s.render.resolution_y=456; s.cycles.samples=8
frames=ROOT/'Previews/Frames'; frames.mkdir(exist_ok=True)
for f in list(range(1,33,3))+list(range(41,89,3))+list(range(97,133,3)):
    s.frame_set(f); s.render.filepath=str(frames/f'{f:03}.png'); bpy.ops.render.render(write_still=True)
(ROOT/'Blocks/GM-Human/validation.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode())
print('VALIDATION_OK')
