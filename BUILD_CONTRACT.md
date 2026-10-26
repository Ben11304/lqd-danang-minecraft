# LQD Minecraft reconstruction v1

This is an evidence-based Minecraft reconstruction, not a surveyed exact replica. Do not present inferred interiors, heights or functional labels as verified. Source images: `../reference-research/images`. Read catalog.json there for provenance. Use view_image to inspect relevant references, including satellite.

## Shared coordinates
Local x EAST 0..148; z SOUTH 0..208; ground TOP y=64. All buildings start y=65. North is -z. Entrance south around x=75,z=205. Footprints follow a campus-aligned rectangular frame, simplifying the small real-world rotation. World margin and landscape managed by root. One block approximately one metre. Store only your component blocks, no large ground plane. Clear air is allowed inside your own building only. No subagents needed.

## Geometry and palette
Wall pale sand `smooth_sandstone`, modern white `white_concrete`, structural white `quartz_block`, floors `smooth_stone`, plinth `stone_bricks`, glass `light_gray_stained_glass`, roof `light_gray_concrete` and `gray_concrete`, metal trim/rail `iron_bars` or `light_gray_concrete`, dark gate `green_concrete`, arch `cyan_concrete`, pier/sign `terracotta` or `red_terracotta`, paving `brick_block` is INVALID use `bricks`; ochre square `yellow_terracotta`, paving green-grey `andesite`. Use modern block state names with namespace omitted, no unsupported custom blocks. Use full cubes as default; slabs and stairs allowed with explicit states. No fences/doors that depend on neighbors unless states explicit. Roofs should be largely flat/light-grey per satellite, not invented red pitched classroom roofs.

Floor heights: provisional 4 blocks, classroom structures 3 floors (y65..76), floor slab y64/68/72/76, roof y77; these are reconstruction choices. Windows bays 3-4 blocks wide, white columns, continuous corridors, lightly cream walls. Preserve important voids under columns. Do not fill every window opening with solid wall.

## API
Import `from voxel import Builder`. `b=Builder('component_id')`. `b.set(x,y,z,'block_name')`, `b.fill(x1,y1,z1,x2,y2,z2,'block')` inclusive; `b.line(x1,y1,z1,x2,y2,z2,'block')`; `b.polygon([(x,z),...], y1,y2,'block')`; `b.disk(cx,cz,r,y1,y2,'block')`; `b.ring(cx,cz,outer,inner,y1,y2,'block',start_degrees=0,end_degrees=360)`. Degrees: 0=+x,90=+z. `b.save('parts/name.json')` writes palette+blocks. Module has `build()` returns builder. Files named `parts/south.py`, `parts/academic.py`, `parts/north.py`; edit your assigned file only and optional corresponding `*_notes.json`. Root owns voxel.py, assemble.py and preview/export.

## Assignments
- south: southern academic/crescent and entrance front x20..142,z142..208. Main south structure is a crescent band, connected to the east arc, not a U-shaped box. Target crescent centre (102,161), outer radius31, inner23, southern/east half degrees 0..180; west straight return x21..103,z149..160. Keep open entrance forecourt x58..90,z176..204. Gate at z204 with asymmetrical two cyan curves rising to central terracotta pier x75, height12; about 28 blocks overall wide. No perimeter entire fence.
- academic: east curved academic band x70..140,z52..145 plus central west-east connecting wing x20..117,z124..137. Curved band centre (76,107), outer radius62, inner52, degrees -73..30 (east-facing arc). Three floors; corridor inside curve. Connecting wing interrupts/joins arc near z127. Courtyard remains open, no central solid disc. End/round stair elements per photos only, not invented large towers.
- north: northwest sports open field x5..40,z20..94; hall building x46..79,z12..84; dormitory approximate x111..136,z4..23, 11 storeys max y109, mark inferred four facades; covered pool approximate x129..145,z28..65 (location inferred from satellite/photo, not exact). Include only selected representative interiors, note uncertainties. Hall and pool roofs simplified based on evidence. Do not cover south/academic assigned space.

## Required agent deliverable
Implement module and run it to JSON; inspect reference images and report observed visual traits, bounds, block count, known guesses and suggested close/mid/far camera targets. Each agent must verify its own geometry dimensions and palette. Do not change shared files. Root performs assembled visual QA and fixes.
