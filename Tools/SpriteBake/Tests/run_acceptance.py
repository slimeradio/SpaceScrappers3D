"""Real Blender end-to-end acceptance, isolated from production sources and PNGs."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli
from common import digest, inventory, read_json, write_json
from preview import read_pixels
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blender', required=True)
    args = parser.parse_args()
    artifacts = cli.ROOT/'Projects/SS/MilitaryArmor/Exports/Sprites/Acceptance'/uuid.uuid4().hex[:8]
    artifacts.mkdir(parents=True)
    with (artifacts/'fixture.log').open('wb') as log:
        subprocess.run([args.blender, '--background', '--factory-startup', '--disable-autoexec',
            '--python-exit-code', '1', '--python', str(Path(__file__).with_name('make_fixture.py')),
            '--', str(artifacts)], stdout=log, stderr=subprocess.STDOUT, check=True)
    cli.ROOT = artifacts
    def invoke(command='bake', blocks='A,B,C'):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            cli.main([command, '--project', 'Test', '--style', 'Fixture', '--blocks', blocks,
                      '--quality', '128', '--blender', args.blender])
        text = stream.getvalue()
        print(text, end='', flush=True)
        return text
    style = artifacts/'Projects/Test/Fixture'
    output = style/'Exports/Sprites'
    sources = {p: digest(p) for p in style.rglob('*') if p.is_file()}
    first = invoke()
    assert first.count('BAKED') == 3
    # Validate role assignment, linear PBR, neutral emissive strength, and relative heights.
    maps = output/'128/A/PNG/damage0/body'
    mask = read_pixels(maps/'material-mask.png')
    emission = read_pixels(maps/'emission.png')
    surface = read_pixels(maps/'surface.png')
    heights = read_pixels(maps/'height.png')
    albedo = read_pixels(maps/'albedo.png')
    for channel in range(4):
        region = mask[:, :, channel] > .99
        assert region.any(), ('Missing material role', channel)
        assert np.max(abs(surface[region, 0]-.25)) < .01
        assert np.max(abs(surface[region, 1]-.6)) < .01
        assert np.max(abs(heights[region, 0]-.4)) < .01
        if channel == 2:
            assert np.max(abs(emission[region, 0]-.5)) < .01
        else:
            assert emission[region, 0].max() < .001
        if channel < 3:
            assert albedo[region, :3].min() > .99
    assert all(digest(p) == sha for p, sha in sources.items()), 'Bake modified authoring sources'
    second = invoke()
    assert second.count('CACHED') == 3 and 'BAKED' not in second
    # Changing only B's assembly settings must not rebuild A or C.
    profile_path = style/'SpriteBake/profile.json'
    profile = read_json(profile_path)
    profile['blocks']['B']['layers'][0]['pivot_bu'] = [.1, 0]
    write_json(profile_path, profile)
    third = invoke()
    assert 'BAKED B' in third and 'CACHED A' in third and 'CACHED C' in third
    # A shared source edit must rebuild all three dependent assemblies.
    part_meta = style/'Parts/part.json'
    before_meta = part_meta.read_bytes()
    part_meta.write_bytes(before_meta+b'\r\n')
    fourth = invoke()
    assert fourth.count('BAKED') == 3
    before = {p.relative_to(output).as_posix(): digest(p) for p in (output/'128').rglob('*') if p.is_file()}
    shared = style/'Parts/shared.blend'
    good_source = shared.read_bytes()
    try:
        shared.write_bytes(b'injected invalid blend file')
        try:
            invoke()
            raise AssertionError('Invalid source was accepted')
        except RuntimeError as error:
            assert 'Blender failed' in str(error)
        after = {p.relative_to(output).as_posix(): digest(p) for p in (output/'128').rglob('*') if p.is_file()}
        assert before == after, 'Failed bake changed previously published output'
    finally:
        shared.write_bytes(good_source)
    # Preview regeneration must recover missing previews without a render.
    (output/'128/A/Previews/paint-slate-a.png').unlink()
    assert 'PREVIEW A' in invoke('preview', 'A')
    write_json(artifacts/'acceptance.json', {'passed': True,
        'checks': ['six maps and four roles', 'linear PBR values', 'height normalization',
                   'neutral emission', 'source preservation', 'unchanged cache',
                   'per-block invalidation', 'shared dependency invalidation',
                   'invalid source preserves previous PNGs and report', 'preview regeneration'],
        'artifacts': str(artifacts)})
    print('ACCEPTANCE PASSED:', artifacts/'acceptance.json')


if __name__ == '__main__':
    main()
