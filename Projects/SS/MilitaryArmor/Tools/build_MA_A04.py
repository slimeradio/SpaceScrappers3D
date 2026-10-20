"""Final long wedge armor, MilitaryArmor scoped. Run in Blender background."""
import sys, math, json, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, bmesh
from mathutils import Vector
from weapon_batch_core import Part, Assembly, ROOT, write

ID='MA-A04'; PID=ID+'-P01'
TRI=[Vector((-.5,-1)),Vector((.5,1)),Vector((-.5,1))]

def contour(inset,cut=.105):
    """Inward parallel offset, then equal-distance corner truncation."""
    lines=[]
    for i,a in enumerate(TRI):
        direction=(TRI[(i+1)%3]-a).normalized()
        n=Vector((-direction.y,direction.x));lines.append((n,n.dot(a)+inset))
    p=[]
    for i in range(3):
        n1,c1=lines[i-1];n2,c2=lines[i]
        det=n1.x*n2.y-n1.y*n2.x
        p.append(Vector(((c1*n2.y-n1.y*c2)/det,(n1.x*c2-c1*n2.x)/det)))
    result=[]
    for i,a in enumerate(p):
        result.extend([a+(p[i-1]-a).normalized()*cut,a+(p[(i+1)%3]-a).normalized()*cut])
    return result

p=Part(PID,'Faceted spacecraft long wedge armor 1x2')
verts=[(*v,z) for z in (0,.16) for v in TRI]
faces=[(2,1,0)];slots=[0]
for i in range(3):
    j=(i+1)%3;faces.append((i,j,j+3,i+3));slots.append(0)
rings=[]
for inset,z in [(.025,.235),(.065,.28),(.085,.28),(.11,.255)]:
    rings.append(len(verts));verts.extend((v.x,v.y,z) for v in contour(inset))
for i in range(3):
    j=(i+1)%3
    faces.append((3+i,rings[0]+2*i,rings[0]+2*i+1));slots.append(0)
    faces.append((3+i,3+j,rings[0]+2*j,rings[0]+2*i+1));slots.append(0)
for k in range(3):
    a,b=rings[k:k+2]
    for i in range(6):
        j=(i+1)%6;faces.append((a+i,a+j,b+j,b+i));slots.append(1 if k==1 else 0)
faces.append(tuple(range(rings[-1],rings[-1]+6)));slots.append(0)
o=p.mesh('MA-A04-P01.ArmorSkin',verts,faces,'Armor',bevel=0)
o.data.materials.append(p.mats['Ceramic'])
for poly,slot in zip(o.data.polygons,slots):poly.material_index=slot
mounts=[{'id':'structural-root','role':'armor-mount','parent':o.name,'position':[0,0,0],'forward':[0,-1,0],'up':[0,0,1],'compatibility':['MilitaryArmor.armor-edge.v1'],'constraints':'Unit transform; structural join walls z0..0.16'}]
p.save(mounts=mounts,points=[],animations=[],notes='Catalog 1x2 footprint; visual 1BU pitch, not metric. Uniform PBR Armor and Ceramic, no UV/image dependency. One manifold mesh; planar chamfers and recessed face. No visible mounting hardware.')
partpath=ROOT/'Parts'/PID/'part.json'
meta=json.loads(partpath.read_text(encoding='utf8'))
meta['catalog_id']='armor-1x2-wedge';meta['catalog_grid']=[1,2]
meta['attachment_areas']=[{'id':'bottom-mount','role':'structural-mount','parent':o.name,'shape':'polygon','vertices':[list(v)+[0] for v in TRI],'local_pose':{'translation':[0,0,0],'rotation_euler_xyz':[0,0,0]},'normal':[0,0,-1],'forward':[0,-1,0],'allowed_rotations_degrees':[0,90,180,270],'constraints':'Keep exact footprint; no nonuniform scale','compatibility':['MilitaryArmor.armor-edge.v1']}]
meta['geometry_parameters']={'nominal_boundary':[list(v) for v in TRI],'structural_wall_height':.16,'thickness':.28,'top_inset_z':.255,'upper_chamfer_corner_cut':.105}
write(partpath,meta)

a=Assembly(ID,'armor-1x2-wedge',[1,2],'Faceted long wedge armor 1x2')
a.instance('armor-shell',PID)
export=a.save(notes='Static one-part armor; unit transforms. Catalog grid != physical meter dimensions. No animations, emission, textures or visible sockets.',frame_end=1)
assembly_path=ROOT/'Blocks'/ID/'assembly.json'
data=json.loads(assembly_path.read_text(encoding='utf8'));data['animations']=[];write(assembly_path,data)

def inspect_scene(label):
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();meshes=[x for x in bpy.context.scene.objects if x.type=='MESH']
    count=0;zero=[];out=[];finite=True;manifold=True;pts=[]
    for obj in meshes:
        ev=obj.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles();count+=len(m.loop_triangles)
        bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);manifold &= all(e.is_manifold for e in bm.edges);bm.free()
        for t in m.loop_triangles:
            if t.area<1e-10:zero.append([obj.name,t.index])
        for v in m.vertices:
            q=obj.matrix_world@v.co;pts.append(q)
            finite &= all(math.isfinite(x) for x in q)
            if q.z< -1e-6 or q.z>.280001 or q.x<-.500001 or q.y>1.000001 or q.y< -1.000001 or q.x>(q.y+1)/2-.5+1e-6:out.append(list(q))
        ev.to_mesh_clear()
    used={m for obj in meshes for m in obj.data.materials}
    return {'stage':label,'evaluated_triangles':count,'mesh_count':len(meshes),'material_count':len(used),'zero_area_triangles':zero,'boundary_overshoot':out,'finite_vertices':bool(finite),'geometrically_closed_after_coincident_vertex_weld':bool(manifold),'unit_scales':all(all(abs(v-1)<1e-6 for v in x.scale) for x in meshes),'emission_free':all(m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value==0 for m in used),'bounds':{'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}}

source=ROOT/'Blocks'/ID/(ID+'.blend')
bpy.ops.wm.open_mainfile(filepath=str(source));source_result=inspect_scene('source-reopened')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(export));roundtrip=inspect_scene('GLB-roundtrip')
print(source_result,roundtrip)
assert all(r['evaluated_triangles']<=240 and r['mesh_count']<=2 and r['material_count']<=3 and not r['zero_area_triangles'] and not r['boundary_overshoot'] and r['finite_vertices'] and r['geometrically_closed_after_coincident_vertex_weld'] and r['unit_scales'] and r['emission_free'] for r in (source_result,roundtrip))

# Review only in TEMP; never save camera/light helpers in delivered source.
bpy.ops.wm.open_mainfile(filepath=str(source))
temp=Path(tempfile.gettempdir())
a.review(path=temp/(ID+'-final-oblique.png'),view=(3,-4,4),target=(0,0,.12),scale=2.9,resolution=700)
scene=bpy.context.scene;scene.camera.location=(0,0,5);scene.camera.rotation_euler=(0,0,0);scene.camera.data.ortho_scale=2.5
scene.render.filepath=str(temp/(ID+'-final-top.png'));bpy.ops.render.render(write_still=True)
# Two mirrored-by-rotation instances form a perfect rectangle; tile the rectangle 2x2.
original=[x for x in scene.objects if x.type=='MESH']
for x in list(original):x.hide_render=True
for ix in range(2):
    for iy in range(2):
        for angle in (0,math.pi):
            for src in original:
                obj=src.copy();obj.data=src.data.copy();scene.collection.objects.link(obj);obj.parent=None;obj.matrix_world=src.matrix_world.copy();obj.rotation_euler.z=angle;obj.location=(ix-0.5,(iy-.5)*2,0);obj.hide_render=False
scene.camera.location=(5,-7,7);scene.camera.rotation_euler=(Vector((0,0,.1))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=5.8
scene.render.filepath=str(temp/(ID+'-final-neighbours.png'));bpy.ops.render.render(write_still=True)
validation_path=ROOT/'Blocks'/ID/'validation.json'
validation=json.loads(validation_path.read_text(encoding='utf8'));validation['geometry_checks']=[source_result,roundtrip];validation['final_review_TEMP']=[str(temp/(ID+'-final-'+x+'.png')) for x in ('oblique','top','neighbours')];validation['visual_review']='Pending external image inspection';write(validation_path,validation)
print('ARMOR_COMPLETE '+json.dumps({'id':ID,'source':source_result,'roundtrip':roundtrip}))
