"""Real Blender regression: transformed semantic points, directions, aliases and invalid parents."""
import json
from pathlib import Path
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import read_json, write_json


def main():
    blender, folder = sys.argv[1:]
    folder = Path(folder).resolve() / uuid.uuid4().hex[:12]
    folder.mkdir(parents=True, exist_ok=True)
    tests = Path(__file__).parent
    tools = tests.parent
    def run(script, args, name, success=True):
        with (folder / (name + '.log')).open('wb') as stream:
            result = subprocess.run([blender, '--background', '--factory-startup', '--disable-autoexec',
                                     '--python-exit-code', '1', '--python', str(script), '--', *args],
                                    stdout=stream, stderr=subprocess.STDOUT)
        assert (result.returncode == 0) == success, name
    run(tests / 'make_fixture.py', [str(folder)], 'fixture')
    root = folder / 'Projects/Test/Fixture'
    part_path = root / 'Parts/part.json'
    part = read_json(part_path)
    part['functional_points'] = [{'id': 'muzzle', 'position': [0, -2, 0],
                                  'direction': [0, -1, 0], 'up': [0, 0, 1]}]
    part['attachment_areas'] = [{'id': 'mount', 'position': [0, 0, 0], 'normal': [0, 0, -1],
                                 'up': [0, 1, 0], 'shape': 'rectangle', 'size': [1, 2],
                                 'compatibility': ['test']},
                                {'id': 'polygon', 'shape': 'polygon', 'vertices': [[0,0,0],[1,0,0],[0,1,0]],
                                 'local_pose': {'translation': [1,0,0]}, 'normal': [0,0,-1]}]
    write_json(part_path, part)
    profile = read_json(root / 'SpriteBake/profile.json')
    profile['blocks']['A']['states']['damage33'] = {'frame': 1, 'poses': {
        'part': {'translation': [2, 3, 0], 'rotation_euler_xyz': [0, 0, 1.5707963267948966]}}}
    request = {'root': str(root), 'profile': profile, 'records': [{'id': 'A'}],
               'mode': 'metadata', 'response': str(folder / 'response.json')}
    write_json(folder / 'request.json', request)
    run(tools / 'blender_worker.py', [str(folder / 'request.json')], 'metadata')
    block = read_json(folder / 'response.json')['blocks'][0]
    rest, moved = block['frames']['damage0']['points'][0], block['frames']['damage33']['points'][0]
    def close(actual, expected):
        assert all(abs(a-b) < 1e-5 for a, b in zip(actual, expected)), (actual, expected)
    close(rest['position_bu'], [0, -2, 0])
    close(moved['position_bu'], [4, 3, 0])
    close(moved['direction_block'], [1, 0, 0])
    close(moved['up_block'], [0, 0, 1])
    close(moved['position_cells'], [5, 4, 0])
    assert block['frames']['destroyed']['alias_of'] == 'damage0'
    assert block['frames']['damage0']['points'][1]['size'] == [1, 2]
    assert block['frames']['damage0']['points'][1]['compatibility'] == ['test']
    close(block['frames']['damage0']['points'][2]['vertices_bu'][1], [2,0,0])
    roles = {slot['role'] for objects in block['material_slots'].values()
             for slots in objects.values() for slot in slots}
    assert roles == {'Color1','Color2','Emissive','Fixed'}, roles
    assert block['inputs']['Parts/part.json']
    part['functional_points'][0]['parent'] = 'missing'
    write_json(part_path, part)
    run(tools / 'blender_worker.py', [str(folder / 'request.json')], 'invalid-parent', success=False)
    part['functional_points'][0].pop('parent')
    part['functional_points'][0]['direction'] = [0, 0, 0]
    write_json(part_path, part)
    run(tools / 'blender_worker.py', [str(folder / 'request.json')], 'invalid-direction', success=False)
    write_json(folder / 'verification.json', {'passed': True, 'checks': [
        'parent hierarchy', 'state pose', 'rotated direction', 'up vector', 'cell coordinates',
        'state aliases', 'attachment area dimensions and compatibility', 'input hashes',
        'polygon local pose and transformed vertices', 'all four resolved material roles',
        'invalid parent rejected', 'zero direction rejected']})
    print('PASS metadata acceptance:', folder)


if __name__ == '__main__':
    main()
