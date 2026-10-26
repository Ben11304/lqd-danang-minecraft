"""Proposed science/computer rooms and corridor fittings inside the v1 shell."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from voxel import Builder,ROOT

def slab(wood='birch'):return f'{wood}_slab[type=top,waterlogged=false]'
def chair(wood='birch',facing='south'):return f'{wood}_stairs[facing={facing},half=bottom,shape=straight,waterlogged=false]'
def build():
    b=Builder('specialist_rooms_detail_v2')
    # Science room: combine existing rooms, preserve the two exterior walls.
    b.fill(23,65,125,47,67,132,'air')
    b.fill(23,64,125,47,64,132,'polished_diorite')
    b.fill(23,65,125,23,67,132,'white_concrete')
    b.fill(47,65,125,47,67,132,'white_concrete')
    b.fill(23,65,133,47,67,133,'white_concrete')
    for x in (24,44):b.fill(x,65,133,x+1,66,133,'air')
    # Safety-colored backsplash, framed teaching board and supply shelves.
    b.fill(23,65,126,23,67,130,'quartz_block')
    b.fill(23,66,127,23,67,130,'green_concrete')
    for x1,x2 in [(26,30),(38,42)]:
        for z in (127,130):
            b.fill(x1,65,z,x2,65,z,slab('quartz'))
            for x in (x1,x2):b.set(x,65,z,'smooth_quartz')
            b.set(x1+2,65,z,'water_cauldron[level=2]')
            # Low polished work surfaces and stools, leaving a wide center aisle.
            for x in (x1+1,x1+3):b.set(x,65,z+1,chair())
    b.fill(46,65,125,46,66,129,'bookshelf')
    for x in (27,39):
        b.fill(x,66,125,x+2,66,125,'light_blue_concrete')
        b.set(x+1,67,125,'sea_lantern')
    for x in (26,32,39,45):
        for z in (126,130):b.set(x,68,z,'sea_lantern')

    # Computer lab on third floor: no overlap with the library ceiling below.
    floor=72
    b.fill(58,floor+1,125,89,floor+3,132,'air')
    b.fill(58,floor,125,89,floor,132,'smooth_stone')
    b.fill(58,floor+1,125,58,floor+3,132,'white_concrete')
    b.fill(89,floor+1,125,89,floor+3,132,'white_concrete')
    b.fill(58,floor+1,133,89,floor+3,133,'white_concrete')
    for x in (59,88):b.fill(x,floor+1,133,x+1,floor+2,133,'air')
    monitors=[61,64,67,72,75,78,83,86]
    for z in (126,130):
        for x1,x2 in [(61,67),(72,78),(83,86)]:
            b.fill(x1,floor+1,z,x2,floor+1,z,slab())
        for x in monitors:
            # Full blocks retain their screen silhouette in Java and Bedrock;
            # isolated pane arms are recalculated to a thin post on Bedrock.
            b.set(x,floor+2,z,'black_concrete')
            b.set(x,floor+1,z+1,chair('spruce'))
    # Screen wall, network/storage texture and restrained wall accents.
    b.fill(58,floor+1,126,58,floor+3,130,'quartz_block')
    b.fill(58,floor+2,127,58,floor+3,129,'black_concrete')
    for z in (125,131):
        b.set(89,floor+1,z,'gray_concrete');b.set(89,floor+2,z,'chiseled_stone_bricks')
    for x in (63,73,84):
        for z in (126,130):b.set(x,76,z,'sea_lantern')
    for x in range(61,87):b.set(x,75,125,'light_blue_concrete')

    # Corridor seating never occupies the two-block circulation strip z134..135.
    for floor in (64,68,72):
        for x in range(72,78):b.set(x,floor+1,136,chair('oak','south'))
        for x in (70,79):b.set(x,floor+1,136,'potted_fern')
        for x in (35,63,91,111):b.set(x,floor+4,135,'sea_lantern')
    return b

if __name__=='__main__':
    b=build();print(json.dumps(b.save('parts/detail_specialist.json')))
    (ROOT/'parts/detail_specialist_notes.json').write_text(json.dumps({
      'status':'Proposed interiors inside existing building; not verified room functions',
      'science':{'bounds':[23,47,125,132],'floor':64,'workstations':4,'sinks':4,'doors':[[24,133],[44,133]]},
      'computer':{'bounds':[58,89,125,132],'floor':72,'stations':16,'doors':[[59,133],[88,133]]},
      'circulation':'Science center aisle x31..37 and z131..132; computer center aisle z128..129 plus x59..60 and88; gallery z134..135',
      'cameras':{'science':{'eye':[33.5,66.62,131.5],'target':[25,66.4,126]},'computer':{'eye':[60.5,74.62,129],'target':[79,74.3,126.5]}}
    },ensure_ascii=False,indent=2),encoding='utf-8')
