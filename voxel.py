from pathlib import Path
import json,math
ROOT=Path(__file__).parent
class Builder:
    def __init__(self,name):self.name=name;self.blocks={}
    def set(self,x,y,z,block):self.blocks[(int(round(x)),int(round(y)),int(round(z)))]=block.removeprefix('minecraft:')
    def fill(self,x1,y1,z1,x2,y2,z2,block):
        for y in range(int(min(y1,y2)),int(max(y1,y2))+1):
            for z in range(int(min(z1,z2)),int(max(z1,z2))+1):
                for x in range(int(min(x1,x2)),int(max(x1,x2))+1):self.set(x,y,z,block)
    def line(self,x1,y1,z1,x2,y2,z2,block):
        n=max(1,int(math.ceil(max(abs(x2-x1),abs(y2-y1),abs(z2-z1)))))
        for i in range(n+1):
            t=i/n;self.set(x1+(x2-x1)*t,y1+(y2-y1)*t,z1+(z2-z1)*t,block)
    def polygon(self,points,y1,y2,block):
        minx=math.floor(min(p[0] for p in points));maxx=math.ceil(max(p[0] for p in points));minz=math.floor(min(p[1] for p in points));maxz=math.ceil(max(p[1] for p in points))
        for z in range(minz,maxz+1):
            for x in range(minx,maxx+1):
                inside=False;j=len(points)-1
                for i in range(len(points)):
                    xi,zi=points[i];xj,zj=points[j]
                    if ((zi>z+.5)!=(zj>z+.5)) and x+.5<(xj-xi)*(z+.5-zi)/(zj-zi)+xi:inside=not inside
                    j=i
                if inside:self.fill(x,y1,z,x,y2,z,block)
    def disk(self,cx,cz,r,y1,y2,block):self.ring(cx,cz,r,0,y1,y2,block)
    def ring(self,cx,cz,outer,inner,y1,y2,block,start_degrees=0,end_degrees=360):
        for z in range(math.floor(cz-outer),math.ceil(cz+outer)+1):
            for x in range(math.floor(cx-outer),math.ceil(cx+outer)+1):
                dx=x+.5-cx;dz=z+.5-cz;dist=math.hypot(dx,dz);a=math.degrees(math.atan2(dz,dx))
                while a<start_degrees:a+=360
                if inner<=dist<=outer and a<=end_degrees:self.fill(x,y1,z,x,y2,z,block)
    def save(self,path):
        palette=sorted(set(self.blocks.values()));ids={v:i for i,v in enumerate(palette)}
        out={'name':self.name,'palette':palette,'blocks':[[x,y,z,ids[b]] for (x,y,z),b in sorted(self.blocks.items())]}
        p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,separators=(',',':')),encoding='utf-8')
        return {'name':self.name,'blocks':len(self.blocks),'file':str(p),'bounds':[[min(v[i] for v in self.blocks),max(v[i] for v in self.blocks)] for i in range(3)]}
