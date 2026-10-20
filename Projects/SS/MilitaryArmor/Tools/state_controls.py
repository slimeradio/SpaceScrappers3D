"""Run in Blender Text Editor, then apply_preset('MA-H01', 'closed') or play_clip('MA-D01', 'stop')."""
import bpy

def controller(block):
    if hasattr(block,'keys'):return block
    found=bpy.data.objects.get(block) or bpy.data.objects.get(block+'::'+block)
    if found is None:raise KeyError(block)
    return found

def freeze(block):
    root=controller(block);values={k:root[k] for k in root.keys()}
    if root.animation_data:root.animation_data.action=None
    for k,v in values.items():root[k]=float(v) if isinstance(v,(float,int)) else v
    root.update_tag();bpy.context.view_layer.update();return root

def apply_preset(block,preset):
    root=freeze(block)
    presets={'off':{'power':0,'activity':0},'idle':{'power':1,'activity':0},'working':{'power':1,'activity':1},
             'hot_off':{'power':0,'activity':0,'heat':1},'cold':{'heat':0},'hot':{'heat':1},
             'closed':{'deployment':0},'opened':{'deployment':1},'empty':{'fill':0},'full':{'fill':1}}
    values=presets[preset]
    if not all(k in root for k in values):raise ValueError('Preset is not applicable to this block')
    for k,v in values.items():root[k]=float(v)
    root.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
    return root

def play_clip(block,clip):
    root=freeze(block);bid=root.name.split('::')[0]
    source=bpy.data.actions[bid+'::'+clip];action=source.copy();action.name=bid+'::Playback.'+clip;action.use_fake_user=False
    start,end=action.frame_range;phase=root.get('cycle_turns',0)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if fc.data_path=='["cycle_turns"]':
                        initial=fc.keyframe_points[0].co.y
                        for k in fc.keyframe_points:
                            delta=phase-initial;k.co.y+=delta;k.handle_left.y+=delta;k.handle_right.y+=delta
                    if clip.endswith('loop'):
                        mod=fc.modifiers.new('CYCLES');mode='REPEAT_OFFSET' if fc.data_path=='["cycle_turns"]' else 'REPEAT'
                        mod.mode_before=mode;mod.mode_after=mode
    root.animation_data_create();root.animation_data.action=action;root.animation_data.action_slot=action.slots[0]
    scene=bpy.context.scene;scene.frame_start=int(start);scene.frame_end=int(end);scene.frame_set(int(start))
    return action
