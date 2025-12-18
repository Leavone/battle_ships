# Battleship Game – Project Report

## Overview

This project is a terminal-based implementation of the classic **Battleship** game.  
A human player plays against a bot with a simple but structured AI.  
The game supports full ship placement validation, turn-based gameplay, logging, and board visualization.

---

## Input Format

### Ship Placement Input

Players place ships using human-readable coordinates on a **10×10 grid (A1–J10)**.

Supported formats:

1. **Space-separated coordinates**
```
A1 A2 A3
```
Used for ships of size > 1.

2. **Range format**
```

B4-B6

```
Automatically expands into consecutive coordinates.
- Must be horizontal or vertical.

3. **Single coordinate**
```

A10

```
Used for ships of size 1.

Coordinates are parsed as:
- **Column**: Letter `A–J`
- **Row**: Number `1–10`

Internally, coordinates are converted to **0-based (row, col)** tuples.

---

### Move Input (Gameplay)

During the game, the player enters moves in the format:
```

A1
J10

```

Validation ensures:
- Correct format
- Within board bounds
- Cell has not been previously attacked

---

## Ship Placement Validation

Ship placement is validated through several layers to ensure a legal Battleship setup.

### Fleet Size Validation
The fleet must exactly match the required configuration:
- 1 ship of size 4
- 2 ships of size 3
- 3 ships of size 2
- 4 ships of size 1

### Coordinate Validation
- All coordinates must be within bounds (`0–9` for rows and columns).
- Ships must be placed in a straight line (horizontal or vertical).
- Ships must consist of **consecutive cells** with no gaps.

### Overlap and Adjacency Rules
- Ships **cannot overlap**.
- Ships **cannot touch**, even diagonally.

This is enforced by checking all adjacent and diagonal cells around each ship coordinate.

If validation fails, the player is prompted to re-enter the entire fleet.

---

## Game State Management

### Boards

Each side maintains:
- **Visible board** (`player_board`, `bot_board`)
  - Tracks hits (`H`), misses (`M`), and unknown cells (`.`)
- **Hidden ship board**
  - Tracks actual ship positions (`S`) for hit detection

Boards are internally stored as 10×10 2D lists.

---

### Applying Moves

When a move is made:
1. The coordinate is checked for validity.
2. The board is updated with:
   - `H` for hit
   - `M` for miss
3. If all parts of a ship are hit, it is marked as **sunk**.
4. All surrounding cells of a sunk ship are automatically marked as misses (Battleship rule).

Players and bots receive an **extra shot** after a hit or sink.

---

## Displaying the Game State

Boards are printed to the terminal after each turn:

- **Player Board**
  - Shows ships (`S`), hits (`H`), and misses (`M`)
- **Bot Board**
  - Shows only hits and misses (ships are hidden)

Example header:
```

A B C D E F G H I J
1 . . . . . . . . . .
2 . S S S . . . . . .

```

Turn number and current player are displayed clearly.

---

## Bot AI Design

The bot uses a **state-based strategy**:

### 1. RANDOM
- Shoots randomly at untested cells.

### 2. HUNT
- Activated after a hit.
- Targets adjacent cells to find the rest of the ship.

### 3. LOCKED
- Activated after consecutive hits.
- Determines ship orientation (horizontal or vertical).
- Systematically attacks along that axis.

When a ship is sunk, the bot resets to RANDOM mode.

---

## Logging

Each turn is logged to a CSV file containing:
- Turn number
- Player move and result
- Bot move and result
- Serialized player board
- Serialized bot board

Boards are serialized into compact strings using:
- `.` for empty
- `H` for hit
- `M` for miss

This allows replay analysis or debugging.

---

## Design Decisions & Trade-offs

### Simplicity vs Performance
- The board is stored as simple 2D lists for clarity.
- Validation uses straightforward iteration instead of optimized spatial indexing.

### Input Flexibility
- Multiple input formats improve usability.
- Parsing logic is kept minimal and centralized.

### Bot AI Complexity
- The bot AI is deterministic and rule-based.
- This avoids randomness-heavy behavior while remaining understandable and debuggable.
- More advanced probability-based AI was intentionally avoided for clarity.

### Full Re-validation on Error
- If ship placement is invalid, the entire fleet is re-entered.
- This simplifies validation logic at the cost of user convenience.

---

## Conclusion

This project implements a complete Battleship game with:
- Robust input handling
- Strict rule validation
- Clear game state visualization
- A multi-mode bot AI
- Turn-by-turn logging

The focus was on correctness, readability, and maintainability rather than advanced optimization.