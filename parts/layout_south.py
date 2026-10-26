"""Satellite-traced lower wing and filled oval lobby, Layout v3.

Footprints follow references/south_trace.json. Floor counts, height, functional
room assignments and furniture are interpreted; no ring courtyard is invented.
"""
from pathlib import Path
import sys,math,json
from collections import Counter,deque
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from voxel import Builder

ROOT=Path(__file__).resolve().parents[1]
BAYS=(30,37,44,51,58,79,86)
CREAM='smooth_sandstone';WHITE='white_concrete';GLASS='light_gray_stained_glass'
CHAIR='birch_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]'
DESK='birch_slab[type=top,waterlogged=false]'

def mask_polygon(points):
    cells=set()
    for z in range(math.floor(min(p[1] for p in points)),math.ceil(max(p[1] for p in points))+1):
        for x in range(math.floor(min(p[0] for p in points)),math.ceil(max(p[0] for p in points))+1):
            inside=False;j=len(points)-1
            for i,(xi,zi) in enumerate(points):
                xj,zj=points[j]
                if (zi>z+.5)!=(zj>z+.5) and x+.5<(xj-xi)*(z+.5-zi)/(zj-zi)+xi:inside=not inside
                j=i
            if inside:cells.add((x,z))
    return cells

def load_masks():
    j=json.loads((ROOT/'references/south_trace.json').read_text(encoding='utf-8'))
    return {p['id']:mask_polygon(p['world_xz']) for p in j['roof_polygons']}

def perimeter(mask):
    return {p for p in mask if any((p[0]+dx,p[1]+dz) not in mask for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)))}

def contour(mask):
    edges={}
    for x,z in mask:
        for n,a,c in (((x,z-1),(x,z),(x+1,z)),((x+1,z),(x+1,z),(x+1,z+1)),
                      ((x,z+1),(x+1,z+1),(x,z+1)),((x-1,z),(x,z+1),(x,z))):
            if n not in mask:edges[a]=c
    loops=[]
    while edges:
        start=next(iter(edges));p=start;loop=[]
        while p in edges:
            loop.append(p);p=edges.pop(p)
            if p==start:break
        simple=[]
        for i,p in enumerate(loop):
            prev=loop[i-1];nxt=loop[(i+1)%len(loop)]
            if (p[0]-prev[0])*(nxt[1]-p[1])!=(p[1]-prev[1])*(nxt[0]-p[0]):simple.append(p)
        loops.append(simple)
    return loops

def build():
    masks=load_masks();wing=masks['lower_wing'];oval=masks['filled_terminal']
    union=wing|oval;b=Builder('layout_south')
    wingedge=perimeter(wing);ovaledge=perimeter(oval)
    def safe(x,y,z,state):
        if (x,z) in union:b.set(x,y,z,state)
    def box(x1,y1,z1,x2,y2,z2,state):
        for z in range(z1,z2+1):
            for x in range(x1,x2+1):
                if (x,z) in union:b.fill(x,y1,z,x,y2,z,state)
    # West-east lower roof plus its broad south bulge. Three classroom levels
    # belong here, distinct from the two tall levels in the oval terminal.
    for x,z in wing:
        for y in (64,68,72,76):b.set(x,y,z,'smooth_stone')
        b.set(x,77,z,WHITE if (x,z) in wingedge else 'light_gray_concrete')
    for floor in range(3):
        low=65+4*floor
        for x,z in wingedge:
            # Front bulge projects over a genuinely open ground lobby/veranda.
            if floor==0 and z>=163:
                if x%7==1 and not (69<=x<=75):b.fill(x,low,z,x,low+2,z,'quartz_block')
            else:
                b.fill(x,low,z,x,low+2,z,CREAM)
                if 2<=x%7<=5 and x>23:
                    b.fill(x,low+1,z,x,low+2,z,GLASS)
                if x%7==1:b.fill(x,low,z,x,low+2,z,WHITE)
            b.set(x,low+3,z,WHITE)
        # Representative rooms fit the traced rectangular core, leaving the
        # central x69..75 academic/public gallery entirely open on each level.
        for left in BAYS:
            right=left+5;door=left+1
            box(left,low,153,right,low+2,158,'air')
            box(left,low-1,153,right,low-1,158,'smooth_quartz')
            box(left-1,low,153,left-1,low+2,159,CREAM)
            box(right+1,low,153,right+1,low+2,159,CREAM)
            box(left,low,159,right,low+2,159,CREAM)
            box(door,low,159,door+1,low+1,159,'air')
            box(left+3,low+1,159,right,low+2,159,GLASS)
            box(left+1,low+1,153,left+4,low+2,153,'green_concrete')
            safe(left,low,153,'bookshelf')
            safe(left,low,154,'lectern[facing=south,has_book=false,powered=false]')
            safe(right,low,153,'spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
            box(left+4,low,154,right,low,154,'spruce_slab[type=top,waterlogged=false]')
            box(door,low,154,door+1,low,158,'light_blue_carpet')
            for z in (155,157):
                safe(left,low,z,DESK);safe(left,low,z+1,CHAIR)
                box(left+3,low,z,right,low,z,DESK)
                for x in (left+3,right):safe(x,low,z+1,CHAIR)
            for x in (left+1,left+4):
                for z in (154,157):safe(x,low+3,z,'sea_lantern')
        # Main west-east public corridor and the gallery from academic spine.
        box(26,low,160,96,low+1,162,'air')
        box(69,low,151,75,low+2,172,'air')
        for x in range(29,97,7):safe(x,low+3,161,'sea_lantern')
        # South edge is a solid low parapet upstairs, open below at the entry.
        if floor:
            for x,z in wingedge:
                if z>=164:b.set(x,low,z,CREAM)
    # Two stacked four-rise flights at west end, with a side return landing.
    box(23,65,154,25,75,157,'air')
    for low in (65,69):
        for i in range(4):
            box(23,low+i,157-i,25,low+i,157-i,
                'polished_andesite_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
        box(23,low+3,153,27,low+3,153,'smooth_stone')
    # The terminal is a filled oval roof and floor plate, not an annulus.
    for x,z in oval:
        # The roof overlap is a join, not an extra stack of classroom slabs.
        b.fill(x,65,z,x,75,z,'air')
        for y in (64,70,76):b.set(x,y,z,'smooth_quartz' if y==64 else 'smooth_stone')
        b.set(x,77,z,WHITE if (x,z) in ovaledge else 'light_gray_concrete')
    # Upper volume: generous solid cream surfaces, separated tall window bays,
    # and no invented repeated three-storey classroom facade around the oval.
    for x,z in ovaledge:
        b.fill(x,71,z,x,75,z,CREAM)
        angle=(math.degrees(math.atan2(z+.5-165.2,x+.5-112.5))+360)%360
        if 8<=angle%30<=18:b.fill(x,72,z,x,74,z,GLASS)
        b.set(x,76,z,WHITE)
    # Ground storey is recessed/open under widely spaced load-bearing piers.
    # At the western join and north connection, keep broad paths unobstructed.
    for a in range(0,360,30):
        tx=112.5+15.1*math.cos(math.radians(a));tz=165.2+15.1*math.sin(math.radians(a))
        x,z=min(ovaledge,key=lambda p:(p[0]+.5-tx)**2+(p[1]+.5-tz)**2)
        if (x<102 and 159<=z<=169) or (106<=x<=120 and z<=153):continue
        b.fill(x,65,z,x,69,z,'quartz_block')
    for x,z in ((106,162),(118,165),(106,174),(119,174)):
        safe(x,65,z,'quartz_block');box(x,65,z,x,69,z,'quartz_block')
    # A glazed recessed rear threshold, with a four-metre public opening.
    box(104,65,157,120,69,157,GLASS)
    box(110,65,157,113,68,157,'air')
    box(104,69,157,120,69,157,WHITE)
    # Reception furniture is deliberately modest and off the central route.
    box(116,65,160,119,65,160,'spruce_slab[type=top,waterlogged=false]')
    for x in (116,118):safe(x,65,159,'spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
    # Open benches by the perimeter; these do not assert a real room function.
    for z in (169,172):
        for x in (102,103,122,123):safe(x,65,z,'quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]')
    for y in (70,76):
        for x in (106,112,118):
            for z in (160,166,173):safe(x,y,z,'sea_lantern')
    # Six-rise stair at northeast side reaches upper oval slab y70 (top71).
    box(121,65,160,122,75,165,'air')
    for i in range(6):
        box(121,65+i,165-i,122,65+i,165-i,
            'polished_andesite_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
    for x in (120,123):
        for z in range(160,166):safe(x,71,z,'iron_bars[east=false,north=true,south=true,waterlogged=false,west=false]')
    # Ground west join: the two traced roof masks meet around x97,z163.
    box(94,65,160,101,66,166,'air')
    # Northern gallery meets academic roof north edge near x110..119,z150.
    box(109,65,150,116,66,153,'air')
    return b

def verify(b):
    masks=load_masks();wing=masks['lower_wing'];oval=masks['filled_terminal'];union=wing|oval
    assert all((x,z) in union and 64<=y<=77 for x,y,z in b.blocks)
    roof={(x,z) for (x,y,z),s in b.blocks.items() if y==77 and s!='air'}
    assert roof==union,'Roof cells diverged from traced filled masks'
    assert all((x,z) in roof for x,z in oval),'Oval contains a roof hole'
    assets=ROOT/'vendor/assets/minecraft/blockstates'
    assert all((assets/(s.split('[')[0]+'.json')).exists() for s in set(b.blocks.values()))
    def air(x,y,z):
        s=b.blocks.get((x,y,z),'air')
        return s=='air' or s.endswith('_carpet')
    def reachable(start,target,y):
        q=deque([start]);seen={start}
        while q:
            x,z=q.popleft()
            for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
                p=x+dx,z+dz
                if p in union and p not in seen and air(p[0],y,p[1]) and air(p[0],y+1,p[1]):seen.add(p);q.append(p)
        assert target in seen,('Clearance',start,target,y)
        return len(seen)
    routes=[]
    for floor in range(3):
        y=65+4*floor
        for left in BAYS:
            reachable((left+1,161),(left+1,154),y)
            for x,z in ((left,156),(left,158),(left+3,156),(left+3,158),(left+5,156),(left+5,158),(left+5,153)):
                assert air(x,y+1,z) and air(x,y+2,z),('Chair headroom',x,y,z)
        reachable((72,152),(72,169),y)
    routes.append({'from':[72,65,152],'to':[72,65,171],'check':'PASS','description':'Academic north-south gallery to open southern threshold'})
    reachable((72,152),(72,171),65)
    reachable((72,171),(112,177),65)
    routes.append({'from':[72,65,171],'to':[112,65,177],'check':'PASS','description':'Southern entry through west-east gallery to open oval lobby'})
    reachable((90,161),(112,166),65)
    routes.append({'from':[90,65,161],'to':[112,65,166],'check':'PASS','description':'West connector into oval centre'})
    for low in (65,69):
        for i in range(4):
            for x in (23,24,25):
                assert air(x,low+i+1,157-i) and air(x,low+i+2,157-i),'West stair headroom'
    for i in range(6):
        for x in (121,122):
            assert air(x,66+i,165-i) and air(x,67+i,165-i),'Oval stair headroom'
    return {'roof_cells':len(roof),'oval_filled_roof_cells':len(oval),'wing_roof_cells':len(wing),
            'routes':routes,'room_door_and_chair_headroom':'PASS','classroom_count':len(BAYS)*3,
            'public_entry_targets':[[72,65,171],[72,65,152],[98,65,164],[112,65,177]],
            'stairs':'Two separate inferred stairs; every step has two clear blocks above, ground connectors fully tested. No direct upper-floor link is claimed between 4m classroom slabs and 6m oval slabs.'}

def main():
    b=build();v=verify(b);masks=load_masks()
    trace_path=ROOT/'references/south_trace.json';trace=json.loads(trace_path.read_text())
    for p in trace['roof_polygons']:
        mask=masks[p['id']];p['achieved_roof_world_polygons']=contour(mask)
        p['achieved_roof_cells']=len(mask)
        p['achieved_roof_bounds_inclusive']=[[min(v[i] for v in mask),max(v[i] for v in mask)] for i in range(2)]
        p['roof_mask_runs']=[[z,min(x for x,zz in mask if zz==z),max(x for x,zz in mask if zz==z)] for z in sorted({z for x,z in mask})]
    trace_path.write_text(json.dumps(trace,indent=2),encoding='utf-8')
    notes={'component':'layout_south','snapshot':'Layout v3; fresh traced geometry, no v1 half-ring retained',
           'evidence':['references/satellite_south.png with corrected +354Y registration','references/georeference.json','research/browser_036.jpg','research/ref_020.jpg'],
           'roof_trace':'references/south_trace.json','uncertainty_m':2.5,
           'floor_interpretation':{'west_wing':'3 classroom storeys; slabs64/68/72/76, roof77','oval':'2 tall levels; slabs64/70/76, roof77; floor count and height inferred from photos, not a survey'},
           'ground_lobby':'Broad open lower oval and southern wing bulge beneath piers; recessed glazed rear threshold. No statue or pedestal invented.',
           'validation':v,'bounds':[[min(p[i] for p in b.blocks),max(p[i] for p in b.blocks)] for i in range(3)],
           'palette_counts':dict(sorted(Counter(b.blocks.values()).items())),
           'cameras':[{'label':'Gate-facing lobby eye','position':[72,66.6,182],'target':[72,67,160]},
                      {'label':'Oval under piers','position':[108,66.6,177],'target':[114,68,158]},
                      {'label':'Oval west connection','position':[90,66.6,162],'target':[112,67,166]},
                      {'label':'Classroom','position':[39,66.6,158],'target':[40,66,153]},
                      {'label':'Far top layout','position':[77,200,166],'target':[77,65,166]}],
           'limitations':['Roof edges may differ from wall line due overhang and image parallax.','Interior room partitions, desks, reception, benches, pillars and stair locations are playable proposals.','No in-game validation; root assembles visual/export QA.','Statue, gate, landscape belong to root and are absent from this component.']}
    (ROOT/'parts/layout_south_notes.json').write_text(json.dumps(notes,indent=2),encoding='utf-8')
    print(json.dumps(b.save('parts/layout_south.json')))
    print(json.dumps(v))

if __name__=='__main__':main()
