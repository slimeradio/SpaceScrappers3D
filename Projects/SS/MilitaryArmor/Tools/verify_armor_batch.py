"""Index all four final armor assets and verify catalog coverage/GLB budgets."""
from pathlib import Path
import csv,json,struct,hashlib
ROOT=Path(__file__).resolve().parents[1]
catalog={r['ID']:r for r in csv.DictReader((ROOT.parent/'Catalog/blocks.csv').open(encoding='utf-8-sig',newline='')) if r['Тип_XML']=='Armor'}
spec=json.loads((ROOT/'armor-spec.json').read_text(encoding='utf8'))
records=[];errors=[]
for bid,cid in spec['ids'].items():
    folder=ROOT/'Blocks'/bid;assembly=json.loads((folder/'assembly.json').read_text(encoding='utf8'));validation=json.loads((folder/'validation.json').read_text(encoding='utf8'))
    raw=(folder/'Exports'/(bid+'.glb')).read_bytes();magic,ver,size=struct.unpack_from('<4sII',raw);n,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n].decode('utf8').rstrip())
    tris=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
    grid=[int(catalog[cid]['Ширина_клеток']),int(catalog[cid]['Высота_клеток'])]
    if assembly['catalog_id']!=cid or assembly['catalog_grid']!=grid:errors.append(bid+': catalog mismatch')
    if magic!=b'glTF' or ver!=2 or size!=len(raw):errors.append(bid+': GLB container')
    if len(doc['meshes'])>2 or len(doc.get('materials',[]))>3 or tris>240:errors.append(bid+': geometry budget')
    if any('uri' in b for b in doc.get('buffers',[])) or doc.get('images'):errors.append(bid+': external/image dependency')
    if doc.get('animations') or any(any(c>0 for c in m.get('emissiveFactor',[])) for m in doc.get('materials',[])):errors.append(bid+': unwanted animation/emission')
    if not validation['checks_passed']:errors.append(bid+': validation failed')
    for instance in assembly['instances']:
        source=(folder/instance['source']).resolve();part=json.loads(source.with_name('part.json').read_text(encoding='utf8'))
        if not source.exists() or part['version']!=instance['version'] or instance['scale']!=[1,1,1]:errors.append(bid+': dependency/version/scale')
        if part['emission'] or part['animations'] or part['functional_points']:errors.append(bid+': armor has unnecessary functions')
    records.append({'id':bid,'title':catalog[cid]['Название_пояснительное'],'catalog_id':cid,'catalog_grid':grid,'source':f'Blocks/{bid}/{bid}.blend','viewer_asset':f'Blocks/{bid}/Exports/{bid}.glb','parts':sorted(set(x['part_id'] for x in assembly['instances'])),'triangles':tris,'mesh_count':len(doc['meshes']),'material_count':len(doc.get('materials',[])),'GLB_bytes':len(raw),'GLB_sha256':hashlib.sha256(raw).hexdigest()})
if set(catalog)!=set(spec['ids'].values()):errors.append('Armor catalog coverage incomplete')
texts=list((ROOT/'Blocks').glob('MA-A*/**/*.md'))+list((ROOT/'Blocks').glob('MA-A*/**/*.json'))+list((ROOT/'Parts').glob('MA-A*/**/*.json'))+list((ROOT/'Tools').glob('*MA_A*.py'))+[Path(__file__),ROOT/'armor-spec.json']
for p in texts:
    if b'\n' in p.read_bytes().replace(b'\r\n',b''):errors.append(str(p)+': non-CRLF')
def write(p,s):p.write_bytes((s.replace('\r\n','\n').rstrip()+'\n').replace('\n','\r\n').encode('utf8'))
result={'schema':'MilitaryArmor.ArmorAuthoringIndex/1','style':'MilitaryArmor','models':records,'catalog_variants':len(catalog),'coverage_complete':not errors,'checks_passed':not errors,'errors':errors,'edge_contract':'armor-spec.json','game_validation':False}
write(ROOT/'armor.json',json.dumps(result,ensure_ascii=False,indent=2))
lines=['# Броня MilitaryArmor','','Полный набор четырёх вариантов из общего каталога SS. Спокойная гранёная форма: широкое плечо, срезанные верхние углы, узкий поясок и утопленное поле. Структурные кромки и толщина согласованы для повторяющейся обшивки. Без подсветки, болтов и навесного декора.','','| ID | Блок | Треугольники | Меши / материалы | Просмотр | Исходник |','|---|---|---:|---|---|---|']
for r in records:lines.append(f'| {r["id"]} | {r["title"]} | {r["triangles"]} | {r["mesh_count"]} / {r["material_count"]} | [GLB]({r["viewer_asset"]}) | [Blender]({r["source"]}) |')
lines+=['','Каждая сборка использует отдельную редактируемую деталь из Parts/. Точки и области крепления — логические метаданные, без видимых вспомогательных мешей. Состав и преобразования — assembly.json; материалы и метаданные деталей — part.json; результаты повторного открытия, импорта GLB и проверки геометрии — validation.json в папке блока.','', 'Окончательные модели проверены отдельно и в повторяющихся полях соседних блоков. Пользовательских промежуточных вариантов и сравнительных изображений нет.','', 'Единица авторинга: один визуальный шаг = 1 BU, толщина 0.28 BU; это согласованная пропорция моделей, не перевод клеток в метры. Физический масштаб, игровые коллайдеры и интеграция в игру не устанавливались.']
write(ROOT/'Armor.md','\n'.join(lines))
print(json.dumps({'blocks':len(records),'triangles':[r['triangles'] for r in records],'checked':not errors,'errors':errors},ensure_ascii=False,indent=2));assert not errors
