"""Minimal SVG stand-in for the reportlab canvas calls fitting_drawings uses.

Lets the same drawing code that makes the PDFs produce inline SVG for the
local inventory app: draw_fitting(SvgCanvas(w, h), kind, 0, 0, w, h, bt).
"""


def _num(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _color(c):
    if c is None:
        return "none"
    if isinstance(c, str):
        return c
    return "#" + c.hexval()[2:].lower()


class _Path:
    def __init__(self):
        self.d = []

    def moveTo(self, x, y):
        self.d.append(f"M{_num(x)} {_num(y)}")

    def lineTo(self, x, y):
        self.d.append(f"L{_num(x)} {_num(y)}")

    def curveTo(self, x1, y1, x2, y2, x3, y3):
        self.d.append("C" + " ".join(_num(v) for v in (x1, y1, x2, y2, x3, y3)))

    def close(self):
        self.d.append("Z")


class SvgCanvas:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.out = []
        self._levels = [0]
        self._stack = []
        self.st = {"lw": 1.0, "stroke": "#000000", "fill": "#000000",
                   "dash": None, "join": 0, "font": ("Helvetica", 10)}

    # state and transforms ------------------------------------------------
    def saveState(self):
        self._stack.append(dict(self.st))
        self._levels.append(0)

    def restoreState(self):
        self.out.append("</g>" * self._levels.pop())
        self.st = self._stack.pop()

    def _group(self, transform):
        self.out.append(f'<g transform="{transform}">')
        self._levels[-1] += 1

    def translate(self, dx, dy):
        self._group(f"translate({_num(dx)} {_num(dy)})")

    def scale(self, sx, sy):
        self._group(f"scale({_num(sx)} {_num(sy)})")

    def rotate(self, deg):
        self._group(f"rotate({_num(deg)})")

    # styles --------------------------------------------------------------
    def setLineWidth(self, w):
        self.st["lw"] = w

    def setStrokeColor(self, c):
        self.st["stroke"] = _color(c)

    def setFillColor(self, c):
        self.st["fill"] = _color(c)

    def setDash(self, array=None, phase=0):
        self.st["dash"] = list(array) if array else None

    def setLineJoin(self, j):
        self.st["join"] = j

    def setFont(self, name, size):
        self.st["font"] = (name, size)

    def _stroke_attrs(self):
        a = (f'stroke="{self.st["stroke"]}" stroke-width="{_num(self.st["lw"])}"'
             f' stroke-linejoin="{["miter", "round", "bevel"][self.st["join"]]}"')
        if self.st["dash"]:
            a += ' stroke-dasharray="' + " ".join(_num(d) for d in self.st["dash"]) + '"'
        return a

    def _paint(self, stroke, fill):
        f = self.st["fill"] if fill else "none"
        s = self._stroke_attrs() if stroke else 'stroke="none"'
        return f'fill="{f}" {s}'

    # drawing -------------------------------------------------------------
    def beginPath(self):
        return _Path()

    def drawPath(self, p, stroke=1, fill=0):
        self.out.append(f'<path d="{" ".join(p.d)}" {self._paint(stroke, fill)}/>')

    def line(self, x1, y1, x2, y2):
        self.out.append(f'<line x1="{_num(x1)}" y1="{_num(y1)}" x2="{_num(x2)}" '
                        f'y2="{_num(y2)}" fill="none" {self._stroke_attrs()}/>')

    def circle(self, x, y, r, stroke=1, fill=0):
        self.out.append(f'<circle cx="{_num(x)}" cy="{_num(y)}" r="{_num(r)}" '
                        f'{self._paint(stroke, fill)}/>')

    def roundRect(self, x, y, w, h, r, stroke=1, fill=0):
        self.out.append(f'<rect x="{_num(x)}" y="{_num(y)}" width="{_num(w)}" height="{_num(h)}" '
                        f'rx="{_num(r)}" {self._paint(stroke, fill)}/>')

    def drawCentredString(self, x, y, text):
        name, size = self.st["font"]
        weight = "700" if "Bold" in name else "400"
        self.out.append(
            f'<text transform="translate({_num(x)} {_num(y)}) scale(1 -1)" text-anchor="middle" '
            f'font-family="Helvetica, Arial, sans-serif" font-size="{_num(size)}" '
            f'font-weight="{weight}" fill="{self.st["fill"]}">{text}</text>')

    # output --------------------------------------------------------------
    def svg(self):
        body = "".join(self.out)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_num(self.width)} '
                f'{_num(self.height)}" aria-hidden="true">'
                f'<g transform="translate(0 {_num(self.height)}) scale(1 -1)">{body}</g></svg>')
