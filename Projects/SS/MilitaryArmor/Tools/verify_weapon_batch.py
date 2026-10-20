"""Verify and index the six final weapon assets without generating variants."""
import csv, json, hashlib, struct, math
from pathlib import Path
from xml.etree import ElementTree as ET

root=Path(__file__).resolve().parents[1]
catalog={r['ID']:r for r in csv.DictReader((root.parent/'Catalog/blocks.csv').open(encoding='utf-8-sig',newline=''))}
names=['Трёхствольная тяжёлая артиллерия','Турель непрерывного лазера','Двухствольная скорострельная турель Cyclone','Четырёхканальная ракетная установка Bastion','Веерный дробовик Fan','Снайперский рельсотрон']
records=[];new_parts=set();hashes=set();failures=[]
for i,title in enumerate(names,1):
    bid=f'MA-W{i:02}';folder=root/'Blocks'/bid
    assembly=json.loads((folder/'assembly.json').read_text(encoding='utf8'))
    validation=json.loads((folder/'validation.json').read_text(encoding='utf8'))
    row=catalog[assembly['catalog_id']]
    grid=[int(row['Ширина_клеток']),int(row['Высота_клеток'])]
    expected=len(ET.fromstring(row['Оружие_XML']).findall('./Barrels/Barrel'))
    actual=0;part_ids=[]
    for instance in assembly['instances']:
        source=(folder/instance['source']).resolve()
        if not source.exists():failures.append(f'{bid}: missing {source}')
        part=json.loads(source.with_name('part.json').read_text(encoding='utf8'))
        if part['version']!=instance['version']:failures.append(f'{bid}: version mismatch {part["id"]}')
        if instance['scale']!=[1,1,1]:failures.append(f'{bid}: instance scale')
        actual+=len(part['functional_points']);part_ids.append(part['id'])
        if part['id'].startswith('MA-W'):new_parts.add(part['id'])
        for point in part['functional_points']:
            fwd=point.get('direction',point.get('forward'));up=point['up']
            if not fwd or abs(sum(x*x for x in fwd)-1)>.0001 or abs(sum(x*x for x in up)-1)>.0001 or abs(sum(x*y for x,y in zip(fwd,up)))>.0001:failures.append(f'{bid}: functional orientation')
    raw=(folder/'Exports'/(bid+'.glb')).read_bytes();magic,version,size=struct.unpack_from('<4sII',raw)
    n,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n].decode('utf8').rstrip())
    good_glb=magic==b'glTF' and version==2 and size==len(raw) and bool(doc.get('meshes')) and all('uri' not in b for b in doc.get('buffers',[])) and all('uri' not in img for img in doc.get('images',[]))
    if not good_glb:failures.append(f'{bid}: invalid/non-embedded GLB')
    if grid!=assembly['catalog_grid'] or actual!=expected:failures.append(f'{bid}: catalog/grid/functional points')
    if not validation.get('checks_passed',False):failures.append(f'{bid}: asset validation failed')
    if not (validation.get('glb_imported_in_Blender',False) or validation.get('glb_roundtrip',{}).get('imported_in_Blender',False)):failures.append(f'{bid}: missing roundtrip evidence')
    digest=hashlib.sha256(raw).hexdigest();hashes.add(digest)
    records.append({'id':bid,'title':title,'catalog_id':assembly['catalog_id'],'catalog_grid':grid,'source':f'Blocks/{bid}/{bid}.blend','viewer_asset':f'Blocks/{bid}/Exports/{bid}.glb','parts':sorted(set(part_ids)),'functional_points':actual,'GLB_meshes':len(doc['meshes']),'GLB_animations':len(doc.get('animations',[])),'GLB_bytes':len(raw),'GLB_sha256':digest})
texts=list((root/'Blocks').glob('MA-W*/**/*.json'))+list((root/'Blocks').glob('MA-W*/**/*.md'))+list((root/'Parts').glob('MA-W*/**/*.json'))+list((root/'Tools').glob('*MA_W*.py'))+[Path(__file__),root/'Tools/weapon_batch_core.py']
for p in texts:
    if b'\n' in p.read_bytes().replace(b'\r\n',b''):failures.append(f'{p}: non CRLF text')
if len(hashes)!=6:failures.append('Duplicate final models')
result={'schema':'MilitaryArmor.WeaponAuthoringIndex/1','style':'MilitaryArmor','models':records,'new_part_count':len(new_parts),'shared_part_ids':['MA-P06','MA-P07'],'checked':not failures,'failures':failures,'notes':'Final authoring assets; GLB for viewing, Blender editable sources. BU scale is unspecified. No game installation or acceptance.'}
def write(p,s):p.write_bytes((s.rstrip()+'\n').replace('\r\n','\n').replace('\n','\r\n').encode('utf8'))
write(root/'weapons.json',json.dumps(result,ensure_ascii=False,indent=2))
lines=['# Шесть блоков вооружения MilitaryArmor','','Финальные модели в утверждённом космическом направлении. GLB содержит материалы, иерархию и анимацию; редактируемые исходники Blender собраны из отдельных деталей.','','| ID | Блок | Сетка каталога | Просмотр | Исходник |','|---|---|---|---|---|']
for r in records:
    lines.append(f'| {r["id"]} | {r["title"]} | {r["catalog_grid"][0]}×{r["catalog_grid"][1]} | [GLB]({r["viewer_asset"]}) | [Blender]({r["source"]}) |')
lines+=['',f'Новых самостоятельных деталей: {len(new_parts)}. Сервисный картридж MA-P06 и лидар MA-P07 версии 1.3 использованы повторно. Состав и локальные преобразования находятся в assembly.json соответствующего блока; исходники деталей и их материалы/крепления/функциональные ориентиры — в Parts/.','', 'Клетки каталога не переведены в метры; это модели для авторинга и просмотра. Игровой экспорт и проверка в игре не выполнялись. Промежуточные пользовательские варианты и сравнительные изображения не создавались.']
write(root/'Weapons.md','\n'.join(lines))
print(json.dumps({'blocks':len(records),'new_parts':len(new_parts),'checks_passed':not failures,'failures':failures},ensure_ascii=False,indent=2))
assert not failures
