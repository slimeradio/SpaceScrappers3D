"""Read-only semantic inventory of Blender sources; never saves a blend file."""
import array
import hashlib
import json
from pathlib import Path
import sys
import traceback

import bpy

args = sys.argv[sys.argv.index('--') + 1:]
root, listing, output = map(Path, args[:3])


def value(v):
    if isinstance(v, float):
        return round(v, 5)
    if isinstance(v, (str, int, bool)) or v is None:
        if isinstance(v, str):
            v = v.replace(str(root), '<ROOT>').replace(str(root).replace('\\', '/'), '<ROOT>')
        return v
    if isinstance(v, bpy.types.ID):
        return v.name
    if hasattr(v, 'to_list'):
        return value(v.to_list())
    if hasattr(v, 'items'):
        return {str(k): value(x) for k, x in v.items()}
    try:
        return [value(x) for x in v]
    except TypeError:
        return str(v)


def properties(obj):
    result = {}
    excluded = {'rna_type', 'name', 'name_full', 'type', 'is_updated', 'is_updated_data',
                'select', 'location', 'width', 'height', 'dimensions', 'color', 'use_custom_color'}
    for prop in obj.bl_rna.properties:
        if prop.identifier in excluded or prop.is_readonly or prop.type == 'COLLECTION':
            continue
        try:
            result[prop.identifier] = value(getattr(obj, prop.identifier))
        except Exception:
            pass
    return result


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def custom(obj):
    return {k: value(obj[k]) for k in obj.keys() if k != '_RNA_UI'}


def animation(owner):
    data = owner.animation_data
    if not data:
        return None
    drivers = []
    for fc in data.drivers:
        d = fc.driver
        drivers.append([fc.data_path, fc.array_index, d.type, d.expression,
                        [[v.name, v.type, [[t.id.name if t.id else None, t.data_path,
                          t.bone_target, t.transform_type, t.transform_space] for t in v.targets]] for v in d.variables]])
    return {'action': data.action.name if data.action else None, 'drivers': drivers,
            'nla': [[t.name, [[s.name, s.action.name if s.action else None, round(s.frame_start, 5),
                              round(s.frame_end, 5), s.blend_type] for s in t.strips]] for t in data.nla_tracks]}


def mesh_data(mesh):
    coords = array.array('f', [0]) * (len(mesh.vertices)*3)
    mesh.vertices.foreach_get('co', coords)
    loops = array.array('i', [0]) * len(mesh.loops)
    mesh.loops.foreach_get('vertex_index', loops)
    uv = []
    for layer in mesh.uv_layers:
        uv.append([layer.name, digest([value(x.uv) for x in layer.data])])
    return {'vertices': digest([round(x, 5) for x in coords]),
            'loops': hashlib.sha256(loops.tobytes()).hexdigest(),
            'faces': digest([[p.loop_total, p.material_index, p.use_smooth] for p in mesh.polygons]),
            'uv': uv, 'counts': [len(mesh.vertices), len(mesh.edges), len(mesh.polygons)]}


def material(mat):
    nodes = []
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            item = [node.name, node.bl_idname, properties(node),
                    [[s.identifier, value(s.default_value)] for s in node.inputs if hasattr(s, 'default_value')]]
            if hasattr(node, 'color_ramp'):
                item.append([[value(e.position), value(e.color)] for e in node.color_ramp.elements])
            if hasattr(node, 'image') and node.image:
                image = node.image
                item.append([image.name, list(image.size), image.colorspace_settings.name,
                             hashlib.sha256(image.packed_file.data).hexdigest() if image.packed_file else image.filepath])
            nodes.append(item)
    return {'name': mat.name, 'nodes': nodes, 'diffuse': value(mat.diffuse_color),
            'links': sorted([[l.from_node.name, l.from_socket.identifier, l.to_node.name,
                              l.to_socket.identifier] for l in mat.node_tree.links]) if mat.use_nodes else [],
            'animation': animation(mat.node_tree) if mat.use_nodes else None}


def inspect(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    scene = bpy.context.scene
    scene.frame_set(1); bpy.context.view_layer.update()
    objects, used_materials = [], {}
    for obj in sorted(scene.objects, key=lambda o: o.name):
        if obj.type in {'LIGHT', 'CAMERA'} or obj.name.startswith(('studio', 'Studio')):
            continue
        item = {'name': obj.name, 'type': obj.type, 'parent': obj.parent.name if obj.parent else None,
                'matrix': value(obj.matrix_local), 'custom': custom(obj), 'animation': animation(obj),
                'modifiers': [[m.type, properties(m)] for m in obj.modifiers],
                'constraints': [[c.type, properties(c)] for c in obj.constraints]}
        if obj.type == 'MESH':
            item['mesh'] = mesh_data(obj.data)
        elif obj.type == 'CURVE':
            item['curve'] = {'settings': properties(obj.data), 'splines':
                [[s.type, s.use_cyclic_u, [[value(p.co), value(p.handle_left), value(p.handle_right)]
                  for p in s.bezier_points], [value(p.co) for p in s.points]] for s in obj.data.splines]}
        item['materials'] = [s.material.name if s.material else None for s in obj.material_slots]
        for slot in obj.material_slots:
            if slot.material:
                used_materials[slot.material.name] = slot.material
        objects.append(item)
    actions = []
    for a in sorted(bpy.data.actions, key=lambda a: a.name):
        curves = []
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        curves.append([fc.data_path, fc.array_index,
                            [[value(k.co), value(k.handle_left), value(k.handle_right), k.interpolation]
                             for k in fc.keyframe_points]])
        actions.append([a.name, curves])
    poses = []
    for frame in sorted(set([scene.frame_start, scene.frame_end, 17, 31, 60, 120])):
        scene.frame_set(frame); bpy.context.view_layer.update()
        poses.append([frame, [[o.name, value(o.matrix_world)] for o in sorted(scene.objects, key=lambda o:o.name)
                             if o.type not in {'LIGHT', 'CAMERA'} and not o.name.startswith(('studio', 'Studio'))]])
    missing = [i.filepath for i in bpy.data.images if i.source == 'FILE' and not i.packed_file
               and not Path(bpy.path.abspath(i.filepath)).is_file()]
    components = {'objects': digest(objects), 'materials': digest([material(m) for _, m in sorted(used_materials.items())]),
                  'actions': digest(actions), 'poses': digest(poses),
                  'texts': digest([[t.name, t.as_string()] for t in bpy.data.texts]),
                  'range': [scene.frame_start, scene.frame_end, scene.render.fps]}
    result = {'fingerprint': digest(components), 'components': components, 'objects': len(objects),
              'meshes': sum('mesh' in o for o in objects), 'actions': len(actions), 'missing_images': missing}
    if '--details' in args:
        result['details'] = objects
    return result


records = {}
for rel in json.loads(listing.read_text('utf-8')):
    path = root/rel
    if not path.is_file():
        continue
    try:
        records[rel] = inspect(path)
    except Exception:
        records[rel] = {'error': traceback.format_exc()}
    output.write_bytes((json.dumps(records, ensure_ascii=False, indent=2).replace('\n', '\r\n')+'\r\n').encode())
    print('INSPECT', len(records), rel, flush=True)
