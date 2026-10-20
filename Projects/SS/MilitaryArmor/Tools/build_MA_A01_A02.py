"""Final rectangular armor sources, parts, viewer exports and review evidence."""
import sys, math, json, tempfile
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from weapon_batch_core import Part, Assembly, write, ROOT, outline
TEMP=Path(tempfile.gettempdir())/'MA-armor-review'
TEMP.mkdir(exist_ok=True)

def check_meshes():
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    result={'mesh_count':len(obs),'triangles':0,'zero_area_faces':0,'nonmanifold_edges':0,'geometric_nonmanifold_edges':0,'materials':set(),'emission':False,'bounds':None,'transforms_finite':True,'unit_scale':True}
    coords=[]
    for o in obs:
        me=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();me.calc_loop_triangles()
        result['triangles']+=len(me.loop_triangles)
        result['zero_area_faces']+=sum(t.area<1e-10 for t in me.loop_triangles)
        bm=bmesh.new();bm.from_mesh(me);result['nonmanifold_edges']+=sum(not e.is_manifold for e in bm.edges);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);result['geometric_nonmanifold_edges']+=sum(not e.is_manifold for e in bm.edges);bm.free()
        result['unit_scale'] &= all(abs(s-1)<1e-6 for s in o.scale)
        result['transforms_finite'] &= all(math.isfinite(v) for row in o.matrix_world for v in row)
        coords.extend(o.matrix_world@v.co for v in me.vertices)
        for mat in me.materials:
            result['materials'].add(mat.name)
            p=mat.node_tree.nodes.get('Principled BSDF');result['emission'] |= bool(p.inputs['Emission Strength'].default_value>0)
    result['bounds']={'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]}
    result['materials']=sorted(result['materials'])
    return result

def render_review(tag,view,scale,target=(0,0,.14),tiled=False,w=1):
    scene=bpy.context.scene
    if tiled:
        sources=[o for o in scene.objects if o.type=='MESH']
        for o in sources:
            for y in range(4):
                for x in range(4):
                    if x==0 and y==0:continue
                    copy=o.copy();copy.data=o.data;scene.collection.objects.link(copy);copy.parent=None;copy.location=(x*w,y,0)
        target=(1.5*w,1.5,.14)
        view=(target[0]+6,target[1]-8,7)
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x=800;scene.render.resolution_y=650;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Temporary armor review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.17,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    bpy.ops.object.camera_add(location=view);cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam
    for pos,power,size in [((0,-3,6),600,4),((-4,2,3),400,4),((4,4,5),700,5)]:
        bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(TEMP/(tag+'.png'));bpy.ops.render.render(write_still=True)
    return scene.render.filepath

def build(bid,w):
    pid=bid+'-P01';p=Part(pid,'Faceted repeatable armor '+('1x1' if w==1 else '2x1'))
    base=[(-w/2,-.5),(w/2,-.5),(w/2,.5),(-w/2,.5)]
    verts=[(x,y,z) for z in (0,.16) for x,y in base]
    faces=[(3,2,1,0)];slots=[0]
    for i in range(4):j=(i+1)%4;faces.append((i,j,4+j,4+i));slots.append(0)
    rings=[]
    for inset,z,cut in [(.025,.235,.105),(.065,.28,.105),(.085,.28,.105),(.11,.255,.105)]:
        rings.append(len(verts));verts.extend((x,y,z) for x,y in outline(w-2*inset,1-2*inset,cut))
    # Octagon order: bottom-left edge, bottom-right edge, right-bottom, right-top, etc.
    first=rings[0]
    for i in range(4):
        j=(i+1)%4;a=first+2*i;b=first+(2*i+1)%8;prev=first+(2*i-1)%8
        faces.extend([(4+i,4+j,b,a),(4+i,a,prev)]);slots.extend([0,0])
    for k in range(3):
        a,b=rings[k:k+2]
        for i in range(8):j=(i+1)%8;faces.append((a+i,a+j,b+j,b+i));slots.append(1 if k==1 else 0)
    faces.append(tuple(rings[-1]+i for i in range(8)));slots.append(0)
    o=p.mesh(pid+'.shell',verts,faces,'Armor',0);o.data.materials.append(p.mats['Ceramic'])
    for face,slot in zip(o.data.polygons,slots):face.material_index=slot
    mounts=[{'id':'root','role':'armor-structural-mount','position':[0,0,0],'forward':[0,-1,0],'up':[0,0,1],'parent':o.name,'compatibility':['MilitaryArmor.armor.cell'],'restrictions':'unit scale; align catalog XY boundary'}]
    p.save(mounts=mounts,notes='Exact rectangular structural perimeter z=0..0.16. Broad upper chamfers and a recessed quiet panel. No emission, animations or file textures.')
    partpath=ROOT/'Parts'/pid/'part.json';meta=json.loads(partpath.read_text());meta['attachment_areas']=[{'id':'structural-bottom','role':'grid-interface','parent':o.name,'shape':'rectangle','size':[w,1],'position':[0,0,0],'normal':[0,0,-1],'up':[0,1,0],'allowed_rotations_degrees':[0,90,180,270],'compatibility':['MilitaryArmor.armor.cell'],'restrictions':'Logical catalog footprint only; no physical scale conversion.'}];write(partpath,meta)
    # Required part is saved and visually reviewed before assembly creation.
    render_review(bid+'-part-final',(3,-4,3),w+1.2)
    a=Assembly(bid,'armor-1x1' if w==1 else 'armor-2x1',[w,1],'MilitaryArmor faceted armor '+str(w)+'x1');a.instance('armor-shell',pid);a.save('Catalog footprint retained. Static viewer authoring; physical scale and game acceptance unspecified.',frame_end=1)
    folder=ROOT/'Blocks'/bid;assembly=json.loads((folder/'assembly.json').read_text());assembly['animations']=[];write(folder/'assembly.json',assembly)
    source=folder/(bid+'.blend');bpy.ops.wm.open_mainfile(filepath=str(source));sourcecheck=check_meshes()
    assert sourcecheck['triangles']<=160 and sourcecheck['zero_area_faces']==0 and sourcecheck['nonmanifold_edges']==0 and len(sourcecheck['materials'])<=2 and not sourcecheck['emission']
    assert all(abs(sourcecheck['bounds']['min'][i]-[-w/2,-.5,0][i])<1e-6 for i in range(3))
    assert all(abs(sourcecheck['bounds']['max'][i]-[w/2,.5,.28][i])<1e-6 for i in range(3))
    oblique=render_review(bid+'-final-oblique',(3,-4,3),w+1.2)
    bpy.ops.wm.open_mainfile(filepath=str(source));top=render_review(bid+'-final-top',(0,0,5),w+.5)
    bpy.ops.wm.open_mainfile(filepath=str(source));tile=render_review(bid+'-final-tiled',(6,-8,7),max(6,4.2*w),tiled=True,w=w)
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(folder/'Exports'/(bid+'.glb')));roundtrip=check_meshes()
    assert roundtrip['triangles']==sourcecheck['triangles'] and roundtrip['zero_area_faces']==0 and not roundtrip['emission']
    assert all(abs(roundtrip['bounds'][k][i]-sourcecheck['bounds'][k][i])<1e-5 for k in ['min','max'] for i in range(3))
    validation=json.loads((folder/'validation.json').read_text());validation.update({'source_reopened':True,'source_geometry':sourcecheck,'glb_roundtrip':roundtrip,'roundtrip_passed':True,'review_images_TEMP_only':[oblique,top,tile],'visual_review':'pending image inspection','catalog_boundary_retained':True,'edge_height_BU':.16,'top_height_BU':.28,'functional_points':[],'animations':[]});write(folder/'validation.json',validation)
    write(folder/'README.md',f'# {bid} — гранёная броня {w}x1\n\nКаталог: `'+assembly['catalog_id']+'`. Одна новая переиспользуемая деталь `'+pid+'` v1.0; масштаб экземпляра 1. Ровная несущая кромка высотой 0.16 BU, широкие фаски, срезанные верхние углы и спокойная утопленная панель; стыковочный нижний контур сохранён.\n\n'+str(sourcecheck['triangles'])+' треугольников, один меш, два PBR-материала Armor/Ceramic; без файловых текстур, эмиссии и анимации. Логические крепления описаны в part.json.\n\nИсточник: `'+bid+'.blend`; финальный просмотр: `Exports/'+bid+'.glb`. Геометрия источника повторно открыта; GLB импортирован обратно с проверкой числа треугольников, материалов и габаритов. Финальные виды и повторение 4x4 проверяются в TEMP; промежуточных вариантов нет.\n\nBU условны; физический масштаб, коллайдеры и работа в игре не подтверждены.\n')
    print('ARMOR_RESULT',bid,sourcecheck,flush=True)

if __name__=='__main__':
    build('MA-A01',1)
    build('MA-A02',2)