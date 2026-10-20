"""Fresh-process checks of saved state rigs, material independence and swept radiator geometry."""
import json, math, sys, hashlib
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_animation_states import ROOT, ARCHIVE, STATIC, VARIANTS, WING, read, write, mesh_gate, sha

def set_values(root,**values):
    for k,v in values.items():root[k]=float(v)
    root.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()

def bvh(o):
    deps=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles()
    vs=[o.matrix_world@v.co for v in m.vertices];polys=[tuple(t.vertices) for t in m.loop_triangles]
    result=BVHTree.FromPolygons(vs,polys,all_triangles=True,epsilon=1e-7);e.to_mesh_clear();return result

def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return tuple(min(v[i] for v in pts) for i in range(3)),tuple(max(v[i] for v in pts) for i in range(3))

def broad_overlap(a,b):
    return all(min(a[1][i],b[1][i])-max(a[0][i],b[0][i])>1e-5 for i in range(3))

def radiator_clearance(root):
    scene=bpy.context.scene;meshes=[o for o in scene.objects if o.type=='MESH']
    wings=[o for o in meshes if '::Deployment' in (o.parent.name if o.parent else '')]
    # Motion children are directly parented to Deployment; all other meshes are collector components.
    static=[o for o in meshes if o not in wings]
    groups={}
    for o in wings:groups.setdefault(o.parent,[]).append(o)
    rows=[]
    for step in range(21):
        d=step/20;set_values(root,deployment=d);boxes={o:bounds(o) for o in meshes};trees={};fail=[];pairs=0
        group_list=list(groups.values())+[ [o] for o in static ]
        group_boxes=[]
        for g in group_list:group_boxes.append((tuple(min(boxes[o][0][i] for o in g) for i in range(3)),tuple(max(boxes[o][1][i] for o in g) for i in range(3))))
        for j,g in enumerate(group_list[:len(groups)]):
            for k in range(j+1,len(group_list)):
                if not broad_overlap(group_boxes[j],group_boxes[k]):continue
                for o in g:
                    for other in group_list[k]:
                        if not broad_overlap(boxes[o],boxes[other]):continue
                        pairs+=1
                        if o not in trees:trees[o]=bvh(o)
                        if other not in trees:trees[other]=bvh(other)
                        if trees[o].overlap(trees[other]):fail.append([o.name,other.name])
        assert not fail,(root.name,d,fail[:8])
        rows.append(dict(deployment=d,near_pairs_tested=pairs,unintended_triangle_intersections=0))
    # Mid-transition reversal must reproduce the same geometry, without a hidden timeline dependency.
    node=wings[0];set_values(root,deployment=.35);a=node.matrix_world.copy()
    set_values(root,deployment=.8);set_values(root,deployment=.35)
    assert max(abs(a[i][j]-node.matrix_world[i][j]) for i in range(4) for j in range(4))<1e-6
    return rows

def material_strength(rec):
    return bpy.data.materials[rec['material']].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value

def verify_block(folder):
    bid=folder.name;a=read(folder/'assembly.json');s=read(folder/'state-authoring.json')
    bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')))
    if bid in STATIC:
        assert sha(folder/(bid+'.blend'))==sha(ARCHIVE/'Blocks'/bid/(bid+'.blend'))
        return dict(id=bid,passed=True,source_unchanged=True,decision=s['static_reason'])
    root=bpy.data.objects[s['controller']];assert root.animation_data is None or root.animation_data.action is None
    for k,d in s['controls'].items():assert abs(root[k]-d['default'])<1e-5,(bid,k,root[k],d['default'])
    for i in a['instances']:
        assert (folder/i['source']).resolve().exists(),i
        n=bpy.data.objects[i['id']];assert n['part_id']==i['part_id'],i
        assert n.get('part_version')==i['version'],i
        assert all(abs(v-1)<1e-6 for v in n.scale),i
    adapter_report=[]
    for m in a.get('mount_adapters',[]):
        marker=bpy.data.objects[m['parent_instance']+'::socket.'+m['id']]
        c=next(c for c in a['connections'] if c['parent_socket']==m['id'])
        child=bpy.data.objects[c['child_instance']]
        assert (marker.matrix_world.translation-child.matrix_world.translation).length<1e-5
        assert marker.matrix_world.to_quaternion().rotation_difference(child.matrix_world.to_quaternion()).angle<1e-5
        adapter_report.append(m['id'])
    clip_report=[]
    for c in s['clips']:
        action=bpy.data.actions.get(c['name']);assert action and action.use_fake_user,c
        assert action.slots,c
        root.animation_data_create();root.animation_data.action=action;root.animation_data.action_slot=action.slots[0]
        for frame in c['frames']:bpy.context.scene.frame_set(frame)
        # A normalized float channel must interpolate; integer ID properties silently quantize Blender curves.
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        ks=fc.keyframe_points
                        if len(ks)>1 and abs(ks[-1].co.y-ks[0].co.y)>.1:
                            frame=(ks[0].co.x+ks[-1].co.x)/2
                            if len(ks)==2:assert abs(fc.evaluate(frame)-(ks[0].co.y+ks[-1].co.y)/2)<1e-5,(bid,action.name,fc.data_path)
        clip_report.append(dict(name=action.name,reopened_and_evaluated=True))
        root.animation_data.action=None
    set_values(root,**{k:d['default'] for k,d in s['controls'].items()})
    motion_report=[]
    for m in s['motion']:
        node=bpy.data.objects[m['node']];key=m['parameter'];d=s['controls'][key]
        vals=[]
        # Unbounded spin is sampled as accumulated turns; pose controls use their authored range.
        sample=[0,.125,.25,.5,1] if key=='cycle_turns' else [d['min'],(d['min']+d['max'])/2,d['max']]
        for value in sample:
            set_values(root,**{key:value});v=getattr(node,m['path'])[m['axis']];assert math.isfinite(v);vals.append(v)
        assert max(vals)-min(vals)>1e-5,(bid,m,vals)
        fc=next(f for f in node.animation_data.drivers if f.data_path==m['path'] and f.array_index==m['axis']);assert fc.driver.is_valid,(bid,m)
        motion_report.append(dict(node=node.name,parameter=key,sampled_values=vals,driver_valid=True))
        set_values(root,**{key:d['default']})
    materials=[]
    heat_records=[r for r in s['materials'] if r['kind']=='heat']
    heat_samples={r['material']:[] for r in heat_records}
    if heat_records:
        for heat in [0,.25,.5,.75,1]:
            set_values(root,heat=heat,power=1)
            for rec in heat_records:heat_samples[rec['material']].append(material_strength(rec))
        set_values(root,power=0)
        for rec in heat_records:assert abs(material_strength(rec)-heat_samples[rec['material']][-1])<1e-5
    set_values(root,power=0)
    off_values={r['material']:material_strength(r) for r in s['materials'] if r['kind']!='heat'}
    extra={r['variables']['a']:1 for r in s['materials'] if r['kind']=='thrust'}
    set_values(root,**dict(dict(power=1,activity=1),**{k:v for k,v in extra.items() if k not in ['power','activity']}))
    on_values={r['material']:material_strength(r) for r in s['materials'] if r['kind']!='heat'}
    for rec in s['materials']:
        mat=bpy.data.materials[rec['material']];o=bpy.data.objects[rec['object']]
        assert o.material_slots[rec['slot']].link=='OBJECT'
        assert o.material_slots[rec['slot']].material==mat
        assert mat.animation_data is None # shader animation belongs to the node tree
        for fc in mat.node_tree.animation_data.drivers:
            assert fc.driver.is_valid,(bid,mat.name,fc.driver.expression)
            for v in fc.driver.variables:assert v.targets[0].id==root,(bid,mat.name,v.name)
        if rec['kind']=='heat':
            strengths=heat_samples[rec['material']]
            assert strengths[0]<1e-6 and all(y>x for x,y in zip(strengths,strengths[1:])),(bid,rec,strengths)
            materials.append(dict(object=o.name,kind='heat',monotonic_strengths=strengths,retained_with_power_off=True))
        else:
            off=off_values[rec['material']];on=on_values[rec['material']];assert off<1e-6 and on>off,(bid,rec,off,on)
            materials.append(dict(object=o.name,kind=rec['kind'],off=off,on=on))
    if 'fill' in root:
        set_values(root,fill=.7,power=0);assert abs(root['fill']-.7)<1e-6
    phase_retained=None
    if 'cycle_turns' in root:
        set_values(root,cycle_turns=2.375,activity=0,power=0);bpy.context.scene.frame_set(57)
        assert abs(root['cycle_turns']-2.375)<1e-6
        phase_retained=True
        from state_controls import play_clip,freeze
        play_clip(root,'stop');bpy.context.scene.frame_set(1);assert abs(root['cycle_turns']-2.375)<1e-6
        bpy.context.scene.frame_set(25);assert abs(root['cycle_turns']-2.625)<1e-6
        freeze(root);play_clip(root,'start');bpy.context.scene.frame_set(1);assert abs(root['cycle_turns']-2.625)<1e-6
        bpy.context.scene.frame_set(25);freeze(root);phase=root['cycle_turns'];play_clip(root,'work_loop')
        bpy.context.scene.frame_set(49);a_phase=root['cycle_turns'];bpy.context.scene.frame_set(50);assert root['cycle_turns']>a_phase
        assert abs(a_phase-phase-1)<1e-5
        freeze(root)
    swept=radiator_clearance(root) if 'deployment' in root else []
    set_values(root,**{k:d['default'] for k,d in s['controls'].items()})
    report=dict(id=bid,passed=True,independent_process_reopen=True,instances_resolved=len(a['instances']),mount_adapters_aligned=adapter_report,clips=clip_report,motion=motion_report,materials=materials,stopped_phase_retained=phase_retained,radiator_sweep=swept,game_validated=False,limitations='Existing static joints and internal bearing contacts intentional. Radiator sweep tests unrelated wing and collector triangle surfaces at 21 poses; no engine collision or physical thermal simulation.')
    write(folder/'state-validation.json',report);print('VERIFIED_STATE',bid,flush=True);return report

def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    blocks=args or sorted(p.name for p in (ROOT/'Blocks').iterdir() if p.is_dir())
    reports=[]
    if True:
        requested_parts=([WING]+list(VARIANTS.values())) if not args else sorted({i['part_id'] for bid in blocks for i in read(ROOT/'Blocks'/bid/'assembly.json')['instances']} & ({WING}|set(VARIANTS.values())))
        for pid in requested_parts:
            folder=ROOT/'Parts'/pid;meta=read(folder/'part.json')
            bpy.ops.wm.open_mainfile(filepath=str(folder/(pid+'.blend')));mesh_gate()
            if 'derived_from' in meta:
                old=meta['derived_from'];assert sha(ROOT/'Parts'/old['id']/(old['id']+'.blend'))==old['sha256']
    for bid in blocks:reports.append(verify_block(ROOT/'Blocks'/bid))
    if args and (ROOT/'animation-state-validation.json').exists():
        reports=[r for r in read(ROOT/'animation-state-validation.json')['blocks'] if r['id'] not in blocks]+reports
    write(ROOT/'animation-state-validation.json',dict(passed=True,blocks=reports,count=len(reports),fresh_blender_process=True))

if __name__=='__main__':main()
