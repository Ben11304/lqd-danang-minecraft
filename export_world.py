"""Export the current campus snapshot to Java 1.20.4 and Sponge v2.

No game/server is launched and no installed save folder is touched. The
post-export checks use nbtlib's parser and separate decoding loops to read
the serialized files back, including every placed source block.
"""
from pathlib import Path
import collections
import gzip
import hashlib
import io
import json
import math
import struct
import sys
import time
import zipfile
import zlib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.deps'))
import numpy as np
import nbtlib as nbt
from nbtlib import tag as T

DATA_VERSION = 3700
MC_VERSION = '1.20.4'
OUT = ROOT / 'exports'
WORLD = OUT / 'LQD_DaNang_Layout_v3_Java_1_20_4'
VALIDATION = OUT / 'qa/export_validation.json'
MIN_Y, MAX_Y = -64, 319
SPEC = 'https://raw.githubusercontent.com/SpongePowered/Schematic-Specification/master/versions/schematic-2.md'


def split_state(state):
    state = state.removeprefix('minecraft:')
    if '[' not in state:
        return state, {}
    name, raw = state[:-1].split('[', 1)
    return name, dict(s.split('=') for s in raw.split(','))


def canonical(state):
    name, props = split_state(state)
    return 'minecraft:' + name + ('[' + ','.join(f'{k}={v}' for k, v in sorted(props.items())) + ']' if props else '')


def state_tag(state):
    name, props = split_state(state)
    result = T.Compound({'Name': T.String('minecraft:' + name)})
    if props:
        result['Properties'] = T.Compound({k: T.String(v) for k, v in sorted(props.items())})
    return result


def tag_state(value):
    name = str(value['Name'])
    props = {str(k): str(v) for k, v in value.get('Properties', {}).items()}
    return canonical(name + ('[' + ','.join(f'{k}={v}' for k, v in props.items()) + ']' if props else ''))


def pack_long_values(values, bits):
    """Post-1.16 aligned packing: entries never straddle a 64-bit boundary."""
    per = 64 // bits
    values = np.asarray(values, dtype=np.uint64).reshape(-1)
    words = np.zeros((len(values) + per - 1) // per, dtype=np.uint64)
    for offset in range(per):
        part = values[offset::per]
        words[:len(part)] |= part << np.uint64(offset * bits)
    return T.LongArray(words.view(np.int64))


def read_packed(data, count, bits):
    # Separate deliberately scalar decoder, also handles signed NBT longs.
    per, mask = 64 // bits, (1 << bits) - 1
    out = np.empty(count, dtype=np.uint16)
    for index in range(count):
        word = int(data[index // per]) & ((1 << 64) - 1)
        out[index] = (word >> ((index % per) * bits)) & mask
    return out


def raw_nbt(compound, root_name=''):
    buffer = io.BytesIO()
    nbt.File(compound, root_name=root_name).write(buffer)
    return buffer.getvalue()


def validate_assets(states):
    """Verify names and model-visible state values against the official jar.

    Non-rendered water/leaf/waterlogged properties do not occur in model
    blockstates; these receive explicit boolean/range checks, reported apart.
    """
    base = ROOT / 'vendor/assets/minecraft/blockstates'
    hidden = []
    checked = []
    for state in states:
        name, props = split_state(state)
        path = base / (name + '.json')
        assert path.is_file(), f'No official blockstate asset: {name}'
        obj = json.loads(path.read_text())
        domains = collections.defaultdict(set)
        for variant in obj.get('variants', {}):
            if variant:
                for field in variant.split(','):
                    key, value = field.split('=')
                    domains[key].add(value)
        def when_values(value):
            if not isinstance(value, dict):
                return
            for key, val in value.items():
                if key in ('OR', 'AND'):
                    for child in val:
                        when_values(child)
                else:
                    domains[key].update(str(val).split('|'))
        for part in obj.get('multipart', []):
            when_values(part.get('when', {}))
        for key, value in props.items():
            if key in domains:
                assert value in domains[key], (state, key, domains[key])
            else:
                waterloggable = (name.endswith(('_leaves','_stairs','_slab','_wall_sign',
                                                '_trapdoor','_pane','_fence','_wall'))
                                 or name in ('iron_bars','lantern','soul_lantern','chain'))
                legal = ((key == 'waterlogged' and waterloggable and value in ('true', 'false'))
                         or (name.endswith('_leaves') and key == 'persistent' and value in ('true', 'false'))
                         or (name.endswith('_leaves') and key == 'distance' and value in map(str, range(1, 8)))
                         or (name == 'water' and key == 'level' and value in map(str, range(16))))
                legal = legal or (name.endswith('_wall_sign') and key == 'facing' and value in ('east','west','north','south'))
                # Client model assets omit these actual Java boolean states.
                # Empty, unpowered lecterns require no book block-entity data;
                # reject true here rather than silently writing an empty book.
                legal = legal or (name == 'lectern' and key in ('powered','has_book') and value == 'false')
                legal = legal or (name.endswith('_trapdoor') and key == 'powered' and value in ('true','false'))
                assert legal, ('Unverified hidden property', state, key)
                hidden.append({'state': state, 'property': key,
                               'accepted_value':value,
                               'check':'block-specific vanilla property allowlist and boolean/range validation; absent from model variants'})
        checked.append(state)
    manifest = json.loads((ROOT / 'vendor/asset_sources.json').read_text())
    jar_sha = hashlib.sha1((ROOT / 'vendor/client-1.20.4.jar').read_bytes()).hexdigest()
    assert jar_sha == manifest['client']['sha1']
    with zipfile.ZipFile(ROOT / 'vendor/client-1.20.4.jar') as archive:
        version = json.loads(archive.read('version.json'))
    assert version['world_version'] == DATA_VERSION and version['id'] == MC_VERSION
    return {'unique_states': len(checked), 'official_assets_version': MC_VERSION,
            'official_client_sha1_verified': jar_sha, 'official_version_json_DataVersion_verified':version['world_version'],
            'model_invisible_property_checks': hidden,
            'validation_scope':'Official client models validate names/rendered values; explicit block-specific domains validate omitted properties. No Java server registry or game launch was used.',
            'hidden_property_policy':{'waterlogged':'true|false on stairs/slabs/leaves/wall signs/trapdoors/panes/fences/walls/iron bars/lanterns/chains only',
                                      'lectern.powered':'false only','lectern.has_book':'false only',
                                      'trapdoors.powered':'true|false',
                                      'leaves.persistent':'true|false','leaves.distance':'1..7','water.level':'0..15'}}


def make_section(sy, values, states):
    unique, inverse = np.unique(values, return_inverse=True)
    content = {'palette': T.List[T.Compound]([state_tag(states[int(i)]) for i in unique])}
    if len(unique) > 1:
        content['data'] = pack_long_values(inverse, max(4, (len(unique) - 1).bit_length()))
    return T.Compound({'Y': T.Byte(sy), 'block_states': T.Compound(content),
                       'biomes': T.Compound({'palette': T.List[T.String](['minecraft:plains'])})})


def sign_body(entry):
    def face(lines):
        return T.Compound({'messages': T.List[T.String]([json.dumps({'text':str(v)},ensure_ascii=False) for v in lines]),
                           'color':T.String('black'),'has_glowing_text':T.Byte(0)})
    return {'front_text':face(entry['lines']), 'back_text':face(['']*4), 'is_waxed':T.Byte(1)}


def make_chunk(cx, cz, overrides, states, lookup, signs):
    dense = np.full((384, 16, 16), lookup['minecraft:air'], dtype=np.uint16)
    dense[0, :, :] = lookup['minecraft:bedrock']
    dense[1:125, :, :] = lookup['minecraft:stone']
    dense[125:128, :, :] = lookup['minecraft:dirt']
    dense[128, :, :] = lookup['minecraft:grass_block[snowy=false]']
    for x, y, z, state in overrides:
        assert MIN_Y <= y <= MAX_Y
        dense[y - MIN_Y, z & 15, x & 15] = lookup[state]
    sections = [make_section(sy, dense[(sy + 4) * 16:(sy + 5) * 16], states) for sy in range(-4, 20)]
    heightmaps = {}
    for name, excluded in [('WORLD_SURFACE', {'minecraft:air'}),
                           ('MOTION_BLOCKING', {'minecraft:air'}),
                           ('OCEAN_FLOOR', {'minecraft:air', 'minecraft:water[level=0]'}),
                           ('MOTION_BLOCKING_NO_LEAVES', {'minecraft:air', 'minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]'})]:
        skip = [lookup[s] for s in excluded if s in lookup]
        valid = ~np.isin(dense, skip)
        heights = 384 - np.argmax(valid[::-1], axis=0)
        heightmaps[name] = pack_long_values(heights.reshape(-1), 9)
    entities=[]
    for entry in signs:
        x,y,z=entry['pos']
        if (x//16,z//16)==(cx,cz):
            entities.append(T.Compound({'id':T.String('minecraft:sign'),'x':T.Int(x),'y':T.Int(y),'z':T.Int(z),**sign_body(entry)}))
    compound = T.Compound({'DataVersion': T.Int(DATA_VERSION), 'xPos': T.Int(cx), 'zPos': T.Int(cz),
                           'yPos': T.Int(-4), 'Status': T.String('minecraft:full'),
                           'LastUpdate': T.Long(0), 'InhabitedTime': T.Long(0),
                           'isLightOn': T.Byte(0), 'sections': T.List[T.Compound](sections),
                           'Heightmaps': T.Compound(heightmaps),
                           'block_entities': T.List[T.Compound](entities),
                           'block_ticks': T.List[T.Compound]([]), 'fluid_ticks': T.List[T.Compound]([]),
                           'PostProcessing': T.List[T.List[T.Short]]([T.List[T.Short]([]) for _ in sections]),
                           'structures': T.Compound({'starts': T.Compound({}), 'References': T.Compound({})})})
    return zlib.compress(raw_nbt(compound), 6)


def write_regions(chunks):
    groups = collections.defaultdict(dict)
    for (cx, cz), payload in chunks.items():
        groups[(cx // 32, cz // 32)][(cx & 31) + (cz & 31) * 32] = payload
    paths = []
    for (rx, rz), content in groups.items():
        locations, timestamps = bytearray(4096), bytearray(4096)
        body = bytearray()
        offset = 2
        for index, payload in sorted(content.items()):
            record = struct.pack('>I', len(payload) + 1) + b'\x02' + payload
            sectors = (len(record) + 4095) // 4096
            assert sectors <= 255
            locations[index * 4:index * 4 + 4] = ((offset << 8) | sectors).to_bytes(4, 'big')
            timestamps[index * 4:index * 4 + 4] = int(time.time()).to_bytes(4, 'big')
            body.extend(record + bytes(sectors * 4096 - len(record)))
            offset += sectors
        path = WORLD / 'region' / f'r.{rx}.{rz}.mca'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(locations + timestamps + body)
        paths.append(path)
    return paths


def make_level():
    dims = {
        'minecraft:overworld': T.Compound({'type': T.String('minecraft:overworld'), 'generator': T.Compound({
            'type': T.String('minecraft:flat'), 'settings': T.Compound({
                'biome': T.String('minecraft:plains'), 'features': T.Byte(0), 'lakes': T.Byte(0),
                'structure_overrides': T.List[T.String]([]),
                'layers': T.List[T.Compound]([T.Compound({'height': T.Int(h), 'block': T.String(s)}) for h, s in
                    [(1,'minecraft:bedrock'),(124,'minecraft:stone'),(3,'minecraft:dirt'),(1,'minecraft:grass_block')]])})})}),
        'minecraft:the_nether': T.Compound({'type': T.String('minecraft:the_nether'), 'generator': T.Compound({
            'type': T.String('minecraft:noise'), 'settings': T.String('minecraft:nether'),
            'biome_source': T.Compound({'type': T.String('minecraft:multi_noise'), 'preset': T.String('minecraft:nether')})})}),
        'minecraft:the_end': T.Compound({'type': T.String('minecraft:the_end'), 'generator': T.Compound({
            'type': T.String('minecraft:noise'), 'settings': T.String('minecraft:end'),
            'biome_source': T.Compound({'type': T.String('minecraft:the_end')})})})}
    data = T.Compound({'DataVersion': T.Int(DATA_VERSION), 'version': T.Int(19133),
        'Version': T.Compound({'Id': T.Int(DATA_VERSION), 'Name': T.String(MC_VERSION), 'Snapshot': T.Byte(0), 'Series': T.String('main')}),
        'LevelName': T.String('LQD Da Nang - Layout v3 - Java reference 1.20.4'),
        'LastPlayed': T.Long(int(time.time() * 1000)), 'Time': T.Long(6000), 'DayTime': T.Long(6000),
        'SpawnX': T.Int(65), 'SpawnY': T.Int(65), 'SpawnZ': T.Int(204), 'SpawnAngle': T.Float(180),
        'GameType': T.Int(1), 'allowCommands': T.Byte(1), 'hardcore': T.Byte(0),
        'Difficulty': T.Byte(0), 'DifficultyLocked': T.Byte(1), 'initialized': T.Byte(1), 'WasModded': T.Byte(0),
        'raining': T.Byte(0), 'thundering': T.Byte(0), 'rainTime': T.Int(2147483647),
        'thunderTime': T.Int(2147483647), 'clearWeatherTime': T.Int(2147483647),
        'GameRules': T.Compound({k:T.String(v) for k,v in {'doDaylightCycle':'false','doWeatherCycle':'false',
            'doMobSpawning':'false','doFireTick':'false','randomTickSpeed':'0','keepInventory':'true','spawnRadius':'0'}.items()}),
        'WorldGenSettings': T.Compound({'seed': T.Long(0), 'generate_features': T.Byte(0), 'bonus_chest': T.Byte(0), 'dimensions': T.Compound(dims)}),
        'DataPacks': T.Compound({'Enabled': T.List[T.String](['vanilla']), 'Disabled': T.List[T.String]([])}),
        'enabled_features': T.List[T.String](['minecraft:vanilla']),
        'BorderCenterX': T.Double(75), 'BorderCenterZ': T.Double(107), 'BorderSize': T.Double(59999968)})
    nbt.File({'Data': data}, gzipped=True).save(str(WORLD / 'level.dat'))


def varints(values):
    if int(values.max(initial=0)) < 128:
        return values.astype(np.uint8).tobytes()
    output = bytearray()
    for value in values:
        value = int(value)
        while value > 127:
            output.append((value & 127) | 128)
            value >>= 7
        output.append(value)
    return bytes(output)


def make_schematic(source, path, signs):
    blocks, original = source['blocks'], source['palette']
    low = [min(b[i] for b in blocks) for i in range(3)]
    high = [max(b[i] for b in blocks) for i in range(3)]
    width, height, length = [high[i] - low[i] + 1 for i in range(3)]
    states = ['minecraft:air'] + sorted({canonical(s) for s in original} - {'minecraft:air'})
    lookup = {s:i for i,s in enumerate(states)}
    grid = np.zeros((height, length, width), dtype=np.uint16)
    for x,y,z,p in blocks:
        grid[y-low[1],z-low[2],x-low[0]] = lookup[canonical(original[p])]
    data = varints(grid.reshape(-1))
    source_coords={(x,y,z):original[p] for x,y,z,p in blocks}
    entities=[]
    for entry in signs:
        pos=entry['pos']
        if 'wall_sign' in source_coords.get(tuple(pos),''):
            entities.append(T.Compound({'Id':T.String('minecraft:sign'),
                'Pos':T.IntArray([pos[i]-low[i] for i in range(3)]),**sign_body(entry)}))
    tag = {'Version': T.Int(2), 'DataVersion': T.Int(DATA_VERSION),
        'Metadata': T.Compound({'Name': T.String(source['name']), 'Author': T.String('User-directed LQD reference reconstruction'),
                              'Date': T.Long(int(time.time()*1000)), 'RequiredMods': T.List[T.String]([])}),
        'Width': T.Short(width), 'Height': T.Short(height), 'Length': T.Short(length),
        'Offset': T.IntArray(low), 'PaletteMax': T.Int(len(states)),
        'Palette': T.Compound({s:T.Int(i) for s,i in lookup.items()}),
        'BlockData': T.ByteArray(np.frombuffer(data,dtype=np.int8)),
        'BlockEntities': T.List[T.Compound](entities), 'Entities': T.List[T.Compound]([]),
        'BiomePaletteMax': T.Int(1), 'BiomePalette': T.Compound({'minecraft:plains': T.Int(0)}),
        'BiomeData': T.ByteArray(np.zeros(width*length,dtype=np.int8))}
    nbt.File(tag, root_name='Schematic', gzipped=True).save(str(path))
    return {'path':str(path), 'dimensions_xyz':[width,height,length], 'offset_xyz':low,
            'volume':int(grid.size), 'non_air':int(np.count_nonzero(grid)), 'palette_size':len(states),'sign_entities':len(entities)}


def validate_schematic(path, source, signs):
    doc = nbt.load(str(path))
    assert doc.root_name == 'Schematic' and int(doc['Version']) == 2 and int(doc['DataVersion']) == DATA_VERSION
    assert str(doc['Metadata']['Name']) == source['name']
    w,h,l = [int(doc[k]) for k in ('Width','Height','Length')]
    assert len(doc['BiomeData']) == w*l
    palette = {int(v):str(k) for k,v in doc['Palette'].items()}
    assert set(palette) == set(range(int(doc['PaletteMax'])))
    raw = bytes(np.asarray(doc['BlockData'],dtype=np.int8))
    decoded, value, shift = [], 0, 0
    for item in raw:
        value |= (item & 127) << shift
        if item & 128:
            shift += 7
            assert shift < 35
        else:
            assert value in palette
            decoded.append(value)
            value, shift = 0, 0
    assert shift == 0 and len(decoded) == w*h*l
    low = [int(v) for v in doc['Offset']]
    for x,y,z,p in source['blocks']:
        index = (x-low[0]) + (z-low[2])*w + (y-low[1])*w*l
        assert palette[decoded[index]] == canonical(source['palette'][p]), (path,x,y,z)
    for entity in doc['BlockEntities']:
        pos=tuple(int(entity['Pos'][i])+low[i] for i in range(3))
        match=next(s for s in signs if tuple(s['pos'])==pos)
        assert [json.loads(str(v))['text'] for v in entity['front_text']['messages']]==match['lines']
        assert int(entity['is_waxed'])==1 and str(entity['Id'])=='minecraft:sign'
    return {'file':path.name, 'decoded_entries':len(decoded), 'source_blocks_compared':len(source['blocks']),
            'nbt_readback':'passed', 'varint_palette_order_and_offset':'passed'}


def validate_world(paths, source, cx_range, cz_range, signs):
    expected = {(x,y,z):canonical(source['palette'][p]) for x,y,z,p in source['blocks']}
    per_chunk = collections.defaultdict(list)
    for coord,state in expected.items():
        per_chunk[(coord[0]//16, coord[2]//16)].append((*coord,state))
    seen, compared, base_samples, sky_sections = set(),0,0,0
    sign_positions=set()
    region_reports = []
    for path in paths:
        _,rx,rz,_ = path.name.split('.')
        rx,rz = int(rx),int(rz)
        raw = path.read_bytes()
        assert len(raw)%4096 == 0 and len(raw)>=8192
        used = {0,1}
        local_count=0
        for index in range(1024):
            record = int.from_bytes(raw[index*4:index*4+4],'big')
            if not record:
                continue
            off,sectors=record>>8,record&255
            assert off>=2 and sectors>0 and (off+sectors)*4096<=len(raw)
            allocated=set(range(off,off+sectors))
            assert not used.intersection(allocated)
            used.update(allocated)
            size = int.from_bytes(raw[off*4096:off*4096+4],'big')
            assert 1<size<=sectors*4096-4 and raw[off*4096+4]==2
            doc=nbt.File.parse(io.BytesIO(zlib.decompress(raw[off*4096+5:off*4096+4+size])))
            cx,cz=rx*32+index%32,rz*32+index//32
            assert (int(doc['xPos']),int(doc['zPos']))==(cx,cz)
            assert int(doc['DataVersion'])==DATA_VERSION and int(doc['yPos'])==-4
            assert str(doc['Status'])=='minecraft:full'
            for entity in doc['block_entities']:
                pos=tuple(int(entity[k]) for k in ('x','y','z'))
                match=next(s for s in signs if tuple(s['pos'])==pos)
                assert str(entity['id'])=='minecraft:sign' and int(entity['is_waxed'])==1
                assert [json.loads(str(v))['text'] for v in entity['front_text']['messages']]==match['lines']
                assert str(entity['front_text']['color'])=='black' and int(entity['front_text']['has_glowing_text'])==0
                assert len(entity['back_text']['messages'])==4
                sign_positions.add(pos)
            sections={int(s['Y']):s for s in doc['sections']}
            assert set(sections)==set(range(-4,20))
            decoded={}
            for sy,section in sections.items():
                assert str(section['biomes']['palette'][0])=='minecraft:plains'
                content=section['block_states']
                palette=[tag_state(s) for s in content['palette']]
                indices=read_packed(content['data'],4096,max(4,(len(palette)-1).bit_length())) if len(palette)>1 else np.zeros(4096,dtype=np.uint16)
                assert int(indices.max())<len(palette)
                decoded[sy]=(indices,palette)
                if sy>=7:
                    assert palette==['minecraft:air']
                    sky_sections+=1
            def block(x,y,z):
                indices,palette=decoded[y//16]
                return palette[int(indices[((y&15)*256)+((z&15)*16)+(x&15)])]
            for x,y,z,state in per_chunk.get((cx,cz),[]):
                assert block(x,y,z)==state,(x,y,z,state,block(x,y,z))
                compared+=1
            for y,state in [(-64,'minecraft:bedrock'),(-63,'minecraft:stone'),(60,'minecraft:stone'),(61,'minecraft:dirt'),(63,'minecraft:dirt')]:
                x,z=cx*16,cz*16
                state=expected.get((x,y,z),state)
                assert block(x,y,z)==state
                base_samples+=1
            for name,data in doc['Heightmaps'].items():
                heights=read_packed(data,256,9)
                assert np.all((heights>=1)&(heights<=384))
                excluded={'minecraft:air'}
                if name=='OCEAN_FLOOR':excluded.add('minecraft:water[level=0]')
                if name=='MOTION_BLOCKING_NO_LEAVES':
                    excluded.add('minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]')
                # Build predicates from independently decoded section palettes.
                mask=[]
                for sy in range(-4,20):
                    indices,palette=decoded[sy]
                    solid=np.array([value not in excluded for value in palette],dtype=bool)
                    mask.append(solid[indices].reshape(16,16,16))
                dense_mask=np.concatenate(mask,axis=0)
                expected_heights=(384-np.argmax(dense_mask[::-1],axis=0)).reshape(-1)
                assert np.array_equal(heights,expected_heights),(path,cx,cz,name)
            assert (cx,cz) not in seen
            seen.add((cx,cz));local_count+=1
        region_reports.append({'file':path.name,'chunks':local_count,'bytes':len(raw),'allocation_non_overlapping':True})
    required={(cx,cz) for cx in cx_range for cz in cz_range}
    assert seen==required
    assert sign_positions=={tuple(s['pos']) for s in signs}
    level=nbt.load(str(WORLD/'level.dat'))['Data']
    assert 'Player' not in level and int(level['DataVersion'])==DATA_VERSION
    assert str(level['LevelName'])=='LQD Da Nang - Layout v3 - Java reference 1.20.4'
    assert int(level['GameType'])==1 and int(level['SpawnY'])==65
    layers=level['WorldGenSettings']['dimensions']['minecraft:overworld']['generator']['settings']['layers']
    assert sum(int(s['height']) for s in layers)==129
    return {'chunks_read_back':len(seen),'source_blocks_compared':compared,'terrain_samples':base_samples,
            'air_biome_sections_above_build_checked':sky_sections,'sections_per_chunk':24,
            'regions':region_reports,'region_bounds_and_sector_allocations':'passed',
            'source_block_states':'all matched', 'heightmaps':'all 4 maps per chunk matched decoded block-state predicates',
            'flat_generator_layers':129,'spawn_xyz':[65,65,204],'player_credentials':'none'}


def main():
    started=time.time()
    snapshot=(ROOT/'campus.json').read_bytes()
    source=json.loads(snapshot)
    sign_path=ROOT/'sign_texts.json'
    source_coords={(x,y,z):source['palette'][p] for x,y,z,p in source['blocks']}
    signs=[s for s in json.loads(sign_path.read_text(encoding='utf-8')) if 'wall_sign' in source_coords.get(tuple(s['pos']),'')] if sign_path.exists() else []
    # Export only the accepted, fully merged snapshot. Detail JSON files are
    # replacement patches with explicit air deletions, while original parts
    # still describe v1 geometry; neither is a standalone final schematic.
    source['name']='LQD_DaNang_Layout_v3_complete_campus'
    sources=[('Complete_Campus',source)]
    states=sorted({'minecraft:air','minecraft:bedrock','minecraft:stone','minecraft:dirt','minecraft:grass_block[snowy=false]'} |
                  {canonical(s) for _,part in sources for s in part['palette']})
    validation={'format':'Layout v3 Java 1.20.4 supplementary reference; mobile Bedrock is the primary target','DataVersion':DATA_VERSION,
                'campus_sha256':hashlib.sha256(snapshot).hexdigest(), 'source_entries':len(source['blocks']),
                'specification':SPEC,'assets':validate_assets(states),'in_game_validation':False,
                'schematic_policy':'Only the fully merged campus snapshot is exported. Raw detail patches and v1 component schematics are excluded.',
                'source_snapshot_name':source['name']}
    OUT.mkdir(exist_ok=True);WORLD.mkdir(exist_ok=True)
    lookup={s:i for i,s in enumerate(states)}
    cx0=min(-3,min(b[0]//16 for b in source['blocks']));cx1=max(12,max(b[0]//16 for b in source['blocks']))
    cz0=min(-2,min(b[2]//16 for b in source['blocks']));cz1=max(15,max(b[2]//16 for b in source['blocks']))
    overrides=collections.defaultdict(list)
    for x,y,z,p in source['blocks']:
        overrides[(x//16,z//16)].append((x,y,z,canonical(source['palette'][p])))
    chunks={}
    for cx in range(cx0,cx1+1):
        for cz in range(cz0,cz1+1):
            chunks[(cx,cz)]=make_chunk(cx,cz,overrides.get((cx,cz),[]),states,lookup,signs)
    paths=write_regions(chunks);make_level()
    validation['world']=validate_world(paths,source,range(cx0,cx1+1),range(cz0,cz1+1),signs)
    validation['world']['sign_entities_validated']=len(signs)
    validation['world']['block_bounds_xz']=[[cx0*16,cx1*16+15],[cz0*16,cz1*16+15]]
    validation['schematics']=[]
    for name,part in sources:
        path=OUT/f'LQD_DaNang_Layout_v3_{name}.schem'
        result=make_schematic(part,path,signs)
        result['validation']=validate_schematic(path,part,signs)
        validation['schematics'].append(result)
    text=('LQD Da Nang - Layout v3 Minecraft reconstruction\n'
          'Supplementary Java reference export: Minecraft Java Edition 1.20.4, DataVersion 3700.\n'
          'The mobile deliverable targets Minecraft Bedrock. This supplementary Java world does not import directly on mobile.\n'
          'Java import: copy the LQD_DaNang_Layout_v3_Java_1_20_4 folder into the saves directory of a Java 1.20.4 profile, then open Singleplayer.\n'
          'Spawn: x65 y65 z204; Creative, peaceful, daylight and weather frozen.\n'
          'No mods are required for this world. A compatible WorldEdit/Sponge loader is needed only to import .schem files.\n'
          'The Complete_Campus schematic contains the final merged detail snapshot, including air in its bounding box. Offset preserves campus local coordinates.\n'
          'Raw detail patches and old component schematics are intentionally excluded: they do not describe the complete Layout v3 map.\n'
          'Architecture follows public photographs and satellite references; dimensions, room divisions and some facades are inferred.\n'
          'NBT files, all placed blocks and region allocations were read back and validated. This export has not been opened in the Minecraft game.\n'
          'No installed Minecraft saves were modified.\n')
    (OUT/'README_Detail_v2_Java_Reference.txt').write_text(text,encoding='utf-8')
    (WORLD/'REFERENCE_README.txt').write_text(text,encoding='utf-8')
    with zipfile.ZipFile(OUT/'LQD_DaNang_Layout_v3_Java_1_20_4.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in WORLD.rglob('*'):
            if path.is_file():archive.write(path,path.relative_to(OUT))
    with zipfile.ZipFile(OUT/'LQD_DaNang_Layout_v3_Java_1_20_4.zip') as archive:
        assert archive.testzip() is None
        validation['world_zip_crc']='passed'
    validation['elapsed_seconds']=round(time.time()-started,2)
    validation['campus_unchanged_during_export']=(ROOT/'campus.json').read_bytes()==snapshot
    assert validation['campus_unchanged_during_export'],'Campus snapshot changed during export; rerun on the final snapshot.'
    own_outputs=([p for p in WORLD.rglob('*') if p.is_file()]
                 + [OUT/'README_Detail_v2_Java_Reference.txt',
                    OUT/'LQD_DaNang_Layout_v3_Java_1_20_4.zip']
                 + [Path(r['path']) for r in validation['schematics']])
    validation['outputs']=[{'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size} for p in own_outputs]
    VALIDATION.parent.mkdir(parents=True,exist_ok=True)
    VALIDATION.write_text(json.dumps(validation,indent=2),encoding='utf-8')
    print(json.dumps({'world_chunks':validation['world']['chunks_read_back'],
                      'compared_blocks':validation['world']['source_blocks_compared'],
                      'schematics':len(validation['schematics']),'elapsed_seconds':validation['elapsed_seconds'],
                      'campus_unchanged':validation['campus_unchanged_during_export'],'validation':str(VALIDATION.relative_to(ROOT))},indent=2))


if __name__=='__main__':main()
