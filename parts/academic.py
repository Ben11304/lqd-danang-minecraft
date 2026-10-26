"""Evidence-based east academic crescent and central connecting classroom wing.

The 1 m grid, three levels and room divisions are reconstruction choices;
photographs establish the cream walls, white piers, open inner galleries,
horizontal gray metalwork and flat roofs, not a surveyed room plan.
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voxel import Builder

CX, CZ = 76, 107
A0, A1 = -73, 30


def point(radius, angle):
    theta = math.radians(angle)
    return (round(CX + radius * math.cos(theta)), round(CZ + radius * math.sin(theta)))


def build():
    b = Builder('east_academic_and_connecting_wing')
    levels = (64, 68, 72)
    cream, white = 'smooth_sandstone', 'white_concrete'
    glass = 'light_gray_stained_glass'
    rail = 'iron_bars[east=true,north=true,south=true,waterlogged=false,west=true]'

    # Annular floors preserve the open planted courtyard and gallery voids.
    for floor in (*levels, 76):
        b.ring(CX, CZ, 62, 52, floor, floor, 'smooth_stone', A0, A1)
    for x in range(90, 139):
        for z in range(47, 140):
            dx, dz = x + .5 - CX, z + .5 - CZ
            r, a = math.hypot(dx, dz), math.degrees(math.atan2(dz, dx))
            if not A0 <= a <= A1:
                continue
            # 7-metre room and column rhythm measured along the mid-radius.
            along = (a - A0) * math.pi / 180 * 58
            bay = along % 7
            pier = bay < 1.15
            for floor in levels:
                for dy in (1, 2, 3):
                    y = floor + dy
                    if 60.8 <= r <= 62:
                        b.set(x, y, z, cream if pier or dy == 1 else glass)
                    if 55.5 <= r < 56.5:
                        # Classroom wall: generous window and door openings.
                        door = 4.8 < bay < 6.5 and dy <= 2
                        if not door:
                            b.set(x, y, z, cream if dy == 1 or pier else glass)
                    if 52 <= r < 53.1:
                        if pier:
                            b.set(x, y, z, 'quartz_block')
                        elif floor > 64 and dy == 1:
                            b.set(x, y, z, rail)
                        elif dy == 3:
                            # High strip of metal louvers; open gallery below.
                            b.set(x, y, z, rail)
                # Room partitions stop before the continuous inner gallery.
                if 56.5 <= r <= 60.8 and bay < .7:
                    b.fill(x, floor + 1, z, x, floor + 3, z, cream)
            for y in (68, 72, 76):
                if 60.8 <= r <= 62 or 52 <= r < 53.1:
                    b.set(x, y, z, white)
                if y in (68, 72) and 52 <= r < 53.1 and not pier:
                    # Only the exposed gallery fascia is a half-height edge.
                    # Its top stays flush with the interior floor; full-height
                    # piers continue through the edge at structural bays.
                    b.set(x, y, z, 'smooth_quartz_slab[type=top,waterlogged=false]')

    # Thin radial end walls; northern cap includes the inferred staircase.
    for angle in (A0, A1):
        p1, p2 = point(55.5, angle), point(62, angle)
        for floor in levels:
            for y in range(floor + 1, floor + 4):
                b.line(p1[0], y, p1[1], p2[0], y, p2[1], cream)
    b.ring(CX, CZ, 62.5, 51.5, 77, 77, 'light_gray_concrete', A0, A1)
    b.ring(CX, CZ, 62.5, 61.3, 78, 78, 'light_gray_concrete', A0, A1)
    b.ring(CX, CZ, 52.6, 51.5, 78, 78, 'light_gray_concrete', A0, A1)

    # Straight connecting wing: classrooms to north, continuous gallery south.
    for floor in (*levels, 76):
        b.fill(20, floor, 124, 117, floor, 137, 'smooth_stone')
    for floor in levels:
        for x in range(20, 118):
            bay = (x - 20) % 7
            pier = bay == 0 or x == 117
            for dy in (1, 2, 3):
                y = floor + dy
                b.set(x, y, 124, cream if pier or dy == 1 else glass)
                if not (bay in (5, 6) and dy in (1, 2)):
                    b.set(x, y, 133, cream if pier or dy == 1 else glass)
                if pier:
                    b.set(x, y, 137, 'quartz_block')
                elif (floor > 64 and dy == 1) or dy == 3:
                    b.set(x, y, 137, rail)
            if pier:
                b.fill(x, floor + 1, 125, x, floor + 3, 132, cream)
            if bay in (2, 3):
                # Representative desks only; room use and exact seating inferred.
                b.set(x, floor + 1, 127, 'oak_slab[type=top,waterlogged=false]')
                b.set(x, floor + 1, 130, 'oak_slab[type=top,waterlogged=false]')
        for z in range(124, 134):
            b.fill(20, floor + 1, z, 20, floor + 3, z, cream)
        for y in (floor,):
            b.fill(20, y, 124, 117, y, 124, white)
            b.fill(20, y, 137, 117, y, 137, white)
            if y in (68, 72):
                for x in range(21, 117):
                    if (x - 20) % 7:
                        b.set(x, y, 137, 'smooth_quartz_slab[type=top,waterlogged=false]')
    b.fill(20, 77, 124, 117, 77, 137, 'light_gray_concrete')
    b.fill(20, 78, 124, 117, 78, 124, 'light_gray_concrete')
    b.fill(20, 78, 137, 117, 78, 137, 'light_gray_concrete')

    # Northern end staircase, within the annular footprint. Small stair treads
    # are deliberately approximate; no unsupported circular stair tower.
    for floor in (64, 68):
        b.fill(98, floor + 1, 54, 101, floor + 4, 56, 'air')
        for step in range(4):
            b.fill(98 + step, floor + step + 1, 54, 98 + step, floor + step + 1, 56,
                   'stone_brick_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]')
        b.fill(102, floor + 4, 54, 104, floor + 4, 56, 'smooth_stone')

    # Accessible straight stair in one central bay. Floors have head openings.
    for floor in (64, 68):
        b.fill(50, floor + 1, 125, 52, floor + 4, 128, 'air')
        for step in range(4):
            b.fill(50, floor + step + 1, 125 + step, 52, floor + step + 1, 125 + step,
                   'stone_brick_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]')
        b.fill(50, floor + 4, 129, 52, floor + 4, 132, 'smooth_stone')
    # Open the staircase room onto the gallery at all levels.
    for floor in levels:
        b.fill(50, floor + 1, 133, 52, floor + 2, 133, 'air')

    # Approved narrow bridge connecting the straight wing to the inner arc.
    for floor in (*levels, 76):
        b.fill(118, floor, 128, 126, floor, 133, 'smooth_stone')
    for floor in levels:
        for dy in (1, 2, 3):
            for x in (119, 125):
                b.set(x, floor + dy, 128, 'quartz_block')
                b.set(x, floor + dy, 133, 'quartz_block')
        if floor > 64:
            b.fill(118, floor + 1, 128, 126, floor + 1, 128, rail)
            b.fill(118, floor + 1, 133, 126, floor + 1, 133, rail)
        # Punch both destination walls so circulation genuinely connects.
        b.fill(117, floor + 1, 129, 126, floor + 2, 132, 'air')
    b.fill(118, 77, 128, 126, 77, 133, 'light_gray_concrete')

    # The south arc continues into the root-owned longitudinal connection.
    for floor in levels:
        b.fill(127, floor + 1, 136, 132, floor + 2, 138, 'air')
    return b


if __name__ == '__main__':
    component = build()
    result = component.save('parts/academic.json')
    result['palette'] = sorted(set(component.blocks.values()))
    # Protect the courtyard and catch accidental solid ring/disc construction.
    assert all(not (math.hypot(x+.5-CX, z+.5-CZ) < 51 and 64 < y < 77 and z < 124)
               for (x, y, z), name in component.blocks.items() if name != 'air')
    assert min(y for x, y, z in component.blocks) == 64
    assert max(y for x, y, z in component.blocks) <= 78
    print(json.dumps(result, indent=2))
