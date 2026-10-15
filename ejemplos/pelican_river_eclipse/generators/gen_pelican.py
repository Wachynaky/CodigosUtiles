#!/usr/bin/env python3
"""Emit one standalone ClickHouse SELECT that paints a pelican cycling on a river.

Python only builds vector geometry and a spatial index. All coverage, shading,
water, eclipse light, reflections, compositing and antialiasing run in SQL.
No images, fonts, UDFs, services or Python packages are used by the renderer.

    python3 generators/gen_pelican.py > queries/pelican_river_eclipse.sql
    clickhouse local --max_query_size 10000000 --output_format_image_width 2400 \
      --output_format_image_height 1500 --param_SAMPLES 4 \
      --queries-file queries/pelican_river_eclipse.sql > images/pelican_river_eclipse.png
"""

import argparse
import math
import random
import sys


WIDTH, HEIGHT = 1600, 1000
TILE = 40
RNG = random.Random(20261015)
SHAPES = []


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def add(kind, bounds, geometry, thickness, opacity, top, bottom, points=()):
    SHAPES.append((kind, tuple(bounds), tuple(geometry), thickness, opacity,
                   rgb(top), rgb(bottom or top), tuple(points) or ((0., 0.),)))


def ellipse(x, y, rx, ry, top, bottom=None, angle=0, opacity=1, glow=False):
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    bx = math.hypot(rx * c, ry * s)
    by = math.hypot(rx * s, ry * c)
    # Glows are truncated at three radii, below 0.02% of peak intensity.
    extent = 3 if glow else 1
    add(4 if glow else 0, (x - bx * extent - 1, y - by * extent - 1,
                         x + bx * extent + 1, y + by * extent + 1),
        (x, y, rx, ry, c, s), 0, opacity, top, bottom)


def ring(x, y, rx, ry, width, color, bottom=None, opacity=1):
    add(3, (x - rx - width - 1, y - ry - width - 1,
            x + rx + width + 1, y + ry + width + 1),
        (x, y, rx, ry, 1., 0.), width, opacity, color, bottom)


def line(x1, y1, x2, y2, width, color, bottom=None, opacity=1):
    pad = width / 2 + 1
    add(1, (min(x1, x2) - pad, min(y1, y2) - pad,
            max(x1, x2) + pad, max(y1, y2) + pad),
        (x1, y1, x2, y2, 1., 0.), width, opacity, color, bottom)


def polygon(points, top, bottom=None, opacity=1):
    xs, ys = zip(*points)
    add(2, (min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1),
        (0., 0., 1., 1., 1., 0.), 0, opacity, top, bottom, points)


class Path:
    """Small authoring helper: flatten cubic curves into vector vertices."""
    def __init__(self, x, y):
        self.points = [(x, y)]

    def L(self, x, y):
        self.points.append((x, y))
        return self

    def C(self, ax, ay, bx, by, x, y, steps=16):
        x0, y0 = self.points[-1]
        for i in range(1, steps + 1):
            t = i / steps
            u = 1 - t
            self.points.append((u**3*x0 + 3*u*u*t*ax + 3*u*t*t*bx + t**3*x,
                                u**3*y0 + 3*u*u*t*ay + 3*u*t*t*by + t**3*y))
        return self

    def fill(self, top, bottom=None, opacity=1):
        polygon(self.points, top, bottom, opacity)
        return self

    def stroke(self, color, width=1, opacity=1):
        for a, b in zip(self.points, self.points[1:]):
            line(*a, *b, width, color, opacity=opacity)
        return self


def feather(x, y, length, width, angle, top, bottom, shaft=True):
    """Tapered, curved individual feather; coordinates are authored, not pixels."""
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    local = (Path(0, -width * .4)
             .C(length*.35, -width*.65, length*.85, -width*.30, length, 0, 8)
             .C(length*.75, width*.48, length*.25, width*.58, 0, width*.4, 8))
    polygon([(x + u*c - v*s, y + u*s + v*c) for u, v in local.points], top, bottom)
    if shaft:
        line(x + length*.13*c, y + length*.13*s,
             x + length*.90*c, y + length*.90*s, .65, top, opacity=.55)


def pine(x, ground, height, color, opacity=1):
    line(x, ground, x, ground-height, max(.8, height*.022), color, opacity=opacity)
    pts = [(x, ground-height)]
    for i in range(1, 8):
        yy = ground-height + height*i/8
        ww = height*.25*(i/8)
        pts.extend([(x-ww*.38, yy-height*.05), (x-ww, yy+height*.06)])
    pts.append((x, ground))
    for i in reversed(range(1, 8)):
        yy = ground-height + height*i/8
        ww = height*.25*(i/8)
        pts.extend([(x+ww, yy+height*.06), (x+ww*.38, yy-height*.05)])
    polygon(pts, color, opacity=opacity)


def background_geometry():
    # Fine cirrus follows the long, quiet lines of the valley.
    for x, y, rx, ry, alpha in [(235, 201, 255, 8, .14), (383, 242, 192, 5, .16),
                                (920, 142, 290, 5, .10), (1445, 190, 175, 7, .12),
                                (1010, 416, 310, 5, .18)]:
        ellipse(x, y, rx, ry, "c9a99a", opacity=alpha, glow=True)
    for i in range(74):
        x, y = RNG.uniform(50, 1550), RNG.uniform(48, 286)
        r = RNG.choice([.45, .55, .7, 1.0])
        ellipse(x, y, r, r, "e7dfcb", opacity=RNG.uniform(.23, .68))
    # Distant low-contrast mountain silhouettes, with individually lit facets.
    polygon([(0,410),(65,386),(122,398),(206,334),(279,392),(350,370),
             (427,410),(516,355),(572,385),(635,362),(744,422),(830,398),
             (900,430),(990,389),(1049,410),(1128,365),(1195,400),(1282,352),
             (1340,374),(1390,350),(1495,405),(1557,382),(1600,398),(1600,515),(0,515)],
            "73777f", "b99b83")
    polygon([(1282,352),(1242,397),(1295,382),(1340,414),(1390,350),(1364,405),(1465,444)],
            "d1ae8d", "8d8e88", .72)
    polygon([(206,334),(174,397),(204,379),(244,407),(279,392)], "aca498", "81868a", .63)
    polygon([(0,437),(110,409),(174,442),(270,402),(346,426),(424,389),(492,425),
             (570,430),(659,468),(740,444),(855,475),(973,437),(1040,457),
             (1140,419),(1205,447),(1290,405),(1365,430),(1470,389),(1600,441),
             (1600,534),(0,534)], "41616b", "869185")
    # Broken ridgelines and scree faces keep the silhouettes from reading as cones.
    for points in [
        [(424,389),(407,423),(384,440),(410,435),(398,465),(449,468),(434,428)],
        [(270,402),(250,428),(256,447),(230,464),(292,473),(279,433)],
        [(1470,389),(1441,424),(1448,444),(1405,464),(1493,473),(1473,435)],
        [(1290,405),(1257,443),(1273,439),(1253,474),(1320,478),(1302,444)],
    ]:
        polygon(points,"7c8d87","6b847d",.43)
    polygon([(0,472),(85,446),(165,463),(220,439),(316,474),(407,453),
             (500,483),(607,491),(720,517),(822,522),(955,507),(1075,488),
             (1190,477),(1310,451),(1390,471),(1490,439),(1600,467),(1600,548),(0,548)],
            "31555d", "526f6b")
    for i in range(125):
        x = RNG.uniform(-10,1610)
        g = 497 + 17*math.sin(x*.006)
        pine(x, g, RNG.uniform(7,34), "36585c", .75)
    # Two banks open out toward the viewer; the river remains the main stage.
    Path(-10,507).C(160,489,273,514,435,550).C(328,550,242,584,138,604).C(64,617,28,657,-10,675).fill("284e51","153f45")
    Path(1610,503).C(1480,496,1360,526,1248,550).C(1365,551,1493,620,1610,660).fill("35574e","164148")
    Path(0,532).C(161,521,257,539,372,548).stroke("96a891",2,.65)
    Path(1600,526).C(1480,519,1382,536,1293,549).stroke("c5b68b",2,.55)
    for i in range(30):
        x = RNG.uniform(-10,260)
        pine(x, 526+((260-x)/260)*43, RNG.uniform(24,83), "173e43")
    for i in range(27):
        x = RNG.uniform(1410,1620)
        pine(x, 538+((x-1410)/210)*61, RNG.uniform(25,74), "21443f")
    ellipse(775,506,437,4,"d4c6a0",opacity=.13,glow=True)
    ellipse(1198,491,211,3,"d9c6a0",opacity=.11,glow=True)


def water_geometry():
    # Small perspective-scaled wave crests, not a regular screen-space grid.
    for i in range(320):
        y = RNG.uniform(527,1005)
        x = RNG.uniform(-25,1620)
        t = (y-510)/490
        length = RNG.uniform(3,18)*(0.25+2*t)
        tint = RNG.choice(["a8c6b7","74a9aa","477e83","214f5d"])
        line(x,y,x+length,y+RNG.uniform(-.5,.5), RNG.uniform(.45,1.25), tint,
             opacity=RNG.uniform(.17,.48))
    # Broken warm reflections from the eclipse close to the right bank.
    for i in range(105):
        y = RNG.uniform(524,986)
        d = (y-510)/490
        x = 1220+RNG.gauss(0,21+75*d)+13*math.sin(y*.037)
        length = RNG.uniform(2,16)*(1+2*d)
        line(x,y,x+length,y,RNG.uniform(.5,1.65),RNG.choice(["e0ac73","f4c88b","ac936b"]),
             opacity=RNG.uniform(.17,.63))
    # Grounding shadows, visible through the clear water below both tyres.
    ellipse(790,823,335,29,"12383f",opacity=.44,glow=True)
    for cx in (600,1025):
        ellipse(cx,821,97,12,"102e37",opacity=.50,glow=True)
        for rx,ry,yy in [(91,13,822),(117,19,825),(153,26,830)]:
            ring(cx,yy,rx,ry,.9,"91c5b8",opacity=.25)
    # Wake behind the moving bicycle.
    Path(196,793).C(287,792,390,804,504,813).stroke("b5d5bd",1.8,.51)
    Path(272,806).C(364,810,429,826,499,827).stroke("548e92",3,.75)
    Path(217,831).C(338,821,430,837,508,838).stroke("a2c8b9",1,.41)


def bicycle():
    # Far pedal and the far leg are behind the entire frame.
    Path(742,557).C(755,583,778,604,801,612).L(836,674).stroke("9b6541",13)
    Path(741,556).C(757,581,781,599,806,609).L(840,674).stroke("dfaa64",6)
    Path(834,668).C(849,669,869,678,877,686).L(844,688).L(829,680).fill("e4a352","9a5e36")
    line(813,687,858,682,8,"1a3439")
    line(813,684,855,680,2,"beb9a0")
    # Tyres, sidewalls, rims, reflected highlights and individually crossed spokes.
    for cx in (600,1025):
        ring(cx,696,130,130,9.4,"102a31","0b2028")
        ring(cx,696,125.4,125.4,2.6,"bda77b","6d786b")
        ring(cx,696,120.5,120.5,2.2,"b8d8d0","517f86")
        ring(cx-1,695,134.6,134.6,.65,"90ada0",opacity=.55)
        for i in range(32):
            a = i*math.tau/32+.12
            b = a+(.25 if i%2 else -.25)
            line(cx+9*math.cos(b),696+9*math.sin(b),cx+119*math.cos(a),696+119*math.sin(a),
                 .87,"bdd4c8",opacity=.70)
        for i in range(54):
            a = i*math.tau/54
            line(cx+128*math.cos(a),696+128*math.sin(a),cx+132*math.cos(a+.007),696+132*math.sin(a+.007),
                 .8,"355159",opacity=.62)
        ellipse(cx,696,12,12,"d5cba3","648184")
        ellipse(cx,696,5,5,"1a3d45")
        ellipse(cx-2,693,2,2,"f7e3b6")
        # Brass spoke reflector and valve stem.
        ellipse(cx+77,642,4,10,"fac278","b7783f",angle=44)
        line(cx-55,799,cx-51,792,2,"d7c5a0")
    # Rear rack, mudguards and a traditional curved front fork.
    Path(486,623).C(527,574,598,547,662,585).stroke("163d40",7)
    Path(486,620).C(534,574,599,551,660,583).stroke("c9995f",2)
    Path(929,590).C(987,548,1066,563,1114,624).stroke("183e41",7)
    Path(930,588).C(987,548,1066,563,1114,622).stroke("c6b184",2)
    line(519,568,661,568,6,"bca375")
    line(524,571,597,694,3,"526e68")
    line(652,571,600,694,3,"526e68")
    # Chain: two clean runs, a rear sprocket, chainring, teeth and links.
    ring(600,696,23,23,3.1,"a4aa91","4a686c")
    ring(790,702,37,37,4.2,"e5c58e","688b89")
    ring(790,702,29,29,2,"274e54")
    line(599,672,791,664,3,"162f34")
    line(597,720,788,740,3,"162f34")
    for i in range(40):
        t=i/39
        ellipse(599+192*t,672-8*t,1.6,.9,"c7b991")
        ellipse(597+191*t,720+20*t,1.6,.9,"a1b19e")
    for i in range(30):
        a=i*math.tau/30
        line(790+35*math.cos(a),702+35*math.sin(a),790+39*math.cos(a),702+39*math.sin(a),1.8,"d1bb8b")
    for i in range(5):
        a=i*math.tau/5
        line(790+9*math.cos(a),702+9*math.sin(a),790+27*math.cos(a+.22),702+27*math.sin(a+.22),4,"829a8e")
    # Teal enamel diamond frame, bronze lining, small silver fasteners.
    bars=[(600,696,718,557),(600,696,790,702),(718,557,790,702),
          (718,557,958,565),(958,565,790,702)]
    for x1,y1,x2,y2 in bars:
        line(x1,y1,x2,y2,12,"133d40")
        line(x1,y1-2,x2,y2-2,7,"3e8784","286569")
        line(x1,y1-4,x2,y2-4,1.5,"c3c59b",opacity=.93)
    Path(952,550).C(973,595,982,663,1025,696).stroke("173e42",13)
    Path(952,548).C(971,594,982,661,1025,694).stroke("548f88",6)
    Path(951,546).C(971,594,982,658,1025,692).stroke("d9c397",1.6)
    line(718,555,706,525,9,"c4c1a0")
    Path(675,531).C(693,519,719,519,741,525).C(750,528,739,538,725,538).L(680,539).fill("483f31","182d2d")
    Path(680,531).C(699,525,721,525,737,529).stroke("c59962",1.7)
    # Stem, drop handlebar, leather grips, brake lever and looping cable.
    line(953,550,944,516,8,"c0c5aa")
    Path(945,518).C(953,509,982,508,994,517).C(1004,526,996,538,982,540).stroke("b9c9b6",6)
    Path(974,511).C(995,512,1007,525,990,537).stroke("3d3c31",8)
    for i in range(7):
        line(981+i*1.5,514+i*2,986+i*1.5,514+i*2,1,"a7865c")
    line(968,516,982,547,3,"b1bca7")
    Path(976,538).C(1016,565,976,600,999,633).stroke("193e43",1.7)
    ellipse(958,507,8,5,"f2d7a0","85754f")
    ellipse(956,505,3,1.5,"fff1c4")
    # Headlamp and its mounting bracket.
    line(983,567,1007,556,3,"a4b09c")
    ellipse(1006,552,12,10,"244b4c","0d2e36",angle=-12)
    ellipse(1015,550,4,7,"ffe1a0","b9975c",angle=-12)
    ellipse(1016,549,14,11,"e9c283",opacity=.07,glow=True)
    # Crank in the near plane, with a clearly visible pedal.
    line(790,702,751,752,8,"203e40")
    line(790,701,750,750,4,"bac1a6")
    ellipse(790,702,8,8,"d6c6a0","5e7f7b")
    line(725,753,774,751,8,"193c41")
    line(729,749,772,747,2,"a0b8a3")
    for x in range(731,772,7):
        line(x,750,x,754,1.2,"d2bc91")
    # Two miniature frame details: bottle and brass head badge.
    line(815,639,836,611,16,"174749")
    line(814,635,831,614,11,"ccba8c","728e80")
    line(830,613,835,607,7,"294c4d")
    ellipse(959,567,3,7,"deb577",angle=-22)


def pelican():
    # Feet grip the pedals. The articulated shins stay visible below the plumage.
    Path(771,554).C(772,581,748,599,739,622).C(728,651,739,698,747,735).stroke("9c693e",14)
    Path(770,553).C(770,580,746,602,738,625).C(731,652,743,701,751,734).stroke("e2a75d",7)
    ellipse(739,622,8,9,"d4a164","b77e48")
    Path(746,730).C(757,731,771,735,780,744).L(771,750).L(757,745).L(747,751).L(740,745).L(726,748).C(724,741,734,734,746,730).fill("f0b56b","aa683d")
    for x in (735,749,763):
        line(746,735,x,745,1,"ac703e")
    # Layered black flight feathers at the tail.
    for i in range(9):
        feather(642-i*3,509+i*4,110+i*2,22,183+i*2.5,"7a8a85","223e46")
    # Main silhouette includes the upright, S-curved neck.
    (Path(563,489).C(591,456,637,427,699,431)
     .C(741,430,770,449,797,441).C(826,425,840,396,846,360)
     .C(848,328,855,300,879,291).C(902,280,933,291,944,311)
     .C(957,330,952,356,940,378).C(933,397,927,426,910,448)
     .C(889,477,882,506,854,538).C(826,573,781,589,731,585)
     .C(660,582,615,547,563,489).fill("fff1d2","a6b7b1"))
    # Warm back light on the crown and the outside edge of the neck.
    (Path(870,306).C(896,282,929,297,938,318).C(944,338,936,355,925,378)
     .C(918,402,916,420,899,441).C(884,460,874,484,860,505)
     .L(854,486).C(862,455,881,431,891,403).C(902,367,896,336,870,306)
     .fill("fff7dc","eee2bb",.91))
    # Blue-grey modelling under the throat and along the belly.
    (Path(859,358).C(856,399,834,433,801,453).C(850,440,876,410,877,370)
     .C(875,346,864,333,861,325).fill("c5d3ce","91abae",.72))
    Path(597,510).C(646,570,733,597,808,568).C(758,586,666,549,620,510).fill("c4ccc2","7f9b9e",.70)
    # Scapular and covert feathers follow the curved surface of the body.
    for row in range(4):
        for j in range(10-row):
            x=614+j*17+row*12
            y=470+row*19+5*math.sin(j*.48)
            feather(x,y,48+row*6,13+row*2,35+row*3+j*1.8,
                    ["f9edd2","e8e4d0","d9decf","c9d3c9"][row],
                    ["d4d9cc","bacac3","a1b8b6","8da7a9"][row], shaft=True)
    # Left shoulder and folded flight feathers, dark tips beneath ivory covers.
    for i in range(7):
        feather(691+i*9,486+i*4,116-i*4,25,140-i*4,
                "9caaa2","294952")
    Path(664,471).C(700,449,748,456,780,480).C(754,499,713,528,651,546).C(673,522,678,491,664,471).fill("f4ead0","bacac0")
    for i in range(9):
        feather(699+i*6,478+i*2,69-i*2,14,135-i*2,"eae7d0","a6bbb6")
    # Fine, overlapping shoulder barbs catch the low amber rim light.
    for i in range(37):
        t=i/36
        x=603+151*t
        y=457+9*math.sin(t*math.pi*1.6)
        Path(x,y).C(x+4,y-2,x+9,y+3,x+12,y+8,5).stroke("fff2d4",.75,.72)
    for i in range(16):
        t=i/15
        x=641+94*t
        y=537+26*math.sin(t*math.pi*.8)
        Path(x,y).C(x+7,y+5,x+11,y+5,x+17,y+2,5).stroke("e3e3cc",.7,.65)
    # The near wing reaches the handlebar; long narrow fingers close over the grip.
    Path(752,459).C(783,447,818,460,845,481).C(870,502,898,510,928,516).L(955,523).C(963,530,960,537,948,538).C(901,537,857,529,822,511).C(798,500,766,501,748,486).fill("fff0d0","afc3ba")
    for i in range(6):
        feather(785+i*12,478+i*4,92-i*4,15-i*.7,24-i*1.9,"f8ebce","b7c7bb")
    for i in range(4):
        Path(928+i*6,519+i).C(942+i*4,522,951+i*3,526,948+i*3,532+i).stroke("f5e6c7",3.8)
    # Small neck feathers, with a directional grain instead of smooth plastic.
    for i in range(23):
        t=i/22
        x=857+22*math.sin(t*2.7)
        y=326+t*116
        Path(x,y).C(x-4,y+7,x-2,y+12,x-5,y+17,5).stroke("c6cfc0",.85,.65)
    # Rounded head, golden crest, soft cheek and tiny individual crown plumes.
    ellipse(901,321,42,32,"fff3d2","dedbc1",angle=9)
    for i in range(12):
        x=865+i*4.5
        Path(x,309-8*math.sin(i/11*math.pi)).C(x-8,299,x-5,289,x+3,286+2*math.sin(i),8).stroke("f8dfaa",1.7)
    ellipse(918,351,27,20,"fff4da","d6d9c0",angle=-15)
    # Bill: very long upper mandible, rich pouch, fine seam and a hooked tip.
    Path(937,345).C(1014,345,1118,363,1210,381).C(1227,385,1229,394,1216,398).L(947,375).fill("f4c077","d58a47")
    Path(945,373).L(1219,391).C(1188,402,1158,410,1122,417).C(1057,447,996,430,954,392).C(945,386,941,380,945,373).fill("edb071","ba713d")
    Path(956,383).C(1002,417,1056,432,1112,413).C(1072,418,1025,408,986,388).fill("f5cd93","d99a60",.74)
    for i in range(15):
        t=i/14
        x=975+198*t
        y=389+15*math.sin(t*math.pi)
        Path(x,y).C(x+7,y+8,x+14,y+12,x+20,y+11,6).stroke("b37d4b",.65,.43)
    Path(946,369).C(1029,372,1118,381,1219,391).stroke("8c663f",1.7)
    Path(953,350).C(1022,352,1121,370,1201,383).stroke("ffe5ac",2.2,.9)
    Path(1206,381).C(1228,383,1233,394,1214,402).L(1217,391).fill("715c3c","313e36")
    ellipse(981,361,7,1.9,"866e43",angle=7)
    # Bare eye patch, fine dark lid, iris, pupil and two tiny catchlights.
    ellipse(925,332,13,11,"dfb876","b58e54",angle=-15)
    ellipse(926,331,7.4,7.9,"283e3b","192d31")
    ellipse(927,331,5.3,5.7,"e6b95c","a57837")
    ellipse(928,331,3,4.3,"152a2e")
    ellipse(929.4,328.7,1.45,1.45,"fff7dc")
    ellipse(925.7,333,0.65,0.65,"dbd9b3")
    Path(914,325).C(922,319,930,320,935,325,8).stroke("fff1ce",2.1)
    # Tiny throat crease and delicately broken feather edges.
    Path(936,374).C(930,384,930,396,925,403).stroke("b6bca7",1.1)
    for i in range(16):
        x=654+i*10
        y=570+13*math.sin((x-654)/160*math.pi)
        line(x,y-3,x+4,y+2,.85,"e4e2c8",opacity=.8)


def foreground():
    # Contact foam overlaps the tyres, making the wheels enter the river.
    for cx in (600,1025):
        Path(cx-103,816).C(cx-54,808,cx-18,826,cx+43,815).C(cx+74,811,cx+93,814,cx+106,816).stroke("d2e4c8",2.4,.8)
        Path(cx-77,828).C(cx-28,836,cx+19,821,cx+88,827).stroke("8bbcb2",1.7,.8)
        for i in range(35):
            x=cx+RNG.uniform(-105,112)
            y=815+RNG.gauss(0,5)
            ellipse(x,y,RNG.uniform(1.1,3.3),RNG.uniform(.45,1),"d7e7c9",opacity=RNG.uniform(.35,.83))
        # Forward flung droplets and graceful, small splashes.
        for i in range(6):
            x=cx+74+i*7
            yy=810-i*5
            Path(cx+65,817).C(x,809,x+8,yy-9,x+11,yy).stroke("badcc7",.9,.65)
            ellipse(x+11,yy-4,1.2,2.3,"e9edd0",angle=20,opacity=.8)
    # Two banks of dark, botanically shaped reeds frame the open foreground.
    Path(-10,954).C(62,911,123,928,208,1009).L(-10,1010).fill("123b40","102f38")
    Path(1400,1010).C(1500,935,1554,934,1610,942).L(1610,1010).fill("204541","103238")
    for side in (0,1):
        for i in range(24):
            x=RNG.uniform(-15,165) if side==0 else RNG.uniform(1480,1620)
            base=RNG.uniform(965,1045)
            h=RNG.uniform(65,225)
            lean=RNG.uniform(-42,35)
            color=RNG.choice(["143e41","28554d","436f59"])
            Path(x,base).C(x+lean*.2,base-h*.4,x+lean*.7,base-h*.85,x+lean,base-h).stroke(color,RNG.uniform(1.1,2.7))
            yy=base-h*.53
            Path(x+lean*.35,yy).C(x-37,yy-50,x-42,yy-70,x-47,yy-77).C(x-25,yy-68,x-5,yy-36,x+lean*.35,yy).fill(color)
            if i%3==0:
                line(x+lean,base-h+9,x+lean*1.02,base-h-17,6.5,"7c6848","3b4c3c")
                line(x+lean,base-h-19,x+lean,base-h-30,.8,"a5956e")
    # Stones with a submerged edge and restrained amber highlights.
    for x,y,rx,ry in [(154,971,53,20),(245,1000,48,19),(1427,989,43,15)]:
        ellipse(x,y+9,rx*1.3,ry*.4,"102e37",opacity=.6)
        ellipse(x,y,rx,ry,"6e8270","274c4c",angle=-8)
        Path(x-rx*.65,y-ry*.5).C(x-rx*.2,y-ry,x+rx*.4,y-ry,x+rx*.7,y-ry*.5).stroke("adb08a",1.2,.55)
    # Small flying silhouettes lead the eye toward the eclipse.
    for x,y,s in [(1057,227,7),(1092,244,5),(1015,251,4),(1384,329,6)]:
        Path(x-s,y+2).C(x-s*.5,y-3,x-2,y-3,x,y).C(x+2,y-4,x+s*.6,y-4,x+s,y-1,8).stroke("2e464f",1.4)


def literal(value):
    if isinstance(value, (tuple,list)):
        left,right = ("[","]") if isinstance(value,list) else ("(",")")
        return left+",".join(literal(v) for v in value)+right
    if isinstance(value,int):
        return str(value)
    return f"{value:.5f}" if abs(value)>0.000005 else "0.00000"


def shape_literal(shape):
    # All shapes use the same nested Tuple type, including their point arrays.
    return "("+",".join(literal(v) if i!=7 else literal(list(v))
                         for i,v in enumerate(shape))+")"


def lets(bindings, body):
    # Bind by value, as in the repository's ray-tracer generators.
    for name, expression in reversed(bindings):
        body=f"arrayMap({name} -> {body}, [{expression}])[1]"
    return body


def generate():
    background_geometry()
    water_geometry()
    hero_first=len(SHAPES)+1
    bicycle()
    pelican()
    hero_last=len(SHAPES)
    foreground()
    cols,rows=math.ceil(WIDTH/TILE),math.ceil(HEIGHT/TILE)
    tiles=[]
    for row in range(rows):
        for col in range(cols):
            x0,y0=col*TILE,row*TILE
            tiles.append([i+1 for i,s in enumerate(SHAPES)
                          if s[1][0]<=x0+TILE and s[1][2]>=x0
                          and s[1][1]<=y0+TILE and s[1][3]>=y0])

    coverage=lets([
        ("u","(p.1-s.3.1)*s.3.5 + (p.2-s.3.2)*s.3.6"),
        ("v","-(p.1-s.3.1)*s.3.6 + (p.2-s.3.2)*s.3.5"),
        ("rad","sqrt(pow(u/s.3.3,2)+pow(v/s.3.4,2))")],
        "multiIf(s.1=0, clamp(0.5-(rad-1.0)*least(s.3.3,s.3.4)/aa,0.,1.), "
        "s.1=3, clamp(0.5-(abs(rad-1.0)*least(s.3.3,s.3.4)-s.4)/aa,0.,1.), "
        "exp(-rad*rad*2.0))")
    segment=lets([
        ("dx","s.3.3-s.3.1"),("dy","s.3.4-s.3.2"),
        ("t","clamp(((p.1-s.3.1)*dx+(p.2-s.3.2)*dy)/greatest(dx*dx+dy*dy,0.00001),0.,1.)")],
        "clamp(0.5-(hypot(p.1-s.3.1-t*dx,p.2-s.3.2-t*dy)-s.4*0.5)/aa,0.,1.)")
    paint=lets([
        ("alpha","s.5*multiIf(s.1=2,toFloat64(pointInPolygon(p,s.8)),s.1=1,segment(p,s),oval(p,s))"),
        ("grad","clamp((p.2-s.2.2)/greatest(s.2.4-s.2.2,0.001),0.,1.)"),
        ("ink","mix(s.6,s.7,grad)")],"mix(acc,ink,alpha)")
    sky=lets([
        ("dist","hypot(p.1-1220.,p.2-301.)"),
        ("theta","atan2(p.2-301.,p.1-1220.)"),
        ("base","mix((0.055,0.13,0.20),(0.81,0.57,0.36),pow(clamp(p.2/530.,0.,1.),1.9))"),
        ("halo","exp(-pow(dist/190.,2))*0.26"),
        ("corona","(exp(-greatest(dist-67.,0.)/(13.+10.*pow(cos(theta*2.+.7),8.)))*(0.72+0.11*cos(theta*5.)+0.09*sin(theta*11.))+0.35*exp(-pow((dist-67.2)/1.4,2)))*if(dist>65.,1.,0.)"),
        ("lit","mix(mix(base,(0.94,0.70,0.41),halo),(1.,0.91,0.67),clamp(corona,0.,.93))"),
        ("disc","clamp((66.5-dist)/aa+0.5,0.,1.)"),
        ("eclipse","mix(lit,(0.055,0.09,0.135),disc)"),
        ("bead","clamp(exp(-pow(hypot(p.1-1273.,p.2-262.)/4.0,2))+.3*exp(-abs(p.1-1273.)/11.-abs(p.2-262.)/1.1)+.22*exp(-abs(p.1-1273.)/1.1-abs(p.2-262.)/9.),0.,1.)")],
        "mix(eclipse,(1.,.97,.83),bead)")
    water=lets([
        ("depth","clamp((p.2-508.)/492.,0.,1.)"),
        ("rip","sin(p.2*(0.6-depth*.39)+sin(p.1*.012+p.2*.021)*2.5)"),
        ("fine","sin(p.2*1.16+p.1*.036+3.*sin(p.1*.004-p.2*.012))"),
        ("base","mix((.28,.43,.43),(.045,.23,.29),pow(depth,.55))"),
        ("band","exp(-pow((p.1-1220.-16.*sin(p.2*.043))/(25.+depth*119.),2))"),
        ("glint","band*(.13+.35*pow(greatest(rip,0.),9.)+.13*pow(greatest(fine,0.),16.))"),
        ("wat","tuplePlus(base,((rip*.018+fine*.009),(rip*.029+fine*.014),(rip*.027+fine*.014)))")],
        "mix(wat,(.92,.66,.35),clamp(glint,0.,.8))")

    shapes_sql=",\n        ".join(shape_literal(s) for s in SHAPES)
    print(f"""-- Generated by generators/gen_pelican.py; edit the generator, then regenerate.
-- A single SELECT. Python supplies only vector geometry and tile membership.
-- Every pixel, water wave, eclipse light, reflection and blend is computed here.
-- Geometry: {len(SHAPES)} primitives. Canvas: {WIDTH} x {HEIGHT}; output size is runtime.
-- Primitive: (kind, bounds, geometry, thickness, opacity, topRGB, bottomRGB, vertices).
-- Kinds: 0 ellipse, 1 capsule/line, 2 polygon, 3 elliptical ring, 4 soft glow.
WITH
    getSetting('output_format_image_width')::UInt64 AS W,
    getSetting('output_format_image_height')::UInt64 AS H,
    {{SAMPLES:UInt32}} AS spp,
    {WIDTH}.0/W AS aa,
    {cols} AS tileCols,
    -- Hammersley samples: stratified X, base-two radical inverse Y.
    -- Calculated once as constant geometry, for any positive sample count.
    arrayMap(si -> ((si+0.5)/spp,
        modulo(arraySum(arrayMap(bi -> bitAnd(bitShiftRight(toUInt64(si),bi),1)
            *pow(0.5,bi+1),range(32)))+0.5/spp,1.)),range(spp)) AS samplePattern,
    [\n        {shapes_sql}\n    ] AS shapes,
    {literal(tiles)} AS tiles,
    ((a,b,t) -> tuplePlus(a,tupleMultiplyByNumber(tupleMinus(b,a),t))) AS mix,
    ((p,s) -> {coverage}) AS oval,
    ((p,s) -> {segment}) AS segment,
    ((acc,p,s) -> {paint}) AS paint,
    (p -> toUInt32(clamp(floor(p.2/{TILE}.),0.,{rows-1}.)*tileCols
                    +clamp(floor(p.1/{TILE}.),0.,{cols-1}.))+1) AS tileAt,
    (p -> arrayFilter(s -> p.1>=s.2.1 AND p.1<=s.2.3 AND p.2>=s.2.2 AND p.2<=s.2.4,
                       arrayMap(i -> shapes[i], tiles[tileAt(p)]))) AS nearby,
    ((p,initial) -> arrayFold((acc,s) -> paint(acc,p,s),nearby(p),initial)) AS draw,
    (p -> {sky}) AS sky,
    (p -> {water}) AS water,
    ((p,initial) -> arrayFold((acc,s) -> paint(acc,p,s),
        arrayFilter(s -> p.1>=s.2.1 AND p.1<=s.2.3 AND p.2>=s.2.2 AND p.2<=s.2.4,
            arrayMap(i -> shapes[i], arrayFilter(i -> i>={hero_first} AND i<={hero_last},tiles[tileAt(p)]))),initial)) AS hero,
    (p -> if(p.2>824.,
        mix(water(p),hero((p.1+5.*sin(p.2*.13)+2.*sin(p.2*.39),824.-(p.2-824.)*1.62),water(p)),
            .24*exp(-(p.2-824.)/190.)*(.7+.3*sin(p.2*.64))),
        if(p.2>508.,water(p),sky(p)))) AS backdrop
SELECT
    clamp(avg(col.1),0.,1.) AS r,
    clamp(avg(col.2),0.,1.) AS g,
    clamp(avg(col.3),0.,1.) AS b,
    pixel % W AS x,
    intDiv(pixel,W) AS y
FROM (
    SELECT pixel,
        tuplePlus(tupleMultiplyByNumber(draw(p,backdrop(p)),vignette),
                  (grain,grain,grain)) AS col
    FROM (
        SELECT intDiv(number,spp) AS pixel,
            number%spp AS sample,
            ((pixel%W+samplePattern[sample+1].1)*{WIDTH}.0/W,
             (intDiv(pixel,W)+samplePattern[sample+1].2)*{HEIGHT}.0/H) AS p,
            1.-.15*pow(clamp(hypot((p.1-800.)/1000.,(p.2-480.)/760.),0.,1.),2.) AS vignette,
            ((cityHash64(pixel,sample,42)%65536)/65535.-.5)*.008 AS grain
        FROM numbers_mt(W*H*spp)
    )
)
GROUP BY pixel
SETTINGS max_threads=8, max_block_size=256,
         max_ast_elements=1000000, max_expanded_ast_elements=2000000,
         short_circuit_function_evaluation='force_enable'
FORMAT PNG
""")
    print(f"Generated {len(SHAPES)} vector primitives, {len(tiles)} spatial buckets.",file=sys.stderr)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    generate()
