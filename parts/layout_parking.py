"""Three satellite-traced open auxiliary roofs; parking functions unverified."""
from pathlib import Path
from collections import Counter,deque
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder
TARGETS={'east_long_auxiliary_canopy':(137,170),
         'northwest_auxiliary_roof':(29,21),
         'west_long_auxiliary_canopy':(9,61)}

def roof_masks():
    trace=json.loads((ROOT/'references/parking_trace.json').read_text(encoding='utf-8'))
    out={}
    for poly in trace['polygons']:
        if poly.get('build_decision')!='BUILD_GENERIC_CANOPY':continue
        temp=Builder('mask');temp.polygon(poly['world_xz_polygon'],64,64,'smooth_stone')
        out[poly['id']]={(x,z) for x,y,z in temp.blocks}
    return out

def roof_mask():
    return set().union(*roof_masks().values())

def build():
    b=Builder('three_auxiliary_canopies_v3_functions_unknown')
    post='iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]'
    for name,mask in roof_masks().items():
        along_z=name!='northwest_auxiliary_roof'
        lo=min(p[1 if along_z else 0] for p in mask);hi=max(p[1 if along_z else 0] for p in mask)
        ribs=set(range(lo+3,hi-1,6))
        for x,z in mask:
            b.set(x,64,z,'andesite');b.fill(x,65,z,x,67,z,'air')
            if name=='east_long_auxiliary_canopy':
                material='terracotta' if z in ribs else 'red_terracotta'
            else:material='light_gray_concrete' if (z if along_z else x) in ribs else 'white_concrete'
            b.set(x,69,z,material)
        for u in sorted(ribs):
            cross=sorted(p[0 if along_z else 1] for p in mask if p[1 if along_z else 0]==u)
            if len(cross)<4:continue
            for v in (cross[0],cross[-1]):
                x,z=(v,u) if along_z else (u,v)
                b.fill(x,65,z,x,68,z,post)
            for v in cross:
                x,z=(v,u) if along_z else (u,v)
                b.set(x,68,z,'light_gray_concrete')
    return b

def validate(b):
    masks=roof_masks();allowed=set().union(*masks.values())
    assert all((x,z) in allowed for x,y,z in b.blocks)
    assert all(64<=y<=69 for x,y,z in b.blocks)
    reports={}
    for name,mask in masks.items():
        walk={p for p in mask if all(b.blocks.get((p[0],y,p[1]),'air')=='air' for y in (65,66))}
        target=TARGETS[name];assert target in walk,(name,'target blocked',target)
        seen={target};q=deque([target])
        while q:
            x,z=q.popleft()
            for p in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
                if p in walk and p not in seen:seen.add(p);q.append(p)
        along_z=name!='northwest_auxiliary_roof';axis=1 if along_z else 0
        lo=min(p[axis] for p in mask);hi=max(p[axis] for p in mask)
        assert any(p[axis]<=lo+1 for p in seen) and any(p[axis]>=hi-1 for p in seen),(name,'end connection')
        narrow=[]
        for u in range(lo,hi+1):
            cross=sorted(p[1-axis] for p in mask if p[axis]==u)
            if len(cross)<2:narrow.append(u);continue
            def point(v):return (v,u) if along_z else (u,v)
            assert any(point(v) in walk and point(v+1) in walk for v in cross),(name,'2wide',u)
        reports[name]={'roof_cells':len(mask),'body_cells_reached':len(seen),
            'validation_target_xyz':[target[0],65,target[1]],
            'bounds_xz':[[min(p[i] for p in mask),max(p[i] for p in mask)] for i in (0,1)],
            'two_wide_on_normal_width_rows':True,'one_cell_roof_tip_rows':narrow}
    for s in set(b.blocks.values()):
        assert (ROOT/'vendor/assets/minecraft/blockstates'/(s.split('[')[0]+'.json')).exists(),s
    return {'entries':len(b.blocks),'solid_blocks':sum(s!='air' for s in b.blocks.values()),
            'roof_cells_total':len(allowed),'canopies':reports,
            'bounds_xyz':[[min(v[i] for v in b.blocks),max(v[i] for v in b.blocks)] for i in range(3)],
            'palette_counts':dict(Counter(b.blocks.values()))}

if __name__=='__main__':
    b=build();checks=validate(b);saved=b.save('parts/layout_parking.json')
    notes={'component':'Three observed auxiliary roofs; parking use not independently verified',
      'checks':checks,'source_trace':'references/parking_trace.json',
      'source_images':['references/satellite_south.png','references/satellite_north.png','references/satellite_northwest_native.png'],
      'native_registration':'references/northwest_native_registration.json',
      'observed':['Eastern reddish long roof beside oval.',
                  'Northwest white roof along northern edge of brown rectangle.',
                  'Narrow pale roof along western perimeter of brown rectangle.'],
      'inferred':['Ground64,roof69 and low open steel supports are provisional; actual heights and unseen walls not measured.',
                  'Support/seam spacing6m and andesite paving simplified.',
                  'No cars,bicycles,parking paint,signage,dedicated gate or small white object identity invented.'],
      'northwest_brown_area':'Function,sport lines and bench interpretation remain inferred; not changed by this component.',
      'unbuilt':'Small repeated pale edgeobjects are unclassified and not added as roofs,benches or vehicles.',
      'integration':'Add full component projection to occupied before tree planting. Explicit air only inside new roofmasks65..67. North hall,field,tower,academic and south generator files unchanged.',
      'root_bfs_targets':[[137,65,170],[29,65,21],[9,65,61]],
      'cameras':{'east':{'eye':[131,66.7,180],'target':[139,66.5,167]},
                 'northwest':{'eye':[47,76,38],'target':[27,67,20]},
                 'west':{'eye':[20,67,65],'target':[9,67,61]}}}
    (ROOT/'parts/layout_parking_notes.json').write_text(json.dumps(notes,indent=2),encoding='utf-8')
    print(json.dumps({'saved':saved,'checks':checks},indent=2))
