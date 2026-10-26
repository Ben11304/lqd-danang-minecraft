"""Open connector traced from the current north satellite frame.

This isolated additive component does not identify the space as canteen or sanh C.
Its one-storey height and pier spacing remain provisional.
"""
from pathlib import Path
from collections import Counter
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder

PIXELS=[(595,423),(615,422),(625,521),(606,526)]

def trace():
    g=json.loads((ROOT/'references/georeference.json').read_text(encoding='utf-8'))
    a,b=g['x_axis_pixel_per_m'];c,d=g['z_axis_pixel_per_m']
    ox,oy=g['north_control_origin_pixel'];det=a*d-b*c
    pts=[]
    for px,py in PIXELS:
        u,v=px-ox,py-oy
        pts.append(((d*u-c*v)/det,(-b*u+a*v)/det))
    return {'source_image':'references/satellite_north.png',
            'supporting_crop':'references/canteen_corridor_crop.png',
            'source_pixel_polygon':PIXELS,'world_xz_polygon':pts,
            'purpose':'Visible missing narrow connector roof only; function unknown.',
            'uncertainty_m':2.5,
            'height_evidence':'Satellite roof footprint does not establish height or storeys. One ground-level open walkway and canopy are provisional.',
            'source_snapshot_sha256':'19a1f10431c0e0b841f7941d5ae05f9db67b839d9e46ea36da9d0b2e3ba7c3e4'}

def floor_mask():
    b=Builder('mask');b.polygon(trace()['world_xz_polygon'],64,64,'smooth_stone')
    return {(x,z) for x,y,z in b.blocks}

def build():
    b=Builder('narrow_north_connector_v3');mask=floor_mask()
    # Exact roof projection from satellite; no new courtyard walls.
    for x,z in mask:
        b.set(x,64,z,'smooth_stone')
        b.set(x,69,z,'gray_concrete')
    for z in sorted({z for x,z in mask}):
        xs=sorted(x for x,zz in mask if zz==z)
        left,right=xs[0],xs[-1]
        # Low metal rails with long sides open above them; both joins stay open.
        if 89<=z<=112:
            for x in (left,right):
                b.set(x,65,z,'iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]')
        # Sparse pale piers and shallow overhead beams.
        if z in (90,96,102,108):
            for x in (left,right):
                b.fill(x,65,z,x,68,z,'smooth_sandstone')
            b.fill(left,68,z,right,68,z,'light_gray_concrete')
        # Keep continuous two-block walkable centre and three metres headroom.
        mid=(left+right)//2
        for x in (mid,mid+1):
            if (x,z) in mask:b.fill(x,65,z,x,67,z,'air')
        # Ground joins do not terminate in a new barrier.
        if z<=88 or z>=113:
            for x in xs:b.fill(x,65,z,x,67,z,'air')
    return b

def validate(b):
    mask=floor_mask()
    assert all((x,z) in mask for x,y,z in b.blocks)
    assert all(64<=y<=69 for x,y,z in b.blocks)
    rows={}
    for z in sorted({z for x,z in mask}):
        xs=sorted(x for x,zz in mask if zz==z);mid=(xs[0]+xs[-1])//2
        assert all(b.blocks.get((x,y,z),'air')=='air' for x in (mid,mid+1) for y in (65,66,67))
        rows[z]=[mid,mid+1]
    for s in set(b.blocks.values()):
        assert (ROOT/'vendor/assets/minecraft/blockstates'/(s.split('[')[0]+'.json')).exists(),s
    return {'block_entries':len(b.blocks),'solid_blocks':sum(s!='air' for s in b.blocks.values()),
            'bounds_xyz':[[min(p[i] for p in b.blocks),max(p[i] for p in b.blocks)] for i in range(3)],
            'roof_projection_cells':len(mask),'two_wide_three_high_centre_clear':True,
            'open_end_rows':True,'centre_path_by_z':rows,'palette_counts':dict(Counter(b.blocks.values()))}

if __name__=='__main__':
    t=trace();b=build();report=validate(b)
    (ROOT/'references/connector_trace.json').write_text(json.dumps(t,indent=2),encoding='utf-8')
    saved=b.save('parts/layout_connectors.json')
    notes={'component':'Narrow missing roof connector south of sports complex','checks':report,
           'evidence':['references/satellite_north.png','references/canteen_corridor_crop.png',
                       'private-reference/LQD_DaNang_Minecraft_Research/images/ref_015.jpg'],
           'interpretation':'One-storey ground walkway with pale piers, low metal railing, dark canopy. It follows the satellite polygon. ref015 supports open-sided gallery typology only; its exact correspondence is not geolocated.',
           'inferred':['Roof y69 and floor64; actual height/storey count not measured.',
                       'Pier spacing6m, rail height1m and exact materials simplified.',
                       'Not labelled canteen or sanh C; no east pale rectangle added.'],
           'integration':'Apply component after north/academic so explicit air preserves the two-wide centre and open end joins; no source modules modified.',
           'cameras':{'eye_level':{'eye':[70,66.7,103],'target':[69.5,66.7,89]},
                      'mid':{'eye':[86,78,107],'target':[70,67,100]}}}
    (ROOT/'parts/layout_connectors_notes.json').write_text(json.dumps(notes,indent=2),encoding='utf-8')
    print(json.dumps({'saved':saved,'checks':{k:v for k,v in report.items() if k not in ('centre_path_by_z','palette_counts')}},indent=2))
