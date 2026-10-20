import bpy
from pathlib import Path
import sys
path = Path(sys.argv[sys.argv.index('--')+1])
bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
bpy.context.preferences.filepaths.save_version = 0
obj = bpy.data.objects.new('part', None)
bpy.context.scene.collection.objects.link(obj)
for frame, x in ((1,0), (10,.8)):
    obj.location.x = x
    obj.keyframe_insert('location', frame=frame)
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(path))
