"""Read-only Blender -> compact viewer scene, geometry and state controls. No glTF/GLB."""
import ast, base64, hashlib, json, math, os, sys
from array import array
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
STYLE=ROOT/'Projects/SS/MilitaryArmor'

def expression(text):
    def node(n):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return float(n.value)
        if isinstance(n,ast.Name):return ['var',n.id]
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):return ['neg' if isinstance(n.op,ast.USub) else 'pos',node(n.operand)]
        ops={ast.Add:'+',ast.Sub:'-',ast.Mult:'*',ast.Div:'/',ast.Pow:'**'}
        if isinstance(n,ast.BinOp) and type(n.op) in ops:return [ops[type(n.op)],node(n.left),node(n.right)]
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'sin','cos','min','max','abs'}:return [n.func.id,*[node(a) for a in n.args]]
        raise ValueError('Unsupported state expression: '+text)
    return node(ast.parse(text,mode='eval').body)

def binding(fc,controller,owner):
    variables={}
    for v in fc.driver.variables:
        t=v.targets[0]
        key=ast.literal_eval(t.data_path[1:-1]) if t.data_path.startswith('[') else None
        if controller is not None and t.id==controller and key in controller:variables[v.name]={'control':key}
        else:
            try:variables[v.name]={'constant':float(t.id.path_resolve(t.data_path))}
            except Exception:raise ValueError('Unresolved state variable on '+owner)
    return {'expression':expression(fc.driver.expression),'variables':variables}

def packed(values,kind='f'):return base64.b64encode(array(kind,values).tobytes()).decode('ascii')

def export(source,target):
    bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1)
    candidates=[o for o in scene.objects if o.type=='EMPTY' and (STYLE/'Blocks'/o.name/'state-authoring.json').exists()]
    controller=next((o for o in candidates if o.name.startswith('MA-')),None)
    meta={};assembly={}
    if controller:
        folder=STYLE/'Blocks'/controller.name;meta=json.loads((folder/'state-authoring.json').read_text('utf8'));assembly=json.loads((folder/'assembly.json').read_text('utf8'))
        objects=[controller,*controller.children_recursive]
    else:objects=[o for o in scene.objects if o.type not in {'CAMERA','LIGHT'}]
    objects=[o for o in objects if o.type in {'MESH','EMPTY'} and not o.hide_render]
    # Realize old collection instances in memory only.
    from mathutils import Matrix
    pending=list(objects)
    while pending:
        inst=pending.pop()
        if inst.instance_type!='COLLECTION' or not inst.instance_collection:continue
        coll=inst.instance_collection;copies={s:s.copy() for s in coll.all_objects if s.type in {'MESH','EMPTY'}}
        for s,o in copies.items():
            scene.collection.objects.link(o);o.name=inst.name+'::'+s.name;o.parent=copies.get(s.parent,inst)
            o.matrix_basis=s.matrix_basis.copy() if s.parent in copies else Matrix.Translation(-coll.instance_offset)@s.matrix_world
            objects.append(o);pending.append(o)
        inst.instance_type='NONE';inst.instance_collection=None
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();members=set(objects)
    materials={};material_keys={};geometries={};nodes=[];motion=[]
    for o in objects:
        local=o.matrix_local if o.parent in members else o.matrix_world
        pos,quat,scale=local.decompose()
        item={'id':o.name,'parent':o.parent.name if o.parent in members else None,'position':list(pos),'quaternion':[quat.x,quat.y,quat.z,quat.w],'scale':list(scale),'euler':list(o.rotation_euler),'part_id':o.get('part_id')}
        if meta and o.animation_data:
            for fc in o.animation_data.drivers:
                if fc.data_path in {'location','rotation_euler','scale'}:
                    motion.append(dict(node=o.name,path=fc.data_path,axis=fc.array_index,**binding(fc,controller,o.name)))
        if o.type=='MESH':
            ev=o.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();positions=[];normals=[];uv=[];groups=[];offset=0
            slots=list(o.material_slots);ids=[]
            for slot in slots:
                mat=slot.material;bs=mat.node_tree.nodes.get('Principled BSDF') if mat and mat.node_tree else None
                data={'color':list(bs.inputs['Base Color'].default_value)[:3] if bs else [.3,.3,.3],'metalness':bs.inputs['Metallic'].default_value if bs else 0,'roughness':bs.inputs['Roughness'].default_value if bs else .5,'emissive':list(bs.inputs['Emission Color'].default_value)[:3] if bs else [0,0,0],'intensity':bs.inputs['Emission Strength'].default_value if bs else 0,'drivers':[]}
                if bs and mat.node_tree.animation_data:
                    for fc in mat.node_tree.animation_data.drivers:
                        if fc.data_path==bs.inputs['Emission Strength'].path_from_id('default_value'):field='intensity'
                        elif fc.data_path==bs.inputs['Emission Color'].path_from_id('default_value'):field='emissive'
                        else:continue
                        data['drivers'].append(dict(field=field,axis=fc.array_index,**binding(fc,controller,mat.name)))
                key=json.dumps(data,sort_keys=True)
                if key not in material_keys:
                    mid='mat-'+str(len(materials));material_keys[key]=mid;data['title']=mat.name.split('::')[-1] if mat else 'Поверхность';materials[mid]=data
                ids.append(material_keys[key])
            if not ids:raise ValueError('Mesh without materials: '+o.name)
            by_mat={}
            for tri in mesh.loop_triangles:by_mat.setdefault(tri.material_index,[]).append(tri)
            for mi,triangles in sorted(by_mat.items()):
                start=offset
                for tri in triangles:
                    for vi,li in zip(tri.vertices,tri.loops):
                        positions.extend(mesh.vertices[vi].co);normals.extend(mesh.corner_normals[li].vector)
                        if mesh.uv_layers.active:uv.extend(mesh.uv_layers.active.data[li].uv)
                        offset+=1
                groups.append([start,offset-start,min(mi,len(ids)-1)])
            geo={'position':packed(positions),'normal':packed(normals),'uv':packed(uv) if uv else None,'groups':groups}
            raw=json.dumps(geo,separators=(',',':'));gid=hashlib.sha256(raw.encode()).hexdigest()[:20];geometries.setdefault(gid,geo)
            item.update(geometry=gid,materials=ids);ev.to_mesh_clear()
        nodes.append(item)
    controls={k:dict(v,default=float(controller[k])) for k,v in meta.get('controls',{}).items() if controller and k in controller}
    clips=[];fps=scene.render.fps/scene.render.fps_base
    for clip in meta.get('clips',[]):
        action=bpy.data.actions.get(clip['name'])
        if not action:continue
        start,end=clip['frames'];tracks=[]
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        if fc.data_path.startswith('['):
                            key=ast.literal_eval(fc.data_path[1:-1])
                            if key in controls:tracks.append({'control':key,'keys':[[(p.co.x-start)/fps,p.co.y] for p in fc.keyframe_points]})
        if tracks:clips.append(dict(name=clip['name'].split('::')[-1],duration=(end-start)/fps,loop=clip['loop'],tracks=tracks))
    if not any('geometry' in n for n in nodes):raise ValueError('Файл не содержит видимой геометрии.')
    pose_clips=[]
    if not meta and any(o.animation_data for o in objects) and scene.frame_end>scene.frame_start:
        first,last=scene.frame_start,scene.frame_end;steps=min(480,last-first);sampled={o.name:{'position':[],'quaternion':[],'scale':[]} for o in objects if o.animation_data};times=[]
        for j in range(steps+1):
            frame=first+(last-first)*j/steps;scene.frame_set(int(frame),subframe=frame-int(frame));times.append((frame-first)/fps)
            for o in objects:
                if o.name not in sampled:continue
                matrix=o.matrix_local if o.parent in members else o.matrix_world;pos,q,scale=matrix.decompose()
                sampled[o.name]['position'].extend(pos);sampled[o.name]['quaternion'].extend([q.x,q.y,q.z,q.w]);sampled[o.name]['scale'].extend(scale)
        tracks=[]
        for name,channels in sampled.items():
            for field,values in channels.items():
                size=4 if field=='quaternion' else 3
                if any(abs(v-values[i%size])>1e-6 for i,v in enumerate(values)):tracks.append({'node':name,'field':field,'times':times,'values':values})
        if tracks:pose_clips=[{'name':'Анимация файла','duration':(last-first)/fps,'tracks':tracks}]
        scene.frame_set(1)
    result={'schema':'SpaceScrappers3D.BlendScene/1','source':source.name,'id':meta.get('id',source.stem),'nodes':nodes,'geometries':geometries,'materials':materials,'motion':motion,'controls':controls,'presets':meta.get('presets',{}),'clips':clips,'pose_clips':pose_clips,'instances':assembly.get('instances',[]),'static_reason':meta.get('static_reason')}
    target.parent.mkdir(parents=True,exist_ok=True)
    pending=target.with_name(target.name+'.'+str(os.getpid())+'.tmp')
    pending.write_bytes((json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\r\n').encode('utf8'));pending.replace(target)
    print('VIEWER_SCENE_READY',len(nodes),len(geometries),len(materials),len(clips),flush=True)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    if args==['--all']:
        results=[]
        for source in sorted((STYLE/'Blocks').glob('*/*.blend')):
            folder=source.parent;output=STYLE/'Exports/ViewerStates'/folder.name;output.mkdir(parents=True,exist_ok=True)
            digest=hashlib.sha256()
            for file in [source,folder/'assembly.json',folder/'state-authoring.json',Path(__file__).resolve()]:
                if file.is_file():digest.update(file.read_bytes())
            key=digest.hexdigest();target=output/'scene.json'
            if not target.exists() or not (output/'fingerprint.txt').exists() or (output/'fingerprint.txt').read_text()!=key:
                export(source,target);(output/'fingerprint.txt').write_text(key,encoding='utf8')
            results.append(folder.name);print('VIEWER_BLOCK_READY',folder.name,flush=True)
        (STYLE/'Exports/ViewerStates/prepared.json').write_bytes((json.dumps({'blocks':results,'count':len(results),'source_files_modified':False,'glb_generated':False},indent=2)+'\r\n').replace('\n','\r\n').replace('\r\r\n','\r\n').encode('utf8'))
    else:
        source,target=args;export(Path(source),Path(target))
