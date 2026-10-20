import bpy,sys,json,math,hashlib,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Scenes/DamageDemo';sys.path.insert(0,str(ROOT/'Tools'))
from weapon_batch_core import write
# Restore original vertex geometry in obsolete destroyed variants while preserving damaged materials.
for folder in ([] if '--resume' in sys.argv else sorted((ROOT/'Parts').glob('*-destroyed'))):
    meta=json.loads((folder/'part.json').read_text(encoding='utf8'));pid=meta['derived_from'];src=ROOT/'Parts'/pid
    bpy.ops.wm.open_mainfile(filepath=str(src/(pid+'.blend')))
    coll=bpy.data.collections.get(pid)
    if coll:coll.name=folder.name
    restored=sum(o.type=='MESH' for o in bpy.context.scene.objects)
    for m in bpy.data.materials:
        if m.use_nodes:
            shader=m.node_tree.nodes.get('Principled BSDF')
            if shader:shader.inputs['Emission Strength'].default_value=0
    base=json.loads((src/'part.json').read_text(encoding='utf8'));meta['bounds_local']=base['bounds_local'];meta['materials']=base['materials'];meta['emission']=[];meta['notes']='Original geometry restored exactly. Superseded by destruction animation. No vertex modifications.'
    write(folder/'part.json',meta);write(folder/'validation.json',{'id':folder.name,'original_geometry_restored':True,'mesh_count':restored})
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(folder.name+'.blend')))

plans={
 'Foundation':((0,0,-.5),(8,5,12),5),
 'AzimuthDrive':((.15,.25,.7),(18,-12,25),3),
 'Capsule':((1.05,.65,1.25),(25,-32,35),2),
 'TripleCradle':((-.7,-.55,.6),(-25,15,-20),3),
 'Accelerator0':((-.8,-1.6,.55),(15,-22,-28),0),
 'Accelerator1':((0,-1.85,.9),(-18,12,8),1),
 'Accelerator2':((.8,-1.6,.6),(22,24,30),2),
 'armor-shell':((.8,.35,1.1),(30,-28,22),0)
}
for bid in ['MA-A01','MA-W01']:
    folder=OUT/bid/'destroyed';bpy.ops.wm.open_mainfile(filepath=str(OUT/bid/'damage66'/(bid+'-damage66.blend')))
    scene=bpy.context.scene;scene.frame_set(1);scene.render.fps=30;scene.frame_start=1;scene.frame_end=37
    meshes=[o for o in scene.objects if o.type=='MESH'];bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);center=(lo+hi)/2;span=max((hi-lo).length,1)
    tracks=[]
    for o in meshes:
        world=o.matrix_world.copy();inst=o.name.split('::')[0];delta,angles,delay=plans.get(inst,((-.6,.8,.9),(20,30,-15),4))
        # Per existing object motion, no mesh cuts, vertex edits or scaling.
        local_center=sum((Vector(v) for v in o.bound_box),Vector())/8
        pivot=world@local_center
        anchor=bpy.data.objects.new('Destruction.'+o.name,None);scene.collection.objects.link(anchor);anchor.location=pivot
        bpy.context.view_layer.update()
        o.parent=anchor;o.matrix_world=world
        bpy.context.view_layer.update()
        radial=pivot-center
        spread=Vector((radial.x,radial.y,abs(radial.z)*.4))*.3
        travel=Vector(delta)*span*.5+spread
        start=1+delay;end=31+delay
        for f,t in [(1,0),(start,0),(end,1),(37,1)]:
            anchor.location=pivot+travel*t;anchor.rotation_euler=tuple(math.radians(a)*t for a in angles)
            anchor.keyframe_insert(data_path='location',frame=f);anchor.keyframe_insert(data_path='rotation_euler',frame=f)
        tracks.append({'object':o.name,'source_instance':inst,'controller':anchor.name,'coordinate_space':'block local; +X right, -Y forward, +Z up','start_frame':start,'end_frame':end,'start_position':list(pivot),'displacement_BU':list(travel),'direction':list(travel.normalized()),'rotation_degrees_xyz':list(angles),'pivot':'existing object bounding-box center','scale_unchanged':True})
    for m in bpy.data.materials:
        if m.use_nodes:
            p=m.node_tree.nodes.get('Principled BSDF')
            if p:p.inputs['Emission Strength'].default_value=0
    spec={'schema':'MilitaryArmor.BlenderAuthoring.DestructionDemo/1','id':bid,'fps':30,'duration_seconds':1.2,'frame_range':[1,37],'loop':False,'geometry_modified':False,'mesh_count':len(meshes),'tracks':tracks,'runtime_contract':False,'end_behavior':'hold separated parts; runtime debris lifetime is unspecified','armor_limitation':'MA-A01 consists of one existing mesh/part; it detaches as one plate, no invented fragments' if bid=='MA-A01' else None}
    # Fixed camera fits all key poses, same camera throughout animation.
    allpts=[]
    for f in [1,19,37]:
        scene.frame_set(f);bpy.context.view_layer.update();allpts.extend(o.matrix_world@Vector(v) for o in meshes for v in o.bound_box)
    lo=Vector([min(p[i] for p in allpts) for i in range(3)]);hi=Vector([max(p[i] for p in allpts) for i in range(3)]);target=(lo+hi)/2;scale=(hi-lo).length*1.05
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
    except Exception:pass
    scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Destruction review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.065,.08,.1,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    bpy.ops.object.camera_add(location=target+Vector((1,-1,1.414)).normalized()*scale*3);cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam
    for delta,power in [((2,-3,5),1700),((-3,-1,3),1000),((1,4,4),1700)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(delta)*span/5);o=bpy.context.object;o.data.energy=power*(span/5)**2;o.data.size=span*.7;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(bid+'-destroyed.blend')))
    write(folder/'destruction.json',spec)
    assembly=json.loads((folder/'assembly.json').read_text(encoding='utf8'));assembly['damage_state']='destruction_animation';assembly['animation']='destruction.json';assembly['geometry_modified']=False
    for i in assembly['instances']:
        i['part_id']=i['part_id'].replace('-destroyed','-damage66');i['source']=os.path.relpath(ROOT/'Parts'/i['part_id']/(i['part_id']+'.blend'),folder).replace('\\','/')
    write(folder/'assembly.json',assembly)
    for f in [1,13,25,37]:
        scene.frame_set(f);scene.render.filepath=str(folder/('frame-%02d.png'%f));bpy.ops.render.render(write_still=True)
    print('ANIMATION_COMPLETE',bid,flush=True)
