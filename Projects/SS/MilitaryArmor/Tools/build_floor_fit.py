"""Run in Blender: validate independent floors, then uniformly fit existing assemblies."""
from pathlib import Path
import sys,math,copy,shutil,itertools,runpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from floor_fit import ROOT,BACKUP,CORNER,MARGIN,FRAME,read,write
sys.path.insert(0,str(ROOT.parents[2]/'Tools/SpriteBake'))
import bpy
import numpy as np
from mathutils import Vector
import blender_worker as bw

def material(name,role,color,metal,rough):
    m=bpy.data.materials.new(name);m.use_nodes=True;m['ss_role']=role
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m

def solid(name,poly,z0,z1,mat):
    n=len(poly);verts=[(x,y,z) for z in (z0,z1) for x,y in poly]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);obj.data.materials.append(mat)
    return obj

def make_floor(fid,record):
    if '--rebuild-floor' not in sys.argv and (ROOT/'Parts'/fid/'validation.json').exists():
        assert read(ROOT/'Parts'/fid/'validation.json')['passed']
        return
    bw.reset();poly=record['polygon'];m1=material('FloorSurface','Color1',(.38,.43,.46),.25,.5);m2=material('FloorArmor','Color2',(.095,.12,.145),.72,.37)
    objects=[solid('Floor continuous surface',poly,0,.035,m1)]
    # Corner triangles have fixed edge distances. Only straight edge middles grow.
    inset=[]
    for i,p in enumerate(poly):
        point=np.asarray(p);prev=np.asarray(poly[i-1]);nxt=np.asarray(poly[(i+1)%len(poly)])
        a=point-prev;b=nxt-point
        na=np.array([-a[1],a[0]])/np.linalg.norm(a);nb=np.array([-b[1],b[0]])/np.linalg.norm(b)
        inset.append(np.linalg.solve(np.asarray([na,nb]),np.asarray([np.dot(point,na)+FRAME,np.dot(point,nb)+FRAME])).tolist())
    for i,p in enumerate(poly):
        p=Vector(p);prev=Vector(poly[i-1]);nxt=Vector(poly[(i+1)%len(poly)])
        a=(prev-p).normalized();b=(nxt-p).normalized()
        objects.append(solid('Floor fixed corner '+str(i),[p,p+b*CORNER,p+a*CORNER],.03,.07,m2))
        q=nxt
        objects.append(solid('Floor straight border '+str(i),[p,q,inset[(i+1)%len(poly)],inset[i]],.03,.06,m2))
    stats=bw.geometry(objects);assert not stats['nonmanifold_edges'],stats
    for i,p in enumerate(poly):
        e=np.asarray(poly[(i+1)%len(poly)])-np.asarray(p);normal=np.array([-e[1],e[0]])/np.linalg.norm(e)
        for obj in objects:
            assert min(float(np.dot(np.asarray((v.co.x,v.co.y))-p,normal)) for v in obj.data.vertices)>=-1e-6,(fid,'floor outside occupied polygon')
    folder=ROOT/'Parts'/fid;folder.mkdir(parents=True,exist_ok=True)
    data=dict(schema='MilitaryArmor.BlenderAuthoring/1',id=fid,version='1.0',name='Floor with fixed corners',source=fid+'.blend',
      axes=dict(handedness='right',up='+Z',forward='-Y',units='1 BU = 1 gameplay cell'),origin=[0,0,0],pivot=[0,0,0],rest_pose='identity',scale_policy='unit only; rebuild parameterized variant to change footprint',
      bounds_local=dict(min=stats['bounds_bu'][0],max=stats['bounds_bu'][1]),materials=[dict(id=m.name,surfaces=[o.name for o in objects if m in list(o.data.materials)],role=m['ss_role'],base_color_linear=list(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value),metalness=m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value,roughness=m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,texture_source='uniform procedural PBR; no UV stretch') for m in (m1,m2)],emission=[],mounts=[dict(id='body',role='body-platform',position=[0,0,.075],forward=[0,-1,0],up=[0,0,1])],functional_points=[],attachment_areas=[dict(id='occupied-area',shape='polygon',vertices=[[x,y,0] for x,y in poly],normal=[0,0,1])],animations=[],floor_parameters=dict(corner_cells=CORNER,frame_cells=FRAME,polygon=poly))
    write(folder/'part.json',data);write(folder/'validation.json',dict(passed=True,geometry=stats,corner_cells=CORNER,frame_cells=FRAME,colors=['Color1','Color2']))
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(fid+'.blend')))
    print('PART_OK',fid,flush=True)

def points(objects):
    dg=bpy.context.evaluated_depsgraph_get();result=[]
    for obj in objects:
        evaluated=obj.evaluated_get(dg);mesh=evaluated.to_mesh()
        try:result.extend(tuple(obj.matrix_world@v.co) for v in mesh.vertices)
        finally:evaluated.to_mesh_clear()
    return np.asarray(result)

def fit(bid,record,original_profile):
    spec=copy.deepcopy(original_profile['blocks'][bid]);path=ROOT/spec['assembly'];a=read(BACKUP/spec['assembly'])
    assert not any(i['id']=='Floor' for i in a['instances'])
    # Rendering and metadata share the exact same hierarchy and transform.
    action_source=ROOT/'Versions/FloorFitBefore'/spec['source']
    if not action_source.exists():
        action_source.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(BACKUP/spec['source'],action_source)
    nodes,instances=bw.assemble(ROOT,dict(spec,use_author_animation=True,source=action_source.relative_to(ROOT).as_posix()),a,path)
    baseline=bw.geometry([o for group in instances.values() for o in group])
    refs=points([o for iid in record['body_instances'] for o in instances[iid]])
    allpts=points([o for group in instances.values() for o in group])
    poly=np.asarray(record['polygon']);planes=[];limits=[]
    # One support constraint per floor edge, with translation free to maximize
    # uniform scale. In particular a wedge does not inherit a bbox-center bias.
    for i,p in enumerate(poly):
        e=poly[(i+1)%len(poly)]-p;n=np.array([-e[1],e[0]])/np.linalg.norm(e)
        planes.append([n[0],n[1],float((refs[:,:2]@n).min())]);limits.append(float(np.dot(p,n))+MARGIN)
    planes=np.asarray(planes);limits=np.asarray(limits);candidates=[]
    for indices in itertools.combinations(range(len(poly)),3):
        try:solution=np.linalg.solve(planes[list(indices)],limits[list(indices)])
        except np.linalg.LinAlgError:continue
        if solution[2]>0 and np.all(planes@solution>=limits-1e-7):candidates.append(solution)
    assert candidates,(bid,'no convex inset fit')
    solution=max(candidates,key=lambda x:x[2]);s=float(solution[2])
    if len(poly)==4:
        solution[:2]=poly.mean(axis=0)-s*(refs[:,:2].min(axis=0)+refs[:,:2].max(axis=0))/2
    assert math.isfinite(s) and s>0,(bid,s)
    translation=[float(solution[0]),float(solution[1]),float(.075-s*allpts[:,2].min())]
    transformed=refs*s+np.asarray(translation)
    for i,p in enumerate(poly):
        e=poly[(i+1)%len(poly)]-p;n=np.array([-e[1],e[0]])/np.linalg.norm(e)
        assert float(((transformed[:,:2]-p)@n).min())>=MARGIN-1e-5,(bid,'body outside margin')
    # Keep original actions/pivots intact below the one uniform placement node.
    wrapper=bpy.data.objects.new('ModelFit',None);bpy.context.scene.collection.objects.link(wrapper)
    wrapper.location=translation;wrapper.scale=(s,s,s)
    roots=[o for o in nodes.values() if o.parent is None]
    for obj in roots:obj.parent=wrapper
    a.setdefault('nodes',[])
    for rootobj in roots:
        match=next((n for n in a['nodes'] if n['id']==rootobj.name),None)
        if match is None:match=dict(id=rootobj.name,parent=None,translation=[0,0,0],rotation_euler_xyz=[0,0,0],scale=[1,1,1]);a['nodes'].append(match)
        match['parent']='ModelFit'
    a['nodes'].append(dict(id='ModelFit',parent=None,translation=translation,rotation_euler_xyz=[0,0,0],scale=[s,s,s]))
    fid=record['floor'];floor_node=bpy.data.objects.new('Floor',None);bpy.context.scene.collection.objects.link(floor_node)
    loaded=bw.load_objects(ROOT/'Parts'/fid/(fid+'.blend'));loaded_set=set(loaded)
    for obj in loaded:
        if obj.parent not in loaded_set:obj.parent=floor_node
    a['instances'].append(dict(id='Floor',part_id=fid,version='1.0',source=f'../../Parts/{fid}/{fid}.blend',parent=None,translation=[0,0,0],rotation_euler_xyz=[0,0,0],scale=[1,1,1]))
    a['nodes'].append(dict(id='Floor',parent=None,translation=[0,0,0],rotation_euler_xyz=[0,0,0],scale=[1,1,1]))
    a['version']=a.get('version','1.0')+'+floor1';a['floor_fit']=dict(floor=fid,margin_cells=MARGIN,uniform_scale=s,translation=translation,body_instances=record['body_instances'],protrusion_instances=record['protrusion_instances'])
    a['axes']['units']='Assembly: 1 BU = 1 gameplay cell; native part units transformed by ModelFit'
    bpy.context.view_layer.update();bpy.context.scene.frame_set(1)
    stats=bw.geometry([o for o in bpy.context.scene.objects if o.type in bw.RENDERABLE])
    assert stats['nonmanifold_edges']==baseline['nonmanifold_edges'],(bid,'new nonmanifold edges',baseline,stats)
    # Floor is independently drawn beneath every static/rotating original layer.
    for layer in spec['layers']:layer['draw_order']+=1
    spec['layers'].insert(0,dict(id='floor',draw_order=0,rotates=False,pivot_bu=[0,0],instances=['Floor']))
    w,h=record['grid'];spec['bu_per_cell']=1.0;spec['footprint_bu']=[-w/2,-h/2,w/2,h/2]
    spec['height_range_bu']=[math.floor((stats['bounds_bu'][0][2]-.02)*100)/100,math.ceil((stats['bounds_bu'][1][2]+.02)*100)/100]
    for layer in spec['layers'][1:]:
        px,py=layer['pivot_bu'];layer['pivot_bu']=[px*s+translation[0],py*s+translation[1]]
    write(path,a);bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/spec['source']))
    proof=dict(id=bid,passed=True,scale=s,translation=translation,body_instances=record['body_instances'],body_bounds_cells=[transformed.min(axis=0).tolist(),transformed.max(axis=0).tolist()],floor_polygon=record['polygon'],geometry=stats,baseline_nonmanifold_edges=baseline['nonmanifold_edges'])
    write(path.parent/'floor-validation.json',proof)
    print('BLOCK_OK',bid,'scale',round(s,6),flush=True)
    return spec,proof

def main():
    config=read(ROOT/'floor-fit.json');profile=read(BACKUP/'SpriteBake/profile.json')
    if '--replay-baseline' not in sys.argv and any(read(ROOT/s['assembly']).get('floor_fit') for s in profile['blocks'].values()):
        raise RuntimeError('Floor migration already applied. Review newer model edits before explicitly using --replay-baseline; it replays the preserved original assemblies.')
    floors={r['floor']:r for r in config['blocks'].values()}
    for fid,record in floors.items():make_floor(fid,record)
    proofs=[]
    # All independent parts have passed before any dependent assembly is saved.
    for bid,record in config['blocks'].items():
        original=profile['blocks'][bid];folder=ROOT/original['assembly'];proof_path=folder.parent/'floor-validation.json'
        if '--resume' in sys.argv and proof_path.exists() and 'floor_fit' in read(folder):
            proof=read(proof_path);s=proof['scale'];translation=proof['translation'];spec=copy.deepcopy(original)
            for layer in spec['layers']:
                layer['draw_order']+=1;px,py=layer['pivot_bu'];layer['pivot_bu']=[px*s+translation[0],py*s+translation[1]]
            spec['layers'].insert(0,dict(id='floor',draw_order=0,rotates=False,pivot_bu=[0,0],instances=['Floor']))
            w,h=record['grid'];spec['bu_per_cell']=1.;spec['footprint_bu']=[-w/2,-h/2,w/2,h/2]
            stats=proof['geometry'];spec['height_range_bu']=[math.floor((stats['bounds_bu'][0][2]-.02)*100)/100,math.ceil((stats['bounds_bu'][1][2]+.02)*100)/100]
        else:spec,proof=fit(bid,record,profile)
        profile['blocks'][bid]=spec;proofs.append(proof)
    profile['material_roles'].update(FloorSurface='Color1',FloorArmor='Color2')
    write(ROOT/'SpriteBake/profile.json',profile)
    write(ROOT/'floor-validation.json',dict(passed=True,parts=len(floors),blocks=proofs,corner_cells=CORNER,frame_cells=FRAME,margin_cells=MARGIN))
    runpy.run_path(str(ROOT/'Tools/attach_floor_geometry.py'),run_name='__main__')
    runpy.run_path(str(ROOT/'Tools/preserve_floor_sources.py'),run_name='__main__')
    print('ALL_FLOORS_AND_FITS_OK',len(proofs),flush=True)

if __name__=='__main__':main()
