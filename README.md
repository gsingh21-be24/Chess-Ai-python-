# ♟ Chess AI

A fully playable Chess game built in Python featuring a custom AI engine with Minimax, Alpha-Beta Pruning, Quiescence Search, and a Transposition Table. Includes a chess.com-style GUI, per-side timers, move history, and post-game analysis with blunder and excellent move detection.

---

## 🖼 Features

- **AI Engine** — Minimax + Alpha-Beta Pruning + Quiescence Search + Transposition Table + Killer Move + History Heuristic + Iterative Deepening
- **3 Difficulty Levels** — Easy / Medium / Hard
- **chess.com-style Board** — Exact colour palette, highlights, coordinates
- **Beautiful Pieces** — 4× supersampled, anti-aliased, hand-drawn pieces
- **Per-side Timers** — 5 / 10 / 30 minute time controls
- **Move History** — Scrollable algebraic notation panel
- **Captured Pieces** — Displayed above and below the board
- **Post-game Analysis** — Every move classified: Blunder / Mistake / Inaccuracy / Good / Excellent with centipawn delta
- **All Chess Rules** — En passant, castling, pawn promotion, 50-move rule, stalemate, threefold repetition

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install pygame-ce python-chess
```

### 2. Run
```bash
python main.py
```

---

## 🗂 Project Structure

```
Chess-Ai-python/
├── main.py          ← Entry point
├── gui.py           ← Full Pygame GUI
├── engine.py        ← Chess AI engine
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🧠 How the AI Works

| Technique | Purpose |
|---|---|
| **Minimax** | Searches all possible moves to find the best outcome |
| **Alpha-Beta Pruning** | Cuts off branches that can't affect result → faster |
| **Quiescence Search** | Continues searching captures to avoid horizon blunders |
| **Transposition Table** | Caches evaluated positions → avoids redundant work |
| **Iterative Deepening** | Searches deeper within time limit, returns best move found |
| **Killer Move Heuristic** | Tries moves that caused cutoffs in sibling nodes first |
| **History Heuristic** | Prioritises moves that have historically been strong |
| **Tapered Evaluation** | Smoothly transitions between midgame and endgame scoring |

---

## 📊 Analysis Legend

| Symbol | Classification | Meaning |
|---|---|---|
| `!!` | **Excellent** | Big improvement (>75 cp) |
| `!`  | **Good**      | Solid improvement (25–75 cp) |
| ` `  | **Neutral**   | No significant change |
| `?!` | **Inaccuracy**| Small loss (25–75 cp) |
| `?`  | **Mistake**   | Noticeable loss (75–150 cp) |
| `??` | **Blunder**   | Major loss (>150 cp) |

---

## ⌨️ Controls

| Action | Input |
|---|---|
| Select piece | Left click |
| Move piece | Left click destination |
| Resign | Resign button |
| Back to menu | Esc |
| Scroll move list | Mouse wheel |

---

## 🛠 Requirements

- Python 3.8+
- pygame-ce ≥ 2.1
- python-chess ≥ 1.9

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
