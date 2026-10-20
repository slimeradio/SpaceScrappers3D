"""Render current states using fixed framing; never save over the authored Blender sources."""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_animation_states import ROOT,STATIC,read,write
from verify_animation_states import set_values
OUT=ROOT/'Exports'/'StatePreviews';OUT.mkdir(parents=True,exist_ok=True)
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
gif_blocks={'MA-H01','MA-F01','MA-FF01','MA-D02'}
previous=read(OUT/'render-manifest.json')['blocks'] if selected and (OUT/'render-manifest.json').exists() else []
results=[r for r in previous if r['id'] not in selected]
for folder in sorted((ROOT/'Blocks').iterdir()):
    bid=folder.name
    if not folder.is_dir() or bid in STATIC or (selected and bid not in selected):continue
    bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')));scene=bpy.context.scene;s=read(folder/'state-authoring.json');root=bpy.data.objects[bid]
    default={k:d['default'] for k,d in s['controls'].items()}
    off=dict(power=0,activity=0);working=dict(power=1,activity=1)
    if 'heat' in root:off['heat']=0;working['heat']=.75
    if 'fill' in root:off['fill']=0;working['fill']=1
    if 'cycle_turns' in root:working['cycle_turns']=.1875
    if bid=='MA-E02':working.update(thrust_0=1,thrust_1=.5,thrust_2=.15)
    poses=[('off',off),('working',working)]
    if 'deployment' in root:
        poses=[('closed-cold',dict(deployment=0,heat=0,power=1)),('open-cold',dict(deployment=1,heat=0,power=1)),('open-warm',dict(deployment=1,heat=.35,power=1)),('open-hot',dict(deployment=1,heat=.85,power=1)),('closed-hot-off',dict(deployment=0,heat=.85,power=0))]
    # One framing encloses all poses so the camera does not move when the rig unfolds.
    pts=[]
    for name,values in poses:
        set_values(root,**default);set_values(root,**values)
        for o in scene.objects:
            if o.type=='MESH':pts.extend(o.matrix_world@Vector(v) for v in o.bound_box)
    lo=Vector(tuple(min(v[i] for v in pts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in pts) for i in range(3)));target=(lo+hi)*.5;scale=max(hi-lo)*1.5
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
    scene.render.resolution_x=360;scene.render.resolution_y=360;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    world=bpy.data.worlds.new('State review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.035,.05,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
    for offlight,power in [((2,-5,8),1100),((-4,-1,5),850),((3,5,6),1300)]:
        bpy.ops.object.light_add(type='AREA',location=target+Vector(offlight));o=bpy.context.object;o.data.energy=power;o.data.size=5;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam
    dest=OUT/bid;dest.mkdir(exist_ok=True);names=[]
    for name,values in poses:
        set_values(root,**default);set_values(root,**values)
        for view,offset in [('top',(0,0,12)),('perspective',(7,-9,8))]:
            cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
            path=dest/(name+'-'+view+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);names.append(path.relative_to(OUT).as_posix())
    if bid in gif_blocks:
        # Fixed perspective and an exact number of full turns make cyclic work previews seamless.
        cam.location=target+Vector((7,-9,8));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        frames=dest/'Frames';frames.mkdir(exist_ok=True)
        for j in range(16):
            t=j/16;set_values(root,**default);set_values(root,power=1,activity=1)
            if 'deployment' in root:set_values(root,deployment=(1-math.cos(t*math.tau))/2,heat=.8)
            elif 'cycle_turns' in root:set_values(root,cycle_turns=t)
            scene.render.filepath=str(frames/f'{j:03}.png');bpy.ops.render.render(write_still=True)
    results.append(dict(id=bid,images=names));write(OUT/'render-progress.json',dict(blocks=results))
    print('STATE_PREVIEWS',bid,flush=True)
write(OUT/'render-manifest.json',dict(blocks=results,sources_modified=False,glb_generated=False,framing='fixed across states and animation frames'))
