"""MilitaryArmor 1.1: editable construction details in part-local coordinates."""
import bpy, math
from mathutils import Vector

def enhance(g, pid):
    box,cyl,ring,label,bolts=(g[k] for k in ('box','cyl','ring','label','bolts'))
    coll,mats=g['coll'],g['mats']
    for name,color,metal,rough in [('Panel',(.054,.069,.075),.65,.4),('Edge',(.22,.245,.25),.8,.38),('Warning',(.49,.30,.075),.25,.56),('Rubber',(.009,.014,.017),.15,.75)]:
        m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;mats[name]=m
    # Keep the finish metallic; the original high-frequency bump was too coarse.
    for m in (mats['Armor'],mats['Steel']):
        for n in m.node_tree.nodes:
            if n.type=='BUMP':n.inputs['Strength'].default_value=.10;n.inputs['Distance'].default_value=.006

    def cable(name,points,r=.025,mat='Rubber'):
        data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=3
        spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
        for p,co in zip(spline.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
        o=bpy.data.objects.new(name,data);coll.objects.link(o);o.data.materials.append(mats[mat]);return o

    def rod(name,a,b,r=.025,mat='Steel'):
        a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,mat);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

    def screw(name,loc,axis='Z',r=.032):
        o=cyl(name,loc,r,.025,'Steel',axis,6)
        if axis=='Z':box('Screw driver recess',(loc[0],loc[1],loc[2]+.016),(r*.95,.012,.008),'Dark',.002)
        return o

    def vent_front(x,y,z,w,h,axis='Y'):
        if axis=='Y':
            box('Recessed vent frame',(x,y,z),(w,.065,h),'Steel',.025)
            box('Vent dark cavity',(x,y-.042,z),(w-.065,.035,h-.065),'Dark',.014)
            for i in range(7):box('Angled ventilation blade',(x,y-.069,z-h*.34+i*h*.113),(w-.10,.045,.027),'Panel',.008)
        else:
            s=1 if x>0 else -1
            box('Side vent frame',(x,y,z),(.065,w,h),'Steel',.02)
            box('Side vent cavity',(x+s*.04,y,z),(.035,w-.06,h-.06),'Dark',.01)
            for i in range(7):box('Side louvre',(x+s*.063,y,z-h*.34+i*h*.113),(.045,w-.10,.026),'Panel',.008)

    if pid=='MA-P01':
        # Large service access doors give the base functional surface hierarchy.
        for x in [-.97,.97]:
            box('Service door gasket',(x,-2.116,.51),(.73,.025,.48),'Rubber',.025)
            box('Recessed service door',(x,-2.143,.51),(.64,.045,.39),'Panel',.025)
            box('Door inset',(x,-2.171,.52),(.43,.02,.22),'Armor',.015)
            for dx in [-.23,.23]:
                for z in [.37,.65]:screw('Door captive screw',(x+dx,-2.178,z),'Y',.023)
            box('Door latch',(x+.20,-2.19,.51),(.05,.035,.14),'Steel',.008)
        # Relocate existing lettering above the doors rather than cover it.
        for o in coll.objects:
            if o.type=='FONT':o.location.z=.83;o.data.size=.095 if o.data.body=='SPACE SCRAPPERS' else .075
        for s in [-1,1]:
            for y in [-1.43,0,1.43]:
                vent_front(s*2.425,y,.52,.71,.38,'X')
                for dy in [-.43,.43]:screw('Armor side bolt',(s*2.43,y+dy,.85),'X')
            for y in [-1.64,1.64]:
                box('Corner armor cap',(s*1.81,y,1.03),(.51,.43,.08),'Panel',.035)
                bolts([s*1.81-.14,s*1.81+.14],[y-.1,y+.1],1.09)
            # Toe rail and deck hardline, clear of moving bearing.
            cable('Deck protected hydraulic line',[(s*1.94,-1.25,1.02),(s*1.94,-.65,1.04),(s*1.94,.65,1.04),(s*1.94,1.25,1.02)],.025,'Steel')
            for y in [-.75,.75]:box('Pipe clamp',(s*1.94,y,1.045),(.15,.10,.08),'Panel',.015)
        for s in [-1,1]:
            for x in [-1.82,1.82]:
                box('Exposed deck light',(x,s*2.118,.84),(.27,.035,.068),'Warm',.009)
        for i in range(4):
            o=box('Front safety stripe',(.20+i*.13,-2.112,.38),(.06,.018,.16),'Warning',.003);o.rotation_euler.y=-.40
        label('LIFT / LOCK',(-.25,-2.119,.68),.065)

    elif pid=='MA-P02':
        # Repeated bearing teeth and visible lubricant fittings.
        for i in range(64):
            a=i*2*math.pi/64;o=box('Ring gear tooth',(1.49*math.cos(a),1.49*math.sin(a),.26),(.075,.06,.12),'Steel',.008);o.rotation_euler.z=a
        for i in range(8):
            a=i*2*math.pi/8
            cyl('Grease fitting',(1.69*math.cos(a),1.69*math.sin(a),.53),.027,.07,'Warning',verts=6)
        for a in [-.70,.70]:
            box('Azimuth drive casing',(1.47*math.cos(a),1.47*math.sin(a),.43),(.30,.28,.17),'Panel',.035)

    elif pid=='MA-P03':
        for s in [-1,1]:
            for y in [-.93,.05,1.01]:
                o=box('Layered flank applique',(s*1.785,y,.84),(.075,.84,.83),'Panel',.035);o.rotation_euler.y=-s*.087
                # Rivets and weld strips follow the actual sloped cheek surface.
                for dy in [-.32,.32]:
                    for z in [.53,1.14]:screw('Flank recessed fastener',(s*(1.90-.087*(z-.18)),y+dy,z),'X',.027)
                for z in [.47,1.23]:
                    cable('Armor weld bead',[(s*(1.89-.087*(z-.18)),y-.32,z),(s*(1.89-.087*(z-.18)),y,z+.004),(s*(1.89-.087*(z-.18)),y+.32,z)],.010,'Edge')
                # Roof seam hardware and elongated panel recesses.
                box('Roof armor recess',(s*1.27,y,1.706),(.48,.39,.025),'Panel',.025)
                for j in range(3):box('Roof stamped rib',(s*1.27,y-.13+j*.13,1.73),(.37,.035,.025),'Armor',.008)
            vent_front(s*1.845,.10,.85,.59,.43,'X')
            # Front wedge seam: a layered nose plate underneath the angled cheek.
            box('Front cheek reinforcement',(s*1.27,-1.54,.53),(.73,.10,.36),'Panel',.04)
            vent_front(s*1.27,-1.602,.51,.51,.23)
            for y in [-.65,.65]:
                box('Roof rail foot',(s*.95,y,1.75),(.14,.17,.07),'Panel',.015)
            rod('Roof grab rail',(s*.95,-.65,1.82),(s*.95,.65,1.82),.027)
            # Cable runs stay on the turret shell and do not bridge the moving cradle.
            cable('Optics armored conduit',[(s*.88,.90,1.66),(s*.85,.58,1.78),(s*.82,.12,1.76),(s*.70,-.26,1.72)],.028)
        for x in [-.75,0,.75]:
            box('Rear exchanger housing',(x,1.595,.72),(.58,.10,.57),'Panel',.025)
            for j in range(8):box('Rear exchanger fin',(x-.22+j*.063,1.66,.72),(.023,.07,.43),'Steel',.005)
        box('Roof spine recess',(0,.08,1.699),(.50,.56,.025),'Dark',.018)
        for j in range(7):box('Spine cooling fin',(0,-.14+j*.069,1.728),(.43,.025,.035),'Steel',.005)
        label('CAUTION / HOT',(-.26,-.405,1.704),.075,(0,0,0))
        # Small antenna with a solid anchored base, clear of the gun sweep.
        cyl('Antenna socket',(.97,1.05,1.75),.09,.12,'Panel')
        cyl('Antenna spring',(.97,1.05,1.89),.043,.18,'Steel')
        rod('Whip antenna',(.97,1.05,1.96),(.97,1.05,2.52),.012,'Dark')
        for o in coll.objects:
            if o.type=='FONT' and o.data.body=='03':o.location.x=-1.855;o.location.y=-.60;o.location.z=.70;o.data.size=.25

    elif pid=='MA-P04':
        for x in [-.58,.58]:
            box('Mantlet top armor',(x,-.28,.486),(.77,.69,.08),'Panel',.025)
            for dx in [-.29,.29]:
                for y in [-.48,-.08]:screw('Mantlet cover screw',(x+dx,y,.539))
            for z in [-.30,.30]:
                for dx in [-.27,.27]:screw('Gun port lock',(x+dx,-.915,z),'Y',.025)
            # Protective rolling bellows remain part of the elevation cradle.
            for j in range(6):ring('Gun dust seal',(x,-.87-j*.035,0),.285,.245,.025,'Y','Rubber')
        for s in [-1,1]:
            cyl('Trunnion end cap',(s*1.26,.17,0),.245,.055,'Panel','X')
            for a in range(6):
                t=a*math.pi/3;screw('Trunnion cap bolt',(s*1.296,.17+.17*math.cos(t),.17*math.sin(t)),'X',.025)

    elif pid=='MA-P05':
        # Separate heat shield sectors, clamps and recoil guide rods.
        for y in [-.97,-1.42,-1.85]:
            ring('Heat shield mounting band',(0,y,0),.213,.17,.065,'Y','Panel')
            for s in [-1,1]:box('Band clamp',(s*.203,y,0),(.07,.10,.12),'Steel',.01)
        for s in [-1,1]:
            rod('Recoil guide',(s*.225,-.12,.13),(s*.225,-.79,.13),.025,'Steel')
            cyl('Recoil guide end',(s*.225,-.80,.13),.043,.06,'Panel','Y',12)
        for y in [-1.20,-1.64]:
            o=box('Upper barrel shield',(0,y,.167),(.29,.31,.055),'Panel',.02)
            for x in [-.09,.09]:screw('Shield screw',(x,y,.20),r=.018)
        muzzle=next(o for o in coll.objects if o.name=='Open muzzle brake')
        # Replace painted side recesses with through-wall rectangular brake ports.
        for o in list(coll.objects):
            if o.name.startswith('Brake gas port recess'):bpy.data.objects.remove(o,do_unlink=True)
        for y in [-2.44,-2.64,-2.84]:
            cutter=box('Temporary port cutter',(0,y,0),(.75,.105,.14),'Dark',0)
            bpy.context.view_layer.objects.active=muzzle
            mod=muzzle.modifiers.new('True gas port','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
            bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
        for y in [-2.30,-2.91]:ring('Muzzle reinforcing lip',(0,y,0),.278,.136,.035,'Y','Panel')

    elif pid=='MA-P06':
        box('Hatch recessed center',(0,.05,.159),(.49,.31,.025),'Panel',.025)
        label('ACCESS',(-.18,.03,.175),.074,(0,0,0))
        for x in [-.27,.27]:
            cyl('Hinge pin',(x,.36,.14),.035,.21,'Steel','X',16)
        box('Latch pocket',(0,-.32,.16),(.21,.09,.04),'Dark',.01)
        box('Hatch locking tongue',(0,-.35,.19),(.12,.10,.035),'Steel',.008)

    elif pid=='MA-P07':
        for s in [-1,1]:
            box('Optics side guard',(s*.27,0,.20),(.07,.40,.21),'Panel',.02)
            for y in [-.12,.12]:screw('Optics mounting screw',(s*.315,y,.23),'X',.021)
        for i in range(12):
            a=i*2*math.pi/12;o=box('Sensor cooling rib',(.176*math.cos(a),.11+.176*math.sin(a),.48),(.035,.035,.19),'Steel',.007)
        cyl('Protected sensor glass',(0,.11,.61),.135,.025,'Glass')
        box('Lens rain brow',(0,-.385,.34),(.51,.14,.035),'Panel',.01)
        cable('Optics cable',[(.23,.22,.08),(.26,.32,.07),(.10,.33,.06)],.02)

    elif pid=='MA-P08':
        for x in [-.23,.23]:
            for y in [-.06,.06]:screw('Shoe fixing',(x,y,.061),r=.019)
        for i in range(9):box('Grip knurl',(i*.035-.14,0,.29),(.012,.086,.086),'Panel',.008)
