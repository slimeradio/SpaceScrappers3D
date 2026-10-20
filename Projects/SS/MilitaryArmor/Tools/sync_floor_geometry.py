"""Explicitly synchronize floor-fitted model geometry with the current game XML."""
from pathlib import Path
import sys,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from floor_fit import ROOT,read,write
sys.path.insert(0,str(ROOT.parents[2]/'Tools/SpriteBake'))
from definition_bridge import synchronize
parser=argparse.ArgumentParser();parser.add_argument('--game',required=True);parser.add_argument('--backups',required=True)
args=parser.parse_args();profile=read(ROOT/'SpriteBake/profile.json')
blocks=[read(ROOT/'Exports/Sprites/Metadata'/(bid+'.json')) for bid in profile['blocks']]
assert len(blocks)==64 and all(b['assembly'].get('floor_fit') for b in blocks)
report=synchronize(args.game,blocks,args.backups)
write(ROOT/'floor-definition-sync.json',report)
print('FLOOR_DEFINITION_SYNC',len(report['changes']),'files;',report['backup'])
