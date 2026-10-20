"""Blender subprocess entry point for one explicitly opened file."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_blender import export

source, target = sys.argv[sys.argv.index('--') + 1:]
export(Path(source), Path(target))
