"""Second design pass: authored faceted shells and three separate body families."""
import bpy, math, json, bmesh, os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
# Reuse only the existing project-local primitive/material helpers, not its models.
exec((ROOT/'Tools'/'build.py').read_text(encoding='utf-8').split("start('Core')")[0])
M['light'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=1.3
M['ruby']=mat('ruby',(.85,.035,.025),.5)
M['cyan']=mat('cyan',(.01,.4,.8),.45,1.2)
M['edge']=mat('edge',(.17,.2,.24),.8)
M['ivory']=mat('ivory',(.63,.69,.76),.55)

def mesh(n,verts,faces,p=(0,0,0),m='armor',r=(0,0,0),bevel=.006):
    me=bpy.data.meshes.new(n); me.from_pydata(verts,[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(n,me); current.objects.link(o); o.location=p; o.rotation_euler=r; me.materials.append(M[m])
    if bevel:
        b=o.modifiers.new('Fine edge glint','BEVEL'); b.width=bevel; b.segments=1
        o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
    return o

def panel(n,outline,p,m='armor',d=.1,ridge=.045,r=(0,0,0)):
    # Authored convex XZ outline, separate planar facets meeting a raised spine.
    count=len(outline); cx=sum(v[0] for v in outline)/count; cz=sum(v[1] for v in outline)/count
    vs=[(x,d/2,z) for x,z in outline]+[(x,-d/2,z) for x,z in outline]+[(cx,-d/2-ridge,cz)]
    fs=[tuple(range(count-1,-1,-1))]
    for i in range(count):
        j=(i+1)%count; fs.append((i,j,count+j,count+i)); fs.append((count+i,count+j,2*count))
    return mesh(n,vs,fs,p,m,r)

def shell(n,rings,m='armor',p=(0,0,0)):
    # Octagonal loft; rings describe z, half-width, half-depth, forward offset.
    vs=[]
    shape=[(-.65,-1),(.65,-1),(1,-.5),(1,.5),(.65,1),(-.65,1),(-1,.5),(-1,-.5)]
    for z,w,d,cy in rings: vs.extend((a*w,b*d+cy,z) for a,b in shape)
    fs=[tuple(range(7,-1,-1))]
    for k in range(len(rings)-1):
        for i in range(8): j=(i+1)%8; fs.append((k*8+i,k*8+j,(k+1)*8+j,(k+1)*8+i))
    fs.append(tuple((len(rings)-1)*8+i for i in range(8)))
    return mesh(n,vs,fs,p,m)

def blade(n,a,b,w=.07,m='trim'):
    a,b=Vector(a),Vector(b); length=(b-a).length
    o=shell(n,[(0,w,w*.65,0),(length*.2,w*.8,w*.48,0),(length,w*.025,w*.025,0)],m,p=a)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); return o

def fasteners(x,y,z,span=.15):
    for s in [-1,1]: cyl('Recessed titanium fastener',(x+s*span,y,z),.019,.013,'silver','Y')

def vents(x,y,z,w=.16,count=5):
    for i in range(count):
        o=box('Recessed heat exchanger',(x,y,z+i*.042),(w,.035,.019),'frame'); o.modifiers['Machined edge highlights'].width=.003

def seam(a,b,m='edge',rad=.008): rod('Armor panel scribe',a,b,rad,m)

def detail_panel(n,outline,p,m='armor',d=.08,ridge=.035):
    panel(n+' gasket',[(x*1.07,z*1.035) for x,z in outline],(p[0],p[1]+.018,p[2]),'frame',d+.025,ridge)
    return panel(n,outline,p,m,d,ridge)

def complete(n):
    finish(n)
    # Part-local checks are recorded before any assembly uses this library.
    print('PART_VALIDATED',n,len(current.objects),flush=True)

def specialize(v,kind):
    if v=='A': return
    if kind=='Core':
        remove=('Chest swept facet','Pectoral inlay','Sternum spear','Core slit','Signature ')
        for o in list(current.objects):
            if o.name.startswith(remove): bpy.data.objects.remove(o,do_unlink=True)
        if v=='K':
            detail_panel('Signature predator breast',[(-.47,.2),(-.22,.34),(.31,.23),(.44,.03),(.12,-.32),(-.3,-.2)],(0,-.39,.86),'red',.1,.11)
            panel('Signature reactor inset',[(-.16,.08),(.1,.13),(.18,-.04),(-.06,-.15),(-.17,-.05)],(0,-.57,.86),'frame',.025,.02)
            panel('Signature reactor diamond',[(-.05,.035),(.03,.065),(.07,-.025),(-.025,-.07)],(0,-.61,.86),'light',.015,.003)
            for s in [-1,1]:
                blade('Signature rib fang',(s*.39,-.4,.89),(s*.21,-.41,.5),.035,'silver')
                fasteners(s*.28,-.52,1.03,.055)
        else:
            for s in [-1,1]:
                detail_panel('Signature imperial cuirass',[(s*.03,.25),(s*.53,.3),(s*.64,.05),(s*.19,-.32),(s*.045,-.15)],(0,-.36,.88),'dark',.16,.11)
                blade('Signature breast rim',(s*.08,-.56,1.14),(s*.54,-.56,1.16),.025,'silver')
                panel('Signature cyan aperture',[(s*.07,.04),(s*.41,.07),(s*.34,-.025),(s*.09,-.05)],(0,-.57,.96),'cyan',.02,.003)
                vents(s*.32,-.52,.74,.16,3)
            blade('Signature central breast keel',(0,-.44,1.12),(0,-.48,.48),.075,'silver')
    if kind=='Leg':
        for o in list(current.objects):
            if o.name.startswith('Signature '): bpy.data.objects.remove(o,do_unlink=True)
        if v=='K':
            for s in [-1,1]:
                panel('Signature swept calf',[(-.08,.31),(.12,.4),(.25,.12),(.11,-.46),(-.07,-.32)],(s*.16,.04,-1.8),'red',.25,.045)
                blade('Signature heel spur',(s*.12,.23,-2.24),(s*.19,.66,-2.48),.055,'silver')
            blade('Signature knee fang',(0,-.28,-1.17),(0,-.36,-1.66),.065,'silver')
        else:
            for s in [-1,1]:
                panel('Signature flared greave',[(-.1,.22),(.17,.47),(.31,.12),(.12,-.58),(-.08,-.32)],(s*.19,.0,-1.83),'dark',.34,.07)
                blade('Signature greave crest',(s*.24,.06,-1.69),(s*.42,.11,-1.18),.065,'silver')
                fasteners(s*.21,-.23,-1.7,.04)

# Preserve unchanged weapon and engine source files. Load existing collections.
for name in ['Sword','Cannon','Thruster']:
    with bpy.data.libraries.load(str(ROOT/'Parts'/name/(name+'.blend')),link=False) as (src,dst): dst.collections=[name]
    parts[name]=dst.collections[0]
    checks[name]={'reused_unchanged':True,'source':'Parts/'+name+'/'+name+'.blend'}

for v in ['A','K','O']:
    dark=v=='O'; red=v=='K'; base='dark' if dark else ('red' if red else 'armor')
    accent='silver' if dark else 'trim'; glow='cyan' if dark else 'light'
    name='Core_'+v; start(name)
    shell('Tapered rib cage',[(-.04,.21,.19,0),(.42,.32,.26,0),(.9,.61 if dark else .49,.31,0),(1.15,.52 if dark else .4,.22,0)],'frame')
    shell('Sculpted breastplate',[(.35,.29,.22,-.02),(.7,.58 if dark else .46,.32,-.015),(.94,.64 if dark else .51,.3,0),(1.14,.43,.22,0)],base)
    # Strong chest arrow and central keel, not a flat rectangular cuirass.
    outline=[(-.48,.12),(-.15,.27),(.03,.04),(-.12,-.19),(-.4,-.09)]
    for s in [-1,1]:
        shape=[(s*x,z) for x,z in outline]
        detail_panel('Chest swept facet',shape,(0,-.32,.88),base,.075,.075)
        panel('Pectoral inlay',[(s*x,z*.2) for x,z in outline],(0,-.405,1.02),accent,.025,.008)
        vents(s*.34,-.365,.68,.14,4)
        fasteners(s*.33,-.405,.93,.07)
        blade('Collar blade',(s*.25,0,1.09),(s*.52,.06,1.35),.065,base)
        rod('Exposed abdominal strut',(s*.2,.02,.1),(s*.31,.03,.47),.035,'silver')
        for i in range(3): cyl('Waist rotating bearing',(s*.2,.05,.15+i*.09),.048,.055,'frame','X')
    panel('Sternum spear',[(-.09,.24),(.09,.24),(.13,.04),(0,-.23),(-.13,.04)],(0,-.38,.84),accent,.08,.06)
    panel('Core slit',[(-.035,.12),(.035,.12),(.045,-.035),(0,-.1),(-.045,-.035)],(0,-.495,.88),glow,.014,.002)
    for i in range(4):
        panel('Floating abdominal lamella',[(-.22,.055),(.22,.055),(.18,-.045),(0,-.085),(-.18,-.045)],(0,-.22,.07+i*.09),'ivory' if not red and not dark else base,.045,.02)
    shell('Cockpit pod',[(.24,.25,.22,.37),(.45,.37,.42,.42),(.98,.3,.39,.36),(1.14,.22,.2,.32)],'frame')
    panel('Angular escape hatch',[(-.27,.22),(.27,.22),(.3,-.1),(0,-.37),(-.3,-.1)],(0,.83,.72),base,.12,.03,r=(0,0,math.pi))
    for s in [-1,1]: rod('Hatch locking piston',(s*.25,.7,.35),(s*.25,.73,.9),.025)
    cyl('Neck gimbal',(0,0,1.23),.12,.22,'silver'); specialize(v,'Core'); complete(name)

    name='Head_'+v; start(name)
    if v=='A':
        shell('Knight helmet',[(-.22,.12,.12,-.015),(-.06,.21,.18,0),(.19,.18,.18,.02),(.3,.07,.12,.03)],base)
        for s in [-1,1]:
            panel('Blade cheek',[(s*.08,.08),(s*.2,.16),(s*.23,-.13),(s*.1,-.27)],(0,-.19,0),base,.055,.03)
            blade('V fin',(s*.08,-.06,.21),(s*.48,-.09,.55),.047,accent)
            panel('Eye slit',[(s*.025,.035),(s*.17,.07),(s*.14,.005),(s*.04,-.01)],(0,-.22,.025),glow,.018,.001)
        blade('Nose spear',(0,-.235,.06),(0,-.275,-.18),.055,accent)
    elif v=='K':
        shell('Predator helmet',[(-.19,.12,.14,0),(-.02,.22,.21,0),(.16,.25,.2,.035),(.24,.12,.15,.07)],base)
        panel('Black slanted visor',[(-.21,.07),(.21,.1),(.14,-.055),(-.12,-.065)],(0,-.21,.015),'frame',.06,.035)
        panel('Mono eye',[(-.09,.025),(.09,.045),(.065,-.02),(-.06,-.03)],(0,-.28,.035),glow,.015,.001)
        for s in [-1,1]: blade('Swept cheek horn',(s*.17,0,.04),(s*.38,.1,.37),.075,base)
        blade('Commander dorsal crest',(0,.05,.18),(0,.23,.62),.085,accent)
    else:
        shell('Crowned command mask',[(-.23,.1,.11,0),(-.06,.24,.19,0),(.22,.22,.21,.03),(.36,.1,.12,.03)],base)
        for s in [-1,1]:
            blade('Crown blade',(s*.11,0,.23),(s*.3,.08,.65),.065,accent)
            panel('Mask flank',[(s*.05,.19),(s*.21,.1),(s*.2,-.1),(s*.06,-.27)],(0,-.22,0),base,.06,.035)
            panel('Optical slit',[(s*.025,.03),(s*.17,.07),(s*.13,.0),(s*.03,-.015)],(0,-.28,.045),glow,.012,.001)
        blade('Center diadem',(0,0,.3),(0,-.02,.79),.045,accent)
    for s in [-1,1]:
        cyl('Ear sensor bezel',(s*.2,.02,-.01),.07,.03,'silver','X')
        vents(s*.13,.16,-.07,.075,3)
    complete(name)

    name='Shoulder_'+v; start(name)
    cyl('Shoulder bearing',(0,0,0),.16,.43,'silver','X')
    if v=='A': outline=[(-.22,.22),(.22,.33),(.78,.02),(.26,-.12),(-.2,-.06)]
    elif v=='K': outline=[(-.22,.16),(.12,.36),(.57,.18),(.38,-.32),(.04,-.12),(-.23,-.08)]
    else: outline=[(-.25,.27),(.16,.68),(.7,.8),(.49,.1),(.26,-.25),(-.2,-.12)]
    detail_panel('Spear pauldron',outline,(0,-.03,.12),base,.5,.15)
    for i in range(3):
        panel('Independent pointed shoulder lame',[(-.13,.08),(.26,.13),(.41,-.16),(.04,-.19),(-.15,-.04)],(.12+i*.07,-.1,-.12-i*.13),base,.36,.04)
    blade('Shoulder rim',(-.18,-.32,.29),(.58,-.3,.16),.02,accent)
    vents(.13,.29,.05,.2,5); fasteners(.11,-.37,.18,.1)
    if dark:
        for i in range(3): blade('Command armor spike',(.17+i*.12,.14,.6),(.45+i*.18,.22,.96+i*.08),.045,accent)
    complete(name)

    name='Arm_'+v; start(name)
    shell('Upper arm',[(-.58,.11,.1,0),(-.34,.15,.14,0),(-.08,.13,.13,0)],'frame')
    detail_panel('Bicep blade',[(-.14,.2),(.15,.15),(.17,-.11),(0,-.32),(-.14,-.16)],(0,-.12,-.28),base,.14,.045)
    cyl('Elbow gimbal',(0,0,-.68),.13,.33,'silver','X')
    shell('Tapered forearm',[(-1.28,.095,.12,0),(-1.13,.16,.19,0),(-.8,.22 if red else .17,.21,0),(-.72,.13,.14,0)],base)
    detail_panel('Forearm knife plate',[(-.17,.25),(.16,.19),(.13,-.16),(0,-.43),(-.13,-.18)],(0,-.19,-.97),base,.08,.065)
    blade('Forearm filigree',(-.1,-.27,-.77),(0,-.285,-1.24),.018,accent)
    for s in [-1,1]: rod('Twin wrist actuator',(s*.1,.13,-.84),(s*.075,.11,-1.3),.022)
    vents(0,.2,-1.08,.13,5)
    shell('Armored palm',[(-1.53,.105,.115,0),(-1.36,.12,.13,0)],'frame')
    for i in range(4):
        x=-.09+i*.06
        for j in range(3):
            o=box('Articulated finger',(x,-.13+j*.035,-1.48-j*.055),(.045,.07,.055),'silver' if j==0 else 'frame'); o.modifiers['Machined edge highlights'].width=.008
    rod('Thumb',( .13,-.02,-1.4),(.16,-.16,-1.49),.035,'silver')
    fasteners(0,-.255,-.88,.09); complete(name)

    name='Leg_'+v; start(name)
    cyl('Hip ball bearing',(0,0,0),.15,.33,'silver','X')
    shell('Exposed femur',[(-1.06,.095,.11,.01),(-.45,.12,.12,0),(-.05,.11,.12,0)],'frame')
    profile=[(-.18,.36),(.16,.28),(.21,-.02),(.08,-.45),(-.1,-.39),(-.19,-.12)]
    detail_panel('Long tapered thigh',profile,(0,-.1,-.48),base,.25,.075)
    for s in [-1,1]:
        rod('Femur tension rod',(s*.11,.14,-.19),(s*.095,.15,-.95),.025)
        cyl('Hip fastener',(s*.17,-.05,-.2),.04,.025,'silver','X')
    cyl('Knee bearing',(0,0,-1.1),.145,.35,'silver','X')
    detail_panel('Pointed knee shield',[(-.19,.13),(0,.28),(.19,.13),(.13,-.15),(0,-.39),(-.13,-.15)],(0,-.21,-1.1),accent,.14,.065)
    shell('Sculpted greave',[(-2.43,.105,.12,.01),(-2.15,.14,.18,.02),(-1.59,.2 if not dark else .26,.23,.05),(-1.3,.17,.17,.03)],base)
    detail_panel('Shin dagger',[(-.12,.31),(.14,.27),(.17,-.09),(0,-.64),(-.09,-.37)],(0,-.18,-1.72),base,.09,.09)
    panel('Shin highlight',[(-.025,.25),(.025,.24),(.04,-.03),(0,-.4),(-.02,-.27)],(0,-.33,-1.72),accent,.018,.006)
    for s in [-1,1]:
        rod('Calf piston barrel',(s*.11,.23,-1.37),(s*.11,.24,-1.94),.042,'frame')
        rod('Calf piston ram',(s*.11,.24,-1.94),(s*.095,.22,-2.42),.023,'silver')
    vents(0,.26,-1.72,.17,6)
    cyl('Ankle articulation',(0,0,-2.48),.115,.3,'silver','X')
    shell('Sabaton heel',[(-2.76,.16,.24,.02),(-2.57,.14,.23,.02)],'frame')
    # Foot planform is a pointed diamond, rather than a rectangular shoe.
    o=panel('Lance toe',[(-.16,.28),(.16,.28),(.17,-.21),(0,-.72),(-.17,-.21)],(0,-.18,-2.63),base,.2,.055,r=(-math.pi/2,0,0))
    for s in [-1,1]:
        cyl('Landspinner tire',(s*.19,.36,-2.55),.2,.085,'frame','X')
        cyl('Wheel rim',(s*.24,.36,-2.55),.125,.025,'silver','X')
        cyl('Hub jewel',(s*.255,.36,-2.55),.055,.03,accent,'X')
        rod('Landspinner swingarm',(s*.18,.11,-2.3),(s*.18,.37,-2.54),.035,base)
    specialize(v,'Leg'); complete(name)

    name='Skirt_'+v; start(name)
    shell('Pelvis yoke',[(-.16,.31,.22,0),(.12,.27,.19,0)],'frame')
    for s in [-1,1]:
        length=.58 if v=='A' else (.38 if red else .86)
        detail_panel('Split fauld',[(-.14,.09),(.16,.12),(.24,-length*.4),(.03,-length),(-.13,-length*.7)],(s*.25,-.26,-.04),base,.09,.045)
        blade('Fauld inlay',(s*.25,-.36,-.02),(s*.25+.025,-.36,-length*.8),.015,accent)
        panel('Swept hip fin',[(s*-.09,.1),(s*.19,.24),(s*.52,-.3),(s*.2,-.56),(s*-.04,-.17)],(s*.34,.02,-.05),base,.22,.07)
        fasteners(s*.25,-.34,-.13,.06)
    complete(name)

# Rework the three distinctive equipment parts, retaining original IDs.
start('Claw')
shell('Radiation gauntlet',[(-.5,.17,.18,0),(-.18,.38,.32,0),(.24,.32,.28,0),(.4,.18,.18,0)],'silver')
for s in [-1,1]:
    panel('Claw carapace',[(s*.09,.28),(s*.32,.22),(s*.43,-.28),(s*.2,-.51),(s*.07,-.18)],(0,-.23,0),'red',.12,.09)
    rod('Gauntlet power piston',(s*.24,.23,.2),(s*.3,.25,-.4),.045,'frame')
cyl('Radiation emitter cage',(0,-.33,-.15),.23,.09,'frame','Y')
cyl('Radiation emitter',(0,-.39,-.15),.17,.055,'light','Y')
for i in range(5):
    x=-.3+i*.15; a=(x,-.05,-.36); b=(x*1.38,-.17,-.8); c=(x*1.19,-.39,-1.02)
    cyl('Claw root knuckle',a,.065,.12,'frame','Y')
    rod('Finger hydraulic',a,b,.032,'silver'); blade('Claw armored phalanx',a,b,.075,'silver'); blade('Curved talon',b,c,.06,'silver')
    blade('Talon point',c,(x*.85,-.53,-1.07),.04,'trim')
for i in range(6): cyl('Emitter retaining bolt',(.2*math.cos(i*math.tau/6),-.39,-.15+.2*math.sin(i*math.tau/6)),.017,.02,'trim','Y')
complete('Claw')
start('Shield')
outline=[(-.18,.7),(.19,.7),(.37,.31),(.18,-.36),(0,-.85),(-.23,-.31),(-.33,.26)]
detail_panel('Lance shield',outline,(0,0,0),'armor',.13,.12)
blade('Shield gold spine',(0,-.2,.58),(0,-.2,-.67),.027,'trim')
for s in [-1,1]:
    panel('Shield incision',[(s*.06,.3),(s*.22,.2),(s*.13,-.15),(s*.06,-.29)],(0,-.17,0),'ivory',.025,.01)
    fasteners(s*.15,-.18,.44,.035)
complete('Shield')
start('Wing')
shell('Flight root',[(-.3,.12,.16,0),(.45,.16,.2,0),(.8,.06,.1,0)],'frame')
for i in range(5):
    x=.17+i*.22; z=.3-i*.23
    outline=[(-.1,.15),(.12,.28),(.95+i*.08,1.27-i*.08),(.72+i*.07,.62),(.12,-.26)]
    panel('Razor flight feather',outline,(x,0,z),'dark',.09,.025)
    panel('Energy membrane',[(.13,.17),(.84+i*.08,1.12-i*.08),(.61+i*.07,.55),(.13,-.09)],(x,-.075,z),'cyan',.015,.001)
    rod('Feather hinge',(x,0,z-.1),(x+.18,0,z+.16),.024,'silver')
complete('Wing')

write(ROOT/'part-validation-v2.json',checks)
for c in list(bpy.context.scene.collection.children): bpy.context.scene.collection.children.unlink(c)

def put(part,n,p,r=(0,0,0),s=(1,1,1)):
    c=bpy.data.collections.new(n); bpy.context.scene.collection.children.link(c)
    root=bpy.data.objects.new(n+'_mount',None); c.objects.link(root); root.location=p; root.rotation_euler=r; root.scale=s
    for src in parts[part].objects:
        o=src.copy(); o.data=src.data; c.objects.link(o); o.parent=root
    mounts.append({'part':part,'instance':n,'position':p,'rotation':r,'scale':s})
    return root

def studio():
    sc=bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=200); bpy.context.object.name='Studio_floor'; bpy.context.object.data.materials.append(mat('Studio floor',(.025,.035,.05),.25))
    sc.world=bpy.data.worlds.new('Studio world'); sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.22,1)
    for p,e,size in [((3,-6,11),1900,6),((-6,-2,7),1700,5),((1,5,10),2600,5)]:
        bpy.ops.object.light_add(type='AREA',location=p); o=bpy.context.object; o.data.energy=e; o.data.shape='DISK'; o.data.size=size; o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(8,-15,7)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,3.1))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=8.2; sc.camera=cam
    sc.render.engine='CYCLES'; sc.cycles.samples=24; sc.cycles.use_denoising=True; sc.render.resolution_x=1100; sc.render.resolution_y=1100; sc.render.resolution_percentage=100; sc.view_settings.view_transform='AgX'

ids={'A':'MF-01_Aureole','K':'MF-02_Kurenai','O':'MF-03_Obsidian'}
for v,rid in ids.items():
    if os.getenv('MF_ONLY') and rid not in os.environ['MF_ONLY'].split(','): continue
    for c in list(bpy.context.scene.collection.children): bpy.context.scene.collection.children.unlink(c)
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o,do_unlink=True)
    mounts=[]; wide=1.12 if v=='O' else (1.04 if v=='K' else .91)
    put('Core_'+v,'Torso',(0,0,3.75),s=(wide,1,1))
    put('Head_'+v,'Head',(0,-.015,5.2))
    put('Skirt_'+v,'Pelvis',(0,0,3.69),s=(wide,1,1))
    for side in [-1,1]:
        put('Leg_'+v,'Leg_'+str(side),(side*(.53 if v=='O' else .36),0,2.81),r=(0,-side*.025,0),s=(1.12 if v=='O' else .92,1,1))
        # Strongly distinct shoulder layout, with an intentionally asymmetric Kurenai.
        shoulderx=(.96 if v=='O' else .8)*side
        sz=4.84+(.12 if v=='K' and side==1 else 0)
        put('Shoulder_'+v,'Shoulder_'+str(side),(shoulderx,0,sz),s=(side*(1.18 if v=='K' and side==1 else 1),1,1))
        put('Arm_'+v,'Arm_'+str(side),(side*(.98 if v=='O' else .83),0,4.66),r=(0,-side*.12,-side*.075))
        put('Thruster','Back_thruster_'+str(side),(side*.34,.77,4.25),s=(.75,.8,.85))
    if v=='A':
        for side in [-1,1]: put('Sword','Sword_'+str(side),(side*1.05,-.38,3.04),r=(math.pi,-side*.27,0),s=(.85,.8,1))
        put('Shield','Left_shield',(-1.03,-.42,3.76),s=(.85,1,.86))
    if v=='K':
        put('Claw','Radiation_claw',(1.04,-.18,3.48),r=(0,-.12,0),s=(1.15,1.15,1.15))
        put('Sword','Left_blade',(-1.02,-.36,3.04),r=(math.pi,.45,0),s=(.85,.85,.8))
        # Asymmetric swept backpack fins, built into an independent small collection.
        put('Wing','Single_flight_fin',(-.32,.8,4.18),r=(0,-.18,0),s=(-.5,.7,.6))
    if v=='O':
        for side in [-1,1]:
            put('Cannon','Dorsal_cannon_'+str(side),(side*.71,.38,5.05),r=(-.12,0,-side*.07),s=(.85,1.1,.85))
            put('Wing','Royal_wing_'+str(side),(side*.45,.93,4.55),r=(0,side*.2,0),s=(side,1,1))
    studio(); sc=bpy.context.scene; sc['robot_id']=rid; sc['design_revision']=2
    old=json.loads((ROOT/'Blocks'/rid/'assembly.json').read_text(encoding='utf-8'))
    old.update({'revision':2,'instances':mounts,'mesh_objects':sum(o.type=='MESH' and o.name!='Studio_floor' for o in sc.objects),'distinct_body_family':v,'parts_prevalidated':True,'validation':'part-validation-v2.json'})
    p=ROOT/'Blocks'/rid; write(p/'assembly.json',old)
    bpy.ops.wm.save_as_mainfile(filepath=str(p/(rid+'.blend')))
    sc.render.filepath=str(p/'preview.png'); bpy.ops.render.render(write_still=True)
    sc.camera.location=(-8,13,7.5); sc.camera.rotation_euler=(Vector((0,0,3.1))-sc.camera.location).to_track_quat('-Z','Y').to_euler(); sc.render.filepath=str(p/'rear.png'); bpy.ops.render.render(write_still=True)
print('MECHAFIGHTER_REFINEMENT_OK',flush=True)
