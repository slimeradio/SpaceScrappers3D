import bpy, math, json, os
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'Tools'))
from detail_geometry import enhance
BLOCK = ROOT / 'Blocks/MA-T01'
PARTS = {}

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) if not isinstance(data, str) else data
    path.write_bytes((text.replace('\r\n','\n').replace('\n','\r\n')+'\r\n').encode('utf-8'))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global mats
    mats={}
    for name,color,metal,rough in [('Armor',(.095,.113,.123),.72,.48),('Steel',(.25,.28,.29),.9,.3),('Dark',(.018,.025,.028),.65,.6),('Mark',(.65,.65,.56),.15,.6),('Warm',(.95,.7,.32),.2,.3),('Glass',(.10,.30,.31),.7,.17)]:
        m=bpy.data.materials.new(name);m.use_nodes=True
        n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
        if name in ('Armor','Steel'):
            noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2
            tex=n.new('ShaderNodeTexCoord');m.node_tree.links.new(tex.outputs['Generated'],noise.inputs['Vector'])
            ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.24;ramp.color_ramp.elements[0].color=(*(v*.62 for v in color),1);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(*(v*1.35 for v in color),1)
            m.node_tree.links.new(noise.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
            bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.018;m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])
        if name=='Warm':p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=3
        mats[name]=m
    global coll
    coll=bpy.data.collections.new('Geometry');bpy.context.scene.collection.children.link(coll)

def finish(o,name,mat,bevel=0):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    coll.objects.link(o);o.data.materials.append(mats[mat])
    if bevel:
        mod=o.modifiers.new('Machined edge radius','BEVEL');mod.width=bevel;mod.segments=3
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o

def box(name,loc,size,mat='Armor',bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,bevel)

def cyl(name,loc,r,depth,mat='Steel',axis='Z',verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);o=bpy.context.object
    if axis=='Y':o.rotation_euler.x=math.pi/2
    if axis=='X':o.rotation_euler.y=math.pi/2
    return finish(o,name,mat,.025)

def ring(name,loc,outer,inner,depth,axis='Z',mat='Steel'):
    v=[];f=[];N=48
    for z,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
        for i in range(N):
            a=2*math.pi*i/N;v.append((r*math.cos(a),r*math.sin(a),z))
    for i in range(N):
        j=(i+1)%N
        f.extend([(i,j,N+j,N+i),(2*N+j,2*N+i,3*N+i,3*N+j),(N+i,N+j,3*N+j,3*N+i),(j,i,2*N+i,2*N+j)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],f);mesh.update();o=bpy.data.objects.new(name,mesh);coll.objects.link(o);o.location=loc
    if axis=='Y':o.rotation_euler.x=math.pi/2
    finish(o,name,mat,.015);return o

def wedge(name,loc,w,d,h,mat='Armor'):
    # Trapezoidal armor section, narrower roof and sloped front/back.
    v=[(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),(-w*.38,-d*.35,h),(w*.38,-d*.35,h),(w*.38,d*.35,h),(-w*.38,d*.35,h)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]);mesh.update();o=bpy.data.objects.new(name,mesh);coll.objects.link(o);o.location=loc;return finish(o,name,mat,.045)

def label(text,loc,size=.18,rot=(math.pi/2,0,0)):
    bpy.ops.object.text_add(location=loc,rotation=rot);o=bpy.context.object;o.data.body=text;o.data.size=size;o.data.extrude=.001;finish(o,'Stencil '+text,'Mark');return o

def bolts(xs,ys,z):
    for x in xs:
        for y in ys:cyl('Captive hex bolt',(x,y,z),.045,.035,'Steel',verts=6)

def base():
    box('Lower structural chassis',(0,0,.18),(4.65,3.95,.36),'Dark',.18)
    box('Armored deck',(0,0,.56),(4.8,4.1,.72),'Armor',.23)
    box('Upper deck inset',(0,0,.94),(3.9,3.25,.1),'Steel',.09)
    for x in [-2.12,2.12]:
        for y in [-1.43,0,1.43]:
            box('Segmented perimeter armor',(x,y,.59),(.55,1.16,.86),'Armor',.1)
            box('Retainer strap',(x,y,.6),(.59,.14,.9),'Steel',.025)
    for y in [-2.04,2.04]:
        box('Service panel',(0,y,.57),(2.85,.12,.53),'Armor')
        for x in [-1.82,1.82]:box('Deck light bezel',(x,y,.83),(.42,.13,.16),'Dark',.02);box('Deck light',(x,y*1.008,.84),(.29,.04,.065),'Warm',.012)
    for x in [-1.6,1.6]:
        for j in range(7):box('Cooling louvre',(x,-.50+j*.15,1.012),(.48,.065,.035),'Dark',.01)
    bolts([-1.8,1.8],[-1.65,1.65],1.0)
    label('SPACE SCRAPPERS',(-1.1,-2.111,.63),.19);label('MA / 03',(-1.1,-2.113,.37),.13)

def bearing():
    cyl('Bearing lower seal',(0,0,.08),1.77,.16,'Dark')
    ring('Machined bearing track',(0,0,.20),1.74,1.42,.16)
    cyl('Turntable',(0,0,.36),1.59,.26,'Dark')
    ring('Upper race',(0,0,.52),1.64,1.40,.14)
    for i in range(20):
        a=2*math.pi*i/20;o=box('Segmented race guard',(1.62*math.cos(a),1.62*math.sin(a),.37),(.29,.21,.24),'Armor',.025);o.rotation_euler.z=a
    for i in range(12):
        a=2*math.pi*i/12;cyl('Race fastener',(1.54*math.cos(a),1.54*math.sin(a),.61),.045,.035,'Steel',verts=6)

def hull():
    box('Inner turret frame',(0,.12,.64),(3.35,2.65,1.12),'Dark',.15)
    box('Armored roof bridge',(0,.05,1.50),(2.30,.95,.38),'Armor',.07)
    for x in [-1.27,1.27]:
        wedge('Heavy cheek armor',(x,-.12,.18),1.10,3.12,1.51)
        for y in [-.94,.04,.98]:
            box('Cheek applique',(x,y,1.63),(.80,.78,.13),'Armor',.06)
            bolts([x-.27,x+.27],[y-.24,y+.24],1.71)
        box('Side armor seam',(x*1.425,.12,.70),(.045,2.05,.055),'Dark',.01)
    box('Rear armored counterweight',(0,1.21,.86),(3.12,.68,1.19),'Armor',.16)
    for x in [-.86,0,.86]:box('Roof spinal panel',(x,.84,1.52),(.68,.90,.15),'Armor',.06)
    for x in [-1.4,1.4]:
        for j in range(5):box('Rear ventilation slot',(x+j*.06 if x<0 else x-j*.06,1.565,.72),(.028,.04,.47),'Dark',.006)
    label('03',(-1.83,-.54,.75),.43,(math.pi/2,0,-math.pi/2))
    label('ARMORED SYSTEMS',(.95,1.563,1.02),.14,(math.pi/2,0,math.pi))

def mantlet():
    box('Cradle beam',(0,.12,0),(2.15,.78,.72),'Dark',.10)
    for x in [-.58,.58]:
        box('Independent armored sleeve',(x,-.20,0),(.98,1.20,.94),'Armor',.14)
        ring('Gun port',(x,-.82,0),.39,.27,.14,'Y','Steel')
        for z in [-.31,.31]:box('Mantlet cheek',(x,-.81,z),(.75,.16,.13),'Armor',.025)
    for x in [-1.15,1.15]:cyl('Elevation trunnion',(x,.17,0),.30,.18,'Steel','X')

def barrel():
    cyl('Recoil sleeve',(0,-.38,0),.275,.76,'Steel','Y')
    cyl('Main tube',(0,-1.53,0),.165,1.65,'Steel','Y')
    for y,r,d in [(-.72,.29,.18),(-1.08,.20,.10),(-1.85,.20,.10),(-2.25,.23,.18)]:ring('Barrel reinforcing collar',(0,y,0),r,.14,d,'Y')
    # Genuine open bore, inner wall and recessed dark bore floor.
    ring('Open muzzle brake',(0,-2.61,0),.265,.135,.62,'Y')
    cyl('Recessed bore darkness',(0,-2.36,0),.133,.015,'Dark','Y')
    for x in [-.255,.255]:
        for y in [-2.44,-2.64,-2.84]:box('Brake gas port recess',(x,y,0),(.025,.115,.18),'Dark',.015)

def hatch():
    box('Hatch gasket',(0,0,.035),(.91,.79,.07),'Dark')
    box('Hatch armor',(0,0,.10),(.84,.72,.10),'Armor',.06)
    for x in [-.27,.27]:box('Hinge',(x,.36,.12),(.16,.14,.13),'Steel',.02)
    box('Handle',(0,-.15,.22),(.31,.065,.06),'Steel',.02)
    for x in [-.125,.125]:box('Handle foot',(x,-.15,.17),(.05,.065,.09),'Steel',.012)
    bolts([-.30,.30],[-.24,.24],.167)

def optics():
    wedge('Optic armor',(0,0,0),.66,.71,.40)
    box('Optic face',(0,-.32,.22),(.47,.09,.23),'Dark',.03)
    for x in [-.13,0,.13]:box('Warm aiming lens',(x,-.375,.24),(.085,.035,.07),'Warm',.012)
    cyl('Sensor cap',(0,.11,.48),.17,.25,'Dark')
    ring('Sensor guard',(0,.11,.61),.20,.14,.06)

def handle():
    for x in [-.23,.23]:box('Deck mounting shoe',(x,0,.025),(.16,.20,.05),'Armor',.015);box('Upright',(x,0,.16),(.07,.08,.25),'Steel',.03)
    box('Grip',(0,0,.285),(.48,.08,.08),'Steel',.035)

def setup(target=(0,0,1.5),scale=8.8,view=(8,-11,8),resolution=900):
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
    s.render.resolution_x=resolution;s.render.resolution_y=resolution;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.world=bpy.data.worlds.new('Studio world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.20,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    s.view_settings.view_transform='AgX'
    bpy.ops.object.camera_add(location=view);cam=bpy.context.object;cam.name='Preview camera';cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;s.camera=cam
    for name,loc,power,size,col in [('Key',(1,-5,9),1800,7,(1,.89,.74)),('Fill',(-6,-1,5),1300,6,(.62,.77,1)),('Rim',(3,6,8),2400,5,(.76,.85,1))]:
        bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.name=name;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.data.color=col;l.rotation_euler=(Vector(target)-l.location).to_track_quat('-Z','Y').to_euler()
    # Studio objects stay outside geometry and authoring assemblies.
    ground=bpy.data.materials.new('Studio ground');ground.diffuse_color=(.037,.047,.058,1)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.035));bpy.context.object.name='Studio floor';bpy.context.object.data.materials.append(ground)
    return cam

def render(path):
    path.parent.mkdir(parents=True,exist_ok=True);bpy.context.scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def mount(name,loc,role):
    o=bpy.data.objects.new(name,None);coll.objects.link(o);o.location=loc;o.empty_display_size=.12;o['role']=role;o['forward']='-Y';o['up']='+Z';return o

specs=[('MA-P01','Armored foundation',base,(0,0,0),[('deck',(0,0,1.0),'bearing')]),('MA-P02','Azimuth bearing',bearing,(0,0,0),[('bottom',(0,0,0),'bearing'),('turret',(0,0,.61),'hull')]),('MA-P03','Armored turret hull',hull,(0,0,0),[('bottom',(0,0,0),'hull'),('elevation',(0,-.94,.9),'cradle'),('hatch',(0,.88,1.61),'accessory'),('optic',(-.5,-.15,1.69),'accessory')]),('MA-P04','Twin gun mantlet',mantlet,(0,0,0),[('pivot',(0,0,0),'cradle'),('barrel-L',(-.58,-.77,0),'gun'),('barrel-R',(.58,-.77,0),'gun')]),('MA-P05','Heavy barrel',barrel,(0,0,0),[('breech',(0,0,0),'gun'),('muzzle',(0,-2.92,0),'projectile-origin')]),('MA-P06','Service hatch',hatch,(0,0,0),[('bottom',(0,0,0),'accessory')]),('MA-P07','Protected optics',optics,(0,0,0),[('bottom',(0,0,0),'accessory')]),('MA-P08','Deck grab handle',handle,(0,0,0),[('bottom',(0,0,0),'accessory')])]

for pid,title,fn,origin,mounts in specs:
    reset();coll.name=pid;fn();enhance(globals(),pid)
    bpy.context.view_layer.update()
    for name,loc,role in mounts:mount('mount.'+name,loc,role)
    meshobjects=[o for o in coll.objects if o.type=='MESH'];pts=[o.matrix_world @ Vector(c) for o in meshobjects for c in o.bound_box]
    low=[min(p[i] for p in pts) for i in range(3)];high=[max(p[i] for p in pts) for i in range(3)];center=tuple((low[i]+high[i])/2 for i in range(3));extent=max(high[i]-low[i] for i in range(3))
    folder=ROOT/'Parts'/pid;folder.mkdir(exist_ok=True)
    setup(center,extent*1.65,(extent*1.5,-extent*2,extent*1.4),520)
    bpy.data.objects['Studio floor'].location.z=low[2]-.06
    render(folder/'Previews'/f'{pid}.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/f'{pid}.blend'))
    data={'schema':'MilitaryArmor.BlenderAuthoring/1','id':pid,'version':'1.1','name':title,'source':f'{pid}.blend','units':'BU, physical scale unspecified','axes':{'handedness':'right','up':'+Z','forward':'-Y'},'origin':[0,0,0],'bounds_local':{'min':low,'max':high},'scale_policy':'unit scale only','materials':[{'id':m.name,'surfaces':[o.name for o in coll.objects if o.type in ('MESH','FONT','CURVE') and m in list(o.data.materials)],'source':'Blender procedural nodes; Generated projection; linear shader values; no file textures; no UV dependency'} for m in bpy.data.materials if any(o.type in ('MESH','FONT','CURVE') and m in list(o.data.materials) for o in coll.objects)],'emission':[{'slot':'Warm','color_linear':[.95,.7,.32],'strength':3,'units':'Blender shader strength','default':'on','regions':[o.name for o in coll.objects if o.type=='MESH' and mats['Warm'] in list(o.data.materials)]}] if any(o.type=='MESH' and mats['Warm'] in list(o.data.materials) for o in coll.objects) else [],'mounts':[{'id':name,'node':'mount.'+name,'role':role,'position':loc,'forward':[0,-1,0],'up':[0,0,1],'compatible_role':role,'allowed_scale':[1,1,1]} for name,loc,role in mounts if role!='projectile-origin'],'functional_points':[{'id':'muzzle','node':'mount.muzzle','position':[0,-2.92,0],'direction':[0,-1,0],'up':[0,0,1]}] if pid=='MA-P05' else [],'attachment_areas':[],'animations':[]}
    write(folder/'part.json',data);PARTS[pid]=data
    print('PART_READY',pid,flush=True)

reset();bpy.data.collections.remove(coll);scene=bpy.context.scene
library={}
for pid in PARTS:
    with bpy.data.libraries.load(str(ROOT/'Parts'/pid/f'{pid}.blend'),link=False) as (src,dst):dst.collections=[pid]
    library[pid]=dst.collections[0]

def empty(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;o.empty_display_size=.2;return o
root=empty('MA-T01');yaw=empty('Azimuth',root,(0,0,1));hullroot=empty('Hull',yaw,(0,0,.61));pitch=empty('Elevation',hullroot,(0,-.94,.9))
instances=[]
def instance(i,pid,parent,loc=(0,0,0)):
    o=empty(i,parent,loc);o.instance_type='COLLECTION';o.instance_collection=library[pid];o['part_id']=pid;o['part_version']='1.1'
    instances.append({'id':i,'part_id':pid,'version':'1.1','source':f'../../Parts/{pid}/{pid}.blend','parent':parent.name,'translation':list(loc),'rotation_euler_xyz':[0,0,0],'scale':[1,1,1]});return o
instance('Foundation','MA-P01',root)
instance('Bearing','MA-P02',yaw)
instance('TurretArmor','MA-P03',hullroot)
instance('Mantlet','MA-P04',pitch)
left=instance('Barrel.L','MA-P05',pitch,(-.58,-.77,0));right=instance('Barrel.R','MA-P05',pitch,(.58,-.77,0))
instance('RoofHatch','MA-P06',hullroot,(0,.88,1.61));instance('RoofOptics','MA-P07',hullroot,(-.5,-.15,1.69))
for x in [-1.9,1.9]:
    for y in [-1.5,1.5]:instance(f'GrabHandle.{x}.{y}','MA-P08',root,(x,y,1.0))

for node,keys in [(yaw,[(1,0),(35,90),(70,180),(105,270),(140,360)]),(pitch,[(1,0),(35,25),(70,-8),(105,12),(140,0)])]:
    axis=2 if node==yaw else 0
    for frame,angle in keys:node.rotation_euler[axis]=math.radians(angle if node==yaw else -angle);node.keyframe_insert('rotation_euler',frame=frame)
    node['axis']='Z' if node==yaw else 'X';node['limits_degrees']='0..360 continuous' if node==yaw else '-8..25 visual test'
for obj in [left,right]:
    for frame,dy in [(1,0),(17,0),(19,.17),(25,0),(140,0)]:obj.location.y=-.77+dy;obj.keyframe_insert('location',frame=frame)
scene.frame_end=140;scene.frame_set(1)
cam=setup((0,-.55,1.65),9.0,(8,-11,8),1100)
render(BLOCK/'Previews/MA-T01-hero.png')
cam.location=(0,-.85,14);cam.rotation_euler=(0,0,0);cam.rotation_euler=(Vector((0,-.85,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.2
render(BLOCK/'Previews/MA-T01-top.png')
cam.location=(-8,8,6);cam.rotation_euler=(Vector((0,0,1.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=8.6
render(BLOCK/'Previews/MA-T01-rear.png')
pose_results=[]
for frame,name in [(35,'elevation-max'),(70,'elevation-min'),(105,'combined')]:
    scene.frame_set(frame);cam.location=(9,-10,7);cam.rotation_euler=(Vector((0,0,1.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9
    render(BLOCK/f'Previews/MA-T01-{name}.png')
    pose_results.append({'frame':frame,'name':name,'yaw_deg':math.degrees(yaw.rotation_euler.z),'elevation_deg':-math.degrees(pitch.rotation_euler.x)})
scene.frame_set(1);cam.location=(8,-11,8);cam.rotation_euler=(Vector((0,-.55,1.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9
# Open source directly in a useful material-colored camera view.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(BLOCK/'MA-T01.blend'))
write(BLOCK/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':'MA-T01','version':'1.1','catalog_id':'fleet-artillery-corvette','catalog_grid':[2,3],'physical_scale':'unspecified; BU are authoring units','axes':{'up':'+Z','forward':'-Y','handedness':'right'},'nodes':[{'id':o.name,'parent':o.parent.name if o.parent else None,'translation':list(o.location),'rotation_euler_xyz':list(o.rotation_euler),'scale':list(o.scale)} for o in [root,yaw,hullroot,pitch]],'instances':instances,'animations':{'fps':scene.render.fps,'frame_range':[1,140],'demonstration_only':True,'channels':[{'node':'Azimuth','axis':'Z','degrees':[0,360]},{'node':'Elevation','axis':'-X','degrees':[-8,25]},{'nodes':['Barrel.L','Barrel.R'],'axis':'+Y','recoil_BU':.17}],'interpolation':'Blender Bezier, rest pose frame 1','composition':'root > azimuth > hull > elevation > recoil'},'exports':[]})
deps=[str(ROOT/'Parts'/p/f'{p}.blend') for p in PARTS]
write(BLOCK/'validation.json',{'parts_saved_before_assembly':True,'part_count':len(PARTS),'instance_count':len(instances),'missing_dependencies':[p for p in deps if not Path(p).exists()],'unit_scales':all(x['scale']==[1,1,1] for x in instances),'rendered_poses':pose_results,'preview_views':['hero','top','rear'],'material_policy':'procedural; no external file textures','muzzle_geometry':'open annular mesh with recessed bore','mount_alignment':'bearing/hull/cradle/hatch/optic/guns coincide by local mount transforms','game_validation':False,'limitations':['Physical scale and game adapter unspecified','No game export, LOD or collision mesh','Pose renders require visual review; no automated collision certification']})
print('ASSEMBLY_READY',flush=True)
