"""Assemble satellite-traced v3 shells, mapped ground and reusable gate/statue."""
from pathlib import Path
import json,math,hashlib,collections
from voxel import Builder,ROOT

def load(p):
    d=json.loads(p.read_text(encoding='utf-8'))
    return {(x,y,z):d['palette'][i] for x,y,z,i in d['blocks']}

def tree(b,x,z,height=7,radius=3):
    b.fill(x,65,z,x,64+height,z,'oak_log[axis=y]')
    for dy in range(-2,3):
        rr=radius*(1-(abs(dy)/3.1)**1.6)**.5
        for dx in range(-radius,radius+1):
            for dz in range(-radius,radius+1):
                if dx*dx+dz*dz<=rr*rr and not(dx==dz==0 and dy<0):
                    b.set(x+dx,64+height+dy,z+dz,'oak_leaves[distance=1,persistent=true,waterlogged=false]')

def assemble():
    old=ROOT/'parts/gate_reference.json'
    assert old.exists(),'The gate reference must be present before assembly.'
    previous=load(old)
    component_names=('north','academic','south','connectors','parking','garden_a','garden_b','ne_circulation')
    components={name:load(ROOT/'parts'/f'layout_{name}.json') for name in component_names}
    b=Builder('LQD_DaNang_Layout_v3')
    b.fill(-30,63,-30,178,63,238,'dirt')
    b.fill(-30,64,-30,178,64,238,'grass_block[snowy=false]')
    # Road centre lines are the georeference axes, not the campus fence.
    for x in (0,148):
        b.fill(x-4,64,-5,x+4,64,213,'gray_concrete')
        for z in range(-4,214,11):b.fill(x,64,z,x,64,z+4,'white_concrete')
    for z in (0,208):
        b.fill(-4,64,z-4,152,64,z+4,'gray_concrete')
        for x in range(-4,153,11):b.fill(x,64,z,x+4,64,z,'white_concrete')
    for x in (5,143):b.fill(x,64,5,x,64,202,'smooth_stone')
    for z in (5,201):b.fill(5,64,z,143,64,z,'smooth_stone')
    # Interior paths and planted strips read from satellite. Roof geometry is
    # applied afterwards, so paving never replaces building floors.
    b.fill(10,64,10,13,64,195,'andesite')
    b.fill(14,64,102,77,64,107,'andesite')
    b.fill(17,64,113,75,64,118,'andesite')
    b.fill(17,64,134,73,64,138,'andesite')
    b.fill(17,64,146,75,64,150,'andesite')
    b.fill(16,64,137,20,64,149,'andesite')
    b.fill(64,64,173,80,64,199,'bricks')
    for xa,xb in ((49,63),(81,94)):
        for x in range(xa,xb+1):
            for z in range(178,198):
                b.set(x,64,z,'smooth_sandstone' if ((x-xa)//4+(z-178)//4)%2 else 'bricks')
    b.fill(21,64,192,49,64,195,'andesite')
    b.fill(94,64,189,130,64,193,'andesite')
    b.fill(132,64,81,137,64,195,'andesite')
    occupied={(x,z) for c in components.values() for x,y,z in c if y>=64}
    # Sparse observed garden bands rather than a uniform grid over every void.
    candidates=[(15,12),(37,12),(48,12),(94,12),(107,13),
      (13,106),(25,110),(41,110),(56,110),(66,111),
      (14,139),(28,142),(43,142),(57,143),(66,143),
      (91,91),(104,98),(91,109),(109,118),(89,140),(100,141),
      (15,178),(24,180),(31,179),(47,181),(16,190),(27,190),
      (47,191),(91,186),(106,187),(123,185),(132,175),(132,158),
      (135,94),(136,110),(136,129),
      # Representative canopy groups visible in the northeast satellite frame;
      # individual trunks/heights cannot be recovered from the aerial image.
      (96,50),(102,54),(111,59),(118,68),(113,72),(105,71)]
    trees=[]
    for i,(x,z) in enumerate(candidates):
        if any((x+dx,z+dz) in occupied for dx in range(-3,4) for dz in range(-3,4)):continue
        if 33<=x<=43 and 182<=z<=192:continue
        tree(b,x,z,6+i%3,2+i%2);trees.append([x,z])
    # Same confirmed split arch, translated to the mapped southern fence.
    for (x,y,z),s in previous.items():
        if 48<=x<=113 and 202<=z<=206 and y>=65:b.set(x-2,y,z-6,s)
    rail='iron_bars[east=true,north=false,south=false,waterlogged=false,west=true]'
    for z in (7,199):
        for x in range(6,143):
            if z==199 and 46<=x<=111:continue
            b.set(x,65,z,'stone_bricks');b.fill(x,66,z,x,67,z,rail)
            if (x-6)%8==0:b.fill(x,65,z,x,68,z,'smooth_sandstone')
    rail='iron_bars[east=false,north=true,south=true,waterlogged=false,west=false]'
    for x in (6,142):
        for z in range(7,200):
            b.set(x,65,z,'stone_bricks');b.fill(x,66,z,x,67,z,rail)
            if (z-7)%8==0:b.fill(x,65,z,x,68,z,'smooth_sandstone')
    # Restore short fence gaps beside the copied entrance structure.
    for xa,xb in ((6,45),(112,142)):
        b.fill(xa,65,199,xb,65,199,'stone_bricks')
    overlaps=[];owners={}
    for name,c in components.items():
        for pos,s in c.items():
            if pos in owners and b.blocks.get(pos,'air')!=s:overlaps.append([owners[pos],name,*pos,b.blocks.get(pos,'air'),s])
            owners[pos]=name
            if s=='air':b.blocks.pop(pos,None)
            else:b.blocks[pos]=s
    # Provisional game doorway at the traced northern approach. The satellite
    # does not establish a real door here; retain this explicit uncertainty.
    proposed_door=[]
    b.fill(93,64,73,94,64,73,'andesite')
    for x in (93,94):
        for z in range(73,77):
            if (x,64,z) not in components['academic']:continue
            for y in (65,66,67):
                old=b.blocks.pop((x,y,z),None)
                if old is not None:proposed_door.append([x,y,z,old])
    # Statue west of gate, as user confirmed. Exact offset remains provisional.
    for (x,y,z),s in load(ROOT/'parts/detail_statue.json').items():
        assert (x-2,z-6) not in occupied or y<=64,'Statue collides with traced roof.'
        b.set(x-2,y,z-6,s)
    for s in set(b.blocks.values()):assert (ROOT/'vendor/assets/minecraft/blockstates'/f'{s.split("[")[0]}.json').exists(),s
    stats=b.save('campus.json')
    digest=hashlib.sha256((ROOT/'campus.json').read_bytes()).hexdigest()
    report={'version':'layout_v3.3','stats':stats,'campus_sha256':digest,'component_blocks':{k:len(v) for k,v in components.items()},
      'georeference':'references/georeference.json','trees':trees,'junction_overlaps':overlaps,
      'provisional_north_door_removed_blocks':proposed_door,
      'uncertainty':'Manually traced satellite roof masks, approx2.5m; heights/interiors not surveyed.',
      'v1_footprints_preserved':False,'in_game_validation':False}
    (ROOT/'qa/assembly.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'junction_overlaps':len(overlaps)}))
    return b,report

if __name__=='__main__':assemble()
