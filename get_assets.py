from pathlib import Path
import urllib.request,json,zipfile,hashlib,io,tarfile
R=Path(__file__).parent
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'LQD-local-build/1.0'}),timeout=60) as f:return f.read()
v=json.loads(get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'))
entry=next(x for x in v['versions'] if x['id']=='1.20.4')
meta=json.loads(get(entry['url']));client=meta['downloads']['client']
path=R/'vendor/client-1.20.4.jar'
if not path.exists():path.write_bytes(get(client['url']))
assert hashlib.sha1(path.read_bytes()).hexdigest()==client['sha1']
with zipfile.ZipFile(path) as z:
    files=[n for n in z.namelist() if n.startswith(('assets/minecraft/textures/block/','assets/minecraft/blockstates/','assets/minecraft/models/block/')) and n.endswith(('.png','.json'))]
    for n in files:
        p=R/'vendor'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
package=json.loads(get('https://registry.npmjs.org/three/0.160.1'))
tgz=get(package['dist']['tarball'])
with tarfile.open(fileobj=io.BytesIO(tgz),mode='r:gz') as tf:
    for src,dst in [('package/build/three.module.js','three.module.js'),('package/LICENSE','THREE_LICENSE.txt')]:
        (R/'vendor'/dst).write_bytes(tf.extractfile(src).read())
(R/'vendor/asset_sources.json').write_text(json.dumps({'minecraft_version':'1.20.4','manifest':entry['url'],'client':client,'three':package['dist']},indent=2),encoding='utf-8')
print(json.dumps({'assets':len(files),'client_sha1':client['sha1']}))
