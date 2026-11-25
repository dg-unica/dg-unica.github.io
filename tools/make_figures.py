"""Generate the research illustrations (SVG) used on the topic pages.

Usage:  python3 tools/make_figures.py
Output: assets/img/research/*.svg

All figures share the same style: line drawings in the site's navy, with one
accent element in burgundy, depth shading for 3D wireframes, transparent background.
"""
import math
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "research")
NAVY, RED, SOFT, SOFTRED, GREY = "#2a3a64", "#8e2f33", "#c9d2e6", "#ecd3d5", "#8a93a8"
FONT = "Georgia, 'Times New Roman', serif"
W, H = 600, 450


def svg(body, w=W, h=H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="{FONT}">{body}</svg>\n')


def save(name, content):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(content)
    print("wrote", name, len(content) // 1024, "KB")


def text(x, y, s, size=22, color=NAVY, italic=True, anchor="middle", extra=""):
    st = ' font-style="italic"' if italic else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="{anchor}"{st}{extra}>{s}</text>'


class View:
    """Rotation about the vertical axis, then tilt towards the viewer, then scale."""

    def __init__(self, rot, tilt, scale, cx=W / 2, cy=H / 2):
        self.cr, self.sr, self.ct, self.st = math.cos(rot), math.sin(rot), math.cos(tilt), math.sin(tilt)
        self.s, self.cx, self.cy = scale, cx, cy

    def p(self, P):
        x, y, z = P
        x1, y1 = x * self.cr - y * self.sr, x * self.sr + y * self.cr
        Y = z * self.ct - y1 * self.st
        depth = y1 * self.ct + z * self.st  # small = front
        return (self.cx + x1 * self.s, self.cy - Y * self.s, depth)


def wire(view, curves, color=NAVY, width=1.0, amin=0.12, amax=0.9, rng=None):
    """Draw 3D polylines with opacity decreasing with depth (6 opacity buckets)."""
    pts = [[view.p(P) for P in c] for c in curves]
    if rng is None:
        ds = [q[2] for c in pts for q in c]
        rng = (min(ds), max(ds))
    lo, hi = rng
    buckets = [[] for _ in range(6)]
    for c in pts:
        for a, b in zip(c, c[1:]):
            t = ((a[2] + b[2]) / 2 - lo) / (hi - lo + 1e-9)
            k = max(0, min(5, int(t * 6)))
            buckets[k].append(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}")
    out = ""
    for k, b in enumerate(buckets):
        if b:
            op = amax - (amax - amin) * k / 5
            out += (f'<path d="{"".join(b)}" stroke="{color}" stroke-width="{width}" '
                    f'stroke-opacity="{op:.2f}" fill="none" stroke-linecap="round"/>')
    return out, rng


def lin(a, b, n):
    return [a + (b - a) * i / n for i in range(n + 1)]


def arrow_head(x, y, ang, color, size=10):
    a1, a2 = ang + math.pi - 0.4, ang + math.pi + 0.4
    return (f'<path d="M{x:.1f} {y:.1f}L{x + size * math.cos(a1):.1f} {y + size * math.sin(a1):.1f}'
            f'L{x + size * math.cos(a2):.1f} {y + size * math.sin(a2):.1f}Z" fill="{color}"/>')


def sphere_grid(center, r, nlat=9, nlon=16, n=60):
    cx, cy, cz = center
    curves = []
    for i in range(1, nlat):
        ph = -math.pi / 2 + math.pi * i / nlat
        curves.append([(cx + r * math.cos(ph) * math.cos(t), cy + r * math.cos(ph) * math.sin(t), cz + r * math.sin(ph))
                       for t in lin(0, 2 * math.pi, n)])
    for j in range(nlon):
        t = 2 * math.pi * j / nlon
        curves.append([(cx + r * math.cos(ph) * math.cos(t), cy + r * math.cos(ph) * math.sin(t), cz + r * math.sin(ph))
                       for ph in lin(-math.pi / 2, math.pi / 2, n // 2)])
    return curves


def contours(f, xs, ys, levels):
    """Marching squares. f is a 2D list f[i][j] at (xs[i], ys[j]); None = outside. Returns {level: path}."""
    out = {}
    for L in levels:
        segs = []
        for i in range(len(xs) - 1):
            for j in range(len(ys) - 1):
                v = [f[i][j], f[i + 1][j], f[i + 1][j + 1], f[i][j + 1]]
                if any(x is None for x in v):
                    continue
                c = [(xs[i], ys[j]), (xs[i + 1], ys[j]), (xs[i + 1], ys[j + 1]), (xs[i], ys[j + 1])]
                pts = []
                for k in range(4):
                    a, b = v[k] - L, v[(k + 1) % 4] - L
                    if (a < 0) != (b < 0):
                        t = a / (a - b)
                        p, q = c[k], c[(k + 1) % 4]
                        pts.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
                for k in range(0, len(pts) - 1, 2):
                    (x0, y0), (x1, y1) = pts[k], pts[k + 1]
                    segs.append(f"M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}")
        out[L] = "".join(segs)
    return out


# ---------------------------------------------------------------- figures

def harmonic_map():
    v = View(rot=0.55, tilt=0.42, scale=118, cy=235)
    n = 10
    sheet = [[(u, w, 1.25) for u in lin(-1, 1, 20)] for w in lin(-1, 1, n)] + \
            [[(u, w, 1.25) for w in lin(-1, 1, 20)] for u in lin(-1, 1, n)]

    def onto(a, b):  # inverse stereographic projection onto the upper cap of the unit sphere
        a, b = 1.25 * a, 1.25 * b
        d = 1 + a * a + b * b
        return (2 * a / d, 2 * b / d, -0.85 + (1 - a * a - b * b) / d)

    img = [[onto(u, w) for u in lin(-1, 1, 30)] for w in lin(-1, 1, n)] + \
          [[onto(u, w) for w in lin(-1, 1, 30)] for u in lin(-1, 1, n)]
    body, rng = wire(v, sphere_grid((0, 0, -0.85), 1, 7, 14), SOFT, 1, 0.25, 0.9)
    b2, _ = wire(v, sheet, NAVY, 1.1, 0.35, 0.95)
    b3, _ = wire(v, img, NAVY, 1.1, 0.25, 0.95, rng)
    hl = [[(u, 0.4, 1.25) for u in lin(-1, 1, 30)]]
    b4, _ = wire(v, hl, RED, 2.4, 0.9, 1)
    b5, _ = wire(v, [[onto(u, 0.4) for u in lin(-1, 1, 40)]], RED, 2.4, 0.9, 1, rng)
    x0, y0, _ = v.p((1.35, -1.1, 1.0))
    x1, y1, _ = v.p((1.35, -1.1, -0.2))
    arr = (f'<path d="M{x0:.1f} {y0:.1f}C{x0 + 40:.1f} {y0 + 40:.1f} {x1 + 40:.1f} {y1 - 40:.1f} {x1:.1f} {y1:.1f}" '
           f'stroke="{RED}" stroke-width="2" fill="none"/>' + arrow_head(x1, y1, math.atan2(40, -40), RED))
    lab = text(x0 + 52, (y0 + y1) / 2 + 6, "φ", 30, RED)
    mx, my, _ = v.p((-1.1, -1.1, 1.25))
    nx, ny, _ = v.p((0, 0, -0.85))
    nx, ny = nx - 1.32 * v.s, ny + 8
    save("harmonic-map.svg", svg(body + b2 + b3 + b4 + b5 + arr + lab +
                                 text(mx - 18, my + 6, "M", 28) + text(nx, ny, "N", 28)))


def catenoid():
    v = View(rot=0.3, tilt=0.32, scale=95, cy=225)
    curves = [[(math.cosh(w) * math.cos(u), math.cosh(w) * math.sin(u), w) for u in lin(0, 2 * math.pi, 72)]
              for w in lin(-1.3, 1.3, 14)]
    curves += [[(math.cosh(w) * math.cos(u), math.cosh(w) * math.sin(u), w) for w in lin(-1.3, 1.3, 30)]
               for u in lin(0, 2 * math.pi, 36)[:-1]]
    body, rng = wire(v, curves, NAVY, 1)
    neck, _ = wire(v, [[(math.cos(u), math.sin(u), 0) for u in lin(0, 2 * math.pi, 90)]], RED, 2.4, 0.4, 1, rng)
    save("catenoid.svg", svg(body + neck))


def contact_planes():
    v = View(rot=-1.2, tilt=0.42, scale=74, cy=230)
    quads = []
    s = 0.46
    for x in lin(-2, 2, 4):
        for y in lin(-2, 2, 4):
            a = (0, s, 0)
            nb = math.sqrt(1 + y * y)
            b = (s / nb, 0, s * y / nb)
            c = (x, y, 0)
            corners = [tuple(c[i] + sa * a[i] + sb * b[i] for i in range(3)) for sa, sb in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
            P = [v.p(q) for q in corners]
            quads.append((sum(q[2] for q in P) / 4, P, abs(y) < 0.01))
    quads.sort(key=lambda q: -q[0])
    body = ""
    for d, P, mid in quads:
        pts = " ".join(f"{q[0]:.1f},{q[1]:.1f}" for q in P)
        col = RED if mid else NAVY
        fill = SOFTRED if mid else SOFT
        body += f'<polygon points="{pts}" fill="{fill}" fill-opacity="0.75" stroke="{col}" stroke-width="1.3" stroke-linejoin="round"/>'
    # axes
    o = v.p((-2.9, -2.9, -0.9))
    ax = ""
    for e, lab in [((1.2, 0, 0), "x"), ((0, 1.2, 0), "y"), ((0, 0, 1.2), "z")]:
        q = v.p((-2.9 + e[0], -2.9 + e[1], -0.9 + e[2]))
        ax += f'<path d="M{o[0]:.1f} {o[1]:.1f}L{q[0]:.1f} {q[1]:.1f}" stroke="{GREY}" stroke-width="1.4"/>'
        ax += arrow_head(q[0], q[1], math.atan2(q[1] - o[1], q[0] - o[0]), GREY, 8)
        ax += text(q[0] + 10 * math.cos(math.atan2(q[1] - o[1], q[0] - o[0])), q[1] + 6 + 10 * math.sin(math.atan2(q[1] - o[1], q[0] - o[0])), lab, 18, GREY)
    save("contact-planes.svg", svg(body))


def reeb_component():
    X = lambda x: 300 + x * 190
    Y = lambda y: 410 - y * 120
    body = ""
    cs = [c / 2 for c in range(-12, 7)]
    for c in cs:
        pts = []
        for x in lin(-0.999, 0.999, 400):
            y = c + 1 / (1 - x * x) - 1
            if 0 <= y <= 3:
                pts.append(f"{X(x):.1f} {Y(y):.1f}")
            elif pts and y > 3:
                pts.append(f"{X(x):.1f} {Y(3):.1f}")
        if len(pts) > 1:
            body += f'<path d="M{"L".join(pts)}" stroke="{NAVY}" stroke-width="1.2" fill="none" stroke-opacity="0.85"/>'
    # outside the component: horizontal-ish leaves of the complementary region
    for xx in (-1, 1):
        body += f'<path d="M{X(xx):.1f} {Y(0):.1f}L{X(xx):.1f} {Y(3):.1f}" stroke="{RED}" stroke-width="3"/>'
    body = f'<clipPath id="c"><rect x="{X(-1.3):.1f}" y="{Y(3):.1f}" width="{X(1.3) - X(-1.3):.1f}" height="{Y(0) - Y(3):.1f}"/></clipPath><g clip-path="url(#c)">{body}</g>'
    body += text(X(1) + 28, Y(1.5), "T²", 24, RED)
    save("reeb-component.svg", svg(body))


def fubini_study():
    v = View(rot=0.6, tilt=0.38, scale=105, cy=265)
    body, rng = wire(v, sphere_grid((0, 0, 1), 1, 9, 16), NAVY, 1, 0.15, 0.9)
    plane = [[(x, y, 0) for x in lin(-2.6, 2.6, 2)] for y in lin(-2.6, 2.6, 13)] + \
            [[(x, y, 0) for y in lin(-2.6, 2.6, 2)] for x in lin(-2.6, 2.6, 13)]
    pb, _ = wire(v, plane, SOFT, 1, 0.5, 1)
    N = (0, 0, 2)
    rays = ""
    for (a, b) in [(1.9, -1.2), (-1.4, 1.7), (0.9, 2.2)]:
        t = 4 / (a * a + b * b + 4)
        q = (t * a, t * b, 2 - 2 * t)
        p0, p1, p2 = v.p(N), v.p(q), v.p((a, b, 0))
        rays += f'<path d="M{p0[0]:.1f} {p0[1]:.1f}L{p2[0]:.1f} {p2[1]:.1f}" stroke="{RED}" stroke-width="1.4" stroke-dasharray="5 4"/>'
        rays += f'<circle cx="{p1[0]:.1f}" cy="{p1[1]:.1f}" r="4.5" fill="{RED}"/><circle cx="{p2[0]:.1f}" cy="{p2[1]:.1f}" r="4.5" fill="{RED}"/>'
    n = v.p(N)
    rays += f'<circle cx="{n[0]:.1f}" cy="{n[1]:.1f}" r="5" fill="{NAVY}"/>'
    c = v.p((2.6, -2.6, 0))
    s = v.p((0.8, -0.8, 1.9))
    save("fubini-study.svg", svg(pb + body + rays + text(c[0] + 10, c[1] + 26, "ℂ", 28) +
                                 text(s[0] + 60, s[1] - 10, "ℂP¹", 26)))


def hodge_diamond():
    rows = [[(0, 0)], [(1, 0), (0, 1)], [(2, 0), (1, 1), (0, 2)], [(2, 1), (1, 2)], [(2, 2)]]
    body = ""
    pos = {}
    for k, row in enumerate(rows):
        y = 70 + 78 * k
        for i, (p, q) in enumerate(row):
            x = 300 + (i - (len(row) - 1) / 2) * 120
            pos[(p, q)] = (x, y)
            col = RED if (p, q) in [(1, 0), (0, 1), (2, 1), (1, 2)] else NAVY
            body += (f'<text x="{x:.1f}" y="{y:.1f}" font-size="28" fill="{col}" text-anchor="middle" font-style="italic">h'
                     f'<tspan dy="-12" font-size="17">{p},{q}</tspan></text>')
    # conjugation symmetry
    yv = pos[(1, 1)][1] - 9
    body += f'<path d="M140 {yv}L460 {yv}" stroke="{GREY}" stroke-width="1" stroke-dasharray="3 5"/>'
    body += f'<path d="M300 40L300 400" stroke="{GREY}" stroke-width="1" stroke-dasharray="3 5"/>'
    # Lefschetz arrow H^1 -> H^3
    x0, y0 = pos[(0, 1)][0] + 55, pos[(0, 1)][1] - 8
    x1, y1 = pos[(1, 2)][0] + 55, pos[(1, 2)][1] - 8
    body += (f'<path d="M{x0} {y0}C{x0 + 85} {y0 + 20} {x1 + 85} {y1 - 20} {x1} {y1}" stroke="{RED}" stroke-width="2" fill="none"/>'
             + arrow_head(x1, y1, math.atan2(20, -85), RED))
    body += text(x0 + 105, (y0 + y1) / 2 + 8, "L", 26, RED, anchor="start")
    save("hodge-diamond.svg", svg(body))


def double_complex():
    O, D = (130, 380), 85
    P = lambda p, q: (O[0] + p * D, O[1] - q * D)
    body = ""
    for p in range(4):
        for q in range(4):
            x, y = P(p, q)
            if p < 3:
                body += f'<path d="M{x + 12} {y}L{x + D - 14} {y}" stroke="{SOFT}" stroke-width="1.6"/>' + arrow_head(x + D - 12, y, 0, SOFT, 8)
            if q < 3:
                body += f'<path d="M{x} {y - 12}L{x} {y - D + 14}" stroke="{SOFT}" stroke-width="1.6"/>' + arrow_head(x, y - D + 12, -math.pi / 2, SOFT, 8)
    zig = [((0, 2), (1, 2)), ((1, 1), (1, 2)), ((1, 1), (2, 1)), ((2, 0), (2, 1))]
    for a, b in zig:
        (x0, y0), (x1, y1) = P(*a), P(*b)
        ang = math.atan2(y1 - y0, x1 - x0)
        body += (f'<path d="M{x0 + 12 * math.cos(ang):.1f} {y0 + 12 * math.sin(ang):.1f}L{x1 - 14 * math.cos(ang):.1f} {y1 - 14 * math.sin(ang):.1f}" '
                 f'stroke="{RED}" stroke-width="3"/>' + arrow_head(x1 - 12 * math.cos(ang), y1 - 12 * math.sin(ang), ang, RED, 11))
    on = {a for e in zig for a in e}
    for p in range(4):
        for q in range(4):
            x, y = P(p, q)
            body += f'<circle cx="{x}" cy="{y}" r="6.5" fill="{RED if (p, q) in on else NAVY}"/>'
    x, y = P(3, 0)
    body += text(x + 50, y + 8, "p", 24, GREY)
    x, y = P(0, 3)
    body += text(x, y - 32, "q", 24, GREY)
    body += text(O[0] + 1.5 * D, O[1] + 42, "∂", 26) + text(O[0] - 40, O[1] - 1.5 * D + 8, "∂̄", 26)
    save("double-complex.svg", svg(body))


def poincare_disc():
    cx, cy, R = 300, 225, 190
    n = 18
    body = f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{SOFT}" fill-opacity="0.25" stroke="{NAVY}" stroke-width="2"/>'

    def geod(a, b, color, width, op):
        d = (b - a) / 2
        r = R * math.tan(d)
        x0, y0 = cx + R * math.cos(a), cy - R * math.sin(a)
        x1, y1 = cx + R * math.cos(b), cy - R * math.sin(b)
        return (f'<path d="M{x0:.1f} {y0:.1f}A{r:.1f} {r:.1f} 0 0 1 {x1:.1f} {y1:.1f}" stroke="{color}" '
                f'stroke-width="{width}" stroke-opacity="{op}" fill="none"/>')

    for k in range(n):
        a = 2 * math.pi * k / n
        body += geod(a, a + 2 * math.pi * 5 / n, NAVY, 1.1, 0.75)
        body += geod(a, a + 2 * math.pi * 3 / n, NAVY, 0.9, 0.4)
    body += geod(0.35, 0.35 + 2 * math.pi * 7 / n, RED, 2.6, 1)
    save("poincare-disc.svg", svg(body))


def loxodrome():
    v = View(rot=0.4, tilt=0.35, scale=165, cy=225)
    body, rng = wire(v, sphere_grid((0, 0, 0), 1, 12, 20), NAVY, 1, 0.1, 0.75)
    k = 2.6
    curve = []
    for ph in lin(-1.48, 1.48, 900):
        lam = k * math.atanh(math.sin(ph))
        curve.append((math.cos(ph) * math.cos(lam), math.cos(ph) * math.sin(lam), math.sin(ph)))
    lx, _ = wire(v, [curve], RED, 2.4, 0.25, 1, rng)
    save("loxodrome.svg", svg(body + lx))


def enneper():
    v = View(rot=0.35, tilt=0.55, scale=88, cy=215)

    def E(r, t):
        return (r * math.cos(t) - r ** 3 / 3 * math.cos(3 * t), -r * math.sin(t) - r ** 3 / 3 * math.sin(3 * t), r * r * math.cos(2 * t))

    curves = [[E(r, t) for t in lin(0, 2 * math.pi, 120)] for r in lin(0.12, 1.45, 12)]
    curves += [[E(r, t) for r in lin(0, 1.45, 30)] for t in lin(0, 2 * math.pi, 48)[:-1]]
    body, rng = wire(v, curves, NAVY, 1, 0.15, 0.9)
    edge, _ = wire(v, [[E(1.45, t) for t in lin(0, 2 * math.pi, 240)]], RED, 2.4, 0.35, 1, rng)
    save("enneper.svg", svg(body + edge))


def hopf():
    """Hopf fibres on a torus of revolution: they are Villarceau circles, pairwise linked."""
    v = View(rot=0.3, tilt=0.75, scale=78, cy=230)
    R, r = 2.0, 1.0
    th = math.asin(r / R)
    T = lambda u, w: ((R + r * math.cos(w)) * math.cos(u), (R + r * math.cos(w)) * math.sin(u), r * math.sin(w))
    grid = [[T(u, w) for w in lin(0, 2 * math.pi, 50)] for u in lin(0, 2 * math.pi, 40)[:-1]]
    grid += [[T(u, w) for u in lin(0, 2 * math.pi, 120)] for w in lin(0, 2 * math.pi, 14)[:-1]]
    body, rng = wire(v, grid, SOFT, 0.9, 0.25, 0.95)

    def villarceau(phi):
        pts = []
        for t in lin(0, 2 * math.pi, 200):
            x, y, z = r + R * math.cos(t), R * math.sin(t) * math.cos(th), R * math.sin(t) * math.sin(th)
            pts.append((x * math.cos(phi) - y * math.sin(phi), x * math.sin(phi) + y * math.cos(phi), z))
        return pts

    # sanity check: the circle lies on the torus
    for (x, y, z) in villarceau(0.3)[::20]:
        assert abs((math.hypot(x, y) - R) ** 2 + z * z - r * r) < 1e-9
    fb, _ = wire(v, [villarceau(phi) for phi in lin(0, 2 * math.pi, 7)[:-1]], RED, 2.0, 0.3, 1, rng)
    save("hopf-fibration.svg", svg(body + fb))


def nodal_square():
    N = 140
    xs, ys = lin(0, 1, N), lin(0, 1, N)
    u = lambda x, y: math.sin(3 * math.pi * x) * math.sin(math.pi * y) + math.sin(math.pi * x) * math.sin(3 * math.pi * y)
    f = [[u(x, y) for y in ys] for x in xs]
    m = max(abs(val) for row in f for val in row)
    levels = [m * t for t in (-0.85, -0.6, -0.35, -0.12, 0.12, 0.35, 0.6, 0.85)]
    S, ox, oy = 370, 115, 40
    paths = contours(f, [ox + x * S for x in xs], [oy + (1 - y) * S for y in ys], levels + [0])
    body = f'<rect x="{ox}" y="{oy}" width="{S}" height="{S}" fill="none" stroke="{NAVY}" stroke-width="2"/>'
    for L in levels:
        col = NAVY if L > 0 else GREY
        dash = "" if L > 0 else ' stroke-dasharray="4 4"'
        body += f'<path d="{paths[L]}" stroke="{col}" stroke-width="1.2" fill="none" stroke-opacity="0.8"{dash}/>'
    body += f'<path d="{paths[0]}" stroke="{RED}" stroke-width="3" fill="none" stroke-linecap="round"/>'
    save("nodal-square.svg", svg(body))


def nodal_disc():
    def J1(x):
        s, term = 0.0, x / 2
        for k in range(40):
            s += term
            term *= -(x / 2) ** 2 / ((k + 1) * (k + 2))
        return s

    j12 = 7.0155866698
    N = 160
    R, cx, cy = 190, 300, 225
    xs, ys = lin(-1, 1, N), lin(-1, 1, N)
    f = [[(J1(j12 * math.hypot(x, y)) * (x / (math.hypot(x, y) + 1e-12)) if math.hypot(x, y) <= 1.0 else None)
          for y in ys] for x in xs]
    m = max(abs(val) for row in f for val in row if val is not None)
    levels = [m * t for t in (-0.8, -0.5, -0.25, 0.25, 0.5, 0.8)]
    paths = contours(f, [cx + x * R for x in xs], [cy - y * R for y in ys], levels)
    body = f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{NAVY}" stroke-width="2"/>'
    for L in levels:
        col = NAVY if L > 0 else GREY
        dash = "" if L > 0 else ' stroke-dasharray="4 4"'
        body += f'<path d="{paths[L]}" stroke="{col}" stroke-width="1.2" fill="none" stroke-opacity="0.8"{dash}/>'
    r1 = R * 3.8317059702 / j12  # interior nodal circle
    body += f'<circle cx="{cx}" cy="{cy}" r="{r1:.1f}" fill="none" stroke="{RED}" stroke-width="3"/>'
    body += f'<path d="M{cx} {cy - R}L{cx} {cy + R}" stroke="{RED}" stroke-width="3"/>'
    save("nodal-disc.svg", svg(body))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fig in (harmonic_map, catenoid, contact_planes, reeb_component, fubini_study, hodge_diamond,
                double_complex, poincare_disc, loxodrome, enneper, hopf, nodal_square, nodal_disc):
        fig()
