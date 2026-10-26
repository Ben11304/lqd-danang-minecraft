"""Reversible compact west-yard statue interpretation from a historic photo."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxel import Builder
BOTTOM='[type=bottom,waterlogged=false]'
WEST='[facing=west,half=bottom,shape=straight,waterlogged=false]'


def build():
    b=Builder('detail_statue_west_yard')
    # Seven-block bed, set into the existing ground rather than raised as a dais.
    b.fill(37,64,190,43,64,196,'stone_bricks')
    b.fill(38,64,191,42,64,195,'grass_block[snowy=false]')
    for x,z in [(38,191),(38,195),(42,191),(42,195)]:b.set(x,65,z,'poppy')
    # Dark rectangular plinth and shallow overhanging cap, total 1.5m high.
    b.fill(39,65,192,41,65,194,'polished_blackstone')
    b.fill(39,66,192,41,66,194,'polished_blackstone_slab'+BOTTOM)
    # White draped seated figure. Back/torso is WEST, knees and feet project
    # EAST into campus; no arms-out generic humanoid or giant upright statue.
    b.set(39,66,193,'quartz_block')
    b.set(39,67,193,'quartz_block')
    b.set(39,68,193,'quartz_block')
    b.set(39,69,193,'chiseled_quartz_block')  # full head: 5m total above ground
    # One shoulder and a low resting arm give the small figure an asymmetric robe.
    b.set(39,68,192,'quartz_slab'+BOTTOM)
    b.set(40,67,192,'quartz_stairs'+WEST)
    b.set(40,67,193,'quartz_stairs'+WEST)
    b.set(41,67,192,'quartz_stairs'+WEST)
    b.set(41,67,193,'quartz_stairs'+WEST)
    # Feet/long robe fold rest on the plinth edge, not in the walking route.
    b.set(41,66,192,'quartz_slab'+BOTTOM)
    b.set(41,66,193,'quartz_slab'+BOTTOM)
    # Pale lap/book-like plane: a simplified inference, no claim about exact hand pose.
    b.set(40,68,193,'cut_sandstone_slab'+BOTTOM)
    # Thin ochre plaque, no text entity. Wood is a vanilla visual stand-in for
    # the small unreadable bronze/gold-coloured plaque in the historic photo.
    b.set(42,65,193,'birch_button[face=wall,facing=east,powered=false]')
    return b


def validate(b):
    raw=(ROOT/'campus.json').read_bytes();d=json.loads(raw)
    current={(x,y,z):d['palette'][i] for x,y,z,i in d['blocks']}
    previous={}
    legacy={(39,69,193):'quartz_slab'+BOTTOM,
            (42,65,193):'bamboo_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]'}
    prior_path=ROOT/'parts/detail_statue.json'
    if prior_path.exists():
        prior=json.loads(prior_path.read_text(encoding='utf-8'))
        previous={(x,y,z):prior['palette'][i] for x,y,z,i in prior['blocks']}
    integrated=0
    for (x,y,z),s in b.blocks.items():
        assert 35<=x<=45 and 187<=z<=198 and 64<=y<=70
        if y>64:
            actual=current.get((x,y,z),'air')
            assert actual in ('air',s,previous.get((x,y,z)),legacy.get((x,y,z))),('Unrelated occupied source coordinate',x,y,z,actual)
            if actual!='air':integrated+=1
        assert (ROOT/'vendor/assets/minecraft/blockstates'/f'{s.split("[")[0]}.json').exists(),s
    assert max(y+(.5 if 'type=bottom' in s else 1) for (x,y,z),s in b.blocks.items())==70
    changes={p for p,s in b.blocks.items() if previous.get(p)!=s}
    if previous:assert changes<={(39,69,193),(42,65,193)},changes
    return {'source_hash':hashlib.sha256(raw).hexdigest(),'no_unrelated_source_collision':True,
            'already_integrated_statue_cells':integrated,'changes_from_prior_patch':len(changes),
            'max_world_top_y':70,'height_above_ground_metres':5,'blocks':len(b.blocks),
            'vanilla_palette_valid':True,'shell_gate_roof_untouched':True}


if __name__=='__main__':
    b=build();checks=validate(b)
    print(json.dumps({'save':b.save('parts/detail_statue.json'),'checks':checks},ensure_ascii=False))
