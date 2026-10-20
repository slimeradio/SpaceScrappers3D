import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Tools'))
from weapon_batch_core import Assembly,write,reset
OUT=ROOT/'Scenes'/'DamageDemo'; OUT.mkdir(parents=True,exist_ok=True)
STATES=['damage0','damage33','damage66','destroyed']
BIDS=['MA-A01','MA-W01']
report={'parts':[],'blocks':[],'game_validated':False,'glb_generated':False}

def damage_material(src,state):
    m=src.copy();m.name=src.name+'_'+state;m['damage_state']=state
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    if not p:return m
    base=tuple(p.inputs['Base Color'].default_value)
    tex=n.new('ShaderNodeTexCoord')
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5;noise.inputs['Detail'].default_value=4
    l.new(tex.outputs['Generated'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position={'damage33':.52,'damage66':.34,'destroyed':.22}[state];ramp.color_ramp.elements[1].position=ramp.color_ramp.elements[0].position+.13
    ramp.color_ramp.elements[0].color=base;ramp.color_ramp.elements[1].color=(.008,.006,.004,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0])
    mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(95,7,45);l.new(tex.outputs['Generated'],mapping.inputs[0])
    scratches=n.new('ShaderNodeTexNoise');scratches.inputs['Scale'].default_value=2;l.new(mapping.outputs[0],scratches.inputs['Vector'])
    threshold=n.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value={'damage33':.76,'damage66':.68,'destroyed':.66}[state];l.new(scratches.outputs['Fac'],threshold.inputs[0])
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(.24,.25,.25,1);l.new(threshold.outputs[0],mix.inputs[0]);l.new(ramp.outputs[0],mix.inputs[1]);l.new(mix.outputs[0],p.inputs['Base Color'])
    p.inputs['Roughness'].default_value=.8
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.012;l.new(scratches.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    if state=='destroyed':p.inputs['Emission Strength'].default_value=0
    elif state=='damage66':p.inputs['Emission Strength'].default_value*=.2
    return m

# Independent variants, checked before assembly. Unchanged source parts are only read.
metadata={bid:json.loads((ROOT/'Blocks'/bid/'assembly.json').read_text(encoding='utf8')) for bid in BIDS}
pids=sorted({i['part_id'] for a in metadata.values() for i in a['instances']})
for pid in ([] if '--resume' in sys.argv else pids):
  for state in STATES[1:]:
    reset();src=ROOT/'Parts'/pid;data=json.loads((src/'part.json').read_text(encoding='utf8'));vid=pid+'-'+state
    with bpy.data.libraries.load(str(src/(pid+'.blend')),link=False) as (a,b):b.collections=[pid]
    coll=b.collections[0];bpy.context.scene.collection.children.link(coll);coll.name=vid
    cache={};meshes=[]
    for o in coll.all_objects:
      if o.type!='MESH':continue
      o.data=o.data.copy();meshes.append(o)
      for idx,mat in enumerate(o.data.materials):
        if mat:
          if mat not in cache:cache[mat]=damage_material(mat,state)
          o.data.materials[idx]=cache[mat]
    checks={'id':vid,'mesh_count':len(meshes),'finite':all(math.isfinite(c) for o in meshes for v in o.data.vertices for c in v.co),'degenerate_faces':sum(p.area<1e-12 for o in meshes for p in o.data.polygons),'material_slots_resolved':all(m is not None for o in meshes for m in o.data.materials)}
    assert checks['finite'] and checks['material_slots_resolved'] and meshes
    folder=ROOT/'Parts'/vid;folder.mkdir(exist_ok=True)
    data.update(id=vid,version='1.0',source=vid+'.blend',damage_state=state,derived_from=pid,notes='Damage demo variant. Procedural soot and exposed metal scratches; destroyed has emission off; destruction uses separate rigid-part animation. Original mounts retained. No file textures or game export.')
    data['materials']=[{'id':m.name,'ss_role':m.get('ss_role','Fixed'),'texture_source':'editable procedural generated-coordinate soot and anisotropic scratches'} for m in cache.values()]
    if state=='destroyed':data['emission']=[]
    write(folder/'part.json',data);write(folder/'validation.json',checks);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(vid+'.blend')));report['parts'].append(checks)

for bid in BIDS:
  if '--resume' in sys.argv and bid=='MA-A01':continue
  a=metadata[bid]
  write(OUT/(bid+'-composition.md'),'# '+bid+' damage demo\nReuse original part IDs for damage0; create explicit damage33/damage66/destroyed variants for each referenced part. Keep original rig transforms and sockets. Procedural soot/scratches; separate rigid-part destruction animation. Existing blocks unchanged.\n')
  for state in STATES:
    asm=Assembly(bid,a['catalog_id'],a['catalog_grid'],a['title']);ids={i['id'] for i in a['instances']}
    pending=[n for n in a['nodes'] if n['id']!=bid]
    inst={i['id']:i for i in a['instances']}
    while pending:
      progress=False
      for n in pending[:]:
        if n['parent'] is None or bpy.data.objects.get(n['parent']):
          if n['id'] in inst:
            i=inst[n['id']];pid=i['part_id'] if state=='damage0' else i['part_id']+'-'+state
            o=asm.instance(i['id'],pid,i['parent'],i['translation'],i['rotation_euler_xyz']);o.scale=i['scale']
          else:
            o=asm.node(n['id'],n['parent'],n['translation'],n['rotation_euler_xyz']);o.scale=n['scale']
          pending.remove(n);progress=True
      assert progress or not pending
    bpy.context.view_layer.update()
    folder=OUT/bid/state;folder.mkdir(parents=True,exist_ok=True)
    write(folder/'assembly.json',{'schema':a['schema'],'id':bid,'damage_state':state,'instances':asm.instances,'source_assembly':str((ROOT/'Blocks'/bid/'assembly.json').relative_to(ROOT)),'animations':'rest pose demo only; original rig retained','game_validated':False})
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(bid+'-'+state+'.blend')))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
    if state=='damage0':
      low=Vector([min(p[i] for p in pts) for i in range(3)]);high=Vector([max(p[i] for p in pts) for i in range(3)]);target=(low+high)/2;scale=(high-low).length*1.1
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    try:
      prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
      for d in prefs.devices:d.use=d.type=='OPTIX'
      scene.cycles.device='GPU'
    except Exception:pass
    scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.065,.08,.10,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    bpy.ops.object.camera_add(location=target+Vector((1,-1,1.414)).normalized()*scale*3);cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam
    for delta,power,size in [((2,-3,5),1300,4),((-3,-1,3),900,3),((1,4,4),1500,3)]:
      bpy.ops.object.light_add(type='AREA',location=target+Vector(delta)*max(scale/5,.3));o=bpy.context.object;o.data.energy=power*max(scale/5,.3)**2;o.data.size=size*max(scale/5,.3);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(folder/'preview.png');bpy.ops.render.render(write_still=True)
    report['blocks'].append({'id':bid,'state':state,'source':str(folder.relative_to(ROOT)),'mesh_count':len(meshes)})
write(OUT/'validation.json',report)
print('DAMAGE_DEMO_COMPLETE',flush=True)
