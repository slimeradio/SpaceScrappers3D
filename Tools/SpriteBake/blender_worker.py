"""Blender-side validation and orthographic AOV capture. Never runs model scripts."""
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from common import ROLES, block_inputs, confined, digest, read_json, write_json
from png import write_png

RENDERABLE = {'MESH', 'CURVE', 'FONT', 'SURFACE'}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0


def load_objects(path, names=None):
    metadata = read_json(Path(path).parent / 'part.json')
    surfaces = {name for m in metadata['materials'] for name in m['surfaces']}
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        target.objects = list(source.objects)
        source_names = list(source.objects)
    objects = [obj for name, obj in zip(source_names, target.objects)
               if obj.type == 'EMPTY' or (obj.type in RENDERABLE and name in surfaces)]
    if names is not None:
        names.update({name: obj for name, obj in zip(source_names, target.objects) if obj in objects})
    for obj in objects:
        bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    return objects


def assign_roles(objects, mapping):
    roles = {}
    for obj in objects:
        if obj.type not in RENDERABLE:
            continue
        if not obj.data.materials:
            raise ValueError('No material: ' + obj.name)
        for mat in obj.data.materials:
            if mat is None:
                raise ValueError('Empty material slot: ' + obj.name)
            role = mat.get('ss_role')
            if role is None:
                name = re.sub(r'\.\d{3}$', '', mat.name)
                role = mapping.get(mat.name, mapping.get(name))
                if role is None:
                    raise ValueError('No explicit role mapping: ' + mat.name)
                mat['ss_role'] = role
            if role not in ROLES:
                raise ValueError('Invalid ss_role: ' + mat.name + ': ' + str(role))
            if not mat.use_nodes or len([n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']) != 1:
                raise ValueError('Expected one Principled BSDF: ' + mat.name)
            roles[mat.name] = role
    return roles


def external_assets(root, source):
    """Record unpacked texture/library dependencies in the same selected style."""
    files = set()
    for library in bpy.data.libraries:
        path = Path(bpy.path.abspath(library.filepath)).resolve()
        if path != source:
            files.add(confined(root, path))
    for image in bpy.data.images:
        if image.source == 'FILE' and not image.packed_file and image.filepath:
            path = Path(bpy.path.abspath(image.filepath, library=image.library)).resolve()
            if not path.is_absolute():
                path = source.parent / path
            files.add(confined(root, path))
        elif image.source not in ('FILE', 'GENERATED', 'VIEWER'):
            raise ValueError('Only static/packed image textures are supported: ' + image.name)
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(files)}


def geometry(objects):
    stats = {'objects': 0, 'triangles': 0, 'degenerate_triangles': 0,
             'nonmanifold_edges': 0, 'bounds_bu': None}
    coords = []
    dg = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type not in RENDERABLE:
            continue
        if not all(math.isfinite(v) for row in obj.matrix_world for v in row):
            raise ValueError('Non-finite transform: ' + obj.name)
        evaluated = obj.evaluated_get(dg)
        mesh = evaluated.to_mesh()
        try:
            if not mesh or not len(mesh.vertices) or not len(mesh.polygons):
                raise ValueError('Empty geometry: ' + obj.name)
            mesh.calc_loop_triangles()
            count = sum(t.area <= 1e-12 for t in mesh.loop_triangles)
            if count:
                raise ValueError('Degenerate triangles: ' + obj.name + ': ' + str(count))
            stats['triangles'] += len(mesh.loop_triangles)
            stats['objects'] += 1
            for face in mesh.polygons:
                if face.material_index >= len(mesh.materials):
                    raise ValueError('Unassigned face material: ' + obj.name)
            for vertex in mesh.vertices:
                point = obj.matrix_world @ vertex.co
                if not all(math.isfinite(v) for v in point):
                    raise ValueError('Non-finite vertex: ' + obj.name)
                coords.append(list(point))
            bm = bmesh.new()
            try:
                bm.from_mesh(mesh)
                stats['nonmanifold_edges'] += sum(not e.is_manifold for e in bm.edges)
            finally:
                bm.free()
        finally:
            evaluated.to_mesh_clear()
    if not coords:
        raise ValueError('No renderable geometry')
    points = np.array(coords)
    stats['bounds_bu'] = [points.min(axis=0).tolist(), points.max(axis=0).tolist()]
    # Open shells and recesses are valid authoring geometry; report rather than close them.
    return stats


def validate(request):
    root = Path(request['root'])
    mapping = request['profile']['material_roles']
    paths = set()
    for record in request['records']:
        _, assembly, _ = block_inputs(root, record['id'], request['profile']['blocks'][record['id']])
        base = Path(record['assembly']).parent
        paths.update(confined(root, base / x['source']) for x in assembly['instances'])
    results = []
    for path in sorted(paths):
        metadata_path = path.parent / 'part.json'
        metadata = read_json(metadata_path)
        key = digest(path)
        cache_dir = root / 'Exports/Sprites/ValidationCache'
        # Includes actual tool contents, settings and Blender version, not just a version label.
        import hashlib
        cache_key = hashlib.sha256((key + digest(metadata_path) + json.dumps(mapping, sort_keys=True) +
            bpy.app.version_string + digest(Path(__file__))).encode()).hexdigest()
        cache_file = cache_dir / (cache_key + '.json')
        if cache_file.is_file() and not request['write_roles']:
            previous = read_json(cache_file)
            if all(confined(root, name).is_file() and digest(confined(root, name)) == sha
                   for name, sha in previous.get('external_assets', {}).items()):
                results.append(previous)
                continue
        reset()
        # Open the source only for the explicit, backed-up material tagging operation.
        if request['write_roles']:
            bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
            surfaces = {name for m in metadata['materials'] for name in m['surfaces']}
            objects = [o for o in bpy.context.scene.objects if o.name in surfaces]
        else:
            objects = load_objects(path)
        before_roles = {m.name: m.get('ss_role') for o in objects if o.type in RENDERABLE for m in o.data.materials if m}
        roles = assign_roles(objects, mapping)
        stats = geometry(objects)
        result = {'source': path.relative_to(root).as_posix(), 'id': metadata['id'],
                  'sha256': key, 'geometry': stats, 'roles': roles,
                  'external_assets': external_assets(root, path),
                  'roles_stored_in_source': all(before_roles.get(name) == role for name, role in roles.items())}
        if request['write_roles'] and not result['roles_stored_in_source']:
            # Byte-exact backup before saving only role properties; no geometry operators.
            backup = root / 'Exports/Sprites/SourceBackups' / key / path.name
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copy2(path, backup)
            temp = path.with_name(path.stem + '.sprite-roles.tmp.blend')
            bpy.ops.wm.save_as_mainfile(filepath=str(temp), check_existing=False)
            os.replace(temp, path)
            result.update(sha256=digest(path), roles_stored_in_source=True,
                          backup=backup.relative_to(root).as_posix(), original_sha256=key)
        write_json(cache_file, result)
        results.append(result)
        print('PART_OK', metadata['id'], stats['triangles'], flush=True)
    return {'parts': results, 'write_roles': request['write_roles']}


def pose_matrix(record):
    from mathutils import Euler
    loc = Vector(record.get('translation', [0, 0, 0]))
    rot = Euler(record.get('rotation_euler_xyz', [0, 0, 0]), 'XYZ').to_quaternion()
    scale = Vector(record.get('scale', [1, 1, 1]))
    return Matrix.LocRotScale(loc, rot, scale)


def assemble(root, spec, assembly, assembly_path, part_nodes=None):
    reset()
    scene = bpy.context.scene
    definitions = {x['id']: x for x in assembly.get('nodes', [])}
    definitions.setdefault(assembly['id'], {'id': assembly['id'], 'parent': None})
    for item in assembly['instances']:
        definitions.setdefault(item['id'], item)
    nodes = {name: bpy.data.objects.new(name, None) for name in definitions}
    for name, obj in nodes.items():
        scene.collection.objects.link(obj)
        parent = definitions[name].get('parent')
        if parent and parent not in nodes:
            raise ValueError('Missing parent node: ' + parent)
        obj.parent = nodes.get(parent)
        obj.matrix_basis = pose_matrix(definitions[name])
        seen = {name}
        while parent:
            if parent in seen:
                raise ValueError('Cyclic assembly hierarchy')
            seen.add(parent)
            parent = definitions[parent].get('parent')
    # Optional author action evaluation, only when explicitly requested by the profile.
    if spec.get('use_author_animation', False):
        with bpy.data.libraries.load(str(confined(root, spec['source'])), link=False) as (src, dst):
            dst.objects = [name for name in src.objects if name in nodes]
            original_names = list(dst.objects)
        for name, source in zip(original_names, dst.objects):
            if source.animation_data and source.animation_data.action:
                target = nodes[name]
                target.animation_data_create()
                target.animation_data.action = source.animation_data.action
                if source.animation_data.action_slot:
                    target.animation_data.action_slot = source.animation_data.action_slot
    instances = {}
    for item in assembly['instances']:
        path = confined(root, assembly_path.parent / item['source'])
        names = {}
        loaded = load_objects(path, names)
        if part_nodes is not None:
            part_nodes[item['id']] = names
        loaded_set = set(loaded)
        objects = []
        for obj in loaded:
            # Preserve local hierarchy from the part. New scene parent replaces only source roots.
            if obj.parent not in loaded_set:
                basis = obj.matrix_world.copy()
                obj.parent = nodes[item['id']]
                obj.matrix_parent_inverse = Matrix.Identity(4)
                obj.matrix_basis = basis
            if obj.type in RENDERABLE:
                obj.hide_render = False
                objects.append(obj)
        instances[item['id']] = objects
    bpy.context.view_layer.update()
    return nodes, instances


def socket_value(tree, socket):
    if socket.is_linked:
        return socket.links[0].from_socket
    if socket.type == 'VALUE':
        n = tree.nodes.new('ShaderNodeValue')
        n.outputs[0].default_value = socket.default_value
    else:
        n = tree.nodes.new('ShaderNodeRGB')
        n.outputs[0].default_value = socket.default_value
    return n.outputs[0]


def scalar(tree, op, a, b):
    n = tree.nodes.new('ShaderNodeMath')
    n.operation = op
    for i, v in enumerate((a, b)):
        if hasattr(v, 'node'):
            tree.links.new(v, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n.outputs[0]


def rgb(tree, values):
    node = tree.nodes.new('ShaderNodeCombineXYZ')
    for i, v in enumerate(values):
        if hasattr(v, 'node'):
            tree.links.new(v, node.inputs[i])
        else:
            node.inputs[i].default_value = v
    return node.outputs[0]


def shader_maps(mat, profile, z0, z1):
    tree = mat.node_tree
    p = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    role = mat['ss_role']
    geom = tree.nodes.new('ShaderNodeNewGeometry')
    # Retain the author bump chain. Unlinked normal inputs fall back to shading normal.
    normal = p.inputs['Normal'].links[0].from_socket if p.inputs['Normal'].is_linked else geom.outputs['Normal']
    split = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(normal, split.inputs[0])
    # Camera right is +X; camera up is -Y. RGB decodes to (+X,-Y,+Z).
    nmap = rgb(tree, (
        scalar(tree, 'ADD', scalar(tree, 'MULTIPLY', split.outputs['X'], .5), .5),
        scalar(tree, 'ADD', scalar(tree, 'MULTIPLY', split.outputs['Y'], -.5), .5),
        scalar(tree, 'ADD', scalar(tree, 'MULTIPLY', split.outputs['Z'], .5), .5)))
    pos = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(geom.outputs['Position'], pos.inputs[0])
    height = scalar(tree, 'DIVIDE', scalar(tree, 'SUBTRACT', pos.outputs['Z'], z0), z1-z0)
    ao = tree.nodes.new('ShaderNodeAmbientOcclusion')
    ao.samples = profile.get('ao_samples', 8)
    ao.inputs['Distance'].default_value = profile['ao_distance_bu']
    metal = socket_value(tree, p.inputs['Metallic'])
    rough = socket_value(tree, p.inputs['Roughness'])
    values = {
        'material-mask': rgb(tree, [float(role == x) for x in ROLES[:3]]),
        'normal': nmap,
        'height': rgb(tree, [height] * 3),
        'surface': rgb(tree, [metal, rough, ao.outputs['AO']]),
        'emission': rgb(tree, [scalar(tree, 'DIVIDE', socket_value(tree, p.inputs['Emission Strength']),
                                     profile['emission_max']) if role == 'Emissive' else 0] * 3),
    }
    for name, value in values.items():
        output = tree.nodes.new('ShaderNodeOutputAOV')
        output.aov_name = name
        tree.links.new(value, output.inputs['Color'])
    output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    emission = tree.nodes.new('ShaderNodeEmission')
    if role == 'Fixed':
        tree.links.new(socket_value(tree, p.inputs['Base Color']), emission.inputs['Color'])
    else:
        emission.inputs['Color'].default_value = (1, 1, 1, 1)
    # No sunlight, studio lights, emission bloom or view transform in the exported albedo.
    alpha = p.inputs['Alpha']
    if alpha.is_linked or alpha.default_value < 1:
        transparent = tree.nodes.new('ShaderNodeBsdfTransparent')
        mix = tree.nodes.new('ShaderNodeMixShader')
        tree.links.new(socket_value(tree, alpha), mix.inputs[0])
        tree.links.new(transparent.outputs[0], mix.inputs[1])
        tree.links.new(emission.outputs[0], mix.inputs[2])
        tree.links.new(mix.outputs[0], output.inputs['Surface'])
    else:
        tree.links.new(emission.outputs[0], output.inputs['Surface'])


def configure_capture(profile, bounds, size, output):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    device = profile.get('device', 'CPU')
    if device not in ('CPU', 'OPTIX', 'CUDA'):
        raise ValueError('Unsupported render device: ' + device)
    if device != 'CPU':
        preferences = bpy.context.preferences.addons['cycles'].preferences
        preferences.compute_device_type = device
        preferences.get_devices()
        devices = [d for d in preferences.devices if d.type == device]
        if not devices:
            raise RuntimeError('Configured render device is unavailable: ' + device)
        for item in preferences.devices:
            item.use = item in devices
        scene.cycles.device = 'GPU'
    else:
        scene.cycles.device = 'CPU'
    scene.cycles.samples = profile['samples']
    scene.cycles.use_denoising = False
    scene.cycles.use_adaptive_sampling = False
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = profile.get('threads', 8)
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.world = None
    x0, y0, x1, y1 = bounds
    camera = bpy.data.objects.new('SpriteBake.Camera', bpy.data.cameras.new('SpriteBake.Camera'))
    scene.collection.objects.link(camera)
    camera.location = ((x0+x1)/2, (y0+y1)/2, 1000)
    # At zero rotation camera right is +X, up +Y.
    # Look -Z with screen right +X and screen up -Y requires a reflection, not a rotation.
    # Capture right +X/up +Y then vertically flip in PNG encoding for -Y forward at top.
    camera.rotation_euler = (0, 0, 0)
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = max(x1-x0, y1-y0)
    camera.data.clip_end = 2000
    scene.camera = camera
    layer = bpy.context.view_layer
    for name in ('material-mask', 'normal', 'height', 'surface', 'emission'):
        aov = layer.aovs.add()
        aov.name, aov.type = name, 'COLOR'
    group = bpy.data.node_groups.new('SpriteBake.Capture', 'CompositorNodeTree')
    if hasattr(scene, 'compositing_node_group'):
        scene.compositing_node_group = group
    else:
        scene.use_nodes = True
        group = scene.node_tree
        group.nodes.clear()
    source = group.nodes.new('CompositorNodeRLayers')
    source.layer = layer.name
    for name in ('albedo', 'material-mask', 'normal', 'height', 'surface', 'emission'):
        node = group.nodes.new('CompositorNodeOutputFile')
        if hasattr(node.format, 'media_type'):
            node.format.media_type = 'IMAGE'
        node.format.file_format = 'OPEN_EXR'
        node.format.color_depth = '32'
        node.format.color_mode = 'RGBA'
        node.save_as_render = False
        if hasattr(node, 'file_output_items'):
            node.directory = str(output)
            node.file_name = name
            node.file_output_items.new('RGBA', name)
            destination = node.inputs[name]
        else:
            node.base_path = str(output)
            node.file_slots[0].path = name
            destination = node.inputs[0]
        group.links.new(source.outputs['Image' if name == 'albedo' else name], destination)
    return camera


def capture_images(folder, target):
    data = {}
    for name in ('albedo', 'material-mask', 'normal', 'height', 'surface', 'emission'):
        matches = list(folder.glob(name + '*.exr'))
        if len(matches) != 1:
            raise ValueError('Missing capture: ' + name + ': ' + str(matches))
        image = bpy.data.images.load(str(matches[0]), check_existing=False)
        w, h = image.size
        array = np.empty(w*h*4, dtype=np.float32)
        image.pixels.foreach_get(array)
        # Blender rows start at bottom (+Y becomes top after PNG row convention).
        # Deliberately keep bottom-to-top array order: screen top corresponds to -Y.
        data[name] = array.reshape(h, w, 4)
        bpy.data.images.remove(image)
    coverage = np.clip(data['albedo'][:, :, 3:4], 0, 1)
    occupied = coverage > 1e-6
    for name, array in data.items():
        if name == 'material-mask':
            # Cycles AOV alpha is geometric coverage, independent of material Alpha.
            # Combined alpha also includes transparency (possibly multiple surfaces).
            aov_coverage = np.maximum(array[:, :, 3:4].copy(), 1e-6)
            array[:, :, :3] = array[:, :, :3] / aov_coverage * coverage
            # Fourth channel is Fixed weight,
            # NOT opacity: independent RGBA data channels, sum equals coverage.
            array[:, :, :3] = np.minimum(np.maximum(array[:, :, :3], 0), coverage)
            array[:, :, 3:4] = np.clip(coverage - array[:, :, :3].sum(axis=2, keepdims=True), 0, 1)
        else:
            divisor = coverage if name == 'albedo' else array[:, :, 3:4].copy()
            array[:, :, :3] = np.where(occupied, array[:, :, :3] / np.maximum(divisor, 1e-6), 0)
            array[:, :, 3:4] = coverage
            if name == 'normal':
                normal = array[:, :, :3]*2-1
                normal /= np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 1e-8)
                array[:, :, :3] = np.where(occupied, normal*.5+.5, 0)
            if name == 'albedo':
                linear = array[:, :, :3]
                array[:, :, :3] = np.where(linear <= .0031308, linear*12.92,
                    1.055*np.maximum(linear, 0)**(1/2.4)-.055)
        write_png(target / (name + '.png'), array,
                  bits=16 if name in ('normal', 'height', 'emission') else 8, srgb=name == 'albedo')
    for file in folder.glob('*.exr'):
        file.unlink()
    return int(coverage.max() > .1)


def bake(request):
    root = Path(request['root'])
    profile = request['profile']
    record = request['records'][0]
    bid = record['id']
    spec = profile['blocks'][bid]
    path, assembly, _ = block_inputs(root, bid, spec)
    nodes, instances = assemble(root, spec, assembly, path)
    objects = [o for group in instances.values() for o in group]
    assign_roles(objects, profile['material_roles'])
    bpy.context.view_layer.update()
    frames = []
    aliases = {}
    replacements = []
    for state, value in spec['states'].items():
        if 'alias' in value:
            aliases[state] = value['alias']
            replacements.append({'state': state, 'uses': value['alias'], 'reason': value['reason']})
        else:
            frames.append((state, value['frame'], value.get('poses', {})))
    for name, clip in spec.get('clips', {}).items():
        if 'alias' in clip:
            aliases['clip-' + name] = clip['alias']
            replacements.append({'clip': name, 'uses': clip['alias'], 'reason': clip['reason']})
        else:
            frames.extend(('clip-' + name + '-' + str(i).zfill(4), f, {}) for i, f in enumerate(clip['frames']))
    rest = {name: o.matrix_basis.copy() for name, o in nodes.items()}
    def set_frame(frame, poses):
        for name, matrix in rest.items():
            nodes[name].matrix_basis = matrix
        bpy.context.scene.frame_set(frame)
        for name, pose in poses.items():
            if name not in nodes:
                raise ValueError('Unknown pose node: ' + name)
            nodes[name].matrix_basis = pose_matrix(pose)
        bpy.context.view_layer.update()
    bounds = []
    for _, frame, poses in frames:
        set_frame(frame, poses)
        stats = geometry(objects)
        bounds.extend(stats['bounds_bu'])
    bounds = np.array(bounds)
    low, high = bounds.min(axis=0), bounds.max(axis=0)
    scale, quality = spec['bu_per_cell'], request['quality']
    pixel = scale / quality
    pad = profile['padding_pixels'] * pixel
    fx0, fy0, fx1, fy1 = spec['footprint_bu']
    # One pixel-aligned common canvas for ALL frames and layers, footprint included.
    x0 = math.floor((min(low[0], fx0)-pad)/pixel)*pixel
    y0 = math.floor((min(low[1], fy0)-pad)/pixel)*pixel
    x1 = math.ceil((max(high[0], fx1)+pad)/pixel)*pixel
    y1 = math.ceil((max(high[1], fy1)+pad)/pixel)*pixel
    size = (round((x1-x0)/pixel), round((y1-y0)/pixel))
    if max(size) > profile['max_image_size']:
        raise ValueError('Canvas exceeds configured max_image_size: ' + str(size))
    z0, z1 = spec['height_range_bu']
    if low[2] < z0-1e-5 or high[2] > z1+1e-5:
        raise ValueError('Geometry exceeds configured height_range_bu: ' + bid + ': ' + str((low[2], high[2])))
    for mat in {m for o in objects for m in o.data.materials if m}:
        shader_maps(mat, profile, z0, z1)
    stage = Path(request['output'])
    capture = stage / 'Capture'
    capture.mkdir()
    configure_capture(profile, (x0, y0, x1, y1), size, capture)
    layer_reports = []
    for layer in spec['layers']:
        included = {o for iid in layer['instances'] for o in instances[iid]}
        for obj in objects:
            obj.hide_render = obj not in included
        bpy.context.view_layer.update()
        for state, frame, poses in frames:
            set_frame(frame, poses)
            bpy.ops.render.render()
            dest = stage / 'PNG' / state / layer['id']
            if not capture_images(capture, dest):
                raise ValueError('Empty rendered layer: ' + layer['id'])
        for state, source in aliases.items():
            shutil.copytree(stage / 'PNG' / source / layer['id'], stage / 'PNG' / state / layer['id'])
        layer_reports.append(layer)
    capture.rmdir()
    return {'id': bid, 'quality': quality, 'device': profile.get('device', 'CPU'),
            'size': size, 'canvas_bu': [x0, y0, x1, y1],
            'footprint_bu': spec['footprint_bu'], 'bu_per_cell': scale,
            'origin_pixels': [(fx0-x0)/pixel, (fy0-y0)/pixel],
            'axes': {'right': '+X', 'image_down': '+Y', 'normal_rgb': ['+X', '-Y', '+Z']},
            'height_range_bu': [z0, z1], 'height_range_cells': [z0/scale, z1/scale],
            'emission_max': profile['emission_max'], 'layers': layer_reports,
            'frames': [x[0] for x in frames] + list(aliases),
            'clips': spec.get('clips', {}), 'temporary_replacements': replacements,
            'demonstration_animation_exported': False,
            'mask_channels': dict(zip('RGBA', ROLES)),
            'mask_alpha_is_coverage': False, 'normal_encoding': 'RGB = normalized(+X,-Y,+Z)*0.5+0.5'}


def main():
    request = read_json(sys.argv[sys.argv.index('--')+1])
    if request['mode'] == 'metadata':
        from model_metadata import export_metadata
        result = export_metadata(request, assemble, pose_matrix, assign_roles)
    else:
        result = validate(request) if request['mode'] == 'validate' else bake(request)
    write_json(request['response'], result)


if __name__ == '__main__':
    main()
