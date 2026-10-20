from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from block_package import export_package, verify_package
from common import digest, inventory, read_json, render_settings, write_json


class BlockPackageTests(unittest.TestCase):
    def test_portable_export_preserves_semantics_and_rejects_changed_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace/'Projects/SS/Test'
            source = root/'Parts/part.json'
            write_json(source, {'functional_points': [{'id':'muzzle','position':[0,-2,0]}]})
            write_json(root/'Blocks/A/assembly.json', {'id':'A'})
            content = workspace/'Game/Assets/Definitions'
            content.mkdir(parents=True)
            definition = b'<Block Name="test"><Size X="1" Y="1"/></Block>'
            (content/'test.definition.xml').write_bytes(definition)
            render = root/'Exports/Sprites/128/A'
            (render/'PNG/damage0/body').mkdir(parents=True)
            for name in ('albedo','material-mask','emission','normal','height','surface'):
                (render/('PNG/damage0/body/'+name+'.png')).write_bytes(b'checked-source-image')
            block = {'id':'A','catalog_id':'test','bu_per_cell':1,'footprint_bu':[0,0,1,1],
                     'layers':[{'id':'body'}], 'clips':{},'frames':{'damage0': {'points':[{'id':'muzzle'}]}},
                     'inputs':{'Parts/part.json':digest(source)}}
            report = {k:block[k] for k in ('bu_per_cell','footprint_bu','layers','clips','inputs')}
            report.update(frames=['damage0'],outputs=inventory(render))
            profile = {'blocks':{'A':{}}}
            report['render_settings'] = render_settings(profile, 'A')
            write_json(render/'Reports/report.json',report)
            summary = export_package(workspace,root,{'blocks':{'A':{}}},[block],workspace/'Game',128)
            result = Path(summary['path'])
            self.assertEqual(read_json(result/'Blocks/A/model.json')['frames'],block['frames'])
            self.assertEqual((result/'DefinitionSources/test.definition.xml').read_bytes(),definition)
            manifest = read_json(result/'package.json')
            self.assertIn('Blocks/A/model.json',manifest['files'])
            self.assertIn('DefinitionSources/test.definition.xml',manifest['files'])
            for name, hash_value in manifest['files'].items():
                self.assertEqual(digest(result/name),hash_value)
            self.assertEqual(verify_package(result)['maps'],6)
            with self.assertRaisesRegex(ValueError,'settings provenance'):
                export_package(workspace,root,{'blocks':{'A':{'states':{'damage0':{'frame':5}}}}},[block],workspace/'Game',128)
            original = (result/'package.json').read_bytes()
            (render/'PNG/damage0/body/albedo.png').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'corrupt image'):
                export_package(workspace,root,{'blocks':{'A':{}}},[block],workspace/'Game',128)
            self.assertEqual((result/'package.json').read_bytes(),original)
            (render/'PNG/damage0/body/albedo.png').write_bytes(b'checked-source-image')
            source.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Stale image source'):
                export_package(workspace,root,{'blocks':{'A':{}}},[block],workspace/'Game',128)


if __name__=='__main__':
    unittest.main()
