"""Check assembled circulation and publish an inspectable roof-plan artifact."""
from pathlib import Path
import json,hashlib,collections,html
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'campus.json').read_text(encoding='utf-8'))
cells={(x,y,z):data['palette'][i] for x,y,z,i in data['blocks']}
digest=hashlib.sha256((ROOT/'campus.json').read_bytes()).hexdigest()
def open2(x,z,y=65):return all(cells.get((x,y+d,z),'air')=='air' for d in (0,1))
start=(65,204);q=collections.deque([start]);parent={start:None}
assert open2(*start)
while q:
    x,z=q.popleft()
    for p in ((x-1,z),(x+1,z),(x,z-1),(x,z+1)):
        if 5<=p[0]<=143 and 6<=p[1]<=204 and p not in parent and open2(*p):parent[p]=(x,z);q.append(p)
targets={'south_lobby':(72,171),'oval_lobby':(112,177),'oval_connection':(98,164),
 'upper_junction':(72,126),'library':(54,128),'east_gallery':(109,130),
 'north_hall':(68,44),'north_field':(31,61),'tower_entry':(129,46),'annex_entry':(127,61),
 'north_connector':(70,103)}
routes=[]
for label,target in targets.items():
    assert target in parent,(label,target,'unreachable from entrance',cells.get((target[0],65,target[1])))
    path=[];p=target
    while p is not None:path.append(list(p));p=parent[p]
    routes.append({'label':label,'feet_y':65,'points':list(reversed(path))})
route_data={'source_sha256':digest,'start_xyz':[65,65,204],'ground_reachable_cells':len(parent),'routes':routes}
(ROOT/'qa/layout_routes.json').write_text(json.dumps(route_data,separators=(',',':')),encoding='utf-8')

colors={'north':'#a7bec6','academic':'#7997ae','south':'#587a96','connectors':'#b38451'}
paths=[];masks={}
for name,color in colors.items():
    d=json.loads((ROOT/'parts'/f'layout_{name}.json').read_text(encoding='utf-8'))
    mask={(x,z) for x,y,z,i in d['blocks'] if y>=(69 if name=='connectors' else 72) and d['palette'][i]!='air'}
    masks[name]=mask
    rows=collections.defaultdict(list)
    for x,z in mask:rows[z].append(x)
    fragments=[]
    for z,xs in sorted(rows.items()):
        xs=sorted(xs);a=last=xs[0]
        for x in xs[1:]+[xs[-1]+2]:
            if x!=last+1:fragments.append(f'M{a} {z}h{last-a+1}v1h{-last+a-1}z');a=x
            last=x
    paths.append(f'<path d="{"".join(fragments)}" fill="{color}"/>')
svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-12 -18 172 244" role="img" aria-label="Mặt bằng mái v3 theo Google Maps"><rect x="-12" y="-18" width="172" height="244" fill="#f3f5ef"/><g stroke="#c1c8c6" stroke-width="7"><path d="M0 -5V213M148 -5V213M-4 0H152M-4 208H152"/></g><rect x="6" y="7" width="136" height="192" fill="#e0e9d5" stroke="#66816d" stroke-width=".6"/><rect x="12" y="26" width="39" height="70" fill="#bdac8b"/>'''+''.join(paths)+'''<path d="M64 173H80V199H64Z" fill="#c38572"/><path d="M56 199H86" stroke="#4d9eb5" stroke-width="2"/><rect x="35" y="184" width="7" height="7" fill="#696763"/><g font-family="sans-serif" text-anchor="middle" fill="#213f49" font-size="3.7"><text x="31" y="64">Sân thể thao</text><text x="68" y="47">Dãy mái bắc</text><text x="125" y="35">Tháp</text><text x="134" y="66">Nhà phụ</text><text x="43" y="126">Dãy ngang trên</text><text x="111" y="100">Dãy cong</text><text x="44" y="160">Dãy ngang dưới</text><text x="112" y="166">Khối oval đặc</text><text x="72" y="190">Sân trước</text><text x="72" y="218">Vũ Văn Dũng · Cổng chính</text><text x="74" y="-8">MẶT BẰNG V3 · DẤU MÁI</text></g><g stroke="#405a60" stroke-width=".5" fill="none"><path d="M10 217H30M10 215V219M30 215V219"/></g><text x="20" y="224" text-anchor="middle" font-family="sans-serif" font-size="3.4" fill="#405a60">20 m (xấp xỉ)</text></svg>'''
(ROOT/'qa/layout_plan.svg').write_text(svg,encoding='utf-8')

# Private side-by-side source overlay, retaining Google's screenshot attribution.
# The public package excludes the Google screenshots; only this project's plan
# and a direct Maps link are published.
ref=[]
for name in ('north','academic','south'):
    trace=json.loads((ROOT/'references'/f'{name}_trace.json').read_text(encoding='utf-8'))
    specs=trace.get('polygons',trace.get('roof_polygons',[]))
    if isinstance(specs,dict):specs=list(specs.values())
    for spec in specs:
        points=spec.get('world_vertices',spec.get('world',spec.get('world_polygon',spec.get('world_xz'))))
        if points:ref.append((name,points))
geo=json.loads((ROOT/'references/georeference.json').read_text())
connector=json.loads((ROOT/'references/connector_trace.json').read_text())
ref.append(('connectors',connector['world_xz_polygon']))
origin=geo['north_control_origin_pixel'];ax=geo['x_axis_pixel_per_m'];az=geo['z_axis_pixel_per_m']
boards=[]
for frame,dy in [('north',0),('south',354)]:
    outlines=[]
    for name,poly in ref:
        pix=' '.join(f'{origin[0]+x*ax[0]+z*az[0]:.2f},{origin[1]+x*ax[1]+z*az[1]-dy:.2f}' for x,z in poly)
        outlines.append(f'<polygon points="{pix}" fill="{colors[name]}33" stroke="{colors[name]}" stroke-width="2"/>')
    boards.append(f'<section><h2>{frame}</h2><div class="board"><img src="satellite_{frame}.png"><svg viewBox="0 0 1280 720">{"".join(outlines)}</svg></div></section>')
page='''<!doctype html><meta charset="utf-8"><title>LQD v3 · đối chiếu nguồn Google Maps</title><style>body{background:#edf1ef;color:#173e3d;font:16px system-ui;margin:20px}.board{position:relative}.board img{width:100%;display:block}.board svg{position:absolute;inset:0;width:100%;height:100%}section{max-width:1280px;margin:20px auto}h1,p{max-width:1280px;margin:18px auto}</style><h1>Đối chiếu đường mái · v3</h1><p>Ảnh từ Google Maps, giữ nguyên ghi công ở mép ảnh. Đường màu là trace thủ công, sai số khoảng2–3m; không phải hồ sơ đo đạc.</p>'''+''.join(boards)
(ROOT/'references/compare.html').write_text(page,encoding='utf-8')
report={'source_sha256':digest,'ground_targets_reached':list(targets),'ground_reachable_cells':len(parent),
 'route_body_points':sum(len(r['points']) for r in routes),'roof_projection_cells':{k:len(v) for k,v in masks.items()},
 'southern_oval_has_solid_roof':all((x,77,z) in cells for x,z in [(112,165),(110,164),(114,166)]),
 'in_game_validation':False,'reference_overlay':'references/compare.html'}
assert report['southern_oval_has_solid_roof']
(ROOT/'qa/layout_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
