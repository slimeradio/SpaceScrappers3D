from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from definition_bridge import patch_coordinates, synchronize


class DefinitionBridgeTests(unittest.TestCase):
    def test_floor_drill_geometry_preserves_cost_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            game=Path(folder);content=game/'Assets/Definitions';content.mkdir(parents=True)
            path=content/'drill.definition.xml'
            path.write_bytes(b'\xef\xbb\xbf<Block Name="drill"><Size X="1" Y="2"/><Drill PowerPerSecond="12"><Head X="0" Y="0" Radius="1"/><Head X="1" Y="1" Radius="1"/></Drill></Block>\r\n')
            block={'id':'D','catalog_id':'drill','footprint_bu':[-.5,-1,.5,1],'bu_per_cell':1,
                'assembly':{'floor_fit':{'drill_head_order':['left','right'],'drill_radii_cells':{'left':.2,'right':.3}}},
                'frames':{'damage0':{'points':[{'id':'right','position_cells':[.9,-.4,0]},{'id':'left','position_cells':[.1,-.4,0]}]}}}
            synchronize(game,[block],game/'backups');data=path.read_bytes()
            self.assertTrue(data.startswith(b'\xef\xbb\xbf'));self.assertTrue(data.endswith(b'\r\n'))
            self.assertIn(b'PowerPerSecond="12"',data);self.assertIn(b'X="0.1" Y="-0.4" Radius="0.2"',data)
            self.assertIn(b'X="0.9" Y="-0.4" Radius="0.3"',data)
            self.assertEqual(synchronize(game,[block],game/'backups')['changes'],[])

    def test_floor_thrust_binding_preserves_individual_force_and_resource(self):
        with tempfile.TemporaryDirectory() as folder:
            game=Path(folder);content=game/'Assets/Definitions';content.mkdir(parents=True)
            path=content/'engine.definition.xml'
            path.write_text('<Block Name="engine"><Size X="1" Y="2"/><Resources><Resource Id="2" UsePerSecond="8"/></Resources><Thrusters><Thruster><Position X="0" Y="0"/><Direction X="1" Y="0"/><Force>17</Force></Thruster><Thruster><Position X="1" Y="1"/><Direction X="1" Y="0"/><Force>43</Force></Thruster></Thrusters></Block>')
            points=[{'id':name+'/thrust','position_cells':[x,.4,0],'position_bu':[x,.4,0]} for name,x in [('a',.1),('b',.9)]]
            points.extend({'id':name+'/exhaust','position_bu':[x,-.6,0]} for name,x in [('a',.1),('b',.9)])
            block={'id':'E','catalog_id':'engine','footprint_bu':[-.5,-1,.5,1],'bu_per_cell':1,
                'assembly':{'floor_fit':{'thruster_point_order':['b/thrust','a/thrust']}},'frames':{'damage0':{'points':points}}}
            synchronize(game,[block],game/'backups');data=path.read_text()
            self.assertIn('<Position X="0.9" Y="0.4"/><Direction X="0" Y="-1"/><Force>17',data)
            self.assertIn('<Position X="0.1" Y="0.4"/><Direction X="0" Y="-1"/><Force>43',data)
            self.assertIn('UsePerSecond="8"',data)
            self.assertEqual(synchronize(game,[block],game/'backups')['changes'],[])

    def test_floor_head_count_mismatch_does_not_mutate_xml(self):
        with tempfile.TemporaryDirectory() as folder:
            game=Path(folder);content=game/'Assets/Definitions';content.mkdir(parents=True)
            path=content/'drill.definition.xml';original=b'<Block Name="drill"><Size X="1" Y="1"/><Drill><Head X="0" Y="0" Radius="1"/></Drill></Block>';path.write_bytes(original)
            block={'id':'D','catalog_id':'drill','footprint_bu':[-.5,-.5,.5,.5],'bu_per_cell':1,'assembly':{'floor_fit':{'drill_head_order':[],'drill_radii_cells':{}}},'frames':{'damage0':{'points':[]}}}
            with self.assertRaisesRegex(ValueError,'head count'):synchronize(game,[block],game/'backups')
            self.assertEqual(path.read_bytes(),original)

    def test_mining_model_point_can_be_outside_footprint(self):
        with tempfile.TemporaryDirectory() as folder:
            game=Path(folder)
            content=game/'Assets/Definitions'
            content.mkdir(parents=True)
            path=content/'mining.definition.xml'
            path.write_bytes(b'<Block Name="mining"><Size X="1" Y="3"/><MiningLaser Range="35" MuzzleX="0.5" MuzzleY="2.5"/></Block>')
            block={'id':'MINING','catalog_id':'mining','footprint_bu':[-.5,-1.5,.5,1.5], 'bu_per_cell':1,
                   'frames':{'damage0':{'points':[{'id':'optic','category':'functional_points',
                              'role':'mining-beam-origin','position_cells':[.5,-.69,1],
                              'forward_block':[0,-1,0]}]}}}
            result=synchronize(game,[block],game/'backups')
            self.assertIn(b'MuzzleX="0.5" MuzzleY="-0.69"',path.read_bytes())
            self.assertEqual(result['coverage'][0]['status'],'mining-geometry-synced')
            self.assertEqual(synchronize(game,[block],game/'backups')['changes'],[])

    def test_preserves_bom_crlf_comments_and_unrelated_attributes(self):
        original = b'\xef\xbb\xbf<?xml version="1.0"?>\r\n<Barrel Name="test">\r\n<!-- keep -->\r\n <ShootPosition Y="1" X="2" />\r\n</Barrel>\r\n'
        changed = patch_coordinates(original, 'ShootPosition', [-.25, 3.125])
        self.assertEqual(changed, original.replace(b'Y="1" X="2"', b'Y="3.125" X="-0.25"'))

    def test_rejects_duplicate_coordinate_elements(self):
        with self.assertRaisesRegex(ValueError, 'Expected one XML element'):
            patch_coordinates(b'<ShootPosition X="1" Y="1"/><ShootPosition X="0" Y="0"/>', 'ShootPosition', [0, 0])

    def test_model_geometry_sync_missing_definition_and_repeat(self):
        with tempfile.TemporaryDirectory() as folder:
            game = Path(folder)
            content = game / 'Assets/Definitions'
            content.mkdir(parents=True)
            files = {
                'block': '<Block Name="block"><Size X="2" Y="3"/><Turret Ref="mount"/><WeaponDefinition Ref="gun"/></Block>',
                'mount': '<Turret Name="mount"><RotationPivot X="1" Y="1"/></Turret>',
                'gun': '<Weapon Name="gun"><Barrels><Barrel Ref="left"/><Barrel Ref="right"/></Barrels></Weapon>',
                'left': '<Barrel Name="left"><ShootPosition X="-1" Y="1"/></Barrel>',
                'right': '<Barrel Name="right"><ShootPosition X="1" Y="1"/></Barrel>'}
            for name, text in files.items():
                (content / (name+'.definition.xml')).write_bytes(text.encode())
            block = {'id': 'MODEL', 'catalog_id': 'block', 'footprint_bu': [-2, -3, 2, 3], 'bu_per_cell': 2,
                     'layers': [{'id': 'turret', 'rotates': True, 'pivot_bu': [0, 0]}],
                     'frames': {'damage0': {'points': [
                         {'id': 'right', 'local_id': 'muzzle', 'layer': 'turret', 'category': 'functional_points',
                          'position_bu': [1, -4, 0], 'direction_block': [0, -1, 0]},
                         {'id': 'left', 'local_id': 'muzzle', 'layer': 'turret', 'category': 'functional_points',
                          'position_bu': [-1, -4, 0], 'direction_block': [0, -1, 0]}]}}}
            report = synchronize(game, [block, {'id': 'VISUAL', 'catalog_id': 'new'}], game/'backups')
            self.assertEqual(len(report['changes']), 3)
            self.assertEqual(report['coverage'][1]['status'], 'missing-definition')
            self.assertIn(b'X="-0.5" Y="2"', (content/'left.definition.xml').read_bytes())
            self.assertIn(b'X="1" Y="1.5"', (content/'mount.definition.xml').read_bytes())
            self.assertEqual(synchronize(game, [block], game/'backups')['changes'], [])
            # A failed preflight must not mutate even the mount proposed earlier.
            before = (content/'mount.definition.xml').read_bytes()
            block['layers'][0]['pivot_bu'] = [1, 1]
            block['frames']['damage0']['points'].pop()
            with self.assertRaisesRegex(ValueError, 'muzzle count'):
                synchronize(game, [block], game/'backups')
            self.assertEqual((content/'mount.definition.xml').read_bytes(), before)
            # Another block retains its original shared mount, weapon and barrels.
            block['frames']['damage0']['points'].append({
                'id': 'left', 'local_id': 'muzzle', 'layer': 'turret', 'category': 'functional_points',
                'position_bu': [-1, -4, 0], 'direction_block': [0, -1, 0]})
            (content/'other.definition.xml').write_bytes(files['block'].replace('Name="block"', 'Name="other"').encode())
            originals = {n: (content/(n+'.definition.xml')).read_bytes() for n in ('mount','gun','left','right')}
            isolated = synchronize(game, [block], game/'backups')
            for name, data in originals.items():
                self.assertEqual((content/(name+'.definition.xml')).read_bytes(), data)
            self.assertIn(b'Ref="mount-block-model"', (content/'block.definition.xml').read_bytes())
            self.assertIn(b'Ref="gun-block-model"', (content/'block.definition.xml').read_bytes())
            self.assertTrue((content/'mount-block-model.definition.xml.meta').is_file())
            self.assertTrue(isolated['changes'])
            self.assertEqual(synchronize(game, [block], game/'backups')['changes'], [])
            fixed_path = content/'mount-block-model.definition.xml'
            fixed_data = fixed_path.read_bytes().replace(b'<Turret ', b'<Turret FiringArcDegrees="0" RotateSpeedDegreesPerSecond="0" ')
            fixed_path.write_bytes(fixed_data)
            block['layers'] = [{'id':'body','rotates':False}]
            for point in block['frames']['damage0']['points']:
                point['layer'] = 'body'
            self.assertEqual(synchronize(game, [block], game/'backups')['changes'], [])
            self.assertEqual(fixed_path.read_bytes(),fixed_data)


if __name__ == '__main__':
    unittest.main()
