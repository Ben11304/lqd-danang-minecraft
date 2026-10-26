"""Audit paved northeast routes and record the user's destination clarification."""
from pathlib import Path
from collections import deque
import json, hashlib
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'campus.json').read_text(encoding='utf-8'))
cells={(x,y,z):data['palette'][i] for x,y,z,i in data['blocks']}
digest=hashlib.sha256((ROOT/'campus.json').read_bytes()).hexdigest()
trace=json.loads((ROOT/'references/ne_circulation_trace.json').read_text(encoding='utf-8'))

def paved_open(p):
    x,z=p
    floor=cells.get((x,64,z),'air')
    return (80<=x<=141 and 40<=z<=132
            and floor not in ('air','dirt','grass_block[snowy=false]')
            and not floor.startswith(('water','lava'))
            and all(cells.get((x,y,z),'air')=='air' for y in (65,66)))

def route(start,end,max_z=132):
    assert paved_open(start),('start blocked',start)
    q=deque([start]);parent={start:None}
    while q and end not in parent:
        x,z=q.popleft()
        for p in ((x-1,z),(x+1,z),(x,z-1),(x,z+1)):
            if p not in parent and p[1]<=max_z and paved_open(p):parent[p]=(x,z);q.append(p)
    assert end in parent,('No paved route without crossing lawn',start,end)
    points=[];p=end
    while p is not None:points.append(list(p));p=parent[p]
    return list(reversed(points))

specs=[('north_gallery_to_dorm_adjacent_annex',(84,83),(127,61)),
       ('east_wing_to_dorm_adjacent_annex',(133,124),(127,61)),
       ('annex_to_dorm_entry',(127,61),(129,46))]
routes=[{'label':name,'feet_y':65,'points':route(start,end,90 if name.startswith('north_gallery') else 132)} for name,start,end in specs]
audit={'source_sha256':digest,'routes':routes,'restricted_to_paved_floor':True,
       'body_height_blocks':2,'lawn_shortcuts_allowed':False,'in_game_validation':False,
       'identity_limit':'Route endpoints are model doorways, not verified real-world lobby C or canteen doors.'}
(ROOT/'qa/ne_circulation_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
all_routes=json.loads((ROOT/'qa/layout_routes.json').read_text())
assert all_routes['source_sha256']==digest
names={r['label'] for r in routes}
all_routes['routes']=[r for r in all_routes['routes'] if r['label'] not in names]+routes
(ROOT/'qa/layout_routes.json').write_text(json.dumps(all_routes,separators=(',',':')),encoding='utf-8')
report=json.loads((ROOT/'qa/layout_validation.json').read_text())
report['route_body_points']=sum(len(r['points']) for r in all_routes['routes'])
report['additional_paved_route_checks']=[r['label'] for r in routes]
(ROOT/'qa/layout_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
old_audit=json.loads((ROOT/'qa/connector_route_audit.json').read_text())
for x,y,z in old_audit['route']:
    assert cells.get((x,y-1,z),'air') not in ('air','water','lava')
    assert all(cells.get((x,y+d,z),'air')=='air' for d in (0,1))
old_audit['source_sha256']=digest
old_audit['segment']='Existing connector toward the sports complex; distinct from the requested dormitory-side route'
(ROOT/'qa/connector_route_audit.json').write_text(json.dumps(old_audit,indent=2)+'\n',encoding='utf-8')
revision={'version':'layout_v3.3','source_sha256':digest,'researched_on':'2026-10-26',
 'user_clarification':'The requested connection is from lobby C to the canteen beside the dormitory, not the old narrow connector toward the sports hall.',
 'sources':[
  {'url':'https://www.google.com/maps?cid=681546677781845227','used_for':'Satellite paving and building adjacency in the northeast campus. Acquisition date is unknown.'},
  {'url':'https://www.google.com/maps/place/K%C3%BD+t%C3%BAc+x%C3%A1+THPT+L%C3%AA+Qu%C3%BD+%C4%90%C3%B4n/@16.0571842,108.2331228,825m/data=!3m1!1e3!4m13!1m7!3m6!1s0x314219d4190559bd:0x9755717ab08d4eb!2sLe+Quy+Don+High+School+Specialist!8m2!3d16.0571842!4d108.2331228!16s%2Fg%2F11c6y_6nh_!3m4!1s0x314219d43ee3e847:0xd9e17b59c3c37046!8m2!3d16.0585315!4d108.233555','used_for':'Dormitory place identity and position.'}],
 'geometry_trace':'references/ne_circulation_trace.json',
 'changes':['Add northeast ground circulation and approach paving visible in enlarged satellite imagery.',
            'Add representative tree-canopy groups beside the northeast approach; individual trunks and heights are approximate.',
            'Keep covered sports connector distinct from the dormitory-side destination.',
            'Add a provisional ground doorway at the northern curved wing for Minecraft circulation; its real-world location is unconfirmed.',
            'Add ground, approach, context and overhead inspection cameras.'],
 'limits':['Canteen adjacency to dormitory is confirmed by the user; exact room footprint and doorway are not identified.',
           'Lobby C has not been assigned to an exact building or doorway. The new model doorway is a gameplay interpretation.',
           'Paving under canopy and shadow is simplified; satellite trace uncertainty about2–3m.',
           'No extra canopy is added without evidence. Building heights and interiors remain provisional.',
           'Web captures are voxel previews; no Minecraft session was run.'],
 'validation':{'paved_route_audit':'qa/ne_circulation_audit.json','export_readback':'exports/bedrock_validation.json'},
 'previous_revision':'references/landscape_revision.json retains its historical v3.2 source hash.'}
(ROOT/'references/ne_circulation_revision.json').write_text(json.dumps(revision,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_sha256':digest,'paved_route_lengths':{r['label']:len(r['points']) for r in routes},'total_route_body_points':report['route_body_points']}))
