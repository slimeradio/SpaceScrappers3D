"""Swept clearance of exposed work elements, excluding documented internal bearings and material seating."""
import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_animation_states import ROOT,read,write
from verify_animation_states import set_values,bounds,broad_overlap,bvh
reports=[]
for bid in ['MA-D01','MA-D02','MA-D03','MA-F01','MA-F02','MA-FF01','MA-FG01']:
    folder=ROOT/'Blocks'/bid;bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')));root=bpy.data.objects[bid]
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];moving={}
    if bid.startswith('MA-D'):
        for o in meshes:
            if any(t in o.name for t in ['Helical cutting flight','Replaceable carbide tooth','Blunt central breaker']):moving[o]=o.parent
    else:
        for o in meshes:
            if o.parent and any(t in o.parent.name for t in ['::WorkRotor','::WorkPump','::WorkFeed']):moving[o]=o.parent
    # Drum is a concentric inner shell under original solid collars; that intentional bearing seating
    # is checked by radial envelope below, not reported as an external collision.
    for o in meshes:
        if o.parent and '::WorkDrum' in o.parent.name:
            if 'Main machine vessel' in o.name:
                pivot=o.parent.matrix_world.translation
                verts=[o.matrix_world@v.co for v in o.data.vertices]
                radial=max(((v.x-pivot.x)**2+(v.z-pivot.z)**2)**.5 for v in verts)
                assert radial<.60,(bid,radial)
    rows=[]
    for j in range(24):
        phase=j/24;set_values(root,cycle_turns=phase);boxes={o:bounds(o) for o in meshes};trees={};fail=[];tested=set()
        for o,g in moving.items():
            for other in meshes:
                if other==o or other.parent==g:continue
                # Existing nested solids describe guide/rotor bearing seats rather than boolean-cut recesses.
                seated=(('Inset intake separator' in o.name and 'Wide intake zone' in other.name)
                        or ('Central process seal' in o.name and any(t in other.name for t in ['Pressure vessel','Inset working cover']))
                        or ('Star head' in o.name and 'Pump neck' in other.name))
                if seated:continue
                # Cutter core, rear locking ring and torque coupling rotate with the same cutter;
                # their designed assembly contacts remain inside that instance and are excluded.
                key=tuple(sorted((o.name,other.name)))
                if key in tested or not broad_overlap(boxes[o],boxes[other]):continue
                tested.add(key)
                if o not in trees:trees[o]=bvh(o)
                if other not in trees:trees[other]=bvh(other)
                if trees[o].overlap(trees[other]):fail.append([o.name,other.name])
        assert not fail,(bid,phase,fail[:10])
        rows.append(dict(turns=phase,near_pairs_tested=len(tested),unintended_surface_intersections=0))
    report=dict(id=bid,passed=True,poses=rows,moving_exterior_mesh_count=len(moving),drum_radius_below_BUs=.60,limitations='Triangle surface intersections at 24 phases; original internal bearing/rotor seating intentionally retained. Not engine collider validation.')
    write(folder/'work-clearance-validation.json',report);reports.append(report);print('WORK_CLEARANCE',bid,flush=True)
write(ROOT/'work-clearance-validation.json',dict(passed=True,blocks=reports))
