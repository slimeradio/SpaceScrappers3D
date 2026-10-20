"""Blender-evaluated block semantics, independent of image capture and game rules."""
import copy
import math
from pathlib import Path

import bpy
from mathutils import Vector

from common import block_inputs, confined, digest, read_json


def vector(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 3 or not all(math.isfinite(x) for x in value):
        raise ValueError('Invalid vector: ' + label)
    return Vector(value)


def transformed(record, matrix):
    result = copy.deepcopy(record)
    if 'position' in record:
        position = matrix @ vector(record['position'], record['id'] + '.position')
    elif record.get('shape') == 'polygon' and record.get('vertices'):
        position = matrix.translation
        result['vertices_bu'] = [list(matrix @ vector(v, record['id'] + '.vertex')) for v in record['vertices']]
    else:
        raise ValueError('Missing semantic position: ' + record['id'])
    basis = matrix.to_3x3()
    # A normal transforms with the inverse transpose under nonuniform scale.
    for key in ('direction', 'forward', 'up', 'normal'):
        if key in record:
            transform = basis.inverted().transposed() if key == 'normal' else basis
            direction = transform @ vector(record[key], record['id'] + '.' + key)
            if direction.length < 1e-8:
                raise ValueError('Zero direction: ' + record['id'] + '.' + key)
            result[key + '_block'] = list(direction.normalized())
    result['position_bu'] = list(position)
    result['matrix_block_from_local'] = [list(row) for row in matrix]
    return result


def frame_plan(spec):
    frames, aliases = [], {}
    for state, value in spec['states'].items():
        if 'alias' in value:
            aliases[state] = value['alias']
        else:
            frames.append((state, value['frame'], value.get('poses', {})))
    for name, clip in spec.get('clips', {}).items():
        if 'alias' in clip:
            aliases['clip-' + name] = clip['alias']
        else:
            frames.extend(('clip-' + name + '-' + str(i).zfill(4), f, {}) for i, f in enumerate(clip['frames']))
    return frames, aliases


def export_metadata(request, assemble, pose_matrix, assign_roles):
    root = Path(request['root'])
    profile = request['profile']
    blocks = []
    for record in request['records']:
        bid = record['id']
        spec = profile['blocks'][bid]
        path, assembly, dependencies = block_inputs(root, bid, spec)
        dependencies = sorted(set(dependencies) | {confined(root, p) for p in record.get('dependencies', [])})
        part_nodes = {}
        nodes, _ = assemble(root, spec, assembly, path, part_nodes)
        assign_roles([obj for group in part_nodes.values() for obj in group.values()], profile['material_roles'])
        material_slots = {iid: {name: [{'id': mat.name, 'role': mat['ss_role']} for mat in obj.data.materials if mat]
                               for name, obj in group.items() if obj.type in ('MESH', 'CURVE', 'FONT', 'SURFACE')}
                          for iid, group in part_nodes.items()}
        parts = {}
        for instance in assembly['instances']:
            source = confined(root, path.parent / instance['source'])
            parts[instance['id']] = read_json(source.parent / 'part.json')
        layers = {iid: layer['id'] for layer in spec['layers'] for iid in layer['instances']}
        rest = {name: obj.matrix_basis.copy() for name, obj in nodes.items()}
        frames, aliases = frame_plan(spec)
        results = {}
        for label, frame, poses in frames:
            for name, matrix in rest.items():
                nodes[name].matrix_basis = matrix
            bpy.context.scene.frame_set(frame)
            for name, pose in poses.items():
                if name not in nodes:
                    raise ValueError('Unknown pose node: ' + name)
                nodes[name].matrix_basis = pose_matrix(pose)
            bpy.context.view_layer.update()
            evaluated = bpy.context.evaluated_depsgraph_get()
            semantics = []
            for instance in assembly['instances']:
                iid = instance['id']
                metadata = parts[iid]
                seen = set()
                for category in ('mounts', 'functional_points', 'attachment_areas'):
                    for point in metadata.get(category, []):
                        identity = category + '/' + point['id']
                        if identity in seen:
                            raise ValueError('Duplicate semantic ID: ' + iid + '/' + identity)
                        seen.add(identity)
                        # node identifies an authoring marker; coordinates are local to parent.
                        # It is not an extra transform applied to the declared position.
                        parent = point.get('parent')
                        if parent in (None, 'part', metadata['id']):
                            obj = nodes[iid]
                        else:
                            if parent not in part_nodes[iid]:
                                raise ValueError('Unknown semantic parent: ' + iid + '/' + str(parent))
                            obj = part_nodes[iid][parent]
                        matrix = obj.evaluated_get(evaluated).matrix_world
                        if 'local_pose' in point:
                            matrix = matrix @ pose_matrix(point['local_pose'])
                        value = transformed(point, matrix)
                        value.update(id=iid + '/' + identity, local_id=point['id'],
                                     instance=iid, part=metadata['id'], category=category, layer=layers[iid])
                        position = value['position_bu']
                        scale = spec['bu_per_cell']
                        fx0, fy0, _, _ = spec['footprint_bu']
                        value['position_cells'] = [(position[0]-fx0)/scale, (position[1]-fy0)/scale, position[2]/scale]
                        semantics.append(value)
            results[label] = {'source_frame': frame, 'points': semantics,
                              'nodes': {name: [list(row) for row in obj.evaluated_get(evaluated).matrix_world]
                                        for name, obj in nodes.items()}}
        for alias, source in aliases.items():
            results[alias] = dict(copy.deepcopy(results[source]), alias_of=source)
        blocks.append({'schema': 'SpriteBake.BlockMetadata/1', 'id': bid,
                       'catalog_id': assembly['catalog_id'], 'axes': profile['axes'],
                       'bu_per_cell': spec['bu_per_cell'], 'footprint_bu': spec['footprint_bu'],
                       'layers': copy.deepcopy(spec['layers']), 'states': copy.deepcopy(spec['states']),
                       'clips': copy.deepcopy(spec.get('clips', {})), 'frames': results,
                       'assembly': assembly, 'parts': parts, 'material_slots': material_slots,
                       'profile': copy.deepcopy(spec),
                       'inputs': {p.relative_to(root).as_posix(): digest(p) for p in dependencies},
                       'dependencies': [p.relative_to(root).as_posix() for p in dependencies]})
        print('METADATA', bid, len(results['damage0']['points']), flush=True)
    return {'schema': 'SpriteBake.ModelMetadata/1', 'blocks': blocks}
