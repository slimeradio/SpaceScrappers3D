import bpy, json, bmesh
from pathlib import Path
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1]
results=[]
for p in sorted((root/'Blocks').glob('*/*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(p))
    errors=[]; count=0
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or o.name.startswith(('Plane','Studio_floor')): continue
        count+=1
        bm=bmesh.new(); bm.from_mesh(o.data)
        if any(not e.is_manifold for e in bm.edges): errors.append(o.name+': open mesh')
        if any(f.calc_area()<1e-9 for f in bm.faces): errors.append(o.name+': degenerate')
        if bm.calc_volume(signed=True)<=0: errors.append(o.name+': inverted normals')
        if not o.data.materials: errors.append(o.name+': missing material')
        bm.free()
    if any(i.source=='FILE' and not i.packed_file for i in bpy.data.images): errors.append('Unpacked texture')
    # Surface crossings for free equipment and the opposing legs; intended panel
    # layering and mating bearings are not treated as clearance failures.
    groups={}
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and o.parent and o.parent.name.endswith('_mount'):
            groups.setdefault(o.parent.name,[]).append(o)
    def tree(o):
        return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],all_triangles=False)
    trees={}
    clearance=[]
    names=list(groups)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            selected=(a.startswith('Leg_') and b.startswith('Leg_')) or (a.startswith(('Sword_','Left_blade_','Radiation_claw_')) and b.startswith('Leg_')) or (b.startswith(('Sword_','Left_blade_','Radiation_claw_')) and a.startswith('Leg_'))
            if not selected: continue
            crossings=[]
            for x in groups[a]:
                if x not in trees: trees[x]=tree(x)
                for y in groups[b]:
                    if y not in trees: trees[y]=tree(y)
                    if trees[x].overlap(trees[y]): crossings.append([x.name,y.name])
            clearance.append({'a':a,'b':b,'surface_crossings':crossings})
            if crossings: errors.append(a+' / '+b+': surface crossings')
    results.append({'file':str(p.relative_to(root)),'reopened':True,'meshes':count,'clearance':clearance,'errors':errors})
    if errors:
        print(json.dumps(results,indent=2))
        raise RuntimeError(str(errors))
(root/'reopen-validation.json').write_bytes((json.dumps(results,indent=2)+'\n').replace('\n','\r\n').encode())
print('REOPEN_VALIDATION_OK')
