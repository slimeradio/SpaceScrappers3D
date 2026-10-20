"""MilitaryArmor all-current-blocks gallery. Imports source scenes; never rebuilds blocks or exports GLB."""
import bpy, sys, math, json, hashlib, csv
from pathlib import Path
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Scenes'/'AllBlocks'
PRE=OUT/'Previews'
BLEND=OUT/'AllBlocks.blend'

def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    value=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)
    path.write_bytes((value.replace('\r\n','\n').rstrip()+'\n').replace('\n','\r\n').encode('utf8'))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def render_previews():
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
    scene.render.resolution_x=2400;scene.render.resolution_y=2400;scene.render.resolution_percentage=100
    for camera,name in [('Camera.Overview','overview.png'),('Camera.Perspective','perspective.png')]:
        scene.camera=bpy.data.objects[camera];scene.render.filepath=str(PRE/name)
        print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)

def verify():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    scene=bpy.context.scene
    manifest=json.loads((OUT/'scene.json').read_text(encoding='utf8'))
    expected={p.parent.name for p in (ROOT/'Blocks').glob('*/assembly.json') if (p.parent/(p.parent.name+'.blend')).exists()}
    found={o['block_id'] for o in scene.objects if o.get('gallery_anchor',False)}
    assert found==expected=={e['id'] for e in manifest['blocks']},(len(found),len(expected))
    source_unchanged=all(sha(ROOT/e['source'])==e['source_sha256'] for e in manifest['blocks'])
    assert source_unchanged
    boxes=[]
    for entry in manifest['blocks']:
        anchor=bpy.data.objects[entry['anchor']]
        assert all(abs(v-1)<1e-7 for v in anchor.scale)
        meshes=[o for o in scene.objects if o.type=='MESH' and o.get('gallery_block_id')==entry['id']]
        assert meshes and len(meshes)==entry['mesh_count']
        assert all(o.data.materials and all(s.material for s in o.material_slots) for o in meshes)
        pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
        assert all(math.isfinite(c) for p in pts for c in p)
        lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
        assert lo[2]>=-1e-4,(entry['id'],lo)
        boxes.append((entry['id'],lo,hi))
    for i,(bid,lo,hi) in enumerate(boxes):
        for bid2,lo2,hi2 in boxes[i+1:]:
            assert hi[0]<lo2[0] or hi2[0]<lo[0] or hi[1]<lo2[1] or hi2[1]<lo[1],(bid,bid2)
    from bpy_extras.object_utils import world_to_camera_view
    assert not any('studio floor' in o.name.lower() for o in scene.objects)
    assert not any(o.instance_type=='COLLECTION' for o in scene.objects)
    for camera_name in ['Camera.Overview','Camera.Perspective']:
        for bid,lo,hi in boxes:
            for x in [lo[0],hi[0]]:
                for y in [lo[1],hi[1]]:
                    for z in [lo[2],hi[2]]:
                        projected=world_to_camera_view(scene,bpy.data.objects[camera_name],Vector((x,y,z)))
                        assert 0<=projected.x<=1 and 0<=projected.y<=1 and projected.z>0,(camera_name,bid,list(projected))
    report={'checks_passed':True,'scene_reopened':True,'all_current_blocks_included':len(found),'source_files_unchanged':source_unchanged,'unit_scale_preserved':True,'block_bounds_nonoverlapping':True,'both_cameras_frame_all_block_bounds':True,'legacy_collection_instances_realized':True,'materials_resolved':True,'mesh_count':sum(e['mesh_count'] for e in manifest['blocks']),'glb_generated':False}
    write(OUT/'validation.json',report);print('ALL_BLOCKS_VERIFIED',json.dumps(report),flush=True)

if '--verify' in sys.argv:
    verify();raise SystemExit
if '--render-only' in sys.argv:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND));render_previews();raise SystemExit

OUT.mkdir(parents=True,exist_ok=True);PRE.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.name='MilitaryArmor.AllBlocks';scene.frame_set(1)
scene.unit_settings.system='NONE'
block_collection=bpy.data.collections.new('Blocks — current sources');scene.collection.children.link(block_collection)
presentation=bpy.data.collections.new('Presentation — labels lights cameras');scene.collection.children.link(presentation)
with (ROOT.parent/'Catalog'/'blocks.csv').open(encoding='utf-8-sig',newline='') as f:
    catalog={r['ID']:r for r in csv.DictReader(f)}
entries=[]
for assembly_path in sorted((ROOT/'Blocks').glob('*/assembly.json')):
    bid=assembly_path.parent.name;source=assembly_path.parent/(bid+'.blend')
    if not source.exists():raise RuntimeError('Missing block source '+str(source))
    metadata=json.loads(assembly_path.read_text(encoding='utf-8-sig'))
    before=sha(source)
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):
        if not src.scenes:raise RuntimeError('No source scene '+bid)
        dst.scenes=[src.scenes[0]]
    imported=dst.scenes[0]
    # Some legacy sources contain a studio floor/cameras and use collection instances.
    # Only the actual assembly hierarchy belongs to the exhibit.
    source_root=next((o for o in imported.objects if o.name==bid),None)
    if source_root:
        descendants=set(source_root.children_recursive)|{source_root}
        objects=[o for o in imported.objects if o in descendants and o.type not in ('CAMERA','LIGHT')]
    else:
        objects=[o for o in imported.objects if o.type not in ('CAMERA','LIGHT') and not any(token in o.name.lower() for token in ('studio floor','review floor'))]
    collection=bpy.data.collections.new(bid);block_collection.children.link(collection)
    anchor=bpy.data.objects.new('Exhibit.'+bid,None);collection.objects.link(anchor)
    anchor['gallery_anchor']=True;anchor['block_id']=bid;anchor['source']=str(source.relative_to(ROOT));anchor.empty_display_size=.25
    pending=list(objects)
    while pending:
        instance=pending.pop()
        if instance.instance_type!='COLLECTION' or not instance.instance_collection:continue
        original_collection=instance.instance_collection
        originals=[o for o in original_collection.all_objects if o.type not in ('CAMERA','LIGHT')]
        copies={s:s.copy() for s in originals}
        from mathutils import Matrix
        for s,n in copies.items():
            collection.objects.link(n)
            if s.parent in copies:
                n.parent=copies[s.parent];n.matrix_parent_inverse=s.matrix_parent_inverse.copy();n.matrix_basis=s.matrix_basis.copy()
            else:
                n.parent=instance;n.matrix_parent_inverse=Matrix.Identity(4)
                n.matrix_basis=Matrix.Translation(-original_collection.instance_offset)@s.matrix_world
            n.name=instance.name+'::'+s.name
            objects.append(n);pending.append(n)
        instance.instance_type='NONE';instance.instance_collection=None
    assert any(o.type=='MESH' for o in objects),bid
    object_set=set(objects)
    for o in objects:
        
        if o.name not in collection.objects:collection.objects.link(o)
        o['gallery_block_id']=bid;o.name=bid+'::'+o.name
    for o in objects:
        if o.parent not in object_set:
            matrix=o.matrix_world.copy();o.parent=anchor;o.matrix_world=matrix
    meshes=[o for o in objects if o.type=='MESH']
    bpy.context.view_layer.update()
    points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    lo=Vector(tuple(min(v[i] for v in points) for i in range(3)));hi=Vector(tuple(max(v[i] for v in points) for i in range(3)))
    bpy.data.scenes.remove(imported)
    title=catalog.get(metadata.get('catalog_id'),{}).get('Название_пояснительное') or metadata.get('title') or bid
    entries.append({'id':bid,'title':title,'catalog_id':metadata.get('catalog_id'),'version':metadata.get('version'),'source':source.relative_to(ROOT).as_posix(),'source_sha256':before,'anchor':anchor.name,'mesh_count':len(meshes),'source_bounds_min':list(lo),'source_bounds_max':list(hi)})
    print('IMPORTED',bid,len(meshes),flush=True)

columns=8;rows=math.ceil(len(entries)/columns)
max_width=max(e['source_bounds_max'][0]-e['source_bounds_min'][0] for e in entries)
max_depth=max(e['source_bounds_max'][1]-e['source_bounds_min'][1] for e in entries)
cell=max(max_width,max_depth)*1.55+1.0
for index,e in enumerate(entries):
    row,col=divmod(index,columns);x=(col-(columns-1)/2)*cell;y=((rows-1)/2-row)*cell
    lo=e['source_bounds_min'];hi=e['source_bounds_max']
    position=(x-(lo[0]+hi[0])/2,y-(lo[1]+hi[1])/2,-lo[2]+.02)
    bpy.data.objects[e['anchor']].location=position
    e.update({'row':row,'column':col,'translation':list(position),'scale':[1,1,1]})

font=bpy.data.fonts.load('C:/Windows/Fonts/arial.ttf')
label_mat=bpy.data.materials.new('Gallery label');label_mat.diffuse_color=(.65,.76,.82,1);label_mat.use_nodes=True
shader=label_mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.65,.76,.82,1);shader.inputs['Roughness'].default_value=.8
shader.inputs['Emission Color'].default_value=(.45,.57,.63,1);shader.inputs['Emission Strength'].default_value=.4
for index,e in enumerate(entries):
    row,col=divmod(index,columns);x=(col-(columns-1)/2)*cell;y=((rows-1)/2-row)*cell
    curve=bpy.data.curves.new('Caption.'+e['id'],'FONT');curve.body=e['id']+'  '+e['title'];curve.font=font;curve.align_x='CENTER';curve.size=cell*.026;curve.extrude=0
    obj=bpy.data.objects.new('Caption.'+e['id'],curve);presentation.objects.link(obj);obj.location=(x,y-cell*.40,.015);curve.materials.append(label_mat)
    bpy.context.view_layer.update()
    if obj.dimensions.x>cell*.92:curve.size*=cell*.92/obj.dimensions.x

width=columns*cell;depth=rows*cell
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.035));floor=bpy.context.object;floor.name='Gallery floor';floor.scale=(width*.53,depth*.53,1)
for c in list(floor.users_collection):c.objects.unlink(floor)
presentation.objects.link(floor)
mat=bpy.data.materials.new('Neutral charcoal floor');mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.026,.035,.043,1);p.inputs['Roughness'].default_value=.85;floor.data.materials.append(mat)
scene.world=bpy.data.worlds.new('Gallery world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.24,.29,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for name,direction,power in [('Key',(30,-45,70),2.2),('Fill',(-55,20,50),1.0)]:
    data=bpy.data.lights.new(name,'SUN');data.energy=power;data.angle=math.radians(12)
    obj=bpy.data.objects.new(name,data);presentation.objects.link(obj);obj.rotation_euler=(-Vector(direction)).to_track_quat('-Z','Y').to_euler()
for name,loc,scale in [('Camera.Overview',(0,0,150),max(width,depth)*1.05),('Camera.Perspective',(width*.18,-depth*.62,depth*1.18),max(width,depth)*1.38)]:
    data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale;data.clip_end=2000
    obj=bpy.data.objects.new(name,data);presentation.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['Camera.Perspective'];scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=2400;scene.render.resolution_y=2400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene['gallery_block_count']=len(entries);scene['source_policy']='Current MilitaryArmor Blocks only. No archives, no other styles. Unit scale.'
for obj in bpy.context.selected_objects:obj.select_set(False)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.shading.type='MATERIAL'
            region=area.spaces.active.region_3d;region.view_location=(0,0,0);region.view_distance=max(width,depth)*.9;region.view_rotation=scene.camera.rotation_euler.to_quaternion()
# Bundle the caption font for a standalone gallery; source blocks are never saved.
bpy.ops.file.pack_all()
write(OUT/'scene.json',{'schema':'MilitaryArmor.AllBlocksScene/1','source_policy':'current Blocks only','blocks_count':len(entries),'columns':columns,'rows':rows,'cell_spacing_BU':cell,'units':'BU, physical scale unspecified','axes':{'up':'+Z','forward':'-Y'},'blocks':entries,'cameras':['Camera.Overview','Camera.Perspective'],'glb_generated':False})
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)
print('ALL_BLOCKS_SCENE_SAVED',len(entries),str(BLEND),flush=True)
render_previews()
