"""Satellite-traced academic roofs, open junctions and representative interiors.

Roof XY traces are observations; floor count, walls/rooms and furniture are
provisional interpretations. No v1 footprint or detail patch is reused.
"""
from collections import Counter, deque
from pathlib import Path
import json
import math
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder

# All points refer to the saved NORTH Google Maps frame. The south frame was
# independently registered at +354px vertically (the initial274 was wrong).
PIXELS={
 'east_band':[(650,356),(681,365),(710,379),(738,397),(761,418),(781,443),
              (798,471),(811,499),(823,526),(824,546),(824,570),(822,594),
              (816,617),(807,639),(803,647),(744,643),(747,634),(752,620),
              (757,602),(760,584),(762,566),(762,545),(756,523),(748,502),
              (738,481),(722,460),(704,445),(682,432),(652,421)],
 'upper_bridge':[(428,554),(487,550),(502,547),(560,542),(849,524),
                 (852,567),(655,582),(565,588),(433,596)],
 'rounded_junction':[(579,542),(582,532),(592,523),(608,519),(625,518),
                     (639,525),(647,537),(651,550),(653,569),(649,586),
                     (636,597),(621,601),(603,599),(588,588),(580,574),(576,558)],
 'north_south_spine':[(613,590),(634,589),(641,651),(622,654)]}
INNER_PIXELS=[(652,421),(682,432),(704,445),(722,460),(738,481),(748,502),
              (756,523),(762,545),(762,566),(760,584),(757,602),(752,620),
              (747,634),(744,643)]
OUTER_PIXELS=PIXELS['east_band'][:15]


def frame():
    return json.loads((ROOT/'references/georeference.json').read_text(encoding='utf-8'))


def world(point):
    g=frame();a,b=g['x_axis_pixel_per_m'];c,d=g['z_axis_pixel_per_m']
    u,v=point[0]-g['north_control_origin_pixel'][0],point[1]-g['north_control_origin_pixel'][1]
    det=a*d-b*c
    return ((d*u-c*v)/det,(-b*u+a*v)/det)


def trace():
    result={'component':'academic_layout_v3','source':'Google Maps live satellite screenshot, retrieved2026-10-26',
            'pixel_frame':'references/satellite_north.png','georeference':frame(),
            'registration_check':{'south_to_north_y_offset':354,'mean_abs_RGB_error_best':5.7403,
               'initial_offset274_error':53.9554,'method':'RGB overlap comparison x420..850; northcrop dy..650 versus south0..650-dy'},
            'uncertainty_m':2.5,'polygons':{},
            'limits':['These are roof edges, not surveyed wall/foundation footprints.',
                      'Trees and shadows obscure several west end and junction edges.',
                      'The lower west-east wing and solid oval are separately traced by the south agent.',
                      'Three floors, rooms and the junction circulation layout are interpretations, not inferred from roof pixels alone.']}
    for name,points in PIXELS.items():
        pts=[world(p) for p in points]
        result['polygons'][name]={'original_pixels':[list(p) for p in points],
            'world_xz':[[round(x,4),round(z,4)] for x,z in pts],
            'world_bounds_xz':[[round(min(p[i] for p in pts),3),round(max(p[i] for p in pts),3)] for i in (0,1)]}
    result['arc_edges']={'inner_world_xz':[world(p) for p in INNER_PIXELS],
                          'outer_world_xz':[world(p) for p in OUTER_PIXELS],
                          'construction':'Follow traced noncircular polygon, not a fixed ideal ring.'}
    return result


def write_trace():
    data=trace();(ROOT/'references/academic_trace.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    return data


def mask(points):
    b=Builder('mask');b.polygon(points,64,64,'smooth_stone')
    return {(x,z) for x,y,z in b.blocks}


def distance_path(point,path):
    best=(float('inf'),0)
    walked=0
    for a,b in zip(path,path[1:]):
        vx,vz=b[0]-a[0],b[1]-a[1];length=math.hypot(vx,vz)
        t=max(0,min(1,((point[0]-a[0])*vx+(point[1]-a[1])*vz)/(length*length)))
        distance=math.hypot(point[0]-a[0]-t*vx,point[1]-a[1]-t*vz)
        if distance<best[0]:best=(distance,walked+t*length)
        walked+=length
    return best


def build():
    t=trace();polys=t['polygons'];m={name:mask(value['world_xz']) for name,value in polys.items()}
    arc,bridge,node,spine=[m[n] for n in ('east_band','upper_bridge','rounded_junction','north_south_spine')]
    roof=arc|bridge|node|spine
    b=Builder('layout_academic_v3_traced')
    cream,white='smooth_sandstone','white_concrete'
    rail='iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]'
    glass='light_gray_stained_glass'
    boundary={p for p in roof if any((p[0]+dx,p[1]+dz) not in roof for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)))}
    for x,z in roof:
        for y in (64,68,72,76):b.set(x,y,z,'smooth_stone')
        b.set(x,77,z,'light_gray_concrete')
        if (x,z) in boundary:b.set(x,78,z,'smooth_quartz_slab[type=bottom,waterlogged=false]')

    inner=t['arc_edges']['inner_world_xz'];outer=t['arc_edges']['outer_world_xz']
    def open_ground(x,z):
        return ((x,z) in node or (108<=x<=135 and 117<=z<=135)
                or z>=146 or (82<=x<=89 and 80<=z<=89))
    # The curved band follows its real traced width; outer classrooms use a
    # continuous inner gallery. Open junctions are handled separately below.
    for x,z in arc:
        di,s=distance_path((x+.5,z+.5),inner)
        do,_=distance_path((x+.5,z+.5),outer)
        bay=s%7.5;column=bay<1.1
        for floor in (64,68,72):
            low=floor+1;ground_open=(floor==64 and open_ground(x,z))
            if ground_open:
                if di<1.05 and column:b.fill(x,low,z,x,low+2,z,'quartz_block')
                continue
            if do<1.05:
                for dy in (0,1,2):b.set(x,low+dy,z,white if column else (cream if dy==0 else glass))
            if 3.6<=di<4.6:
                door=4.5<bay<6.7
                for dy in (0,1,2):
                    if not(door and dy<2):b.set(x,low+dy,z,cream if column or dy==0 else glass)
            if di<1.05:
                if column:b.fill(x,low,z,x,low+2,z,'quartz_block')
                elif floor>64:
                    b.set(x,low,z,cream);b.set(x,low+1,z,rail)
            if di>4.6 and do>1 and bay<.65:
                b.fill(x,low,z,x,low+2,z,cream)

    # Straight bridge roof has a library/classroom side and a generous public
    # south gallery. Leave the central rotunda and eastern junction open below.
    by_x={x:[z for xx,z in bridge if xx==x] for x,z in bridge}
    for x,z in bridge:
        north=min(by_x[x]);south=max(by_x[x]);column=(x-20)%7==0
        for floor in (64,68,72):
            low=floor+1
            is_junction=(x,z) in node or (108<=x<=135)
            if floor==64 and is_junction:continue
            if z==north:
                for dy in (0,1,2):b.set(x,low+dy,z,white if column else (cream if dy==0 else glass))
            if z==south:
                if column:b.fill(x,low,z,x,low+2,z,'quartz_block')
                elif floor>64:
                    b.set(x,low,z,cream);b.set(x,low+1,z,rail)
            if z==128 and (x,z) not in node:
                bay=(x-20)%7
                for dy in (0,1,2):
                    if not (bay in (2,3) and dy<2):b.set(x,low+dy,z,cream if dy==0 or column else glass)
            if column and north<z<128 and 56<=x<108 and (x,z) not in node:
                b.fill(x,low,z,x,low+2,z,cream)
    # End cap west of the representative rooms, away from public east-west flow.
    for floor in (64,68,72):
        for z in range(121,129):
            if (19,z) in bridge:b.fill(19,floor+1,z,19,floor+3,z,cream)

    # Broad rounded junction: air through its full depth at ground level,
    # fewer perimeter columns, no radial classroom partitions or centre lawn.
    for x,z in node:
        b.fill(x,65,z,x,67,z,'air')
        if (x,z) in boundary:
            for floor in (68,72):
                b.set(x,floor+1,z,cream);b.set(x,floor+2,z,rail)
    piers=[(64,116),(71,115),(77,118),(79,126),(77,133),(71,136),(62,132),(60,125)]
    for x,z in piers:
        if (x,z) in roof:b.fill(x,65,z,x,75,z,'quartz_block')
    # Open covered north/south spine, with top-half slabs and selected columns.
    for x,z in spine:
        if (x,z) in node:continue
        b.fill(x,65,z,x,67,z,'air')
        if (x,z) in boundary:
            if z%6==0:b.fill(x,65,z,x,75,z,'quartz_block')
            for floor in (68,72):
                b.set(x,floor+1,z,cream);b.set(x,floor+2,z,rail)
    # Small representative stair fits inside the observed junction roof.
    for floor in (64,68):
        b.fill(62,floor+1,123,65,floor+4,125,'air')
        for step in range(4):
            b.fill(62+step,floor+step+1,123,62+step,floor+step+1,125,
                   'stone_brick_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]')
        b.fill(66,floor+4,123,68,floor+4,125,'smooth_stone')

    # A representative library fits wholly inside the newly traced west wing.
    library=(21,55,121,127)
    for floor in (64,72):
        for x in range(21,56):
            for z in range(121,128):
                if (x,z) not in bridge:continue
                b.fill(x,floor+1,z,x,floor+3,z,'air')
                b.set(x,floor,z,'birch_planks')
        # These are new circulation doors, not blind copies of old v2 walls.
        for x1 in (22,53):b.fill(x1,floor+1,128,x1+1,floor+2,128,'air')
        for x in (25,33,41,49):b.set(x,floor+4,124,'sea_lantern')
    for left,right in ((22,26),(30,34),(38,42),(46,50)):
        b.fill(left,65,121,right,65,121,'bookshelf')
        b.fill(left,66,121,right,66,121,'birch_slab[type=bottom,waterlogged=false]')
    for x in (28,36,44,52):
        b.fill(x,65,122,x,66,125,'bookshelf')
        b.fill(x,67,122,x,67,125,'birch_slab[type=bottom,waterlogged=false]')
    for x in (30,38,46):
        b.fill(x,65,124,x+2,65,124,'oak_slab[type=top,waterlogged=false]')
        for xx in (x,x+2):
            b.set(xx,65,123,'oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
            b.set(xx,65,125,'oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]')
    b.fill(23,65,124,25,65,124,'birch_slab[type=top,waterlogged=false]')
    b.set(23,65,123,'lectern[facing=south,has_book=false,powered=false]')
    b.set(25,65,123,'oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
    # Two8-station rows in the representative computer room on the third floor.
    # Full black blocks remain legible screens after Bedrock neighbour-state
    # recomputation; isolated panes would collapse visually into narrow posts.
    pane='black_concrete'
    for x in (24,28,32,36,40,44,48,52):
        for z,seat,facing in ((122,123,'south'),(126,125,'north')):
            b.set(x,73,z,'birch_slab[type=top,waterlogged=false]');b.set(x,74,z,pane)
            b.set(x,73,seat,f'oak_stairs[facing={facing},half=bottom,shape=straight,waterlogged=false]')
    # Primary portals are protected after all wall/furniture passes. They only
    # remove blocks within the traced roof; no arbitrary campus plane is added.
    portals=[(70,74,124,151),(108,119,147,153),(82,87,82,87),(53,57,129,131),(103,115,129,131)]
    for x1,x2,z1,z2 in portals:
        for x in range(x1,x2+1):
            for z in range(z1,z2+1):
                if (x,z) in roof:b.fill(x,65,z,x,66,z,'air')
    return b


def notes_and_check(b):
    t=trace();roof=set().union(*(mask(p['world_xz']) for p in t['polygons'].values()))
    # Reserved ground-floor destinations: gate-side spine, wide rotunda,
    # library portals, east arcade and south oval connection.
    def open2(p,floor=64):return all(b.blocks.get((p[0],floor+dy,p[1]),'air')=='air' for dy in (1,2))
    start=(72,150);assert start in roof and open2(start)
    reached={start};q=deque([start])
    while q:
        x,z=q.popleft()
        for p in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
            if p in roof and p not in reached and open2(p):reached.add(p);q.append(p)
    targets=[(72,136),(72,126),(55,130),(54,128),(22,128),(109,130),(110,149),(113,151)]
    missing=[p for p in targets if p not in reached]
    assert not missing,('Ground routes blocked',missing)
    # Representative room circulation at both floor levels.
    for floor in (64,72):
        assert all(open2((x,127),floor) for x in range(21,56))
        assert all(open2((x,128),floor) for x in (22,23,53,54))
    for block in set(b.blocks.values()):
        assert (ROOT/'vendor/assets/minecraft/blockstates'/(block.split('[')[0]+'.json')).exists(),block
    data={'component':'academic_v3','status':'Satellite-traced roofs; interpreted three-storey shell and proposed representative interiors',
          'traced_roof_bounds':{n:v['world_bounds_xz'] for n,v in t['polygons'].items()},
          'roof_cells':len(roof),'blocks':len(b.blocks),'non_air':sum(v!='air' for v in b.blocks.values()),
          'geometry':'All slabs and main roof outlines follow the traced polygon union. No old radius62/52 or southern half-ring was reused.',
          'floors':[64,68,72,76],'roof_y':77,
          'junction':'Broad round roof node is open at ground through full depth with selected columns and a representative stair. Arc/bridge and oval interfaces are also open below.',
          'parapets':'Pale solid classroom parapets with thin horizontal iron trapdoor coping, separate from open ground colonnades; a voxel approximation to the photographed concrete wall + metal handrail.',
          'library':{'bounds':[21,55,121,127],'floor':64,'bookshelf_blocks':52,'reading_seats':12,
                     'reception':'birch counter +empty lectern','status':'Proposed function/furniture'},
          'computer':{'bounds':[21,55,121,127],'floor':72,'stations':16,'status':'Proposed function/furniture'},
          'ground_public_entries':{'south_spine':[72,65,150],'south_oval':[113,65,151],'upper_junction':[72,65,126],
                                   'bridge_library':[54,65,128],'arc_gallery':[109,65,130]},
          'circulation':{'ground_roof_cells_reached':len(reached),'ground_targets_checked':targets,'all_reached':True,
                         'room_aisles':'x21..55,z127 and designateddoors remain2-block-body clear at floors64/72'},
          'cameras':{'upper_junction':{'eye':[72,66.7,135],'target':[67,66.7,120]},
                     'east_arc':{'eye':[102,75,112],'target':[122,71,105]},
                     'library':{'eye':[54,66.7,127],'target':[34,66.1,124]},
                     'computer':{'eye':[54,74.7,127],'target':[35,74.2,123]},
                     'roof_trace_far':{'eye':[186,180,210],'target':[78,74,112]}},
          'uncertainties':['Roof tracing tolerance approximately2.5m; westedges, trees and shadows limit accuracy.',
                           'Satellite does not verify floor count, room divisions, library/computer functions or exact piers.',
                           'The stair and ground-floor junction interpretation remain provisional; no in-game validation.'],
          'palette_counts':dict(Counter(b.blocks.values()))}
    return data


if __name__=='__main__':
    evidence=write_trace()
    if '--trace-only' in sys.argv:
        print(json.dumps({n:p['world_bounds_xz'] for n,p in evidence['polygons'].items()},indent=2))
    else:
        component=build();report=notes_and_check(component)
        result=component.save('parts/layout_academic.json')
        (ROOT/'parts/layout_academic_notes.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({**result,'roof_cells':report['roof_cells'],'ground_routes':report['circulation']},indent=2))
