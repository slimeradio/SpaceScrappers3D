from pathlib import Path
from PIL import Image,ImageOps
import json,hashlib
R=Path(__file__).resolve().parents[1];SHARED=R.parents[2]/'SharedTextures'
OUT=R/'Materials/SharedTexturesPreview';OUT.mkdir(parents=True,exist_ok=True)
entries=[];errors=[]
all_files={str(p).lower():p for p in SHARED.rglob('*') if p.is_file()}
for p in sorted(SHARED.rglob('*')):
    if not p.is_file() or p.suffix.lower()!='.dds' or not p.stem.lower().endswith('_cm'):continue
    relative=p.relative_to(SHARED).as_posix();key=hashlib.sha256(relative.encode()).hexdigest()[:16]
    try:
        with Image.open(p) as source:
            size=list(source.size);image=source.convert('RGB');image.thumbnail((1024,1024),Image.Resampling.LANCZOS)
            image.save(OUT/(key+'.png'));image.thumbnail((128,128),Image.Resampling.LANCZOS);image.save(OUT/(key+'-thumb.png'))
        entry=dict(id=key,group=p.parent.name,name=p.stem[:-3],source='SharedTextures/'+relative,size=size,map=key+'.png',thumbnail=key+'-thumb.png')
        normal=all_files.get(str(p.with_name(p.stem[:-3]+'_ng'+p.suffix)).lower())
        if normal:
            with Image.open(normal) as im:
                im=im.convert('RGBA');im.thumbnail((1024,1024),Image.Resampling.LANCZOS);im.convert('RGB').save(OUT/(key+'-normal.png'))
                ImageOps.invert(im.getchannel('A')).convert('RGB').save(OUT/(key+'-roughness.png'))
            entry.update(normal=key+'-normal.png',roughness=key+'-roughness.png',normalSource='SharedTextures/'+normal.relative_to(SHARED).as_posix())
        entries.append(entry)
    except Exception as e:errors.append(dict(source=relative,error=str(e)))
manifest=dict(schema='cht-shared-texture-preview/1',description='Browser approximation: _cm RGB color; paired _ng RGB tangent normal; roughness=1-_ng alpha. CM alpha and ADD are not interpreted. Normal Y is user-selectable. Derived previews up to 1024px; source DDS unchanged.',entries=entries,errors=errors)
(OUT/'catalog.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8'))
print('Prepared',len(entries),'textures; errors:',errors)
