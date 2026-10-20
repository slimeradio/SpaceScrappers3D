"""MilitaryArmor 1.3: orbital artillery, split accelerator housings and swept armor."""
import bpy, bmesh, math

def build_orbital(g,pid):
    box,cyl,ring,label=(g[k] for k in ('box','cyl','ring','label'))
    coll,mats=g['coll'],g['mats']
    for name,color,metal,rough,emission in [('Ceramic',(.38,.43,.46),.38,.32,0),('Titanium',(.075,.105,.13),.84,.30,0),('Signal',(.015,.55,.78),.35,.25,2.5),('Optic',(.015,.18,.25),.65,.18,.7)]:
        m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
        if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
        mats[name]=m
    for m in (mats['Armor'],mats['Steel']):
        for n in m.node_tree.nodes:
            if n.type=='BUMP':n.inputs['Strength'].default_value=.055;n.inputs['Distance'].default_value=.004

    def mesh(name,verts,faces,mat='Armor',bevel=.018):
        data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        o=bpy.data.objects.new(name,data);coll.objects.link(o);data.materials.append(mats[mat]);o['shape_revision']='1.3 / orbital'
        if len(faces)==1:
            mod=o.modifiers.new('Armor skin thickness','SOLIDIFY');mod.thickness=.022
        if bevel:
            mod=o.modifiers.new('Micro edge radius','BEVEL');mod.width=bevel;mod.segments=2
            o.modifiers.new('Weighted planar normals','WEIGHTED_NORMAL')
        return o

    def outline(w,h,c):
        c=min(c,w*.36,h*.36)
        return [(-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)]

    def section_body(name,sections,mat='Armor',bevel=.018):
        # Eight-sided transverse rings, forward along -Y. Origin remains local.
        v=[]
        for y,x,z,w,h,c in sections:
            v.extend((u+x,y,t+z) for u,t in outline(w,h,c))
        f=[tuple(reversed(range(8))),tuple(range((len(sections)-1)*8,len(sections)*8))]
        for j in range(len(sections)-1):
            for i in range(8):k=(i+1)%8;f.append((8*j+i,8*j+k,8*(j+1)+k,8*(j+1)+i))
        return mesh(name,v,f,mat,bevel)

    def slab(name,points,z,thick,mat='Armor',bevel=.015):
        v=[(x,y,z) for x,y in points]+[(x,y,z+thick) for x,y in points];n=len(points)
        f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        return mesh(name,v,f,mat,bevel)

    def panel(name,loc,size,mat='Armor',cut=.12):
        x,y,z=loc;w,d,h=size
        pts=outline(w,d,min(cut,w*.3,d*.3))
        return slab(name,[(x+a,y+b) for a,b in pts],z-h/2,h,mat)

    def stripe(name,a,b,width=.025,mat='Signal'):
        from mathutils import Vector
        a,b=Vector(a),Vector(b);delta=b-a
        o=box(name,(a+b)/2,(width,width,delta.length),mat,.004);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return o

    def flush_fastener(x,y,z):
        cyl('Flush quarter turn lock',(x,y,z),.024,.008,'Titanium',verts=8)

    if pid=='MA-P01':
        plan=[(-1.45,-2.06),(1.45,-2.06),(2.35,-1.13),(2.35,.97),(1.36,1.97),(-1.36,1.97),(-2.35,.97),(-2.35,-1.13)]
        slab('Octagonal anchor keel',[(x*.94,y*.94) for x,y in plan],0,.25,'Dark')
        slab('Orbital hardpoint foundation',plan,.25,.48,'Armor',.045)
        slab('Inset upper interface',[(x*.87,y*.87) for x,y in plan],.73,.15,'Titanium')
        ring('Turret interface collar',(0,0,.92),1.77,1.48,.16,'Z','Dark')
        for s in [-1,1]:
            # Swept detachable cheek pieces, generous diagonal corners.
            slab('Diagonal structural outrigger',[(s*1.17,-1.87),(s*1.50,-1.88),(s*2.21,-1.10),(s*2.21,-.54),(s*1.89,-.54)],.45,.38,'Ceramic')
            slab('Aft structural outrigger',[(s*1.40,1.78),(s*2.21,.97),(s*2.21,.35),(s*1.90,.35),(s*1.13,1.59)],.45,.38,'Ceramic')
            for y in [-.28,.21]:
                # Side capacitive service interfaces, no ground-vehicle grilles.
                box('Capacitor interface recess',(s*2.365,y,.48),(.035,.34,.15),'Dark',.015)
                box('Capacitor interface luminous insert',(s*2.388,y,.48),(.014,.20,.022),'Signal',.004)
            stripe('Diagonal interface indicator',(s*1.51,-1.874,.842),(s*2.11,-1.24,.842),.026)
            panel('Docking foot',(s*1.83,.79,.31),(.69,.74,.18),'Titanium',.20)
            panel('Recessed deck service cover',(s*1.81,-.05,.88),(.35,.78,.035),'Armor',.08)
            for y in [-.32,.24]:flush_fastener(s*1.81,y,.905)
        box('Forward interface recess',(0,-2.075,.51),(2.15,.035,.17),'Dark',.02)
        for x in [-.73,.73]:box('Forward status segment',(x,-2.099,.51),(.44,.015,.023),'Signal',.004)
        label('ORBITAL DEFENSE / MA-03',(-.80,-2.106,.64),.078)
        label('HARDPOINT INTERFACE',(-.59,-2.106,.35),.057)

    elif pid=='MA-P02':
        cyl('Direct drive stator',(0,0,.22),1.53,.42,'Dark',verts=64)
        ring('Precision azimuth track',(0,0,.12),1.66,1.43,.18,'Z','Titanium')
        ring('Upper azimuth seat',(0,0,.52),1.54,1.33,.18,'Z','Titanium')
        for i in range(12):
            a=i*math.pi/6
            o=panel('Segmented motor shield',(1.48*math.cos(a),1.48*math.sin(a),.32),(.32,.49,.25),'Armor',.10);o.rotation_euler.z=a
            o=box('Azimuth index',(1.66*math.cos(a),1.66*math.sin(a),.22),(.027,.16,.025),'Signal',.005);o.rotation_euler.z=a
        for x in [-.69,.69]:
            panel('Upper torque transfer pad',(x,.45,.57),(.50,.69,.08),'Dark',.16)

    elif pid=='MA-P03':
        section_body('Swept structural core',[(-1.16,0,.45,2.55,.58,.20),(.15,0,.58,3.0,.95,.28),(1.31,0,.67,2.72,1.10,.30),(1.59,0,.73,1.82,.65,.20)],'Dark')
        for s in [-1,1]:
            section_body('Swept armored shoulder',[(-1.57,s*1.36,.60,.52,.49,.13),(-.57,s*1.52,.70,.97,1.10,.23),(.75,s*1.42,.76,1.03,1.16,.24),(1.43,s*1.20,.78,.69,.85,.20)],'Armor',.025)
            # A broad faceted outer skin, wrapped around a graphite insert.
            v=[(s*2.025,-.56,.49),(s*1.91,.75,.52),(s*1.65,1.28,.68),(s*1.70,1.12,1.02),(s*1.91,.62,1.20),(s*2.025,-.42,1.06)]
            mesh('Swept ceramic flank skin',v,[(0,1,2,3,4,5)],'Ceramic',0)
            # Dark technological recess sits proud of the shell by a tiny offset.
            v=[(s*2.043,-.30,.64),(s*1.956,.57,.65),(s*1.946,.65,.85),(s*2.043,-.26,.87)]
            mesh('Lateral coolant channel',v,[(0,1,2,3)],'Dark',0)
            stripe('Coolant channel light',(s*2.047,-.19,.72),(s*1.966,.49,.73),.023)
            # Long ridge folds replace the row of square armor plates.
            section_body('Swept dorsal shoulder cap',[(-.94,s*1.36,1.08,.40,.10,.035),(-.40,s*1.46,1.28,.57,.13,.05),(.74,s*1.35,1.36,.57,.12,.05),(1.24,s*1.12,1.20,.34,.12,.05)],'Ceramic')
            stripe('Dorsal diagnostic trace',(s*1.41,-.32,1.357),(s*1.30,.61,1.427),.014,'Titanium')
            # Front wedge optical ranging slit.
            box('Shoulder ranging recess',(s*1.36,-1.585,.66),(.30,.028,.075),'Dark',.014)
            box('Shoulder ranging lens',(s*1.36,-1.606,.66),(.20,.012,.025),'Optic',.004)
        slab('Tapered upper bridge',[(-.87,-.19),(.87,-.19),(1.17,.50),(.90,1.38),(-.90,1.38),(-1.17,.50)],1.10,.20,'Armor',.025)
        slab('Dorsal flush spine',[(-.31,-.14),(.31,-.14),(.47,.70),(.26,1.28),(-.26,1.28),(-.47,.70)],1.301,.032,'Titanium')
        for s in [-1,1]:
            stripe('Spine recessed signal',(s*.36,.10,1.337),(s*.36,.45,1.337),.018)
        # Closed, segmented radiators on the aft face, inset in a tapered pod.
        section_body('Aft thermal manifold',[(1.32,0,.78,1.91,.57,.15),(1.58,0,.80,1.60,.39,.12)],'Titanium')
        for x in [-.55,-.33,-.11,.11,.33,.55]:box('Thermal manifold ceramic segment',(x,1.591,.80),(.13,.032,.23),'Ceramic',.015)
        label('MA-03',(-.22,-.201,1.315),.09,(0,0,0))

    elif pid=='MA-P04':
        section_body('Common elevation yoke',[(-.64,0,0,2.10,.65,.16),(.36,0,.02,2.03,.67,.16)],'Titanium')
        for x in [-.58,.58]:
            section_body('Accelerator breech armor',[(-1.02,x,0,.70,.64,.18),(-.70,x,0,.94,.92,.23),(.29,x,0,.83,.72,.19)],'Armor')
            section_body('Breech upper ceramic blade',[(-.91,x,.36,.52,.08,.02),(-.45,x,.49,.68,.10,.025),(.20,x,.39,.58,.08,.02)],'Ceramic')
            for dx in [-.29,.29]:
                box('Breech power recess',(x+dx,-.74,.09),(.06,.21,.11),'Dark',.008)
                box('Breech status insert',(x+dx,-.85,.09),(.023,.014,.065),'Signal',.003)
            ring('Recessed breech aperture',(x,-1.034,0),.278,.224,.025,'Y','Titanium')
        for s in [-1,1]:
            cyl('Sealed elevation bearing',(s*1.10,.15,0),.245,.14,'Dark','X',16)

    elif pid=='MA-P05':
        # Central physical bore, mostly concealed by angular accelerator rails.
        cyl('Accelerator bore core',(0,-1.30,0),.119,2.55,'Dark','Y',32)
        section_body('Receiver shroud',[(-.08,0,0,.48,.47,.12),(-.64,0,0,.56,.53,.13),(-.88,0,0,.40,.39,.10)],'Titanium')
        # Split upper/lower rails expose the induction modules between them.
        for s in [-1,1]:
            section_body('Longitudinal accelerator rail',[(-.69,0,s*.205,.39,.17,.055),(-1.18,0,s*.23,.40,.15,.05),(-2.39,0,s*.20,.28,.14,.045),(-2.75,0,s*.15,.24,.10,.03)],'Ceramic')
            for y in [-1.04,-1.43,-1.82,-2.21]:
                box('Induction block',(s*.18,y,0),(.095,.19,.23),'Titanium',.026)
                box('Induction channel',(s*.236,y,0),(.012,.12,.09),'Dark',.004)
                box('Induction energized core',(s*.245,y,0),(.01,.09,.025),'Signal',.003)
        support=section_body('Faceted muzzle support',[(-2.52,0,0,.33,.38,.09),(-2.87,0,0,.40,.34,.09)],'Titanium')
        cutter=cyl('Temporary bore tool',(0,-2.70,0),.108,.80,'Dark','Y',32)
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=support
        mod=support.modifiers.new('Open through bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
        bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_move_up(modifier=mod.name)
        bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
        # Genuine open bore at the same functional muzzle point as earlier versions.
        ring('Open accelerator muzzle',(0,-2.85,0),.158,.105,.14,'Y','Titanium')
        cyl('Recessed bore darkness',(0,-2.60,0),.104,.015,'Dark','Y')
        for s in [-1,1]:
            stripe('Muzzle alignment marking',(s*.165,-2.77,.14),(s*.165,-2.86,.14),.012,'Ceramic')

    elif pid=='MA-P06':
        panel('Flush pressure seal',(0,0,.018),(.74,.60,.035),'Dark',.18)
        panel('Hexagonal service cartridge',(0,0,.043),(.68,.54,.032),'Ceramic',.17)
        panel('Inset cartridge center',(0,0,.062),(.47,.34,.012),'Titanium',.10)
        for x in [-.24,.24]:flush_fastener(x,0,.068)
        box('Cartridge status',(0,-.17,.075),(.17,.013,.01),'Signal',.003)

    elif pid=='MA-P07':
        section_body('Flush lidar blade',[(-.36,0,.055,.65,.11,.03),(-.15,0,.14,.80,.23,.07),(.30,0,.12,.57,.20,.055)],'Titanium')
        section_body('Lidar armored visor',[(-.30,0,.17,.68,.035,.01),(.10,0,.25,.70,.04,.01),(.30,0,.21,.51,.035,.01)],'Ceramic')
        box('Lidar aperture recess',(0,-.344,.09),(.52,.024,.057),'Dark',.008)
        for x in [-.18,0,.18]:box('Lidar independent optical cell',(x,-.362,.09),(.11,.014,.029),'Optic',.005)

    elif pid=='MA-P08':
        panel('Flush magnetic tie down',(0,0,.018),(.48,.30,.035),'Titanium',.10)
        panel('Tie down recessed socket',(0,0,.038),(.30,.15,.008),'Dark',.06)
        for x in [-.15,.15]:flush_fastener(x,0,.044)

    bpy.context.view_layer.update()
