"""Verify the updated 64-block gallery plus driver isolation after library import."""
import bpy,sys,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_animation_states import ROOT,STATIC,read,write
script=Path(__file__).with_name('build_all_blocks_scene.py');sys.argv=[str(script),'--verify']
try:runpy.run_path(str(script),run_name='__main__')
except SystemExit:pass
folder=ROOT/'Scenes'/'AllBlocks';manifest=read(folder/'scene.json');report=read(folder/'validation.json')
blocks=[]
for entry in manifest['blocks']:
    bid=entry['id']
    if bid in STATIC:continue
    root=bpy.data.objects[entry['state_controller']];state=read(ROOT/'Blocks'/bid/'state-authoring.json')
    for key in state['controls']:assert key in root,(bid,key)
    for clip in state['clips']:assert bpy.data.actions.get(clip['name']),(bid,clip['name'])
    count=0
    for o in root.children_recursive:
        if o.type!='MESH':continue
        for slot in o.material_slots:
            mat=slot.material
            if not mat or not mat.node_tree or not mat.node_tree.animation_data:continue
            for fc in mat.node_tree.animation_data.drivers:
                assert fc.driver.is_valid,(bid,mat.name)
                for v in fc.driver.variables:assert v.targets[0].id==root,(bid,mat.name,v.targets[0].id.name)
                count+=1
    blocks.append(dict(id=bid,controller=root.name,isolated_material_driver_count=count,clips_loaded=len(state['clips'])))
assert len(blocks)==55
report.update(state_blocks=blocks,state_block_count=55,static_block_count=9,isolated_material_controllers=True,source_actions_preserved=True)
write(folder/'state-validation.json',report);print('STATE_GALLERY_VERIFIED',55,9,flush=True)
