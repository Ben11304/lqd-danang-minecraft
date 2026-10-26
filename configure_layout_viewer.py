"""Use v3 cameras and the current content hash in the static web viewer."""
from pathlib import Path
import json,re,hashlib,gzip
ROOT=Path(__file__).resolve().parent
digest=hashlib.sha256((ROOT/'campus.json').read_bytes()).hexdigest()
assert json.loads((ROOT/'preview/metadata.json').read_text())['source_sha256']==digest
views={
 'overview':dict(label='Toàn cảnh · mặt bằng v3.2',p=[245,175,310],t=[74,7,108],fov=48,note='Cập nhật hai vườn trong và các mái phụ quan sát trên Google Maps. Chi tiết dưới tán cây và công năng bãi xe còn cần đối chiếu.'),
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
views['connector']=dict(label='Lối nối nhà thi đấu · bổ sung từ ảnh vệ tinh',p=[70,2.7,103],t=[69.5,2.7,89],fov=65,note='Dải mái hẹp nối nhà thi đấu với nút giao giữa trường. Chiều cao, cột và lan can còn ước dựng; chưa gán tên căn tin hoặc sảnh C.')
views['connector_context']=dict(label='Khu nối phía bắc · toàn cảnh',p=[87,32,123],t=[73,5,94],fov=64,note='Đã bổ sung đoạn nối dài khoảng 28 m bị thiếu ở bản v3. Công năng các phòng quanh khu này đang được đối chiếu với ảnh mặt đất.')
views['connector_from_academic']=dict(label='Đường nối · từ dãy học nhìn sang khối bắc',p=[70,2.7,118],t=[69.3,2.7,83],fov=65,note='Góc kiểm tra tuyến bạn nhắc từ sảnh C sang căn tin. Đây là đoạn mái nối hiện có; tên hai đầu chưa được xác nhận trên tư liệu định vị.')
views['connector_from_north']=dict(label='Đường nối · từ khối bắc nhìn về dãy học',p=[69,2.7,84],t=[70.5,2.7,120],fov=65,note='Nhìn ngược qua đường nối để thấy điểm tiếp giáp và lối đi. Kiểm tra model cho thấy đường xuyên suốt; chưa xác nhận độc lập hai đầu là căn tin và sảnh C.')
views['connector_top']=dict(label='Đường nối · mặt bằng hai đầu',p=[70,62,103],t=[70,0,103],fov=52,note='Mặt bằng đoạn mái nối dài khoảng 28 m. Chiều cao, cột và lan can còn ước dựng; góc này dùng đối chiếu tuyến sảnh C–căn tin bạn nhắc.',mobile=dict(p=[70,85,103],t=[70,0,103],fov=60))
views['garden_south']=dict(label='Vườn trong phía nam · đài tròn và bồn cong',p=[79,3,147],t=[90,2,144],fov=72,note='Vị trí đài tròn đối chiếu ảnh vệ tinh; hồ súng và đường đá tham khảo ảnh sân trường. Đường bồn bị tán che còn ước dựng; chưa chốt tên sảnh A.')
views['garden_south_context']=dict(label='Vườn trong phía nam · nhìn từ trên',p=[89,37,151],t=[89,0,143],fov=64,note='Giữ khoảng vườn giữa hai dãy ngang và dãy cong. Đài nước có tượng cá heo giản lược, khác với tượng Lê Quý Đôn ở sân trước.')
views['garden_b']=dict(label='Vườn cạnh sảnh B · lối đá và giàn cây',p=[42,2.7,140],t=[59,4,140],fov=70,note='Ảnh có tên sảnh B và tương quan dãy nhà hỗ trợ vị trí sân phía tây. Giàn cây, lối đá và bồn được dựng lại; nhịp giàn và phần dưới tán còn ước lượng.')
views['garden_b_context']=dict(label='Vườn cạnh sảnh B · nhìn từ trên',p=[44,52,148],t=[44,0,142],fov=66,note='Khoảng sân dài giữa hai dãy ngang, phía tây trục nối. Ranh vườn theo ảnh vệ tinh; đường đi và giàn dây leo dựa thêm ảnh mặt đất.')
views['parking']=dict(label='Dãy mái phụ phía đông · công năng chưa chốt',p=[131,2.7,180],t=[139,2.5,167],fov=68,note='Mái dài sát phía đông khối oval được bổ sung theo ảnh vệ tinh. Chưa xác minh đây là bãi xe; chiều cao và cột còn ước dựng.')
views['parking_context']=dict(label='Mái phụ phía đông · tương quan với khối oval',p=[164,35,201],t=[137,4,168],fov=62,note='Bổ sung phần mái thấp bị thiếu, giữ khoảng đi dọc bên trong hàng rào. Vị trí đỗ xe và lối vào bãi chưa được xác nhận.')
views['parking_northwest']=dict(label='Các mái phụ phía tây bắc',p=[-22,60,112],t=[27,3,50],fov=64,note='Bổ sung mái ngang phía bắc và mái dài sát rào phía tây theo ảnh vệ tinh. Công năng bãi xe và chiều cao chưa được xác minh bằng ảnh mặt đất.')
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
page=re.sub(r'Lê Quý Đôn · Mặt bằng v3(?:\.\d+)?</h1>','Lê Quý Đôn · Mặt bằng v3.2</h1>',page)
page=page.replace('Nội thất đề xuất · giữ bố cục v1 · vật liệu vanilla.','Mặt bằng theo Google Maps · độ cao và nội thất ước dựng.')
page=page.replace('LQD_DaNang_Detail_Bedrock_v2.mcworld','LQD_DaNang_Layout_Bedrock_v3.mcworld')
page=re.sub(r'LQD_DaNang_Layout_Bedrock_v3\.mcworld(?:\?v=[a-f0-9]+)?','LQD_DaNang_Layout_Bedrock_v3.mcworld?v='+digest[:12],page)
if '>Google Maps</a>' not in page:
    page=page.replace('</nav>','<a href="https://www.google.com/maps?cid=681546677781845227" target="_blank" rel="noopener">Google Maps</a></nav>')
page=page.replace("applyView(params.get('view')||'library')","applyView(params.get('view')||'overview')")
page=re.sub(r'(mesh\.bin(?:\.gz)?|metadata\.json|atlas\.png|sign_texts\.json)(?:\?v=[a-f0-9]+)?',lambda m:m[1]+'?v='+digest[:12],page)
page=page.replace('https://ben11304.github.io/lqd-danang-minecraft/qa/detail_board.jpg','https://ben11304.github.io/lqd-danang-minecraft/qa/v3_overview.png')
path.write_text(page,encoding='utf-8')
raw=(ROOT/'preview/mesh.bin').read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
(ROOT/'preview/mesh.bin.gz').write_bytes(packed)
assert gzip.decompress(packed)==raw
(ROOT/'qa/web_build.json').write_text(json.dumps({'version':'layout_v3.2','campus_sha256':digest,'mesh_raw_bytes':len(raw),'mesh_gzip_bytes':len(packed),'gzip_roundtrip':'passed'},indent=2),encoding='utf-8')
print(json.dumps({'views':list(views),'source_sha256':digest,'gzip_bytes':len(packed)}))
