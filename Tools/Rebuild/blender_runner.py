"""Run one historical authoring recipe without producing game exports.

Used only in a disposable copy. Source files and saved models are never patched.
"""
import ast
import builtins
import importlib.machinery
import json
import os
from pathlib import Path
import runpy
import sys
import traceback

import bpy


def called(node, suffix):
    return any(isinstance(n, ast.Call) and ast.unparse(n.func).endswith(suffix)
               for n in ast.walk(node))


class SourceOnly(ast.NodeTransformer):
    def __init__(self, filename):
        self.filename = filename.replace('\\', '/')

    def visit_Call(self, node):
        self.generic_visit(node)
        name = ast.unparse(node.func)
        if name.endswith('bpy.ops.render.render'):
            node.func = ast.Name(id='_ss3d_render', ctx=ast.Load())
        if name.endswith('bpy.ops.export_scene.gltf'):
            node.func = ast.Name(id='_ss3d_forbidden', ctx=ast.Load())
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        core = (self.filename.endswith('/weapon_batch_core.py') and node.name == 'save'
                and 'self.bid' in ast.unparse(node))
        cm = self.filename.endswith('/weapon_asset_runtime.py') and node.name == 'finish'
        assembly = self.filename.endswith('/build_turret.py') and node.name == 'assembly_stage'
        if core or cm or assembly:
            for i, statement in enumerate(node.body):
                if called(statement, 'wm.save_as_mainfile'):
                    node.body = node.body[:i + 1]
                    if core:
                        node.body += ast.parse("write(folder/'validation.json', {'source_saved': True, 'source_only': True, 'game_validation': False}); return folder/(self.bid+'.blend')").body
                    break
        if self.filename.endswith('/weapon_asset_runtime.py') and node.name == '_export':
            node.body = ast.parse('return {}').body
        # Historical GLB roundtrip checks are outside source reconstruction.
        for i, statement in enumerate(node.body):
            if called(statement, 'import_scene.gltf'):
                node.body = node.body[:i] or [ast.Pass()]
                break
        return node

    def visit_Module(self, node):
        self.generic_visit(node)
        for i, statement in enumerate(node.body):
            if not isinstance(statement, (ast.FunctionDef, ast.ClassDef)) and called(statement, 'import_scene.gltf'):
                node.body = node.body[:i]
                break
        return node


original_source_to_code = importlib.machinery.SourceFileLoader.source_to_code


def source_to_code(self, data, path, *, _optimize=-1):
    tree = SourceOnly(str(path)).visit(ast.parse(data, filename=str(path)))
    return compile(ast.fix_missing_locations(tree), str(path), 'exec', optimize=_optimize)


importlib.machinery.SourceFileLoader.source_to_code = source_to_code
sys.dont_write_bytecode = True
importlib.machinery.SourceFileLoader.get_code = lambda self, fullname: self.source_to_code(self.get_data(self.path), self.path)

# Fast *real* preview renders; keep all scene settings as authored when saving.
original_render = bpy.ops.render.render


def render(*args, **kwargs):
        scene = bpy.context.scene
        saved = (scene.render.engine, scene.render.resolution_x,
                 scene.render.resolution_y, scene.render.resolution_percentage)
        try:
            scene.render.engine = 'BLENDER_WORKBENCH'
            scene.render.resolution_x = scene.render.resolution_y = 96
            scene.render.resolution_percentage = 100
            return original_render(*args, **kwargs)
        finally:
            (scene.render.engine, scene.render.resolution_x,
             scene.render.resolution_y, scene.render.resolution_percentage) = saved


def forbidden(*args, **kwargs):
    raise RuntimeError('GLB generation is disabled in source reconstruction')


builtins._ss3d_render = render
builtins._ss3d_forbidden = forbidden

args = sys.argv[sys.argv.index('--') + 1:]
recipe, result = Path(args[0]), Path(args[1])
sys.argv = [str(recipe), '--', *args[2:]]
sys.path.insert(0, str(recipe.parent))
status = {'recipe': str(recipe), 'ok': False}
try:
    tree = SourceOnly(str(recipe)).visit(ast.parse(recipe.read_text('utf-8-sig')))
    exec(compile(ast.fix_missing_locations(tree), str(recipe), 'exec'),
         {'__name__': '__main__', '__file__': str(recipe)})
    status['ok'] = True
except SystemExit as exc:
    status['ok'] = exc.code in (None, 0)
    status['error'] = str(exc)
except Exception:
    status['error'] = traceback.format_exc()
    traceback.print_exc()
result.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
if not status['ok']:
    raise SystemExit(1)
