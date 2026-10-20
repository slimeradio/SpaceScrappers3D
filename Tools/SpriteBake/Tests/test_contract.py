import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (block_inputs, cache_valid, confined, digest, fingerprint,
                    inventory, load_profile, publish, write_json, catalog_entry)
from png import write_png
from preview import read_pixels, srgb_to_linear, linear_to_srgb
from block_package import image_settings_match
import numpy as np


class ContractTests(unittest.TestCase):
    def test_only_unused_added_role_mapping_keeps_original_image_provenance_valid(self):
        old = {'samples': 16, 'material_roles': {'Armor': 'Color2'}}
        new = {'samples': 16, 'material_roles': {'Armor': 'Color2', 'Thermal': 'Fixed'}}
        used = {'part': {'mesh': [{'id': 'Armor.001', 'role': 'Color2'}]}}
        self.assertTrue(image_settings_match(old, new, used))
        self.assertFalse(image_settings_match(old, new, {}))
        self.assertFalse(image_settings_match(old, new, None))
        self.assertEqual(old['material_roles'], {'Armor': 'Color2'})
        self.assertFalse(image_settings_match(old, new, {'part': {'mesh': [{'id': 'Thermal.001'}]}}))
        numbered = {'samples': 16, 'material_roles': {'Armor': 'Color2', 'Thermal.001': 'Fixed'}}
        self.assertFalse(image_settings_match(old, numbered, {'part': {'mesh': [{'id': 'Thermal.001'}]}}))
        changed = copy.deepcopy(new); changed['material_roles']['Armor'] = 'Fixed'
        self.assertFalse(image_settings_match(old, changed, used))
        changed = copy.deepcopy(new); changed['samples'] = 32
        self.assertFalse(image_settings_match(old, changed, used))
        self.assertFalse(image_settings_match(new, old, used))

    def test_catalog_dimensions_are_verified_against_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            path=root/'Projects/SS/Catalog/blocks.csv'
            path.parent.mkdir(parents=True)
            path.write_text('ID,Ширина_клеток,Высота_клеток\nblock,1,3\n',encoding='utf-8')
            self.assertEqual(catalog_entry(root,{'catalog_id':'block','catalog_grid':[1,3]})['grid'],[1,3])
            with self.assertRaisesRegex(ValueError,'Catalog grid mismatch'):
                catalog_entry(root,{'catalog_id':'block','catalog_grid':[1,2]})

    def test_png_lossless_rgba8_and_16(self):
        with tempfile.TemporaryDirectory() as temp:
            a = np.random.default_rng(42).random((9, 13, 4)).astype(np.float32)
            for bits in (8, 16):
                path = Path(temp)/str(bits)
                write_png(path, a, bits)
                self.assertLessEqual(float(np.max(abs(a-read_pixels(path)))), 1/((1 << bits)-1))

    def test_png_crc_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'test.png'
            write_png(path, np.ones((2, 2, 4)))
            data = bytearray(path.read_bytes()); data[20] ^= 1
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'CRC'):
                read_pixels(path)

    def test_nonfinite_pixels_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            write_png('unused.png', np.full((1, 1, 4), np.nan))

    def test_path_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'escapes'):
                confined(Path(temp)/'style', '../other/model.blend', exists=False)

    def test_publication_restores_previous_on_rename_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); target = root/'target'; stage = root/'stage'
            target.mkdir(); stage.mkdir()
            (target/'data').write_bytes(b'old'); (stage/'data').write_bytes(b'new')
            rename = Path.rename
            def injected(path, destination):
                if path == stage:
                    raise OSError('injected publication failure')
                return rename(path, destination)
            with mock.patch.object(Path, 'rename', injected):
                with self.assertRaisesRegex(OSError, 'injected'):
                    publish(stage, target)
            self.assertEqual((target/'data').read_bytes(), b'old')
            self.assertFalse((root/'target.previous').exists())

    def test_publication_rejects_unresolved_previous(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'stage').mkdir(); (root/'target.previous').mkdir()
            with self.assertRaisesRegex(RuntimeError, 'recovery'):
                publish(root/'stage', root/'target')

    def test_cache_detects_changed_and_missing_png(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); image = root/'PNG/x.png'; image.parent.mkdir()
            image.write_bytes(b'first')
            write_json(root/'Reports/report.json', {'fingerprint': 'x', 'outputs': inventory(root)})
            self.assertTrue(cache_valid(root, 'x'))
            self.assertFalse(cache_valid(root, 'other'))
            image.write_bytes(b'changed')
            self.assertFalse(cache_valid(root, 'x'))
            image.unlink()
            self.assertFalse(cache_valid(root, 'x'))

    def test_fingerprint_is_per_block_and_actual_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); shared = root/'shared'; local = root/'local'
            shared.write_bytes(b'part'); local.write_bytes(b'other')
            profile = {'material_roles': {'a': 'Color1'}, 'blocks': {'A': {'a': 1}, 'B': {'a': 2}}}
            def key(bid, deps): return fingerprint(root, profile, bid, deps, 128, 'Blender test')[0]
            a, b = key('A', [shared]), key('B', [local])
            profile['blocks']['B']['a'] = 3
            self.assertEqual(a, key('A', [shared]))
            self.assertNotEqual(b, key('B', [local]))
            b = key('B', [local]); shared.write_bytes(b'new shared')
            self.assertNotEqual(a, key('A', [shared]))
            self.assertEqual(b, key('B', [local]))

    def test_color_transfer_roundtrip(self):
        x = np.linspace(0, 1, 101)
        np.testing.assert_allclose(linear_to_srgb(srgb_to_linear(x)), x, atol=1e-6)

    def test_current_profile_membership_and_catalog_dimensions(self):
        workspace = Path(__file__).resolve().parents[3]
        root, _, profile = load_profile(workspace, 'SS', 'MilitaryArmor')
        self.assertEqual(profile['pilot'], ['MA-A01', 'MA-T01', 'MA-E01'])
        for bid, spec in profile['blocks'].items():
            block_inputs(root, bid, spec)

    def test_duplicate_layer_membership_rejected(self):
        workspace = Path(__file__).resolve().parents[3]
        root, _, profile = load_profile(workspace, 'SS', 'MilitaryArmor')
        spec = copy.deepcopy(profile['blocks']['MA-A01'])
        spec['layers'][0]['instances'] *= 2
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            block_inputs(root, 'MA-A01', spec)


if __name__ == '__main__':
    unittest.main()
