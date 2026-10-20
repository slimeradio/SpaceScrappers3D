"""Render all current MilitaryArmor exhibits at exact 45-degree elevation/azimuth and top. No source saves."""
import bpy,sys,math,json,hashlib,time,struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
SCENE=ROOT/'Scenes'/'AllBlocks'/'AllBlocks.blend'
OUT=ROOT/'Exports'/'Renders-45-Top'
OUT.mkdir(parents=True,exist_ok=True)
STATE=OUT/'render-manifest.json'

def write(path,data):
    value=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)
    Path(path).write_bytes((value.replace('\r\n','\n').rstrip()+'\n').replace('\n','\r\n').encode('utf8'))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
scene_hash=sha(SCENE)
manifest={'schema':'MilitaryArmor.RenderSet45Top/1','source_scene':SCENE.relative_to(ROOT).as_posix(),'source_sha256':scene_hash,'individual_resolution':[1536,1536],'overview_resolution':[3200,3200],'samples':16,'elevation_degrees':45,'azimuth_degrees':45,'glb_generated':False,'files':[],'complete':False}
if STATE.exists():
    previous=json.loads(STATE.read_text(encoding='utf8'))
    if previous.get('source_sha256')==scene_hash and previous.get('schema')==manifest['schema']:
        manifest=previous
completed={e['file']:e for e in manifest['files']}
bpy.ops.wm.open_mainfile(filepath=str(SCENE))
scene=bpy.context.scene;scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
preferences=bpy.context.preferences.addons['cycles'].preferences
preferences.compute_device_type='OPTIX';preferences.get_devices()
for device in preferences.devices:device.use=(device.type=='OPTIX')
scene.cycles.device='GPU'
if hasattr(scene.cycles,'denoising_use_gpu'):scene.cycles.denoising_use_gpu=True
scene.render.use_persistent_data=True
print('RENDER_BACKEND','OPTIX',[d.name for d in preferences.devices if d.use],flush=True)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.render.use_file_extension=True
camera=bpy.data.objects.new('RenderSet.Camera',bpy.data.cameras.new('RenderSet.Camera'))
scene.collection.objects.link(camera);camera.data.type='ORTHO';camera.data.clip_start=.001;camera.data.clip_end=10000;scene.camera=camera
anchors={o['block_id']:o for o in scene.objects if o.get('gallery_anchor',False)}
metadata=json.loads((ROOT/'Scenes'/'AllBlocks'/'scene.json').read_text(encoding='utf8'))
expected={e['id'] for e in metadata['blocks']};assert set(anchors)==expected
block_collections={bid:next(c for c in anchors[bid].users_collection) for bid in anchors}
model_objects={bid:[o for o in scene.objects if o.get('gallery_block_id')==bid and o.type in ('MESH','CURVE','FONT')] for bid in anchors}
assert all(model_objects.values())
labels=[o for o in scene.objects if o.name.startswith('Caption.')]
points={}
bpy.context.view_layer.update()
for bid,objects in model_objects.items():
    points[bid]=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    assert all(math.isfinite(c) for p in points[bid] for c in p)
all_points=[p for pp in points.values() for p in pp]
floor=bpy.data.objects.get('Gallery floor')
if floor:
    minx=min(p.x for p in all_points);maxx=max(p.x for p in all_points);miny=min(p.y for p in all_points);maxy=max(p.y for p in all_points)
    floor.location=((minx+maxx)/2,(miny+maxy)/2,min(p.z for p in all_points)-.035)
    size=max(maxx-minx,maxy-miny)*3
    floor.scale=(size,size,1)

def configure_camera(points,view):
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    target=(low+high)/2
    direction=Vector((1,-1,math.sqrt(2))).normalized() if view=='45deg' else Vector((0,0,1))
    distance=max((high-low).length,1)*4+20
    camera.location=target+direction*distance
    camera.rotation_euler=(0,0,0) if view=='top' else (-direction).to_track_quat('-Z','Y').to_euler()
    inverse=camera.rotation_euler.to_quaternion().inverted()
    corners=[Vector((x,y,z)) for x in (low.x,high.x) for y in (low.y,high.y) for z in (low.z,high.z)]
    local=[inverse@(p-target) for p in corners]
    spanx=max(p.x for p in local)-min(p.x for p in local);spany=max(p.y for p in local)-min(p.y for p in local)
    camera.data.ortho_scale=max(spanx,spany,.1)*1.20
    bpy.context.view_layer.update()
    for p in corners:
        projected=world_to_camera_view(scene,camera,p)
        assert 0<=projected.x<=1 and 0<=projected.y<=1 and projected.z>0
    return {'location':list(camera.location),'rotation_euler_xyz':list(camera.rotation_euler),'ortho_scale':camera.data.ortho_scale,'all_bounds_in_frame':True,'elevation_degrees':45 if view=='45deg' else 90,'azimuth_degrees':45 if view=='45deg' else 0}

def valid_file(name,resolution):
    path=OUT/name
    if not path.exists() or path.stat().st_size<1000:return False
    with path.open('rb') as f:header=f.read(24)
    return header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(resolution,resolution)

jobs=[(bid,view,1536) for bid in sorted(anchors) for view in ('45deg','top')]+[('ALL',view,3200) for view in ('45deg','top')]
manifest['expected_images']=len(jobs);manifest['block_count']=len(anchors);write(STATE,manifest)
for collection in block_collections.values():collection.hide_render=True
for obj in labels:obj.hide_render=True
last=None
started=time.time()
for index,(bid,view,resolution) in enumerate(jobs,1):
    name=bid+'_'+view+'.png'
    if name in completed and valid_file(name,resolution):
        print('SKIP',index,len(jobs),name,flush=True);continue
    if bid!=last:
        for key,collection in block_collections.items():collection.hide_render=(bid!='ALL' and key!=bid)
        for obj in labels:obj.hide_render=(bid!='ALL')
        last=bid
    scene.render.resolution_x=resolution;scene.render.resolution_y=resolution
    if bid=='ALL':
        camera_points=all_points+[o.matrix_world@Vector(v) for o in labels for v in o.bound_box]
    else:camera_points=points[bid]
    pose=configure_camera(camera_points,view)
    scene.render.filepath=str(OUT/name)
    print('RENDER_START',index,len(jobs),name,flush=True)
    t=time.time()
    try:bpy.ops.render.render(write_still=True)
    except RuntimeError:
        print('GPU_RETRY_ON_CPU',name,flush=True)
        scene.cycles.device='CPU';scene.render.use_persistent_data=False
        if hasattr(scene.cycles,'denoising_use_gpu'):scene.cycles.denoising_use_gpu=False
        bpy.ops.render.render(write_still=True)
    assert valid_file(name,resolution),name
    entry={'id':bid,'view':view,'file':name,'resolution':[resolution,resolution],'bytes':(OUT/name).stat().st_size,'seconds':round(time.time()-t,2),'camera':pose}
    completed[name]=entry;manifest['files']=list(completed.values());write(STATE,manifest)
    print('RENDER_DONE',index,len(jobs),name,'seconds',entry['seconds'],flush=True)
assert all(valid_file(bid+'_'+view+'.png',resolution) for bid,view,resolution in jobs)
assert sha(SCENE)==scene_hash
manifest['complete']=True;manifest['source_scene_unchanged']=True;manifest['actual_images']=len(jobs);manifest['last_run_seconds']=round(time.time()-started,2);write(STATE,manifest)
write(OUT/'README.md','# Рендеры всех блоков MilitaryArmor\n\n58 блоков, по два изображения: <ID>_45deg.png и <ID>_top.png, 1536 x 1536. ALL_45deg.png и ALL_top.png — общие виды всей сцены, 3200 x 3200. Всего 118 PNG в этой папке.\n\n45deg: ортографическая камера, возвышение 45 градусов над горизонталью и азимут 45 градусов относительно переднего направления -Y (спереди справа). top: строго сверху, +Z, направление вверх изображения +Y. Для отдельных моделей камера вписана по габаритам; геометрия/масштаб объектов не менялись. Материалы и освещение одинаковы для обоих ракурсов.\n\nИсточник: Scenes/AllBlocks/AllBlocks.blend. Исходная сцена и блоки не перезаписывались. Все текущие 58 моделей включены. GLB не создавался. render-manifest.json содержит точные параметры камер, список файлов, размеры и хеш исходной сцены.\n')
print('RENDER_SET_COMPLETE',len(jobs),str(OUT),flush=True)
