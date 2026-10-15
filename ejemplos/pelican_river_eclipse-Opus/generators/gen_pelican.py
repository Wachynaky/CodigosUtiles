#!/usr/bin/env python3
r"""Emit one self-contained ClickHouse SELECT: a pelican cycling on a river.

Python describes vector geometry and emits SQL; it never renders pixels or
encodes an image. ClickHouse evaluates signed-distance fields, shading,
supersampling, the eclipse, water, reflections and grain, then writes FORMAT PNG.

    python3 generators/gen_pelican.py > queries/pelican_river_eclipse.sql
    clickhouse local --output_format_image_width 2400 \
        --output_format_image_height 1500 --param_SAMPLES 4 \
        --queries-file queries/pelican_river_eclipse.sql > images/pelican_river_eclipse.png

The composition uses a 1600 x 1000 artboard. Other aspect ratios crop/extend
the view horizontally; resolution and samples remain runtime query parameters.
Only the Python standard library is needed to generate the query.
"""

import math
import sys


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def sql(value):
    if isinstance(value, float):
        return f"{value:.6f}"  # Keep every geometry/color field Float64.
    if isinstance(value, int):
        return str(value)
    if isinstance(value, tuple):
        return "(" + ",".join(map(sql, value)) + ")"
    if isinstance(value, list):
        return "[" + ",\n".join(map(sql, value)) + "]"
    raise TypeError(value)


class Path:
    """Sample Bezier outlines into constant geometry, never into pixels."""

    def __init__(self, x, y):
        self.points = [(float(x), float(y))]

    def line(self, x, y):
        self.points.append((float(x), float(y)))
        return self

    def curve(self, x1, y1, x2, y2, x3, y3, n=12):
        x0, y0 = self.points[-1]
        for i in range(1, n + 1):
            t = i / n
            u = 1 - t
            self.points.append((u**3*x0 + 3*u*u*t*x1 + 3*u*t*t*x2 + t**3*x3,
                                u**3*y0 + 3*u*u*t*y1 + 3*u*t*t*y2 + t**3*y3))
        return self


class Scene:
    """Shapes: kind, geometry, rotation, gradient, opacity, bounds, edges, rim."""

    def __init__(self):
        self.shapes = []

    def add(self, kind, a, b, r, angle, color, bottom, opacity, bounds, edges, rim):
        theta = math.radians(angle)
        self.shapes.append((kind, float(a[0]), float(a[1]), float(b[0]), float(b[1]),
                            float(r), math.cos(theta), math.sin(theta), rgb(color),
                            rgb(bottom or color), float(opacity),
                            tuple(float(v) for v in bounds), edges, float(rim)))

    def ellipse(self, x, y, rx, ry, color, bottom=None, angle=0, opacity=1, rim=0):
        t = math.radians(angle)
        dx = math.hypot(rx * math.cos(t), ry * math.sin(t))
        dy = math.hypot(rx * math.sin(t), ry * math.cos(t))
        self.add(1, (x, y), (rx, ry), 0, angle, color, bottom, opacity,
                 (x-dx-2, y-dy-2, x+dx+2, y+dy+2), [], rim)

    def line(self, x1, y1, x2, y2, width, color, bottom=None, opacity=1, rim=0):
        r = width / 2
        self.add(2, (x1, y1), (x2, y2), r, 0, color, bottom, opacity,
                 (min(x1,x2)-r-2, min(y1,y2)-r-2,
                  max(x1,x2)+r+2, max(y1,y2)+r+2), [], rim)

    def ring(self, x, y, radius, width, color, bottom=None, opacity=1, rim=0):
        r = radius + width / 2 + 2
        self.add(4, (x,y), (radius,0), width / 2, 0, color, bottom, opacity,
                 (x-r,y-r,x+r,y+r), [], rim)

    def poly(self, points, color, bottom=None, opacity=1, rim=0):
        if isinstance(points, Path):
            points = points.points
        points = [(float(x), float(y)) for x, y in points]
        # Drop identical vertices: distance-to-segment divides by edge length.
        points = [p for i,p in enumerate(points) if p != points[i-1]]
        edges = [(a[0],a[1],b[0],b[1])
                 for a,b in zip(points, points[1:] + points[:1])]
        xs, ys = zip(*points)
        self.add(3, (0,0), (0,0), 0, 0, color, bottom, opacity,
                 (min(xs)-2,min(ys)-2,max(xs)+2,max(ys)+2), edges, rim)


land = Scene()
bird = Scene()
front = Scene()

# Distant rose-colored cloud ribbons and mountain ranges.
land.poly(Path(-50,164).curve(180,137,340,188,579,159)
          .curve(386,195,214,171,-50,185), "c2949b", opacity=.16)
land.poly(Path(850,170).curve(1120,130,1310,181,1670,150)
          .line(1670,171).curve(1260,191,1100,155,850,180), "f2aa8b", opacity=.20)
land.poly(Path(-20,281).curve(182,250,261,292,449,274)
          .curve(294,304,113,287,-20,298), "e8a095", opacity=.15)
land.poly(Path(1360,265).curve(1440,247,1515,268,1625,251)
          .line(1625,265).curve(1510,284,1450,260,1360,276), "ffd3a2", opacity=.20)

land.poly([(-40,460),(-40,388),(49,364),(128,393),(228,356),(328,414),
           (417,387),(539,437),(674,409),(794,444),(923,407),(1030,450),
           (1142,421),(1251,450),(1372,395),(1479,422),(1615,375),(1640,480)],
          "827b91", "a48b96")
land.poly(Path(-40,427).curve(123,368,224,422,364,443)
          .curve(523,380,622,443,751,458).line(1650,490).line(-40,493),
          "4a6575", "75838b")
land.poly(Path(1000,467).curve(1120,402,1197,441,1260,427)
          .curve(1430,351,1519,397,1650,361).line(1650,492).line(1000,492),
          "3a5867", "65777d")

# River banks point toward the open river and leave room for the bicycle.
land.poly(Path(-50,446).curve(105,440,208,477,390,485)
          .curve(308,504,249,505,215,526).curve(146,548,49,552,-50,585),
          "254b57", "386c71")
land.poly(Path(1650,438).curve(1506,451,1440,473,1314,483)
          .curve(1370,505,1484,505,1516,540).line(1650,574),
          "234853", "38666a")

# Small cypress silhouettes along the banks (all geometry becomes SQL constants).
for x,y,h in [(18,453,68),(48,457,85),(87,461,51),(122,467,63),
              (154,472,40),(183,476,44),(228,480,32),(277,484,23),
              (1408,471,32),(1450,466,52),(1478,461,61),(1522,454,85),
              (1556,452,66),(1594,447,104)]:
    land.poly(Path(x-9,y).curve(x-18,y-h*.37,x-6,y-h*.88,x,y-h)
              .curve(x+7,y-h*.80,x+18,y-h*.3,x+9,y), "284c59")
    land.line(x,y-5,x,y+5,2,"284c59")

# Quiet birds near the eclipse, silhouettes drawn with tapered Bezier polygons.
for x,y,s in [(1065,216,1.0),(1119,198,.65),(1392,302,.8)]:
    land.poly(Path(x-19*s,y+3*s).curve(x-12*s,y-13*s,x-3*s,y-7*s,x,y)
              .curve(x+10*s,y-12*s,x+19*s,y-9*s,x+27*s,y-4*s)
              .curve(x+11*s,y-8*s,x+7*s,y+1*s,x,y+4*s)
              .curve(x-8*s,y-4*s,x-13*s,y-5*s,x-19*s,y+3*s), "283e51")

# Water displaced by each tire: luminous ripples and elongated wakes.
for x in (535,965):
    for dx,dy,rx,ry,op in [(0,0,113,11,.45),(-9,8,151,15,.27),
                           (-22,17,181,19,.18),(-39,29,208,21,.10)]:
        bird.ellipse(x+dx,843+dy,rx,ry,"aec9bd",opacity=op)
        bird.ellipse(x+dx-6,842+dy,rx*.88,ry*.65,"315e65",opacity=op+.08)
    bird.line(x-192,851,x-110,850,2,"d3d8bc",opacity=.40)
    bird.line(x+78,847,x+144,847,2,"f7d0a3",opacity=.60)

# Far leg and webbed foot, behind the bicycle frame.
bird.line(673,490,665,579,20,"b07445","734641",rim=.18)
bird.line(665,579,692,714,15,"b98348","70453d",rim=.15)
bird.ellipse(667,579,12,12,"bd8551","956247")
bird.poly(Path(684,706).curve(697,708,704,719,723,721)
          .line(727,736).line(710,730).line(697,739).line(680,731)
          .line(666,733).curve(668,721,678,718,684,706),"dc9851","a45c3d",rim=.25)

# Wheels. Narrow ivory sidewalls, metallic rims and radial spokes.
for x in (535,965):
    bird.ring(x,709,133,19,"263a43","122d38",rim=.40)
    bird.ring(x,709,131,8,"e8d4ad","ab9983",rim=.22)
    bird.ring(x,709,123,3.4,"92afac","73999c")
    bird.ring(x,709,138,1.3,"f9d6a8",opacity=.75)
    for i in range(24):
        t = 2*math.pi*i/24
        # Slightly crossed spokes: the hub endpoint is rotated 45 degrees.
        a = (x+9*math.cos(t+.8),709+9*math.sin(t+.8))
        b = (x+121*math.cos(t),709+121*math.sin(t))
        bird.line(*a,*b,1.05,"c2c8b6",opacity=.75)
    bird.ellipse(x,709,12,12,"cbd1bd","486e77",rim=.3)
    bird.ellipse(x-2,706,3,3,"f9e6c1")

# Frame, chain, mudguards, crank, pedals. The geometry is a real diamond frame.
bird.line(535,709,731,688,8,"1b3641")
bird.line(535,719,733,705,3,"b8ac87")
bird.line(535,698,733,674,3,"d5c6a1")
bird.ring(731,692,27,5,"d6c7a0","57767a",rim=.3)
bird.ring(731,692,19,2,"7e9290")
for a,b,width in [((535,709),(659,554),10),((535,709),(731,692),10),
                  ((659,554),(731,692),15),((659,554),(898,554),14),
                  ((731,692),(915,606),17),((898,554),(915,606),19),
                  ((910,602),(965,709),12)]:
    bird.line(*a,*b,width+3,"743d3b","443c43")
    bird.line(*a,*b,width,"ed7954","aa4240",rim=.25)
    bird.line(a[0]-1,a[1]-3,b[0]-1,b[1]-3,2,"ffbd82",opacity=.75)

# Curved fenders, generated as short metallic capsule strokes.
for x in (535,965):
    for i in range(23):
        a = math.radians(201+i*6)
        b = math.radians(201+(i+1)*6)
        bird.line(x+145*math.cos(a),709+145*math.sin(a),
                  x+145*math.cos(b),709+145*math.sin(b),5,"b75d48","915149")
        bird.line(x+147*math.cos(a),708+147*math.sin(a),
                  x+147*math.cos(b),708+147*math.sin(b),1.2,"ffd3a0",opacity=.7)

bird.line(659,554,648,519,11,"b7c7bd","6c8d8e",rim=.35)
bird.poly(Path(612,514).curve(643,504,677,509,691,519)
          .curve(674,534,631,535,609,526).curve(601,520,605,516,612,514),
          "62463e","302f37",rim=.15)
bird.line(902,556,882,482,10,"b4c5b9","60868b",rim=.5)
bird.line(882,482,917,476,9,"c9d4c4","69969b",rim=.4)
bird.line(917,476,932,486,11,"334a50","1c3944")
bird.line(926,482,943,489,14,"b27350","6c493f",rim=.2)
# Brake cable, lamp and a little brass bell.
cable = Path(917,489).curve(938,501,936,550,918,587,n=14).points
for a,b in zip(cable,cable[1:]):
    bird.line(*a,*b,1.8,"2c4850")
bird.line(926,562,949,552,4,"8ba9a5")
bird.ellipse(950,548,15,13,"bc9a62","735c48",angle=-16,rim=.4)
bird.ellipse(960,546,7,10,"ffdda2","d7bc80",angle=-16)
bird.ellipse(907,469,9,6,"f4c482","a3754b",rim=.3)

bird.line(731,692,692,726,8,"a5b9ad","4a7178",rim=.3)
bird.line(677,730,711,728,10,"314951")
bird.line(731,692,772,650,9,"c1cec0","4b747a",rim=.4)
bird.line(756,652,794,651,9,"334952")
bird.ellipse(731,692,11,11,"c4cdb8","608b8e",rim=.4)

# Pelican tail and body. Pale warm top surfaces catch the light of the corona.
bird.poly(Path(570,398).curve(525,385,492,365,467,367)
          .line(482,388).line(462,391).curve(489,421,534,442,582,436),
          "ede7d4","a3b4b0",rim=.20)
bird.poly(Path(556,412).curve(510,411,490,401,480,401)
          .curve(504,438,534,451,577,449),"43585e","203e4b",rim=.15)

bird.poly(Path(553,388).curve(590,355,653,342,715,364)
          .curve(766,377,784,422,774,462).curve(753,505,701,525,645,514)
          .curve(585,505,553,475,542,440).curve(532,419,536,404,553,388),
          "fff4d9","b3bcb4",rim=.26)

# Long S-curved neck: its outline, including the throat, is one continuous shape.
bird.poly(Path(713,398).curve(749,376,768,352,768,316)
          .curve(764,277,775,230,804,209).curve(824,192,858,200,872,220)
          .curve(884,240,872,263,853,272).curve(820,286,823,313,821,338)
          .curve(826,377,813,430,779,452).curve(744,470,715,443,713,398),
          "fff5dc","bec7be",rim=.22)
bird.poly(Path(800,259).curve(785,301,800,337,782,378)
          .curve(770,405,755,418,738,430).curve(774,430,800,400,805,366)
          .curve(815,319,802,300,820,271), "e4dcc5","98ada8",opacity=.55)

# Folded wing with scalloped covert feathers and dark flight-feather tips.
bird.poly(Path(564,395).curve(605,369,679,373,720,409)
          .curve(712,447,653,470,600,460).curve(565,448,547,423,564,395),
          "e6e1cb","718c91",rim=.20)
for i in range(10):
    bird.ellipse(560+i*11.5,431+i*1.4,44-i*.6,10.5,
                 "53696f" if i < 6 else "8e9f9b", "2b4955" if i < 6 else "587780",
                 angle=-25+i*3.4,rim=.13)
for i in range(9):
    bird.ellipse(576+i*11.8,405+math.sin(i*.33)*15,37-i*1.0,10.0,
                 "fff1d5","b5bfaf",angle=27-i*3.2,rim=.13)
bird.poly(Path(563,393).curve(602,368,663,385,690,406)
          .curve(650,392,619,394,587,412).curve(572,415,557,406,563,393),
          "fff5dc","d7d7bf",rim=.1)

# Near leg bends naturally onto the forward pedal.
bird.poly(Path(710,491).curve(730,484,750,492,748,509)
          .line(763,559).curve(767,572,759,581,750,579)
          .curve(740,577,739,570,739,562).line(724,517).line(709,510),
          "dfac69","b67c44",rim=.25)
bird.line(752,569,754,635,16,"e7b86d","aa7245",rim=.22)
bird.ellipse(752,567,11,10,"e5ae60","c38e51",rim=.2)
bird.poly(Path(748,628).curve(761,629,765,639,778,640)
          .line(799,652).line(778,654).line(771,664).line(757,656)
          .line(737,659).line(730,649).curve(737,641,745,642,748,628),
          "f8bb65","c08041",rim=.25)
bird.line(750,641,777,650,1.3,"a47748",opacity=.7)
bird.line(749,645,759,653,1.3,"a47748",opacity=.7)

# A second wing reaches the handlebar; individual feathers curl around the grip.
bird.poly(Path(749,397).curve(773,398,789,426,811,444)
          .curve(843,466,884,459,915,473).line(923,486)
          .curve(875,490,835,493,799,474).curve(771,463,749,441,738,421),
          "fff0d2","b8c0b1",rim=.25)
for i in range(3):
    bird.ellipse(904+i*7,480+i*2,17,5,"f6e9cc","a8b7ac",angle=24+i*10,rim=.1)
bird.poly(Path(761,417).curve(787,447,805,461,848,473)
          .curve(806,473,779,454,761,438),"d4d6be","9bafa7",opacity=.75)

# A small windblown scarf, behind the head and bill.
bird.poly(Path(789,312).curve(745,296,724,320,681,297)
          .curve(653,280,629,290,610,296).line(632,309).line(622,324)
          .curve(679,309,703,344,751,337).line(798,331),
          "e78365","9d4948",rim=.2)
bird.poly(Path(782,308).curve(797,306,813,312,821,321)
          .line(817,335).curve(802,327,792,326,780,330),
          "f19c76","b4514b",rim=.15)

# Round head, expressive eye and unmistakably long bill with a hanging pouch.
bird.ellipse(833,241,47,48,"fff5dc","e0dfc6",angle=-12,rim=.22)
bird.poly(Path(858,254).curve(910,262,1024,272,1102,282)
          .curve(1082,300,1045,314,1014,329).curve(974,356,911,342,878,304)
          .curve(869,291,862,270,858,254),"efb773","cc8050",rim=.2)
bird.poly(Path(878,277).curve(927,303,971,328,1011,317)
          .curve(980,342,930,328,903,308).line(878,277),
          "f2c289","dfa06b",opacity=.75)
bird.poly(Path(866,251).curve(921,250,1035,270,1110,281)
          .curve(1116,283,1113,291,1107,291).curve(1011,282,933,275,867,272),
          "ffd17d","e5a45d",rim=.4)
bird.line(883,271,1100,286,2.2,"aa7048",opacity=.8)
bird.ellipse(1108,285,5.5,4,"c38950",angle=20)
bird.ellipse(895,259,4.0,1.5,"9a7453",angle=5)
bird.ellipse(854,236,11,12,"b9be9d","d7c693",angle=-12)
bird.ellipse(855,235,6.6,7.5,"173440","0d2635")
bird.ellipse(857,232,2.4,2.7,"fff7dc")
bird.ellipse(852,239,1,1,"6caba9")
bird.poly(Path(843,218).curve(851,213,863,216,869,222)
          .curve(858,218,850,219,843,222),"bcbea2")
bird.poly(Path(793,217).curve(790,202,795,189,804,181)
          .line(807,201).line(820,187).line(818,210),"fff3d7","d8ddc3",rim=.2)

# Bright sprays and droplets at the two water contacts, in front of the tires.
for x in (535,965):
    bird.ellipse(x,843,43,4,"e7e3c0",opacity=.85)
    for dx,dy,r in [(-53,-4,2.4),(-39,-15,2),(-27,-7,2.6),
                    (31,-12,2.3),(45,-6,2.1),(58,2,1.5),(-66,6,1.5)]:
        bird.ellipse(x+dx,843+dy,r,r*1.6,"f8e7be",opacity=.80)
    for dx,dy in [(-42,-4),(36,-3)]:
        bird.line(x+dx,843+dy,x+dx*1.35,831+dy,1.4,"e5dec1",opacity=.75)

# Foreground rushes and lily leaves frame the open water.
for x,y,s in [(28,1008,1.2),(78,1008,.8),(1555,1010,1.1),(1600,1010,1.4)]:
    for i in range(6):
        t = (i-2.5)/2.5
        front.poly(Path(x,y).curve(x+t*19*s,y-59*s,x+t*48*s,y-150*s,
                                   x+t*64*s,y-(172-abs(t)*32)*s)
                   .curve(x+t*42*s,y-68*s,x+t*10*s,y-19*s,x+5*s,y),
                   "143d48","123943")
    front.line(x+4,y,x-12*s,y-166*s,2.5,"345b57")
    front.line(x-12*s,y-166*s,x-14*s,y-194*s,7,"644f42","334e4a")

for x,y,rx,ry in [(169,935,38,11),(251,969,51,15),(1382,939,40,10),
                  (1469,894,25,7),(1293,989,46,13)]:
    front.ellipse(x,y+4,rx+5,ry+2,"183e4c",opacity=.45)
    front.ellipse(x,y,rx,ry,"5f8374","284e54",angle=-4,rim=.2)
    front.poly([(x,y),(x+rx+2,y-3),(x+rx*.7,y-ry-2)],"35646a")
    front.line(x-rx*.65,y,x+rx*.60,y,1,"91a28a",opacity=.35)


def let(bindings, body):
    """By-value bindings avoid expanding ClickHouse's call-by-name lambdas."""
    for name, value in reversed(bindings):
        body = f"arrayMap({name} -> {body}, [{value}])[1]"
    return body


def visible(scene, point="p"):
    """Cull the whole layer using its generated bounds, not a hand-set crop."""
    boxes = [shape[11] for shape in scene.shapes]
    xmin, ymin = min(b[0] for b in boxes), min(b[1] for b in boxes)
    xmax, ymax = max(b[2] for b in boxes), max(b[3] for b in boxes)
    return (f"{point}.1>{xmin:.6f} AND {point}.1<{xmax:.6f} AND "
            f"{point}.2>{ymin:.6f} AND {point}.2<{ymax:.6f}")


SEGMENT = let([
    ("sx", "bx-ax"), ("sy", "by-ay"),
    ("st", "clamp(((p.1-ax)*sx+(p.2-ay)*sy)/greatest(sx*sx+sy*sy,0.00001),0.,1.)"),
], "sqrt(pow(p.1-ax-st*sx,2)+pow(p.2-ay-st*sy,2))")

DISTANCE = let([
    ("dx", "p.1-s.2"), ("dy", "p.2-s.3"),
], """multiIf(
    s.1=1, (sqrt(pow((dx*s.7+dy*s.8)/greatest(s.4,0.00001),2)
                  +pow((-dx*s.8+dy*s.7)/greatest(s.5,0.00001),2))-1.)*least(s.4,s.5),
    s.1=2, seg(p,s.2,s.3,s.4,s.5)-s.6,
    s.1=4, abs(sqrt(dx*dx+dy*dy)-s.4)-s.6,
    arrayMin(arrayMap(e -> seg(p,e.1,e.2,e.3,e.4),s.13))
      *if(arraySum(arrayMap(e -> toUInt8(
           ((e.2>p.2)!=(e.4>p.2)) AND
           (p.1 < (e.3-e.1)*(p.2-e.2)/if(abs(e.4-e.2)<0.000001,0.000001,e.4-e.2)+e.1)),s.13))%2=1,-1.,1.)
)""")

FOLD = let([
    ("dd", "sdf(p,s)"),
    ("al", "clamp(0.5-dd/aa,0.,1.)*s.11"),
    ("cc", "tuplePlus(mix(s.9,s.10,clamp((p.2-s.12.2)/greatest(s.12.4-s.12.2,0.001),0.,1.)),"
           "tupleMultiplyByNumber((0.34,0.23,0.12),exp(-abs(dd)/1.6)*s.14))"),
], "(cc.1*al+a.1*(1.-al),cc.2*al+a.2*(1.-al),cc.3*al+a.3*(1.-al),al+a.4*(1.-al))")

SKY = let([
    ("ht", "clamp(p.2/488.,0.,1.)"),
    ("base", "mix(mix((0.055,0.115,0.205),(0.31,0.34,0.45),pow(ht,0.75)),"
             "(0.96,0.64,0.44),pow(ht,3.2))"),
    ("sd", "sqrt(pow(p.1-1217.,2)+pow(p.2-332.,2))"),
    ("th", "atan2(p.2-332.,p.1-1217.)"),
    ("halo", "exp(-greatest(sd-72.,0.)/52.)*.38"),
    ("corona", "exp(-greatest(sd-73.,0.)/(10.+6.*pow(sin(th*3.+0.4),2)))"),
    ("ring", "exp(-pow((sd-73.5)/1.8,2))"),
    ("glow", "tuplePlus(base,tupleMultiplyByNumber((1.,0.69,0.34),halo+corona*.60+ring*.47))"),
    ("moon", "mix(glow,(0.031,0.066,0.112),clamp((72.2-sd)/aa+.5,0.,1.))"),
    ("diamond", "exp(-(pow(p.1-1268.,2)+pow(p.2-280.,2))/12.)*.70"),
    ("star", "if(p.2<250. AND cityHash64(toInt64(floor(p.1/23.)),toInt64(floor(p.2/23.)))%37=0,"
             "exp(-(pow(modulo(p.1,23.)-11.,2)+pow(modulo(p.2,23.)-11.,2))/1.0)*(1.-ht)*.6,0.)"),
], "tuplePlus(moon,tupleMultiplyByNumber((1.,0.91,0.72),diamond+star))")

WATER = let([
    ("dep", "clamp((p.2-473.)/527.,0.,1.)"),
    ("wc", "mix((0.49,0.56,0.59),(0.105,0.29,0.34),pow(dep,.40))"),
    ("wav", "pow(.5+.5*sin(p.2*.54+sin(p.1*.018)*1.7+sin(p.1*.047+p.2*.033)),18.)"),
    ("fine", "sin(p.2*1.30+sin(p.1*.037)*2.3)*.012*dep"),
    ("refx", "1217.+sin(p.2*.087)*13.+sin(p.2*.231)*7."),
    ("path", "exp(-pow((p.1-refx)/(19.+dep*120.),2))"),
    ("gold", "path*(.075+wav*.43)*(1.-dep*.25)"),
    ("blue", "wav*(.028+.060*dep)+fine"),
    ("wr", "tuplePlus(wc,tuplePlus(tupleMultiplyByNumber((1.,.59,.25),gold),"
           "tupleMultiplyByNumber((.58,.76,.75),blue)))"),
], "wr")

SAMPLE = let([
    ("p", "(u,v)"),
    ("base", "if(v<473.,sky(p),water(p))"),
    ("bg", "paint(p,landscape)"),
    ("back", "over(base,bg)"),
    ("rp", "(u+sin(v*.33)*2.8+sin(v*.081)*6.,1686.-v)"),
    ("rf", f"if(v>849. AND {visible(bird, 'rp')},paint(rp,subject),(0.,0.,0.,0.))"),
    ("ra", "clamp((v-849.)/26.,0.,1.)*.29*exp(-(v-849.)/255.)"
           "*(.65+.35*pow(.5+.5*sin(v*.56+sin(u*.024)*1.5),3.))"),
    ("refl", "mix(back,(rf.1*.68,rf.2*.87,rf.3*.93),rf.4*ra)"),
    ("fg", f"if({visible(bird)},paint(p,subject),(0.,0.,0.,0.))"),
    ("hero", "over(refl,fg)"),
    ("plants", f"if({visible(front)},paint(p,foreground),(0.,0.,0.,0.))"),
    ("allcol", "over(hero,plants)"),
    ("grain", "((cityHash64(pixel,sample,73)%65536)/65535.-.5)*.014"),
    ("vignette", "1.-.12*clamp(pow((u-800.)/1030.,2)+pow((v-500.)/800.,2),0.,1.)"),
], "tuplePlus(tupleMultiplyByNumber(allcol,vignette),(grain,grain,grain))")


QUERY = f"""/* Generated by generators/gen_pelican.py. No tables, UDFs or external images.
   Every sampled pixel is evaluated in this single SELECT and encoded by FORMAT PNG.
   Artboard: 1600 x 1000. Suggested render: 2400 x 1500, SAMPLES=4.
   Shapes: {len(land.shapes)} landscape, {len(bird.shapes)} subject, {len(front.shapes)} foreground. */
WITH
    getSetting('output_format_image_width')::UInt64 AS W,
    getSetting('output_format_image_height')::UInt64 AS H,
    {{SAMPLES:UInt32}} AS spp,
    toUInt64(ceil(sqrt(spp))) AS side,
    1000. / H AS aa,
    ((a,b,t) -> tuplePlus(a,tupleMultiplyByNumber(tupleMinus(b,a),t))) AS mix,
    ((c,a) -> (a.1+c.1*(1.-a.4),a.2+c.2*(1.-a.4),a.3+c.3*(1.-a.4))) AS over,
    ((p,ax,ay,bx,by) -> {SEGMENT}) AS seg,
    ((p,s) -> {DISTANCE}) AS sdf,
    ((p,shapes) -> arrayFold((a,s) ->
        if(p.1>s.12.1 AND p.1<s.12.3 AND p.2>s.12.2 AND p.2<s.12.4,
           {FOLD},a),shapes,(0.,0.,0.,0.))) AS paint,
    {sql(land.shapes)} AS landscape,
    {sql(bird.shapes)} AS subject,
    {sql(front.shapes)} AS foreground,
    (p -> {SKY}) AS sky,
    (p -> {WATER}) AS water
SELECT
    clamp(avg(col.1),0.,1.) AS r,
    clamp(avg(col.2),0.,1.) AS g,
    clamp(avg(col.3),0.,1.) AS b,
    pixel % W AS x,
    intDiv(pixel,W) AS y
FROM (
    SELECT pixel,
        {SAMPLE} AS col
    FROM (
        SELECT
            intDiv(number,spp) AS pixel,
            number % spp AS sample,
            /* Regular stratification for square sample counts; unbiased,
               deterministic jitter for every other positive sample count. */
            if(side*side=spp,(sample%side+.5)/side,
               (cityHash64(pixel,sample,11)%1048576)/1048576.) AS jx,
            if(side*side=spp,(intDiv(sample,side)+.5)/side,
               (cityHash64(pixel,sample,19)%1048576)/1048576.) AS jy,
            ((pixel % W)+jx-W*.5)*aa+800. AS u,
            (intDiv(pixel,W)+jy)*aa AS v
        FROM numbers_mt(W*H*spp)
    )
)
GROUP BY pixel
SETTINGS max_block_size=256, max_threads=8,
         short_circuit_function_evaluation='enable', optimize_and_compare_chain=0
FORMAT PNG
"""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        sys.exit("This generator takes no arguments; set dimensions and SAMPLES in ClickHouse. Use --help.")
    sys.stdout.write(QUERY)
