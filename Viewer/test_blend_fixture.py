"""Small standalone object-animation fixture for the file picker; not a catalog asset."""
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[1]/'Projects/SS/MilitaryArmor/Exports/ViewerStates/Acceptance'
root.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.mesh.primitive_cube_add(size=1)
cube=bpy.context.object;cube.name='ViewerProbe'
mat=bpy.data.materials.new('Probe');mat.use_nodes=True
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.12,.35,.6,1)
cube.data.materials.append(mat)
cube.location.x=0;cube.keyframe_insert('location',frame=1)
cube.location.x=1.2;cube.keyframe_insert('location',frame=25)
bpy.context.scene.frame_end=25;bpy.context.scene.render.fps=24;bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'animated.blend'))
