"""Official-model voxel preview mesh, retaining the v1 eight-float layout.

Use --check to resolve the campus + detail palettes and run geometry tests
without writing preview files. Normal execution reads one campus snapshot
and emits mesh.bin, a guttered power-of-two atlas and metadata.json.
"""
from pathlib import Path
from functools import lru_cache
from collections import Counter
import argparse
import array
import copy
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.deps'))
import numpy as np
from PIL import Image

ASSETS = ROOT / 'vendor/assets/minecraft'
DIRS = {'east': (1,0,0), 'west':(-1,0,0), 'up':(0,1,0),
        'down':(0,-1,0), 'south':(0,0,1), 'north':(0,0,-1)}
FACE_POINTS = {
    'east':[(1,0,1),(1,0,0),(1,1,0),(1,1,1)],
    'west':[(0,0,0),(0,0,1),(0,1,1),(0,1,0)],
    'up':[(0,1,1),(1,1,1),(1,1,0),(0,1,0)],
    'down':[(0,0,0),(1,0,0),(1,0,1),(0,0,1)],
    'south':[(0,0,1),(1,0,1),(1,1,1),(0,1,1)],
    'north':[(1,0,0),(0,0,0),(0,1,0),(1,1,0)]}
DEFAULTS = {'facing':'north','half':'bottom','shape':'straight','type':'bottom',
            'open':'false','powered':'false','waterlogged':'false','hanging':'false',
            'north':'false','south':'false','east':'false','west':'false',
            'up':'true','down':'true','in_wall':'false','axis':'y','snowy':'false',
            'level':'0','face':'floor','part':'foot','hinge':'left','lit':'true','age':'0'}
MISSING_MODELS=set(); MISSING_TEXTURES=set(); FALLBACKS={}; DEFAULTED={}
USED_FILES={}; WEIGHTED=set(); SPECIALS=set(); UV_OUTSIDE=set()


def sha(data): return hashlib.sha256(data).hexdigest()


def read_json(path):
    raw=path.read_bytes();USED_FILES[str(path.relative_to(ASSETS))]=sha(raw)
    return json.loads(raw)


def split_state(state):
    state=state.removeprefix('minecraft:')
    if '[' not in state:return state,{}
    name,raw=state[:-1].split('[',1)
    return name,dict(item.split('=') for item in raw.split(','))


def rotation(axis,angle):
    a=math.radians(angle);c,s=math.cos(a),math.sin(a)
    if axis=='x':return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    if axis=='y':return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])


@lru_cache(None)
def model(resource):
    resource=resource.removeprefix('minecraft:')
    path=ASSETS/'models'/(resource+'.json')
    if not path.is_file():
        MISSING_MODELS.add(resource);return {}
    local=read_json(path)
    result=copy.deepcopy(model(local['parent'])) if 'parent' in local else {}
    textures=dict(result.get('textures',{}));textures.update(local.get('textures',{}))
    result.update(local);result['textures']=textures
    return result


def resolve_texture(value,textures):
    seen=set()
    while value.startswith('#'):
        if value in seen:return 'block/stone'
        seen.add(value)
        value=textures.get(value[1:],'block/stone')
    return value.removeprefix('minecraft:')


def matches(condition,props):
    if not condition:return True
    for key,value in condition.items():
        if key=='OR':
            if not any(matches(c,props) for c in value):return False
        elif key=='AND':
            if not all(matches(c,props) for c in value):return False
        else:
            wanted=str(value).lower();actual=props.get(key,'')
            if wanted.startswith('!'):
                if actual in wanted[1:].split('|'):return False
            elif actual not in wanted.split('|'):return False
    return True


def condition_keys(condition):
    output=set()
    for key,value in condition.items():
        if key in ('OR','AND'):
            for child in value:output.update(condition_keys(child))
        else:output.add(key)
    return output


@lru_cache(None)
def state_models(state):
    name,props=split_state(state)
    path=ASSETS/'blockstates'/(name+'.json')
    if not path.exists():
        FALLBACKS[state]='missing blockstate';return [],props
    definition=read_json(path)
    required=set()
    for key in definition.get('variants',{}):
        required.update(item.split('=')[0] for item in key.split(',') if item)
    for part in definition.get('multipart',[]):required.update(condition_keys(part.get('when',{})))
    for key in required-props.keys():
        props[key]=DEFAULTS.get(key,'false')
        DEFAULTED.setdefault(state,{})[key]=props[key]
    result=[]
    def selected(value):
        if isinstance(value,list):
            WEIGHTED.add(state);return value[0]
        return value
    for key,value in definition.get('variants',{}).items():
        cond=dict(item.split('=') for item in key.split(',') if item)
        if matches(cond,props):result.append(selected(value));break
    for part in definition.get('multipart',[]):
        if matches(part.get('when',{}),props):result.append(selected(part['apply']))
    if not result:FALLBACKS[state]='no matching variant or multipart'
    return result,props


def default_uv(face,low,high):
    x0,y0,z0=low;x1,y1,z1=high
    return {'down':[x0,16-z1,x1,16-z0], 'up':[x0,z0,x1,z1],
            'north':[16-x1,16-y1,16-x0,16-y0], 'south':[x0,16-y1,x1,16-y0],
            'west':[z0,16-y1,z1,16-y0], 'east':[16-z1,16-y1,16-z0,16-y0]}[face]


def project_uv(face,points):
    x,y,z=np.asarray(points).T
    return {'down':np.stack((x,1-z),axis=1), 'up':np.stack((x,z),axis=1),
            'north':np.stack((1-x,1-y),axis=1), 'south':np.stack((x,1-y),axis=1),
            'west':np.stack((z,1-y),axis=1), 'east':np.stack((1-z,1-y),axis=1)}[face]


def locked_uv(uv,face,transform):
    # Derive the UV-lock affine transform from canonical block face frames.
    # This moves UVs around the sprite centre independently of model vertices,
    # preserving the selected rectangular texture slices under x/y rotations.
    points=np.array(FACE_POINTS[face],dtype=float)
    transformed=(points-.5)@transform.T+.5
    normal=transform@np.array(DIRS[face],dtype=float)
    newface=max(DIRS,key=lambda key:np.dot(DIRS[key],normal))
    old=project_uv(face,points)
    new=project_uv(newface,transformed)
    affine=np.linalg.lstsq(np.column_stack((old,np.ones(4))),new,rcond=None)[0]
    return (np.column_stack((np.asarray(uv)/16,np.ones(4)))@affine)*16


def texture_key(texture,face,name):
    tint=None
    if 'water_still' in texture or 'water_flow' in texture:tint='3f76e4'
    elif int(face.get('tintindex',-1))>=0:
        tint='77ab2f' if 'leaves' in name else '91bd59'
    return (texture,tint)


def synthetic_cube(texture,low=(0,0,0),high=(16,16,16)):
    return {'textures':{'all':texture},'elements':[{'from':low,'to':high,
            'faces':{face:{'texture':'#all','cullface':face} for face in DIRS}}]}


@lru_cache(None)
def geometry(state):
    name,provided=split_state(state)
    if name=='air':return ()
    variants,props=state_models(state)
    special=None
    if name=='water':
        SPECIALS.add('water: flat still-fluid surface at8/9 block; neighbour-aware top/side culling')
        level=int(props.get('level','0'));height=(8-min(level,7))/9 if level<8 else 8/9
        special=synthetic_cube('block/water_still',high=(16,height*16,16))
        variants=[{}]
    elif name.endswith('_wall_sign'):
        SPECIALS.add('wall_sign: thin board geometry; text is rendered separately by HTML')
        wood=name.removesuffix('_wall_sign')
        special=synthetic_cube('block/'+wood+'_planks',low=(0,4,14),high=(16,12,16))
        variants=[{'y':{'north':0,'east':90,'south':180,'west':270}[props.get('facing','north')]}]
    if not variants:
        variants=[{}];special=synthetic_cube('block/stone')
    output=[]
    for variant in variants:
        source=special if special else model(variant.get('model','block/'+name))
        if not source.get('elements'):
            FALLBACKS[state]='model contains no elements';source=synthetic_cube(source.get('textures',{}).get('particle','block/stone'))
        transform=rotation('y',-variant.get('y',0))@rotation('x',-variant.get('x',0))
        textures=source.get('textures',{})
        for element in source['elements']:
            low=np.array(element['from'],dtype=float);high=np.array(element['to'],dtype=float)
            er=element.get('rotation');element_matrix=np.eye(3);element_scale=np.ones(3);origin=np.zeros(3)
            if er:
                element_matrix=rotation(er['axis'],er['angle']);origin=np.array(er['origin'],dtype=float)/16
                if er.get('rescale'):
                    element_scale[:]=1/max(.00001,math.cos(math.radians(er['angle'])))
                    element_scale['xyz'.index(er['axis'])]=1
            for face,definition in element.get('faces',{}).items():
                pts=(low+np.array(FACE_POINTS[face],dtype=float)*(high-low))/16
                if er:pts=((pts-origin)*element_scale)@element_matrix.T+origin
                pts=(pts-.5)@transform.T+.5
                normal=transform@element_matrix@np.array(DIRS[face],dtype=float)
                normal/=np.linalg.norm(normal)
                u0,v0,u1,v1=definition.get('uv',default_uv(face,low,high))
                uv=np.array([(u0,v1),(u1,v1),(u1,v0),(u0,v0)],dtype=float)
                quarter=definition.get('rotation',0)//90
                uv=np.roll(uv,-quarter,axis=0)
                if variant.get('uvlock'):uv=locked_uv(uv,face,transform)
                if uv.min() < -1e-5 or uv.max()>16.00001:UV_OUTSIDE.add(state)
                uv=np.clip(uv,0,16)
                cull=definition.get('cullface')
                if cull:cull=tuple(int(round(v)) for v in transform@np.array(DIRS[cull]))
                texture=resolve_texture(definition.get('texture','#all'),textures)
                key=texture_key(texture,definition,name)
                output.append({'points':pts,'normal':normal,'uv':uv,'cull':cull,'texture':key,'face':face,
                               'glass':('glass' in name)})
    return tuple(output)


def opaque(state):
    name,_=split_state(state)
    if any(token in name for token in ('glass','leaves','water','azalea','bars','slab','stairs','trapdoor',
                                      'carpet','lectern','lantern','sign','door','fern','cauldron')):return False
    quads=geometry(state)
    return any(np.allclose(quad['points'],np.array(FACE_POINTS[quad['face']])) for quad in quads)


def make_atlas(keys,path):
    grid=1
    while grid*grid<len(keys):grid*=2
    tile,content,gutter=64,32,16
    size=grid*tile
    atlas=Image.new('RGBA',(size,size),(128,128,128,255))
    manifest=[]
    for index,(texture,tint) in enumerate(keys):
        source=ASSETS/'textures'/(texture+'.png')
        if not source.is_file():
            MISSING_TEXTURES.add(texture);source=ASSETS/'textures/block/stone.png'
        raw=source.read_bytes();USED_FILES[str(source.relative_to(ASSETS))]=sha(raw)
        image=Image.open(source).convert('RGBA')
        image=image.crop((0,0,image.width,image.width)).resize((content,content),Image.Resampling.NEAREST)
        pixels=np.array(image)
        if tint:
            rgb=np.array([int(tint[i:i+2],16) for i in (0,2,4)],dtype=float)/255
            pixels[:,:,:3]=(pixels[:,:,:3]*rgb).astype(np.uint8)
        if texture.startswith('block/water_'):pixels[:,:,3]=255
        image=Image.fromarray(pixels)
        # Replicate all edge pixels and corners across the full16px gutter.
        padded=Image.fromarray(np.pad(np.array(image),((gutter,gutter),(gutter,gutter),(0,0)),mode='edge'))
        atlas.paste(padded,((index%grid)*tile,(index//grid)*tile))
        manifest.append({'index':index,'texture':texture,'tint':tint,'sha256':sha(raw),
                         'content_pixel_rect':[(index%grid)*tile+gutter,(index//grid)*tile+gutter,content,content]})
    atlas.save(path)
    return grid,manifest


def validate_geometry(states):
    tests={}
    checkstates=['oak_slab[type=bottom,waterlogged=false]','oak_slab[type=top,waterlogged=false]',
        'light_blue_carpet','spruce_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]',
        'black_stained_glass_pane[east=true,north=false,south=false,west=true,waterlogged=false]',
        'lectern[facing=south,has_book=false,powered=false]','lantern[hanging=false,waterlogged=false]',
        'potted_fern','water_cauldron[level=2]','oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]']
    for state in sorted(set(states)|set(checkstates)):
        quads=geometry(state)
        if split_state(state)[0]!='air':assert quads,state
        for quad in quads:
            assert np.isfinite(quad['points']).all() and np.isfinite(quad['uv']).all(),state
            assert abs(np.linalg.norm(quad['normal'])-1)<1e-6,state
        if state in checkstates:
            points=np.concatenate([q['points'] for q in quads])
            tests[state]={'quads':len(quads),'bounds':[points.min(axis=0).round(6).tolist(),points.max(axis=0).round(6).tolist()]}
    assert abs(tests[checkstates[0]]['bounds'][1][1]-.5)<1e-6
    assert abs(tests[checkstates[1]]['bounds'][0][1]-.5)<1e-6
    assert abs(tests[checkstates[2]]['bounds'][1][1]-.0625)<1e-6
    assert tests[checkstates[5]]['quads']>=14
    assert any(abs(q['normal'][1])>.1 and abs(q['normal'][2])>.1 for q in geometry(checkstates[5]))
    return tests


def report_missing():
    return {'missing_models':sorted(MISSING_MODELS),'missing_textures':sorted(MISSING_TEXTURES),
            'fallback_states':dict(sorted(FALLBACKS.items())),'defaulted_properties':DEFAULTED,
            'uv_outside_sprite_states':sorted(UV_OUTSIDE)}


def main(check=False):
    snapshot=(ROOT/'campus.json').read_bytes();data=json.loads(snapshot);palette=data['palette']
    allstates=set(palette)
    for path in (ROOT/'parts').glob('detail_*.json'):
        if not path.name.endswith('_notes.json'):allstates.update(json.loads(path.read_text(encoding='utf-8')).get('palette',[]))
    tests=validate_geometry(allstates)
    if check:
        print(json.dumps({'mode':'check only; no files written','campus_states':len(palette),'detail_union_states':len(allstates),
                          'geometry_tests':tests,**report_missing()},indent=2));return
    vox={(x,y,z):idx for x,y,z,idx in data['blocks'] if split_state(palette[idx])[0]!='air'}
    geometries=[geometry(state) for state in palette]
    keys=sorted({quad['texture'] for quads in geometries for quad in quads},key=lambda k:(k[0],k[1] or ''))
    destination=ROOT/'preview';destination.mkdir(exist_ok=True)
    grid,manifest=make_atlas(keys,destination/'atlas.png')
    texture_indices={key:i for i,key in enumerate(keys)}
    occludes=[opaque(state) for state in palette]
    names=[split_state(state)[0] for state in palette]
    buffers=[array.array('f'),array.array('f')];facecount=0;faces_by_state=Counter()
    for (x,y,z),idx in vox.items():
        state=palette[idx];name=names[idx]
        for quad in geometries[idx]:
            cull=quad['cull']
            if cull:
                nx,ny,nz=cull
                if ny<0 and y<=64:continue
                neighbor=vox.get((x+nx,y+ny,z+nz))
                if neighbor is not None:
                    if occludes[neighbor]:continue
                    if names[neighbor]==name and ('glass' in name or 'leaves' in name or name=='water'):continue
            if name=='water' and quad['face']=='down':continue
            points=quad['points'].copy()
            if name=='water' and names[vox[(x,y+1,z)]]=='water' if (x,y+1,z) in vox else False:
                points[points[:,1]>.5,1]=1
            ti=texture_indices[quad['texture']];tx,ty=ti%grid,ti//grid
            u=(tx*64+16+quad['uv'][:,0]*2)/(grid*64)
            v=1-(ty*64+16+quad['uv'][:,1]*2)/(grid*64)
            normal=quad['normal'];target=buffers[1 if quad['glass'] else 0]
            for j in (0,1,2,0,2,3):
                px,py,pz=points[j]
                target.extend((x+px,y+py-64,z+pz,*normal,u[j],v[j]))
            facecount+=1;faces_by_state[state]+=1
    opaque_vertices=len(buffers[0])//8;glass_vertices=len(buffers[1])//8
    mesh=buffers[0].tobytes()+buffers[1].tobytes()
    (destination/'mesh.bin').write_bytes(mesh)
    metadata={'blocks':len(vox),'faces':facecount,'vertices':opaque_vertices+glass_vertices,'stride':8,
        'endianness':'little','palette':palette,'source':'campus.json; exact elements and UVs from official Java1.20.4 client assets',
        'source_sha256':sha(snapshot),'source_unchanged_during_render':snapshot==(ROOT/'campus.json').read_bytes(),
        'renderer_sha256':sha(Path(__file__).read_bytes()),'mesh_sha256':sha(mesh),
        'atlas_sha256':sha((destination/'atlas.png').read_bytes()),
        'asset_set_sha256':sha(json.dumps(USED_FILES,sort_keys=True).encode()),
        'atlas':{'width':grid*64,'height':grid*64,'grid':grid,'tile_pixels':64,'content_pixels':32,'gutter_pixels':16,
                 'magFilter':'NearestFilter','minFilter':'NearestMipmapLinearFilter','generateMipmaps':True,
                 'textures':manifest},
        'meshGroups':[{'start':0,'count':opaque_vertices,'materialIndex':0,'name':'opaque_and_alpha_cutout'},
                      {'start':opaque_vertices,'count':glass_vertices,'materialIndex':1,'name':'transparent_glass'}],
        'materials':{'0':{'alphaTest':.35,'side':'DoubleSide'},
                     '1':{'transparent':True,'opacity':1,'depthWrite':False,'alphaTest':0,'side':'DoubleSide'}},
        'geometry_tests':tests,'faces_by_state':dict(faces_by_state),**report_missing(),
        'special_geometry':sorted(SPECIALS),'weighted_variants_deterministic_first':sorted(WEIGHTED),
        'limitations':['Preview lighting is not the Minecraft light engine; no per-vertex AO is baked into stride8.',
                      'Water uses a still flat8/9 surface, not neighbour-averaged fluid corner slopes or animated texture frames.',
                      'Wall-sign board geometry is procedural; its text is supplied by the HTML sign overlay.',
                      'Biome tint uses a fixed plains-like palette; weighted texture variants choose their first deterministic model.',
                      'Transparent glass uses a separate material pass; intersecting transparent surfaces retain Three.js sorting limits.']}
    (destination/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'blocks':len(vox),'faces':facecount,'vertices':metadata['vertices'],'mesh_MB':round(len(mesh)/1e6,2),
        'atlas_size':grid*64,'texture_slots':len(keys),'meshGroups':metadata['meshGroups'],**report_missing()},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true')
    main(parser.parse_args().check)
