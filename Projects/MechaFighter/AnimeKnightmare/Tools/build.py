import bpy, math, json, bmesh, os
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version = 0
def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').replace('\n','\r\n').encode('utf-8'))
def mat(n,c,metal=.5,emit=0):
    m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True
    s=m.node_tree.nodes.get('Principled BSDF'); s.inputs['Base Color'].default_value=(*c,1); s.inputs['Metallic'].default_value=metal; s.inputs['Roughness'].default_value=.32
    s.inputs['Emission Color'].default_value=(*c,1); s.inputs['Emission Strength'].default_value=emit
    return m
M={k:mat(k,c,me,em) for k,c,me,em in [('armor',(.85,.88,.91),.5,0),('trim',(.9,.57,.12),.75,0),('frame',(.035,.048,.065),.8,0),('silver',(.36,.43,.49),.85,0),('light',(.03,.9,.65),.3,4),('red',(.56,.025,.035),.5,0),('dark',(.055,.045,.12),.6,0)]}
parts={}; checks={}; current=None
def box(n,p,s,m='armor',r=(0,0,0),taper=.78):
    x,y,z=[v/2 for v in s]
    verts=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x*taper,-y*taper,z),(x*taper,-y*taper,z),(x*taper,y*taper,z),(-x*taper,y*taper,z)]
    mesh=bpy.data.meshes.new(n); mesh.from_pydata(verts,[],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]); mesh.update()
    o=bpy.data.objects.new(n,mesh); current.objects.link(o); o.location=p; o.rotation_euler=r; o.data.materials.append(M[m])
    be=o.modifiers.new('Machined edge highlights','BEVEL'); be.width=.025; be.segments=2
    o.modifiers.new('Weighted normals','WEIGHTED_NORMAL'); return o
def cyl(n,p,rad,depth,m='frame',axis='Z'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=rad,depth=depth,location=p)
    o=bpy.context.object; o.name=n
    for c in list(o.users_collection): c.objects.unlink(o)
    current.objects.link(o)
    if axis=='X': o.rotation_euler[1]=math.pi/2
    if axis=='Y': o.rotation_euler[0]=math.pi/2
    o.data.materials.append(M[m]); be=o.modifiers.new('Rim bevel','BEVEL'); be.width=.015; be.segments=2
    o.modifiers.new('Weighted normals','WEIGHTED_NORMAL'); return o
def rod(n,a,b,r=.035,m='silver'):
    a,b=Vector(a),Vector(b); o=cyl(n,(a+b)/2,r,(b-a).length,m); o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); return o
def start(n):
    global current
    current=bpy.data.collections.new(n); bpy.context.scene.collection.children.link(current); parts[n]=current
def finish(n):
    failures=[]
    for o in current.objects:
        bm=bmesh.new(); bm.from_mesh(o.data)
        if any(not e.is_manifold for e in bm.edges): failures.append(o.name+': nonmanifold')
        if any(f.calc_area()<1e-9 for f in bm.faces): failures.append(o.name+': degenerate')
        if bm.calc_volume(signed=True)<=0: failures.append(o.name+': normals')
        bm.free()
    if failures: raise RuntimeError(str(failures))
    checks[n]={'objects':len(current.objects),'closed_manifold':True,'positive_volume':True,'degenerate_faces':0}
    p=ROOT/'Parts'/n; p.mkdir(parents=True,exist_ok=True)
    if not os.environ.get('MF_ASSEMBLIES_ONLY'):
        bpy.data.libraries.write(str(p/(n+'.blend')),{current},fake_user=True)
        write(p/'part.json',{'id':n,'units':'meters','forward':'-Y','up':'+Z','mount':'local origin','validation':checks[n]})
start('Core')
box('Narrow waist',(0,0,0),(.68,.5,.5),'frame')
for z in [.0,.18,.36]: box('Abdominal segment',(0,-.25,z),(.67,.16,.14),'silver')
box('Chest cuirass',(0,0,.83),(1.32,.72,.9))
for s in [-1,1]:
    box('Pectoral layered plate',(s*.34,-.43,.9),(.61,.18,.55),r=(0,s*-.2,s*.12))
    box('Chest gold border',(s*.35,-.53,1.05),(.5,.06,.065),'trim')
    for i in range(4): box('Chest intake',(s*.35,-.545,.72+i*.055),(.31,.025,.025),'frame')
box('Sakura core lens',(0,-.46,1.12),(.19,.1,.22),'light')
box('Rear cockpit escape pod',(0,.58,.65),(.86,.72,.9),'frame')
box('Cockpit hatch',(0,.97,.7),(.68,.08,.65))
for s in [-1,1]: rod('Cockpit hinge',(s*.37,.98,.45),(s*.37,.98,.9))
cyl('Neck bearing',(0,0,1.42),.18,.25,'silver'); finish('Core')
start('Head')
box('Helmet',(0,0,0),(.48,.45,.5)); box('Face',(0,-.25,-.055),(.3,.1,.28),'frame')
box('Emerald visor',(0,-.31,.055),(.34,.045,.075),'light')
box('Chin',(0,-.29,-.2),(.14,.15,.19),'trim')
for s in [-1,1]:
    box('Cheek guard',(s*.22,-.14,-.1),(.11,.32,.36))
    rod('Antenna',(s*.2,0,.15),(s*.39,.06,.65),.027,'trim')
box('Central crest',(0,.015,.34),(.08,.3,.34),'trim'); finish('Head')
start('Shoulder')
cyl('Shoulder axle',(0,0,0),.23,.6,'silver','X')
box('Pauldron',(0,0,.22),(.78,.81,.46),r=(0,-.18,0))
for i in range(3): box('Overlapping shoulder lames',(.12+i*.12,0,.02-i*.12),(.32,.72,.23))
box('Shoulder trim',(0,-.42,.25),(.67,.05,.09),'trim')
for i in range(3): box('Rear shoulder vent',(0,.4,.13+i*.07),(.44,.03,.025),'frame')
finish('Shoulder')
start('Arm')
box('Upper arm frame',(0,0,-.3),(.29,.32,.64),'frame'); box('Bicep armor',(0,-.15,-.28),(.43,.3,.52))
cyl('Elbow',(0,0,-.67),.17,.46,'silver','X')
box('Forearm',(0,-.015,-1.02),(.48,.47,.63)); box('Forearm trim',(0,-.27,-1),(.31,.05,.4),'trim')
rod('Arm actuator',(.2,.2,-.3),(.2,.22,-1.12),.04)
box('Palm',(0,0,-1.49),(.31,.32,.28),'frame')
for i in range(4):
    box('Finger knuckle',(-.12+i*.08,-.19,-1.48),(.06,.14,.13),'silver')
    box('Finger tip',(-.12+i*.08,-.18,-1.61),(.06,.11,.12),'frame')
finish('Arm')
start('Leg')
cyl('Hip',(0,0,0),.22,.46,'silver','X'); box('Thigh frame',(0,0,-.42),(.34,.36,.78),'frame')
box('Thigh armor',(0,-.15,-.39),(.53,.38,.72))
cyl('Knee bearing',(0,0,-.91),.2,.56,'silver','X'); box('Knee shield',(0,-.27,-.91),(.46,.26,.4),'trim')
box('Long shin',(0,0,-1.48),(.53,.55,.94)); box('Shin inset',(0,-.31,-1.49),(.3,.09,.64),'frame')
for i in range(3): box('Shin light',(0,-.365,-1.22-i*.12),(.2,.035,.04),'light')
rod('Rear hydraulic',(.15,.3,-1.0),(.15,.32,-1.94),.045)
cyl('Ankle',(0,0,-2.06),.16,.45,'silver','X')
box('Pointed sabaton',(0,-.25,-2.26),(.57,1.02,.32)); box('Toe trim',(0,-.72,-2.24),(.46,.08,.13),'trim')
for s in [-1,1]:
    cyl('Landspinner wheel',(s*.27,.38,-2.16),.25,.12,'frame','X'); cyl('Wheel hub',(s*.34,.38,-2.16),.115,.03,'trim','X')
finish('Leg')
start('HipSkirt')
for s in [-1,1]:
    box('Front skirt',(s*.31,-.36,-.22),(.5,.22,.62),r=(0,s*-.15,0)); box('Skirt gold',(s*.31,-.49,-.2),(.33,.035,.07),'trim')
    box('Side skirt',(s*.6,0,-.18),(.26,.6,.58),r=(0,s*.22,0))
finish('HipSkirt')
start('Sword')
box('Hilt',(0,0,0),(.11,.13,.36),'frame'); box('Crossguard',(0,0,.22),(.48,.19,.1),'trim')
box('Vibration blade',(0,0,1.16),(.15,.07,1.8),'silver',taper=.05)
box('Luminous cutting edge',(-.08,-.015,1.15),(.035,.08,1.76),'light',taper=.02); finish('Sword')
start('Shield')
box('Shield frame',(0,0,0),(.75,.2,1.35),'frame',taper=.48); box('Shield armor',(0,-.13,.05),(.67,.15,1.22),taper=.45)
box('Shield cross',(0,-.23,.1),(.1,.07,.9),'trim'); box('Shield cross bar',(0,-.23,.36),(.5,.07,.09),'trim'); finish('Shield')
start('Claw')
box('Oversized gauntlet',(0,0,0),(.75,.65,.8),'red'); cyl('Radiation palm',(0,-.37,-.15),.24,.12,'light','Y')
for i in range(4):
    x=-.3+i*.2; rod('Claw first phalanx',(x,-.2,-.3),(x*1.35,-.28,-.75),.07)
    rod('Claw hooked tip',(x*1.35,-.28,-.75),(x,-.55,-.95),.045,'trim')
box('Claw capacitor',(0,.36,.1),(.5,.2,.4),'frame'); finish('Claw')
start('Cannon')
box('Receiver',(0,0,0),(.48,.7,.5),'dark'); cyl('Barrel',(0,-.8,0),.13,1.2,'silver','Y')
for i in range(4): cyl('Barrel cooling ring',(0,-.38-i*.23,0),.19,.09,'frame','Y')
box('Muzzle brake',(0,-1.5,0),(.32,.27,.29),'dark'); box('Bore',(0,-1.64,0),(.15,.02,.12),'frame')
box('Ammo pack',(.34,.05,-.06),(.22,.5,.44),'trim'); finish('Cannon')
start('Wing')
box('Wing root',(0,0,0),(.25,.35,1),'frame')
for i in range(4):
    box('Swept feather',(.45+i*.28,0,.12-i*.3),(.32,.16,1.45-i*.12),'dark',r=(0,.48,0),taper=.12)
    box('Energy feather',(.51+i*.28,-.1,.15-i*.3),(.1,.035,1.25-i*.12),'light',r=(0,.48,0),taper=.05)
finish('Wing')
start('Thruster')
box('Thruster housing',(0,0,0),(.45,.52,.75),'frame')
cyl('Nozzle',(0,.3,-.18),.19,.27,'silver','Y'); cyl('Nozzle glow',(0,.45,-.18),.13,.035,'light','Y')
for i in range(4): box('Cooling grille',(0,-.29,-.21+i*.13),(.3,.035,.045),'silver')
finish('Thruster')
# Templates are validated and saved before any robot instances are assembled.
for c in parts.values(): bpy.context.scene.collection.children.unlink(c)
def instance(part,n,p,rot=(0,0,0),scale=(1,1,1),palette=None):
    c=bpy.data.collections.new(n); bpy.context.scene.collection.children.link(c)
    root=bpy.data.objects.new(n+'_mount',None); c.objects.link(root); root.location=p; root.rotation_euler=rot; root.scale=scale
    for src in parts[part].objects:
        o=src.copy(); o.data=src.data
        if palette:
            o.data=src.data.copy()
            for slot in o.material_slots:
                if slot.material.name in palette: slot.material=palette[slot.material.name]
        c.objects.link(o); o.parent=root
    return root
def studio():
    global current
    current=bpy.data.collections.new('Studio'); bpy.context.scene.collection.children.link(current)
    floor=mat('Studio floor',(.025,.035,.055),.25)
    bpy.ops.mesh.primitive_plane_add(size=200); o=bpy.context.object; o.data.materials.append(floor)
    world=bpy.context.scene.world or bpy.data.worlds.new('World'); bpy.context.scene.world=world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.08,.1,.15,1)
    for p,power,size in [((3,-6,10),2200,7),((-6,-2,6),1600,6),((1,5,9),2600,5)]:
        bpy.ops.object.light_add(type='AREA',location=p); o=bpy.context.object; o.data.energy=power; o.data.shape='DISK'; o.data.size=size; o.rotation_euler=(Vector((0,0,2.5))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(8,-13,7.5)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,2.5))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=7.8; bpy.context.scene.camera=cam
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=24; sc.cycles.use_denoising=True; sc.render.resolution_x=1000; sc.render.resolution_y=1000; sc.render.resolution_percentage=100
    sc.view_settings.view_transform='AgX'
robots=[('MF-01_Aureole','Aureole',None,['Twin vibration swords','Forearm shield','Landspinner dash','Slash-wire launchers']),('MF-02_Kurenai','Kurenai',{'armor':M['red']},['Radiation claw','Thermal overload','Grapple dash','Close combat guard']),('MF-03_Obsidian','Obsidian',{'armor':M['dark'],'trim':M['silver']},['Twin shoulder cannons','Energy wings','Drone control concept','Barrier projection concept'])]
for rid,title,pal,abilities in robots:
    if os.environ.get('MF_ONLY') and rid not in os.environ['MF_ONLY'].split(','): continue
    for c in list(bpy.context.scene.collection.children): bpy.context.scene.collection.children.unlink(c)
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o,do_unlink=True)
    mounts=[]
    def put(part,n,p,r=(0,0,0),s=(1,1,1)):
        root=instance(part,n,p,r,s,pal); mounts.append({'part':part,'instance':n,'position':p,'rotation':r,'scale':s}); return root
    put('Core','Torso',(0,0,3.35)); put('Head','Head',(0,-.02,5.05)); put('HipSkirt','Pelvis',(0,0,3.3))
    for side in [-1,1]:
        put('Leg','Leg_'+str(side),(side*.43,0,2.45),s=(1,1,1))
        put('Shoulder','Shoulder_'+str(side),(side*.95,0,4.45),s=(side,1,1))
        put('Arm','Arm_'+str(side),(side*1.02,0,4.28),r=(0,side*-.09,side*-.08))
        put('Thruster','Back_thruster_'+str(side),(side*.48,.82,3.96))
        # visible independent hip cables and chest-launched grapple pods
        put('Thruster','Slashwire_'+str(side),(side*.64,-.08,3.55),s=(.42,.55,.55))
    if '01_' in rid:
        for side in [-1,1]: put('Sword','Sword_'+str(side),(side*1.17,-.38,2.72),r=(math.pi,-side*.3,0))
        put('Shield','Shield',(-1.3,-.36,3.29),s=(.75,.8,.8))
    if '02_' in rid:
        put('Claw','Radiation_claw',(1.16,-.15,2.96),s=(1.25,1.25,1.25)); put('Sword','Left_blade',(-1.2,-.38,2.68),r=(math.pi,.5,0),s=(.8,.8,.8))
        put('Shield','Left_guard',(-1.24,-.35,3.35),s=(.7,.8,.65))
    if '03_' in rid:
        for side in [-1,1]:
            put('Cannon','Shoulder_cannon_'+str(side),(side*.79,.2,4.92))
            put('Wing','Energy_wing_'+str(side),(side*.5,.94,4.3),r=(0,side*.22,0),s=(side,1,1))
    studio(); sc=bpy.context.scene; sc['robot_id']=rid; sc['abilities_design_only']=json.dumps(abilities)
    meshes=[o for o in sc.objects if o.type=='MESH' and o.name!='Plane']
    report={'robot':rid,'mesh_objects':len(meshes),'parts_prevalidated':True,'materials_embedded':True,'textures_external':0,'abilities_are_design_metadata':True,'animation':'Static articulated modules; no combat animation or game logic','instances':mounts}
    p=ROOT/'Blocks'/rid; p.mkdir(parents=True,exist_ok=True)
    write(p/'assembly.json',report)
    bpy.ops.wm.save_as_mainfile(filepath=str(p/(rid+'.blend')))
    sc.render.filepath=str(p/'preview.png'); bpy.ops.render.render(write_still=True)
    sc.camera.location=(-8,12,7); sc.camera.rotation_euler=(Vector((0,0,2.5))-sc.camera.location).to_track_quat('-Z','Y').to_euler(); sc.render.filepath=str(p/'rear.png'); bpy.ops.render.render(write_still=True)
write(ROOT/'part-validation.json',checks)
print('MECHAFIGHTER_BUILD_OK')
