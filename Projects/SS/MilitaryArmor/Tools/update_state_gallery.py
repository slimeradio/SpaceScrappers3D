"""Replace changed exhibits only; retain all unchanged geometry and existing gallery placement."""
import bpy,json,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_animation_states import ROOT,ARCHIVE,STATIC,read,write,sha
OUT=ROOT/'Scenes'/'AllBlocks';SOURCE=OUT/'AllBlocks.blend'
backup=ARCHIVE/'Scenes'/'AllBlocks';backup.mkdir(parents=True,exist_ok=True)
for name in ['AllBlocks.blend','scene.json','README.md','validation.json']:
    if (OUT/name).exists() and not (backup/name).exists():shutil.copy2(OUT/name,backup/name)
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=str(SOURCE if selected else backup/'AllBlocks.blend'));bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;manifest=read((OUT if selected else backup)/'scene.json');entries={e['id']:e for e in manifest['blocks']};cell=manifest['cell_spacing_BU'];changed=[]
block_collection=next(c for c in scene.collection.children if c.name.startswith('Blocks'))
presentation=next(c for c in scene.collection.children if c.name.startswith('Presentation'))
# Keep the growing gallery out of dependency evaluation while importing each source scene.
layer=bpy.context.view_layer.layer_collection.children[block_collection.name];layer.exclude=True
for folder in sorted((ROOT/'Blocks').iterdir()):
    if not folder.is_dir():continue
    bid=folder.name
    if bid in STATIC or (selected and bid not in selected):continue
    source=folder/(bid+'.blend');a=read(folder/'assembly.json');state=read(folder/'state-authoring.json')
    existing=entries.get(bid);coll=bpy.data.collections.get(bid)
    if coll:
        for o in list(coll.objects):
            if o.name!='Exhibit.'+bid:bpy.data.objects.remove(o,do_unlink=True)
        anchor=bpy.data.objects['Exhibit.'+bid]
    else:
        coll=bpy.data.collections.new(bid);block_collection.children.link(coll)
        anchor=bpy.data.objects.new('Exhibit.'+bid,None);coll.objects.link(anchor);anchor['gallery_anchor']=True;anchor['block_id']=bid
    anchor['source']=str(source.relative_to(ROOT));anchor['state_authoring']='Blocks/'+bid+'/state-authoring.json'
    for action in list(bpy.data.actions):
        if action.name.startswith(bid+'::'):bpy.data.actions.remove(action)
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):
        dst.scenes=[src.scenes[0]];dst.actions=[n for n in src.actions if n.startswith(bid+'::')]
    for action in dst.actions:action.use_fake_user=True
    imported=dst.scenes[0];root=next(o for o in imported.objects if o.name==bid)
    objects=list(root.children_recursive)+[root];meshes=[o for o in objects if o.type=='MESH']
    for o in objects:
        coll.objects.link(o);o['gallery_block_id']=bid;o.name=bid+'::'+o.name
    root.parent=anchor;root.matrix_parent_inverse.identity();root.location=(0,0,0)
    # Local source bounds before exhibit translation, independent from earlier gallery anchor placement.
    oldpos=anchor.location.copy();anchor.location=(0,0,0)
    matrices={}
    def local_matrix(o):
        if o not in matrices:matrices[o]=(local_matrix(o.parent)@o.matrix_parent_inverse if o.parent and o.parent!=anchor else Matrix.Identity(4))@o.matrix_basis
        return matrices[o]
    pts=[local_matrix(o)@Vector(v) for o in meshes for v in o.bound_box]
    lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
    if existing:
        index=existing['row']*manifest['columns']+existing['column'];anchor.location=oldpos
    else:
        index=len(entries);row,col=divmod(index,manifest['columns']);x=(col-3.5)*cell;y=(3.5-row)*cell
        anchor.location=(x-(lo[0]+hi[0])/2,y-(lo[1]+hi[1])/2,.02-lo[2])
        proto=next(o for o in presentation.objects if o.type=='FONT')
        caption=proto.copy();caption.data=proto.data.copy();caption.name='Caption.'+bid;caption.data.body=bid+'  '+(a.get('title') or bid)
        caption.location=(x,y-cell*.40,.015);presentation.objects.link(caption)
        if len(caption.data.body)>60:caption.data.size*=60/len(caption.data.body)
    row,col=divmod(index,manifest['columns'])
    entry=dict(id=bid,title=a.get('title') or bid,catalog_id=a['catalog_id'],version=a['version'],source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),anchor=anchor.name,mesh_count=len(meshes),source_bounds_min=lo,source_bounds_max=hi,row=row,column=col,translation=list(anchor.location),scale=[1,1,1],state_controller=root.name)
    entries[bid]=entry;changed.append(bid);bpy.data.scenes.remove(imported)
    print('UPDATED_EXHIBIT',bid,flush=True)
manifest['blocks']=sorted(entries.values(),key=lambda e:(e['row'],e['column']));manifest['blocks_count']=len(entries);manifest['state_updated_blocks']=sorted(set(manifest.get('state_updated_blocks',[]))|set(changed))
assert len(entries)==64
scene['gallery_block_count']=64;scene['state_controls']='Select MA-...::MA-... root > Custom Properties; stashed actions are block specific.'
helper=bpy.data.texts.get('state_controls.py') or bpy.data.texts.new('state_controls.py');helper.clear();helper.write(Path(__file__).with_name('state_controls.py').read_text('utf-8-sig'))
write(OUT/'scene.json',manifest);layer.exclude=False;bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE),compress=True)
write(OUT/'README.md',(backup/'README.md').read_text('utf-8-sig')+'\n## Состояния: текущая редакция\n\nСцена обновлена до 64 блоков. Заменены только 55 изменённых/добавленных экспонатов; 9 статичных моделей сохранены. В каждом активном блоке корневой объект MA-...::MA-... содержит независимые Custom Properties. Actions импортированы по именам блока; state_controls.py доступен в Text Editor. Прежние превью относятся к прошлой редакции; актуальные состояния показаны в Exports/StatePreviews стиля. Проверка текущей сцены — state-validation.json.\n')
print('STATE_GALLERY_SAVED',len(entries),len(changed),flush=True)
