import sys,runpy
from pathlib import Path
sys.argv.append('--verify')
runpy.run_path(str(Path(__file__).with_name('build_MA_I05.py')),run_name='__main__')
