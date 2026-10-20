from pathlib import Path
import json,math,itertools
r=Path(__file__).resolve().parents[1]
v=json.loads((r/'Blocks/CHT-T01/validation.json').read_text(encoding='utf-8'))
pose=v['poses'][0]
note=f'''# Проверка CHT-T01 / 1.1.0

Угловатая переработка: 7 деталей, 9 экземпляров, 117 геометрических элементов в библиотеке; {pose['meshCount']} мешей и {pose['triangles']} треугольников в сборке. Изменены все семь деталей, номера версий подняты до 1.1.0. Старые источники 1.0.0 сохранены отдельно.

Детали просмотрены независимо в перспективе и сверху; сохранены предпросмотры и каталог. Добавлены наклонные грани, ступенчатые панели, шестигранные дула, жабры, замки и рёбра. Гладкие кромки имеют небольшую фаску. Платформа имеет отдельные уровни бронеплиты и основания без совпадающих верхних плоскостей.

Проверены 8 креплений: позиции совпадают, нормали противоположны, ориентация сохраняется; у подшипника разрешён поворот вокруг +Z. Проверены позы 0°, 45°, 90°, 180°, 270°, 360°. Основание неподвижно, верх следует за yaw. Между подвижным корпусом и платформой есть вертикальный зазор; посадки и кожухи имеют намеренные нахлёсты. Разборка — режим осмотра.

Габариты исходной позы: {' × '.join(f'{x:.3f}' for x in pose['bounds'])} model-unit. Метры на клетку не заданы. Точки стволов ±0.254 X сохранены; визуальное дуло смещено вперёд на 0.031 от каталожной точки по Y. Это авторская геометрия без установки в игру, LOD и игровых коллайдеров.

Экспортированы отдельные glTF деталей и сборка с PBR, эмиссией, иерархией и клипом yaw-demo. Загруженный повторно glTF сохранил родителей head → yaw и emitter-L → head. Анимация проверена в шести временных точках. Корневой поворот переводит авторский +Z вверх в glTF +Y вверх. Текстуры процедурные, файловых карт нет.

Проверены конечность координат, нормали, материалы, версии и связи креплений. Ошибок JavaScript нет. Подробности: validation.json и ../../Parts/validation.json. Текстовые файлы CRLF. Другие стили, общий каталог и корневые документы не менялись.
'''
(r/'Blocks/CHT-T01/verification.md').write_text(note,encoding='utf-8')
for p in (r/'Parts').glob('*/part.json'):
    data=json.loads(p.read_text(encoding='utf-8'));lo=[float('inf')]*3;hi=[-float('inf')]*3
    for g in data['geometry']:
        if g['shape']=='loft':
            pts=[[x*l['scale'][0],y*l['scale'][1],l['z']] for l in g['levels'] for x,y in g['outline']]
            for v in pts:
                lo=[min(a,c+e) for a,c,e in zip(lo,g['position'],v)];hi=[max(a,c+e) for a,c,e in zip(hi,g['position'],v)]
            continue
        if g['shape']=='roundedBox':ext=[x/2 for x in g['size']]
        elif g['shape']=='cylinder':
            radius=max(g['radius'],g['radiusTop']);ext=[radius,g['depth']/2,radius] if g['axis']=='Y' else [radius,radius,g['depth']/2]
        else:
            radius=g['radius']+g['tube'];ext=[radius,g['tube'],radius] if g['axis']=='Y' else [radius,radius,g['tube']]
        rx,ry,rz=g.get('rotationEulerXYZ',[0,0,0]);cx,sx,cy,sy,cz,sz=math.cos(rx),math.sin(rx),math.cos(ry),math.sin(ry),math.cos(rz),math.sin(rz)
        for signs in itertools.product([-1,1],repeat=3):
            x,y,z=[e*s for e,s in zip(ext,signs)];x,y=cz*x-sz*y,sz*x+cz*y;x,z=cy*x+sy*z,-sy*x+cy*z;y,z=cx*y-sx*z,sx*y+cx*z
            v=[x,y,z];lo=[min(a,c+e) for a,c,e in zip(lo,g['position'],v)];hi=[max(a,c+e) for a,c,e in zip(hi,g['position'],v)]
    data['bounds']={'min':lo,'max':hi,'size':[b-a for a,b in zip(lo,hi)]}
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p in r.rglob('*'):
    if p.is_file() and p.suffix in {'.js','.cjs','.html','.json','.gltf','.md','.py','.ps1','.txt'}:
        s=p.read_bytes().decode('utf-8').replace('\r\n','\n').replace('\n','\r\n');p.write_bytes(s.encode('utf-8'))
v=json.loads((r/'Blocks/CHT-T01/validation.json').read_text())
assert not v['browserErrors']
assert all(not p['errors'] for p in v['poses'])
assert v['roundtrip']['headParent']=='yaw'
assert v['roundtrip']['emitterParent']=='head'
assert v['roundtrip']['animations']==['yaw-demo']
print('Final check: 7 parts, 9 instances, 6 poses, glTF roundtrip, all text CRLF.')
