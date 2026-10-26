"""Vanilla furniture patch: 30 interpreted classrooms in the south west wing.

The accepted shell and floor levels are retained. Interiors are design proposals,
not measured documentation of the real school's rooms.
"""
from pathlib import Path
import sys, json
from collections import Counter, deque
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from voxel import Builder

ROOT=Path(__file__).resolve().parents[1]
BAYS=(30,37,44,51,58,65,72,79,86,93)
CHAIR='birch_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]'
TEACHER_CHAIR='spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]'
DESK='birch_slab[type=top,waterlogged=false]'
TEACHER_DESK='spruce_slab[type=top,waterlogged=false]'

def baseline():
    d=json.loads((ROOT/'campus.json').read_text(encoding='utf-8'))
    return {(x,y,z):d['palette'][i] for x,y,z,i in d['blocks']}

def build():
    existing=baseline()
    b=Builder('detail_classrooms')
    for floor in range(3):
        low=65+4*floor
        carpet=('cyan_carpet','light_blue_carpet','blue_carpet')[floor]
        for left in BAYS:
            right=left+5; door=left+1
            # Remove v1 proposal furniture and accidental exterior plant/bench
            # intrusion strictly inside the room; keep wall and partition grid.
            b.fill(left,low,150,right,low+2,155,'air')
            b.fill(left,low-1,150,right,low-1,155,'smooth_quartz')
            b.fill(left,low-1,155,right,low-1,155,'light_gray_terracotta')
            # Two block broad entrance and spine remain unobstructed. Carpet
            # is a 1/16-block surface, not a full-height obstruction.
            b.fill(door,low,152,door+1,low,155,carpet)
            b.fill(door,low,156,door+1,low+1,156,'air')
            # Readable large green board, shelf, chalk tray and teacher station.
            b.fill(left+1,low+1,150,left+4,low+2,150,'green_concrete')
            b.set(left,low,150,'bookshelf')
            b.set(left,low,151,'lectern[facing=south,has_book=false,powered=false]')
            b.set(right,low,150,TEACHER_CHAIR)
            b.fill(left+4,low,151,right,low,151,TEACHER_DESK)
            # Two rows; single place to west, paired student benches to east.
            # Birch is lighter than teacher spruce and reads clearly at eye level.
            for z in (152,154):
                b.set(left,low,z,DESK)
                b.set(left,low,z+1,CHAIR)
                b.fill(left+3,low,z,right,low,z,DESK)
                for x in (left+3,right): b.set(x,low,z+1,CHAIR)
            # Compact pin board and clock substitute: simple vanilla materials,
            # no invented text/entity requirements or inaccessible containers.
            b.set(left,low+1,151,'yellow_terracotta')
            b.set(left,low+2,151,'white_concrete')
            # Existing glass and exterior wall z149 are untouched. No full
            # cubes project into the head volume above any student chair.
            # Flush ceiling fixtures replace only the existing top slab cells.
            for x in (left+1,left+4):
                for z in (151,154):b.set(x,low+3,z,'sea_lantern')
            # Colour-coded room header above a kept-open door at z156.
            b.fill(door,low+2,156,door+1,low+2,156,
                   ('light_blue_terracotta','cyan_terracotta','blue_terracotta')[floor])
        # Root explicitly authorized removing accidental landscape bench/tree
        # intrusions from this corridor while leaving trusses/piers at z160.
        b.fill(29,low,157,99,low+1,159,'air')
        for x in range(31,99,7):b.set(x,low+3,158,'sea_lantern')
    # Record inspection by reading actual baseline, instead of assuming it empty.
    assert any(existing.get((x,65,z),'air')!='air'
               for x in range(29,100) for z in range(157,160))
    return b

def verify(b):
    before=baseline(); merged=before.copy(); merged.update(b.blocks)
    assets=ROOT/'vendor/assets/minecraft/blockstates'
    missing=sorted({v.split('[')[0] for v in b.blocks.values()
                    if not (assets/(v.split('[')[0]+'.json')).exists()})
    assert not missing,missing
    assert all(29<=x<=99 and 64<=y<=76 and 150<=z<=159 for x,y,z in b.blocks)
    # No external facade or structural corridor piers change.
    assert not any(z in (149,160) for x,y,z in b.blocks)
    def passable(x,y,z):
        # The carpet surface raises feet 1/16 block, leaving standing headroom.
        return merged.get((x,y,z),'air')=='air' or merged.get((x,y,z),'air').endswith('_carpet')
    rooms=[]; removed_intrusions=[]
    for floor in range(3):
        low=65+floor*4
        # Entire three-block-wide gallery now gives two clear body blocks.
        assert all(passable(x,y,z) for x in range(29,100)
                   for z in range(157,160) for y in (low,low+1))
        for left in BAYS:
            door=left+1
            assert all(merged.get((x,y,156),'air')=='air'
                       for x in (door,door+1) for y in (low,low+1))
            # BFS from the public corridor to the front teaching aisle.
            start=(door,158); target=(door,151)
            seen={start};q=deque([start])
            while q:
                x,z=q.popleft()
                for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,nz=x+dx,z+dz
                    if left<=nx<=left+5 and 151<=nz<=159 and (nx,nz) not in seen:
                        if passable(nx,low,nz) and passable(nx,low+1,nz):
                            seen.add((nx,nz));q.append((nx,nz))
            assert target in seen,(floor,left,'No route to teacher aisle')
            chair_cells=[(left,153),(left,155),(left+3,153),(left+3,155),
                         (left+5,153),(left+5,155),(left+5,150)]
            assert all(merged.get((x,y,z),'air')=='air' for x,z in chair_cells
                       for y in (low+1,low+2)),(floor,left,'Chair headroom')
            rooms.append({'floor':floor+1,'bounds':[left,left+5,150,155],
                          'floor_y':low-1,'seats':6,'door_x':[door,door+1],
                          'two_block_route_to_teacher_aisle':'PASS'})
        n=sum(before.get((x,y,z),'air')!='air' for x in range(29,100)
              for z in range(157,160) for y in (low,low+1))
        removed_intrusions.append({'floor':floor+1,'body_cells_cleared':n})
    return {'classrooms':rooms,'corridor_clearance':'PASS',
            'removed_existing_corridor_intrusions':removed_intrusions,
            'valid_vanilla_materials':'PASS','external_facades_and_z160_piers':'PRESERVED',
            'palette_counts':dict(sorted(Counter(b.blocks.values()).items())),
            'in_game_validation':False}

if __name__=='__main__':
    b=build();result=verify(b)
    result.update({'status':'Interiors proposed, not surveyed room plans.',
                   'material_rationale':'White/grey tile, pale birch student furniture, darker spruce teacher furniture, broad green boards, restrained blue floor accents; flush sea lanterns keep low ceilings clear.',
                   'camera_suggestions':[
                       {'label':'classroom eye level','position':[32,66.6,155],'target':[33,66,150]},
                       {'label':'classroom reverse','position':[32,66.6,151],'target':[34,66,155]},
                       {'label':'corridor eye level','position':[32,66.6,158],'target':[88,66.6,158]},
                       {'label':'upper room','position':[53,74.6,155],'target':[54,74,150]}],
                   'limits':['Room partitions and furniture are interpreted for Minecraft, not exact real-school furniture placement.','Thirty compact six-seat rooms illustrate teaching interiors at metre grid; they do not claim real capacity.','Clearance is verified in merged voxel coordinates, not through an in-game session.']})
    (ROOT/'parts/detail_classrooms_notes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(b.save('parts/detail_classrooms.json')))
    print(json.dumps({'checks':'PASS','rooms':len(result['classrooms']),
                      'corridor_intrusions':result['removed_existing_corridor_intrusions']}))
