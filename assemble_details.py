"""Apply isolated detail patches to the unchanged v1 shell, validating paths."""
from pathlib import Path
import json,math,collections,hashlib
from voxel import Builder,ROOT

def load(path):
    obj=json.loads(path.read_text(encoding='utf-8'))
    return {(x,y,z):obj['palette'][i] for x,y,z,i in obj['blocks']}

base=load(ROOT/'qa/baseline_campus.json')
final=dict(base);owners={};overlaps=[];reports={}
for name in ['library','classrooms','north','specialist']:
    patch=load(ROOT/'parts'/f'detail_{name}.json')
    for pos,state in patch.items():
        if pos in owners and final.get(pos,'air')!=state:overlaps.append([name,owners[pos],*pos,final.get(pos,'air'),state])
        owners[pos]=name
        if state=='air':final.pop(pos,None)
        else:final[pos]=state
    reports[name]={'patch_entries':len(patch),'removed_cells':sum(state=='air' for state in patch.values())}
assert not overlaps,overlaps[:10]
assert all(final.get(pos)==state for pos,state in base.items() if pos[1]>=77),'Roof/shell changed'
assert all(final.get(pos)==state for pos,state in base.items() if 48<=pos[0]<=113 and 202<=pos[2]<=206),'Gate changed'
assert all(final.get((x,y,z)) is None for x in range(64,70) for z in range(176,215) for y in (65,66))

def open2(x,z,feet):return not any((x,feet+dy,z) in final for dy in (0,1))
def bfs(bounds,feet,start,targets):
    x1,x2,z1,z2=bounds
    todo=collections.deque([start]);seen={start}
    assert open2(*start,feet),(start,feet)
    while todo:
        x,z=todo.popleft()
        for p in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
            if x1<=p[0]<=x2 and z1<=p[1]<=z2 and p not in seen and open2(*p,feet):seen.add(p);todo.append(p)
    missing=[t for t in targets if t not in seen]
    assert not missing,(bounds,feet,missing)
    return {'two_block_body_reachable':len(seen),'targets_checked':len(targets),'all_reached':True}

paths={
 'library':bfs((58,89,125,136),65,(59,135),[(x,z) for x in range(58,90) for z in (131,132)]+[(85,133)]),
 'science':bfs((23,47,125,136),65,(24,135),[(x,z) for x in range(31,38) for z in range(125,133)]+[(44,133)]),
 'computer':bfs((58,89,125,136),73,(59,135),[(x,z) for x in range(59,89) for z in (128,129)]+[(88,133)]),
 'gym':bfs((47,78,34,85),66,(62,84),[(x,z) for x in range(66,70) for z in range(35,83)])}

for state in sorted(set(final.values())):
    assert (ROOT/'vendor/assets/minecraft/blockstates'/(state.split('[')[0]+'.json')).exists(),state
b=Builder('LQD_DaNang_Detail_v2');b.blocks=final;stats=b.save('campus.json')
manifest={'version':'detail_v2','stats':stats,'palette_count':len(set(final.values())),'patches':reports,'patch_conflicts':overlaps,
 'v1_roofs_preserved':True,'v1_gate_preserved':True,'entrance_clear':True,'circulation':paths,
 'changed_cells':sum(base.get(k)!=final.get(k) for k in set(base)|set(final)),
 'baseline_sha256':hashlib.sha256((ROOT/'qa/baseline_campus.json').read_bytes()).hexdigest(),
 'campus_sha256':hashlib.sha256((ROOT/'campus.json').read_bytes()).hexdigest(),
 'interior_accuracy':'Proposed room interiors; campus massing retained from provisional v1',
 'in_game_validation':False}
(ROOT/'qa/assembly.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=True))
