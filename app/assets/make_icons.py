# Istanbul-themed sight icons: little round scenes in Night's palette (flat style), 32x32, clipped to a circle.
import json, sys
TURQ, BRICK, BRASS, CREAM, CHAR = "var(--i-turq)", "var(--i-brick)", "var(--i-brass)", "var(--i-cream)", "var(--i-char)"
SKY, SAND, SEA, LEAF, ORNG = "var(--i-sky)", "var(--i-sand)", "var(--i-sea)", "var(--i-leaf)", "var(--i-orange)"
def f(c): return f'style="fill:{c}"'
def R(x,y,w,h,c,rx=0): return "" if h <= 0 or w <= 0 else f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" {f(c)}/>'
def C(x,y,r,c): return f'<circle cx="{x}" cy="{y}" r="{r}" {f(c)}/>'
def P(d,c): return f'<path d="{d}" {f(c)}/>'
def seg(y, c):  # bottom of the circle below y
    import math
    dx = math.sqrt(max(0, 256 - (y-16)**2)); return P(f"M{16-dx-1:.2f} {y} H{16+dx+1:.2f} V33 H{16-dx-1:.2f}Z", c)
def waves(y): return seg(y, SEA) + P(f"M3 {y+2.2} q2 -1.2 4 0 t4 0 t4 0 t4 0 t4 0 t4 0 t4 0", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-cream);stroke-width:.7;opacity:.7"')
def minaret(x, top, base, w=1.5, cap=BRASS, body=CREAM):
    return R(x-w/2, top+2.5, w, base-top-2.5, body) + P(f"M{x-w/2-.2} {top+2.6} L{x} {top} L{x+w/2+.2} {top+2.6}Z", cap) + R(x-w/2-.4, top+6, w+.8, .8, body)
def dome(cx, base, rx, ry, c): return P(f"M{cx-rx} {base} A{rx} {ry} 0 0 1 {cx+rx} {base}Z", c)
def arches(x0, y, n, w, h, c, gap):
    return "".join(P(f"M{x0+i*(w+gap)} {y+h} v{-h+w/2} a{w/2} {w/2} 0 0 1 {w} 0 v{h-w/2}z", c) for i in range(n))
def birds(): return P("M7 8 q1 -1 2 0 q1 -1 2 0", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-char);stroke-width:.6"')
sym = {}
sym["hagia"] = seg(24.5, LEAF) + minaret(5, 7, 25) + minaret(27, 7, 25) + minaret(8.2, 10, 25, 1.2) + minaret(23.8, 10, 25, 1.2) \
  + R(9.5, 17.5, 13, 7, SAND) + dome(11, 18, 2.6, 2.2, ORNG) + dome(21, 18, 2.6, 2.2, ORNG) + dome(16, 17.6, 5.8, 5.2, BRICK) \
  + R(15.75, 10.4, .5, 2.2, BRASS) + arches(11, 20, 5, 1.3, 2.6, CHAR, .9) + P("M12.4 15.5 h7.2", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-sand);stroke-width:.6"')
sym["bluemosque"] = seg(24.5, LEAF) + "".join(minaret(x, t, 25, 1.1, BRASS, CREAM) for x, t in [(3.8,9),(6.6,8),(9.2,11),(22.8,11),(25.4,8),(28.2,9)]) \
  + R(10, 18.5, 12, 6, SAND) + dome(12.2, 19, 2.2, 1.9, TURQ) + dome(19.8, 19, 2.2, 1.9, TURQ) + dome(16, 18.6, 4.6, 4.4, TURQ) + R(15.75, 12.4, .5, 1.9, BRASS) + arches(11.3, 21, 4, 1.4, 2.4, CHAR, 1.6)
sym["mosque"] = seg(24.5, LEAF) + minaret(8, 8, 25) + minaret(24, 8, 25) + R(10.5, 18, 11, 6.5, SAND) + dome(16, 18.2, 5, 4.6, BRASS) + R(15.75, 11.8, .5, 2, BRASS) + arches(12, 20.5, 4, 1.4, 2.6, CHAR, 1.3)
sym["ortakoy"] = waves(24) + P("M-1 13 Q16 22 33 13", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-char);stroke-width:1"') \
  + "".join(R(x, 13 + ((x-16)**2)/37 - .2, .3, 18 - (13 + ((x-16)**2)/37), CHAR) for x in [2,5,8,26,29]) + R(-1, 17.6, 34, .8, CHAR) \
  + minaret(9.5, 9, 24, 1.3) + minaret(22.5, 9, 24, 1.3) + R(11.5, 18, 9, 6, CREAM) + dome(16, 18.2, 4, 3.6, SAND) + arches(12.6, 20, 3, 1.6, 3, TURQ, 1.3)
sym["topkapi"] = seg(25, LEAF) + R(9, 15, 14, 10, SAND) + R(6, 12, 4.5, 13, CREAM) + R(21.5, 12, 4.5, 13, CREAM) \
  + P("M5.5 12.2 L8.25 4.8 L11 12.2Z", BRICK) + P("M21 12.2 L23.75 4.8 L26.5 12.2Z", BRICK) + P("M13 25 v-5 a3 3 0 0 1 6 0 v5z", CHAR) \
  + R(9, 14, 14, 1.4, BRICK) + "".join(R(x, 13, 1, 1, BRICK) for x in [9.5, 12, 14.5, 17, 19.5, 21.5])
sym["cistern"] = C(16, 16, 16, CHAR) + "".join(R(x, 9, 1.6, 16, SAND) for x in [5, 11, 17, 23]) \
  + "".join(P(f"M{x} 9.5 a3.2 3.2 0 0 1 6.4 0", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-orange);stroke-width:1.1"') for x in [5.8, 11.8, 17.8]) \
  + seg(24, SEA) + "".join(R(x, 24.6, 1.6, 3, SAND).replace("/>", ' opacity=".35"/>') for x in [5, 11, 17, 23]) + C(13.8, 20.5, 1.3, BRASS)
sym["obelisk"] = seg(25, SAND) + P("M14.3 23 L15 8 L16 6 L17 8 L17.7 23Z", BRASS) + R(12.5, 22.5, 7, 2.5, CREAM) + R(13.4, 21, 5.2, 1.6, ORNG) \
  + "".join(R(15.4, y, 1.2, .5, CHAR) for y in [11, 13.5, 16, 18.5]) + C(25, 9, 2.4, ORNG)
sym["museum"] = seg(25, LEAF) + P("M6 12 L16 6.5 L26 12Z", BRICK) + R(6, 12, 20, 1.5, CREAM) + "".join(R(x, 13.5, 1.6, 8.5, CREAM) for x in [7.5, 11.5, 15.2, 19, 22.9]) + R(5, 22, 22, 2.8, SAND)
sym["carpet"] = R(5, 7, 22, 18, BRICK, 1) + R(7, 9, 18, 14, ORNG) + P("M16 10.5 L22 16 L16 21.5 L10 16Z", CREAM) + P("M16 13 L19 16 L16 19 L13 16Z", TURQ) \
  + "".join(R(x, 25, .6, 2.5, SAND) for x in range(6, 27, 2)) + "".join(R(x, 4.5, .6, 2.5, SAND) for x in range(6, 27, 2))
sym["painting"] = R(6, 7, 20, 17, BRASS, 1) + R(8, 9, 16, 13, SKY) + seg(18, LEAF).replace("V33", "V22") + C(13, 15.5, 1.8, BRICK) + R(12.2, 17, 1.6, 4, BRICK) + P("M16 21 q2 -3 5 -1 l1 1z", CHAR) + R(14, 25, 4, 1.4, CHAR)
sym["modern"] = waves(24.5) + R(6, 13, 20, 11.5, CREAM) + R(6, 13, 20, 2, CHAR) + "".join(R(x, 16.5, 3, 6, TURQ) for x in [8, 12.5, 17, 21.5]) + C(24, 8, 2.2, ORNG)
sym["tulip"] = seg(26, LEAF) + P("M16 25 V15", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-leaf);stroke-width:1.4"') \
  + P("M16 22 q-6 -1 -7 -7 q5 1 7 7z", LEAF) + P("M16 23 q6 -1 7 -8 q-5 1 -7 8z", LEAF) \
  + P("M11.5 8 q0 7 4.5 8 q4.5 -1 4.5 -8 l-2.2 2 l-2.3 -3.5 l-2.3 3.5z", BRICK) + P("M16 6.5 l-2.3 3.5 q.8 5 2.3 6 q1.5 -1 2.3 -6z", ORNG)
sym["bazaar"] = seg(25.5, SAND) + R(7, 10, 18, 15.5, CREAM) + P("M10 25.5 v-8 a6 6 0 0 1 12 0 v8z", CHAR) \
  + "".join(P(f"M{10+i*1.5} {17.5 - (2.7 if 2<i<6 else 1.4 if i in (1,6) else 0)} ", "none") for i in range(0)) \
  + P("M10 17.5 a6 6 0 0 1 12 0", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-brick);stroke-width:1.4;stroke-dasharray:1.4 1.2"') \
  + R(6, 8.5, 20, 2, BRICK) + C(13, 20, 1, BRASS) + C(16, 21.5, 1, TURQ) + C(19, 20, 1, ORNG) + R(15.8, 14.5, .4, 7, BRASS)
sym["spice"] = seg(24, SAND) + "".join(P(f"M{x-4} 22 Q{x} {y} {x+4} 22Z", c) for x, y, c in [(9, 11, BRICK), (23, 12, BRASS), (16, 9, ORNG)]) \
  + R(3.5, 21.5, 25, 3, CHAR) + R(3.5, 21.5, 25, .8, BRASS)
sym["bridge"] = waves(21) + R(-1, 18.5, 34, 2.5, CREAM) + R(-1, 18, 34, .8, CHAR) + "".join(P(f"M{x} 18 L{x+5} 6", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-char);stroke-width:.5"') for x in [6, 13, 20]) \
  + "".join(P(f"M{x+5} 6 v{12+(i%2)*2}", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-char);stroke-width:.25"') for i, x in enumerate([6, 13, 20])) + C(25, 8, 2.2, ORNG)
sym["galata"] = seg(26, LEAF) + R(11.5, 12, 9, 14, SAND) + R(10.5, 11, 11, 1.6, CREAM) + P("M10.8 11.2 L16 3.5 L21.2 11.2Z", BRICK) \
  + "".join(P(f"M{x} 17 v-1.5 a.8 .8 0 0 1 1.6 0 v1.5z", CHAR) for x in [12.6, 15.2, 17.8]) + "".join(R(x, 20.5, 1.4, 2, CHAR) for x in [12.8, 15.3, 17.8]) \
  + R(9, 22, 2.5, 4, CREAM) + R(20.5, 21, 3, 5, ORNG)
sym["tram"] = seg(26, SAND) + P("M3 25.5 H29", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-char);stroke-width:.7"') + R(8, 9, 16, 15, BRICK, 2.5) + R(8, 9, 16, 2.4, CREAM, 1) \
  + R(10, 12.5, 5, 5, SKY, .8) + R(17, 12.5, 5, 5, SKY, .8) + R(10, 19.5, 12, 1.2, CREAM) + C(11, 23, .8, BRASS) + C(21, 23, .8, BRASS) \
  + P("M16 9 L13 4.5 M16 9 L19 4.5", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-char);stroke-width:.6"') + R(9.5, 24, 4, 1.5, CHAR) + R(18.5, 24, 4, 1.5, CHAR)
sym["simit"] = C(16, 16, 9.5, BRASS) + C(16, 16, 3.8, SKY) + C(16, 16, 7.6, ORNG).replace("/>", ' opacity=".35"/>') + C(16, 16, 3.8, SKY) \
  + "".join(R(16 + 6.3*__import__("math").cos(a/9*6.283) - .45, 16 + 6.3*__import__("math").sin(a/9*6.283) - .25, .9, .5, CREAM) for a in range(9)) \
  + "".join(R(16 + 8.4*__import__("math").cos((a+.5)/11*6.283) - .45, 16 + 8.4*__import__("math").sin((a+.5)/11*6.283) - .25, .9, .5, CREAM) for a in range(11))
sym["palace"] = waves(24) + R(4, 15, 24, 9, CREAM) + R(13, 11, 6, 13, CREAM) + P("M12.5 11.2 L16 8 L19.5 11.2Z", BRASS) + R(3.5, 14, 25, 1.3, BRASS) \
  + arches(5, 17.5, 3, 1.6, 4, TURQ, 1) + arches(20.6, 17.5, 3, 1.6, 4, TURQ, 1) + P("M14.5 24 v-4 a1.5 1.5 0 0 1 3 0 v4z", CHAR) + C(16, 14, 1.1, BRICK)
sym["fortress"] = waves(25) + R(5, 15, 22, 10, SAND) + R(4, 10, 6, 15, CREAM) + R(22, 10, 6, 15, CREAM) + R(13.5, 6.5, 5, 18.5, CREAM) \
  + P("M3.6 10.2 L7 4.6 L10.4 10.2Z", CHAR) + P("M21.6 10.2 L25 4.6 L28.4 10.2Z", CHAR) + "".join(R(x, 5.5, 1, 1, CREAM) for x in [13.5, 15.5, 17.5]) \
  + "".join(R(x, 14, 1.2, 1.2, SAND) for x in [11, 19.8]) + P("M14.6 25 v-3 a1.4 1.4 0 0 1 2.8 0 v3z", CHAR)
sym["houses"] = seg(25.5, SAND) + "".join(R(x, y, w, 25.5 - y, c) + P(f"M{x-.5} {y} L{x+w/2} {y-3} L{x+w+.5} {y}Z", BRICK if c != BRICK else CHAR)
  + R(x+1, y+2, w-2, 1.8, CREAM).replace("/>", ' opacity=".9"/>') + R(x+1, y+5.5, w-2, 1.8, CREAM) for x, y, w, c in [(3, 14, 6, TURQ), (9.5, 11, 6.5, ORNG), (16.5, 13, 6, BRASS), (23, 12, 6.5, BRICK)])
sym["tea"] = C(16, 16, 16, SKY) + P("M11 7 q0 4 1.5 7 q-1.5 3 -1 7 h9 q.5 -4 -1 -7 q1.5 -3 1.5 -7z", CREAM).replace("/>", ' opacity=".85"/>') \
  + P("M11.6 10 q.4 2.5 1.4 4 q-1.4 3 -.9 6.5 h7.8 q.5 -3.5 -.9 -6.5 q1 -1.5 1.4 -4z", BRICK) + P("M6 23 h20 q-1 3 -10 3 q-9 0 -10 -3z", BRASS) + R(19, 4, 1, 6, BRASS)
sym["mini"] = seg(24, LEAF) + R(4, 19, 6, 5, SAND) + dome(7, 19, 3, 2.5, BRICK) + minaret(3.2, 13, 24, .9) + R(13, 13, 4, 11, CREAM) + P("M12.6 13 L15 9 L17.4 13Z", BRICK) \
  + R(20, 17, 8, 7, TURQ) + P("M19.5 17 L24 14 L28.5 17Z", BRASS) + C(24, 7, 3, ORNG)
sym["maiden"] = waves(23) + P("M7 24 q9 -4 18 0z", SAND) + R(13.5, 13, 5, 9.5, CREAM) + P("M13 13 L16 6 L19 13Z", TURQ) + R(15.75, 4.3, .5, 2, BRASS) \
  + R(9.5, 18, 4, 4.5, CREAM) + R(18.5, 18, 4, 4.5, CREAM) + R(15.2, 15, 1.6, 2, CHAR) + C(25, 9, 2.2, ORNG)
sym["hilltower"] = P("M-1 33 V22 Q8 14 16 16 Q24 18 33 21 V33Z", LEAF) + R(15, 6, 2, 12, CREAM) + P("M14 6.5 h4 l-.5 -3 h-3z", BRICK) + R(13.8, 9, 4.4, 2, CREAM) + R(15.75, 1, .5, 3, CHAR) \
  + minaret(23, 12, 19, .8) + minaret(26.5, 12, 20, .8) + dome(24.75, 19.5, 2.2, 2, BRASS)
sym["fish"] = seg(24, SAND) + R(3, 21, 26, 3, CHAR) + P("M6 15 q5 -5 11 0 q-6 5 -11 0z", TURQ) + P("M17 15 l3 -2.5 v5z", TURQ) + C(8.5, 14.5, .6, CHAR) \
  + P("M12 20 q5 -5 11 0 q-6 5 -11 0z", BRASS) + P("M23 20 l3 -2.5 v5z", BRASS) + C(14.5, 19.5, .6, CHAR) + P("M21 8 a3 3 0 1 1 0 .01z", BRICK)
sym["island"] = waves(23) + P("M2 24 Q10 12 18 16 Q24 19 31 24Z", LEAF) + R(9, 15, 7, 6, CREAM) + P("M8.4 15 L12.5 11.5 L16.6 15Z", BRICK) + R(11, 17, 1.4, 2, TURQ) + R(13.5, 17, 1.4, 2, TURQ) \
  + P("M22 19 L24 11 L26 19Z", "var(--i-leaf2)") + R(23.6, 19, .8, 2, CHAR) + C(26, 7, 2.2, ORNG)
sym["tile"] = R(5, 5, 22, 22, CREAM, 1.2) + R(5, 5, 22, 22, "none") + P("M16 7 q4 4 0 9 q-4 -5 0 -9z", BRICK) + P("M16 16 q5 -1 7 -6 q-5 0 -7 6zM16 16 q-5 -1 -7 -6 q5 0 7 6z", TURQ) \
  + P("M16 16 v8", "none").replace('style="fill:none"', 'style="fill:none;stroke:var(--i-turq);stroke-width:1"') + "".join(C(x, y, 1.2, BRASS) for x, y in [(8, 8), (24, 8), (8, 24), (24, 24)]) + C(11, 21, 1.6, TURQ) + C(21, 21, 1.6, TURQ)
sym["mosaic"] = C(16, 16, 16, BRASS) + "".join(R(x, y, 1.7, 1.7, ORNG if (x*3+y) % 7 < 3 else SAND) for x in range(1, 31, 2) for y in range(1, 31, 2)) \
  + C(16, 12, 6, CREAM) + C(16, 12, 6.2, "none") + C(16, 12.5, 3.2, SAND) + P("M9 31 q0 -12 7 -12 q7 0 7 12z", TURQ) + P("M14.5 19 h3 v6 h-3z", CREAM)

MAP = {"Hagia Sophia":"hagia","Blue Mosque (Sultan Ahmed)":"bluemosque","Topkapi Palace":"topkapi","Basilica Cistern":"cistern","Hippodrome (Sultanahmet Square)":"obelisk",
 "Istanbul Archaeology Museums":"museum","Museum of Turkish and Islamic Arts":"carpet","Gulhane Park":"tulip","Grand Bazaar":"bazaar","Spice Bazaar":"spice","Suleymaniye Mosque":"mosque",
 "Rustem Pasha Mosque":"tile","Theodosius Cistern":"cistern","Galata Bridge":"bridge","Galata Tower":"galata","Istiklal Avenue":"tram","Taksim Square":"simit","Pera Museum":"painting",
 "Istanbul Modern":"modern","Dolmabahce Palace":"palace","Ortakoy Mosque":"ortakoy","Rumeli Fortress":"fortress","Chora (Kariye) Mosque":"mosaic","Balat and Fener streets":"houses",
 "Pierre Loti Hill":"tea","Miniaturk":"mini","Maiden's Tower":"maiden","Beylerbeyi Palace":"palace","Camlica Hill":"hilltower","Kadikoy Market and Moda":"fish","Buyukada (Princes' Islands)":"island"}
out = ['<clipPath id="mclip" clipPathUnits="userSpaceOnUse"><circle cx="16" cy="16" r="16"/></clipPath>']
for k, body in sym.items():
    out.append(f'<symbol id="m-{k}" viewBox="0 0 32 32"><g clip-path="url(#mclip)" style="stroke:none">{C(16,16,16,SKY)}{body}</g></symbol>')
open(sys.argv[1], "w").write("\n    ".join(out))
m = json.load(open(sys.argv[2]))
for x in m: x["ic"] = MAP[x["n"]]
json.dump(m, open(sys.argv[2], "w"), ensure_ascii=False, separators=(",", ":"))
print(len(sym), "symbols")
