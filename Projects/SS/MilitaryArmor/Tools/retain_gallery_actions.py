"""Restore and retain unassigned state Actions without reimporting any geometry."""
import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_animation_states import ROOT,STATIC,read
path=ROOT/'Scenes'/'AllBlocks'/'AllBlocks.blend';bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.preferences.filepaths.save_version=0
count=0
for p in sorted((ROOT/'Blocks').glob('*/state-authoring.json')):
    if p.parent.name in STATIC:continue
    state=read(p);names=[c['name'] for c in state['clips']];missing=[n for n in names if n not in bpy.data.actions]
    if missing:
        with bpy.data.libraries.load(str(p.parent/(p.parent.name+'.blend')),link=False) as (src,dst):dst.actions=missing
    for name in names:bpy.data.actions[name].use_fake_user=True;count+=1
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True);print('GALLERY_ACTIONS_RETAINED',count,flush=True)
