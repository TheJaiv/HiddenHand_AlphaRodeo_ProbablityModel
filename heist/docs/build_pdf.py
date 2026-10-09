"""Build the pamplona.py study guide.  Usage: python build_pdf.py SRC.py content.txt OUT.pdf"""
import os
import re
import sys

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

SRC, CONTENT, OUT = sys.argv[1:4]
NAME = os.environ.get('GUIDE_NAME', 'professor.py')
FINAL_ROW = os.environ.get('GUIDE_FINAL', 'heist/professor.py = heist/pamplona.py (v14), 1,112 lines')
FOOT = os.environ.get('GUIDE_FOOT', 'heist/pamplona.py = heist/professor.py (final upload)')
NPL = int(os.environ.get('GUIDE_NPLAN', '8'))
SHIFT = int(os.environ.get('GUIDE_SHIFT', '0'))   # code lines from 41 on are this much lower in SRC


def sl(n):
    return n - SHIFT if n >= 41 else n

# ── fonts ────────────────────────────────────────────────────────────────
SUP = '/System/Library/Fonts/Supplemental/'
for name, f in (('Sans', 'Arial.ttf'), ('Sans-Bold', 'Arial Bold.ttf'),
                ('Sans-Italic', 'Arial Italic.ttf'), ('Sans-BoldItalic', 'Arial Bold Italic.ttf')):
    pdfmetrics.registerFont(TTFont(name, SUP + f))
pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='Sans-Bold', italic='Sans-Italic',
                              boldItalic='Sans-BoldItalic')
for i, name in enumerate(('Mono', 'Mono-Bold', 'Mono-Italic', 'Mono-BoldItalic')):
    pdfmetrics.registerFont(TTFont(name, '/System/Library/Fonts/Menlo.ttc', subfontIndex=i))
pdfmetrics.registerFontFamily('Mono', normal='Mono', bold='Mono-Bold', italic='Mono-Italic',
                              boldItalic='Mono-BoldItalic')

# ── look ────────────────────────────────────────────────────────────────
INK, MUTED, ACCENT = '#1f2328', '#57606a', '#0b4f8a'
CODE_BG, CODE_BORDER, LNO = '#f6f8fa', '#d0d7de', '#8c959f'
PAGE_W, PAGE_H = A4
LM = RM = 48
TM, BM = 52, 54
FW = PAGE_W - LM - RM

body = ParagraphStyle('body', fontName='Sans', fontSize=9.8, leading=13.8, textColor=INK, spaceAfter=5)
small = ParagraphStyle('small', parent=body, fontSize=8.4, leading=11, textColor=MUTED, spaceAfter=0)
h1 = ParagraphStyle('h1', fontName='Sans-Bold', fontSize=19, leading=23, textColor=ACCENT, spaceAfter=12)
h2 = ParagraphStyle('h2', fontName='Sans-Bold', fontSize=12.5, leading=16, textColor=ACCENT,
                    spaceBefore=10, spaceAfter=4)
h3 = ParagraphStyle('h3', fontName='Sans-Bold', fontSize=10.5, leading=14, textColor=INK,
                    spaceBefore=6, spaceAfter=3)
ctitle = ParagraphStyle('ctitle', fontName='Sans-Bold', fontSize=10.4, leading=13.5, textColor=INK,
                        spaceBefore=13, spaceAfter=4)
li = ParagraphStyle('li', parent=body, leftIndent=16, bulletIndent=4, spaceAfter=3, bulletFontName='Sans-Bold',
                    bulletColor=ACCENT)
ln = ParagraphStyle('ln', parent=body, fontSize=9.6, leading=13.2, leftIndent=62, bulletIndent=0,
                    bulletFontName='Sans-Bold', bulletFontSize=8.6, bulletColor=ACCENT, spaceAfter=2.6)
callout_st = ParagraphStyle('callout', parent=body, fontSize=9.5, leading=13.2, spaceAfter=0)
th = ParagraphStyle('th', fontName='Sans-Bold', fontSize=8.6, leading=11, textColor=INK)
td = ParagraphStyle('td', fontName='Sans', fontSize=8.6, leading=11, textColor=INK)
qst = ParagraphStyle('q', fontName='Sans-Bold', fontSize=9.9, leading=13.5, textColor=ACCENT,
                     spaceBefore=8, spaceAfter=2)
ast = ParagraphStyle('a', parent=body, leftIndent=14)

fn_head = ParagraphStyle('fnh', fontName='Mono-Bold', fontSize=8.8, leading=11.5, textColor='#0b3d66')
fn_lab = ParagraphStyle('fnl', fontName='Sans-Bold', fontSize=7.6, leading=11.6, textColor='#2f5f8a')
fn_txt = ParagraphStyle('fnt', fontName='Sans', fontSize=9.3, leading=12.6, textColor=INK)

CODE_FS, CODE_LEAD = 7.35, 9.15
codep = ParagraphStyle('code', fontName='Mono', fontSize=CODE_FS, leading=CODE_LEAD, textColor=INK)
lnop = ParagraphStyle('lno', fontName='Mono', fontSize=CODE_FS - 0.7, leading=CODE_LEAD, textColor=LNO,
                      alignment=TA_RIGHT)
NUMW = 25
WRAP = int((FW - NUMW - 12) / pdfmetrics.stringWidth('M', 'Mono', CODE_FS))


# ── inline markup ───────────────────────────────────────────────────────────
def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def inline(s):
    s = esc(s)
    s = re.sub(r'`([^`]+)`', lambda m: '<font face="Mono" size="8.4" color="#8a3b00">%s</font>' % m.group(1), s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\^\{([^}]*)\}', r'<super>\1</super>', s)
    return s


# ── source and highlighting ─────────────────────────────────────────────────
SRC_LINES = open(SRC).read().split('\n')
if SRC_LINES and SRC_LINES[-1] == '':
    SRC_LINES.pop()
ISDOC = {}
state = False
for n, line in enumerate(SRC_LINES, 1):
    k = line.count('"""')
    ISDOC[n] = state or k > 0
    if k % 2 == 1:
        state = not state
CONSTS = set()
for line in SRC_LINES:
    m = re.match(r'^([A-Z][A-Z0-9_]*(?:\s*,\s*[A-Z][A-Z0-9_]*)*)\s*=', line)
    if m:
        CONSTS.update(x.strip() for x in m.group(1).split(','))
KWS = set('def class return if elif else for in while not and or is None True False try except '
          'continue break import lambda pass from as with yield global'.split())
BUILTINS = set('min max sum len range abs any all round float int zip id enumerate reversed sorted set '
               'list tuple dict isinstance getattr staticmethod Exception'.split())
TOKRE = re.compile(r'''("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(\d+\.\d*(?:e-?\d+)?|\.\d+|\d+(?:e-?\d+)?)'''
                   r'''|([A-Za-z_]\w*)|(\s+)|(.)''')
STY = {'kw': ('#cf222e', True, False), 'str': ('#0a3069', False, False), 'num': ('#0550ae', False, False),
       'com': ('#6e7781', False, True), 'doc': ('#3b6e3b', False, True), 'def': ('#8250df', True, False),
       'bi': ('#0550ae', False, False), 'const': ('#953800', False, False), 'self': ('#6639ba', False, False),
       'deco': ('#8250df', False, False), 'plain': (None, False, False)}


def split_comment(line):
    q, i = None, 0
    while i < len(line):
        ch = line[i]
        if q:
            if ch == '\\':
                i += 1
            elif ch == q:
                q = None
        elif ch in '"\'':
            q = ch
        elif ch == '#':
            return line[:i], line[i:]
        i += 1
    return line, ''


def highlight(n):
    line = SRC_LINES[n - 1]
    if ISDOC[n]:
        ind = len(line) - len(line.lstrip(' '))
        return [('plain', line[:ind]), ('doc', line[ind:])]
    code, com = split_comment(line)
    segs = []
    want_def = False
    stripped = code.lstrip(' ')
    if stripped.startswith('@'):
        ind = len(code) - len(stripped)
        return [('plain', code[:ind]), ('deco', stripped)] + ([('com', com)] if com else [])
    for m in TOKRE.finditer(code):
        s, num, ident, ws, other = m.groups()
        if s:
            segs.append(('str', s))
        elif num:
            segs.append(('num', num))
        elif ident:
            if want_def:
                st = 'def'
                want_def = False
            elif ident in ('def', 'class'):
                st, want_def = 'kw', True
            elif ident in KWS:
                st = 'kw'
            elif ident in BUILTINS:
                st = 'bi'
            elif ident in CONSTS:
                st = 'const'
            elif ident == 'self':
                st = 'self'
            else:
                st = 'plain'
            segs.append((st, ident))
        elif ws:
            segs.append(('plain', ws))
        else:
            segs.append(('plain', other))
    if com:
        segs.append(('com', com))
    return segs


def wrap_segs(segs, width):
    text = ''.join(t for _, t in segs)
    if len(text) <= width:
        return [segs]
    styles = [st for st, t in segs for _ in t]
    indent = len(text) - len(text.lstrip(' '))
    rows, start, first = [], 0, True
    while start < len(text):
        lead = 0 if first else indent + 4
        avail = width - lead
        if len(text) - start <= avail:
            end = len(text)
        else:
            cut = text.rfind(' ', start + 1, start + avail)
            end = cut if cut > start + avail // 2 else start + avail
        row = [('plain', ' ' * lead)] if lead else []
        for i in range(start, end):
            st = styles[i]
            if row and row[-1][0] == st:
                row[-1] = (st, row[-1][1] + text[i])
            else:
                row.append((st, text[i]))
        rows.append(row)
        start = end
        if start < len(text) and text[start] == ' ':
            start += 1
        first = False
    return rows


def render(segs):
    out = []
    for st, t in segs:
        if not t:
            continue
        col, b, it = STY[st]
        x = esc(t).replace(' ', '&nbsp;')
        if b:
            x = '<b>%s</b>' % x
        if it:
            x = '<i>%s</i>' % x
        if col:
            x = '<font color="%s">%s</font>' % (col, x)
        out.append(x)
    return ''.join(out) or '&nbsp;'


COVERED = set()


def code_block(a, b):
    rows = []
    for n in range(a, b + 1):
        COVERED.add(n)
        for k, part in enumerate(wrap_segs(highlight(n), WRAP)):
            rows.append([Paragraph(str(n) if k == 0 else '', lnop), Paragraph(render(part), codep)])
    t = Table(rows, colWidths=[NUMW, FW - NUMW], hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('BOX', (0, 0), (-1, -1), 0.6, CODE_BORDER),
        ('LINEAFTER', (0, 0), (0, -1), 0.5, CODE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (0, -1), 1), ('RIGHTPADDING', (0, 0), (0, -1), 4),
        ('LEFTPADDING', (1, 0), (1, -1), 6), ('RIGHTPADDING', (1, 0), (1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 3.5), ('BOTTOMPADDING', (0, -1), (-1, -1), 3.5),
    ]))
    return t


# ── building blocks ───────────────────────────────────────────────────────────
def callout(kind, text):
    lab, bg, bar = {'say': ('SAY IT LIKE THIS', '#e9f5ec', '#2e7d32'),
                    'why': ('WHY / EVIDENCE', '#fff6e0', '#b06a00')}[kind]
    p = Paragraph('<font size="7.3" color="%s"><b>%s</b></font><br/>%s' % (bar, lab, inline(text)), callout_st)
    t = Table([[p]], colWidths=[FW], hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), bg), ('LINEBEFORE', (0, 0), (0, -1), 3, bar),
                           ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                           ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
    return [Spacer(1, 4), t, Spacer(1, 5)]


def fn_card(sig, rows):
    data = [[Paragraph('<font name="Sans-Bold" size="7" color="#4a6b8a">FUNCTION CARD</font>&nbsp;&nbsp;&nbsp;' + esc(sig), fn_head), '']]
    for k, v in rows:
        data.append([Paragraph(esc(k).upper(), fn_lab), Paragraph(inline(v), fn_txt)])
    t = Table(data, colWidths=[92, FW - 92], hAlign='LEFT')
    t.setStyle(TableStyle([('SPAN', (0, 0), (-1, 0)), ('BACKGROUND', (0, 0), (-1, -1), '#eef4fa'),
                           ('BACKGROUND', (0, 0), (-1, 0), '#dfeaf5'), ('LINEBEFORE', (0, 0), (0, -1), 3, '#2f6fa6'),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 8),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 3.2),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 3.6), ('TOPPADDING', (0, 0), (-1, 0), 5),
                           ('BOTTOMPADDING', (0, 0), (-1, 0), 5)]))
    return [Spacer(1, 2), KeepTogether([t]), Spacer(1, 6)]


def notes_box(n):
    rows = [[Paragraph('<font color="%s"><b>Your notes</b></font>' % MUTED, small)]] + [['']] * n
    t = Table(rows, colWidths=[FW], rowHeights=[17] + [19.5] * n, hAlign='LEFT')
    st = [('BOX', (0, 0), (-1, -1), 0.7, '#c9d1d9'), ('BACKGROUND', (0, 0), (-1, -1), '#fdfdfe'),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 8)]
    for i in range(1, n):
        st.append(('LINEBELOW', (0, i), (-1, i), 0.4, '#d8dee4'))
    t.setStyle(TableStyle(st))
    return [Spacer(1, 10), KeepTogether([t])]


def make_table(rows, cols):
    n = len(rows[0])
    widths = [FW * c / 100.0 for c in cols] if cols and len(cols) == n else [FW / n] * n
    data = [[Paragraph(inline(c), th if i == 0 else td) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    st = [('BACKGROUND', (0, 0), (-1, 0), '#e8eef5'), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
          ('TOPPADDING', (0, 0), (-1, -1), 2.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.2),
          ('LINEBELOW', (0, 0), (-1, -1), 0.4, '#d8dee4'), ('BOX', (0, 0), (-1, -1), 0.6, '#c9d1d9')]
    t.setStyle(TableStyle(st))
    return [Spacer(1, 3), t, Spacer(1, 7)]


def flow_diagram():
    W, H = FW, 270
    d = Drawing(W, H)

    def box(x, y, w, h, title, lines, fill):
        d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=fill, strokeColor='#9aa7b4', strokeWidth=0.8))
        d.add(String(x + 8, y + h - 14, title, fontName='Sans-Bold', fontSize=8.7, fillColor=INK))
        for i, t in enumerate(lines):
            d.add(String(x + 8, y + h - 26.5 - i * 10.6, t, fontName='Sans', fontSize=7.7, fillColor='#3d4650'))

    def arrow(x, y1, y2):
        d.add(Line(x, y1, x, y2 + 5, strokeColor=ACCENT, strokeWidth=1.1))
        d.add(Polygon([x, y2, x - 3.6, y2 + 6.5, x + 3.6, y2 + 6.5], fillColor=ACCENT, strokeColor=ACCENT))

    y = H - 26
    box(0, y, W, 24, 'The engine calls quote(obs), respond(obs, price) or move(obs)', [], '#eef3f9')
    arrow(W / 2, y, y - 14)
    y -= 14 + 52
    box(0, y, W, 52, '_sync (line %d): learn from everything new' % sl(635), [
        'their quote  →  Kalman update of every hypothesis (_see, line %d)' % sl(565),
        'their answer to my quote  →  truncated-normal update (_see, line %d)' % sl(588),
        'their swap  →  belief shifts and widens (_see_swap); reweight; prune (line %d)' % sl(461)], '#f6f8fa')
    arrow(W / 2, y, y - 14)
    y -= 14 + 45
    box(0, y, W, 45, '_ev + _plan_setup: value and the %d likeliest hypotheses' % NPL, [
        'E[V | O] = α + β·O  (line %d)' % sl(666),
        'top %d hypotheses, the quotes of mine they read, the slots left (line %d)' % (NPL, sl(840))], '#f6f8fa')
    gap = 10
    bw = (W - 2 * gap) / 3
    xs = [0, bw + gap, 2 * (bw + gap)]
    for x in xs:
        arrow(x + bw / 2, y, y - 14)
    y -= 14 + 56
    box(xs[0], y, bw, 56, 'quote  →  _quote (%d)' % sl(907), [
        'stage 1: best profit now', 'stage 2: + play-out (_roll), util', '70% plan + 30% safe quote'], '#e9f5ec')
    box(xs[1], y, bw, 56, 'respond  →  _respond (%d)' % sl(1039), [
        'buy / pass / sell', 'profit now + play-out', 'best utility wins'], '#e9f5ec')
    box(xs[2], y, bw, 56, 'move  →  _move (%d)' % sl(1071), [
        'never peek', 'round 5 only: swap lowest / highest', 'card if the gain is over 4'], '#e9f5ec')
    for x in xs:
        arrow(x + bw / 2, y, y - 14)
    y -= 14 + 33
    box(0, y, W, 33, 'Wrappers (lines %d-%d), then the answer goes back to the engine' % (sl(874), sl(905)), [
        'the exact house-bot attack may override (never on against real teams); try/except fallbacks'],
        '#fff6e0')
    return [Spacer(1, 2), d, Spacer(1, 6)]


# ── document ──────────────────────────────────────────────────────────────
class Doc(BaseDocTemplate):
    def __init__(self, fn):
        super().__init__(fn, pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                         title=NAME + ', line by line', author='Alpha Rodeo',
                         subject='Study guide for the Alpha Rodeo Hidden Hand bot')
        frame = Frame(LM, BM, FW, PAGE_H - TM - BM, id='f', leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.chapter = ''
        self.addPageTemplates([PageTemplate('cover', [frame]),
                               PageTemplate('main', [frame], onPageEnd=self.decorate)])

    def beforeDocument(self):
        self.chapter = ''

    def decorate(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor('#d0d7de')
        canv.setLineWidth(0.5)
        canv.line(LM, PAGE_H - TM + 14, PAGE_W - RM, PAGE_H - TM + 14)
        canv.setFont('Sans', 7.6)
        canv.setFillColor(MUTED)
        canv.drawString(LM, PAGE_H - TM + 19, 'Alpha Rodeo  ·  ' + NAME + ', line by line')
        canv.drawRightString(PAGE_W - RM, PAGE_H - TM + 19, self.chapter)
        canv.line(LM, BM - 16, PAGE_W - RM, BM - 16)
        canv.drawRightString(PAGE_W - RM, BM - 27, 'page %d' % doc.page)
        canv.drawString(LM, BM - 27, FOOT)
        canv.restoreState()

    def afterFlowable(self, f):
        toc = getattr(f, '_toc', None)
        if not toc:
            return
        level, text, key, outline = toc
        if level == 0:
            self.chapter = outline
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(outline, key, level=level, closed=level == 0)
        self.notify('TOCEntry', (level, text, self.page, key))


KEYS = [0]


def tagged(par, level, text, outline):
    KEYS[0] += 1
    par._toc = (level, text, 'k%d' % KEYS[0], outline)
    return par


def cover():
    out = [Spacer(1, 120)]
    out.append(Paragraph(NAME + ', line by line', ParagraphStyle(
        'ct', fontName='Sans-Bold', fontSize=30, leading=36, textColor=ACCENT)))
    out.append(Spacer(1, 10))
    out.append(Paragraph('How the Alpha Rodeo Hidden Hand bot works: a study guide to read, annotate and explain',
                         ParagraphStyle('cs', fontName='Sans', fontSize=13.5, leading=18, textColor=INK)))
    out.append(Spacer(1, 26))
    rows = [['Team', 'Alpha Rodeo'], ['Member', 'Jaiv Patel (26075057)'], ['Mentor', 'Arpit Gupta'],
            ['Final upload', FINAL_ROW],
            ['Event', 'Hidden Hand, The Quant Club, IIT BHU'], ['Prepared', 'Thursday 8 October 2026']]
    t = Table([[Paragraph('<b>%s</b>' % a, td), Paragraph(b, td)] for a, b in rows], colWidths=[90, FW - 90],
              hAlign='LEFT')
    t.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.4, '#d8dee4'), ('TOPPADDING', (0, 0), (-1, -1), 4),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 5), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    out.append(t)
    out.append(Spacer(1, 30))
    key = ('Code colours: <font color="#cf222e"><b>keywords</b></font>, <font color="#953800">CONSTANTS</font>, '
           '<font color="#8250df"><b>function names</b></font>, <font color="#0550ae">numbers</font>, '
           '<font color="#0a3069">"strings"</font>, <font color="#6e7781"><i># comments</i></font>, '
           '<font color="#3b6e3b"><i>docstrings</i></font>. Grey numbers on the left are the line numbers of '
           'heist/' + NAME + '.')
    out.append(Paragraph(key, small))
    out += [NextPageTemplate('main'), PageBreak()]
    return out


def build():
    text = open(CONTENT).read()
    story = []
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle('toc0', fontName='Sans-Bold', fontSize=10.2, leading=14, leftIndent=0, firstLineIndent=0,
                       textColor=INK, spaceBefore=5),
        ParagraphStyle('toc1', fontName='Sans', fontSize=8.5, leading=10.8, leftIndent=16, firstLineIndent=0,
                       textColor='#3d4650'),
    ]
    toc.dotsMinLevel = 0
    pending = None          # (kind, label, text)
    held = []               # code table waiting for its function cards
    card = None             # function card being read
    para = []
    table_rows = []
    cols = None
    in_chapter = False

    def flush():
        nonlocal pending, para, table_rows, cols
        if para:
            story.append(Paragraph(inline(' '.join(para)), body))
            para = []
        if pending:
            kind, label, t = pending
            if kind == 'li':
                story.append(Paragraph(inline(t), li, bulletText=label or '•'))
            elif kind == 'ln':
                story.append(Paragraph(inline(t), ln, bulletText=label))
            elif kind in ('say', 'why'):
                story.extend(callout(kind, t))
            elif kind == 'q':
                story.append(('Q', t))
            elif kind == 'a':
                q = story.pop() if story and isinstance(story[-1], tuple) else None
                items = ([Paragraph(inline('Q.  ' + q[1]), qst)] if q else []) + [Paragraph(inline(t), ast)]
                story.append(KeepTogether(items))
            pending = None
        if table_rows:
            story.extend(make_table(table_rows, cols))
            table_rows, cols = [], None

    def release():
        if held:
            story.extend(held)
            del held[:]

    for raw in text.split('\n'):
        line = raw.rstrip()
        if card is not None:
            if line.strip() == '%end':
                story.extend(fn_card(card[0], card[1]))
                card = None
            elif line.startswith('  ') and card[1]:
                card[1][-1] = (card[1][-1][0], card[1][-1][1] + ' ' + line.strip())
            elif ':' in line:
                k, v = line.split(':', 1)
                card[1].append((k.strip(), v.strip()))
            continue
        if line.startswith('%fn '):
            flush()
            card = (line[4:].strip(), [])
            continue
        if not line.strip():
            flush()
            continue
        release()
        if line.startswith('  ') and pending is not None:
            pending = (pending[0], pending[1], pending[2] + ' ' + line.strip())
            continue
        if line.startswith('|'):
            if para or pending:
                keep_cols = cols
                flush()
                cols = keep_cols
            table_rows.append([c.strip() for c in line.strip().strip('|').split('|')])
            continue
        if table_rows:
            keep = None
            flush()
        m = re.match(r'^%(\w+)\s*(.*)$', line)
        if m:
            flush()
            cmd, arg = m.groups()
            if cmd == 'cover':
                story.extend(cover())
            elif cmd == 'toc':
                story.append(Paragraph('Contents', h1))
                story.append(Paragraph('Chapters, then every code block of the walkthrough by its line numbers.',
                                       small))
                story.append(Spacer(1, 6))
                story.append(toc)
            elif cmd == 'notes':
                story.extend(notes_box(int(arg)))
            elif cmd == 'cols':
                cols = [float(x) for x in arg.split(',')]
            elif cmd == 'diagram':
                story.extend(flow_diagram())
            elif cmd == 'pagebreak':
                story.append(PageBreak())
            continue
        if line.startswith('# '):
            flush()
            title = line[2:].strip()
            story.append(PageBreak())
            story.append(tagged(Paragraph(inline(title), h1), 0, esc(title), title))
            in_chapter = True
            continue
        if line.startswith('## '):
            flush()
            title = line[3:].strip()
            story.append(CondPageBreak(60))
            story.append(tagged(Paragraph(inline(title), h2), 1, esc(title), title))
            continue
        if line.startswith('### '):
            flush()
            story.append(Paragraph(inline(line[4:].strip()), h3))
            continue
        m = re.match(r'^@code\s+(\d+)-(\d+)\s*(.*)$', line)
        if m:
            flush()
            a, b, title = int(m.group(1)), int(m.group(2)), m.group(3).strip()
            rng = '%d–%d' % (a, b) if b != a else '%d' % a
            head = Paragraph('<font color="%s">Lines %s</font>  ·  %s' % (ACCENT, rng, inline(title)), ctitle)
            story.append(CondPageBreak(110))
            story.append(tagged(head, 1, '<font name="Mono" size="7.8" color="%s">%s</font>   %s'
                                % (ACCENT, rng, esc(title)), 'L%s  %s' % (rng, title)))
            held.extend([code_block(a, b), Spacer(1, 6)])
            continue
        m = re.match(r'^L(\d+)(?:-(\d+))?:\s*(.*)$', line)
        if m:
            flush()
            lab = 'L%s' % m.group(1) + ('–%s' % m.group(2) if m.group(2) else '')
            pending = ('ln', lab, m.group(3))
            continue
        if line.startswith('- '):
            flush()
            t = line[2:].strip()
            mm = re.match(r'^\*\*(\d+\.)\*\*\s*(.*)$', t)
            pending = ('li', mm.group(1), mm.group(2)) if mm else ('li', None, t)
            continue
        if line.startswith('> '):
            flush()
            pending = ('say', None, line[2:].strip())
            continue
        if line.startswith('! '):
            flush()
            pending = ('why', None, line[2:].strip())
            continue
        if line.startswith('? '):
            flush()
            pending = ('q', None, line[2:].strip())
            continue
        if line.startswith('= '):
            if pending and pending[0] == 'q':
                story.append(('Q', pending[2]))
                pending = None
            flush()
            pending = ('a', None, line[2:].strip())
            continue
        if pending:
            flush()
        para.append(line.strip())
    flush()
    release()
    story = [s for s in story if not isinstance(s, tuple)]
    doc = Doc(OUT)
    doc.multiBuild(story)
    return doc


if __name__ == '__main__':
    content = open(CONTENT).read()
    face = pdfmetrics.getFont('Sans').face
    miss = sorted({ch for ch in content if ord(ch) > 127 and ord(ch) not in face.charToGlyph})
    print('missing in Arial:', miss)
    mface = pdfmetrics.getFont('Mono').face
    miss = sorted({ch for ch in open(SRC).read() if ord(ch) > 127 and ord(ch) not in mface.charToGlyph})
    print('missing in Menlo:', miss)
    doc = build()
    unc = [n for n, l in enumerate(SRC_LINES, 1) if n not in COVERED and l.strip()]
    print('non-blank source lines not shown:', unc)
    print('pages:', doc.page, 'wrap width', WRAP)
