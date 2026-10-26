"""Create a real Bedrock LevelDB world using Amulet's maintained translators.

No game is launched. The .mcworld contains level.dat and db/ at its root.
Source Java 1.20.4 states are projected to native Bedrock 1.21.0 states, then
every source coordinate is read back. State properties unique to Java are
listed in the report instead of being claimed as byte-identical.
"""
from pathlib import Path
import sys,os,json,hashlib,zipfile,collections,re,time,copy,logging,shutil

ROOT=Path(__file__).resolve().parent
DEPS=ROOT/'.bedrock_deps'
sys.path[:0]=[str(DEPS),str(DEPS/'win32'),str(DEPS/'win32/lib'),str(DEPS/'pywin32_system32')]
_dll_path=os.add_dll_directory(str(DEPS/'pywin32_system32'))
sys.stdout.reconfigure(encoding='utf-8')
import amulet
from amulet.level.formats.leveldb_world import LevelDBFormat
from amulet.level.formats.leveldb_world.format import BedrockLevelDAT
from amulet.api.block import Block
from amulet.api.block_entity import BlockEntity
from amulet.api.chunk import Chunk
from amulet_nbt import (NamedTag,CompoundTag,ListTag,StringTag,ByteTag,IntTag,LongTag,FloatTag)

DIM='minecraft:overworld'
JAVA=('java',(1,20,4))
BEDROCK=('bedrock',(1,21,0))
OUT=ROOT/'exports'
WORLD=OUT/'LQD_DaNang_Layout_Bedrock_v3'
ARCHIVE=OUT/'LQD_DaNang_Layout_Bedrock_v3.mcworld'
SOURCES=[
 'https://github.com/Amulet-Team/Amulet-Core',
 'https://pypi.org/project/amulet-core/1.9.50/',
 'https://pypi.org/project/amulet-leveldb/1.0.7/',
 'https://amulet-core.readthedocs.io/en/stable/api_reference/level.formats/leveldb_world.html',
 'https://amulet-core.readthedocs.io/en/stable/api_reference/api/level/base_level/index.html',
 'https://learn.microsoft.com/en-us/minecraft/creator/documents/createaworldtemplate',
 'https://learn.microsoft.com/en-us/minecraft/creator/documents/bedrockeditor/editorworkflow?view=minecraft-bedrock-stable'
]


def parse_java(state):
    return Block.from_string_blockstate('minecraft:'+state.removeprefix('minecraft:'))


def sig(block):
    """Deterministic typed native state, preserving all Bedrock properties."""
    return {'name':block.namespaced_name,
            'properties':{k:v.to_snbt() for k,v in sorted(block.properties.items())},
            'extra_blocks':[sig(b) for b in block.extra_blocks]}


def normalized_java(block):
    """Ignore only documented properties that Bedrock computes differently."""
    props={k:v.py_str for k,v in block.properties.items()}
    if props.get('waterlogged')=='false':props.pop('waterlogged')
    if block.base_name.endswith('_leaves'):props.pop('distance',None)
    if block.base_name=='iron_bars' or block.base_name.endswith('_glass_pane'):
        for k in ('east','west','north','south'):props.pop(k,None)
    return {'name':block.namespaced_name,'properties':props,
            'extra_blocks':[normalized_java(b) for b in block.extra_blocks]}


def reverse_validate(source):
    check=amulet.load_level(str(WORLD));exact=0;normalized=0;differences=collections.Counter()
    try:
        for x,y,z,i in source['blocks']:
            actual,_=check.get_version_block(x,y,z,DIM,JAVA)
            expected=parse_java(source['palette'][i])
            if actual==expected:exact+=1
            else:differences[source['palette'][i]]+=1
            assert normalized_java(actual)==normalized_java(expected),('Reverse semantic mismatch',x,y,z,expected,actual)
            normalized+=1
    finally:check.close()
    return {'source_coordinates_checked':normalized,'exact_java_state_matches':exact,
            'equivalent_after_documented_property_normalization':normalized,
            'normalization_only_source_states':dict(differences),
            'ignored_properties':{
              'waterlogged=false':'Bedrock source fluid storage omits explicit false waterlogging.',
              'leaf distance':'Bedrock retains persistent=true but does not store Java decay distance.',
              'iron_bars and glass_pane north/east/south/west':'Bedrock computes neighbor connections instead of storing forced Java arms.'}}


def package_world():
    with zipfile.ZipFile(ARCHIVE,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in sorted(WORLD.rglob('*')):
            if p.is_file() and p.name not in ('LOCK','session.lock'):archive.write(p,p.relative_to(WORLD).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        assert 'level.dat' in z.namelist() and 'db/CURRENT' in z.namelist()
        assert z.testzip() is None


def make_sign(entry):
    x,y,z=entry['pos']
    lines=(entry['lines']+['','','',''])[:4]
    messages=ListTag([StringTag(json.dumps({'text':s},ensure_ascii=False)) for s in lines])
    text=CompoundTag({'messages':messages,'color':StringTag('black'),'has_glowing_text':ByteTag(0)})
    nbt=NamedTag(CompoundTag({'id':StringTag('minecraft:sign'),'x':IntTag(x),'y':IntTag(y),'z':IntTag(z),
                             'front_text':text,'back_text':copy.deepcopy(text),'is_waxed':ByteTag(1)}))
    return BlockEntity('minecraft','sign',x,y,z,nbt)


def configure(wrapper):
    r=wrapper.root_tag.compound
    values={
      'LevelName':StringTag('Lê Quý Đôn Đà Nẵng · Layout v3'),
      'GameType':IntTag(1),'Difficulty':IntTag(0),'RandomSeed':LongTag(26001026),
      'SpawnX':IntTag(65),'SpawnY':IntTag(65),'SpawnZ':IntTag(204),
      'Time':LongTag(6000),'currentTick':LongTag(0),'commandsEnabled':ByteTag(1),
      'hasBeenLoadedInCreative':ByteTag(1),'hasBeenLoadedInCreativeMode':ByteTag(1),
      'doDaylightCycle':ByteTag(0),'dodaylightcycle':ByteTag(0),
      'doweathercycle':ByteTag(0),'domobspawning':ByteTag(0),
      'dofiretick':ByteTag(0),'mobgriefing':ByteTag(0),
      'keepinventory':ByteTag(1),'spawnMobs':ByteTag(0),'showcoordinates':ByteTag(1),
      'rainLevel':FloatTag(0),'lightningLevel':FloatTag(0),
      'Generator':IntTag(2),'FlatWorldLayers':StringTag(json.dumps({
          'biome_id':1,'block_layers':[
             {'block_name':'minecraft:bedrock','count':1},
             {'block_name':'minecraft:stone','count':124},
             {'block_name':'minecraft:dirt','count':3},
             {'block_name':'minecraft:grass_block','count':1}],
          'encoding_version':6,'structure_options':None,'world_version':'version.post_1_18'})),
      'MinimumCompatibleClientVersion':ListTag([IntTag(i) for i in (1,21,0,0,0)]),
      'NetherScale':IntTag(8),'MultiplayerGame':ByteTag(0),'LANBroadcast':ByteTag(0)
    }
    for k,v in values.items():r[k]=v


def export(expected_hash=None,replace_export=False):
    started=time.time();raw=(ROOT/'campus.json').read_bytes();source=json.loads(raw)
    digest=hashlib.sha256(raw).hexdigest()
    if expected_hash:assert digest==expected_hash,'Source changed; confirm the current snapshot before export.'
    if replace_export:
        # Replace only the two derived artifacts this exporter owns. Resolved
        # absolute targets are checked before the Windows recursive removal.
        assert WORLD.resolve().parent==OUT.resolve() and WORLD.name=='LQD_DaNang_Layout_Bedrock_v3'
        assert ARCHIVE.resolve().parent==OUT.resolve() and ARCHIVE.name=='LQD_DaNang_Layout_Bedrock_v3.mcworld'
        if WORLD.exists():
            assert (WORLD/'BEDROCK_EXPORT_INFO.json').is_file(),'Refusing to delete an unrecognized directory.'
            shutil.rmtree(WORLD)
        if ARCHIVE.exists():ARCHIVE.unlink()
    assert not WORLD.exists(),f'Refusing to overwrite an existing world: {WORLD}'
    assert not ARCHIVE.exists(),f'Refusing to overwrite an existing archive: {ARCHIVE}'
    OUT.mkdir(exist_ok=True)
    coords={(x,y,z):i for x,y,z,i in source['blocks']}
    signs=json.loads((ROOT/'sign_texts.json').read_text(encoding='utf-8'))
    signs=[e for e in signs if 'wall_sign' in source['palette'][coords.get(tuple(e['pos']),-1)]]
    sign_entities={tuple(e['pos']):make_sign(e) for e in signs}
    wrapper=LevelDBFormat(str(WORLD));wrapper.create_and_open(*BEDROCK)
    configure(wrapper);wrapper.save();wrapper.close()
    level=amulet.load_level(str(WORLD))
    tm=level.translation_manager
    java=tm.get_version(*JAVA).block;bedrock=tm.get_version(*BEDROCK).block
    java_blocks=[parse_java(s) for s in source['palette']]
    universals=[];default_entities=[];projection=[]
    for state,block in zip(source['palette'],java_blocks):
        universal,entity,_=java.to_universal(block)
        native,native_entity,_=bedrock.from_universal(universal,entity)
        assert native.namespace=='minecraft',f'Untranslated Bedrock block: {state}'
        universals.append(universal);default_entities.append(entity)
        projection.append({'java':state,'bedrock':sig(native),'block_entity':native_entity.base_name if native_entity else None})
    grouped=collections.defaultdict(list)
    for x,y,z,i in source['blocks']:grouped[(x//16,z//16)].append((x,y,z,i))
    min_cx=min(-3,min(k[0] for k in grouped));max_cx=max(12,max(k[0] for k in grouped))
    min_cz=min(-2,min(k[1] for k in grouped));max_cz=max(15,max(k[1] for k in grouped))
    foundation={n:java.to_universal(Block('minecraft',n))[0] for n in ('bedrock','stone','dirt')}
    grass=java.to_universal(parse_java('grass_block[snowy=false]'))[0]
    chunk_count=0
    try:
        for cx in range(min_cx,max_cx+1):
            for cz in range(min_cz,max_cz+1):
                c=level.create_chunk(cx,cz,DIM)
                for n,y1,y2 in [('bedrock',-64,-63),('stone',-63,61),('dirt',61,64)]:
                    c.blocks[:,y1:y2,:]=c.block_palette.get_add_block(foundation[n])
                c.blocks[:,64,:]=c.block_palette.get_add_block(grass)
                palette_ids=[c.block_palette.get_add_block(u) for u in universals]
                for x,y,z,i in grouped.get((cx,cz),[]):
                    pos=(x,y,z);u=universals[i];entity=default_entities[i]
                    if pos in sign_entities:
                        u,entity,_=java.to_universal(java_blocks[i],sign_entities[pos],block_location=pos)
                    c.blocks[x-cx*16,y,z-cz*16]=palette_ids[i] if u==universals[i] else c.block_palette.get_add_block(u)
                    if entity is not None:c.block_entities[pos]=entity.new_at_location(*pos)
                # Generated chunks are complete; avoid terrain generation over construction.
                c.status=2.0;c.changed=True;chunk_count+=1
        level.save()
    finally:level.close()
    # Read a newly opened LevelDB, not the in-memory construction objects.
    check=amulet.load_level(str(WORLD));mismatches=[];door_checks=[];sign_checks=[]
    expected_native=[p['bedrock'] for p in projection]
    try:
        read_chunks=set(check.all_chunk_coords(DIM))
        assert len(read_chunks)==chunk_count,(len(read_chunks),chunk_count)
        for x,y,z,i in source['blocks']:
            block,be=check.get_version_block(x,y,z,DIM,BEDROCK)
            if sig(block)!=expected_native[i]:
                mismatches.append({'position':[x,y,z],'source':source['palette'][i],
                                   'expected':expected_native[i],'actual':sig(block)})
            if '_door[' in source['palette'][i] and 'trapdoor' not in source['palette'][i]:
                j,_=check.get_version_block(x,y,z,DIM,JAVA)
                assert j==java_blocks[i],f'Door failed Java round-trip at {(x,y,z)}'
                door_checks.append([x,y,z])
        assert not mismatches,f'{len(mismatches)} source projection mismatches: {mismatches[:3]}'
        for e in signs:
            x,y,z=e['pos'];_,entity=check.get_version_block(x,y,z,DIM,BEDROCK)
            assert entity is not None,f'Missing sign entity at {e["pos"]}'
            root=entity.nbt.compound
            for side in ('FrontText','BackText'):
                text=root[side]['Text'].py_str
                plain=re.sub(r'§.','',text).replace('\r','')
                assert plain=='\n'.join((e['lines']+['','','',''])[:4]),(e['pos'],side,plain)
            assert root['IsWaxed'].py_int==1
            sign_checks.append({'position':e['pos'],'front_back_unicode_text':True,'waxed':True})
        # Foundation, spawn and required gym exits checked after serialization.
        terrain=[]
        for cx,cz in sorted(read_chunks):
            for y,n in [(-64,'bedrock'),(-63,'stone'),(60,'stone'),(61,'dirt'),(63,'dirt')]:
                b,_=check.get_version_block(cx*16,y,cz*16,DIM,JAVA)
                assert b.base_name==n;terrain.append([cx,cz,y])
        route_data=json.loads((ROOT/'qa/layout_routes.json').read_text(encoding='utf-8'))
        route_cells=0
        for route in route_data['routes']:
            for x,z in route['points']:
                for y in (route['feet_y'],route['feet_y']+1):
                    block,_=check.get_version_block(x,y,z,DIM,BEDROCK)
                    assert block.base_name=='air',('Blocked layout route',route['label'],x,y,z,block)
                    route_cells+=1
        for pos in [(65,65,204),(65,66,204)]:
            block,_=check.get_version_block(*pos,DIM,BEDROCK);assert block.base_name=='air',('spawn',pos,block)
    finally:check.close()
    meta=BedrockLevelDAT.from_file(str(WORLD/'level.dat')).compound
    assert meta['GameType'].py_int==1 and meta['SpawnY'].py_int==65
    # No Java region files; LevelDB must have its real CURRENT/MANIFEST structure.
    assert (WORLD/'db/CURRENT').is_file() and list((WORLD/'db').glob('MANIFEST-*'))
    assert not (WORLD/'region').exists()
    report={'format':'Minecraft Bedrock LevelDB world','target_version':list(BEDROCK[1]),
      'source_sha256':digest,'source_entries':len(source['blocks']),'source_palette_size':len(source['palette']),
      'source_blocks_read_back_and_compared':len(source['blocks']),'source_projection_mismatches':mismatches,
      'chunks_read_back':chunk_count,'foundation_samples':len(terrain),'door_halves_round_trip_exact':len(door_checks),
      'signs':sign_checks,'layout_route_body_cells_checked':route_cells,'layout_routes_clear':True,'spawn_clear':True,
      'palette_projection':projection,'library_versions':{'amulet-core':amulet.__version__,'amulet-leveldb':'1.0.7'},
      'sources':SOURCES,'limitations':[
        'Not opened in Minecraft; iPad/phone import and actual in-game appearance remain unverified.',
        'Java-only block properties, including leaf distance and explicit pane/bars connections, map to Bedrock native semantics.',
        'Architecture dimensions and interiors retain the reconstruction uncertainties documented in the research and detail notes.'],
      'elapsed_seconds':round(time.time()-started,2)}
    report['reverse_translation_validation']=reverse_validate(source)
    (WORLD/'BEDROCK_EXPORT_INFO.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'bedrock_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    package_world()
    assert hashlib.sha256((ROOT/'campus.json').read_bytes()).hexdigest()==digest,'Source changed during export.'
    print(json.dumps({'world':str(WORLD),'mcworld':str(ARCHIVE),'bytes':ARCHIVE.stat().st_size,
                      'source_hash':digest,'source_blocks_compared':len(source['blocks']),
                      'door_halves':len(door_checks),'signs':len(sign_checks),'chunks':chunk_count},ensure_ascii=False))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--expected-sha256');parser.add_argument('--validate-existing',action='store_true');parser.add_argument('--replace-export',action='store_true')
    args=parser.parse_args()
    if args.validate_existing:
        source=json.loads((ROOT/'campus.json').read_text(encoding='utf-8'))
        report=json.loads((OUT/'bedrock_validation.json').read_text(encoding='utf-8'))
        assert report['source_sha256']==hashlib.sha256((ROOT/'campus.json').read_bytes()).hexdigest()
        report['reverse_translation_validation']=reverse_validate(source)
        (WORLD/'BEDROCK_EXPORT_INFO.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (OUT/'bedrock_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        package_world();print(json.dumps(report['reverse_translation_validation'],ensure_ascii=False))
    else:export(args.expected_sha256,args.replace_export)
