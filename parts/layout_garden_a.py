"""Southern INNER garden patch; A/B label remains unverified.

Roof positions are protected. Visible fountain registration is measured from
saved satellite frames. Fine planting/path contours interpolate obscured pixels
using the historical courtyard photograph and the 2026 yearbook photographs.
"""
from pathlib import Path
import json, math, sys
from collections import deque, Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder

# New native capture is approximately 2x the original SOUTH screenshot:
# native = 2*south + (-1034,-214). Roof points independently check this fit.
NATIVE_BOUNDARY=[(248,256),(309,243),(390,235),(473,219),(486,243),
 (480,283),(464,323),(443,360),(405,375),(350,369),(296,372),(247,371)]
NATIVE_BEDS=[[(285,264),(312,252),(353,249),(390,247),(411,256),(419,277),
 (409,295),(389,306),(366,300),(346,286),(319,281),(296,285)],
 [(268,298),(285,291),(305,301),(318,314),(314,338),(300,351),(274,346),(259,327)],
 [(378,317),(397,306),(414,296),(436,288),(449,290),(448,312),(436,332),
 (414,349),(396,351),(381,338)]]
FOUNTAIN_NATIVE=(346,326)

def world(p):
    g=json.loads((ROOT/'references/georeference.json').read_text(encoding='utf-8'))
    a,b=g['x_axis_pixel_per_m'];c,d=g['z_axis_pixel_per_m'];ox,oy=g['north_control_origin_pixel']
    px,py=(p[0]+1034)/2,(p[1]+214)/2
    u,v=px-ox,py+g['south_frame_to_north_pixel_offset'][1]-oy;det=a*d-b*c
    return ((d*u-c*v)/det,(-b*u+a*v)/det)

def raster(poly):
    b=Builder('mask');b.polygon(poly,64,64,'grass_block[snowy=false]')
    return {(x,z) for x,y,z in b.blocks}

def protected():
    result=set()
    for name in ('north','academic','south','connectors'):
        d=json.loads((ROOT/'parts'/f'layout_{name}.json').read_text(encoding='utf-8'))
        result|={(x,z) for x,y,z,i in d['blocks'] if y>=64 and d['palette'][i]!='air'}
    return result

def mask():
    return raster([world(p) for p in NATIVE_BOUNDARY])-protected()

def distance(p,path):
    best=999
    for a,b in zip(path,path[1:]):
        vx,vz=b[0]-a[0],b[1]-a[1];l=vx*vx+vz*vz
        t=max(0,min(1,((p[0]-a[0])*vx+(p[1]-a[1])*vz)/l))
        best=min(best,math.hypot(p[0]-a[0]-t*vx,p[1]-a[1]-t*vz))
    return best

PATHS=[[(76,145),(81,145),(85,146),(87,149),(93,149),(99,148),(104,145),(109,138)],
       [(78,136),(83,136),(87,138),(91,140),(96,140),(102,137),(109,136)]]

def build():
    b=Builder('southern_inner_garden_unlabelled_v3');m=mask();cx,cz=world(FOUNTAIN_NATIVE)
    # Remove generic landscape only in the garden and never under a roof mask.
    # Root should omit whole old trees with trunks (89,140),(100,141), avoiding
    # canopy remnants beyond this deliberately restricted patch mask.
    for x,z in m:
        b.fill(x,65,z,x,76,z,'air')
        b.set(x,64,z,'grass_block[snowy=false]')
    paths=set()
    for x,z in m:
        r=math.hypot(x+.5-cx,z+.5-cz)
        if min(distance((x+.5,z+.5),p) for p in PATHS)<=1.15 or 2.4<r<4:
            paths.add((x,z))
            b.set(x,64,z,('andesite','cobblestone','stone')[((x*13+z*7)%11)//4])
    # The 2008 photo clearly shows water-lily basins with sinuous low kerbs.
    # Current water level/species are unknown; these are representative details.
    beds=[]
    for poly in NATIVE_BEDS:
        cells=(raster([world(p) for p in poly]) & m)-paths
        cells={p for p in cells if math.hypot(p[0]+.5-cx,p[1]+.5-cz)>3.3}
        edge={p for p in cells if any((p[0]+dx,p[1]+dz) not in cells for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)))}
        interior=cells-edge
        for x,z in cells:
            b.set(x,64,z,'smooth_sandstone')
            if (x,z) in edge:b.set(x,65,z,'smooth_sandstone_slab[type=bottom,waterlogged=false]')
            else:
                b.set(x,64,z,'water[level=0]')
                if (x*11+z*7)%4!=0:b.set(x,65,z,'lily_pad')
        beds.append(cells)
    # Low circular fountain at the registered satellite centre, approx 4m wide.
    # Two low tiers suggest the ornament without an oversized vertical column.
    fountain=set()
    for x,z in m:
        r=math.hypot(x+.5-cx,z+.5-cz)
        if r<=2.25:
            fountain.add((x,z));b.fill(x,65,z,x,69,z,'air')
            b.set(x,64,z,'smooth_sandstone')
            if r>1.45:
                b.set(x,65,z,'brick_slab[type=bottom,waterlogged=false]')
            else:b.set(x,64,z,'water[level=0]')
    b.disk(cx,cz,1.1,65,65,'smooth_quartz_slab[type=bottom,waterlogged=false]')
    x,z=round(cx),round(cz)
    b.set(x,64,z,'smooth_quartz')
    b.set(x,66,z-1,'quartz_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]')
    b.set(x-1,66,z,'quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]')
    # Sparse low planting, leaving the fountain and all paths legible at eye level.
    for px,pz in ((79,139),(83,148),(98,135),(103,143),(100,149)):
        if (px,pz) not in m or (px,pz) in paths or any((px,pz) in a for a in beds):continue
        b.set(px,65,pz,'flowering_azalea')
    return b

def write_trace(b):
    m=mask();cx,cz=world(FOUNTAIN_NATIVE)
    report={
      'component':'southern INNER garden; A/B location label UNVERIFIED',
      'display_name':'Vườn trong phía nam',
      'ground_block_y':64,'ground_surface_y':65,
      'source_frame':'references/satellite_south_gardens_native.png',
      'primary_affine_frame':'references/satellite_south.png +354Y into north frame',
      'native_to_south':{'scale':0.5,'offset':[517,107],
        'validation_pairs':[{'south':[727,304],'native_observed':[421,397],'native_predicted':[420,394]},
          {'south':[835,332],'native_observed':[633,450],'native_predicted':[636,450]},
          {'south':[782,339],'native_observed':[532,466],'native_predicted':[530,464]}],
        'limit':'Manual visual registration, approximately4 native pixels plus original2.5m georeference uncertainty.'},
      'garden_boundary_native_pixels':NATIVE_BOUNDARY,
      'garden_boundary_world_xz':[world(p) for p in NATIVE_BOUNDARY],
      'fountain':{'native_centre':FOUNTAIN_NATIVE,'south_centre':[690,270],
        'world_centre':[cx,cz],'outer_radius_m':2.25,
        'evidence':'A light circular object is visible at this location in both satellite scales. Ref016 matches a circular brick-capped basin in an enclosed courtyard with a curved side. Yearbook54/65 shows the same characteristic dolphin fountain and curving basins.',
        'confidence':'High for circular feature location; medium for matching the historic/2026 fountain photos; diameter and sculpture simplified to voxel scale.',
        'sculpture_height_limit_y':66,'sculpture_top_above_ground_surface_m':2,
        'visual_qa_fix':'Lowered the former tall quartz column to two compact tiers of slabs/stairs, with no ornament above y66.'},
      'bed_contours_native_pixels':NATIVE_BEDS,
      'bed_contours_world_xz':[[world(p) for p in poly] for poly in NATIVE_BEDS],
      'path_centrelines_world_xz':PATHS,
      'clear_mask_world_xz':[list(p) for p in sorted(m)],
      'clear_bounds_xz':[[min(x for x,z in m),max(x for x,z in m)],[min(z for x,z in m),max(z for x,z in m)]],
      'omit_original_generic_tree_centres':[[89,140],[100,141]],
      'sources':[
       {'file':'references/satellite_south_gardens_native.png','kind':'Current saved Google Maps satellite screenshot; imagery capture date unknown'},
       {'file':'private-reference:ref_016.jpg',
        'url':'https://commons.wikimedia.org/wiki/File:Le_Quy_Don_High_School_Campus,_Da_Nang,_Vietnam.jpg','date':'2008-08-25','credit':'Fa2f CC BY3.0',
        'observation':'Circular multi-tier basin, red brick rim, cream sinuous lily-pool kerbs, narrow irregular stone paths, three-floor courtyard galleries and curved east corner.'},
       {'file':'references/yearbook_research/pdf_page_054.jpg','printed_pages':'105–106',
        'url':'https://drive.google.com/file/d/1TXEm1fgCggApbRagWQ6FrjlikIiKA2iY/view',
        'publication':'School40-year anniversary yearbook, October2026',
        'observation':'Three white dolphin ornaments above a two-tier circular basin, cream wall and vine canopy behind.'},
       {'file':'references/yearbook_research/pdf_page_065.jpg','printed_pages':'127–128',
        'url':'https://drive.google.com/file/d/1TXEm1fgCggApbRagWQ6FrjlikIiKA2iY/view',
        'publication':'School40-year anniversary yearbook, October2026',
        'observation':'Sinuous low cream water-lily bed edges, irregular stone path and circular red-rim fountain.'},
       {'file':'private-reference:843884969_1103992185724382_5632097927844893394_n.jpg','url':'https://www.facebook.com/lqddn/posts/1103992365724364/',
        'observation':'Caption identifies reception A and scale-model lobby, but no exterior geolocation; does not assign garden A.'},
       {'url':'https://nguoikemon.blogspot.com/2012/05/68-truong-toi-tu-mot-goc-nhin.html',
        'files':['private-reference:blog2012_image_1.jpg','private-reference:blog2012_image_2.jpg'],
        'observation':'Shows front checkerboard forecourt and statue; not the interior lily garden, so not used to move fountain into the forecourt.'}],
      'uncertainties':['Planting obscures exact pool and path boundaries; contours are an interpretation constrained by satellite and reference morphology, not survey traces.',
        'Water lilies are explicit in the2008 photograph; current pool water level and plant species are not established.',
        'No pergola constructed here because saved southern garden imagery does not establish its exact footprint. Rectangular pergola photos may depict a different courtyard.',
        'Quartz stairs/slabs only approximate dolphin silhouettes; no claim of sculptural accuracy.',
        'All existing building/connector ground projections are excluded from this patch.'],
      'integration':'Apply after terrain/buildings. Air clears old garden decoration only outside protected building projections. Omit old trees at listed trunk centres to avoid branch remnants outside clear mask.',
      'camera_suggestions':[{'eye':[79,67,147],'target':[90,66,144]},{'eye':[105,68,145],'target':[89,66,144]},{'eye':[88,82,146],'target':[89,64,144]}],
      'walk_targets':[{'feet':[80,65,145],'look_at':[89.13,66.5,144.63],'purpose':'Close fountain view from west path'},
                      {'feet':[103,65,144],'look_at':[89.13,66.5,144.63],'purpose':'Fountain and curving beds from east path'}],
      'validation':validate(b)}
    (ROOT/'references/garden_a_trace.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

def validate(b):
    m=mask();guard=protected()
    assert all((x,z) in m for x,y,z in b.blocks),'Patch escaped garden mask'
    assert not(m & guard),'Patch touches a building projection'
    assert all(64<=y<=76 for x,y,z in b.blocks)
    for s in set(b.blocks.values()):
        assert (ROOT/'vendor/assets/minecraft/blockstates'/f'{s.split("[")[0]}.json').exists(),s
    # Low kerbs/basins stay clear of a continuous north edge connection.
    walk={p for p in m if all(b.blocks.get((p[0],y,p[1]),'air')=='air' for y in (65,66))
          and b.blocks.get((p[0],64,p[1]),'air') not in ('water[level=0]','air')}
    starts=[p for p in walk if p[0]<=78];ends={p for p in walk if p[0]>=103}
    assert starts and ends
    q=deque(starts);seen=set(starts)
    while q:
        x,z=q.popleft()
        for p in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
            if p in walk and p not in seen:seen.add(p);q.append(p)
    assert seen & ends,'Garden blocks west-east circulation'
    air={p for p,s in b.blocks.items() if s=='air'}
    assert all((x,z) in m and 65<=y<=76 for x,y,z in air)
    cx,cz=world(FOUNTAIN_NATIVE)
    path_cells={p for p in m if min(distance((p[0]+.5,p[1]+.5),q) for q in PATHS)<=1.15
                or 2.4<math.hypot(p[0]+.5-cx,p[1]+.5-cz)<4}
    beds=[]
    for poly in NATIVE_BEDS:
        cells=(raster([world(p) for p in poly])&m)-path_cells
        cells={p for p in cells if math.hypot(p[0]+.5-cx,p[1]+.5-cz)>3.3}
        assert not(cells&path_cells)
        assert not any(cells&prior for prior in beds)
        beds.append(cells)
    assert all(p in seen for p in ((80,145),(103,144))), 'Close-view targets must be reachable'
    return {'garden_cells':len(m),'block_cells_including_air':len(b.blocks),
      'palette_states':len(set(b.blocks.values())),'protected_footprint_overlap':0,
      'two_block_headroom_west_east_route':'PASS','reachable_walk_cells':len(seen),
      'air_cells':len(air),'air_mask_outside_garden':0,'air_building_footprint_overlap':0,
      'bed_path_overlap':0,'bed_bed_overlap':0,'bed_raster_cells':[len(cells) for cells in beds],
      'close_view_walk_targets':'PASS',
      'materials_exist':'PASS','in_game_test':False}

if __name__=='__main__':
    b=build();report=write_trace(b);print(json.dumps(b.save('parts/layout_garden_a.json')))
    print(json.dumps(report['validation']))
