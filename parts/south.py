"""South crescent, west return and characteristic split entrance arch.

Reference based exterior; room divisions and stairs are inferred for playability.
All dimensions are on the shared approximate one metre grid.
"""
from pathlib import Path
import sys, math, json
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voxel import Builder

CREAM='smooth_sandstone'
WHITE='white_concrete'
GLASS='light_gray_stained_glass'
RAIL='iron_bars[east=true,north=false,south=false,waterlogged=false,west=true]'

def build():
    b=Builder('south')
    cx,cz=102,161
    def point(r,a):
        return cx+r*math.cos(math.radians(a)),cz+r*math.sin(math.radians(a))
    def ray(r1,r2,a,y1,y2,mat):
        x1,z1=point(r1,a); x2,z2=point(r2,a)
        for y in range(y1,y2+1): b.line(x1,y,z1,x2,y,z2,mat)
    # The crescent is a band: its centre and courtyard stay empty.
    for y in (64,68,72,76):
        b.ring(cx,cz,31,23,y,y,'smooth_stone',0,180)
    b.ring(cx,cz,31,23,77,77,'light_gray_concrete',0,180)
    b.ring(cx,cz,31,30,77,77,WHITE,0,180)
    b.ring(cx,cz,24,23,77,77,WHITE,0,180)
    for floor in range(3):
        low=65+4*floor
        # Outer rooms are enclosed, with broad glazing and repeated white piers.
        b.ring(cx,cz,31,30,low,low+2,CREAM,0,180)
        b.ring(cx,cz,27,26,low,low+2,CREAM,0,180)
        # Glazed outer bays separated by cream/white columns, not a solid facade.
        for a in range(3,180,14):
            b.ring(cx,cz,31,30,low+1,low+2,GLASS,a,min(a+9,180))
        # Corridor-side classroom windows remain broad two-block-high openings.
        # Without these, an entrance view only sees small door slits above rails.
        for a in range(0,180,14):
            b.ring(cx,cz,27,26,low+1,low+2,GLASS,a,min(a+5,180))
        for a in range(0,181,14):
            ray(30,31,a,low,low+2,WHITE)
            ray(23,24,a,low,low+2,'quartz_block')
            # Partition wall is behind corridor, with one playable door per bay.
            ray(27,30,a,low,low+2,CREAM)
            if a+7<180:
                for da in (-1,0,1): ray(26,27,a+7+da,low,low+1,'air')
        # Balcony edge follows the curve. Upper floors have parapet at foot level.
        if floor:
            b.ring(cx,cz,24,23,low,low,CREAM,0,180)
        b.ring(cx,cz,31,30,low+3,low+3,WHITE,0,180)
        b.ring(cx,cz,24,23,low+3,low+3,WHITE,0,180)
    # End walls tie into the west return and the parent academic connection.
    for a in (0,180):
        ray(24,31,a,65,75,CREAM)
        for low in (65,69,73):ray(24,26,a,low,low+1,'air')
    # A long west return: flat pale roof, repeated windows, open south corridor.
    for y in (64,68,72,76):b.fill(21,y,149,103,y,160,'smooth_stone')
    b.fill(21,77,149,103,77,160,'light_gray_concrete')
    b.fill(21,77,149,103,77,149,WHITE)
    b.fill(21,77,160,103,77,160,WHITE)
    for floor in range(3):
        low=65+4*floor
        b.fill(21,low,149,103,low+2,149,CREAM)
        b.fill(21,low,156,103,low+2,156,CREAM)
        # Square west end, modest glazing instead of an invented tower.
        b.fill(21,low,149,21,low+2,160,CREAM)
        b.fill(21,low+1,151,21,low+2,154,GLASS)
        for x in range(24,101,7):
            b.fill(x,low+1,149,x+3,low+2,149,GLASS)
            b.fill(x,low,156,x+1,low+1,156,'air')
            b.fill(x-2,low,160,x-2,low+2,160,'quartz_block')
            b.fill(x+5,low,149,x+5,low+2,156,CREAM)
            b.fill(x+2,low+1,156,x+4,low+2,156,GLASS)
            b.fill(x+5,low,156,x+5,low+2,156,WHITE)
            # Just two furnished representative classrooms; other rooms stay open.
            if x in (38,59):
                b.fill(x,low+1,150,x+3,low+2,150,'green_concrete')
                for dx in (0,2):
                    b.set(x+dx,low,153,'oak_slab[type=bottom,waterlogged=false]')
                    b.set(x+dx,low,154,'oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
        if floor:b.fill(22,low,160,102,low,160,CREAM)
        b.fill(21,low+3,149,103,low+3,149,WHITE)
        b.fill(21,low+3,160,103,low+3,160,WHITE)
    # Stairwell at west end, two straight flights up to the corridor landings.
    # Clear only this building, including the intermediate slabs above each flight.
    for base in (65,69):
        b.fill(22,base,157,28,base+3,159,'air')
        for i in range(4):
            b.fill(23+i,base+i,157,23+i,base+i,159,
                   'smooth_stone_slab[type=bottom,waterlogged=false]')
            if i>0:b.fill(23+i,base,157,23+i,base+i-1,159,'smooth_stone')
        b.fill(27,base+3,157,28,base+3,159,'smooth_stone')
    # Restore longitudinal corridor slab away from stairs and add inner-side safety rail.
    for y in (69,73):b.fill(22,y,160,102,y,160,CREAM)
    # Entrance uses two quarter ellipses of different span/height.
    # The white undersides are visible in the primary street photographs.
    def arch(x1,x2,height,left):
        for x in range(x1,x2+1):
            t=(x-x1)/(x2-x1)
            h=height*math.sqrt(max(0,1-(1-t if left else t)**2))
            y=65+round(h)
            b.fill(x,y-1,203,x,y-1,205,WHITE)
            b.fill(x,y,203,x,y+1,205,'light_blue_concrete')
    arch(58,75,10,True)
    arch(77,88,7,False)
    b.fill(75,65,202,77,77,205,'terracotta')
    b.fill(75,65,202,77,65,205,'stone_bricks')
    # Short, partially retracted gate leaves leave a generous route through.
    for x1,x2 in ((60,63),(71,74),(79,80),(85,87)):
        b.fill(x1,65,204,x2,65,204,'green_concrete')
        b.fill(x1,66,204,x2,68,204,RAIL)
        b.fill(x1,69,204,x2,69,204,'green_concrete')
    b.fill(89,65,203,103,70,205,'terracotta')
    b.fill(89,65,203,103,65,205,'stone_bricks')
    # A light trim suggests applied metal lettering; exact Vietnamese name goes
    # in the named Minecraft sign entity at export rather than giant fake letters.
    b.fill(91,68,206,101,68,206,'yellow_terracotta')
    b.fill(91,66,206,100,66,206,'smooth_sandstone')
    # Short fence returns, local to entrance; root owns the campus boundary.
    for x1,x2 in ((48,57),(104,113)):
        b.fill(x1,65,204,x2,65,204,'stone_bricks')
        b.fill(x1,66,204,x2,68,204,RAIL)
        b.fill(x1,69,204,x2,69,204,'green_concrete')
        for x in (x1,x2):b.fill(x,65,204,x,70,204,'quartz_block')
    return b

if __name__=='__main__':
    b=build()
    print(json.dumps(b.save('parts/south.json')))
