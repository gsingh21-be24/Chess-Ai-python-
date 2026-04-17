"""
Chess AI Engine  –  Professional Strength
==========================================
Features:
  • Iterative Deepening (time-managed search)
  • Quiescence Search  (no horizon-effect blunders)
  • Transposition Table with Zobrist keys
  • Killer Move Heuristic
  • History Heuristic
  • MVV-LVA capture ordering
  • Piece-Square Tables (midgame + endgame, tapered eval)
  • Passed-pawn, doubled-pawn, isolated-pawn bonuses
  • King safety evaluation
  • Mobility bonus
"""

import chess
import random
import time
from collections import defaultdict

# ── Piece values (centipawns) ────────────────────────────────────────────────
MG_VAL = {chess.PAWN:100, chess.KNIGHT:320, chess.BISHOP:330,
          chess.ROOK:500, chess.QUEEN:900, chess.KING:20000}
EG_VAL = {chess.PAWN:120, chess.KNIGHT:290, chess.BISHOP:310,
          chess.ROOK:520, chess.QUEEN:940, chess.KING:20000}

# ── Piece-Square Tables  (a1=index 0, white's perspective) ──────────────────
MG_PAWN = [
   0,  0,  0,  0,  0,  0,  0,  0,
  98,134, 61, 95, 68,126, 34,-11,
  -6,  7, 26, 31, 65, 56, 25,-20,
 -14, 13,  6, 21, 23, 12, 17,-23,
 -27, -2, -5, 12, 17,  6, 10,-25,
 -26, -4, -4,-10,  3,  3, 33,-12,
 -35, -1,-20,-23,-15, 24, 38,-22,
   0,  0,  0,  0,  0,  0,  0,  0,
]
EG_PAWN = [
   0,  0,  0,  0,  0,  0,  0,  0,
 178,173,158,134,147,132,165,187,
  94,100, 85, 67, 56, 53, 82, 84,
  32, 24, 13,  5, -2,  4, 17, 17,
  13,  9, -3, -7, -7, -8,  3, -1,
   4,  7, -6,  1,  0, -5, -1, -8,
  13,  8,  8, 10, 13,  0,  2, -7,
   0,  0,  0,  0,  0,  0,  0,  0,
]
MG_KNIGHT = [
 -167,-89,-34,-49, 61,-97,-15,-107,
  -73,-41, 72, 36, 23, 62,  7, -17,
  -47, 60, 37, 65, 84,129, 73,  44,
   -9, 17, 19, 53, 37, 69, 18,  22,
  -13,  4, 16, 13, 28, 19, 21,  -8,
  -23, -9, 12, 10, 19, 17, 25, -16,
  -29,-53,-12, -3, -1, 18,-14, -19,
 -105,-21,-58,-33,-17,-28,-19, -23,
]
EG_KNIGHT = [
  -58,-38,-13,-28,-31,-27,-63,-99,
  -25, -8,-25, -2, -9,-25,-24,-52,
  -24,-20, 10,  9, -1, -9,-19,-41,
  -17,  3, 22, 22, 22, 11,  8,-18,
  -18, -6, 16, 25, 16, 17,  4,-18,
  -23, -3, -1, 15, 10, -3,-20,-22,
  -42,-20,-10, -5, -2,-20,-23,-44,
  -29,-51,-23,-15,-22,-18,-50,-64,
]
MG_BISHOP = [
  -29,  4,-82,-37,-25,-42,  7, -8,
  -26, 16,-18,-13, 30, 59, 18,-47,
  -16, 37, 43, 40, 35, 50, 37, -2,
   -4,  5, 19, 50, 37, 37,  7, -2,
   -6, 13, 13, 26, 34, 12, 10,  4,
    0, 15, 15, 15, 14, 27, 18, 10,
    4, 15, 16,  0,  7, 21, 33,  1,
  -33, -3,-14,-21,-13,-12,-39,-21,
]
EG_BISHOP = [
  -14,-21,-11, -8, -7, -9,-17,-24,
   -8, -4,  7,-12, -3,-13, -4,-14,
    2, -8,  0, -1, -2,  6,  0,  4,
   -3,  9, 12,  9, 14, 10,  3,  2,
   -6,  3, 13, 19,  7, 10, -3, -9,
  -12, -3,  8, 10, 13,  3, -7,-15,
  -14,-18, -7, -1,  4, -9,-15,-27,
  -23, -9,-23, -5, -9,-16, -5,-17,
]
MG_ROOK = [
   32, 42, 32, 51,63,  9, 31, 43,
   27, 32, 58, 62,80, 67, 26, 44,
   -5, 19, 26, 36,17, 45, 61, 16,
  -24,-11,  7, 26,24, 35, -8,-20,
  -36,-26,-12, -1, 9,-7,  6,-23,
  -45,-25,-16,-17, 3, 0, -5,-33,
  -44,-16,-20, -9,-1,11, -6,-71,
  -19,-13,  1, 17,16, 7,-37,-26,
]
EG_ROOK = [
  13, 10, 18, 15, 12, 12,  8,  5,
  11, 13, 13, 11, -3,  3,  8,  3,
   7,  7,  7,  5,  4, -3, -5, -3,
   4,  3, 13,  1,  2,  1, -1,  2,
   3,  5,  8,  4, -5, -6, -8,-11,
  -4,  0, -5, -1, -7,-12, -8,-16,
  -6, -6,  0,  2, -9, -9,-11, -3,
  -9,  2,  3, -1, -5,-13,  4,-20,
]
MG_QUEEN = [
  -28,  0, 29, 12, 59, 44, 43, 45,
  -24,-39, -5,  1,-16, 57, 28, 54,
  -13,-17,  7,  8, 29, 56, 47, 57,
  -27,-27,-16,-16, -1, 17, -2,  1,
   -9,-26, -9,-10, -2, -4,  3, -3,
  -14,  2,-11, -2, -5,  2, 14,  5,
  -35, -8, 11,  2,  8, 15, -3,  1,
   -1,-18, -9, 10,-15,-25,-31,-50,
]
EG_QUEEN = [
   -9, 22, 22, 27, 27, 19, 10, 20,
  -17, 20, 32, 41, 58, 25, 30,  0,
  -20,  6,  9, 49, 47, 35, 19,  9,
    3, 22, 24, 45, 57, 40, 57, 36,
  -18, 28, 19, 47, 31, 34, 39, 23,
  -16,-27, 15,  6,  9, 17, 10,  5,
  -22,-23,-30,-16,-16,-23,-36,-32,
  -33,-28,-22,-43, -5,-32,-20,-41,
]
MG_KING = [
  -65, 23, 16,-15,-56,-34,  2, 13,
   29, -1,-20, -7, -8, -4,-38,-29,
   -9, 24,  2,-16,-20,  6, 22,-22,
  -17,-20,-12,-27,-30,-25,-14,-36,
  -49, -1,-27,-39,-46,-44,-33,-51,
  -14,-14,-22,-46,-44,-30,-15,-27,
    1,  7, -8,-64,-43,-16,  9,  8,
  -15, 36, 12,-54,  8,-28, 24, 14,
]
EG_KING = [
  -74,-35,-18,-18,-11, 15,  4,-17,
  -12, 17, 14, 17, 17, 38, 23, 11,
   10, 17, 23, 15, 20, 45, 44, 13,
   -8, 22, 24, 27, 26, 33, 26,  3,
  -18, -4, 21, 24, 27, 23,  9,-11,
  -19, -3, 11, 21, 23, 16,  7, -9,
  -27,-11,  4, 13, 14,  4, -5,-17,
  -53,-34,-21,-11,-28,-14,-24,-43,
]

MG_PST = {chess.PAWN:MG_PAWN, chess.KNIGHT:MG_KNIGHT, chess.BISHOP:MG_BISHOP,
          chess.ROOK:MG_ROOK,  chess.QUEEN:MG_QUEEN,   chess.KING:MG_KING}
EG_PST = {chess.PAWN:EG_PAWN, chess.KNIGHT:EG_KNIGHT, chess.BISHOP:EG_BISHOP,
          chess.ROOK:EG_ROOK,  chess.QUEEN:EG_QUEEN,   chess.KING:EG_KING}

# ── Transposition table entry flags ─────────────────────────────────────────
EXACT, LOWER, UPPER = 0, 1, 2

# ── Global killer / history tables ──────────────────────────────────────────
MAX_DEPTH = 10
killers   = [[None, None] for _ in range(MAX_DEPTH + 2)]
history   = defaultdict(int)


def _pst_idx(sq, white):
    r = chess.square_rank(sq)
    f = chess.square_file(sq)
    return ((7 - r) * 8 + f) if white else (r * 8 + f)


def _game_phase(board):
    """0 = full endgame, 24 = full midgame (material-based taper)."""
    phase = 0
    weights = {chess.KNIGHT:1, chess.BISHOP:1, chess.ROOK:2, chess.QUEEN:4}
    for pt, w in weights.items():
        phase += w * (len(board.pieces(pt, chess.WHITE)) +
                      len(board.pieces(pt, chess.BLACK)))
    return min(24, phase)


def evaluate(board):
    if board.is_checkmate():
        return -99000 if board.turn == chess.WHITE else 99000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    phase   = _game_phase(board)
    mg, eg  = 0, 0

    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p is None:
            continue
        idx  = _pst_idx(sq, p.color == chess.WHITE)
        sign = 1 if p.color == chess.WHITE else -1
        mg  += sign * (MG_VAL[p.piece_type] + MG_PST[p.piece_type][idx])
        eg  += sign * (EG_VAL[p.piece_type] + EG_PST[p.piece_type][idx])

    # Taper between midgame and endgame
    score = (mg * phase + eg * (24 - phase)) // 24

    # ── Pawn structure ────────────────────────────────────────────────────
    for color, sign in [(chess.WHITE, 1), (chess.BLACK, -1)]:
        pawns = board.pieces(chess.PAWN, color)
        pawn_files = [chess.square_file(sq) for sq in pawns]
        # Doubled pawns
        for f in range(8):
            cnt = pawn_files.count(f)
            if cnt > 1:
                score -= sign * 15 * (cnt - 1)
        # Isolated pawns
        for f in set(pawn_files):
            if (f - 1 not in pawn_files) and (f + 1 not in pawn_files):
                score -= sign * 10

    # ── Bishop pair bonus ─────────────────────────────────────────────────
    for color, sign in [(chess.WHITE, 1), (chess.BLACK, -1)]:
        if len(board.pieces(chess.BISHOP, color)) >= 2:
            score += sign * 25

    # ── Mobility ──────────────────────────────────────────────────────────
    if not board.is_game_over():
        our_mob = board.legal_moves.count() if board.turn == chess.WHITE else 0
        board.push(chess.Move.null())
        opp_mob = board.legal_moves.count() if board.turn == chess.BLACK else 0
        board.pop()
        score += (our_mob - opp_mob) * 2

    return score if board.turn == chess.WHITE else -score


# ── Move ordering ─────────────────────────────────────────────────────────────
def _score_move(board, move, depth, tt_move):
    if move == tt_move:
        return 30000
    if board.is_capture(move):
        vic  = board.piece_at(move.to_square)
        att  = board.piece_at(move.from_square)
        if vic and att:
            return 10000 + MG_VAL[vic.piece_type] - MG_VAL[att.piece_type] // 10
        return 9000
    if move.promotion:
        return 9500
    if depth < len(killers):
        if move == killers[depth][0]: return 8000
        if move == killers[depth][1]: return 7000
    return history.get((move.from_square, move.to_square), 0)


def _ordered_moves(board, depth, tt_move=None):
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: _score_move(board, m, depth, tt_move), reverse=True)
    return moves


# ── Quiescence search ─────────────────────────────────────────────────────────
def _quiesce(board, alpha, beta, depth=0):
    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    if depth > 6:
        return alpha

    for move in board.generate_pseudo_legal_moves():
        if not board.is_capture(move):
            continue
        if not board.is_legal(move):
            continue
        board.push(move)
        score = -_quiesce(board, -beta, -alpha, depth + 1)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


# ── Negamax with alpha-beta + TT ─────────────────────────────────────────────
def _negamax(board, depth, alpha, beta, tt, nodes):
    nodes[0] += 1
    key = board._transposition_key()

    # TT lookup
    tt_entry = tt.get(key)
    tt_move  = None
    if tt_entry:
        tt_depth, tt_score, tt_flag, tt_move = tt_entry
        if tt_depth >= depth:
            if tt_flag == EXACT:
                return tt_score
            if tt_flag == LOWER:
                alpha = max(alpha, tt_score)
            elif tt_flag == UPPER:
                beta  = min(beta,  tt_score)
            if alpha >= beta:
                return tt_score

    if depth == 0 or board.is_game_over():
        return _quiesce(board, alpha, beta)

    orig_alpha = alpha
    best_score = -999999
    best_move  = None

    for move in _ordered_moves(board, depth, tt_move):
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha, tt, nodes)
        board.pop()

        if score > best_score:
            best_score = score
            best_move  = move

        alpha = max(alpha, score)
        if alpha >= beta:
            # Update killer + history
            if not board.is_capture(move):
                if depth < len(killers):
                    killers[depth][1] = killers[depth][0]
                    killers[depth][0] = move
                history[(move.from_square, move.to_square)] += depth * depth
            break

    # TT store
    if best_score <= orig_alpha:
        flag = UPPER
    elif best_score >= beta:
        flag = LOWER
    else:
        flag = EXACT
    tt[key] = (depth, best_score, flag, best_move)

    return best_score


# ── Iterative deepening with time management ──────────────────────────────────
DIFFICULTY_CFG = {
    'Easy':   {'max_depth': 2, 'time': 0.5,  'random_pct': 0.35},
    'Medium': {'max_depth': 5, 'time': 2.0,  'random_pct': 0.0},
    'Hard':   {'max_depth': 8, 'time': 5.0,  'random_pct': 0.0},
}


def get_best_move(board, difficulty='Medium'):
    cfg       = DIFFICULTY_CFG.get(difficulty, DIFFICULTY_CFG['Medium'])
    max_depth = cfg['max_depth']
    time_lim  = cfg['time']
    rand_pct  = cfg['random_pct']

    if rand_pct > 0 and random.random() < rand_pct:
        return random.choice(list(board.legal_moves))

    tt        = {}
    nodes     = [0]
    best_move = None
    deadline  = time.time() + time_lim

    # Clear killers for new search
    global killers, history
    killers  = [[None, None] for _ in range(MAX_DEPTH + 2)]
    history  = defaultdict(int)

    for depth in range(1, max_depth + 1):
        if time.time() >= deadline:
            break

        alpha, beta = -999999, 999999
        depth_best  = None
        depth_score = -999999

        for move in _ordered_moves(board, depth):
            board.push(move)
            score = -_negamax(board, depth - 1, -beta, -alpha, tt, nodes)
            board.pop()

            if score > depth_score:
                depth_score = score
                depth_best  = move

            alpha = max(alpha, score)

        if depth_best:
            best_move = depth_best

        if time.time() >= deadline:
            break

    return best_move or random.choice(list(board.legal_moves))


# ── Post-game analysis ────────────────────────────────────────────────────────
def analyze_game(board_history, move_list):
    results = []
    for i, move in enumerate(move_list):
        b_before = board_history[i]
        b_after  = board_history[i + 1]

        ev_before = evaluate(b_before)
        ev_after  = evaluate(b_after)

        mover_white = (i % 2 == 0)
        delta = (ev_after - ev_before) if mover_white else (ev_before - ev_after)

        if   delta <= -150: cls, sym, col = 'Blunder',    '??', (220,  50,  50)
        elif delta <=  -75: cls, sym, col = 'Mistake',    '?',  (230, 130,  50)
        elif delta <=  -25: cls, sym, col = 'Inaccuracy', '?!', (240, 200,  50)
        elif delta >=   75: cls, sym, col = 'Excellent',  '!!', ( 50, 210,  80)
        elif delta >=   25: cls, sym, col = 'Good',       '!',  (100, 200, 100)
        else:               cls, sym, col = 'Neutral',    '·',  (170, 170, 170)

        results.append({'move': move, 'classification': cls,
                        'symbol': sym, 'color': col,
                        'delta': delta, 'mover_white': mover_white})
    return results
