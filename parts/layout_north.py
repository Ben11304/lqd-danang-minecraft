"""North reconstruction from fresh registered satellite roof polygons.

Room use and heights remain inferred. The long roof is explicitly segmented;
only its upper large green segment and short adjoining green strip contain a
representative gym. The southeast rounded annex is not labelled as a pool.
"""
from pathlib import Path
import sys,json,math,collections
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder
BOTTOM='[type=bottom,waterlogged=false]'
WEST='[facing=west,half=bottom,shape=straight,waterlogged=false]'
EAST='[facing=east,half=bottom,shape=straight,waterlogged=false]'


def trace_masks():
    trace=json.loads((ROOT/'references/north_trace.json').read_text(encoding='utf-8'))
    result={}
    for name,spec in trace['polygons'].items():
        tmp=Builder(name);tmp.polygon(spec['world_vertices'],64,64,'smooth_stone')
        result[name]={(x,z) for x,y,z in tmp.blocks}
    return result


def boundary(mask):
    return {(x,z) for x,z in mask if any((x+dx,z+dz) not in mask for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])}


def shell(b,mask,wall_top,floor='smooth_stone',wall='smooth_sandstone'):
    edge=boundary(mask)
    for x,z in mask:b.set(x,64,z,floor)
    for x,z in edge:
        b.fill(x,65,z,x,wall_top,z,wall)
        if x%7==0 or z%8==0:b.fill(x,65,z,x,wall_top,z,'white_concrete')
        elif wall_top>=70:
            b.fill(x,67,z,x,69,z,'light_gray_stained_glass')
    return edge


def clear_door(b,x1,x2,z1,z2,y=65,height=3):
    b.fill(x1,y,z1,x2,y+height-1,z2,'air')


def build():
    b=Builder('north_registered_layout_v3');m=trace_masks()
    # Satellite brown playing surface, without invented football goals.
    field=m['field_playing_surface'];fe=boundary(field)
    for x,z in field:b.set(x,64,z,'coarse_dirt')
    for x,z in fe:b.set(x,64,z,'smooth_sandstone')
    # A thin representative training-court line; exact sport markings unverified.
    for x in (17,45):
        for z in range(31,91):
            if (x,z) in field:b.set(x,64,z,'white_concrete')
    for z in (31,61,90):
        for x in range(17,46):
            if (x,z) in field:b.set(x,64,z,'white_concrete')
    # White bench row just inside the long edge, as pale repeated objects appear
    # along the photographed sports rectangle; no surrounding landscape plane.
    for z in range(32,90,7):
        for x in (13,14):
            if (x,z) in field:b.set(x,65,z,'smooth_quartz_slab'+BOTTOM)

    names=[n for n in m if n.startswith('hall_')]
    hall=set().union(*(m[n] for n in names))
    # Shared floor uses the traced union; separate segment skins preserve the
    # five visible roof portions instead of inventing one uniform 80m gym.
    for n in names:
        floor='oak_planks' if n in ('hall_upper_green_main_roof','hall_green_divider_roof') else 'smooth_stone'
        for x,z in m[n]:b.set(x,64,z,floor)
    gym=m['hall_upper_green_main_roof']|m['hall_green_divider_roof']
    for x,z in boundary(hall):
        top=74 if (x,z) in gym else 71
        b.fill(x,65,z,x,top,z,'smooth_sandstone')
        if z%7==0 or x%8==0:b.fill(x,65,z,x,top,z,'quartz_block')
        else:
            b.fill(x,67,z,x,min(71,top),z,'light_gray_stained_glass')
            for y in (70,72,74):
                if y<=top:b.set(x,y,z,'white_concrete')
    # Partition only between roof segments, with generous central pass-throughs.
    for z in (18,55,69):
        xs=[x for x,zz in hall if zz==z]
        if xs:
            b.fill(min(xs),65,z,max(xs),70,z,'white_concrete')
            clear_door(b,66,70,z,z,height=4)
    # Ground entrances at both ends; connecting use remains unlabelled.
    clear_door(b,65,71,6,10,height=4)
    clear_door(b,66,71,84,88,height=4)
    # Public west entrance in the generic southern section.
    clear_door(b,53,56,73,76,height=3)
    # Mint lower interior wall trim and high horizontal white louver rhythms.
    for x,z in boundary(hall):
        if (x,z) in gym:
            b.set(x,65,z,'cyan_terracotta')
            b.set(x,66,z,'prismarine')
            b.set(x,69,z,'white_concrete')
    # Gym: the actual playable court fits only the upper ~30m by38m roof part.
    for x in (61,78):
        for z in range(22,50):
            if (x,z) in gym:b.set(x,64,z,'white_concrete')
    for z in (22,36,49):
        for x in range(61,79):
            if (x,z) in gym:b.set(x,64,z,'white_concrete')
    for x in range(65,75):
        for z in range(31,42):
            if (x,z) in gym and 4<=math.hypot(x-69.5,z-36)<=5:b.set(x,64,z,'white_concrete')
    # Supported side bleachers, correct backs west so seats look east to court.
    for x,top in [(55,68),(56,67),(57,66)]:
        for z in range(22,50):
            if (x,z) not in gym:continue
            if top>65:b.fill(x,65,z,x,top-1,z,'smooth_stone')
            material='polished_andesite_stairs' if z in (29,30,41,42) else 'birch_stairs'
            b.set(x,top,z,material+WEST)
    for z in range(22,50):
        if z not in (29,30,41,42) and (54,z) in gym:
            b.set(54,69,z,'iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]')
    # Low east team bench faces toward west/court.
    for z in list(range(25,31))+list(range(41,47)):
        if (81,z) in gym:b.set(81,65,z,'spruce_stairs'+EAST)
    # Overhead boards: no posts obstruct the centre circulation route.
    for z in (21,50):
        b.fill(67,70,z,72,73,z,'white_concrete')
        b.fill(68,71,z,71,72,z,'light_gray_concrete')
        b.fill(69,70,z+(1 if z==21 else -1),70,70,z+(1 if z==21 else -1),'orange_concrete')
        for x in (68,71):b.fill(x,74,z,x,75,z,'light_gray_concrete')
    # Side scoreboard has simple neutral graphics, not an invented school logo.
    b.fill(81,70,33,81,73,39,'black_concrete')
    for z in (34,35,37,38):b.set(81,72,z,'yellow_concrete')
    # Roof outlines and colour segmentation follow independently traced polygons.
    for n in names:
        if n=='hall_north_red_end_roof':
            material='red_terracotta';base=72;arched=False
        elif n=='hall_purple_mid_roof':
            material='purple_terracotta';base=73;arched=False
        elif n=='hall_lower_green_roof':
            material='smooth_stone';base=74;arched=False
        else:
            # Smooth stone is a light grey-green visual stand-in for the metal
            # sheet roof. It avoids an invented bright red classroom roof.
            material='smooth_stone';base=75;arched=True
        for x,z in m[n]:
            rise=max(0,4-int(abs(x-68.5)/3.5)) if arched else 0
            b.set(x,base+rise,z,material)
            if x%8==0:b.set(x,base+rise,z,'light_gray_concrete')
    # Steel-coloured ties and paired lights under the main gym roof.
    for z in (24,34,44,52):
        for x in range(54,83):
            if (x,z) in gym:b.set(x,74,z,'light_gray_concrete')
        for x in (62,75):
            if (x,z) in gym:b.set(x,73,z,'sea_lantern')
    # Generic lower spaces: representative benches, no assertion of auditorium.
    for z in (59,64,73,79):
        for x in (59,76):
            if (x,z) in hall:b.set(x,65,z,'oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]')
    for z in (12,61,78):b.set(68,70,z,'sea_lantern')
    # Continuous clear interior centreline connects all five roof sections.
    for x in range(67,71):
        for z in range(8,87):
            if (x,z) in hall:
                b.fill(x,65,z,x,66,z,'air')

    # NE dormitory tower, registered from the roof with high-rise parallax caveat.
    tower=m['ne_tower_roof'];te=boundary(tower)
    for floor in range(12):
        y=64+4*floor
        for x,z in tower:b.set(x,y,z,'smooth_stone')
    for x,z in te:
        for y in range(65,108):
            if y%4==0:continue
            b.set(x,y,z,'white_concrete')
            if (x in (125,126) or z in (33,34)):
                b.set(x,y,z,'cyan_concrete')
            elif y%4 in (1,2) and ((z%6 in (1,2)) or (x%6 in (1,2))):
                b.set(x,y,z,'light_gray_stained_glass')
    # Roof keeps the observed polygon instead of returning to old z4 footprint.
    for x,z in tower:b.set(x,109,z,'light_gray_concrete')
    # Small internal stairwell: floor cuts and same-sided turn-around landings.
    b.fill(117,65,40,120,107,41,'air')
    for floor in range(10):
        y=64+4*floor
        for step in range(4):
            b.fill(117+step,y+1+step,40,117+step,y+1+step,41,
                   'polished_andesite_stairs'+EAST)
    # South door with a two-block clear approach to the annex side.
    clear_door(b,127,131,44,48,height=3)
    # Representative interior circulation through open floor plates.
    for fy in range(64,105,4):
        for z in range(24,44):
            for x in (127,128):
                if (x,z) in tower:b.fill(x,fy+1,z,x,fy+2,z,'air')
        b.set(129,fy+3,34,'sea_lantern')

    # Rounded low annex: generic use; no invented pool or water volume.
    annex=m['ne_rounded_annex_roof'];shell(b,annex,71,'oak_planks')
    for x,z in annex:b.set(x,72,z,'terracotta')
    for x,z in boundary(annex):b.set(x,72,z,'red_terracotta')
    clear_door(b,130,134,47,51,height=3)
    clear_door(b,125,128,59,62,height=3)
    for z in (56,64,71):
        for x in (129,137):
            if (x,z) in annex:b.set(x,65,z,'birch_stairs'+(WEST if x<133 else EAST))
        if (133,z) in annex:b.set(133,71,z,'sea_lantern')
    # Tower/annex labels and exact contents are recorded only in notes.
    return b


def validate(b):
    m=trace_masks();allowed=set().union(*m.values())
    # Air at public entrances may extend 1-2m outside traced outlines but does
    # not create external geometry or remove other components in root assembly.
    solid=[(x,y,z,s) for (x,y,z),s in b.blocks.items() if s!='air']
    assert all((x,z) in allowed for x,y,z,s in solid),[(x,y,z,s) for x,y,z,s in solid if (x,z) not in allowed][:8]
    assert all(64<=y<=109 for x,y,z,s in solid)
    assert not any('water'==s.split('[')[0] for x,y,z,s in solid),'No evidence-based pool footprint was assigned.'
    for s in set(b.blocks.values()):
        assert (ROOT/'vendor/assets/minecraft/blockstates'/f'{s.split("[")[0]}.json').exists(),s
    # Geometry validation of uninterrupted hall aisle at normal body height.
    hall=set().union(*(mask for n,mask in m.items() if n.startswith('hall_')))
    for x in range(67,71):
        for z in range(8,87):
            if (x,z) in hall:
                for y in (65,66):assert b.blocks.get((x,y,z),'air')=='air'
    return {'blocks_including_explicit_air':len(b.blocks),'solid_blocks':len(solid),
            'palette_size':len(set(b.blocks.values())),'hall_body_clearance':True,
            'traced_masks':{n:len(mask) for n,mask in m.items()},
            'roof_trace_geometry_checked':True,'generic_annex_has_no_pool':True}


if __name__=='__main__':
    b=build();report=validate(b)
    print(json.dumps({'save':b.save('parts/layout_north.json'),'checks':report},ensure_ascii=False))
