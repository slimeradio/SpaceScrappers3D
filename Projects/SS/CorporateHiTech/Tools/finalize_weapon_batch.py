from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
ids=[f'CHT-W{i:02}' for i in range(1,7)]
def save(p,s):
    p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
rows=[];unique=set()
for bid in ids:
    block=R/'Blocks'/bid;a=json.loads((block/'assembly.json').read_text(encoding='utf-8'));v=json.loads((block/'validation.json').read_text(encoding='utf-8'))
    assert not v['problems'] and not v['browserErrors'] and not v['failedRequests']
    export=block/v['export']['path'];assert hashlib.sha256(export.read_bytes()).hexdigest()==v['export']['sha256']
    sources=[block/'assembly.json']
    for i in a['instances']:
        p=(block/i['source']).resolve();d=json.loads(p.read_text(encoding='utf-8'));assert d['version']==i['partVersion'];sources.append(p);unique.add(d['id'])
    v['sourceSHA256']={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in set(sources)}
    save(block/'validation.json',json.dumps(v,ensure_ascii=False,indent=2)+'\n')
    rows.append((bid,a.get('title',a['catalogId']),len(set(i['partId'] for i in a['instances'])),len(a['instances'])))
readme=R/'README.md';text=readme.read_text(encoding='utf-8')
marker='## Готовые блоки вооружения'
suffix=''
if marker in text:
    marker_index=text.index(marker);next_section=text.find('\n## ',marker_index+len(marker))
    if next_section>=0:suffix=text[next_section:]
    text=text[:marker_index].rstrip()+'\n'
text+='\n'+marker+'\n\n'
for bid,title,parts,instances in rows:text+=f'- [{title}](Blocks/{bid}/README.md) — {bid}, {parts} деталей / {instances} экземпляров.\n'
text+='\nШесть финальных сборок зарегистрированы в существующем общем просмотрщике. Создано 26 новых деталей; подходящие CHT-P01/CHT-P02 переиспользованы без изменений. Редактируемая геометрия — Parts/*/part.json, сборки — Blocks/*/assembly.json; финальные glTF находятся в Exports/ каждой сборки. Проверки креплений, геометрии, крайних поз и экспорта — validation.json каждой сборки. Промежуточные варианты и отдельные просмотрщики не создавались. Масштаб в метрах и игровой импорт не установлены.\n'
text+=suffix
save(readme,text)
paths=[R/'Tools/verify_weapon_batch.cjs',R/'Tools/register_weapons.py',Path(__file__).resolve()]
for p in paths:save(p,p.read_text(encoding='utf-8'))
new_text=[]
for p in R.rglob('*'):
    if p.is_file() and p.suffix in {'.json','.md','.py','.cjs','.gltf'} and (any(part.startswith(tuple(ids)) for part in p.relative_to(R).parts) or p in paths):
        content=p.read_bytes();assert b'\n' not in content.replace(b'\r\n',b''),'LF text: '+str(p);new_text.append(p)
print('FINAL PASS:',len(rows),'blocks;',len(unique),'unique referenced parts; 26 new parts;',len(new_text),'CRLF files checked.')
