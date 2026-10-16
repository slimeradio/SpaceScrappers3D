"""Portable Blender source builder. Run from repository root using Blender --background --python."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.collections):
    if d.name != 'Collection': bpy.data.collections.remove(d)
scene = bpy.context.scene
scene.unit_settings.system='METRIC'; scene.render.fps=24
scene.render.engine='CYCLES'; scene.cycles.samples=24
scene.render.resolution_x=1500; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.world.color=(0.22,0.22,0.22)
scene.view_settings.view_transform='AgX'
M={}
def mat(n,c,metal=0):
    m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=.65; p.inputs['Metallic'].default_value=metal
    M[n]=m; return m
for n,c in {'Skin':(.88,.53,.32),'Blush':(1,.25,.24),'Ink':(.045,.035,.075),'Cream':(1,.86,.57),'Hair':(.18,.065,.03),'Mint':(.1,.72,.48),'Coral':(.98,.20,.25),'Lavender':(.52,.28,.9),'Sun':(1,.62,.045),'Teal':(.025,.28,.30),'Plum':(.29,.07,.27),'Blue':(.12,.23,.55),'Leather':(.30,.13,.065),'Wood':(.5,.23,.085),'Gold':(1,.65,.12),'Steel':(.53,.77,.88),'White':(1,.96,.84)}.items(): mat(n,c,.5 if n in ['Gold','Steel'] else 0)
assets=[]; checks=[]; coll=None
def finish(o,n,m,bone=None):
    o.name=n; o.data.materials.append(M[m])
    for p in o.data.polygons: p.use_smooth=True
    for c in list(o.users_collection): c.objects.unlink(o)
    coll.objects.link(o)
    if o.type=='MESH':
        import bmesh
        bm=bmesh.new(); bm.from_mesh(o.data)
        bad=sum(1 for f in bm.faces if f.calc_area()<1e-10); boundary=sum(1 for e in bm.edges if not e.is_manifold)
        bm.free(); assert bad==0,(n,'degenerate'); assert boundary==0,(n,'open mesh')
        checks.append({'part':n,'vertices':len(o.data.vertices),'degenerate_faces':bad,'nonmanifold_edges':boundary})
    assets.append((o,bone)); return o
def ball(n,loc,scale,m,b=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc); o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,n,m,b)
def box(n,loc,scale,m,b=None,bev=.06):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('Soft tailored edges','BEVEL'); mod.width=bev; mod.segments=3
    o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return finish(o,n,m,b)
def rod(n,a,b,r,m,bone=None):
    mid=(Vector(a)+Vector(b))/2; bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=(Vector(b)-Vector(a)).length,location=mid)
    o=bpy.context.object; o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler()
    mod=o.modifiers.new('Rounded ends','BEVEL'); mod.width=r*.35; mod.segments=3
    return finish(o,n,m,bone)
def line(n,pts,r,m,bone=None):
    # Closed solid beads/segments retain editable geometry and robust manifold checks.
    return [rod(n+str(i),a,b,r,m,bone) for i,(a,b) in enumerate(zip(pts,pts[1:]))]

variants=[('Mint_Ranger','Mint','Teal','hood'),('Coral_Guard','Coral','Plum','helmet'),('Lavender_Traveler','Lavender','Blue','beret'),('Sunny_Villager','Sun','Teal','cap')]
rigs=[]; weapon_objects=[]
for index,(name,primary,secondary,hat) in enumerate(variants):
    coll=bpy.data.collections.new(name); scene.collection.children.link(coll); assets=[]
    ball('Tunic', (0,0,1.0),(.30,.20,.39),primary,'root')
    ball('Tunic hem',(0,0,.77),(.34,.22,.15),primary,'root')
    box('Belt',(0,-.005,.90),(.59,.42,.085),'Leather','root',.025)
    box('Buckle',(0,-.232,.90),(.13,.04,.11),'Gold','root',.025)
    for s in [-1,1]:
        x=s*.16; side='L' if s<0 else 'R'
        ball('Trousers '+side,(x,0,.56),(.13,.14,.26),secondary,'thigh.'+side)
        ball('Boot '+side,(x,-.06,.20),(.14,.20,.20),'Leather','shin.'+side)
        ball('Boot cuff '+side,(x,0,.35),(.145,.15,.07),'Cream','shin.'+side)
        x=s*.36
        ball('Sleeve '+side,(x,0,1.12),(.16,.16,.23),primary,'upper.'+side)
        ball('Forearm '+side,(s*.4,0,.86),(.105,.11,.18),'Skin','fore.'+side)
        ball('Mitten '+side,(s*.4,-.015,.71),(.115,.115,.12),'Skin','fore.'+side)
    rod('Neck',(0,0,1.24),(0,0,1.47),.105,'Skin','head')
    ball('Hair back',(0,.025,1.68),(.30,.255,.34),'Hair','head')
    ball('Face',(0,-.045,1.65),(.28,.245,.30),'Skin','head')
    for s in [-1,1]:
        ball('Ear',(s*.275,-.01,1.65),(.065,.065,.09),'Skin','head')
        ball('Eye',(s*.10,-.274,1.69),(.034,.022,.05),'Ink','head')
        ball('Eye glint',(s*.10-.009,-.294,1.708),(.01,.008,.014),'White','head')
        ball('Cheek',(s*.17,-.25,1.595),(.049,.013,.027),'Blush','head')
        ball('Fringe',(s*.12,-.155,1.87),(.13,.14,.09),'Hair','head')
    ball('Nose',(0,-.293,1.62),(.047,.044,.047),'Skin','head')
    line('Smile',[(-.048,-.282,1.565),(0,-.292,1.553),(.048,-.282,1.565)],.009,'Ink','head')
    if hat=='hood':
        ball('Hood crown',(0,.06,1.96),(.32,.25,.18),primary,'head')
        for s in [-1,1]: ball('Hood side',(s*.27,.08,1.78),(.085,.22,.26),primary,'head')
        ball('Scarf',(0,0,1.39),(.27,.22,.09),'Cream','root')
        box('Scarf tail',(.18,-.18,1.20),(.12,.07,.30),'Cream','root')
    elif hat=='helmet':
        ball('Soft helmet',(0,.035,1.95),(.32,.26,.15),'Steel','head')
        box('Helmet crest',(0,.04,2.09),(.08,.28,.17),primary,'head')
        for s in [-1,1]: ball('Shoulder pad',(s*.34,0,1.26),(.18,.19,.10),'Gold','upper.'+('L' if s<0 else 'R'))
        box('Chest badge',(0,-.204,1.16),(.16,.04,.19),'Cream','root')
    elif hat=='beret':
        ball('Beret',(.04,.02,1.98),(.36,.27,.12),primary,'head')
        ball('Beret button',(.08,.02,2.10),(.04,.04,.04),'Gold','head')
        box('Satchel',(.29,-.025,.87),(.19,.24,.23),'Leather','root')
        rod('Satchel strap',(-.20,-.205,1.32),(.25,-.205,.87),.025,'Gold','root')
        ball('Collar',(0,0,1.37),(.24,.20,.065),'Cream','root')
    else:
        ball('Cap brim',(0,-.045,1.94),(.37,.32,.055),'Cream','head')
        ball('Cap crown',(0,.01,2.015),(.25,.22,.13),primary,'head')
        box('Apron',(0,-.205,.94),(.36,.045,.43),'Cream','root')
        box('Apron pocket',(0,-.235,.90),(.18,.03,.13),primary,'root')
    # Bow in left hand; the string has its own draw control bone.
    bow=[]
    pts=[(-.40,-.04,.71+z) for z in [-.43,-.30,0,.30,.43]]
    pts[1]=(-.40,-.20,.41); pts[2]=(-.40,-.26,.71); pts[3]=(-.40,-.20,1.01)
    bow+=line('Bow limb',pts,.026,'Wood','bow')
    curve=bpy.data.curves.new('Flexible bowstring','CURVE'); curve.dimensions='3D'; curve.bevel_depth=.006; curve.bevel_resolution=2; curve.use_fill_caps=True
    spline=curve.splines.new('POLY'); spline.points.add(2)
    for p,co in zip(spline.points,[pts[0],(-.4,-.04,.71),pts[-1]]): p.co=(*co,1)
    string=bpy.data.objects.new('Bow string',curve); coll.objects.link(string); curve.materials.append(M['Cream']); assets.append((string,'bow'))
    string.shape_key_add(name='Basis'); key=string.shape_key_add(name='Draw'); key.data[1].co.y+=.4
    bow+=line('Arrow',[(-.4,.05,.71),(-.4,-.68,.71)],.012,'Wood','string')
    bow.append(ball('Arrow head',(-.4,-.70,.71),(.025,.065,.025),'Steel','string'))
    sword=[]
    sword.append(box('Sword blade',(.40,-.015,1.10),(.09,.045,.59),'Steel','sword',.025))
    sword.append(ball('Sword tip',(.40,-.015,1.39),(.045,.022,.075),'Steel','sword'))
    sword.append(box('Sword guard',(.40,-.015,.79),(.26,.07,.06),'Gold','sword'))
    sword.append(rod('Sword grip',(.40,-.015,.61),(.40,-.015,.79),.035,'Leather','sword'))
    sword.append(ball('Sword pommel',(.40,-.015,.60),(.055,.045,.045),'Gold','sword'))
    # Validate reusable geometry before creating its articulated assembly.
    if index==0:
        bpy.data.libraries.write(str(ROOT/'Parts/GM-Human/GM-Human.blend'),{coll},fake_user=True)
    data=bpy.data.armatures.new(name+' skeleton'); rig=bpy.data.objects.new(name+' Rig',data); coll.objects.link(rig)
    bpy.context.view_layer.objects.active=rig; rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    specs={'root':((0,0,.75),(0,0,1.15),None),'head':((0,0,1.4),(0,0,1.8),'root')}
    for s,side in [(-1,'L'),(1,'R')]:
        specs['thigh.'+side]=((s*.16,0,.75),(s*.16,0,.43),'root')
        specs['shin.'+side]=((s*.16,0,.43),(s*.16,0,.10),'thigh.'+side)
        specs['upper.'+side]=((s*.36,0,1.30),(s*.4,0,.98),'root')
        specs['fore.'+side]=((s*.4,0,.98),(s*.4,0,.71),'upper.'+side)
    specs['bow']=((-.4,0,.71),(-.4,0,.91),'fore.L')
    specs['string']=((-.4,0,.71),(-.4,0,.81),'bow')
    specs['sword']=((.4,0,.71),(.4,0,.91),'fore.R')
    for side,s in [('L',-1),('R',1)]: specs['target.'+side]=((s*.4,0,.71),(s*.4,0,.81),None)
    for n,(h,t,p) in specs.items():
        bone=data.edit_bones.new(n); bone.head=h; bone.tail=t
        if p: bone.parent=data.edit_bones[p]
    bpy.ops.object.mode_set(mode='OBJECT'); rig.select_set(False); rig.show_in_front=True
    for o,b in assets:
        if b:
            world=o.matrix_world.copy(); o.parent=rig; o.parent_type='BONE'; o.parent_bone=b; o.matrix_world=world
    rig.location.x=(index-1.5)*1.35
    for p in rig.pose.bones: p.rotation_mode='XYZ'
    for side in ['L','R']:
        con=rig.pose.bones['fore.'+side].constraints.new('IK'); con.name='Bow hand placement'; con.target=rig; con.subtarget='target.'+side; con.chain_count=2; con.use_stretch=False
    con=rig.pose.bones['bow'].constraints.new('COPY_ROTATION'); con.target=rig; con.subtarget='root'; con.target_space='POSE'; con.owner_space='POSE'; con.mix_mode='REPLACE'
    # Keep the bow upright independently of the bent arm, with a diagonal shooting direction.
    rig.pose.bones['bow'].constraints.remove(con)
    con=rig.pose.bones['bow'].constraints.new('COPY_ROTATION'); con.target=rig; con.subtarget='root'; con.target_space='POSE'; con.owner_space='POSE'
    driver=key.driver_add('value').driver; driver.expression='max(0,min(1,-draw/0.4))'
    var=driver.variables.new(); var.name='draw'; var.targets[0].id=rig; var.targets[0].data_path='pose.bones["string"].location[2]'
    rigs.append(rig)
    rig.animation_data_create()
    clips=[('Walk',1,32),('Bow_Shoot',41,88),('Sword_Attack',97,132)]
    for clip,start,end in clips:
        act=bpy.data.actions.new(name+' / '+clip); rig.animation_data.action=act
        for f in range(start,end+1):
            t=(f-start)/(end-start); phase=t*2*math.pi
            for p in rig.pose.bones: p.rotation_euler=(0,0,0); p.location=(0,0,0); p.scale=(1,1,1)
            pose=rig.pose.bones
            for side in ['L','R']:
                ik=pose['fore.'+side].constraints['Bow hand placement']; ik.influence=0
            pose['bow'].scale=(.001,)*3; pose['sword'].scale=(.001,)*3
            if clip=='Walk':
                pose['root'].location.y=.025*(1-math.cos(phase*2))
                for side,sgn in [('L',1),('R',-1)]:
                    pose['thigh.'+side].rotation_euler.x=.48*math.sin(phase)*sgn
                    pose['shin.'+side].rotation_euler.x=-.42*max(0,math.sin(phase)*sgn)
                    pose['upper.'+side].rotation_euler.x=-.36*math.sin(phase)*sgn
                    pose['fore.'+side].rotation_euler.x=-.15
            elif clip=='Bow_Shoot':
                pose['bow'].scale=(1,)*3
                lift=min(1,t/.20, (1-t)/.18); draw=max(0,min(1,(t-.2)/.35)) if t<.66 else max(0,1-(t-.66)/.08)
                for side in ['L','R']: pose['fore.'+side].constraints['Bow hand placement'].influence=1
                pose['target.L'].location=pose['target.L'].bone.matrix_local.to_3x3().inverted() @ (Vector((.20,-.43,.69))*lift)
                pose['target.R'].location=pose['target.R'].bone.matrix_local.to_3x3().inverted() @ (Vector((-.53,-.10,.69))*lift)
                pose['string'].location.z=-.4*draw if t<.66 else max(0,(t-.66)/.16)*2.8
                if t>.82: pose['string'].scale=(.001,)*3
                pose['head'].rotation_euler.z=-.08*lift
            else:
                pose['sword'].scale=(1,)*3
                swing=math.sin(math.pi*t)**2
                pose['sword'].rotation_euler.x=4*swing
                pose['upper.R'].rotation_euler.x=-2.3*swing
                pose['upper.R'].rotation_euler.z=.7*math.sin(phase)
                pose['fore.R'].rotation_euler.x=-.5*swing
                pose['root'].rotation_euler.z=.25*math.sin(phase)
                pose['upper.L'].rotation_euler.x=-.35*swing
                pose['thigh.L'].rotation_euler.x=.2*swing
            for p in pose:
                p.keyframe_insert(data_path='rotation_euler',frame=f,group=p.name)
                p.keyframe_insert(data_path='location',frame=f,group=p.name)
                p.keyframe_insert(data_path='scale',frame=f,group=p.name)
            for side in ['L','R']: pose['fore.'+side].constraints['Bow hand placement'].keyframe_insert(data_path='influence',frame=f)
        rig.animation_data.action=None
        track=rig.animation_data.nla_tracks.new(); track.name=clip
        strip=track.strips.new(clip,start,act); strip.extrapolation='NOTHING'; strip.blend_type='REPLACE'
    rig['outfit']=name; rig['animation_notes']='Walk 1-32; Bow_Shoot 41-88; Sword_Attack 97-132. 24 fps. In-place walk.'

coll=bpy.data.collections.new('Studio'); scene.collection.children.link(coll); assets=[]
box('Display plinth',(0,0,-.09),(6.0,1.65,.18),'Cream',bev=.15)
for i,(_,p,_,_) in enumerate(variants):
    box('Color tile',((i-1.5)*1.35,0,.015),(1.12,1.16,.045),p,bev=.12)
def text(body,loc,size):
    c=bpy.data.curves.new(body,'FONT'); c.body=body; c.align_x='CENTER'; c.size=size; c.extrude=.001
    o=bpy.data.objects.new(body,c); coll.objects.link(o); o.location=loc; o.rotation_euler=(math.pi/2,0,0); o.data.materials.append(M['Teal'])
text('GoMedieval', (0,.4,2.85),.42)
text('N I C E  &  C U T E', (0,.4,2.57),.13)
for i,label in enumerate(['MINT RANGER','CORAL GUARD','LAVENDER TRAVELER','SUNNY VILLAGER']): text(label,((i-1.5)*1.35,-.85,-.015),.095)
box('Floor',(0,0,-.30),(200,200,.12),'White',bev=.02)
def aim(o,pt): o.rotation_euler=(Vector(pt)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(4,-10,5)); cam=bpy.context.object; cam.name='Presentation camera'; aim(cam,(0,0,1.25)); cam.data.type='ORTHO'; cam.data.ortho_scale=7.2; scene.camera=cam
for loc,power,size in [((1,-4,7),1000,5),((-4,-2,4),800,4),((2,4,5),1200,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.data.energy=power; o.data.shape='DISK'; o.data.size=size; aim(o,(0,0,1))
for n,f in [('Walk • loop start',1),('Walk • loop end',32),('Bow • ready',41),('Bow • draw',66),('Bow • release',73),('Bow • recover',88),('Sword • ready',97),('Sword • strike',114),('Sword • recover',132)]: scene.timeline_markers.new(n,frame=f)
scene.frame_start=1; scene.frame_end=132; scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT'); rigs[0].select_set(True); bpy.context.view_layer.objects.active=rigs[0]
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'
out=ROOT/'Blocks/GM-Human/GM-Human.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(out))
def write(n,obj): (ROOT/n).write_bytes((json.dumps(obj,indent=2,ensure_ascii=False)+'\n').replace('\n','\r\n').encode('utf-8'))
write('Parts/GM-Human/validation.json',{'checked_before_assembly':True,'mesh_checks':checks,'units':'meters','front':'-Y','up':'+Z','external_textures':False})
write('Blocks/GM-Human/assembly.json',{'id':'GM-Human','project':'GoMedieval','style':'NiceAndCute','source':'GM-Human.blend','outfits':[v[0] for v in variants],'clips':[{'name':n,'start':s,'end':e,'fps':24} for n,s,e in clips]})
for frame,name in [(1,'wardrobe'),(66,'bow_draw'),(114,'sword_strike')]:
    scene.frame_set(frame); scene.render.filepath=str(ROOT/'Previews'/f'{name}.png'); bpy.ops.render.render(write_still=True)
print('BUILD_OK',out)
