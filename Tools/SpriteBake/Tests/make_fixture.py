"""Generate a tiny authoring fixture with all four explicit material roles."""
import bpy
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import write_json

root = Path(sys.argv[sys.argv.index('--')+1])
style = root/'Projects/Test/Fixture'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
materials, surfaces = [], []
for i, role in enumerate(('Color1', 'Color2', 'Emissive', 'Fixed')):
    mat = bpy.data.materials.new(role)
    mat.use_nodes = True
    mat['ss_role'] = role
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (.2, .3, .4, 1)
    p.inputs['Metallic'].default_value = .25
    p.inputs['Roughness'].default_value = .6
    p.inputs['Emission Strength'].default_value = 2 if role == 'Emissive' else 0
    bpy.ops.mesh.primitive_cube_add(size=1, location=((i%2-.5)*.9, (i//2-.5)*.9, .2))
    obj = bpy.context.object
    obj.name = 'surface-' + role
    obj.scale = (.8, .8, .4)
    obj.data.materials.append(mat)
    materials.append({'id': role, 'surfaces': [obj.name]})
    surfaces.append(obj.name)
parts = style/'Parts'
parts.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(parts/'shared.blend'))
write_json(parts/'part.json', {'id': 'shared', 'materials': materials})
blocks = {}
for bid in ('A', 'B', 'C'):
    folder = style/'Blocks'/bid
    folder.mkdir(parents=True)
    source = '../..' + '/Parts/shared.blend'
    a = {'id': bid, 'catalog_id': bid, 'catalog_grid': [2, 2],
         'instances': [{'id': 'part', 'part_id': 'shared', 'source': source, 'parent': bid}]}
    write_json(folder/'assembly.json', a)
    # A valid assembly source is kept separate, even for this minimal fixture.
    import shutil
    shutil.copyfile(parts/'shared.blend', folder/(bid+'.blend'))
    blocks[bid] = {'assembly': 'Blocks/'+bid+'/assembly.json', 'source': 'Blocks/'+bid+'/'+bid+'.blend',
        'bu_per_cell': 1, 'footprint_bu': [-1, -1, 1, 1], 'height_range_bu': [0, 1],
        'layers': [{'id':'body','draw_order':0,'rotates':False,'pivot_bu':[0,0],'instances':['part']}],
        'states': {'damage0': {'frame':1}, **{s: {'alias':'damage0','reason':'test placeholder'}
                    for s in ('damage33','damage66','destroyed')}}}
write_json(style/'SpriteBake/profile.json', {'schema':'SpriteBake.Profile/1',
    'axes':{'up':'+Z','forward':'-Y'}, 'material_roles':{}, 'blocks':blocks,
    'samples':4, 'threads':4, 'padding_pixels':4, 'max_image_size':1024,
    'ao_samples':4, 'ao_distance_bu':.15, 'emission_max':4})
