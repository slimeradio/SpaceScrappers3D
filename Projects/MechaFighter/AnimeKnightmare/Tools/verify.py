import bpy, json, bmesh
from pathlib import Path
root=Path(__file__).resolve().parents[1]
results=[]
for p in sorted((root/'Blocks').glob('*/*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(p))
    errors=[]; count=0
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or o.name.startswith('Plane'): continue
        count+=1
        bm=bmesh.new(); bm.from_mesh(o.data)
        if any(not e.is_manifold for e in bm.edges): errors.append(o.name+': open mesh')
        if any(f.calc_area()<1e-9 for f in bm.faces): errors.append(o.name+': degenerate')
        if not o.data.materials: errors.append(o.name+': missing material')
        bm.free()
    if any(i.source=='FILE' and not i.packed_file for i in bpy.data.images): errors.append('Unpacked texture')
    results.append({'file':str(p.relative_to(root)),'reopened':True,'meshes':count,'errors':errors})
    if errors: raise RuntimeError(str(errors))
(root/'reopen-validation.json').write_bytes((json.dumps(results,indent=2)+'\n').replace('\n','\r\n').encode())
print('REOPEN_VALIDATION_OK')
