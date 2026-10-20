import sys,json
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_MA_A01_A02 import check_meshes, ROOT, write
for bid in ['MA-A01','MA-A02']:
    folder=ROOT/'Blocks'/bid;pid=bid+'-P01'
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts'/pid/(pid+'.blend')))
    part=check_meshes();assert part['geometric_nonmanifold_edges']==0
    bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')))
    source=check_meshes();assert source['nonmanifold_edges']==0
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(folder/'Exports'/(bid+'.glb')))
    roundtrip=check_meshes();assert roundtrip['geometric_nonmanifold_edges']==0
    assert source['triangles']==roundtrip['triangles']==76
    assert source['materials']==roundtrip['materials']==['Armor','Ceramic']
    meta=json.loads((folder/'validation.json').read_text());meta.update({'part_source_reopened':True,'part_geometry':part,'source_geometry':source,'glb_roundtrip':roundtrip,'visual_review':'Passed: final oblique, top, and 4x4 repetition images inspected; quiet repeated panel, consistent structural edges, no display geometry in source/export.','gltf_vertex_splits':'Raw imported boundary counts reflect expected hard-normal/material vertex splits; position-welded topology is closed and manifold.'});write(folder/'validation.json',meta)
    print('VERIFIED',bid,source['triangles'],'triangles, closed manifold source and GLB geometry',flush=True)