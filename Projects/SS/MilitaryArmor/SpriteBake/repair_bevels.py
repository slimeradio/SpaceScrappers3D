"""Part-level repair of collapsed bevel output. Only explicitly supplied parts.

Editable source geometry stays intact; a Weld modifier removes coincident
bevel vertices before normal calculation. A backup precedes any source save.
"""
import sys
from pathlib import Path
import bpy
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[2]/'Tools/SpriteBake'))
from common import digest, read_json, write_json
import shutil


def bad(obj):
    e = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = e.to_mesh()
    try:
        m.calc_loop_triangles()
        return sum(t.area <= 1e-12 for t in m.loop_triangles)
    finally:
        e.to_mesh_clear()


report_path = ROOT/'SpriteBake/bevel-repairs.json'
results = read_json(report_path) if report_path.exists() else []
for pid in sys.argv[sys.argv.index('--')+1:]:
    if not pid.startswith('MA-') or '/' in pid or '\\' in pid:
        raise ValueError(pid)
    path = ROOT/'Parts'/pid/(pid+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
    meta = read_json(path.parent/'part.json')
    names = {s for m in meta['materials'] for s in m['surfaces']}
    repaired = []
    for obj in list(bpy.context.scene.objects):
        if obj.name not in names or obj.type != 'MESH' or not bad(obj):
            continue
        before = bad(obj)
        if not any(m.type == 'BEVEL' for m in obj.modifiers):
            raise ValueError('Non-bevel source defect: '+obj.name)
        mod = obj.modifiers.new('SpriteBake: merge collapsed bevel corners', 'WELD')
        mod.merge_threshold = 1e-6
        index = list(obj.modifiers).index(mod)
        normal_indices = [i for i, m in enumerate(obj.modifiers) if m.type == 'WEIGHTED_NORMAL']
        if normal_indices:
            obj.modifiers.move(index, normal_indices[0])
        bpy.context.view_layer.update()
        after = bad(obj)
        if after:
            raise ValueError('Weld did not repair: '+obj.name+': '+str(after))
        repaired.append({'object': obj.name, 'degenerate_before': before, 'degenerate_after': after})
    if repaired:
        key = digest(path)
        backup = ROOT/'Exports/Sprites/SourceBackups'/key/path.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(path, backup)
        temp = path.with_name(path.stem+'.repair.tmp.blend')
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(temp))
        import os
        os.replace(temp, path)
        results.append({'part': pid, 'backup': str(backup), 'objects': repaired})
        print('REPAIRED', pid, len(repaired), flush=True)
write_json(report_path, results)
