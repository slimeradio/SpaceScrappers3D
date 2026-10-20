"""MA-W07: compact single-bore ballistic point defense; no export side effects."""
import sys, math, json, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy, bmesh
from mathutils import Vector
from weapon_batch_core import Part, Assembly, ROOT, AXES, write
BID='MA-W07'
FOLDER=ROOT/'Blocks'/BID

def socket(i,p,role='structural'):
    return dict(id=i,role=role,position=list(p),forward=[0,-1,0],up=[0,0,1],allowed_scale=[1,1,1])

def check_part(p):
    checks=[]
    for o in p.coll.objects:
        if o.type!='MESH': continue
        bm=bmesh.new();bm.from_mesh(o.data)
        assert all(e.is_manifold for e in bm.edges),o.name
        assert all(f.calc_area()>1e-10 for f in bm.faces),o.name
        assert bm.calc_volume(signed=True)>0,o.name
        checks.append(dict(object=o.name,vertices=len(bm.verts),faces=len(bm.faces),closed_manifold=True,positive_volume=True))
        bm.free();assert len(o.data.materials)>0
    assert checks
    write(ROOT/'Parts'/p.pid/'validation.json',dict(checks_passed=True,checked_before_assembly=True,meshes=checks))

def render(path,view=(8,-8.3,12.3137085),target=(0,-.3,1),scale=5.5,gray=False):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    try:
        pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
        for d in pref.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
    except Exception:scene.cycles.device='CPU'
    scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Preview world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.32
    temp=[]
    bpy.ops.object.camera_add(location=view);cam=bpy.context.object;temp.append(cam)
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    if view[0]==target[0] and view[1]==target[1]:cam.rotation_euler=(0,0,0)
    cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam
    for loc,power,size in [((2,-4,7),1100,5),((-4,-1,4),800,4),((2,4,6),1500,4)]:
        bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;temp.append(o);o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    saved=[]
    if gray:
        for m in bpy.data.materials:
            if not m.use_nodes:continue
            n=m.node_tree.nodes.get('Principled BSDF')
            if not n:continue
            col=tuple(n.inputs['Base Color'].default_value);saved.append((n,col,n.inputs['Emission Strength'].default_value))
            y=.2126*col[0]+.7152*col[1]+.0722*col[2];n.inputs['Base Color'].default_value=(y,y,y,1);n.inputs['Emission Strength'].default_value=0
    path.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    for n,col,power in saved:n.inputs['Base Color'].default_value=col;n.inputs['Emission Strength'].default_value=power
    for o in temp:bpy.data.objects.remove(o,do_unlink=True)
    scene.camera=None

def build_parts():
    p=Part(BID+'-P01','Trefoil low-profile point-defense pedestal')
    p.cyl('Low stationary drive case',(0,0,.17),1.00,.34,'Dark',verts=48)
    p.ring('Turret bearing race',(0,0,.38),.84,.65,.15,'Z','Titanium',48)
    for angle in [30,150,270]:
        a=math.radians(angle);x,y=1.00*math.cos(a),1.00*math.sin(a)
        o=p.panel('Triangular radial foot',(x,y,.18),(.70,1.12,.30),'Ceramic',.25);o.rotation_euler.z=a-math.pi/2
        o=p.panel('Foot graphite inset',(x,y,.345),(.32,.70,.035),'Titanium',.12);o.rotation_euler.z=a-math.pi/2
    p.ring('Recessed encoder',(0,0,.46),.76,.69,.025,'Z','Signal',48)
    p.save(mounts=[socket('bottom',(0,0,0)),socket('yaw',(0,0,.48),'yaw')],notes='Compact trefoil footprint; no rectangular generic tray. Unit scale only.')
    check_part(p);render(ROOT/'Parts'/p.pid/'Previews/perspective.png',target=(0,0,.2),scale=3.6)
    p=Part(BID+'-P02','Asymmetric drum-fed tracking saddle')
    p.cyl('Yaw direct drive',(0,0,.12),.68,.24,'Dark',verts=48)
    p.panel('Tracking saddle sill',(0,0,.31),(1.75,1.32,.22),'Titanium',.32)
    for s in [-1,1]:
        p.section('Short elevation cheek',[(-.45,s*.67,.62,.30,.58,.09),(.0,s*.70,.74,.37,.74,.12),(.54,s*.53,.57,.31,.48,.10)],'Ceramic')
        p.cyl('Elevation trunnion',(s*.70,0,.79),.22,.18,'Steel','X',24)
    p.cyl('Offset ammunition drum',(-1.02,.14,.67),.49,.50,'Titanium','X',32)
    p.cyl('Faceted feed drum lid',(-1.29,.14,.67),.45,.06,'Ceramic','X',16)
    p.ring('Drum concentric seal',(-1.332,.14,.67),.34,.28,.026,'X','Dark',32)
    p.cyl('Drum central feed spindle',(-1.35,.14,.67),.16,.035,'Steel','X',16)
    p.section('Enclosed feed bridge',[(-.20,-.79,.72,.26,.28,.07),(.30,-.79,.72,.26,.28,.07)],'Armor')
    p.section('Opposite compact tracking pod',[(-.50,.99,.83,.37,.46,.1),(.30,.99,.90,.45,.56,.14),(.58,.86,.83,.30,.40,.1)],'Armor')
    p.box('Tracking pod optical recess',(.99,-.514,.83),(.27,.025,.12),'Dark',.009)
    p.box('Tracking pod split aperture',(.99,-.532,.84),(.17,.012,.035),'Optic',.003)
    p.panel('Rear service landing',(0,.53,.61),(.82,.66,.09),'Titanium',.14)
    p.save(mounts=[socket('root',(0,0,0),'yaw'),socket('elevation',(0,0,.79),'elevation'),socket('service',(0,.53,.66),'accessory')],notes='Left transverse ammunition drum, right armored sensor; asymmetric silhouette. No shell props or exposed belts.')
    check_part(p);render(ROOT/'Parts'/p.pid/'Previews/perspective.png',target=(-.1,0,.55),scale=3.8)
    p=Part(BID+'-P03','Single short ventilated machinegun')
    p.section('Narrow ballistic receiver',[(-.61,0,0,.61,.40,.1),(.35,0,.04,.72,.55,.14),(.65,0,.02,.43,.35,.10)],'Titanium')
    p.section('Receiver dorsal wedge',[(-.46,0,.24,.48,.11,.035),(.30,0,.35,.63,.13,.04),(.61,0,.22,.35,.1,.03)],'Ceramic')
    p.ring('One actual open barrel',(0,-1.32,0),.13,.075,1.55,'Y','Steel',32)
    # A short open cage is recognizably a ballistic cooling shroud, not an energy coil.
    for y in [-.72,-1.18,-1.63]:p.ring('Ventilated shroud collar',(0,y,0),.245,.195,.10,'Y','Titanium',12)
    for a in [45,135,225,315]:
        angle=math.radians(a);x,z=.213*math.cos(angle),.213*math.sin(angle)
        p.box('Open longitudinal cage rib',(x,-1.18,z),(.075,1.02,.075),'Armor',.014)
    p.ring('Compact muzzle crown',(0,-2.08,0),.17,.075,.15,'Y','Steel',16)
    p.box('Receiver charging cover',(.365,.10,.04),(.032,.46,.18),'Ceramic',.012)
    p.save(mounts=[socket('pivot',(0,0,0),'elevation')],points=[dict(id='muzzle',node='socket.pivot',role='projectile-muzzle',position=[0,-2.16,0],direction=[0,-1,0],up=[0,0,1])],notes='Exactly one hollow bullet bore. Static single barrel; no invented rotor or laser emission.')
    check_part(p);render(ROOT/'Parts'/p.pid/'Previews/perspective.png',target=(0,-.7,0),scale=3.6)

def main():
    reused=ROOT/'Parts/MA-P06/MA-P06.blend';hash_before=hashlib.sha256(reused.read_bytes()).hexdigest()
    build_parts()
    a=Assembly(BID,'point-defense-turret',[1,1],'Пулемётная турель ближней обороны')
    a.instance('Pedestal',BID+'-P01')
    yaw=a.node('Yaw',a.root,(0,0,.48));a.instance('TrackingSaddle',BID+'-P02',yaw)
    elev=a.node('Elevation',yaw,(0,0,.79));recoil=a.node('Recoil',elev);a.instance('SingleMachinegun',BID+'-P03',recoil)
    a.instance('ServiceCartridge','MA-P06',yaw,(0,.53,.66))
    a.animate_rotation(yaw,'Z',[(1,0),(30,-60),(60,0),(90,60),(120,0)])
    a.animate_rotation(elev,'X',[(1,0),(30,-18),(60,8),(90,-18),(120,0)])
    a.animate_location(recoil,'Y',[(1,0),(40,0),(42,.05),(48,0),(120,0)])
    scene=bpy.context.scene;scene.frame_end=120;scene.frame_set(1);bpy.context.view_layer.update()
    connections=[dict(parent_instance='Pedestal',parent_socket='yaw',child_instance='TrackingSaddle',child_socket='root',node_chain=['Yaw']),dict(parent_instance='TrackingSaddle',parent_socket='elevation',child_instance='SingleMachinegun',child_socket='pivot',node_chain=['Elevation','Recoil']),dict(parent_instance='TrackingSaddle',parent_socket='service',child_instance='ServiceCartridge',child_socket='bottom',node_chain=[])]
    data=dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',catalog_id='point-defense-turret',catalog_grid=[1,1],axes=AXES,instances=a.instances,nodes=[dict(id=o.name,parent=o.parent.name if o.parent else None,translation=list(o.location),rotation_euler_xyz=list(o.rotation_euler),scale=list(o.scale)) for o in a.nodes],connections=connections,animations=dict(fps=24,frame_range=[1,120],channels=a.clips,demonstration_only=True,interpolation='Blender Bezier'),exports=[],notes='Catalog yaw arc 120 degrees. Single bullet bore and single muzzle. Elevation/recoil are visual demonstration. No GLB, collider/LOD, engine import or game validation.',reused_source_sha256={'MA-P06':hash_before})
    write(FOLDER/'assembly.json',data)
    bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
    render(FOLDER/'Previews/perspective.png')
    render(FOLDER/'Previews/top.png',view=(0,-.3,10),target=(0,-.3,0))
    render(FOLDER/'Previews/grayscale-top.png',view=(0,-.3,10),target=(0,-.3,0),gray=True)
    assert hashlib.sha256(reused.read_bytes()).hexdigest()==hash_before
    write(FOLDER/'README.md','# MA-W07 — пулемётная турель ближней обороны\n\nКомпактная одноствольная турель: короткий открытый охлаждающий кожух, асимметричный барабан подачи слева, малый оптический блок справа и трёхлучевая низкая опора.\n\nТри новые отдельные детали MA-W07-P01..P03 v1.0 и сервисный картридж MA-P06 v1.3 без изменений. Редактируемая сборка MA-W07.blend, состав/сокеты/локальные позы — assembly.json, план — composition-plan.md. Отдельные превью деталей находятся в Parts/<ID>/Previews; виды сборки — Previews/perspective.png, top.png, grayscale-top.png.\n\nКаталог: point-defense-turret, 1x1. Сектор поворота 120 градусов; прицеливание и короткая отдача показаны демонстрационной анимацией. BU условные, физический размер не согласован. Метаданные только для авторинга, игровые XML не менялись. GLB не создавался; коллайдеры, LOD, интеграция и игровая проверка не входят в результат.')
    print('MA-W07_BUILD_COMPLETE')
if __name__=='__main__':
    if '--render-only' in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(FOLDER/(BID+'.blend')))
        render(FOLDER/'Previews/perspective.png')
        render(FOLDER/'Previews/top.png',view=(0,-.3,10),target=(0,-.3,0))
        render(FOLDER/'Previews/grayscale-top.png',view=(0,-.3,10),target=(0,-.3,0),gray=True)
    else:main()
