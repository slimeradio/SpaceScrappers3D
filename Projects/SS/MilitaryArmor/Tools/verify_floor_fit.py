"""Independent export checks against the preserved pre-fit semantics."""
from pathlib import Path
import sys,math,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from floor_fit import ROOT,BACKUP,read,write,CORNER,MARGIN,FRAME
profile=read(ROOT/'SpriteBake/profile.json');results=[];point_count=0;original_parts={}
for bid,spec in profile['blocks'].items():
    old=read(BACKUP/'Metadata'/(bid+'.json'));new=read(ROOT/'Exports/Sprites/Metadata'/(bid+'.json'));fit=new['assembly']['floor_fit'];s=fit['uniform_scale'];t=fit['translation']
    assert spec['bu_per_cell']==1
    assert spec['layers'][0]['id']=='floor' and spec['layers'][0]['instances']==['Floor'] and not spec['layers'][0]['rotates']
    assert new['assembly']['instances'][-1]['id']=='Floor' and new['assembly']['instances'][-1]['parent'] is None
    for path,sha in old['inputs'].items():
        if path.startswith('Parts/'):
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
            original_parts[path]=sha
    max_error=0
    for frame,old_frame in old['frames'].items():
        index={p['id']:p for p in new['frames'][frame]['points']}
        for p in old_frame['points']:
            q=index[p['id']]
            error=max(abs(q['position_bu'][i]-(p['position_bu'][i]*s+t[i])) for i in range(3));max_error=max(max_error,error)
            assert error<1e-5,(bid,frame,p['id'],error)
            before_matrix=p['matrix_block_from_local'];after_matrix=q['matrix_block_from_local']
            assert max(abs(after_matrix[i][j]-(before_matrix[i][j]*s+(t[i] if j==3 else 0))) for i in range(3) for j in range(4))<1e-5,(bid,p['id'],'area/local transform')
            if 'vertices_bu' in p:
                assert max(abs(q['vertices_bu'][k][i]-(v[i]*s+t[i])) for k,v in enumerate(p['vertices_bu']) for i in range(3))<1e-5,(bid,p['id'],'area vertices')
            for key in ('forward_block','up_block','normal_block','direction_block'):
                if key in p:assert max(abs(q[key][i]-p[key][i]) for i in range(3))<1e-5,(bid,p['id'],key)
            point_count+=1
    floor=new['parts']['Floor'];assert floor['floor_parameters']['corner_cells']==CORNER and floor['floor_parameters']['frame_cells']==FRAME
    assert {m['role'] for m in floor['materials']}=={'Color1','Color2'}
    occupied=next(p for p in new['frames']['damage0']['points'] if p['id']=='Floor/attachment_areas/occupied-area')
    assert len(occupied['vertices_bu'])==len(floor['floor_parameters']['polygon'])
    results.append(dict(id=bid,max_semantic_error=max_error,margin=fit['margin_cells'],scale=s))
assert read(ROOT/'floor-source-preservation.json')['passed']
write(ROOT/'floor-export-validation.json',dict(passed=True,blocks=len(results),semantic_points_all_frames=point_count,unchanged_original_part_files=len(original_parts),results=results))
print('FLOOR_EXPORT_OK',len(results),'blocks;',point_count,'semantic points; unchanged native part files',len(original_parts))
