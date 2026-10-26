"""North facilities: observed material cues, provisional surveyed-free footprints.

The hall's internal subdivision, dormitory's four facades and pool position are
interpretations, not verified plans. See north_notes.json for provenance.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voxel import Builder


def build():
    b = Builder('north_facilities')
    # Northwest open sports ground. Paint is limited to the ground plane.
    b.fill(5,64,20,40,64,94,'coarse_dirt')
    b.fill(8,64,24,37,64,90,'terracotta')
    for x in (9,36): b.line(x,64,25,x,64,89,'white_concrete')
    for z in (25,57,89): b.line(9,64,z,36,64,z,'white_concrete')
    # Court center circle, drawn into the ground to avoid raised obstacles.
    for x in range(18,28):
        for z in range(52,63):
            if 4.0 <= ((x-22.5)**2+(z-57)**2)**.5 <= 5.0:
                b.set(x,64,z,'white_concrete')
    # Football goal outlines. Unknown exact sports use of satellite rectangle.
    for z in (25,89):
        for x in (19,26): b.fill(x,65,z,x,68,z,'quartz_block')
        b.fill(19,68,z,26,68,z,'quartz_block')

    # Main north hall: cream plinth, white structural bays, pale louver panels.
    b.fill(46,64,12,79,64,84,'stone_bricks')
    b.fill(47,65,13,78,65,83,'oak_planks')
    for x in (46,79):
        b.fill(x,65,12,x,76,84,'smooth_sandstone')
        for z in range(17,82,7):
            b.fill(x,67,z,x,72,z+3,'light_gray_stained_glass')
            # White louver bars occur prominently in sports interior photos.
            for y in (70,72,74): b.fill(x,y,z,x,y,z+3,'white_concrete')
        for z in range(12,85,8): b.fill(x,65,z,x,77,z,'quartz_block')
    for z in (12,84): b.fill(46,65,z,79,76,z,'smooth_sandstone')
    # Large public entrance on south end and a north exit.
    for z in (12,84):
        b.fill(58,65,z,67,69,z,'light_gray_stained_glass')
        b.fill(61,65,z,64,68,z,'air')
        b.fill(55,70,z,70,71,z,'white_concrete')
    # Hall interior: gym shares an interpreted block with auditorium.
    b.fill(47,66,33,78,73,33,'white_concrete')
    b.fill(61,66,33,64,69,33,'air')
    # Pale aqua lower wall trim and white ventilation are evidence based.
    for x in (47,78):
        b.fill(x,66,35,x,68,82,'prismarine')
        for z in range(38,81,7):
            for y in (70,72,74): b.fill(x,y,z,x,y,z+3,'white_concrete')
    # Court lines set into the playable floor, not above it.
    for x in (52,73): b.line(x,65,40,x,65,78,'white_concrete')
    for z in (40,59,78): b.line(52,65,z,73,65,z,'white_concrete')
    for x in range(58,68):
        for z in range(54,65):
            d=((x-62.5)**2+(z-59)**2)**.5
            if 4<=d<=5: b.set(x,65,z,'white_concrete')
    for z in (40,78):
        b.fill(62,66,z,63,70,z,'quartz_block')
        b.fill(60,70,z,65,73,z,'white_concrete')
        b.fill(62,70,z+(1 if z==40 else -1),63,70,z+(1 if z==40 else -1),'orange_concrete')
    # Bleachers along western wall, railing at the raised rear aisle.
    for step in range(4):
        x=48+step
        b.fill(x,66+3-step,39,x,66+3-step,80,'smooth_stone')
    b.fill(48,70,38,48,70,81,'iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]')
    # Representative small auditorium at north end, layout entirely inferred.
    b.fill(49,66,15,76,66,18,'dark_oak_planks')
    b.fill(50,67,14,75,71,14,'red_terracotta')
    b.fill(52,69,14,73,71,14,'white_concrete')
    for z in (21,24,27,30):
        for x in range(51,75,3):
            if x not in (60,63):
                b.set(x,66,z,'oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
    # Three roof sections visible from satellite are simplified shallow roofs.
    # Avoid an invented red tile roof; light grey dominant metal roof.
    for x in range(46,80):
        y=77 + max(0, 3-abs(x-62)//5)
        b.fill(x,y,12,x,y,84,'light_gray_concrete')
        for z in (12,33,60,84): b.set(x,y+1,z,'gray_concrete')
    # Exposed steel roof ties, visible to a player inside the sports hall.
    for z in (39,50,61,72,82):
        b.line(47,76,z,62,79,z,'light_gray_concrete')
        b.line(62,79,z,78,76,z,'light_gray_concrete')
        b.line(47,76,z,78,76,z,'light_gray_concrete')
    for z in (23,43,63,79): b.set(62,76,z,'sea_lantern')

    # Dormitory: eleven 4-block storeys, with a provisional repeated facade.
    # Photo behind pool shows white walls, teal strips and regular dark windows.
    b.fill(111,64,4,136,64,23,'stone_bricks')
    for floor in range(11):
        y=65+4*floor
        b.fill(111,y,4,136,y,23,'smooth_stone')
        for z in (4,23):
            b.fill(111,y+1,z,136,y+3,z,'white_concrete')
            for x in (114,119,127,132):
                b.fill(x,y+1,z,x+1,y+2,z,'light_gray_stained_glass')
            b.fill(123,y+1,z,124,y+3,z,'cyan_concrete')
        for x in (111,136):
            b.fill(x,y+1,4,x,y+3,23,'white_concrete')
            for z in (7,12,17): b.fill(x,y+1,z,x,y+2,z+1,'light_gray_stained_glass')
            b.fill(x,y+1,20,x,y+3,20,'cyan_concrete')
        # Compact side stair: walkable interpretation, not a known floor plan.
        if floor < 10:
            for step in range(4):
                b.fill(112+step,y+1+step,6,112+step,y+1+step,8,'smooth_stone')
                b.fill(112+step,y+2+step,6,112+step,y+3+step,8,'air')
    # Re-cap above stair clearance so the stated maximum roof remains y109.
    b.fill(111,109,4,136,109,23,'light_gray_concrete')
    b.fill(120,66,23,126,68,23,'light_gray_stained_glass')
    b.fill(122,66,23,124,68,23,'air')
    # Small flat entrance canopy within the assigned footprint.
    b.fill(119,70,22,128,70,23,'white_concrete')

    # Covered pool, compressed to avoid the east academic arc. Location inferred.
    b.fill(129,64,28,145,64,48,'bricks')
    b.fill(131,63,30,143,63,46,'light_blue_concrete')
    b.fill(131,64,30,143,64,46,'water[level=0]')
    for z in range(30,47):
        for x in (134,138,142):
            # Ceramic lane markers at bottom; water surface remains continuous.
            b.set(x,63,z,'blue_concrete')
    for x in (129,145):
        for z in (28,38,48):
            b.fill(x,65,z,x,70,z,'quartz_block')
    for x in range(129,146):
        y=72-abs(x-137)//4
        b.fill(x,y,28,x,y,48,'light_gray_concrete')
        for z in (28,38,48): b.set(x,y-1,z,'gray_concrete')
    # Narrow seating / equipment ledge on east wall as visible in pool photo.
    b.fill(145,65,31,145,65,45,'smooth_stone')
    return b


if __name__ == '__main__':
    import json
    b=build()
    # All components remain in their assigned envelopes.
    envelopes=[(5,40,20,94),(46,79,12,84),(111,136,4,23),(129,145,28,48)]
    assert all(any(x1<=x<=x2 and z1<=z<=z2 for x1,x2,z1,z2 in envelopes)
               for x,y,z in b.blocks)
    assert max(y for x,y,z in b.blocks)<=109
    print(json.dumps(b.save('parts/north.json')))
