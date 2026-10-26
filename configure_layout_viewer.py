"""Use v3 cameras and the current content hash in the static web viewer."""
from pathlib import Path
import json,re,hashlib,gzip
ROOT=Path(__file__).resolve().parent
digest=hashlib.sha256((ROOT/'campus.json').read_bytes()).hexdigest()
assert json.loads((ROOT/'preview/metadata.json').read_text())['source_sha256']==digest
views={
 'overview':dict(label='Toàn cảnh · mặt bằng v3',p=[245,175,310],t=[74,7,108],fov=48,note='Bố cục dựng lại theo dấu mái Google Maps; chiều cao và nội thất vẫn là ước dựng.'),
 'top':dict(label='Mặt bằng · đối chiếu Google Maps',p=[74,345,104],t=[74,0,104],fov=48,note='Khối oval đặc, hai dãy ngang, trục nối và dãy cong theo ảnh vệ tinh. Sai số đường mái khoảng 2–3 m.'),
 'gate':dict(label='Cổng · nhìn vào khu phía nam',p=[71,7,225],t=[74,5,163],fov=64,note='Khối oval khoảng31m ở phía đông, dãy ngang và sân trước được bố trí lại theo bản đồ.'),
 'lobby_south':dict(label='Khu phía nam · sảnh dãy ngang',p=[73,2.62,183],t=[72,3,160],fov=65,note='Lối xuyên trục giữa và tầng trệt mở; chi tiết cột, cửa và nội thất là phương án ước dựng.'),
 'lobby_mid':dict(label='Sảnh nối · hai trục giữa trường',p=[72,2.62,144],t=[72,4,123],fov=65,note='Trục nhỏ nối hai dãy ngang; giữ hai khoảng sân riêng thay vì gộp thành một khối.'),
 'east_arc':dict(label='Dãy cong · nhìn từ sân trong',p=[96,3.2,133],t=[114,5,114],fov=65,note='Dải cong sâu khoảng16–18m, được truy theo đường mái thực tế thay cho vòng tròn áp đặt của v1.'),
 'lobby_north':dict(label='Khối bắc · sảnh phía sân',p=[85,2.62,96],t=[71,3,84],fov=65,note='Tương quan dãy mái thể thao và đầu dãy cong; tên sảnh A/B/C chưa được gán khi chưa xác nhận.'),
 'gym':dict(label='Nhà thi đấu · khu đại diện',p=[70,2.7,44],t=[56,4,34],fov=65,note='Sàn sân, ghế khán đài và lối đi trong phần mái trên. Vị trí chi tiết bên trong chưa được đo đạc.'),
 'north':dict(label='Khu bắc · sân và các mái nối',p=[22,55,-42],t=[88,11,46],fov=60,note='Giữ năm phần mái quan sát được, sân thể thao và vị trí tháp đông bắc theo ảnh vệ tinh.'),
 'tower':dict(label='Khối đông bắc · tháp và nhà phụ',p=[215,48,90],t=[126,19,42],fov=60,note='Mái tháp cao có độ lệch ảnh so với chân công trình; vị trí và mặt đứng còn sai số.'),
 'statue':dict(label='Tượng Lê Quý Đôn · cận cảnh',p=[47,3.8,196],t=[38.5,3.2,187.5],fov=45,note='Tượng trắng và bệ sẫm giản lược từ ảnh2012; phía tây do bạn xác nhận, khoảng cách đến cổng vẫn ước lượng.',mobile=dict(fov=65)),
 'statue_gate':dict(label='Tượng và cổng · từ sân nhìn ra',p=[62,2.62,176],t=[51,3,193],fov=70,note='Tượng bên phải khi đứng trong trường nhìn ra đường; bố cục sân và dãy nhà đã cập nhật theo Google Maps.',mobile=dict(p=[65,24,176],t=[55,2.5,192],fov=65))
}
views['top']['mobile']=dict(p=[74,330,104],t=[74,0,104],fov=65)
views['overview']['mobile']=dict(p=[300,300,390],t=[74,7,108],fov=60)
extra=ROOT/'qa/interior_views.json'
if extra.exists():views.update(json.loads(extra.read_text(encoding='utf-8')))
path=ROOT/'preview/detail.html';page=path.read_text(encoding='utf-8')
page=re.sub(r'const views=\{.*?\n\};\nconst names=', 'const views='+json.dumps(views,ensure_ascii=False,indent=1)+';\nconst names=',page,count=1,flags=re.S)
# The first pass may already have JSON syntax from an earlier v3 run.
if 'mặt bằng v3' not in page:
    page=re.sub(r'const views=.*?;\nconst names=', 'const views='+json.dumps(views,ensure_ascii=False,indent=1)+';\nconst names=',page,count=1,flags=re.S)
apply="""function applyView(id){const base=views[id]||views.overview;const v=camera.aspect<.8&&base.mobile?{...base,...base.mobile}:base;target.fromArray(v.t);camera.position.fromArray(v.p);camera.fov=v.fov||60;if(camera.aspect<.8&&!base.mobile&&['overview','top','gate','north','tower'].includes(id)){camera.fov=65;camera.position.sub(target).multiplyScalar(1.8).add(target)}camera.updateProjectionMatrix();const d=camera.position.clone().sub(target);radius=d.length();theta=Math.atan2(d.x,d.z);phi=Math.acos(d.y/radius);camera.lookAt(target);picker.value=id;document.querySelector('#caption').textContent=v.label;document.querySelector('header p.small').textContent=v.note;document.body.dataset.camera=id;render()}
picker.onchange"""
page=re.sub(r'function applyView\(id\)\{.*?\n?picker\.onchange',lambda m:apply,page,count=1,flags=re.S)
page=page.replace('Lê Quý Đôn · Chi tiết &amp; tượng','Lê Quý Đôn · Mặt bằng v3')
page=page.replace('Nội thất đề xuất · giữ bố cục v1 · vật liệu vanilla.','Mặt bằng theo Google Maps · độ cao và nội thất ước dựng.')
page=page.replace('LQD_DaNang_Detail_Bedrock_v2.mcworld','LQD_DaNang_Layout_Bedrock_v3.mcworld')
if '>Google Maps</a>' not in page:
    page=page.replace('</nav>','<a href="https://www.google.com/maps?cid=681546677781845227" target="_blank" rel="noopener">Google Maps</a></nav>')
page=page.replace("applyView(params.get('view')||'library')","applyView(params.get('view')||'overview')")
page=re.sub(r'(mesh\.bin(?:\.gz)?|metadata\.json|atlas\.png|sign_texts\.json)(?:\?v=[a-f0-9]+)?',lambda m:m[1]+'?v='+digest[:12],page)
page=page.replace('https://ben11304.github.io/lqd-danang-minecraft/qa/detail_board.jpg','https://ben11304.github.io/lqd-danang-minecraft/qa/v3_overview.png')
path.write_text(page,encoding='utf-8')
raw=(ROOT/'preview/mesh.bin').read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
(ROOT/'preview/mesh.bin.gz').write_bytes(packed)
assert gzip.decompress(packed)==raw
(ROOT/'qa/web_build.json').write_text(json.dumps({'version':'layout_v3','campus_sha256':digest,'mesh_raw_bytes':len(raw),'mesh_gzip_bytes':len(packed),'gzip_roundtrip':'passed'},indent=2),encoding='utf-8')
print(json.dumps({'views':list(views),'source_sha256':digest,'gzip_bytes':len(packed)}))
