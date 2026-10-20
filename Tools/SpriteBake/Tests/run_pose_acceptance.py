"""Transparent Fixed surfaces and union canvas across authored poses."""
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
    source = folder/'Projects/Test/Fixture/Parts/shared.blend'
    subprocess.run(base+[str(Path(__file__).with_name('patch_fixture_alpha.py')), '--', str(source)], stdout=log, stderr=subprocess.STDOUT, check=True)
profile_path = folder/'Projects/Test/Fixture/SpriteBake/profile.json'
profile = read_json(profile_path)
profile['blocks']['A']['states']['damage33'] = {'frame':1, 'poses':{'part':{'translation':[.4,.2,0]}}}
write_json(profile_path, profile)
cli.ROOT = folder
cli.main(['bake','--project','Test','--style','Fixture','--blocks','A','--quality','128','--blender',blender])
output = folder/'Projects/Test/Fixture/Exports/Sprites/128/A'
report = read_json(output/'Reports/report.json')
assert report['canvas_bu'][2] > 1.2, 'Union canvas missed shifted pose'
for state in ('damage0','damage33'):
    root = output/'PNG'/state/'body'
    albedo, mask = read_pixels(root/'albedo.png'), read_pixels(root/'material-mask.png')
    fixed = mask[:,:,3] > .15
    assert fixed.any()
    alpha = albedo[:,:,3][fixed]
    assert .25 < float(alpha.mean()) < .8, ('Transparent material did not preserve coverage', float(alpha.mean()))
    # Interior translucent pixels must retain the same physical map values as opaque ones.
    interior = (mask[:,:,3] > .7) & (albedo[:,:,3] < .8)
    assert interior.any()
    surface = read_pixels(root/'surface.png')
    height = read_pixels(root/'height.png')
    normal = read_pixels(root/'normal.png')
    assert np.max(abs(surface[interior,0]-.25)) < .01
    assert np.max(abs(surface[interior,1]-.6)) < .01
    assert np.max(abs(height[interior,0]-.4)) < .01
    assert np.max(abs(normal[interior,:3]-np.array([.5,.5,1]))) < .03
write_json(folder/'pose-acceptance.json', {'passed':True, 'checks':['transparent Fixed material','shared union canvas','distinct authored pose states','six aligned maps']})
print('POSE ACCEPTANCE PASSED',folder/'pose-acceptance.json')
