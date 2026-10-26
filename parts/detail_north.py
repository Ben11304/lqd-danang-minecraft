"""Vanilla furnishing patch; all furniture and exact room arrangements inferred."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder

EAST='[facing=east,half=bottom,shape=straight,waterlogged=false]'
NORTH='[facing=north,half=bottom,shape=straight,waterlogged=false]'
WEST='[facing=west,half=bottom,shape=straight,waterlogged=false]'
SOUTH='[facing=south,half=bottom,shape=straight,waterlogged=false]'
TOP='[type=top,waterlogged=false]'
LOW='[type=bottom,waterlogged=false]'
RAIL='[east=false,north=true,south=true,west=false,waterlogged=false]'


def build():
    b=Builder('detail_north')
    # Upgrade the existing bleacher tiers, without changing their footprint.
    # Aisles at three intervals ascend from court level; rear rail stays behind.
    for x in range(48,52):
        top=69-(x-48)
        if top>66:b.fill(x,66,39,x,top-1,80,'smooth_stone')
        for z in range(39,81):
            if x==48:
                b.set(x,top,z,'smooth_stone')
            else:
                stair='polished_andesite_stairs' if z in (48,49,62,63,76,77) else 'birch_stairs'
                b.set(x,top,z,stair+WEST)
        # White riser edge reads as tier trim beneath the light wood seat.
        if x<51:b.fill(x,top-1,39,x,top-1,80,'smooth_sandstone')
    # Rear rail: leave gaps aligned with the clear ascending aisles.
    for z in range(38,82):
        b.set(48,70,z,'air' if z in (48,49,62,63,76,77) else 'iron_bars'+RAIL)
    # Short edge rails at the ends of the spectator terrace.
    for z in (38,81):
        for x in (49,50,51):
            b.set(x,70-(x-48),z,
                  'iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]')

    # Suspended basketball equipment: remove floor-standing central obstacles.
    for z in (40,78):
        b.fill(62,66,z,63,69,z,'air')
        for x in (61,64):
            b.fill(x,74,z,x,75,z,'iron_bars'+RAIL)
            b.fill(x,75,min(z,39 if z==40 else 82),x,75,max(z,39 if z==40 else 82),'light_gray_concrete')
        # Backboard border, small aim square and hoop already exist in v1.
        b.fill(60,70,z,65,73,z,'white_concrete')
        b.fill(61,71,z,64,72,z,'light_gray_concrete')
        b.fill(62,71,z,63,71,z,'white_concrete')
        hoop_z=z+(1 if z==40 else -1)
        b.fill(62,70,hoop_z,63,70,hoop_z,'orange_concrete')

    # Team benches and a compact scorer desk on east side, outside the aisle.
    for z in list(range(43,51))+list(range(68,76)):
        b.set(76,66,z,'spruce_stairs'+EAST)
    for z in (44,49,69,74):b.set(77,66,z,'polished_andesite')
    for z in range(36,40):
        b.set(75,67,z,'smooth_quartz_slab'+TOP)
    for z in (36,39):b.set(75,66,z,'polished_andesite')
    for z in (36,38):b.set(77,66,z,'spruce_stairs'+EAST)
    # Equipment storage is represented with cupboards, not block entities.
    b.fill(76,66,79,77,67,81,'spruce_planks')
    for z in (79,81):
        b.set(75,67,z,'spruce_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]')

    # East-wall scoreboard: two bright digit-like modules on charcoal backing.
    b.fill(77,70,53,77,75,64,'light_gray_concrete')
    b.fill(77,71,54,77,74,63,'black_concrete')
    for z0 in (55,60):
        for dy,dz in [(0,0),(0,1),(0,2),(1,2),(2,2),(3,0),(3,1),(3,2)]:
            b.set(77,71+dy,z0+dz,'yellow_concrete')
    b.set(77,74,58,'red_concrete')
    b.set(77,72,58,'white_concrete')
    # Mint white wall band from the gym references, with darker base trim.
    for x in (47,78):
        for z in range(35,83):
            b.set(x,66,z,'cyan_terracotta')
            b.set(x,69,z,'white_concrete')
    # Suspended fixture pairs and short vertical hangers under existing trusses.
    # Nothing touches y77+ roofs or changes the visible exterior silhouette.
    for z in (43,54,65,76):
        for x in (55,70):
            b.set(x,75,z,'polished_andesite')
            b.set(x,74,z,'sea_lantern')
            b.set(x,73,z,'smooth_quartz_slab'+LOW)
    # Additional cross ties; do not overwrite original high roof geometry.
    for z in (44,55,66,77):
        b.fill(49,75,z,76,75,z,'light_gray_concrete')

    # Representative auditorium: warm wood seats, central and side aisles.
    # Remove the sparse v1 placeholders before creating consistent seat groups.
    for z in (21,24,27,30):
        for x in range(51,75,3):
            if x not in (60,63):b.set(x,66,z,'air')
    for z in (21,24,27,30):
        for x in (50,51,53,54,56,57,68,69,71,72,74,75):
            b.set(x,66,z,'birch_stairs'+SOUTH)
        # End chair arms stay below the sitting surface's visual top.
        for x in (49,58,67,76):b.set(x,66,z,'dark_oak_slab'+LOW)
    # Narrow red carpet aisle: no raised desks or seating on the centerline.
    b.fill(61,66,19,64,66,32,'red_carpet')
    # Break in the interpreted stage preserves the north emergency exit.
    b.fill(61,66,13,64,68,18,'air')
    b.fill(61,65,13,64,65,18,'oak_planks')
    b.fill(61,66,13,64,66,18,'red_carpet')
    # Stage details on either side of the retained central passage.
    b.fill(49,67,15,59,67,15,'dark_oak_slab'+LOW)
    b.fill(66,67,15,76,67,15,'dark_oak_slab'+LOW)
    b.set(57,67,17,'lectern[facing=south,has_book=false,powered=false]')
    for x in range(67,74):b.set(x,68,17,'smooth_quartz_slab'+TOP)
    for x in (67,73):b.set(x,67,17,'dark_oak_planks')
    for x in (68,70,72):b.set(x,67,16,'birch_stairs'+NORTH)
    # Projection screen, curtain side panels and two speaker columns.
    b.fill(51,69,14,59,72,14,'white_concrete')
    for x in (50,60,66,75):b.fill(x,67,14,x,72,14,'red_terracotta')
    for x in (49,76):b.fill(x,67,16,x,70,16,'black_concrete')
    # Acoustic ribs and low dark timber dado visually match the warm auditorium.
    for x in (47,78):
        b.fill(x,66,15,x,67,32,'dark_oak_planks')
        for z in (17,22,27,31):b.fill(x,68,z,x,71,z,'spruce_planks')
    # A small rear waiting bench lies outside the central circulation spine.
    for x in range(50,59):b.set(x,66,32,'spruce_stairs'+SOUTH)
    for x in range(68,76):b.set(x,66,32,'spruce_stairs'+SOUTH)
    # Floating ceiling ribs and recessed lantern modules, below existing roof.
    for z in (18,24,30):
        b.fill(49,74,z,76,74,z,'white_concrete')
        for x in (53,58,67,72):b.set(x,74,z,'sea_lantern')
    # Interior bulletin panels: no arbitrary text entities or logos.
    for x in (48,77):
        b.fill(x,68,28,x,70,30,'brown_terracotta')
        b.set(x,69,29,'white_concrete')
    # South facade door surround leaves the actual opening untouched.
    for x in (59,60,65,66):b.fill(x,66,84,x,69,84,'quartz_block')
    b.fill(59,70,84,66,70,84,'cyan_terracotta')
    b.set(60,69,84,'sea_lantern');b.set(65,69,84,'sea_lantern')
    # Required circulation is explicitly cleared last; carpet is confined to
    # auditorium and is removed from the mandated clear-volume assertions.
    b.fill(66,66,35,69,67,82,'air')
    b.fill(61,66,78,64,67,83,'air')
    # No exterior assignment at z85, and the actual z84 opening is unchanged.
    return b


def validate(b):
    data=json.loads((ROOT/'campus.json').read_text(encoding='utf-8'))
    baseline={(x,y,z):data['palette'][i] for x,y,z,i in data['blocks']}
    merged=dict(baseline)
    for p,v in b.blocks.items():
        if v=='air':merged.pop(p,None)
        else:merged[p]=v
    assert all(47<=x<=78 and 13<=z<=84 and 65<=y<=76 for x,y,z in b.blocks)
    assert all(z<84 or x not in range(61,65) or y>68 for x,y,z in b.blocks)
    for x in range(66,70):
        for z in range(35,83):
            for y in (66,67):assert (x,y,z) not in merged,(x,y,z)
    for x in range(61,65):
        for z in range(78,86):
            for y in (66,67):assert (x,y,z) not in merged,(x,y,z)
    # Roof and exterior structural piers remain identical to baseline.
    assert all(merged.get(p)==v for p,v in baseline.items()
               if 46<=p[0]<=79 and 12<=p[2]<=84 and p[1]>=77)
    for state in set(b.blocks.values()):
        assert (ROOT/'vendor/assets/minecraft/blockstates'/f'{state.split("[")[0]}.json').exists(),state
    return {'patch_entries':len(b.blocks),'explicit_air':sum(v=='air' for v in b.blocks.values()),
            'valid_palette':True,'body_clearance':'x66..69,z35..82 and x61..64,z78..85,y66..67 passed',
            'roof_unchanged':True,'palette':sorted(set(b.blocks.values()))}


if __name__=='__main__':
    b=build();report=validate(b)
    print(json.dumps({'save':b.save('parts/detail_north.json'),'checks':report},ensure_ascii=False))
