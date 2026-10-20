"""CM-T01 source. Blender background: --python build_turret.py -- parts|assembly.
Geometry is authored in design units, +Z up, -Y forward. No game-scale claim.
"""
import bpy, math, json, sys, struct, copy, importlib.util
from pathlib import Path
from mathutils import Vector
import numpy as np

HERE = Path(__file__).resolve().parent
STYLE = HERE.parent.parent
PARTS = STYLE / 'Parts'
OUT = STYLE / 'Exports' / 'CM-T01'
TEX = STYLE / 'Materials' / 'CM-T01'
VERSION = '1.0.0'
BEVEL_SEGMENTS = 8
CYL_SEGMENTS = 96
MATS = {}
ASSET = None
ROOT = None

def text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((content.replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n').rstrip('\r\n')+'\r\n').encode('utf-8'))

def js(path, data):
    text(path, json.dumps(data, ensure_ascii=False, indent=2))

PALETTE = {
    'orange': ((0.50,0.17,0.025),0.20,0.46),
    'ivory': ((0.70,0.685,0.61),0.22,0.49),
    'graphite': ((0.075,0.083,0.09),0.68,0.37),
    'steel': ((0.25,0.275,0.29),0.85,0.31),
    'rubber': ((0.018,0.023,0.026),0.0,0.70),
    'marking': ((0.88,0.86,0.76),0.12,0.48),
}

def image_file(name, data, noncolor=False):
    h,w = data.shape[:2]
    im = bpy.data.images.new(name, width=w, height=h, alpha=True)
    im.colorspace_settings.name = 'Non-Color' if noncolor else 'sRGB'
    if data.ndim == 2: data = np.repeat(data[:,:,None],3,axis=2)
    rgba = np.concatenate([data, np.ones((h,w,1))],axis=2).astype(np.float32)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = str(TEX / (name+'.png'))
    im.file_format = 'PNG'
    im.save()
    return im

def materials():
    TEX.mkdir(parents=True,exist_ok=True)
    rng = np.random.default_rng(71)
    size = 512
    grain = rng.normal(0,0.016,(size,size))
    # Fine manufacturing grain, scattered exposed-metal chips and scratches.
    wear = np.zeros((size,size),np.float32)
    for i in range(850):
        x,y = rng.integers(2,size-16,2)
        length = int(rng.integers(1,12)); width = int(rng.integers(1,3))
        wear[y:y+width,x:x+length] = rng.uniform(.25,.9)
    yy,xx = np.mgrid[0:size,0:size]
    rough = np.clip(.50 + grain*2 + .025*np.sin(xx*.15),.25,.8)
    normal = np.zeros((size,size,3),np.float32)
    normal[:,:,0] = .5 + np.gradient(grain,axis=1)*.8
    normal[:,:,1] = .5 + np.gradient(grain,axis=0)*.8
    normal[:,:,2] = 1.0
    rim = image_file('machined_normal',normal,True)
    roughim = image_file('surface_roughness',rough,True)
    for name,(color,metal,roughness) in PALETTE.items():
        base = np.clip(np.array(color)[None,None,:]*(1+grain[:,:,None]*1.5),0,1)
        amount = wear * (.70 if name in ('orange','ivory') else .15)
        base = base*(1-amount[:,:,None]) + np.array([.22,.24,.25])*amount[:,:,None]
        im = image_file(name+'_basecolor',base)
        mat = bpy.data.materials.new('CM.'+name); mat.use_nodes = True
        bs = mat.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Metallic'].default_value = metal
        bs.inputs['Roughness'].default_value = roughness
        nodes = mat.node_tree.nodes; links = mat.node_tree.links
        c = nodes.new('ShaderNodeTexImage'); c.image=im; c.label='Base color / sRGB'; c.location=(-650,240)
        links.new(c.outputs['Color'],bs.inputs['Base Color'])
        r = nodes.new('ShaderNodeTexImage'); r.image=roughim; r.location=(-650,-40)
        links.new(r.outputs['Color'],bs.inputs['Roughness'])
        n = nodes.new('ShaderNodeTexImage'); n.image=rim; n.location=(-650,-300)
        nm = nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value=.22; nm.location=(-350,-180)
        links.new(n.outputs['Color'],nm.inputs['Color']); links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        mat.diffuse_color=(*color,1); MATS[name]=mat
    for name,col,power in [('amber',(1,.43,.065),3.5),('cyan',(.10,.65,.90),2.0)]:
        mat=bpy.data.materials.new('CM.'+name); mat.use_nodes=True
        bs=mat.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=(*col,1)
        bs.inputs['Emission Color'].default_value=(*col,1)
        bs.inputs['Emission Strength'].default_value=power
        bs.inputs['Roughness'].default_value=.26
        MATS[name]=mat
    js(TEX/'materials.json',{'version':VERSION,'textures':'512x512 repeatable PNG; color sRGB, roughness and tangent normal Non-Color',
       'materials':{k:{'base_color_srgb':v[0],'metallic':v[1],'roughness_source':'surface_roughness.png','base_color':k+'_basecolor.png','normal':'machined_normal.png'} for k,v in PALETTE.items()},
       'emission':{'amber':{'linear_rgb':[1,.43,.065],'blender_strength':3.5},'cyan':{'linear_rgb':[.1,.65,.9],'blender_strength':2}},
       'note':'Authoring materials, not a game shader contract. Source textures packed in blend files.'})

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        if c.users==0: bpy.data.collections.remove(c)

def setup_asset(pid):
    global ASSET,ROOT
    reset()
    ASSET=bpy.data.collections.new(pid); bpy.context.scene.collection.children.link(ASSET)
    ROOT=bpy.data.objects.new(pid+'.root',None); ASSET.objects.link(ROOT)
    ROOT['part_id']=pid; ROOT['version']=VERSION
    return ROOT

def finish_obj(obj,name,mat,bevel=0):
    obj.name=name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    ASSET.objects.link(obj)
    obj.parent=ROOT
    obj.data.materials.append(MATS[mat])
    if obj.type=='MESH':
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if not obj.data.uv_layers:
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.cube_project(cube_size=1.25)
            bpy.ops.object.mode_set(mode='OBJECT')
        if bevel:
            mod=obj.modifiers.new('High density edge fillets','BEVEL'); mod.width=bevel
            mod.segments=BEVEL_SEGMENTS
        for poly in obj.data.polygons: poly.use_smooth=True
        mod=obj.modifiers.new('Face weighted normals','WEIGHTED_NORMAL'); mod.keep_sharp=True; mod.weight=50
    return obj

def box(name,loc,dims,mat='graphite',bevel=.045,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.dimensions=dims
    if rot: o.rotation_euler=rot
    return finish_obj(o,name,mat,bevel)

def cyl(name,loc,radius,depth,mat='steel',axis='Z',vertices=CYL_SEGMENTS,bevel=.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    o=bpy.context.object
    if axis=='Y': o.rotation_euler[0]=math.pi/2
    if axis=='X': o.rotation_euler[1]=math.pi/2
    return finish_obj(o,name,mat,bevel)

def ring(name,loc,outer,inner,depth,mat='steel',axis='Z'):
    vs=[]; fs=[]; n=CYL_SEGMENTS
    for z,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
        for i in range(n):
            a=2*math.pi*i/n; p=Vector((r*math.cos(a),r*math.sin(a),z))
            if axis=='Y': p=Vector((p.x,-p.z,p.y))
            if axis=='X': p=Vector((p.z,p.x,p.y))
            vs.append(tuple(p+Vector(loc)))
    for i in range(n):
        j=(i+1)%n
        fs.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),
                   (j,i,2*n+i,2*n+j),(n+i,n+j,3*n+j,3*n+i)])
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vs,[],fs); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o)
    return finish_obj(o,name,mat,.012)

def profile(name,coords,width,mat='orange',bevel=.06):
    # Extruded y/z profile, centered across x. Normals recalculated for variants.
    vs=[(x,y,z) for x in (-width/2,width/2) for y,z in coords]
    n=len(coords); fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vs,[],fs); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o)
    finish_obj(o,name,mat,bevel)
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    return o

def bolt(name,loc,axis='Z'):
    cyl(name+'.seat',loc,.063,.018,'rubber',axis,32,.004)
    head=cyl(name,loc,.043,.035,'steel',axis,6,.006)
    return head

def label(name,body,loc,size=.13,rotation=(math.pi/2,0,0),mat='marking',align='CENTER'):
    curve=bpy.data.curves.new(name,'FONT'); curve.body=body; curve.size=size
    curve.align_x=align; curve.extrude=.0007; curve.bevel_depth=.0003
    o=bpy.data.objects.new(name,curve); ASSET.objects.link(o)
    o.location=loc; o.rotation_euler=rotation; o.parent=ROOT; curve.materials.append(MATS[mat])
    bpy.context.view_layer.objects.active=o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    return o

def build_deck():
    box('cast lower platform',(0,0,.19),(3.55,2.95,.38),'graphite',.16)
    box('upper armored deck',(0,0,.44),(3.46,2.84,.38),'steel',.15)
    box('front orange beam',(0,-1.35,.46),(2.74,.26,.48),'orange',.065)
    box('rear orange beam',(0,1.35,.46),(2.74,.26,.48),'orange',.065)
    for s in [-1,1]:
        box('ivory side panel',(s*1.70,0,.40),(.14,2.18,.46),'ivory',.055)
        box('side inset',(s*1.78,.36,.42),(.018,.91,.30),'graphite',.025)
        label('side identification','T-01',(s*1.793,.36,.38),.16,(math.pi/2,0,s*math.pi/2))
        for y in [-.87,.92]: bolt('side captive bolt',(s*1.785,y,.43),'X')
    box('front service hatch',(0,-1.51,.36),(1.64,.10,.43),'graphite',.055)
    label('service stencil','BUILT FROM BETTER JUNK',(0,-1.569,.37),.095)
    for x in [-.70,.70]: bolt('hatch bolt',(x,-1.57,.43),'Y')
    for x in [-1.24,1.24]:
        for y in [-.98,.98]: bolt('deck fastening',(x,y,.64))
    for y in [-1.05,1.05]: box('top anti slip insert',(0,y,.65),(1.20,.18,.022),'rubber',.02)

def build_foot():
    profile('splayed corner guard',[(-.35,.04),(-.35,.18),(-.19,.67),(.17,.67),(.35,.19),(.35,.04)],.58,'graphite',.065)
    box('steel sole',(0,0,.075),(.72,.80,.15),'steel',.055)
    box('rubber contact',(0,0,.022),(.63,.69,.044),'rubber',.025)
    box('foot armor insert',(0,-.245,.35),(.30,.075,.28),'steel',.028,(-.23,0,0))
    box('recessed guard slot',(0,-.31,.25),(.18,.035,.16),'rubber',.018,(-.23,0,0))
    bolt('guard lock',(0,-.26,.48),'Y')
    box('orange top keeper',(0,0,.66),(.33,.27,.065),'orange',.024)

def build_bearing():
    cyl('lower bearing flange',(0,0,.06),1.10,.12,'graphite')
    ring('machined lower race',(0,0,.145),1.07,.82,.09,'steel')
    cyl('rotation drum',(0,0,.285),.91,.25,'rubber')
    ring('upper bearing race',(0,0,.405),1.02,.74,.13,'steel')
    cyl('upper turntable',(0,0,.49),1.00,.10,'graphite')
    for i in range(16):
        a=2*math.pi*i/16
        o=box('radial bearing rib',(.945*math.cos(a),.945*math.sin(a),.28),(.12,.15,.18),'graphite',.018)
        o.rotation_euler[2]=a
        bolt('race bolt',(.92*math.cos(a),.92*math.sin(a),.555))

def build_yoke():
    box('traverse cross member',(0,0,.12),(2.30,1.33,.24),'graphite',.09)
    for s in [-1,1]:
        p=profile('elevation support',[(-.57,.20),(-.43,.98),(-.18,1.24),(.27,1.24),(.56,.54),(.56,.20)],.25,'steel',.07)
        p.location.x=s*1.12
        cyl('elevation axle',(s*1.12,0,1.18),.31,.28,'graphite','X')
        box('orange support inset',(s*1.27,.20,.50),(.04,.37,.45),'orange',.035)
    box('forward yoke shield',(0,-.54,.27),(1.17,.25,.35),'graphite',.055)

def build_receiver():
    profile('cast receiver',[(-.84,-.36),(-.92,.26),(-.66,.69),(.77,.69),(.99,.43),(.99,-.27),(.55,-.54),(-.56,-.54)],2.17,'graphite',.095)
    box('roof armor',(0,.12,.72),(1.73,1.46,.16),'steel',.085)
    box('roof center spline',(0,.05,.823),(.60,1.33,.07),'graphite',.04)
    for x in [-.58,.58]:
        box('barrel socket',(x,-.90,.02),(.69,.35,.69),'steel',.065)
        ring('receiver socket collar',(x,-1.08,.02),.285,.223,.07,'graphite','Y')
        for dx in [-.25,.25]:
            for z in [-.22,.25]: bolt('receiver block bolt',(x+dx,-1.09,z),'Y')
    box('roof signal bezel',(0,-.52,.827),(.66,.23,.09),'rubber',.04)
    box('roof amber strip',(0,-.54,.88),(.51,.085,.025),'amber',.012)
    for x in [-.77,.77]:
        for y in [-.42,.64]: bolt('roof fixing',(x,y,.817))
    box('underslung actuator',(0,.15,-.52),(.80,1.03,.24),'steel',.055)

def build_cheek(sign):
    coords=[(-.92,-.24),(-.96,.24),(-.67,.69),(.71,.69),(.98,.39),(.98,-.18),(.48,-.61),(-.44,-.61)]
    profile('orange shell',coords,.26,'orange',.07)
    p=profile('ivory lower cheek',[(-.91,-.28),(-.76,-.59),(-.44,-.61),(.07,-.61),(-.26,-.19),(-.77,-.12)],.276,'ivory',.04)
    box('rear ivory armor',(0,.80,.20),(.29,.32,.77),'ivory',.055)
    outer=sign*.148
    for y,z in [(-.66,.54),(.62,.48),(.65,-.17),(-.50,-.43)]: bolt('cheek captive bolt',(outer,y,z),'X')
    # Text lies in the side plane with normal pointing outward.
    rot=(math.pi/2,0,sign*math.pi/2)
    label('side SS marking','SS',(sign*.153,-.62,.23),.22,rot)
    label('side brand','SPACE\nSCRAPPERS',(sign*.155,-.62,.10),.064,rot)
    box('lower sacrificial strip',(0,.36,-.49),(.30,.40,.10),'steel',.022)

def build_barrel():
    box('sliding breech',(0,-.12,0),(.51,.44,.51),'graphite',.055)
    cyl('rear reinforced jacket',(0,-.38,0),.246,.65,'steel','Y')
    cyl('barrel tube',(0,-.98,0),.173,1.25,'graphite','Y')
    ring('rear retaining ring',(0,-.61,0),.224,.172,.10,'steel','Y')
    ring('orange heat sleeve',(0,-1.29,0),.265,.179,.45,'orange','Y')
    ring('sleeve front rim',(0,-1.54,0),.269,.178,.055,'steel','Y')
    ring('muzzle jacket',(0,-1.76,0),.270,.158,.40,'graphite','Y')
    ring('machined muzzle lip',(0,-1.965,0),.272,.158,.065,'steel','Y')
    ring('bore inner wall',(0,-1.79,0),.158,.147,.35,'rubber','Y')
    cyl('recessed bore darkness',(0,-1.59,0),.148,.012,'rubber','Y')
    for a in [0,math.pi/2,math.pi,3*math.pi/2]:
        x=.268*math.cos(a); z=.268*math.sin(a)
        o=box('muzzle longitudinal key',(x,-1.77,z),(.075,.26,.045),'graphite',.012)
        o.rotation_euler[1]=a-math.pi/2
    box('barrel top rail',(0,-.78,.193),(.11,.51,.07),'steel',.018)
    for x in [-.21,.21]: bolt('breech lock',(x,-.20,.27))

def build_trunnion():
    cyl('trunnion housing',(0,0,0),.49,.18,'graphite','X')
    ring('outer machined rim',(.10,0,0),.465,.394,.035,'steel','X')
    cyl('dark center cap',(.123,0,0),.372,.03,'graphite','X')
    ring('amber annular status',(.125,0,0),.407,.386,.018,'amber','X')
    # A dark arc cover interrupts the luminous ring to create a functional indicator.
    for i in range(8):
        a=2*math.pi*i/8
        bolt('cap perimeter fastener',(.152,.435*math.cos(a),.435*math.sin(a)),'X')
    box('central axle plate',(.153,0,0),(.025,.30,.16),'steel',.018)
    bolt('axis center',(.174,0,0),'X')

def build_handle():
    for y in [-.30,.30]:
        box('handle foot',(0,y,.04),(.23,.19,.08),'steel',.025)
        bolt('handle socket',(0,y,.09))
    for y in [-.245,.245]: box('handle upright',(0,y,.19),(.12,.11,.26),'graphite',.035,(-y*.8,0,0))
    box('handle grip',(0,0,.33),(.12,.48,.12),'graphite',.035)

def build_lamp():
    box('armored lamp housing',(0,0,0),(.56,.20,.25),'graphite',.055)
    box('lamp gasket',(0,-.107,0),(.42,.025,.14),'rubber',.018)
    box('amber lens',(0,-.127,0),(.35,.028,.077),'amber',.016)
    for x in [-.225,.225]: bolt('lens fastener',(x,-.11,0),'Y')

def build_radiator():
    box('radiator backplate',(0,0,0),(1.34,.19,.69),'graphite',.055)
    for x in np.linspace(-.56,.56,9): box('cooling blade',(float(x),.14,0),(.055,.23,.53),'steel',.012)
    for z in [-.32,.32]: box('radiator guard',(0,.22,z),(1.43,.12,.09),'graphite',.02)
    box('coolant service port',(.44,.24,-.16),(.20,.08,.12),'orange',.02)

BUILDERS={
 'cm-deck':build_deck,'cm-foot':build_foot,'cm-bearing':build_bearing,
 'cm-yoke':build_yoke,'cm-receiver':build_receiver,
 'cm-cheek-left':lambda:build_cheek(-1),'cm-cheek-right':lambda:build_cheek(1),
 'cm-barrel':build_barrel,'cm-trunnion':build_trunnion,'cm-handle':build_handle,
 'cm-lamp':build_lamp,'cm-radiator':build_radiator,
}

def pose_point(pid,pos=(0,0,0),forward=(0,-1,0),up=(0,0,1),role='mount'):
    return {'id':pid,'role':role,'position':pos,'forward':forward,'up':up,'parent':'root','space':'local'}

def part_meta(pid):
    sockets=[pose_point('mount')]; points=[]; animations=[]; areas=[]
    if pid=='cm-deck':
        sockets.append(pose_point('bearing',(0,0,.65)))
        areas=[{'id':'hull_mount','shape':'rectangle','size':[3.905,3.0975], 'position':[0,0,0], 'normal':[0,0,-1], 'up':[0,-1,0],'parent':'root','space':'local','allowed_rotation_degrees':[0,90,180,270]}]
    if pid=='cm-bearing':
        sockets.append(pose_point('yoke',(0,0,.55)))
        animations=[{'id':'yaw','node':'root','axis':[0,0,1],'range_degrees':[-180,180],'rest_degrees':0,'control':'rotation_z','demo_clip':'yaw_demo'}]
    if pid=='cm-yoke':
        sockets.append(pose_point('elevation',(0,0,1.18)))
    if pid=='cm-receiver':
        sockets += [pose_point('barrel_left',(-.58,-1.08,.02)),pose_point('barrel_right',(.58,-1.08,.02)),pose_point('cheek_left',(-1.16,0,0)),pose_point('cheek_right',(1.16,0,0)),pose_point('handle_left',(-.58,.25,.82)),pose_point('handle_right',(.58,.25,.82)),pose_point('radiator',(0,1.04,.10),forward=(0,1,0))]
        animations=[{'id':'elevation','node':'root','axis':[1,0,0],'range_degrees':[-40,8],'rest_degrees':0,'demo_clip':'elevation_demo','note':'negative X elevates -Y forward; artistic limits only'}]
    if pid=='cm-barrel':
        points=[pose_point('muzzle',(0,-2.0,0),role='projectile_origin'),pose_point('eject',(0.27,-.12,0),(1,0,0),role='optional_effect')]
        animations=[{'id':'recoil','node':'root','axis':[0,1,0],'range':[0,.14],'unit':'design_unit','rest':0,'demo_clip':'recoil_demo','duration_seconds':.6}]
    return {'schema':'SS3D.authoring.part/1','id':pid,'version':VERSION,'project':'SS','style':'ChunkyModular','source':pid+'.blend',
       'units':'design_unit','coordinate_system':{'handedness':'right','up':'+Z','forward':'-Y'},'origin':[0,0,0],'pivot':[0,0,0],
       'scale_policy':'positive uniform instance scale; nonuniform requires explicit parametric variant and revalidation',
       'sockets':sockets,'mount_regions':areas,'functional_points':points,'animations':animations,
       'bind_pose':{'translation':[0,0,0],'rotation_euler_xyz_radians':[0,0,0],'scale':[1,1,1]},
       'materials':[], 'emissive_regions':[], 'dependencies':['../../Materials/CM-T01/materials.json'],
       'compatibility':'authoring metadata only; game mapping pending'}

def studio(target,size,res=600):
    scene=bpy.context.scene
    scene.render.engine='CYCLES'; scene.cycles.samples=24
    scene.cycles.use_denoising=True
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type='OPTIX'; prefs.get_devices()
        for d in prefs.devices: d.use=d.type!='CPU'
        if any(d.use for d in prefs.devices): scene.cycles.device='GPU'
    except Exception: pass
    scene.render.resolution_x=res; scene.render.resolution_y=res; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('CM studio world'); scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.28,.30,.34,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    scene.view_settings.view_transform='AgX'
    scene.render.fps=30
    c=bpy.data.collections.new('STUDIO'); scene.collection.children.link(c)
    def link(o):
        for cc in list(o.users_collection): cc.objects.unlink(o)
        c.objects.link(o)
    floor_mat=bpy.data.materials.get('studio floor') or bpy.data.materials.new('studio floor')
    floor_mat.diffuse_color=(.245,.265,.29,1)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.045)); o=bpy.context.object; o.name='Studio floor'; o.data.materials.append(floor_mat); link(o)
    for name,loc,power,area in [('Key',(4,-5,8),1700,5),('Fill',(-5,-1,4),1100,5),('Rim',(3,5,6),2100,4)]:
        dat=bpy.data.lights.new(name,'AREA'); dat.energy=power; dat.shape='DISK'; dat.size=area
        o=bpy.data.objects.new(name,dat); c.objects.link(o); o.location=loc
        o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    dat=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',dat); c.objects.link(cam)
    cam.location=Vector(target)+Vector((6,-9,5.8)).normalized()*size*2
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    dat.type='ORTHO'; dat.ortho_scale=size; dat.lens=50; scene.camera=cam
    return cam,c

def bounds(objects):
    bpy.context.view_layer.update()
    points=[o.matrix_world @ Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box]
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return low,high

def add_demo(root,kind):
    if kind=='recoil':
        for f,y in [(1,0),(3,.14),(8,.03),(19,0)]: root.location.y=y; root.keyframe_insert(data_path='location',frame=f,index=1)
    elif kind=='yaw':
        for f,a in [(1,0),(31,30),(61,-30),(91,0)]: root.rotation_euler.z=math.radians(a); root.keyframe_insert(data_path='rotation_euler',frame=f,index=2)
    elif kind=='elevation':
        for f,a in [(1,0),(31,-40),(61,8),(91,0)]: root.rotation_euler.x=math.radians(a); root.keyframe_insert(data_path='rotation_euler',frame=f,index=0)
    if root.animation_data and root.animation_data.action: root.animation_data.action.name=kind+'_demo'
    bpy.context.scene.frame_set(1)

def parts_stage(only=None):
    materials(); records=[]
    kit_path=STYLE/'Kits'/'CM-T01'/'kit.json'
    if only and kit_path.exists(): records=json.loads(kit_path.read_text(encoding='utf-8'))['parts']
    for pid,builder in BUILDERS.items():
        if only and pid not in only: continue
        records=[r for r in records if r['id']!=pid]
        root=setup_asset(pid); builder()
        meta=part_meta(pid)
        objects=list(ASSET.objects)
        low,high=bounds(objects)
        meta['bounds']={'min':list(low),'max':list(high),'dimensions':list(high-low)}
        meta['materials']=sorted({m.name for o in objects if o.type=='MESH' for m in o.data.materials})
        meta['emissive_regions']=[{'object':o.name,'material':m.name,'settings':'../../Materials/CM-T01/materials.json#emission'} for o in objects if o.type=='MESH' for m in o.data.materials if m.name in ('CM.amber','CM.cyan')]
        for a in meta['animations']:
            target=root if a['node']=='root' else ASSET.objects[a['node']]
            add_demo(target,a['id'])
        root['metadata_json']=json.dumps(meta,ensure_ascii=False)
        size=max(high-low)*1.70
        center=(high+low)*.5
        cam,sc=studio(center,max(size,.85),560)
        if pid in ('cm-cheek-left','cm-radiator'):
            cam.location=center+Vector((-6,9,5.8) if pid=='cm-radiator' else (-6,-9,5.8)).normalized()*max(size,.85)*2
            cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        # Raise studio floor under standalone parts without changing model origin.
        sc.objects['Studio floor'].location.z=low.z-.04
        dest=PARTS/pid; dest.mkdir(parents=True,exist_ok=True)
        js(dest/'part.json',meta)
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(dest/(pid+'.blend')),compress=True)
        scene=bpy.context.scene; scene.render.filepath=str(dest/'preview.png')
        bpy.ops.render.render(write_still=True)
        records.append({'id':pid,'version':VERSION,'source':str((dest/(pid+'.blend')).relative_to(STYLE)),'preview':str((dest/'preview.png').relative_to(STYLE)),'materials_ready':True,'metadata_ready':True})
        print('PART_READY '+pid,flush=True)
    js(STYLE/'Kits'/'CM-T01'/'kit.json',{'id':'CM-T01-kit','version':VERSION,'parts':records,'status':'all parts individually modeled, textured and previewed before block assembly'})

def append_part(pid,instance,parent,loc=(0,0,0),rot=(0,0,0)):
    source=PARTS/pid/(pid+'.blend')
    with bpy.data.libraries.load(str(source),link=False) as (src,dst): dst.collections=[pid]
    col=dst.collections[0]
    mapping={}
    for original in col.objects:
        o=original.copy(); o.animation_data_clear(); mapping[original]=o
        o.name=instance+'.'+original.name
        bpy.context.scene.collection.objects.link(o)
    for original,o in mapping.items():
        o.parent=mapping.get(original.parent)
    root=next(o for original,o in mapping.items() if original.parent is None)
    root.name=instance; root.parent=parent; root.location=loc; root.rotation_euler=rot
    root['instance_id']=instance; root['source_part']=pid; root['source_version']=VERSION
    # Appended collection is not in scene: remove originals, preserve shared mesh data.
    for original in list(col.objects): bpy.data.objects.remove(original,do_unlink=True)
    bpy.data.collections.remove(col)
    return root

def empty(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None); bpy.context.scene.collection.objects.link(o); o.parent=parent; o.location=loc; return o

def add_combined_glb_clip(path):
    # Blender emits separate object clips. Keep them and add a simultaneous demo.
    blob=path.read_bytes(); chunks=[]; offset=12
    while offset<len(blob):
        length,kind=struct.unpack_from('<II',blob,offset)
        chunks.append((kind,blob[offset+8:offset+8+length])); offset+=8+length
    doc=json.loads(chunks[0][1]); original=doc.get('animations',[])
    merged={'name':'CM-T01 Demo','samplers':[],'channels':[]}
    for anim in original:
        base=len(merged['samplers']); merged['samplers']+=copy.deepcopy(anim['samplers'])
        for channel in anim['channels']:
            c=copy.deepcopy(channel); c['sampler']+=base; merged['channels'].append(c)
    assert len(merged['channels'])==4, 'Expected yaw, elevation and two recoils'
    doc['animations']=[merged]+original
    raw=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    raw+=b' '*((-len(raw))%4); chunks[0]=(chunks[0][0],raw)
    payload=b''.join(struct.pack('<II',len(data),kind)+data for kind,data in chunks)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,12+len(payload))+payload)

def assembly_stage():
    kit=json.loads((STYLE/'Kits'/'CM-T01'/'kit.json').read_text(encoding='utf-8'))
    assert len(kit['parts'])==len(BUILDERS) and all(p['materials_ready'] and p['metadata_ready'] for p in kit['parts'])
    reset(); OUT.mkdir(parents=True,exist_ok=True)
    block=empty('CM-T01'); instances=[]
    def place(pid,i,parent,loc=(0,0,0),rot=(0,0,0)):
        o=append_part(pid,i,parent,loc,rot)
        instances.append({'id':i,'part':pid,'version':VERSION,'parent':parent.name,'translation':list(loc),'rotation_xyz_radians':list(rot),'scale':[1,1,1]})
        return o
    place('cm-deck','deck',block)
    for i,(x,y) in enumerate([(-1.75,-1.36),(1.75,-1.36),(-1.75,1.36),(1.75,1.36)]):
        place('cm-foot','foot_'+str(i+1),block,(x,y,0),(0,0,0 if y<0 else math.pi))
    yaw=empty('joint_yaw',block,(0,0,.65))
    place('cm-bearing','bearing',yaw)
    place('cm-yoke','yoke',yaw,(0,0,.55))
    pitch=empty('joint_elevation',yaw,(0,0,1.73))
    place('cm-receiver','receiver',pitch)
    place('cm-cheek-left','cheek_left',pitch,(-1.53,0,0))
    place('cm-cheek-right','cheek_right',pitch,(1.53,0,0))
    left=place('cm-barrel','barrel_left',pitch,(-.754,-1.404,.024))
    right=place('cm-barrel','barrel_right',pitch,(.754,-1.404,.024))
    for sign in [-1,1]:
        place('cm-trunnion-armored','trunnion_'+str(sign),yaw,(sign*1.84,0,1.73),(0,0,0 if sign==1 else math.pi))
        place('cm-handle','handle_'+str(sign),pitch,(sign*1.03,.25,1.058))
        place('cm-lamp','lamp_'+str(sign),block,(sign*1.20,-1.55,.59))
    place('cm-radiator','radiator',pitch,(0,1.352,.12))
    place('cm-access-hatch','roof_hatch',pitch,(0,.20,1.056))
    for side,barrel in [('left',left),('right',right)]:
        place('cm-breech-collar','collar_'+side,barrel,(0,-.70,0))
    for side,barrel in [('left',left),('right',right)]:
        p=empty('muzzle_'+side,barrel,(0,-3.40,0)); p['role']='projectile_origin'; p['forward_local']='0,-1,0'; p['up_local']='0,0,1'
    meta={'schema':'SS3D.authoring.block/1','id':'CM-T01','version':VERSION,'catalog_id':None,'project':'SS','style':'ChunkyModular',
        'units':'design_unit','up':'+Z','forward':'-Y','handedness':'right','instances':instances,
        'joints':[{'id':'joint_yaw','parent':'CM-T01','position':[0,0,.65],'axis':[0,0,1],'range_degrees':[-180,180]},
                  {'id':'joint_elevation','parent':'joint_yaw','position':[0,0,1.73],'axis':[1,0,0],'range_degrees':[-40,8]}],
        'animations':{'aim_demo':{'duration_frames':120,'fps':30,'yaw_degrees':[-30,30],'elevation_degrees':[-40,8]},'recoil_left':{'frames':18,'distance':.14},'recoil_right':{'frames':18,'distance':.14}},
        'mount_regions':[{'id':'hull_mount','parent':'deck','shape':'rectangle','size':[3.905,3.0975],'position':[0,0,0],'normal':[0,0,-1],'up':[0,-1,0]}],
        'functional_points':[{'id':'muzzle_left','parent':'barrel_left','position':[0,-3.40,0],'forward':[0,-1,0],'up':[0,0,1]}, {'id':'muzzle_right','parent':'barrel_right','position':[0,-3.40,0],'forward':[0,-1,0],'up':[0,0,1]}],
        'note':'Art asset. GLB converts Blender Z-up to glTF Y-up. No game import/scale/collider/LOD contract.'}
    scene=bpy.context.scene; scene.frame_end=120
    for f,y,p in [(1,0,0),(31,30,-40),(61,-30,8),(91,0,-18),(120,0,0)]:
        yaw.rotation_euler.z=math.radians(y); yaw.keyframe_insert(data_path='rotation_euler',frame=f,index=2)
        pitch.rotation_euler.x=math.radians(p); pitch.keyframe_insert(data_path='rotation_euler',frame=f,index=0)
    yaw.animation_data.action.name='aim_yaw'; pitch.animation_data.action.name='aim_elevation'
    for barrel,start in [(left,42),(right,51)]:
        rest=barrel.location.y
        for f,d in [(1,0),(start,0),(start+2,.14),(start+8,.04),(start+18,0),(120,0)]:
            barrel.location.y=rest+d; barrel.keyframe_insert(data_path='location',frame=f,index=1)
        barrel.animation_data.action.name='recoil_'+barrel.name
    scene.frame_set(1)
    meshes=[o for o in scene.objects if o.type=='MESH']
    canonical={}
    for o in meshes:
        for slot in o.material_slots:
            if slot.material:
                key='.'.join(slot.material.name.split('.')[:2])
                canonical.setdefault(key,slot.material); slot.material=canonical[key]
    low,high=bounds(meshes); meta['rest_bounds']={'min':list(low),'max':list(high),'dimensions':list(high-low)}
    block['metadata_json']=json.dumps(meta,ensure_ascii=False)
    js(HERE/'assembly.json',meta)
    cam,studio_col=studio((0,-.9,1.65),8.4,1400)
    scene.cycles.samples=64
    # Preserve source textures when the project is moved.
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'CM-T01.blend'),compress=True)
    for name,loc,target,scale in [
        ('hero',(7,-10,6.8),(0,-.9,1.7),8.4),
        ('top',(0,-1.45,12),(0,-1.45,0),8.2),
        ('rear',(-7,9,6),(0,0,1.6),7.8)]:
        cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale
        scene.render.filepath=str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
        print('RENDER_READY '+name,flush=True)
    scene.frame_set(1)
    # GLB selection excludes presentation lights/floor/camera.
    bpy.ops.object.select_all(action='DESELECT')
    for o in scene.objects:
        if studio_col not in o.users_collection: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/'CM-T01.glb'),export_format='GLB',use_selection=True,
        export_animations=True,export_animation_mode='SCENE',export_extras=True,export_apply=True,export_yup=True)
    add_combined_glb_clip(OUT/'CM-T01.glb')
    # Actual evaluated geometry counts and sampled mechanical checks.
    counts=[]; dg=bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        ev=o.evaluated_get(dg); mesh=ev.to_mesh(); mesh.calc_loop_triangles()
        counts.append(len(mesh.loop_triangles)); ev.to_mesh_clear()
    check={'part_types':len(BUILDERS),'instances':len(instances),'mesh_objects':len(meshes),'evaluated_triangles_rest':sum(counts),
        'bevel_segments':BEVEL_SEGMENTS,'cylinder_segments':CYL_SEGMENTS,'sampled_poses':[],
        'scope':'Authoring checks. Visual self intersections require render inspection; no live game verification.'}
    for f in [1,31,44,53,61,91,120]:
        scene.frame_set(f); bpy.context.view_layer.update()
        directions=[]
        for name in ['muzzle_left','muzzle_right']:
            o=scene.objects[name]; d=(o.matrix_world.to_quaternion()@Vector((0,-1,0))).normalized()
            assert abs(d.length-1)<1e-5
            directions.append({'id':name,'position':list(o.matrix_world.translation),'direction':list(d)})
        check['sampled_poses'].append({'frame':f,'points':directions})
    scene.frame_set(1)
    js(OUT/'validation.json',check)
    print('ASSEMBLY_READY '+str(sum(counts))+' triangles',flush=True)

# The current revision is explicit source, with v1 preserved in Revisions/.
_revision_spec=importlib.util.spec_from_file_location('cm_revision2',HERE/'revision2.py')
_revision=importlib.util.module_from_spec(_revision_spec)
_revision_spec.loader.exec_module(_revision)
_revision.apply(globals())
if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if args and args[0]=='parts':
        assert all(p in BUILDERS for p in args[1:]), 'Unknown part ID'
        parts_stage(args[1:] or None)
    elif args==['assembly']: assembly_stage()
    else: raise SystemExit('Choose -- parts or -- assembly')
