"""Proposed library fit-out, not a survey of the school's real library."""
from collections import Counter, deque
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from voxel import Builder


def load_base():
    source = json.loads((ROOT / 'campus.json').read_text(encoding='utf-8'))
    return {(x, y, z): source['palette'][p] for x, y, z, p in source['blocks']}


def build():
    # Read current baseline before defining the patch; no baseline is mutated.
    base = load_base()
    assert all(base.get((x, 64, z), 'air') != 'air'
               for x in range(58, 90) for z in range(125, 133))
    b = Builder('detail_library_proposed_ground_floor')

    # Remove only partitions and old representative furniture within the
    # assigned interior. North facade z124, gallery wall z133 and piers remain.
    b.fill(58, 65, 125, 89, 67, 132, 'air')
    b.fill(58, 64, 125, 89, 64, 132, 'birch_planks')
    b.fill(58, 64, 131, 89, 64, 132, 'smooth_stone')

    # End screens define this fit-out without cutting across its clear spine.
    b.fill(58, 65, 125, 58, 67, 130, 'smooth_sandstone')
    b.fill(89, 65, 125, 89, 67, 130, 'smooth_sandstone')

    # Low shelves under the north glazing retain the upper daylight opening.
    for left, right in ((59, 62), (66, 70), (74, 78), (82, 86)):
        b.fill(left, 65, 125, right, 65, 125, 'bookshelf')
        b.fill(left, 66, 125, right, 66, 125,
               'birch_slab[type=bottom,waterlogged=false]')

    # Four short, two-tier bookcase fins. Their ends stop before the cross
    # aisle z129..130 and the protected 2-metre spine z131..132.
    for x in (64, 72, 80, 88):
        b.fill(x, 65, 126, x, 66, 128, 'bookshelf')
        b.fill(x, 67, 126, x, 67, 128,
               'birch_slab[type=bottom,waterlogged=false]')

    # Three readable shared study tables, with 4 chairs each. The narrow table
    # slabs are one metre above the floor, chairs have their backs away from
    # the table. Carpet is a proposed quiet-zone accent, away from the spine.
    for left in (66, 74, 82):
        b.fill(left, 65, 127, left + 2, 65, 127,
               'oak_slab[type=top,waterlogged=false]')
        for x in (left, left + 2):
            b.set(x, 65, 126,
                  'oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
            b.set(x, 65, 128,
                  'oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]')
        b.fill(left, 65, 129, left + 2, 65, 129, 'light_blue_carpet')

    # Reception and a standalone reading lectern; no inventory/book entities.
    b.fill(60, 65, 127, 62, 65, 127,
           'birch_slab[type=top,waterlogged=false]')
    b.set(60, 65, 126, 'lectern[facing=south,has_book=false,powered=false]')
    b.set(62, 65, 126,
          'oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
    b.fill(59, 65, 129, 62, 65, 130, 'light_blue_carpet')

    # Flush ceiling lights replace only the assigned local slab cells. No
    # hanging fixture reduces headroom and no upper-room furniture is changed.
    for x in (61, 68, 76, 84):
        for z in (127, 130):
            b.set(x, 68, z, 'sea_lantern')

    # Only the two specifically authorized openings modify the gallery wall.
    for left in (59, 85):
        b.fill(left, 65, 133, left + 1, 66, 133, 'air')
    # Guarantee body clearance after all furniture passes.
    b.fill(58, 65, 131, 89, 67, 132, 'air')
    return b


def verify_and_notes(patch):
    base = load_base()
    merged = dict(base)
    merged.update(patch.blocks)
    state = lambda x, y, z: merged.get((x, y, z), 'air')
    doors = {(x, y, 133) for x in (59, 60, 85, 86) for y in (65, 66)}
    ceiling_lights = {(x, 68, z) for x in (61, 68, 76, 84) for z in (127, 130)}
    for (x, y, z), block in patch.blocks.items():
        interior = 58 <= x <= 89 and 125 <= z <= 132 and 64 <= y <= 67
        assert interior or (x, y, z) in doors or (x, y, z) in ceiling_lights
        assert z != 124
        if z == 133:
            assert (x, y, z) in doors and block == 'air'
    # Strict reserved path: air for all three body blocks, not just collision
    # approximations. Routes to seats/shelves use the two-air-block predicate.
    spine = {(x, z) for x in range(58, 90) for z in (131, 132)}
    assert all(state(x, y, z) == 'air' for x, z in spine for y in (65, 66, 67))
    assert all(state(x, y, 133) == 'air' for x in (59, 60, 85, 86) for y in (65, 66))

    def walkable(x, z):
        return state(x, 65, z) == 'air' and state(x, 66, z) == 'air'
    queue, reached = deque([(59, 134)]), {(59, 134)}
    while queue:
        x, z = queue.popleft()
        for nx, nz in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
            if 58 <= nx <= 89 and 125 <= nz <= 134 and (nx,nz) not in reached and walkable(nx,nz):
                reached.add((nx,nz));queue.append((nx,nz))
    targets = spine | {(59,133),(60,133),(85,133),(86,133),
                      (63,126),(70,126),(78,126),(86,126),
                      (63,128),(70,128),(78,128),(86,128)}
    assert targets <= reached, sorted(targets-reached)
    # The north facade, piers in the gallery, all non-door gallery walls and
    # every floor above the authorized ceiling cells are unchanged by design.
    palette = sorted(set(patch.blocks.values()))
    for block in palette:
        name = block.split('[')[0]
        assert (ROOT / 'vendor/assets/minecraft/blockstates' / (name + '.json')).is_file(), name
    changed_old_solids = sum(base.get(coord, 'air') != 'air' and value == 'air'
                             for coord, value in patch.blocks.items())
    counts = Counter(patch.blocks.values())
    return {
        'component':'proposed_library_fit_out',
        'status':'Proposed interior, not a documented copy of the real school library.',
        'room_bounds_xyz':[[58,89],[64,67],[125,132]],
        'ceiling_light_y':68,
        'room_area_square_blocks':256,
        'design':{
            'bookshelves':'19 low window-side bookshelf blocks plus four 3m bookcase fins, two tiers high (24 bookshelf blocks).',
            'reading':'Three 3m reading tables with four chairs each; 12 reading seats total.',
            'reception':'3m birch counter, one chair, one empty lectern with no block-entity book content.',
            'materials':'Birch floor and shelf caps keep the palette light; oak table/chair wood supplies contrast; bookshelf textures add restrained color and light-blue carpet marks proposed quiet study areas.',
            'lighting':'Eight flush sea lanterns replace local ceiling cells and preserve full clear room height.'
        },
        'palette':palette,
        'block_counts':dict(sorted(counts.items())),
        'removed_existing_solid_cells':changed_old_solids,
        'circulation_checks':{
            'baseline_loaded':True,
            'reserved_spine':'x58..89,z131..132: all 64 floor positions have air at y65/66/67.',
            'designated_doorways':'x59..60 and85..86,z133 have air at y65/66.',
            'BFS_body_clearance':'Two air blocks at y65/66; carpets conservatively excluded from strict BFS.',
            'BFS_reachable_cells':len(reached),
            'checked_targets':len(targets),
            'result':'All spine, doorway and reading/shelf-side aisle targets reachable from gallery (59,134).',
            'source_facade_and_structure':'z124 untouched; z133 modified only at the 8 allowed doorway cells; no y69+ edits; gallery pier route untouched.',
            'material_names':'All palette block names exist in official vanilla1.20.4 blockstate assets.'
        },
        'cameras':[
            {'id':'library_wide','eye':[60,66.7,131],'target':[79,66.1,127],
             'purpose':'Overall proposed library zoning, bookshelf rhythm, wood palette and reading tables.'},
            {'id':'library_reading_close','eye':[75,66.65,130],'target':[75,66.0,127],
             'purpose':'Table/chair proportions, bookcase color and carpet detail.'},
            {'id':'library_entry','eye':[85.5,66.7,135],'target':[78,66.2,128],
             'purpose':'Clear 2m entrance and relationship to existing gallery.'}
        ],
        'limits':['Interior layout and room function are proposed and not established from source photos.',
                  'Furniture uses voxel representations; vanilla stairs do not provide a sitting interaction.',
                  'No game runtime validation; root will render merged close/mid views and export.']
    }


if __name__ == '__main__':
    component = build()
    notes = verify_and_notes(component)
    result = component.save('parts/detail_library.json')
    (ROOT / 'parts/detail_library_notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({**result,'checks':notes['circulation_checks']},indent=2))
