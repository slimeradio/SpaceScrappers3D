from pathlib import Path
import json
r=Path(__file__).resolve().parents[1];workspace=r.parents[2]
p=workspace/'Viewer/catalog.json';catalog=json.loads(p.read_text(encoding='utf-8'))
titles={'CHT-W01':'Citadel · Артиллерия','CHT-W02':'Needle · Рельсовая турель','CHT-W03':'Cyclone · Пулемёт','CHT-W04':'Assault · Штурмовой дробовик','CHT-W05':'Bastion · Ракетная башня','CHT-W06':'Prism · Непрерывный лазер'}
for bid,title in titles.items():
    if not (r/'Blocks'/bid/'assembly.json').exists():continue
    assembly=json.loads((r/'Blocks'/bid/'assembly.json').read_text(encoding='utf-8'))
    entry=dict(id='SS/CorporateHiTech/'+bid,title=assembly.get('title',title)+' · '+bid,style='SS / CorporateHiTech',assembly='Projects/SS/CorporateHiTech/Blocks/'+bid+'/assembly.json',materials='Projects/SS/CorporateHiTech/Materials/materials.json',textures='Projects/SS/CorporateHiTech/Materials/SharedTexturesPreview/catalog.json')
    old=next((i for i,b in enumerate(catalog['blocks']) if b['id']==entry['id']),None)
    if old is None:catalog['blocks'].append(entry)
    else:catalog['blocks'][old]=entry
p.write_bytes((json.dumps(catalog,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8'))
print('Registered blocks:',len(catalog['blocks']))
