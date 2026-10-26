# Layout v3 — Google Maps roof trace

The user's current instruction rejects v1/v2 layout and requires Google Maps.
This supersedes all earlier footprint-preservation constraints in BUILD_CONTRACT.md
and DETAIL_CONTRACT.md. Preserve v2 as a historical snapshot; rebuild the shell here.

Current evidence is in references/. georeference.json defines road-center control
points and a local campus-aligned metre grid. The settled satellite south screenshot
registers to the north screenshot by +354 pixels vertically. Trace visible roof
outlines, distinguish courtyards from solid roofs, and record uncertainties. Road
measurements are approximate browser measurements, not a cadastral survey. Floors,
wall positions under roof overhangs and internal room functions remain inferred.

Ground block y64, surface y65. Fence approximately x6..142,z7..199; roads lie outside.
Root owns terrain, paths, vegetation, fence, gate and statue. Component agents own
parts/layout_north, layout_academic and layout_south, and their reference traces.
Do not apply old interior patches at old coordinates after rebuilding the shell.
Keep two-block-high routes through public entries and junctions.

Layout acceptance: main roofs follow manually traced satellite outlines within
voxel rounding and stated ~2.5m reference uncertainty; the southern oval has a solid
roof, the two cross wings and central spine remain distinct, and the north hall,
field and northeast buildings retain their measured relative placement.

Root validates near/middle/far browser views, a north-up roof plan and ground routes,
then regenerates both web and Bedrock from the same frozen campus snapshot.
Browser renders and data readback must never be called in-game screenshots/tests.
