"""Ground-only interpretation of visible northeast circulation; no C label."""
from pathlib import Path
from collections import deque
import sys,json,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder

PIXEL_ROUTES={
 'east_curve_gap':[(847,544),(832,519),(822,503),(818,474),(817,447),(816,418),(805,393),(797,382),(797,368)],
 'north_curve_garden':[(681,365),(683,357),(699,363),(714,371),(732,380),(760,386),(783,384),(797,368)]}
WORLD_ROUTES={
 'annex_west_approach':[(123.5,77),(123.5,70),(123.5,61),(127,61)],
 'tower_south_approach':[(123.5,61),(123.5,52),(124,48),(129,46)]}

def world(p):
    g=json.loads((ROOT/'references/georeference.json').read_text())
    a,b=g['x_axis_pixel_per_m'];c,d=g['z_axis_pixel_per_m'];u,v=p[0]-332,p[1]-126;det=a*d-b*c
    return ((d*u-c*v)/det,(-b*u+a*v)/det)

def distance(p,a,b):
    dx,dz=b[0]-a[0],b[1]-a[1];l=dx*dx+dz*dz
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/l)) if l else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dz)

def components():
    blocks={}
    for name in ('north','academic','south','connectors'):
        d=json.loads((ROOT/'parts'/f'layout_{name}.json').read_text())
        for x,y,z,i in d['blocks']:blocks[x,y,z]=d['palette'][i]
    return blocks

def routes():
    r={k:[world(p) for p in ps] for k,ps in PIXEL_ROUTES.items()}
    # Join observed paving at southwest annex to the unchanged existing entry.
    r['east_curve_gap'] += [(123.5,77)]
    r['north_curve_garden'] += [(123.5,77)]
    r.update(WORLD_ROUTES)
    return r

def make():
    existing=components();r=routes();mask=set();blocked=set()
    for x in range(82,141):
        for z in range(42,129):
            p=(x+.5,z+.5)
            if min(distance(p,a,b) for ps in r.values() for a,b in zip(ps,ps[1:]))>1.45:continue
            # Do not delete existing walls, columns, stairs or any building.
            if any(existing.get((x,y,z),'air')!='air' for y in (65,66,67)):
                blocked.add((x,z));continue
            mask.add((x,z))
    # Rasterization may leave one cell behind a preserved facade corner.
    # Keep only the paved component connected to the eastern bridge portal.
    reached={(133,124)};q=deque(reached)
    while q:
        x,z=q.popleft()
        for p in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
            if p in mask and p not in reached:reached.add(p);q.append(p)
    mask &= reached
    b=Builder('layout_ne_ground_circulation_v3')
    for x,z in mask:
        if existing.get((x,64,z),'air')=='air':b.set(x,64,z,'andesite')
        for y in (65,66,67):b.set(x,y,z,'air')
    return b,mask,blocked

def build():return make()[0]

def check(mask,points):
    start=points[0];seen={start};q=deque([start])
    while q:
        x,z=q.popleft()
        for p in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
            if p in mask and p not in seen:seen.add(p);q.append(p)
    return {'start':start,'targets':points[1:],'all_targets_reached':all(p in seen for p in points),
            'reached_mask_cells':len(seen),'target_status':{f'{x},{z}':(x,z) in seen for x,z in points}}

if __name__=='__main__':
    b,mask,blocked=make();r=routes()
    qa=check(mask,[(133,124),(127,61),(129,46)])
    print(json.dumps({**b.save('parts/layout_ne_circulation.json'),'paved_mask_cells':len(mask),'qa':qa}))
    report={'component':'layout_ne_ground_circulation_v3','source_frames':['satellite_north.png','satellite_northeast_route_native.png','satellite_northeast_route_south_native.png'],
      'georeference':'references/georeference.json','pixel_frame':'Original north1280x720; native zoom images used to inspect paving, not guessed scale-transformed.',
      'routes':{k:{'world_xz':[[round(x,3),round(z,3)] for x,z in ps],
                   'original_pixels_north':PIXEL_ROUTES.get(k),
                   'status':'Ground paving route interpretation; exact boundaries underneath tree canopy uncertain.'} for k,ps in r.items()},
      'paved_mask_xz':sorted([list(p) for p in mask]),
      'mask_includes_existing_structural_floor':True,
      'clearance':'Only air65..67 where original building components already have air; solid structural blocks unchanged.',
      'unchanged_entry_targets':[[127,65,61],[129,65,46]],
      'qa':qa,'structural_blockers_excluded_xz':sorted([list(p) for p in blocked]),
      'north_branch_interface':{'paved_approach_xz':[[93,72],[94,72]],
           'root_proposed_door_xz':[[93,73],[94,76]],
           'status':'The traced ground approach meets the northern curved-wing facade. Root may separately open a game-access door at x93..94,z73..76. This component does not cut the wall and makes no claim that this is a real school doorway.'},
      'confidence':{'paving_around_southwest_annex':'high visible hardscape',
           'narrow_gap_between_curve_and_pale_rectangle':'medium-high continuous visible strip; roof parallax/trees affect width',
           'north_branch_around_round_garden_feature':'medium-high visible curved paving with local canopy occlusion',
           'exact_route_width':'voxel interpretation, nominal2.9m',
           'C_identity':'unresolved; neither bridge nor northern branch is labelled C'},
      'limits':['No canteen function inferred from pale rectangle or roof area.',
                'Native south image suggests pale rectangle is a surface with tree shadows, but no building/roof added or removed.',
                'Individual tree/plant gaps preserved except narrow ground corridor clearance; no new roof or door.',
                'The approach stubs to existing annex/tower doors adapt the traced pavement for usable Minecraft circulation.'],
      'public_naming':'Northeast circulation / route toward dormitory-side annex; C-to-canteen function pending confirmation.',
      'writes':['parts/layout_ne_circulation.py','parts/layout_ne_circulation.json','references/ne_circulation_trace.json']}
    (ROOT/'references/ne_circulation_trace.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
