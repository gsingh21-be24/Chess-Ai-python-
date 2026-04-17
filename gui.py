"""
Chess AI  –  Professional GUI
chess.com-quality board · premium dark theme · captured pieces · smooth design
"""

import pygame
import pygame.gfxdraw
import chess
import time
import threading
import sys
import math

from engine import get_best_move, analyze_game

# ══════════════════════════════════════════════════════════════════════════════
#  LAYOUT  (1040 × 720 window)
# ══════════════════════════════════════════════════════════════════════════════
SQ        = 76            # board square
BOARD_PX  = SQ * 8       # 608
BX        = 36            # board left
BY        = 56            # board top  (room for captured pieces above)
PANEL_X   = BX + BOARD_PX + 24
PANEL_W   = 288
WIN_W     = PANEL_X + PANEL_W + 16
WIN_H     = BY + BOARD_PX + 56   # room below for captured pieces

# ── Exact chess.com board colours ─────────────────────────────────────────────
C_LIGHT   = (240, 217, 181)
C_DARK    = (181, 136,  99)
C_LAST_L  = (205, 209, 105)
C_LAST_D  = (170, 161,  57)
C_SEL_L   = (245, 245, 104)
C_SEL_D   = (185, 201,  66)
C_CHECK   = (200,  30,  30)

# ── UI palette ────────────────────────────────────────────────────────────────
C_BG      = ( 21,  21,  21)   # near-black background
C_SURFACE = ( 30,  30,  30)   # card surfaces
C_PANEL   = ( 26,  26,  26)   # panel bg
C_BORDER  = ( 48,  48,  48)   # subtle borders
C_TEXT    = (235, 235, 235)
C_DIM     = (150, 150, 150)
C_FAINT   = ( 90,  90,  90)
C_GREEN   = (129, 183,  86)   # chess.com green
C_GREEN_D = ( 93, 145,  60)
C_RED     = (180,  45,  45)
C_RED_D   = (140,  30,  30)
C_GOLD    = (212, 175,  55)
C_BLUE    = ( 72, 130, 200)

# ── Piece palette ─────────────────────────────────────────────────────────────
WF = (252, 252, 252)
WK = ( 26,  26,  26)
WS = (190, 190, 190)
BF = ( 38,  38,  38)
BK = (  6,   6,   6)
BS = ( 85,  85,  85)

SCALE = 4   # 4× supersampling for ultra-smooth pieces


# ══════════════════════════════════════════════════════════════════════════════
#  FONT HELPER
# ══════════════════════════════════════════════════════════════════════════════
def _font(size, bold=False):
    priority = ['segoeui','calibri','trebuchetms','verdana','tahoma','arial']
    if bold:
        priority = ['segoeuisemibold','calibri','verdana','arial']
    av = set(pygame.font.get_fonts())
    for name in priority:
        if name in av:
            return pygame.font.SysFont(name, size, bold=bold)
    return pygame.font.SysFont('arial', size, bold=bold)


# ══════════════════════════════════════════════════════════════════════════════
#  AA DRAWING PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════
def _aa_fill_circle(surf, col, cx, cy, r):
    if r < 1: return
    pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), int(r), col)
    pygame.gfxdraw.aacircle(surf, int(cx), int(cy), int(r), col)

def _aa_fill_ellipse(surf, col, cx, cy, rx, ry):
    if rx < 1 or ry < 1: return
    pygame.gfxdraw.filled_ellipse(surf, int(cx), int(cy), max(1,int(rx)), max(1,int(ry)), col)
    pygame.gfxdraw.aaellipse(surf, int(cx), int(cy), max(1,int(rx)), max(1,int(ry)), col)

def _aa_fill_poly(surf, col, pts):
    ip = [(int(x), int(y)) for x, y in pts]
    if len(ip) < 3: return
    pygame.gfxdraw.filled_polygon(surf, ip, col)
    pygame.gfxdraw.aapolygon(surf, ip, col)

def _rr(surf, col, rect, r=8, bw=0, bc=None):
    pygame.draw.rect(surf, col, rect, border_radius=int(r))
    if bw and bc:
        pygame.draw.rect(surf, bc, rect, bw, border_radius=int(r))

def _ctext(surf, font, text, col, rect):
    t = font.render(text, True, col)
    surf.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))


# ══════════════════════════════════════════════════════════════════════════════
#  SUPERSAMPLED PIECE RENDERER
# ══════════════════════════════════════════════════════════════════════════════
def _render_piece(piece_type, is_white, sq_size):
    S  = sq_size * SCALE
    hi = pygame.Surface((S, S), pygame.SRCALPHA)
    cx = cy = S // 2
    s  = S / 2.0

    fill  = WF if is_white else BF
    key   = WK if is_white else BK
    shade = WS if is_white else BS

    def P(rx, ry): return (cx + s*rx, cy + s*ry)
    def CI(rx,ry,rr,c=None,w=0):
        c=c or fill
        if w==0: _aa_fill_circle(hi,c,cx+s*rx,cy+s*ry,max(1,s*rr))
        else:
            for d in range(w): pygame.gfxdraw.aacircle(hi,int(cx+s*rx),int(cy+s*ry),max(1,int(s*rr)-d),c)
    def PO(pts,c=None,w=0):
        c=c or fill
        if w==0: _aa_fill_poly(hi,c,[P(x,y) for x,y in pts])
        else: pygame.gfxdraw.aapolygon(hi,[(int(cx+s*x),int(cy+s*y)) for x,y in pts],c)
    def EL(rx,ry,ex,ey,c=None):
        c=c or fill; _aa_fill_ellipse(hi,c,cx+s*rx,cy+s*ry,max(1,s*ex),max(1,s*ey))
    def RR(rx,ry,rw,rh,c=None,bw=0,bc=None,rad=5):
        c=c or fill
        x,y,w,h=int(cx+s*rx-s*rw/2),int(cy+s*ry-s*rh/2),max(1,int(s*rw)),max(1,int(s*rh))
        pygame.draw.rect(hi,c,(x,y,w,h),bw,border_radius=rad)

    # Drop shadow
    sh = pygame.Surface((S,S),pygame.SRCALPHA)
    _aa_fill_ellipse(sh,(0,0,0,50),cx,cy+s*0.80,s*0.54,s*0.09)
    hi.blit(sh,(0,0))

    # Base ring
    EL(0, 0.65, 0.48, 0.11, shade)
    EL(0, 0.63, 0.44, 0.09)
    PO([ (-0.44,0.63),(0.44,0.63),(0.44,0.72),(-0.44,0.72) ])

    if piece_type == chess.PAWN:
        PO([(-0.15,0.63),(0.15,0.63),(0.11,0.06),(-0.11,0.06)])
        PO([(-0.15,0.63),(0.15,0.63),(0.11,0.06),(-0.11,0.06)], key, 2)
        EL(0,0.09,0.18,0.06,shade); EL(0,0.07,0.16,0.055)
        CI(0,-0.24,0.32,shade); CI(0,-0.27,0.29); CI(0,-0.27,0.29,key,2)
        CI(-0.09,-0.36,0.09,(*shade[:3],190))

    elif piece_type == chess.ROOK:
        PO([(-0.34,0.63),(0.34,0.63),(0.28,-0.16),(0.26,-0.38),(-0.26,-0.38),(-0.28,-0.16)])
        PO([(-0.34,0.63),(0.34,0.63),(0.28,-0.16),(0.26,-0.38),(-0.26,-0.38),(-0.28,-0.16)], key, 2)
        RR(0,-0.38,0.72,0.10,shade,rad=4); RR(0,-0.38,0.72,0.10,key,2,rad=4)
        for dx in (-0.24,0,0.24):
            bx2=int(cx+s*dx-s*0.10); by2=int(cy-s*0.70)
            bw2=max(1,int(s*0.20)); bh2=max(1,int(s*0.34))
            pygame.draw.rect(hi,fill,(bx2,by2,bw2,bh2),border_radius=4)
            pygame.draw.rect(hi,key, (bx2,by2,bw2,bh2),2,border_radius=4)
        RR(0, 0.12,0.26,0.36,shade,rad=3)
        RR(0,-0.08,0.60,0.08,shade,rad=3); RR(0,-0.08,0.60,0.08,key,1,rad=3)

    elif piece_type == chess.KNIGHT:
        PO([(-0.30,0.63),(0.34,0.63),(0.30,0.16),(0.12,-0.16),(-0.08,-0.46),(-0.28,-0.36),(-0.30,0.16)])
        PO([(-0.30,0.63),(0.34,0.63),(0.30,0.16),(0.12,-0.16),(-0.08,-0.46),(-0.28,-0.36),(-0.30,0.16)], key, 2)
        PO([(-0.28,-0.36),(-0.08,-0.46),(0.14,-0.62),(0.26,-0.42),(0.10,-0.14),(-0.14,-0.20)])
        PO([(-0.28,-0.36),(-0.08,-0.46),(0.14,-0.62),(0.26,-0.42),(0.10,-0.14),(-0.14,-0.20)], key, 2)
        PO([(0.04,-0.58),(0.16,-0.76),(0.28,-0.60),(0.16,-0.48)])
        PO([(0.04,-0.58),(0.16,-0.76),(0.28,-0.60),(0.16,-0.48)], key, 2)
        CI(0.11,-0.44,0.08,key); CI(0.10,-0.45,0.05,shade)
        CI(0.22,-0.31,0.05,shade)
        PO([(-0.24,-0.28),(-0.10,-0.44),(-0.02,-0.36),(-0.16,-0.20)], shade)
        CI(-0.10,0.04,0.09,(*shade[:3],150))

    elif piece_type == chess.BISHOP:
        PO([(-0.30,0.63),(0.30,0.63),(0.18,0.10),(0.12,-0.12),(-0.12,-0.12),(-0.18,0.10)])
        PO([(-0.30,0.63),(0.30,0.63),(0.18,0.10),(0.12,-0.12),(-0.12,-0.12),(-0.18,0.10)], key, 2)
        EL(0,-0.12,0.22,0.07,shade); EL(0,-0.14,0.19,0.06)
        RR(0, 0.08,0.52,0.08,shade,rad=3); RR(0,0.08,0.52,0.08,key,1,rad=3)
        CI(0,-0.32,0.26,shade); CI(0,-0.35,0.23); CI(0,-0.35,0.23,key,2)
        PO([(-0.06,-0.54),(0.06,-0.54),(0.02,-0.82),(-0.02,-0.82)])
        PO([(-0.06,-0.54),(0.06,-0.54),(0.02,-0.82),(-0.02,-0.82)], key, 2)
        CI(0,-0.54,0.07,key); CI(0,-0.54,0.04,shade)
        CI(-0.08,-0.43,0.08,(*shade[:3],185))

    elif piece_type == chess.QUEEN:
        PO([(-0.42,0.63),(0.42,0.63),(0.30,0.06),(0.24,-0.20),(-0.24,-0.20),(-0.30,0.06)])
        PO([(-0.42,0.63),(0.42,0.63),(0.30,0.06),(0.24,-0.20),(-0.24,-0.20),(-0.30,0.06)], key, 2)
        RR(0,-0.28,0.58,0.14,shade,rad=4); RR(0,-0.28,0.58,0.14,key,2,rad=4)
        RR(0,-0.04,0.56,0.09,shade,rad=3); RR(0,-0.04,0.56,0.09,key,1,rad=3)
        for dx,dy in [(-0.24,-0.46),(-0.12,-0.60),(0,-0.67),(0.12,-0.60),(0.24,-0.46)]:
            CI(dx,dy,0.11,shade); CI(dx,dy,0.09); CI(dx,dy,0.09,key,2)
            CI(dx-0.03,dy-0.03,0.04,(*shade[:3],210))
        PO([(-0.12,0.63),(-0.04,0.06),(0.04,0.06),(0.12,0.63)], (*shade[:3],70))

    elif piece_type == chess.KING:
        PO([(-0.40,0.63),(0.40,0.63),(0.28,0.04),(0.22,-0.22),(-0.22,-0.22),(-0.28,0.04)])
        PO([(-0.40,0.63),(0.40,0.63),(0.28,0.04),(0.22,-0.22),(-0.22,-0.22),(-0.28,0.04)], key, 2)
        RR(0,-0.30,0.56,0.14,shade,rad=4); RR(0,-0.30,0.56,0.14,key,2,rad=4)
        RR(0,-0.06,0.56,0.09,shade,rad=3); RR(0,-0.06,0.56,0.09,key,1,rad=3)
        for dx,dy in [(-0.22,-0.48),(0,-0.57),(0.22,-0.48)]:
            PO([(dx-0.09,-0.36),(dx+0.09,-0.36),(dx+0.04,dy),(dx-0.04,dy)])
            PO([(dx-0.09,-0.36),(dx+0.09,-0.36),(dx+0.04,dy),(dx-0.04,dy)], key, 2)
        RR(0,-0.66,0.14,0.50,fill,rad=4); RR(0,-0.66,0.14,0.50,key,2,rad=4)
        RR(0,-0.76,0.38,0.13,fill,rad=4); RR(0,-0.76,0.38,0.13,key,2,rad=4)
        PO([(-0.12,0.63),(-0.04,0.04),(0.04,0.04),(0.12,0.63)], (*shade[:3],75))

    return pygame.transform.smoothscale(hi, (sq_size, sq_size))


def _build_cache(sq):
    return {(pt, col): _render_piece(pt, col==chess.WHITE, sq)
            for pt in [chess.PAWN,chess.ROOK,chess.KNIGHT,
                       chess.BISHOP,chess.QUEEN,chess.KING]
            for col in [chess.WHITE, chess.BLACK]}


# ══════════════════════════════════════════════════════════════════════════════
#  MINI PIECE CACHE  (for captured-piece display, ~22px)
# ══════════════════════════════════════════════════════════════════════════════
MINI_SQ = 22


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _fmt(s):
    s = max(0, int(s))
    return f'{s//60:02d}:{s%60:02d}'

def _gradient_rect(surf, top_col, bot_col, rect):
    """Vertical gradient fill."""
    r = pygame.Rect(rect)
    for y in range(r.height):
        t  = y / max(1, r.height - 1)
        c  = tuple(int(top_col[i]*(1-t) + bot_col[i]*t) for i in range(3))
        pygame.draw.line(surf, c, (r.x, r.y+y), (r.x+r.width-1, r.y+y))


# ══════════════════════════════════════════════════════════════════════════════
#  CHESS APP
# ══════════════════════════════════════════════════════════════════════════════
class ChessApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption('Chess AI')
        self.clock  = pygame.time.Clock()

        # Fonts
        self.fT  = _font(30, bold=True)   # title
        self.fB  = _font(22, bold=True)   # big
        self.fM  = _font(16)              # medium
        self.fS  = _font(13)              # small
        self.fXS = _font(11)              # tiny
        self.fC  = _font(12)              # coord

        # Piece caches
        self._pc   = _build_cache(SQ)
        self._mini = _build_cache(MINI_SQ)

        # Settings
        self.difficulty   = 'Medium'
        self.player_color = chess.WHITE
        self.time_control = 600

        # State
        self.board = self.selected_sq = self.last_move = None
        self.legal_for_sel = []
        self.board_history = self.move_list = self.san_list = []
        self.t_white = self.t_black = 0.0
        self.last_tick = 0.0
        self.timer_running = self.ai_thinking = self.game_over = False
        self.result_str = ''
        self.analysis   = []
        self.state      = 'menu'

    # ══════════════════════════════════════════════════════════════════════
    def run(self):
        while True:
            {'menu':self._run_menu,'game':self._run_game,
             'analysis':self._run_analysis}[self.state]()

    # ══════════════════════════════════════════════════════════════════════
    #  MENU
    # ══════════════════════════════════════════════════════════════════════
    def _run_menu(self):
        diff_opts  = ['Easy', 'Medium', 'Hard']
        color_opts = ['White', 'Black']
        time_opts  = [('5 min',300),('10 min',600),('30 min',1800)]
        sel_time   = 1
        cx         = WIN_W // 2

        while True:
            self.screen.fill(C_BG)

            # Header bar
            _gradient_rect(self.screen,(28,28,28),(18,18,18),(0,0,WIN_W,70))
            pygame.draw.line(self.screen, C_BORDER, (0,70),(WIN_W,70))

            # Logo area
            logo = self.fT.render('Chess AI', True, C_TEXT)
            self.screen.blit(logo,(cx-logo.get_width()//2, 18))
            # Green accent underline
            uw = logo.get_width()
            pygame.draw.rect(self.screen, C_GREEN,
                             (cx-uw//2, 20+logo.get_height(), uw, 3), border_radius=2)

            sub = self.fS.render('Professional Chess Engine  ·  Minimax · Alpha-Beta · Quiescence Search',
                                  True, C_DIM)
            self.screen.blit(sub,(cx-sub.get_width()//2, 84))

            y      = 116
            events = pygame.event.get()

            def section(label, opts, active, sy):
                lbl = self.fXS.render(label, True, C_FAINT)
                self.screen.blit(lbl,(cx-lbl.get_width()//2, sy))
                bw,bh,gap = 136,46,10
                total = len(opts)*bw+(len(opts)-1)*gap
                x0    = cx-total//2
                btns  = []
                for i,opt in enumerate(opts):
                    txt = opt if isinstance(opt,str) else opt[0]
                    bx  = x0+i*(bw+gap)
                    r   = pygame.Rect(bx,sy+20,bw,bh)
                    sel = (txt==active) if isinstance(active,str) else (i==active)
                    if sel:
                        _rr(self.screen,C_GREEN,r,10,2,C_GREEN_D)
                    else:
                        _rr(self.screen,(42,42,42),r,10,1,C_BORDER)
                    _ctext(self.screen,self.fM,txt,C_TEXT if sel else C_DIM,r)
                    btns.append((r,opt))
                return btns, sy+82

            diff_btns, y = section('DIFFICULTY',   diff_opts,  self.difficulty, y)
            col_lbl       = 'White' if self.player_color==chess.WHITE else 'Black'
            col_btns,  y = section('PLAY AS',       color_opts, col_lbl,         y)
            time_btns, y = section('TIME CONTROL',  [t[0] for t in time_opts], sel_time, y)

            y += 14
            start = pygame.Rect(cx-155, y, 310, 56)
            _rr(self.screen, C_GREEN, start, 12, 2, C_GREEN_D)
            _ctext(self.screen, self.fB, '▶   START GAME', C_TEXT, start)

            # Version tag
            ver = self.fXS.render('v2.0  ·  Built with python-chess + pygame', True, (55,55,55))
            self.screen.blit(ver,(cx-ver.get_width()//2, WIN_H-22))

            pygame.display.flip()
            self.clock.tick(60)

            for ev in events:
                if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type==pygame.MOUSEBUTTONDOWN:
                    p=ev.pos
                    for r,opt in diff_btns:
                        if r.collidepoint(p): self.difficulty=opt
                    for r,opt in col_btns:
                        if r.collidepoint(p):
                            self.player_color=chess.WHITE if opt=='White' else chess.BLACK
                    for i,(r,_) in enumerate(time_btns):
                        if r.collidepoint(p): sel_time=i; self.time_control=time_opts[i][1]
                    if start.collidepoint(p): self._reset(); return

    # ══════════════════════════════════════════════════════════════════════
    #  GAME
    # ══════════════════════════════════════════════════════════════════════
    def _reset(self):
        self.board         = chess.Board()
        self.selected_sq   = None
        self.legal_for_sel = []
        self.last_move     = None
        self.board_history = [self.board.copy()]
        self.move_list     = []
        self.san_list      = []
        self.t_white       = float(self.time_control)
        self.t_black       = float(self.time_control)
        self.last_tick     = time.time()
        self.timer_running = True
        self.ai_thinking   = False
        self.game_over     = False
        self.result_str    = ''
        self.analysis      = []
        self.state         = 'game'
        if self.player_color==chess.BLACK: self._trigger_ai()

    def _run_game(self):
        while self.state=='game':
            self.clock.tick(30)
            self._tick_timers()
            self.screen.fill(C_BG)
            self._draw_board()
            self._draw_panel()
            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: self.state='menu'
                if ev.type==pygame.MOUSEBUTTONDOWN: self._on_click(ev.pos)

    def _tick_timers(self):
        if not self.timer_running or self.game_over or self.ai_thinking: return
        now=time.time(); dt=now-self.last_tick; self.last_tick=now
        if self.board.turn==chess.WHITE:
            self.t_white=max(0.0,self.t_white-dt)
            if self.t_white==0.0: self._end('Black wins on time!')
        else:
            self.t_black=max(0.0,self.t_black-dt)
            if self.t_black==0.0: self._end('White wins on time!')

    def _end(self, msg=''):
        self.game_over=True; self.timer_running=False
        if not msg:
            r=self.board.result()
            msg={'1-0':'White wins!','0-1':'Black wins!','1/2-1/2':'Draw!'}.get(r,'Game Over')
        self.result_str=msg

    def _on_click(self, pos):
        if self.game_over:
            if self._btn('analyse').collidepoint(pos):
                self.analysis=analyze_game(self.board_history,self.move_list); self.state='analysis'
            if self._btn('menu').collidepoint(pos): self.state='menu'
            return
        if self._btn('resign').collidepoint(pos):
            w='Black' if self.player_color==chess.WHITE else 'White'
            self._end(f'You resigned — {w} wins!'); return
        if self.ai_thinking or self.board.turn!=self.player_color: return
        sq=self._pix2sq(pos)
        if sq is None: return
        if self.selected_sq is None:
            p=self.board.piece_at(sq)
            if p and p.color==self.player_color:
                self.selected_sq=sq
                self.legal_for_sel=[m for m in self.board.legal_moves if m.from_square==sq]
        else:
            mv=self._build_move(self.selected_sq,sq)
            if mv and mv in self.board.legal_moves: self._push(mv)
            else:
                p=self.board.piece_at(sq)
                if p and p.color==self.player_color:
                    self.selected_sq=sq
                    self.legal_for_sel=[m for m in self.board.legal_moves if m.from_square==sq]
                else: self.selected_sq=None; self.legal_for_sel=[]

    def _build_move(self,frm,to):
        p=self.board.piece_at(frm)
        if not p: return None
        promo=None
        if p.piece_type==chess.PAWN:
            if (p.color==chess.WHITE and chess.square_rank(to)==7) or \
               (p.color==chess.BLACK and chess.square_rank(to)==0): promo=chess.QUEEN
        return chess.Move(frm,to,promotion=promo)

    def _push(self,mv):
        san=self.board.san(mv)
        self.board.push(mv)
        self.san_list.append(san); self.move_list.append(mv)
        self.board_history.append(self.board.copy())
        self.last_move=mv; self.selected_sq=None; self.legal_for_sel=[]
        self.last_tick=time.time()
        if self.board.is_game_over(): self._end()
        else: self._trigger_ai()

    def _trigger_ai(self):
        self.ai_thinking=True
        threading.Thread(target=self._ai_worker,daemon=True).start()

    def _ai_worker(self):
        mv=get_best_move(self.board.copy(),self.difficulty)
        if mv:
            san=self.board.san(mv)
            self.board.push(mv); self.san_list.append(san); self.move_list.append(mv)
            self.board_history.append(self.board.copy())
            self.last_move=mv; self.last_tick=time.time()
            if self.board.is_game_over(): self._end()
        self.ai_thinking=False

    def _sq2pix(self,sq):
        f,r=chess.square_file(sq),chess.square_rank(sq)
        c,rw=(f,7-r) if self.player_color==chess.WHITE else (7-f,r)
        return BX+c*SQ, BY+rw*SQ

    def _pix2sq(self,pos):
        x,y=pos[0]-BX,pos[1]-BY
        if not(0<=x<BOARD_PX and 0<=y<BOARD_PX): return None
        c,rw=x//SQ,y//SQ
        if self.player_color==chess.WHITE: f,r=c,7-rw
        else: f,r=7-c,rw
        return chess.square(f,r)

    def _btn(self, name):
        if name=='analyse': return pygame.Rect(PANEL_X, WIN_H-112, PANEL_W, 50)
        if name=='menu':    return pygame.Rect(PANEL_X, WIN_H-56,  PANEL_W, 42)
        if name=='resign':  return pygame.Rect(PANEL_X, WIN_H-56,  PANEL_W, 42)

    # ── CAPTURED PIECES ────────────────────────────────────────────────────
    def _captured(self, color):
        """Return list of captured pieces of `color`."""
        orig = chess.Board()
        captured = []
        for pt in [chess.QUEEN,chess.ROOK,chess.BISHOP,chess.KNIGHT,chess.PAWN]:
            orig_cnt = len(orig.pieces(pt,color))
            curr_cnt = len(self.board.pieces(pt,color))
            for _ in range(orig_cnt - curr_cnt):
                captured.append(pt)
        return captured

    def _draw_captured_row(self, pieces, color, y):
        x = BX
        for pt in pieces:
            self.screen.blit(self._mini[(pt,color)],(x,y)); x+=MINI_SQ-4
        if not pieces:
            none_t = self.fXS.render('No captures yet', True, C_FAINT)
            self.screen.blit(none_t,(BX, y+4))

    # ── BOARD ──────────────────────────────────────────────────────────────
    def _draw_board(self):
        last_sqs  = (self.last_move.from_square,self.last_move.to_square) if self.last_move else ()
        legal_tos = {m.to_square for m in self.legal_for_sel}

        # Outer shadow
        shadow_rect = pygame.Rect(BX-6, BY-6, BOARD_PX+12, BOARD_PX+12)
        _rr(self.screen,(10,10,10), shadow_rect, 4)

        for sq in chess.SQUARES:
            px,py=self._sq2pix(sq)
            f,r=chess.square_file(sq),chess.square_rank(sq)
            light=(f+r)%2==1
            if sq==self.selected_sq:      col=C_SEL_L if light else C_SEL_D
            elif sq in last_sqs:           col=C_LAST_L if light else C_LAST_D
            else:                          col=C_LIGHT  if light else C_DARK
            pygame.draw.rect(self.screen,col,(px,py,SQ,SQ))

            if sq in legal_tos:
                cx2,cy2=px+SQ//2,py+SQ//2
                if self.board.piece_at(sq):
                    pygame.draw.circle(self.screen,(0,0,0),(cx2,cy2),SQ//2-3,5)
                else:
                    dot=pygame.Surface((SQ,SQ),pygame.SRCALPHA)
                    _aa_fill_circle(dot,(0,0,0,72),SQ//2,SQ//2,16)
                    self.screen.blit(dot,(px,py))

        if self.board.is_check():
            ksq=self.board.king(self.board.turn)
            kx,ky=self._sq2pix(ksq)
            # Glow effect
            glow=pygame.Surface((SQ,SQ),pygame.SRCALPHA)
            for alpha,r2 in [(30,SQ//2),(60,SQ//2-3),(120,SQ//2-6)]:
                _aa_fill_circle(glow,(200,30,30,alpha),SQ//2,SQ//2,r2)
            self.screen.blit(glow,(kx,ky))
            pygame.draw.rect(self.screen,C_CHECK,(kx,ky,SQ,SQ),3)

        for sq in chess.SQUARES:
            p=self.board.piece_at(sq)
            if p:
                px,py=self._sq2pix(sq)
                self.screen.blit(self._pc[(p.piece_type,p.color)],(px,py))

        # Board border
        pygame.draw.rect(self.screen,(55,55,55),(BX-1,BY-1,BOARD_PX+2,BOARD_PX+2),1)

        # Coordinates
        files='abcdefgh' if self.player_color==chess.WHITE else 'hgfedcba'
        ranks='87654321' if self.player_color==chess.WHITE else '12345678'
        for i in range(8):
            light_sq=i%2==0
            ft=self.fC.render(files[i],True,C_DARK if light_sq else C_LIGHT)
            rt=self.fC.render(ranks[i],True,C_LIGHT if light_sq else C_DARK)
            self.screen.blit(ft,(BX+i*SQ+SQ-ft.get_width()-3, BY+BOARD_PX-ft.get_height()-2))
            self.screen.blit(rt,(BX+3, BY+i*SQ+3))

        # Captured pieces
        opp_color = chess.BLACK if self.player_color==chess.WHITE else chess.WHITE
        ai_cap    = self._captured(self.player_color)   # AI captured player's pieces
        pl_cap    = self._captured(opp_color)           # Player captured AI's pieces
        # Above board = AI's captures (opponent pieces taken by AI)
        self._draw_captured_row(ai_cap, self.player_color, BY - MINI_SQ - 6)
        # Below board = player's captures
        self._draw_captured_row(pl_cap, opp_color, BY + BOARD_PX + 8)

    # ── PANEL ──────────────────────────────────────────────────────────────
    def _draw_panel(self):
        px=PANEL_X

        # Panel background card
        panel_rect=pygame.Rect(px-8,BY-MINI_SQ-10,PANEL_W+8,BOARD_PX+MINI_SQ*2+20)
        _rr(self.screen,(26,26,26),panel_rect,10,1,C_BORDER)

        # ── AI Timer ──────────────────────────────────────────────────────
        ai_col  = chess.BLACK if self.player_color==chess.WHITE else chess.WHITE
        ai_t    = self.t_black if ai_col==chess.BLACK else self.t_white
        ai_act  = self.board.turn==ai_col and not self.game_over
        self._timer_card(px, BY, PANEL_W, 'AI', _fmt(ai_t), ai_act, self.difficulty)

        # ── Status ────────────────────────────────────────────────────────
        status_y = BY + 84
        if self.game_over:
            _rr(self.screen,(40,40,20),pygame.Rect(px,status_y,PANEL_W,28),6)
            t=self.fS.render(self.result_str,True,C_GOLD)
        elif self.ai_thinking:
            _rr(self.screen,(28,38,28),pygame.Rect(px,status_y,PANEL_W,28),6)
            t=self.fS.render('AI is thinking…',True,(180,220,100))
        elif self.board.is_check():
            _rr(self.screen,(45,20,20),pygame.Rect(px,status_y,PANEL_W,28),6)
            t=self.fS.render('⚠  Check!',True,(240,100,100))
        elif self.board.turn==self.player_color:
            _rr(self.screen,(22,38,22),pygame.Rect(px,status_y,PANEL_W,28),6)
            t=self.fS.render('▸  Your turn',True,C_GREEN)
        else:
            _rr(self.screen,(30,30,30),pygame.Rect(px,status_y,PANEL_W,28),6)
            t=self.fS.render('Waiting…',True,C_DIM)
        self.screen.blit(t,(px+10,status_y+7))

        # ── Move list ─────────────────────────────────────────────────────
        mv_hdr_y = status_y + 36
        hdr = self.fXS.render('MOVE HISTORY', True, C_FAINT)
        self.screen.blit(hdr,(px, mv_hdr_y))
        pygame.draw.line(self.screen, C_BORDER,(px,mv_hdr_y+16),(px+PANEL_W,mv_hdr_y+16))

        mbox = pygame.Rect(px, mv_hdr_y+18, PANEL_W, 262)
        _rr(self.screen,(20,20,20), mbox, 6, 1, C_BORDER)

        pairs=[(i//2+1,self.san_list[i],
                self.san_list[i+1] if i+1<len(self.san_list) else '')
               for i in range(0,len(self.san_list),2)]
        MAX_V=14; visible=pairs[max(0,len(pairs)-MAX_V):][:MAX_V]
        for idx,(n,w,b) in enumerate(visible):
            vy=mbox.y+6+idx*18
            if idx%2==0:
                pygame.draw.rect(self.screen,(24,24,24),(px,vy,PANEL_W,18))
            self.screen.blit(self.fXS.render(f'{n}.',True,(80,80,80)),(px+6,vy+3))
            self.screen.blit(self.fXS.render(w,True,(220,220,220)),(px+36,vy+3))
            self.screen.blit(self.fXS.render(b,True,(155,155,155)),(px+138,vy+3))

        # ── Player Timer ──────────────────────────────────────────────────
        pl_t   = self.t_white if self.player_color==chess.WHITE else self.t_black
        pl_act = self.board.turn==self.player_color and not self.game_over
        pl_nm  = 'You (White)' if self.player_color==chess.WHITE else 'You (Black)'
        self._timer_card(px, BY+400, PANEL_W, pl_nm, _fmt(pl_t), pl_act)

        # ── Buttons ───────────────────────────────────────────────────────
        if self.game_over:
            ab=self._btn('analyse')
            _rr(self.screen,C_GREEN,ab,10,2,C_GREEN_D)
            _ctext(self.screen,self.fM,'📊  Analyse Game',C_TEXT,ab)
            mb=self._btn('menu')
            _rr(self.screen,(40,40,40),mb,8,1,C_BORDER)
            _ctext(self.screen,self.fS,'Main Menu',C_DIM,mb)
        else:
            rb=self._btn('resign')
            hover=rb.collidepoint(pygame.mouse.get_pos())
            _rr(self.screen,(195,48,48) if hover else C_RED, rb, 9,
                2,(220,80,80) if hover else C_RED_D)
            _ctext(self.screen,self.fS,'Resign',C_TEXT,rb)

    def _timer_card(self, x, y, w, name, time_str, active, diff=''):
        bg  = (48,96,48) if active else (30,30,30)
        bc  = (75,155,65) if active else C_BORDER
        _rr(self.screen, bg, pygame.Rect(x,y,w,74), 10, 2, bc)
        n_txt = name.upper() + (f'   [{diff.upper()}]' if diff else '')
        nt = self.fXS.render(n_txt, True, (140,210,120) if active else C_FAINT)
        tt = self.fB.render(time_str, True, (195,255,175) if active else C_TEXT)
        self.screen.blit(nt,(x+12, y+8))
        self.screen.blit(tt,(x+12, y+32))

    # ══════════════════════════════════════════════════════════════════════
    #  ANALYSIS
    # ══════════════════════════════════════════════════════════════════════
    def _run_analysis(self):
        scroll=0; IH=28; LY=252; lh=WIN_H-LY-66
        CATS=[('Excellent','!!', (50,210,80)),('Good','!',(100,200,100)),
              ('Inaccuracy','?!',(240,200,50)),('Mistake','?',(230,130,50)),
              ('Blunder','??', (220,50,50))]
        cp={c[0]:0 for c in CATS}; ca={c[0]:0 for c in CATS}
        for i,a in enumerate(self.analysis):
            mp=(i%2==0 and self.player_color==chess.WHITE) or \
               (i%2==1 and self.player_color==chess.BLACK)
            if a['classification'] in cp:
                if mp: cp[a['classification']]+=1
                else:  ca[a['classification']]+=1

        while self.state=='analysis':
            self.screen.fill(C_BG)

            # Header
            _gradient_rect(self.screen,(28,28,28),(18,18,18),(0,0,WIN_W,68))
            pygame.draw.line(self.screen,C_BORDER,(0,68),(WIN_W,68))
            ti=self.fT.render('Game Analysis',True,C_TEXT)
            self.screen.blit(ti,(WIN_W//2-ti.get_width()//2,16))

            # Stat cards
            total_cats=len(CATS); card_w=114; gap=8
            total_w=total_cats*card_w+(total_cats-1)*gap
            cx_start=WIN_W//2-total_w//2
            for ci,(cat,sym,col) in enumerate(CATS):
                bx=cx_start+ci*(card_w+gap); by=80; bh=74
                _rr(self.screen,(28,28,28),pygame.Rect(bx,by,card_w,bh),10,2,col)
                cnt=self.fB.render(str(cp[cat]),True,col)
                sym_t=self.fXS.render(f'{sym}  {cat}',True,(170,170,170))
                ai_t=self.fXS.render(f'AI: {ca[cat]}',True,(100,100,100))
                self.screen.blit(cnt,(bx+card_w//2-cnt.get_width()//2,by+6))
                self.screen.blit(sym_t,(bx+card_w//2-sym_t.get_width()//2,by+40))
                self.screen.blit(ai_t,(bx+card_w//2-ai_t.get_width()//2,by+56))

            leg=self.fXS.render(
                'Your moves are highlighted  ·  Delta = centipawn change from your perspective',
                True,(80,80,80))
            self.screen.blit(leg,(WIN_W//2-leg.get_width()//2,162))

            # Column headers
            hy=176
            pygame.draw.line(self.screen,C_BORDER,(28,hy),(WIN_W-28,hy))
            for txt,hx in [('#',38),('Move',80),('Player',156),
                           ('Classification',232),('Δ  eval',392)]:
                self.screen.blit(self.fXS.render(txt,True,C_FAINT),(hx,hy+4))
            pygame.draw.line(self.screen,C_BORDER,(28,hy+20),(WIN_W-28,hy+20))

            lr=pygame.Rect(28,LY,WIN_W-56,lh)
            _rr(self.screen,(20,20,20),lr,8,1,C_BORDER)
            self.screen.set_clip(lr)

            for i,a in enumerate(self.analysis):
                iy=LY+4+(i-scroll)*IH
                if iy<LY-IH or iy>LY+lh: continue
                mp=(i%2==0 and self.player_color==chess.WHITE) or \
                   (i%2==1 and self.player_color==chess.BLACK)

                row_bg=(24,24,24) if i%2==0 else (20,20,20)
                pygame.draw.rect(self.screen,row_bg,(28,iy,WIN_W-56,IH-1))

                if mp and a['classification']=='Blunder':
                    pygame.draw.rect(self.screen,(55,16,16),(28,iy,WIN_W-56,IH-1))
                elif mp and a['classification']=='Mistake':
                    pygame.draw.rect(self.screen,(50,25,10),(28,iy,WIN_W-56,IH-1))
                elif mp and a['classification'] in ('Excellent','Good'):
                    pygame.draw.rect(self.screen,(16,46,16),(28,iy,WIN_W-56,IH-1))

                who='You' if mp else 'AI'
                wc=C_GREEN if mp else (130,130,130)
                d=a['delta']
                ds=f'+{d:.0f}' if d>=0 else f'{d:.0f}'
                dc=(70,195,70) if d>=0 else (195,70,70)
                mn=i//2+1
                col_label=a['color']

                for txt,tx,fc in [
                    (f'{mn}.{"W" if i%2==0 else "B"}',38,(85,85,85)),
                    (self.san_list[i],80,(215,215,215)),
                    (who,156,wc),
                    (f"{a['symbol']}  {a['classification']}",232,col_label),
                    (f'{ds} cp',392,dc)]:
                    self.screen.blit(self.fXS.render(txt,True,fc),(tx,iy+8))

            self.screen.set_clip(None)

            # Summary bar
            total_moves=len([a for i,a in enumerate(self.analysis) if
                (i%2==0 and self.player_color==chess.WHITE) or
                (i%2==1 and self.player_color==chess.BLACK)])
            blunders=cp['Blunder']; excellent=cp['Excellent']
            summary=f'Your game:  {total_moves} moves  ·  {excellent} excellent  ·  {blunders} blunders'
            st=self.fS.render(summary,True,C_DIM)
            self.screen.blit(st,(WIN_W//2-st.get_width()//2, LY+lh+8))

            back=pygame.Rect(WIN_W//2-120,WIN_H-52,240,42)
            _rr(self.screen,(40,40,40),back,10,1,C_BORDER)
            _ctext(self.screen,self.fM,'← Back to Menu',C_TEXT,back)

            pygame.display.flip(); self.clock.tick(60)
            ms=max(0,len(self.analysis)-lh//IH+1)
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type==pygame.MOUSEWHEEL: scroll=max(0,min(ms,scroll-ev.y))
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: self.state='menu'
                if ev.type==pygame.MOUSEBUTTONDOWN:
                    if back.collidepoint(ev.pos): self.state='menu'
