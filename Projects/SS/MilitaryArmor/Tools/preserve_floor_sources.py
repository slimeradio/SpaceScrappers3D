"""Place the original authored scene under ModelFit, preserving all actions/drivers."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from floor_fit import ROOT,BACKUP,read,write
sys.path.insert(0,str(ROOT.parents[2]/'Tools/SpriteBake'))
import bpy
import blender_worker as bw

def channels():
    result={}
    for collection,label in ((bpy.data.objects,'object'),(bpy.data.materials,'material'),(bpy.data.node_groups,'node_group')):
        for owner in collection:
            data=owner.animation_data
            if data:
                result[label+'/'+owner.name]=dict(action=data.action.name if data.action else None,drivers=[(d.data_path,d.array_index,d.driver.expression) for d in data.drivers])
            tree=getattr(owner,'node_tree',None)
            if tree and tree.animation_data:
                data=tree.animation_data
                result[label+'/'+owner.name+'/shader']=dict(action=data.action.name if data.action else None,drivers=[(d.data_path,d.array_index,d.driver.expression) for d in data.drivers])
    return result

profile=read(ROOT/'SpriteBake/profile.json');proofs=[]
for bid,spec in profile['blocks'].items():
    a=read(ROOT/spec['assembly']);original=read(BACKUP/spec['assembly']);fit=a['floor_fit']
    source=ROOT/'Versions/FloorFitBefore'/spec['source']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    before=channels();frame_range=[bpy.context.scene.frame_start,bpy.context.scene.frame_end]
    roots=[n['id'] for n in original.get('nodes',[]) if n.get('parent') is None]
    if not roots:roots=[bid]
    assert all(name in bpy.data.objects for name in roots),(bid,'missing authored root',roots)
    assert 'ModelFit' not in bpy.data.objects
    wrapper=bpy.data.objects.new('ModelFit',None);bpy.context.scene.collection.objects.link(wrapper)
    wrapper.location=fit['translation'];s=fit['uniform_scale'];wrapper.scale=(s,s,s)
    for name in roots:
        obj=bpy.data.objects[name];assert obj.parent is None,(bid,name)
        obj.parent=wrapper
    floor=bpy.data.objects.new('Floor',None);bpy.context.scene.collection.objects.link(floor)
    fid=fit['floor'];loaded=bw.load_objects(ROOT/'Parts'/fid/(fid+'.blend'));loaded_set=set(loaded)
    for obj in loaded:
        if obj.parent not in loaded_set:obj.parent=floor
    after=channels();assert all(after.get(name)==value for name,value in before.items()),bid
    assert frame_range==[bpy.context.scene.frame_start,bpy.context.scene.frame_end]
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/spec['source']))
    # Reopening is part of the check; a saved file alone does not prove drivers survived.
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']),load_ui=False,use_scripts=False)
    reopened=channels();assert all(reopened.get(name)==value for name,value in before.items()),bid
    proofs.append(dict(id=bid,animation_owners=len(before),preserved=True,reopened=True,frame_range=frame_range))
    print('AUTHORED_SOURCE_PRESERVED',bid,len(before),flush=True)
write(ROOT/'floor-source-preservation.json',dict(passed=True,blocks=proofs))
print('ALL_AUTHORED_SOURCES_PRESERVED',len(proofs),flush=True)
