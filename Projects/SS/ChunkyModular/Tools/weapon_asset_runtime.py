"""Shared final-asset authoring for the six-weapon batch. No renders or texture writes."""
import bpy, csv, json, math, struct, copy, importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Vector, Matrix

STYLE=Path(__file__).resolve().parent.parent
PARTS=STYLE/'Parts'
BASE=STYLE/'Blocks'/'CM-T01'/'build_turret.py'
spec=importlib.util.spec_from_file_location('cm_geometry',BASE)
cm=importlib.util.module_from_spec(spec); spec.loader.exec_module(cm)
_mode=None
_root=None
_block=None
_instances=[]
_muzzles=[]
_expected=0
_title=''
_tracks=[]
_loaded=False

box=cm.box
cyl=cm.cyl
ring=cm.ring
profile=cm.profile
bolt=cm.bolt

def write(path,data):
    cm.js(Path(path),data)

def mesh(name,vertices,faces,mat='graphite',bevel=.02):
    data=bpy.data.meshes.new(name); data.from_pydata(vertices,[],faces); data.update()
    obj=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(obj)
    cm.finish_obj(obj,name,mat,bevel)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    return obj

def _materials():
    global _loaded
    if _loaded: return
    wanted={'graphite','steel','orange','ivory','rubber','weld','amber','cyan'}
    for pid in ['cm-receiver','cm-handle','cm-cheek-right','cm-barrel']:
        missing=wanted-set(cm.MATS)
        if not missing: break
        with bpy.data.libraries.load(str(PARTS/pid/(pid+'.blend')),link=False) as (src,dst):
            dst.materials=[name for name in src.materials if name in {'CM.'+key for key in missing}]
        for mat in dst.materials:
            if mat: cm.MATS[mat.name.split('.')[1]]=mat
    for name,col,power in [('cyan',(.03,.40,.7),1.4),('amber',(1,.29,.025),1.7)]:
        if name in cm.MATS: continue
        mat=bpy.data.materials.new('CM.'+name); mat.use_nodes=True
        node=mat.node_tree.nodes.get('Principled BSDF')
        node.inputs['Base Color'].default_value=(*col,1)
        node.inputs['Emission Color'].default_value=(*col,1)
        node.inputs['Emission Strength'].default_value=power
        node.inputs['Roughness'].default_value=.45; cm.MATS[name]=mat
    assert wanted<=set(cm.MATS), 'Missing materials: '+str(wanted-set(cm.MATS))
    _loaded=True
    bpy.context.preferences.filepaths.save_version=0

def socket(id,position,forward=(0,-1,0),up=(0,0,1),parent='root',role='mount'):
    f=Vector(forward); u=Vector(up)
    assert abs(f.length-1)<1e-5 and abs(u.length-1)<1e-5 and abs(f.dot(u))<1e-5
    return {'id':id,'position':list(position),'forward':list(forward),'up':list(up),
            'parent':parent,'role':role,'space':'local'}

def joint(name,parent=None,loc=(0,0,0)):
    obj=bpy.data.objects.new(name,None)
    (cm.ASSET if _mode=='part' else bpy.context.scene.collection).objects.link(obj)
    obj.parent=parent if parent is not None else _root
    obj.location=loc; obj.empty_display_type='PLAIN_AXES'; obj.empty_display_size=.10
    return obj

def key(obj,path,index,values):
    for frame,value in values:
        getattr(obj,path)[index]=value; obj.keyframe_insert(data_path=path,index=index,frame=frame)
    if obj.animation_data and obj.animation_data.action: obj.animation_data.action.name=obj.name+'.motion'
    _tracks.append({'node':obj.name,'path':path,'component':index,'keys':[[f,v] for f,v in values]})
    bpy.context.scene.frame_set(1)

def _logical(data):
    parent=_root if data.get('parent','root')=='root' else bpy.context.scene.objects[data['parent']]
    obj=joint('logical.'+data['id'],parent,data['position'])
    forward=Vector(data.get('forward',(0,-1,0))); up=Vector(data.get('up',(0,0,1)))
    assert abs(forward.length-1)<1e-5 and abs(up.length-1)<1e-5 and abs(forward.dot(up))<1e-5
    right=up.cross(forward)
    obj.rotation_euler=Matrix((right,-forward,up)).transposed().to_euler()
    obj['logical_metadata']=json.dumps(data,ensure_ascii=False)
    return obj

def _images_and_materials(objects):
    materials={}; images={}
    for obj in objects:
        if obj.type!='MESH': continue
        assert len(obj.data.vertices)>0
        assert all(slot.material is not None for slot in obj.material_slots),obj.name
        for slot in obj.material_slots:
            mat=slot.material; materials[mat.name]=True
            for node in mat.node_tree.nodes if mat.use_nodes else []:
                if node.type=='TEX_IMAGE' and node.image:
                    assert node.image.packed_file or Path(bpy.path.abspath(node.image.filepath)).exists(),node.image.name
                    images[node.image.name]=list(node.image.size)
    return sorted(materials),images

def _export(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
        export_animations=True,export_animation_mode='SCENE',export_extras=True,export_apply=True,export_yup=True)
    blob=path.read_bytes(); chunks=[]; offset=12
    while offset<len(blob):
        n,kind=struct.unpack_from('<II',blob,offset); chunks.append((kind,blob[offset+8:offset+8+n])); offset+=8+n
    doc=json.loads(chunks[0][1]); originals=doc.get('animations',[])
    if len(originals)>1:
        merged={'name':path.stem+' Demo','samplers':[],'channels':[]}; seen=set()
        for anim in originals:
            base=len(merged['samplers']); merged['samplers']+=copy.deepcopy(anim['samplers'])
            for channel in anim['channels']:
                identity=(channel['target']['node'],channel['target']['path'])
                if identity in seen: continue
                seen.add(identity); ch=copy.deepcopy(channel); ch['sampler']+=base; merged['channels'].append(ch)
        doc['animations']=[merged]+originals
        raw=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode('utf-8'); raw+=b' '*((-len(raw))%4)
        chunks[0]=(chunks[0][0],raw)
        payload=b''.join(struct.pack('<II',len(v),k)+v for k,v in chunks)
        path.write_bytes(struct.pack('<4sII',b'glTF',2,12+len(payload))+payload)
    assert all('bufferView' in image for image in doc.get('images',[]))
    assert all('uri' not in buffer for buffer in doc.get('buffers',[]))
    return doc

def part(pid,builder_fn,sockets=None,points=None,regions=None,animations=None):
    global _mode,_root,_tracks
    assert pid.startswith(('cm-cyclone-','cm-monitor-','cm-sniper-','cm-beam-','cm-bastion-','cm-fan-')), 'Part namespace is outside this batch: '+pid
    if (PARTS/pid/'part.json').exists():
        prior=json.loads((PARTS/pid/'part.json').read_text(encoding='utf-8'))
        assert prior['id']==pid and prior['version']=='1.0.0', 'Part version conflict: '+pid
    _materials(); _mode='part'; _tracks=[]
    _root=cm.setup_asset(pid); builder_fn()
    bpy.context.scene.frame_set(1)
    sockets=sockets or [socket('mount',(0,0,0))]; points=points or []
    for item in sockets+points: _logical(item)
    objs=list(bpy.context.scene.objects); mats,images=_images_and_materials(objs)
    low,high=cm.bounds(objs)
    data={'schema':'SS3D.authoring.part/1','id':pid,'version':'1.0.0','project':'SS','style':'ChunkyModular',
      'source':pid+'.blend','units':'design_unit','coordinate_system':{'handedness':'right','up':'+Z','forward':'-Y'},
      'origin':[0,0,0],'pivot':[0,0,0],'sockets':sockets,'functional_points':points,'mount_regions':regions or [],
      'animations':animations or [],'animation_tracks':list(_tracks),'materials':mats,'images':images,
      'material_library':'../../Materials/CM-T01/materials.json','scale_policy':'positive uniform instance scaling',
      'bounds':{'min':list(low),'max':list(high),'dimensions':list(high-low)},
      'emissive_regions':[{'object':o.name,'material':m.name} for o in objs if o.type=='MESH' for m in o.data.materials if m.name.startswith(('CM.amber','CM.cyan'))],
      'logical_only':'sockets and regions are invisible metadata, not physical fastening geometry'}
    _root['metadata_json']=json.dumps(data,ensure_ascii=False); _root['version']='1.0.0'
    dest=PARTS/pid; dest.mkdir(parents=True,exist_ok=True)
    write(dest/'part.json',data); bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/(pid+'.blend')),compress=True)
    _export(STYLE/'Exports'/'Parts'/(pid+'.glb'))
    print('FINAL_PART '+pid,flush=True)
    return data

def begin(block_id,expected_muzzles,title=''):
    global _mode,_root,_block,_instances,_muzzles,_expected,_title,_tracks,_loaded
    # Last saved part must not remain the current file when appending it.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cm.MATS.clear(); _loaded=False
    _materials(); cm.reset(); _mode='block'; _block=block_id; _instances=[]; _muzzles=[]; _tracks=[]
    _expected=expected_muzzles; _title=title
    _root=cm.empty(block_id)
    bpy.context.scene.frame_end=120; bpy.context.scene.render.fps=30
    return _root

def add(pid,instance,parent=None,loc=(0,0,0),rot=(0,0,0),scale=1.0):
    assert _mode=='block'
    meta=json.loads((PARTS/pid/'part.json').read_text(encoding='utf-8'))
    if isinstance(scale,(int,float)): scale=(scale,scale,scale)
    assert min(scale)>0 and max(scale)-min(scale)<1e-6, 'Use a parametric variant instead of nonuniform scaling'
    obj=cm.append_part(pid,instance,parent if parent is not None else _root,loc,rot)
    obj.scale=scale; obj['source_version']=meta['version']
    _instances.append({'id':instance,'part':pid,'version':meta['version'],'parent':obj.parent.name,
        'translation':list(loc),'rotation_xyz_radians':list(rot),'scale':list(scale)})
    return obj

def muzzle(id,parent,position,forward=(0,-1,0),up=(0,0,1),barrel_ref=''):
    data=socket(id,position,forward,up,parent.name,'projectile_origin')
    data['barrel_ref']=barrel_ref; _muzzles.append(data)
    return _logical(data)

def finish():
    assert _mode=='block' and len(_muzzles)==_expected
    rows=list(csv.DictReader((STYLE.parent/'Catalog'/'blocks.csv').open(encoding='utf-8-sig',newline='')))
    row=next(r for r in rows if r['ID']==_block)
    xml=ET.fromstring('<Root>'+row['Стволы_XML']+'</Root>')
    barrel_ids=[node.attrib['Name'] for node in xml.findall('Barrel')]
    assert len(barrel_ids)==_expected, 'Catalog barrel count mismatch'
    assert sorted(p['barrel_ref'] for p in _muzzles)==sorted(barrel_ids), 'Muzzle references must match catalog IDs'
    scene=bpy.context.scene; scene.frame_set(1)
    objects=list(scene.objects); meshes=[o for o in objects if o.type=='MESH']
    assert meshes and not any(o.type in ('LIGHT','CAMERA','FONT') for o in objects)
    canonical={}
    for obj in meshes:
        for slot in obj.material_slots:
            key='.'.join(slot.material.name.split('.')[:2]); canonical.setdefault(key,slot.material); slot.material=canonical[key]
    mats,images=_images_and_materials(objects); low,high=cm.bounds(meshes)
    dg=bpy.context.evaluated_depsgraph_get(); triangles=0
    for obj in meshes:
        ev=obj.evaluated_get(dg); data=ev.to_mesh(); data.calc_loop_triangles(); triangles+=len(data.loop_triangles); ev.to_mesh_clear()
    poses=[]
    for frame in [1,16,31,46,61,91,120]:
        scene.frame_set(frame); bpy.context.view_layer.update()
        values=[]
        for item in _muzzles:
            node=scene.objects['logical.'+item['id']]
            direction=(node.matrix_world.to_quaternion()@Vector((0,-1,0))).normalized()
            assert abs(direction.length-1)<1e-6
            values.append({'id':item['id'],'position':list(node.matrix_world.translation),'direction':list(direction)})
        poses.append({'frame':frame,'muzzles':values})
    scene.frame_set(1)
    data={'schema':'SS3D.authoring.block/1','id':_block,'catalog_id':_block,'title':_title,'version':'1.0.0',
      'project':'SS','style':'ChunkyModular','units':'design_unit','up':'+Z','forward':'-Y','handedness':'right',
      'catalog_grid_cells':[int(row['Ширина_клеток']),int(row['Высота_клеток'])],
      'cell_scale':'not defined; grid footprint is reference metadata, not meters',
      'instances':_instances,'functional_points':_muzzles,'animation_tracks':_tracks,
      'rest_bounds':{'min':list(low),'max':list(high),'dimensions':list(high-low)},
      'materials':mats,'sampled_poses':poses,'game_import':'not performed; local authoring metadata only'}
    _root['metadata_json']=json.dumps(data,ensure_ascii=False)
    dest=STYLE/'Blocks'/_block; dest.mkdir(parents=True,exist_ok=True)
    write(dest/'assembly.json',data)
    write(STYLE/'Kits'/_block/'kit.json',{'id':_block+'-kit','version':'1.0.0','parts':[{'id':p,'version':json.loads((PARTS/p/'part.json').read_text(encoding='utf-8'))['version']} for p in sorted({i['part'] for i in _instances})]})
    bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=str(dest/(_block+'.blend')),compress=True)
    output=STYLE/'Exports'/_block; doc=_export(output/(_block+'.glb'))
    report={'id':_block,'status':'passed','instances':len(_instances),'mesh_objects':len(meshes),'triangles':triangles,
        'logical_muzzles':len(_muzzles),'catalog_barrel_ids':barrel_ids,'animations':len(doc.get('animations',[])),
        'embedded_images':len(doc.get('images',[])),'sampled_frames':[p['frame'] for p in poses],
        'no_presentation_assets':True,'scope':'Source and GLB validation; no game integration.'}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(output/(_block+'.glb')))
    bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    imported=[o for o in bpy.context.scene.objects if o.type=='MESH']; ilow,ihigh=cm.bounds(imported)
    assert len(imported)==len(meshes), 'Reimport mesh count changed'
    assert (ilow-low).length<.015 and (ihigh-high).length<.015, 'Reimport bounds changed'
    report['real_reimport']={'mesh_count_matches':True,'bounds_match':True,'self_contained':True}
    write(output/'validation.json',report)
    print('FINAL_BLOCK '+_block+' '+str(triangles)+' triangles',flush=True)
    return report
