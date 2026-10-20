"""Opt-in author actions: actual sampled frames, never automatic demo export."""
from pathlib import Path
import sys
import subprocess
import uuid
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli
from common import read_json, write_json
from preview import read_pixels

blender = sys.argv[1]
folder = cli.ROOT/'Projects/SS/MilitaryArmor/Exports/Sprites/Acceptance'/uuid.uuid4().hex[:8]
folder.mkdir(parents=True)
with (folder/'fixture.log').open('wb') as log:
    base = [blender, '--background', '--factory-startup', '--disable-autoexec', '--python-exit-code', '1', '--python']
    subprocess.run(base+[str(Path(__file__).with_name('make_fixture.py')), '--', str(folder)], stdout=log, stderr=subprocess.STDOUT, check=True)
    source = folder/'Projects/Test/Fixture/Blocks/A/A.blend'
    subprocess.run(base+[str(Path(__file__).with_name('patch_fixture_action.py')), '--', str(source)], stdout=log, stderr=subprocess.STDOUT, check=True)
path = folder/'Projects/Test/Fixture/SpriteBake/profile.json'
profile = read_json(path)
profile['blocks']['A'].update(use_author_animation=True, clips={'fire':{'frames':[1,10],'fps':24}})
write_json(path, profile)
cli.ROOT = folder
cli.main(['bake','--project','Test','--style','Fixture','--blocks','A','--quality','128','--blender',blender])
output = folder/'Projects/Test/Fixture/Exports/Sprites/128/A'
positions = []
for frame in ('clip-fire-0000','clip-fire-0001'):
    alpha = read_pixels(output/'PNG'/frame/'body/albedo.png')[:,:,3]
    yy,xx=np.mgrid[:alpha.shape[0],:alpha.shape[1]]
    positions.append(float((alpha*xx).sum()/alpha.sum()))
assert abs((positions[1]-positions[0])-.8*128) < 2, positions
report = read_json(output/'Reports/report.json')
assert report['canvas_bu'][2] > 1.6
write_json(folder/'action-acceptance.json', {'passed':True, 'checks':['explicit author action loaded','sampled frame displacement','union canvas over clip frames']})
print('ACTION ACCEPTANCE PASSED',folder/'action-acceptance.json')
