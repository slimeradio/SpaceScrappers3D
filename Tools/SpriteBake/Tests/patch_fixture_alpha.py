import bpy
from pathlib import Path
import sys
path = Path(sys.argv[sys.argv.index('--')+1])
bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
bpy.context.preferences.filepaths.save_version = 0
for material in bpy.data.materials:
    if material.get('ss_role') == 'Fixed':
        material.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value = .5
bpy.ops.wm.save_as_mainfile(filepath=str(path))
