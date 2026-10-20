"""Incremental Blender state authoring. Never exports or regenerates unchanged geometry."""
import argparse, copy, hashlib, json, math, shutil, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT, Part, write, AXES, reset

ARCHIVE = ROOT / 'Versions' / 'StateAnimation-before'
STATIC = {'MA-A01','MA-A02','MA-A03','MA-A04','MA-L01','MA-SP01','MA-SP02','MA-SP03','MA-SP04'}
VARIANTS = {'MA-F01-R2-P01':'MA-F01-R2-P01-AN1', 'MA-F01-R2-P02':'MA-F01-R2-P02-AN1',
            'MA-FG01-R2-P02':'MA-FG01-R2-P02-AN1', 'MA-FG01-R2-P03':'MA-FG01-R2-P03-AN1',
            'MA-D03-P01':'MA-D03-P01-AN1','MA-FF01-P04':'MA-FF01-P04-AN1'}
WING = 'MA-H-AN1-P01'

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prop(o, name, value=0., lo=0., hi=1., description=''):
    o[name] = float(value)
    o.id_properties_ui(name).update(min=lo,max=hi,soft_min=lo,soft_max=hi,description=description)

def drive(owner, path, expression, target, variables, index=None):
    fc = owner.driver_add(path) if index is None else owner.driver_add(path,index)
    d = fc.driver; d.type='SCRIPTED'; d.expression=expression
    for name, key in variables.items():
        v=d.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id=target;v.targets[0].data_path='["'+key+'"]'
    return fc

def mesh_gate():
    bpy.context.view_layer.update(); rows=[];deps=bpy.context.evaluated_depsgraph_get()
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(o.data)
        non=sum(not e.is_manifold for e in bm.edges);bad=sum(f.calc_area()<1e-10 for f in bm.faces)
        volume=bm.calc_volume(signed=True);bm.free()
        ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles()
        finite=all(math.isfinite(c) for v in me.vertices for c in v.co)
        zero=sum(t.area<1e-10 for t in me.loop_triangles);ev.to_mesh_clear()
        ok=not non and not bad and volume>0 and finite and not zero and all(s.material for s in o.material_slots)
        assert ok,(o.name,non,bad,volume,zero)
        rows.append(dict(mesh=o.name,source_manifold=True,positive_volume=True,evaluated_finite=True,no_zero_area_triangles=True))
    assert rows
    return dict(passed=True,validated_before_assembly=True,meshes=rows)

def group(coll,name,pivot,objects):
    n=bpy.data.objects.new(name,None);coll.objects.link(n);n.location=pivot;n.empty_display_size=.08
    bpy.context.view_layer.update()
    for o in objects:
        m=o.matrix_world.copy();o.parent=n;o.matrix_world=m
    return n

def add_marker(coll,name,loc,size,mat,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    coll.objects.link(o);o.data.materials.append(mat)
    if parent:
        m=o.matrix_world.copy();o.parent=parent;o.matrix_world=m
    return o

def render_views(folder, stem='state', views=('top','perspective'), resolution=340):
    # Disposable camera/light objects: no render helpers enter saved source collections.
    scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();pts=[]
    for o in scene.objects:
        if o.type=='MESH':pts.extend(o.matrix_world@Vector(v) for v in o.bound_box)
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    target=(lo+hi)*.5;scale=max(hi-lo)*1.45
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
    scene.render.resolution_x=resolution;scene.render.resolution_y=resolution;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    world=bpy.data.worlds.new('State review');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.035,.05,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
    added=[]
    for off,power in [((2,-4,7),1100),((-4,-2,4),900),((3,5,6),1400)]:
        bpy.ops.object.light_add(type='AREA',location=target+Vector(off));o=bpy.context.object;o.data.energy=power;o.data.size=5
        o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();added.append(o)
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam;added.append(cam)
    folder.mkdir(parents=True,exist_ok=True)
    for view in views:
        cam.location=target+Vector((0,0,12) if view=='top' else (7,-9,8))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(folder/(stem+'-'+view+'.png'));bpy.ops.render.render(write_still=True)
    for o in added:bpy.data.objects.remove(o,do_unlink=True)
    scene.camera=None

def save_variant(oldpid,newpid):
    src=ROOT/'Parts'/oldpid;out=ROOT/'Parts'/newpid
    bpy.ops.wm.open_mainfile(filepath=str(src/(oldpid+'.blend')))
    bpy.context.preferences.filepaths.save_version=0
    coll=bpy.data.collections[oldpid];coll.name=newpid
    meta=read(src/'part.json');motion=[]
    if oldpid=='MA-F01-R2-P01':
        n=group(coll,'WorkFeed',(0,0,0),[o for o in coll.objects if o.name.startswith('Inset intake separator')])
        # Leave travel clearance before the chamber bed; the old last separator was too close.
        for o in n.children:o.location.x-=.04
        motion=[dict(node=n.name,kind='feed',axis='X',amplitude_BU=.035)]
    elif oldpid=='MA-F01-R2-P02':
        n=group(coll,'WorkRotor',(0,0,.62),[o for o in coll.objects if o.name.startswith('Central process seal')])
        mat=bpy.data.materials.get('Steel')
        for j in range(3):
            angle=j*math.tau/3
            o=add_marker(coll,'Rotor index '+str(j),(.19*math.cos(angle),.19*math.sin(angle),.673),(.13,.035,.018),mat,n)
            o.rotation_euler.z=angle
        motion=[dict(node=n.name,kind='spin',axis='Z')]
    elif oldpid=='MA-FG01-R2-P02':
        # Only the inner drum and end couplings rotate. Collars, armour and dorsal cover stay fixed.
        n=group(coll,'WorkDrum',(0,0,.62),[o for o in coll.objects if o.name.startswith(('Main machine vessel','Axial coupling'))])
        mat=bpy.data.materials.get('Steel')
        # An inlaid longitudinal stripe is part of the rotating shell, inside collar clearance.
        for j in range(3):
            a=j*math.tau/3
            o=add_marker(coll,'Drum index '+str(j),(.591*math.sin(a),0,.62+.591*math.cos(a)),(.026,.48,.006),mat,n)
            o.rotation_euler.y=a
        motion=[dict(node=n.name,kind='spin',axis='Y')]
    elif oldpid=='MA-FG01-R2-P03':
        n=group(coll,'WorkPump',(0,0,.77),[o for o in coll.objects if o.name=='Star head'])
        motion=[dict(node=n.name,kind='spin',axis='Z')]
    elif oldpid=='MA-D03-P01':
        for o in coll.objects:
            if o.name=='Forward crosshead':o.location.y=-1.45
            elif o.name.startswith('Longitudinal lower drive bed'):
                o.location.y=.625;o.dimensions.y=4.05
                bpy.context.view_layer.objects.active=o;o.select_set(True)
                bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.select_set(False)
    else:
        for o in coll.objects:
            if o.name.startswith('Closed vertical transfer') and o.location.y < -1:
                o.location.z=.83;o.dimensions.z=.43
                bpy.context.view_layer.objects.active=o;o.select_set(True)
                bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.select_set(False)
    assert all(any(o.parent and o.parent.name==m['node'] for o in coll.objects) for m in motion)
    gate=mesh_gate();out.mkdir(parents=True,exist_ok=True)
    meta.update(id=newpid,version='3.0',source=newpid+'.blend',derived_from=dict(id=oldpid,version=meta['version'],sha256=sha(src/(oldpid+'.blend'))),motion_nodes=motion)
    meta['notes']=('Animation variant: moving internals separated; ' if motion else 'Clearance correction variant: static geometry; ')+'original source unchanged. BU authoring only. No GLB.'
    for material in meta['materials']:
        material['surfaces']=[o.name for o in coll.objects if o.type=='MESH' and any(s.material and s.material.name==material['id'] for s in o.material_slots)]
    pts=[o.matrix_world@Vector(v) for o in coll.objects if o.type=='MESH' for v in o.bound_box]
    meta['bounds_local']={'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
    # Standalone controls are remapped to the block controller when instanced.
    ctrl=bpy.data.objects.new('PartState',None);coll.objects.link(ctrl);prop(ctrl,'cycle_turns',0,0,100000)
    for m in motion:
        node=bpy.data.objects[m['node']];axis='XYZ'.index(m['axis'])
        drive(node,'rotation_euler' if m['kind']=='spin' else 'location', 't*6.283185307179586' if m['kind']=='spin' else '.035*sin(t*6.283185307179586)',ctrl,{'t':'cycle_turns'},axis)
    meta['animations']=[dict(controller='PartState',parameter='cycle_turns',units='turns; caller integrates work speed',motion_nodes=motion)] if motion else []
    for m in motion:
        m['pivot_local']=list(bpy.data.objects[m['node']].location)
    write(out/'part.json',meta);write(out/'geometry-validation.json',gate)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(newpid+'.blend')))
    render_views(out/'Previews',resolution=280)
    detail='Подвижный рабочий узел отделён от неподвижного корпуса. PartState.cycle_turns управляет фазой; pivots и оси в part.json.' if motion else 'Статичный вариант с исправленным зазором до движущихся рабочих элементов; собственная анимация не требуется.'
    write(out/'README.md',f'# {newpid} v3.0\n\nВариант {oldpid}. {detail} Геометрия проверена до сборки. Оригинал не изменён; процедурные PBR, BU условные, без GLB.\n')
    print('PART_READY',newpid,flush=True)

def make_wing():
    p=Part(WING,'Folding radiative wing with two sided thermal faces','3.0')
    p.mats['Thermal']=p.mats['Dark'].copy();p.mats['Thermal'].name='Thermal'
    p.panel('Radiative substrate',(.35,0,0),(.70,.22,.046),'Dark',.035,.003)
    for z in [-.026,.026]:p.panel('Thermal face',(.36,0,z),(.60,.17,.008),'Thermal',.025,.001)
    for y in [-.105,.105]:p.box('Protected edge rib',(.35,y,.008),(.69,.022,.07),'Titanium',.003)
    p.cyl('Hinge spindle',(0,0,0),.052,.25,'Steel',axis='Y',verts=16)
    gate=mesh_gate();p.save(mounts=[dict(id='root',role='hinge',position=[0,0,0],forward=[0,-1,0],up=[0,0,1],compatibility=['MilitaryArmor.radiator.hinge'],allowed_scale=[1,1,1])],notes='Articulated radiator wing. Local +X outward, hinge along local Y. Two sided thermal faces; static root socket. Original radiator blade untouched.')
    folder=ROOT/'Parts'/WING;meta=read(folder/'part.json')
    meta['motion_nodes']=[dict(node='part-root',kind='deployment',axis='Y',radians_closed=-math.pi/2,radians_open=0)]
    meta['thermal_surfaces']=[o.name for o in bpy.context.scene.objects if o.name.startswith('Thermal face')]
    meta['emission']=[dict(slot='Thermal',regions=meta['thermal_surfaces'],parameter='heat',default='cold',units='normalized authoring heat, not Kelvin',binding='per-instance material override in assembly')]
    meta['animations']=[dict(controller='assembly deployment',axis='Y',range_radians=[-math.pi/2,0],rest='open',pivot=[0,0,0])]
    write(folder/'part.json',meta);write(folder/'geometry-validation.json',gate)
    render_views(folder/'Previews',resolution=280)
    write(folder/'README.md','# '+WING+' v3.0\n\nШарнирная половина радиаторной секции. Две тепловые поверхности, узкие защитные рёбра и ось Y; открыта при 0°, закрыта при −90°. Крепление root в начале оси. Тепловая эмиссия назначается независимо на уровне экземпляра. Геометрия проверена до сборки, исходник редактируемый, BU условные, без GLB.\n')
    print('PART_READY',WING,flush=True)

def remove_instance(iid):
    o=bpy.data.objects.get(iid)
    assert o,iid
    for c in list(o.children_recursive):bpy.data.objects.remove(c,do_unlink=True)
    bpy.data.objects.remove(o,do_unlink=True)

def realize_instances(root):
    pending=list(root.children_recursive)
    while pending:
        instance=pending.pop()
        if instance.instance_type!='COLLECTION' or not instance.instance_collection:continue
        original=instance.instance_collection;copies={s:s.copy() for s in original.all_objects if s.type not in ('CAMERA','LIGHT')}
        for source,o in copies.items():
            bpy.context.scene.collection.objects.link(o);o.name=instance.name+'::'+source.name
            if source.parent in copies:
                o.parent=copies[source.parent];o.matrix_parent_inverse=source.matrix_parent_inverse.copy();o.matrix_basis=source.matrix_basis.copy()
            else:
                o.parent=instance;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Translation(-original.instance_offset)@source.matrix_world
            pending.append(o)
        instance.instance_type='NONE';instance.instance_collection=None

def append_part(iid,pid,parent,loc,rot=(0,0,0)):
    path=ROOT/'Parts'/pid/(pid+'.blend')
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.collections=[pid]
    coll=dst.collections[0];copies={}
    n=bpy.data.objects.new(iid,None);bpy.context.scene.collection.objects.link(n);n.parent=parent;n.location=loc;n.rotation_euler=rot
    n['part_id']=pid;n['part_version']='3.0'
    canonical=[m['node'] for m in read(ROOT/'Parts'/pid/'part.json').get('motion_nodes',[])]+['PartState']
    for source in coll.objects:
        stable=next((name for name in canonical if source.name==name or source.name.startswith(name+'.')),source.name)
        o=source.copy();o.name=iid+'::'+stable;bpy.context.scene.collection.objects.link(o);copies[source]=o
    for source,o in copies.items():
        o.parent=copies.get(source.parent,n);o.matrix_basis=source.matrix_basis.copy()
        if o.animation_data:
            for fc in o.animation_data.drivers:
                for v in fc.driver.variables:
                    for t in v.targets:
                        if t.id in copies:t.id=copies[t.id]
    bpy.data.collections.remove(coll)
    return n

def parameters(bid):
    d={'power':(1,0,1,'Electrical availability; independent from retained heat/fill'),'activity':(0,0,1,'Actual work/load; zero means idle'), 'fault':(0,0,1,'Externally supplied fault, not inferred')}
    if bid.startswith(('MA-H0','MA-HS','MA-E','MA-M','MA-R')) or bid.startswith('MA-W') or bid in {'MA-T01','MA-F01','MA-F02','MA-FF01','MA-FG01'}:d['heat']=(0,0,1,'Retained normalized heat; independent from power')
    if bid.startswith('MA-H0'):d['deployment']=(1,0,1,'0 closed, 1 open; reversible at any point')
    if bid.startswith(('MA-D','MA-F')) and not bid.startswith('MA-FT'):d['cycle_turns']=(0,0,100000,'Accumulated turns; preserve phase when stopping')
    if bid.startswith(('MA-I','MA-FT','MA-B')):d['fill']=(.5,0,1,'Stored amount/charge; independent from power')
    if bid=='MA-B01':d['flow']=(0,-1,1,'Negative discharge, positive charge')
    if bid=='MA-N01':d['transmit']=(0,0,1,'0 receive/ready, 1 transmit')
    if bid=='MA-E02':
        for j in range(3):d['thrust_'+str(j)]=(0,0,1,'Independent nozzle '+str(j)+' output')
    return d

def shader_override(o,root,kind='status',extra=None):
    # Object-linked slots avoid mutating shared source meshes or materials.
    records=[]
    for idx,slot in enumerate(o.material_slots):
        if not slot.material:continue
        mat=slot.material.copy();mat.name=root.name+'::'+o.name+'::'+kind;slot.link='OBJECT';slot.material=mat
        bs=mat.node_tree.nodes.get('Principled BSDF')
        if not bs:continue
        vars={'p':'power','a':'activity','f':'fault'}
        if kind=='heat':
            vars={'h':'heat'};strength='10*h*h';colors=['min(1,h*4)','max(0,min(1,(h-.32)*1.55))','max(0,(h-.78)*1.8)']
        elif kind=='fill':
            vars['q']='fill';strength='p*(.06+2.8*q)';colors=['.015','.3+.4*q','.65']
        elif kind=='thrust':
            key=extra or 'activity';vars['a']=key;strength='p*(.02+7*a)';colors=['.025','.35+.4*a','1']
        elif kind=='optic':
            strength='p*(.03+5*a)';colors=['.015','.5','1']
        elif kind=='flow':
            vars['q']='flow';strength='p*(.15+2.5*abs(q))';colors=['max(0,-q)*.6','.35+max(0,q)*.55','.7']
        elif kind=='radio':
            vars['t']='transmit';strength='p*(.25+2.8*a)';colors=['.02','.35+.5*t','1-.5*t']
        else:
            strength='p*(.25+2.5*a+2*f)';colors=['.015+.985*f','.55*(1-f)+.08*f','.78*(1-f)']
        strength_socket=bs.inputs['Emission Strength'];drive(strength_socket,'default_value',strength,root,vars)
        color=bs.inputs['Emission Color']
        for j,expr in enumerate(colors):drive(color,'default_value',expr,root,vars,j)
        records.append(dict(object=o.name,slot=idx,material=mat.name,kind=kind,expression=strength,variables=vars))
    return records

def stashed_action(root,name,keys):
    saved={k:root[k] for k in keys};root.animation_data_create();root.animation_data.action=None
    for key,points in keys.items():
        for frame,value in points:root[key]=float(value);root.keyframe_insert(data_path='["'+key+'"]',frame=frame,group='State controls')
    act=root.animation_data.action;act.name=root.name+'::'+name;act.use_fake_user=True
    # Linear phase curves prevent a jump in speed at loop boundaries.
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
    root.animation_data.action=None
    for k,v in saved.items():root[k]=v
    return dict(name=act.name,parameters=list(keys),frames=[min(x[0] for pts in keys.values() for x in pts),max(x[0] for pts in keys.values() for x in pts)],loop=name.endswith('loop'),authoring_only=True)

def build_block(bid):
    folder=ROOT/'Blocks'/bid;source=folder/(bid+'.blend');backup=ARCHIVE/'Blocks'/bid;backup.mkdir(parents=True,exist_ok=True)
    for name in [bid+'.blend','assembly.json','README.md','validation.json']:
        if (folder/name).exists() and not (backup/name).exists():shutil.copy2(folder/name,backup/name)
    # Always start from the snapshot so reruns do not accumulate overrides, objects, or actions.
    a=read(backup/'assembly.json');bpy.ops.wm.open_mainfile(filepath=str(backup/(bid+'.blend')))
    bpy.context.preferences.filepaths.save_version=0;scene=bpy.context.scene;scene.frame_set(1)
    root=bpy.data.objects.get(bid)
    if not root:root=bpy.data.objects.new(bid,None);scene.collection.objects.link(root)
    states={'schema':'MilitaryArmor.StateAuthoring/1','id':bid,'game_validated':False,'authoring_units':'BU; normalized controls; not game timings','controls':{},'motion':[],'materials':[],'clips':[],'events':[]}
    if bid in STATIC:
        # No changes to static source files: only the decision document is added.
        reason='Static armour/corridor: no functional mechanism or powered emission required.' if not bid.startswith('MA-SP') else 'Rigid solar field: no deployment/tracking mechanism requested; no emissive photovoltaic surface.'
        write(folder/'state-authoring.json',dict(**states,static_reason=reason));print('STATIC_RETAINED',bid,flush=True);return
    realize_instances(root)
    for key,(default,lo,hi,desc) in parameters(bid).items():
        prop(root,key,default,lo,hi,desc);states['controls'][key]=dict(default=default,min=lo,max=hi,description=desc)
    # Preserve former demonstration actions as unassigned legacy assets, drive each channel separately.
    oldanim=a.get('animations',{});oldchannels=oldanim.get('channels',[]) if isinstance(oldanim,dict) else []
    for idx,c in enumerate(oldchannels):
        names=[c['node']] if 'node' in c else c.get('nodes',[])
        axis='XYZ'.index(c['axis'].replace('+','').replace('-','').upper())
        for name in names:
            o=bpy.data.objects.get(name)
            assert o,(bid,name)
            if o.animation_data and o.animation_data.action:
                o.animation_data.action.use_fake_user=True;o.animation_data.action=None
            isrot=c.get('channel','rotation_euler' if 'recoil_BU' not in c else 'location')=='rotation_euler'
            path='rotation_euler' if isrot else 'location';base=getattr(o,path)[axis]
            if 'rotor' in name.lower():key='cycle_turns';expr=f'{base}+t*6.283185307179586';limits=(0,100000)
            elif not isrot:
                key='recoil_'+name.replace('.','_');amplitude=c.get('recoil_BU')
                if amplitude is None:
                    vals=[k[1] for k in c['keys']];amplitude=max(vals)-min(vals)
                expr=f'{base}+t*{amplitude}';limits=(0,1)
            else:
                key='aim_yaw' if axis==2 else 'aim_pitch';limits=(-360,360) if axis==2 else (-90,90)
                if 'keys' in c:
                    vals=[k[1] for k in c['keys']];limits=(min(vals),max(vals))
                elif 'degrees' in c:limits=tuple(c['degrees'])
                expr=f'{base}+t*0.017453292519943295'
            if key not in root:
                prop(root,key,0,*limits,'Independent motion; authoring range from existing demonstration')
                states['controls'][key]=dict(default=0,min=limits[0],max=limits[1])
            drive(o,path,expr,root,{'t':key},axis);states['motion'].append(dict(node=name,path=path,axis=axis,parameter=key,expression=expr))
    if bid.startswith('MA-H0'):
        fins=[i for i in a['instances'] if i['part_id']=='MA-H01-R2-P02'];retired={i['id'] for i in fins}
        original_connections={c.get('child_instance',c.get('child')):c for c in a.get('connections',[])}
        a['mount_adapters']=[]
        a['instances']=[i for i in a['instances'] if i['id'] not in retired]
        a['connections']=[c for c in a.get('connections',[]) if c.get('child_instance',c.get('child')) not in retired]
        for fin in fins:
            remove_instance(fin['id']);x,y,z=fin['translation']
            for side in [-1,1]:
                iid=fin['id']+('.L' if side<0 else '.R');loc=[x+side*.18,y,z+.32];rot=[0,0,math.pi if side<0 else 0]
                n=append_part(iid,WING,root,loc,rot)
                hinge=bpy.data.objects.new(iid+'::Deployment',None);scene.collection.objects.link(hinge);hinge.parent=n
                for child in list(n.children):
                    if child!=hinge:child.parent=hinge
                expr='-1.5707963267948966*(1-d)';drive(hinge,'rotation_euler',expr,root,{'d':'deployment'},1)
                states['motion'].append(dict(node=hinge.name,path='rotation_euler',axis=1,parameter='deployment',expression=expr))
                a['instances'].append(dict(id=iid,part_id=WING,version='3.0',source=f'../../Parts/{WING}/{WING}.blend',parent=bid,translation=loc,rotation_euler_xyz=rot,scale=[1,1,1]))
                oldcon=original_connections[fin['id']];parent_id=oldcon.get('parent_instance',oldcon.get('parent'));socket_id=oldcon['parent_socket'];adapter_id='hinge-'+iid
                parent_inst=next(i for i in a['instances'] if i['id']==parent_id)
                pm=read(ROOT/'Parts'/parent_inst['part_id']/'part.json');mount=next(m for m in pm['mounts'] if m['id']==socket_id)
                pos=[mount['position'][0]+side*.18,mount['position'][1],mount['position'][2]+.32]
                adapter=dict(id=adapter_id,parent_instance=parent_id,source_socket=socket_id,position=pos,rotation_euler_xyz=rot,forward=[0,1 if side<0 else -1,0],up=[0,0,1],compatibility=['MilitaryArmor.radiator.hinge'],reason='Explicit local hinge adapter above existing collector fin seat; collector geometry unchanged')
                a['mount_adapters'].append(adapter)
                marker=bpy.data.objects.new(parent_id+'::socket.'+adapter_id,None);scene.collection.objects.link(marker);marker.parent=bpy.data.objects[parent_id];marker.location=pos;marker.rotation_euler=rot;marker['socket_id']=adapter_id
                a['connections'].append(dict(parent_instance=parent_id,parent_socket=adapter_id,child_instance=iid,child_socket='root',adapter=True))
        states['hinge_design']='Two wings per former fin; Y hinges at x +/-0.18 and z +0.32 from former blade socket. Wings fold upward into separate vertical slots.'
    for i in a['instances']:
        pid=i['part_id']
        if pid not in VARIANTS:continue
        newpid=VARIANTS[pid];remove_instance(i['id'])
        parent=bpy.data.objects[i['parent']];n=append_part(i['id'],newpid,parent,i['translation'],i['rotation_euler_xyz'])
        i.update(part_id=newpid,version='3.0',source=f'../../Parts/{newpid}/{newpid}.blend')
        pm=read(ROOT/'Parts'/newpid/'part.json')
        for m in pm['motion_nodes']:
            o=bpy.data.objects[i['id']+'::'+m['node']];o.animation_data_clear()
            axis='XYZ'.index(m['axis']);path='rotation_euler' if m['kind']=='spin' else 'location'
            base=getattr(o,path)[axis];expr=f'{base}+t*6.283185307179586' if m['kind']=='spin' else f'{base}+.035*sin(t*6.283185307179586)'
            drive(o,path,expr,root,{'t':'cycle_turns'},axis)
            states['motion'].append(dict(node=o.name,path=path,axis=axis,parameter='cycle_turns',expression=expr))
    if bid.startswith('MA-D'):
        for i in a['instances']:
            if i['part_id']!='MA-D01-P03':continue
            n=bpy.data.objects[i['id']];expr='t*6.283185307179586';drive(n,'rotation_euler',expr,root,{'t':'cycle_turns'},1)
            states['motion'].append(dict(node=n.name,path='rotation_euler',axis=1,parameter='cycle_turns',expression=expr))
    # Per-object semantic material overrides, never change source part materials.
    for o in list(scene.objects):
        if o.type!='MESH':continue
        local=o.name.split('::')[-1];lower=local.lower();kind=None;extra=None
        mats=[s.material.name.split('.')[0] for s in o.material_slots if s.material]
        if bid.startswith('MA-H0') and lower.startswith('thermal face'):kind='heat'
        elif bid.startswith('MA-HS') and 'core' in lower:kind='heat'
        elif bid=='MA-R01' and o.name.startswith('Thermal') and any(x in lower for x in ['fin','panel','rib']):kind='heat'
        elif bid.startswith('MA-E') and any(t in lower for t in ['deep combustion chamber','lateral thermal recess','cooling notch']):kind='heat'
        elif bid.startswith('MA-M') and any(t in lower for t in ['dark thermal','thermal tile']):kind='heat'
        elif bid.startswith('MA-EI') and any(t in lower for t in ['emitter','electrode']) and 'optic' not in lower:kind='heat'
        elif bid.startswith('MA-FT') and lower.startswith('Inset longitudinal seam'.lower()):kind='fill'
        elif bid.startswith(('MA-B','MA-I')) and ('Signal' in mats or 'Optic' in mats):kind='flow' if bid=='MA-B01' and lower.endswith('.001') else 'fill'
        elif bid.startswith('MA-E') and ('Signal' in mats or 'Optic' in mats):
            kind='thrust' if any(t in lower for t in ['throat','aperture','plasma','discharge','annular','ion']) or 'Electrode' in o.name else 'status'
            if bid=='MA-E02' and o.name.startswith('Nozzle'):kind='thrust';extra='thrust_'+o.name[6]
        elif bid.startswith(('MA-M','MA-W')) and ('Optic' in mats):kind='optic'
        elif 'Signal' in mats or 'Optic' in mats:kind='radio' if bid=='MA-N01' else 'status'
        elif any(slot.material and slot.material.use_nodes and slot.material.node_tree.nodes.get('Principled BSDF') and slot.material.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value>0 for slot in o.material_slots):kind='status'
        if kind:states['materials']+=shader_override(o,root,kind,extra)
    if 'deployment' in root:
        states['clips'] += [stashed_action(root,'open',{'deployment':[(1,0),(31,1)]}),stashed_action(root,'close',{'deployment':[(1,1),(31,0)]})]
    if 'cycle_turns' in root:
        states['clips'] += [stashed_action(root,'work_loop',{'activity':[(1,1),(49,1)],'cycle_turns':[(1,0),(49,1)]}),stashed_action(root,'start',{'activity':[(1,0),(25,1)],'cycle_turns':[(1,0),(13,.0625),(25,.25)]}),stashed_action(root,'stop',{'activity':[(1,1),(25,0)],'cycle_turns':[(1,0),(13,.1875),(25,.25)]})]
    states['clips'] += [stashed_action(root,'activate',{'power':[(1,0),(25,1)],'activity':[(1,0),(25,1)]}),stashed_action(root,'deactivate',{'activity':[(1,1),(13,0)],'power':[(1,1),(25,0)]})]
    if 'heat' in root:states['clips'] += [stashed_action(root,'heat_up',{'heat':[(1,0),(49,1)]}),stashed_action(root,'cool_down',{'heat':[(1,1),(97,0)]})]
    if 'fill' in root:states['clips'].append(stashed_action(root,'fill',{'fill':[(1,0),(97,1)]}))
    recoil={key:[(1,0),(3,1),(13,0),(25,0)] for key in states['controls'] if key.startswith('recoil_')}
    if bid.startswith('MA-W') or bid=='MA-T01':
        keys={'activity':[(1,0),(2,1),(5,0),(25,0)]};keys.update(recoil)
        states['clips'].append(stashed_action(root,'fire',keys));states['events']=[dict(name='fire',frame=2,source='authoring cue; external projectile/beam effect')]
        if bid=='MA-W02':states['clips'].append(stashed_action(root,'beam_hold_loop',{'activity':[(1,1),(49,1)]}))
    presets={'off':{'power':0,'activity':0},'idle':{'power':1,'activity':0},'working':{'power':1,'activity':1}}
    if 'heat' in root:presets.update(hot_off={'power':0,'activity':0,'heat':1},cold={'heat':0},hot={'heat':1})
    if 'deployment' in root:presets.update(closed={'deployment':0},opened={'deployment':1})
    if 'fill' in root:presets.update(empty={'fill':0},full={'fill':1})
    states['presets']=presets
    states['phase_policy']='cycle_turns is integrated phase, not speed. Stop retains phase. NLA cycle repetition must use cyclic extrapolation/REPEAT_OFFSET for spin; never reset turns on start. Clips start from relative phase 0; apply current phase offset when sequencing.'
    states['controller']=root.name;states['legacy_animation_metadata']=oldanim
    root['state_authoring']='state-authoring.json; choose a stashed action in Action Editor or edit Custom Properties with action unassigned.'
    scene.frame_end=120;scene.frame_set(1);root.update_tag();bpy.context.view_layer.update()
    a['state_authoring']='state-authoring.json';a['version']=str(a['version'])+'+states1'
    a['animations']=dict(controller=bid,controls=states['controls'],channels=states['motion'],clips=states['clips'],independent_controls=True,demonstration_only=False,game_integration=False)
    write(folder/'assembly.json',a);write(folder/'state-authoring.json',states)
    text=bpy.data.texts.get('STATE_CONTROLS') or bpy.data.texts.new('STATE_CONTROLS');text.clear()
    text.write('Select '+bid+' > Object Custom Properties. Controls are independent; phase is accumulated turns.\nNo action is assigned by default. Named actions are retained in the Action Editor with fake users.\nSee state-authoring.json for presets, events and authoring-only ranges. No game integration.\n')
    helper=bpy.data.texts.get('state_controls.py') or bpy.data.texts.new('state_controls.py');helper.clear()
    helper.write(Path(__file__).with_name('state_controls.py').read_text('utf-8-sig'))
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    oldread=(backup/'README.md').read_text('utf-8-sig')
    # Keep historical geometry notes but make the superseding status unambiguous.
    write(folder/'README.md',oldread+'\n## Состояния — текущая редакция\n\nПрежние замечания о статике/отсутствии анимаций выше относятся к сохранённой версии до этой правки. Текущий Blender-исходник содержит независимые контролы, управляемые материалы и сохранённые Actions: state-authoring.json. Выбрать объект '+bid+' → Custom Properties; Actions доступны в Action Editor, по умолчанию не назначены. Нагрев/заполнение не сбрасываются отключением. Геометрия неизменённых деталей не пересоздавалась, старые исходники — Versions/StateAnimation-before. Старый validation.json — историческая проверка; новые результаты в state-validation.json. Игровой интеграции и новых GLB нет.\n')
    print('BLOCK_READY',bid,len(states['motion']),len(states['materials']),flush=True)

def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--parts',action='store_true');parser.add_argument('--blocks',nargs='*');ns=parser.parse_args(args)
    if ns.parts:
        make_wing()
        for old,new in VARIANTS.items():save_variant(old,new)
    if ns.blocks is not None:
        for bid in ns.blocks or sorted(p.name for p in (ROOT/'Blocks').iterdir() if p.is_dir()):build_block(bid)

if __name__=='__main__':main()
