"""MilitaryArmor 1.2: broad planar armor cuts and octagonal sections."""
import bpy, bmesh, math
from mathutils import Vector

def facet(g,pid):
    coll=g['coll']
    bpy.context.view_layer.update()

    def replace(o,vertices,faces,width=.018):
        mesh=bpy.data.meshes.new(o.name+' / planar armor');mesh.from_pydata(vertices,[],faces);mesh.update()
        for m in o.data.materials:mesh.materials.append(m)
        o.data=mesh
        for mod in list(o.modifiers):o.modifiers.remove(mod)
        if width:
            mod=o.modifiers.new('Small machined edge','BEVEL');mod.width=width;mod.segments=1
            o.modifiers.new('Planar weighted normals','WEIGHTED_NORMAL')
        o['shape_revision']='1.2 / faceted'

    def octagon(w,d,c):
        c=min(c,w*.36,d*.36)
        return [(-w/2+c,-d/2),(w/2-c,-d/2),(w/2,-d/2+c),(w/2,d/2-c),(w/2-c,d/2),(-w/2+c,d/2),(-w/2,d/2-c),(-w/2,-d/2+c)]

    def profile(o,axis=2,corner=.18,inset=.07,shoulder=.18):
        # Local mesh coordinates retain object transforms and mounting origins.
        coords=[v.co.copy() for v in o.data.vertices]
        lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
        uv=[i for i in range(3) if i!=axis];w=hi[uv[0]]-lo[uv[0]];d=hi[uv[1]]-lo[uv[1]];h=hi[axis]-lo[axis]
        center=[(lo[i]+hi[i])/2 for i in range(3)];inset=min(inset,w*.15,d*.15);shoulder=min(shoulder,h*.30)
        rings=[(lo[axis],inset*.5),(lo[axis]+shoulder,0),(hi[axis]-shoulder,0),(hi[axis],inset)]
        vertices=[]
        for z,shrink in rings:
            for x,y in octagon(w-2*shrink,d-2*shrink,corner):
                p=center.copy();p[uv[0]]+=x;p[uv[1]]+=y;p[axis]=z;vertices.append(p)
        faces=[tuple(reversed(range(8))),tuple(range(24,32))]
        for k in range(3):
            for i in range(8):j=(i+1)%8;faces.append((k*8+i,k*8+j,(k+1)*8+j,(k+1)*8+i))
        # The UV axis order can reverse orientation for an extrusion along Y.
        if axis==1:faces=[tuple(reversed(f)) for f in faces]
        replace(o,vertices,faces,min(.018,h*.08))

    if pid=='MA-P01':
        for o in list(coll.objects):
            if o.type!='MESH':continue
            if o.name.startswith(('Lower structural chassis','Armored deck','Upper deck inset')):profile(o,2,.58,.12,.12)
            elif o.name.startswith('Segmented perimeter armor'):profile(o,2,.16,.06,.14)
            elif o.name.startswith(('Service panel','Recessed service door','Door inset')):profile(o,1,.09,.015,.015)
        # Cut the assembled perimeter consistently, including its trim.
        for o in list(coll.objects):
            if o.type!='MESH':continue
            bm=bmesh.new();bm.from_mesh(o.data)
            for sx,sy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                n=Vector((sx,sy,0)).normalized();point=n*(4.10/math.sqrt(2))
                local_point=o.matrix_world.inverted()@point
                local_normal=o.matrix_world.to_3x3().transposed()@n
                result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=local_point,plane_no=local_normal,clear_outer=True)
                border=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
                if border:bmesh.ops.holes_fill(bm,edges=border,sides=0)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()

    elif pid=='MA-P03':
        for o in coll.objects:
            if o.type!='MESH':continue
            if o.name.startswith('Heavy cheek armor'):
                # Keep the established sloping side plane; cut the nose and tail
                # diagonally and add a roof shoulder as broad flat facets.
                w,d,h=1.10,3.12,1.51;v=[]
                for t in [0,.20,.78,1]:
                    for x,y in octagon(w*(1-.24*t),d*(1-.30*t),.28-.05*t):v.append((x,y,h*t))
                faces=[tuple(reversed(range(8))),tuple(range(24,32))]
                for k in range(3):
                    for i in range(8):j=(i+1)%8;faces.append((8*k+i,8*k+j,8*(k+1)+j,8*(k+1)+i))
                replace(o,v,faces,.015)
            elif o.name.startswith(('Inner turret frame','Rear armored counterweight')):profile(o,2,.32,.12,.18)
            elif o.name.startswith('Armored roof bridge'):profile(o,2,.28,.07,.10)
            elif o.name.startswith(('Cheek applique','Roof spinal panel')):profile(o,2,.13,.025,.03)
            elif o.name.startswith('Layered flank applique'):profile(o,0,.16,.012,.012)
            elif o.name.startswith('Front cheek reinforcement'):profile(o,1,.12,.015,.02)

    elif pid=='MA-P04':
        for o in coll.objects:
            if o.type=='MESH' and o.name.startswith(('Independent armored sleeve','Cradle beam')):profile(o,1,.22,.065,.17)
            elif o.type=='MESH' and o.name.startswith('Mantlet top armor'):profile(o,2,.12,.02,.02)

    elif pid=='MA-P06':
        for o in coll.objects:
            if o.type=='MESH' and o.name.startswith(('Hatch armor','Hatch gasket','Hatch recessed center')):profile(o,2,.12,.015,.015)

    elif pid=='MA-P05':
        for o in coll.objects:
            if o.type=='MESH' and o.name.startswith('Upper barrel shield'):profile(o,2,.075,.01,.012)

    bpy.context.view_layer.update()
