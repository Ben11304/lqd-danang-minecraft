"""Garden west of the spine between the two transverse wings.

Courtyard envelope/tree bands/path sightlines follow satellite; small pergola
and planting detail are an explicitly provisional interpretation of the
staff-labelled B photograph. This module edits landscape only.
"""
from pathlib import Path
from collections import Counter, deque
import json, math, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder

NORTH_PIXELS={
 'courtyard_envelope':[(444,603),(565,594),(576,603),(606,605),(614,647),(600,656),(450,665),(436,648)],
 'north_canopy_band':[(448,606),(530,598),(565,599),(579,612),(554,620),(476,628),(444,623)],
 'south_canopy_band':[(455,641),(505,629),(546,628),(574,642),(575,655),(452,663),(444,651)],
 'path_observed_fragments':[(436,637),(466,632),(494,630),(526,625),(550,623),(570,627),(586,634),(607,645)],
 'east_connection':[(607,645),(617,641)]
}

def world(p):
    g=json.loads((ROOT/'references/georeference.json').read_text())
    a,b=g['x_axis_pixel_per_m'];c,d=g['z_axis_pixel_per_m'];u,v=p[0]-332,p[1]-126
    det=a*d-b*c
    return ((d*u-c*v)/det,(-b*u+a*v)/det)

def raster(poly):
    q=Builder('mask');q.polygon(poly,64,64,'grass_block[snowy=false]')
    return {(x,z) for x,y,z in q.blocks}

def protection():
    result=set()
    for name in ('north','academic','south','connectors'):
        path=ROOT/'parts'/f'layout_{name}.json'
        if path.exists():
            d=json.loads(path.read_text()); result.update((x,z) for x,y,z,i in d['blocks'] if y>=64)
    return result

def dist(p,a,b):
    vx,vz=b[0]-a[0],b[1]-a[1];length=vx*vx+vz*vz
    t=max(0,min(1,((p[0]-a[0])*vx+(p[1]-a[1])*vz)/length)) if length else 0
    return math.hypot(p[0]-a[0]-t*vx,p[1]-a[1]-t*vz)

def data():
    return {key:[world(p) for p in pts] for key,pts in NORTH_PIXELS.items()}

def build():
    d=data();protected=protection();court=raster(d['courtyard_envelope'])-protected
    b=Builder('layout_garden_b_west_inner_court_v3')
    # Clear only the courtyard void. All structural footprint cells, including
    # open galleries/roofed circulation, are excluded from every operation.
    for x,z in court:
        b.fill(x,65,z,x,76,z,'air')
        b.set(x,64,z,'grass_block[snowy=false]')
    route=d['path_observed_fragments']+d['east_connection'][1:]
    pathcells=set()
    for x,z in court:
        nearest=min(dist((x+.5,z+.5),a,c) for a,c in zip(route,route[1:]))
        if nearest<=1.15:
            b.set(x,64,z,'cobblestone' if (x+z)%5 else 'andesite');pathcells.add((x,z))
        elif nearest<=1.8 and (x*7+z*3)%6==0:b.set(x,64,z,'coarse_dirt')
    # Dense, irregular canopy bands are visible on satellite. Individual tree
    # trunks/heights/species are not measured; do not replace them by a grid.
    north=raster(d['north_canopy_band'])&court
    south=raster(d['south_canopy_band'])&court
    trees=[(25,136,6,3),(32,136,7,3),(39,135,6,3),(47,135,7,3),
           (55,136,6,2),(26,148,6,3),(34,146,7,3),(42,146,6,3),
           (50,148,7,3),(57,146,6,2)]
    for cx,cz,h,r in trees:
        if (cx,cz) not in court or (cx,cz) in pathcells:continue
        b.fill(cx,65,cz,cx,64+h,cz,'oak_log[axis=y]')
        for dy in range(-2,3):
            rr=r*(1-(abs(dy)/3.1)**1.6)**.5
            for x in range(cx-r,cx+r+1):
                for z in range(cz-r,cz+r+1):
                    if (x,z) in court and (x-cx)**2+(z-cz)**2<=rr**2:
                        if not(x==cx and z==cz and dy<0):b.set(x,64+h+dy,z,'oak_leaves[distance=1,persistent=true,waterlogged=false]')
    # Low planting in canopy beds, with a kept-open, winding stone path.
    for x,z in (north|south)-pathcells:
        if b.blocks.get((x,65,z))!='air':continue
        k=(x*19+z*11)%31
        if k in (0,1,2):b.set(x,65,z,'azalea' if k==0 else 'fern')
        elif k in (3,4,5):b.set(x,65,z,'short_grass')
    # The labelled B close-up proves square vine-wrapped supports. Its small
    # visible cluster does not reveal a complete plan; retain a modest 3-bay
    # interpreted trellis at the east garden edge, not a roof over the garden.
    pergola={'x':[52,58,64],'z':[138,143],'beam_y':69,'status':'representative / placement provisional'}
    for x in pergola['x']:
        for z in pergola['z']:
            if (x,z) not in court or (x,z) in pathcells:continue
            b.fill(x,65,z,x,68,z,'smooth_sandstone')
            for y in (66,67,68,69):
                for xx,zz in ((x+1,z),(x,z+1)):
                    if (xx,zz) in court and (xx,zz) not in pathcells:
                        b.set(xx,y,zz,'oak_leaves[distance=1,persistent=true,waterlogged=false]')
    for z in pergola['z']:
        for x in range(52,65):
            if (x,z) in court:b.set(x,69,z,'smooth_sandstone')
    for x in pergola['x']:
        for z in range(138,144):
            if (x,z) in court:b.set(x,69,z,'smooth_sandstone')
    # Sparse climbers above selected beams, leaving large open sky gaps.
    for x in range(52,65):
        for z in range(138,144):
            if (x,z) in court and (x+2*z)%5==0:
                b.set(x,70,z,'oak_leaves[distance=1,persistent=true,waterlogged=false]')
    # Restore the two-block-body route after all planting passes.
    for x,z in pathcells:b.fill(x,65,z,x,66,z,'air')
    return b

def validate(b):
    d=data();protected=protection();court=raster(d['courtyard_envelope'])-protected
    assert not any((x,z) in protected for x,y,z in b.blocks)
    route=d['path_observed_fragments']+d['east_connection'][1:]
    pathcells={(x,z) for x,z in court if min(dist((x+.5,z+.5),a,c) for a,c in zip(route,route[1:]))<=1.15}
    assert pathcells
    assert all(b.blocks.get((x,y,z))=='air' for x,z in pathcells for y in (65,66))
    reached={next(iter(pathcells))};q=deque(reached)
    while q:
        x,z=q.popleft()
        for p in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
            if p in pathcells and p not in reached:reached.add(p);q.append(p)
    assert len(reached)==len(pathcells),('Disconnected traced path',len(reached),len(pathcells))
    for state in set(b.blocks.values()):
        assert (ROOT/'vendor/assets/minecraft/blockstates'/f'{state.split("[")[0]}.json').exists(),state
    return {'court_cells':len(court),'route_cells':len(pathcells),'route_single_component':True,
            'two_block_head_clear':True,'structural_footprint_overlaps':0,
            'palette_counts':dict(Counter(b.blocks.values())),
            'ground_bfs_destinations':[[63,65,147],[25,65,143]],
            'cameras':{'east_edge':{'eye':[63,66.7,147],'target':[43,66.4,141]},
                       'mid_path':{'eye':[42,66.7,140],'target':[59,68,140]},
                       'overhead':{'eye':[44,104,149],'target':[44,64,142]}}}

def write_evidence(check):
    d=data()
    out={
      'component':'garden_b_west_inner_court_v3',
      'researched_on':'2026-10-26',
      'location':{'description':'Rectangular courtyard WEST of the thin north/south spine, between the two transverse academic wings.',
                  'bounds_approx_world_xz':[[19,68],[134,152]],
                  'confidence':'moderate: labelled B photo location check supports this courtyard, but source geolocation horizontal uncertainty is about18m; exact camera spot is not fixed.',
                  'naming':'Component file keeps assigned garden_b identifier; public camera should use geographical description until A/B limits are established.'},
      'source_frame':'references/satellite_north.png',
      'south_to_north_offset_y':354,
      'georeference':'references/georeference.json',
      'trace_uncertainty_m':2.5,
      'polygons':{k:{'original_pixels_north_frame':NORTH_PIXELS[k],
                     'world_xz':[[round(x,3),round(z,3)] for x,z in v],
                     'status':'canopy envelope, not individual trunks or exact bed edging'}
                  for k,v in d.items() if k not in ('path_observed_fragments','east_connection')},
      'polylines':{k:{'original_pixels_north_frame':NORTH_PIXELS[k],
                      'world_xz':[[round(x,3),round(z,3)] for x,z in d[k]],
                      'status':'visible light gaps / walking fragments joined across canopy; hidden bends are inferred'}
                   for k in ('path_observed_fragments','east_connection')},
      'primary_photo':{'path':'references/lobby_source_0.jpg',
        'url':'https://drive.google.com/file/d/19ASqF0LWPNKoxvaHOJ5ktPoeFQvqbRJ4/view',
        'original_filename':'12D1 sảnh B còn 1 túi rác.HEIC',
        'provenance':'Public photo-evidence folder linked from teacher/staff youth branch cleaning plan06 dated2024-01-25; photo2024-01-27.',
        'observed':['Stone footpath with uneven slate-like pieces and narrow reddish edging',
                    'Lush low planting and square supports densely wrapped in climbing vines',
                    'Opposite cream wall has metal-framed/grilled rectangular windows',
                    'Foreground low cream concrete parapet, one gray pipe rail, terrazzo bench and gray floor tiles'],
        'position_check':'Checked original photograph location against live Google Maps satellite; supports the west courtyard near the spine, at stated18m uncertainty. Personal/device metadata is deliberately omitted.'},
      'comparison_photos':[
        {'path':'private-reference/LQD_DaNang_Minecraft_Research/images/browser_037.jpg',
         'use':'Architectural example of square concrete pergola, winding stone path and planting; exact relationship to B photo is NOT established. Not used as an independent site locator.'},
        {'path':'private-reference/LQD_DaNang_Minecraft_Research/images/ref_016.jpg',
         'date':'2008-08-25',
         'use':'Historic curving pond/fountain garden. Different distinctive features; excluded from this component and handled separately by the south garden agent.'},
        {'path':'private-reference/LQD_DaNang_Minecraft_Research/images/ref_012.jpg',
         'date':'2025-08-22',
         'use':'Supports pale gallery/parapet and rail materials; not used to label this garden or copy an entire garden plan.'}],
      'construction_decisions':{
        'observed':'Court bounds between traced roofs, dense twin canopy bands and central light walking gaps.',
        'interpreted':'Individual tree trunks/species/heights; exact path bends under trees; sparse underplanting.',
        'pergola':'Only a modest representative cluster x52..64,z138..143, beams69; type supported by B photo but exact grid/footprint is provisional.',
        'not_added':['No fountain, lily pond, invented dolphin sculpture, or full rectangular paved plaza.',
                     'No trees or clearing operations inside structural footprints.']},
      'qa':check,
      'mutations':'Only this trace JSON and parts/layout_garden_b.py/.json. Assembly/buildings/public repo not edited.'
    }
    (ROOT/'references/garden_b_trace.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    b=build();check=validate(b);write_evidence(check)
    print(json.dumps({**b.save('parts/layout_garden_b.json'),**check},ensure_ascii=False))
