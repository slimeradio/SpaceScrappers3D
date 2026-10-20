from pathlib import Path
source=Path(__file__).with_name('build_MA_D01.py').read_text(encoding='utf-8-sig')
exec(source.split("p=Part('MA-D01-P01'")[0])
exec('# Dependency gate'+source.split('# Dependency gate',1)[1])
