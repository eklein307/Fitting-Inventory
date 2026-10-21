"""Generic line drawings of compression tube fittings for reportlab.

Each drawing is a simple side view in its own unit space, centred on the
tube axis (y = 0). draw_fitting() scales a drawing to fit a box on a
reportlab canvas. Drawings are illustrative only and not to scale; the same
drawing is used for every size of a given fitting type.
"""

import math

from reportlab.lib.colors import HexColor, white

INK = HexColor("#2B2F33")
STEEL = HexColor("#DDE1E5")
STEEL_DARK = HexColor("#C2C9D0")
TUBE = HexColor("#F1F3F5")
THREAD = HexColor("#7D868E")
PANEL = HexColor("#8F99A2")
ACCENT = HexColor("#1F6FB2")

LINE_PT = 0.6      # outline width in points, kept constant at any scale
FINE_PT = 0.35     # thread marks, hex flats, hidden lines
MAX_SCALE = 1.1    # points per drawing unit, so small parts aren't blown up


class Sketch:
    """Draws in drawing units while keeping line widths fixed in points."""

    def __init__(self, c, scale):
        self.c = c
        self.scale = scale

    def _pen(self, pt, color, dash):
        self.c.setLineWidth(pt / self.scale)
        self.c.setStrokeColor(color)
        self.c.setDash([d / self.scale for d in dash] if dash else [])

    def poly(self, pts, fill=None, pt=LINE_PT, color=INK, dash=None):
        p = self.c.beginPath()
        p.moveTo(*pts[0])
        for xy in pts[1:]:
            p.lineTo(*xy)
        p.close()
        self.draw_path(p, fill, pt, color, dash)

    def rect(self, x1, y1, x2, y2, fill=None, **kw):
        self.poly([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], fill, **kw)

    def line(self, x1, y1, x2, y2, pt=FINE_PT, color=INK, dash=None):
        self._pen(pt, color, dash)
        self.c.line(x1, y1, x2, y2)
        self.c.setDash([])

    def circle(self, x, y, r, fill=None, pt=LINE_PT, color=INK):
        self._pen(pt, color, None)
        if fill is not None:
            self.c.setFillColor(fill)
        self.c.circle(x, y, r, stroke=1, fill=1 if fill is not None else 0)

    def draw_path(self, p, fill=None, pt=LINE_PT, color=INK, dash=None):
        self._pen(pt, color, dash)
        if fill is not None:
            self.c.setFillColor(fill)
        self.c.drawPath(p, stroke=1, fill=1 if fill is not None else 0)
        self.c.setDash([])


# ---------------------------------------------------------------- components
# All components run along +x with the tube axis at y = 0.

def hex_body(s, x1, x2, h, fill=STEEL_DARK):
    """Hex seen from the side: a block with two flat lines."""
    s.rect(x1, -h / 2, x2, h / 2, fill)
    s.line(x1, h / 4, x2, h / 4)
    s.line(x1, -h / 4, x2, -h / 4)


def nut(s, x1, x2, h, fill=STEEL):
    """Hex nut seen from the side, with chamfered corners."""
    ch = min(2.0, (x2 - x1) / 4)
    s.poly([(x1 + ch, -h / 2), (x2 - ch, -h / 2), (x2, -h / 2 + ch),
            (x2, h / 2 - ch), (x2 - ch, h / 2), (x1 + ch, h / 2),
            (x1, h / 2 - ch), (x1, -h / 2 + ch)], fill)
    s.line(x1, h / 4, x2, h / 4)
    s.line(x1, -h / 4, x2, -h / 4)


def male_thread(s, x1, x2, h, end_h=None):
    """Threaded section; end_h smaller than h gives a tapered (NPT) thread."""
    end_h = h if end_h is None else end_h
    s.poly([(x1, -h / 2), (x2, -end_h / 2), (x2, end_h / 2), (x1, h / 2)], STEEL)
    pitch = 2.2
    x = x1 + pitch * 0.75
    while x < x2 - pitch * 0.4:
        hx = h + (end_h - h) * (x - x1) / (x2 - x1)
        s.line(x - 0.7, -hx / 2, x + 0.7, hx / 2, color=THREAD)
        x += pitch


def fitting_end(s, x0, k=1.0):
    """Body thread plus tube nut running along +x from x0; k scales diameter."""
    male_thread(s, x0, x0 + 8, 16 * k)
    nut(s, x0 + 6, x0 + 21, 24 * k)


def arm(s, angle, x0, k=1.0):
    """A fitting end rotated about the origin (0 = right, 90 = up)."""
    s.c.saveState()
    s.c.rotate(angle)
    fitting_end(s, x0, k)
    s.c.restoreState()


def hexagon(s, cx, h, hole_r, fill=STEEL):
    """Hex nut seen end-on (flats top and bottom), with a bore."""
    r = (h / 2) / math.sin(math.radians(60))
    pts = [(cx + r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
           for a in range(0, 360, 60)]
    s.poly(pts, fill)
    s.circle(cx, 0, r * 0.82, pt=FINE_PT)  # chamfer circle
    if hole_r:
        s.circle(cx, 0, hole_r, fill=white)


def front_ferrule(s, dx=0.0):
    s.poly([(dx - 12, -4), (dx + 4, -9), (dx + 10, -9),
            (dx + 10, 9), (dx + 4, 9), (dx - 12, 4)], STEEL)
    s.line(dx + 4, -9, dx + 4, 9)
    s.line(dx - 12, 2.5, dx + 10, 2.5, dash=(1.4, 1.0))
    s.line(dx - 12, -2.5, dx + 10, -2.5, dash=(1.4, 1.0))


def back_ferrule(s, dx=0.0):
    s.poly([(dx - 5, -5), (dx - 1, -8), (dx + 6, -8),
            (dx + 6, 8), (dx - 1, 8), (dx - 5, 5)], STEEL)
    s.line(dx - 1, -8, dx - 1, 8)
    s.line(dx - 5, 3, dx + 6, 3, dash=(1.4, 1.0))
    s.line(dx - 5, -3, dx + 6, -3, dash=(1.4, 1.0))


# ------------------------------------------------------------------ drawings

def d_union(s):
    hex_body(s, -9, 9, 22)
    arm(s, 0, 9)
    arm(s, 180, 9)


def d_reducing_union(s):
    hex_body(s, -9, 9, 24)
    arm(s, 180, 9, k=1.15)
    arm(s, 0, 9, k=0.8)


def _block(s):
    s.rect(-10, -10, 10, 10, STEEL_DARK)


def d_union_elbow(s):
    _block(s)
    arm(s, 180, 10)
    arm(s, 90, 10)


def d_union_tee(s):
    _block(s)
    for a in (180, 0, 90):
        arm(s, a, 10)


def d_union_cross(s):
    _block(s)
    for a in (0, 90, 180, 270):
        arm(s, a, 10)


def d_bulkhead_union(s):
    male_thread(s, -6, 28, 16)        # long threaded body
    hex_body(s, -18, -6, 24)
    arm(s, 180, 18)                   # left tube nut
    nut(s, 26, 41, 24)                # right tube nut
    s.rect(-4, -20, 0, 20, PANEL)     # panel the union passes through
    nut(s, 0, 7, 27)                  # bulkhead lock nut


def d_male_connector(s):
    arm(s, 180, 8)
    male_thread(s, 8, 28, 15, end_h=12)   # tapered NPT end
    hex_body(s, -8, 8, 22)


def d_female_connector(s):
    arm(s, 180, 4)
    hex_body(s, -4, 24, 26)
    # hidden threaded NPT port at the right end
    s.rect(11, -8, 24, 8, pt=FINE_PT, dash=(1.4, 1.0))
    s.line(11, 5.5, 24, 5.5, dash=(1.4, 1.0))
    s.line(11, -5.5, 24, -5.5, dash=(1.4, 1.0))


def d_reducer(s):
    arm(s, 180, 6, k=0.9)
    s.rect(6, -5.5, 30, 5.5, TUBE)    # tube stub
    hex_body(s, -6, 6, 20)


def _port_connector(s, stub_h, nut_h):
    s.rect(8, -stub_h / 2, 40, stub_h / 2, TUBE)          # tube end
    s.poly([(-8, -3.5), (-2, -6), (-2, 6), (-8, 3.5)], STEEL)  # ferrule nose
    nut(s, -2, 13, nut_h)


def d_port_connector(s):
    _port_connector(s, stub_h=10, nut_h=22)


def d_reducing_port_connector(s):
    _port_connector(s, stub_h=7, nut_h=24)


def d_cap(s):
    nut(s, -10, 6, 24)
    p = s.c.beginPath()
    p.moveTo(6, -9)
    p.curveTo(12, -9, 12, 9, 6, 9)
    p.close()
    s.draw_path(p, STEEL_DARK)


def d_plug(s):
    s.rect(0, -5, 14, 5, STEEL)
    s.poly([(14, -5), (20, -3), (20, 3), (14, 5)], STEEL)
    hex_body(s, -12, 0, 22)


def d_nut(s):
    nut(s, -8, 8, 24)
    r = 12 / math.sin(math.radians(60))
    hexagon(s, 8 + 6 + r, 24, 5)


def d_bulkhead_lock_nut(s):
    nut(s, -4, 4, 28)
    r = 14 / math.sin(math.radians(60))
    hexagon(s, 4 + 6 + r, 28, 9.5)


def d_front_ferrule(s):
    front_ferrule(s)


def d_back_ferrule(s):
    back_ferrule(s)


def d_ferrule_set(s):
    front_ferrule(s, dx=-10)
    back_ferrule(s, dx=12)


def _hex_r(h):
    return (h / 2) / math.sin(math.radians(60))


# kind -> (draw function, bounding box (xmin, ymin, xmax, ymax) in units)
DRAWINGS = {
    "union": (d_union, (-30, -12, 30, 12)),
    "reducing_union": (d_reducing_union, (-30, -13.8, 30, 13.8)),
    "union_elbow": (d_union_elbow, (-31, -12, 12, 31)),
    "union_tee": (d_union_tee, (-31, -12, 31, 31)),
    "union_cross": (d_union_cross, (-31, -31, 31, 31)),
    "bulkhead_union": (d_bulkhead_union, (-39, -20, 41, 20)),
    "male_connector": (d_male_connector, (-29, -12, 28, 12)),
    "female_connector": (d_female_connector, (-25, -13, 24, 13)),
    "reducer": (d_reducer, (-27, -10.8, 30, 10.8)),
    "port_connector": (d_port_connector, (-8, -11, 40, 11)),
    "reducing_port_connector": (d_reducing_port_connector, (-8, -12, 40, 12)),
    "cap": (d_cap, (-10, -12, 10.5, 12)),
    "plug": (d_plug, (-12, -11, 20, 11)),
    "nut": (d_nut, (-8, -12, 14 + 2 * _hex_r(24), 12)),
    "bulkhead_lock_nut": (d_bulkhead_lock_nut, (-4, -14, 10 + 2 * _hex_r(28), 14)),
    "front_ferrule": (d_front_ferrule, (-12, -9, 10, 9)),
    "back_ferrule": (d_back_ferrule, (-5, -8, 6, 8)),
    "ferrule_set": (d_ferrule_set, (-22, -9, 18, 9)),
}

BT_KINDS_EXTEND = 4  # how far the bored-through line runs past each end


def draw_fitting(c, kind, x, y, w, h, bored_through=False, pad=3):
    """Draw fitting `kind` centred in the box (x, y, w, h) on canvas c.

    bored_through adds a dashed through-line along the axis and a BT badge.
    """
    fn, (bx0, by0, bx1, by1) = DRAWINGS[kind]
    ext = BT_KINDS_EXTEND if bored_through else 0
    bw = (bx1 - bx0) + 2 * ext
    bh = by1 - by0
    scale = min((w - 2 * pad) / bw, (h - 2 * pad) / bh, MAX_SCALE)

    c.saveState()
    c.translate(x + w / 2 - (bx0 + bx1) / 2 * scale,
                y + h / 2 - (by0 + by1) / 2 * scale)
    c.scale(scale, scale)
    c.setLineJoin(1)
    s = Sketch(c, scale)
    fn(s)
    if bored_through:
        s.line(bx0 - ext, 0, bx1 + ext, 0, pt=0.9, color=ACCENT, dash=(2.5, 1.6))
    c.restoreState()

    if bored_through:
        c.saveState()
        bw_pt, bh_pt = 14, 8
        bx, by = x + w - bw_pt - 1.5, y + h - bh_pt - 1.5
        c.setFillColor(ACCENT)
        c.roundRect(bx, by, bw_pt, bh_pt, 2, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(bx + bw_pt / 2, by + 2.3, "BT")
        c.restoreState()
