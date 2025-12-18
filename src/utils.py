import csv
import os
from typing import List, Tuple

# Constants
BOARD_SIZE = 10
SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

# Coordinate type alias
Coord = Tuple[int, int]

# Ship type alias
Ship = List[Coord]


def coords_to_str(ship) -> str:
    """
    Converts a list of coordinates (or a single coordinate) to a string representation.
    """
    # Check if the input is a single coordinate (tuple)
    if isinstance(ship, tuple):
        return f"{chr(ship[1] + 65)}{ship[0] + 1}"

    # Otherwise, assume it's a list of coordinates (for a ship)
    return ",".join([f"{chr(c[1] + 65)}{c[0] + 1}" for c in ship])


def str_to_coords(s: str) -> Ship:
    """
    Converts a string representation (e.g., 'A1,A2,A3') to a list of coordinates.
    """
    coords = []
    for cell in s.split(","):
        cell = cell.strip()
        row = int(cell[1:]) - 1  # <-- changed: take ALL digits after the letter
        col = ord(cell[0].upper()) - 65
        coords.append((row, col))
    return coords


# Board validation helpers
def in_bounds(coord: Coord) -> bool:
    """
    Checks if a coordinate is within the bounds of the board (0 <= row, col < 10).
    """
    return 0 <= coord[0] < BOARD_SIZE and 0 <= coord[1] < BOARD_SIZE


def get_adjacent_and_diagonal_cells(coord: Coord) -> List[Coord]:
    """
    Returns a list of adjacent and diagonal cells around a given coordinate.
    """
    row, col = coord
    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),  # Up, Down, Left, Right
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ]  # Diagonals
    return [
        (row + dr, col + dc) for dr, dc in directions if in_bounds((row + dr, col + dc))
    ]


# Ship validation helpers
def ships_touch_or_overlap(ships: List[Ship]) -> bool:
    """
    Checks if any ships overlap or touch (including diagonally).
    """
    for ship in ships:
        for coord in ship:
            # Check for overlap/touching with other ships
            for other_ship in ships:
                if coord in other_ship:
                    continue  # Skip checking the ship itself
                adjacent_cells = get_adjacent_and_diagonal_cells(coord)
                if any(cell in other_ship for cell in adjacent_cells):
                    return True
    return False


def validate_ship_fleet(ships: List[Ship]) -> Tuple[bool, str | None]:
    """
    Validates a fleet of ships:
    - All coordinates are in bounds.
    - Ships are straight lines (horizontal or vertical).
    - Fleet sizes match SHIP_SIZES (exact multiset of lengths).
    - Ships do not touch or overlap.
    """
    # Validate ship sizes
    if sorted([len(ship) for ship in ships]) != sorted(SHIP_SIZES):
        return False, "Fleet sizes do not match required configuration."

    # Validate coordinates and ships' validity
    for ship in ships:
        if not all(in_bounds(coord) for coord in ship):
            return False, "Ship coordinates out of bounds."

        # Check if the ship is a straight line (horizontal or vertical)
        rows = [coord[0] for coord in ship]
        cols = [coord[1] for coord in ship]

        if not (all(r == rows[0] for r in rows) or all(c == cols[0] for c in cols)):
            return False, "Ship is not a straight line."

        # Ensure ship consists of consecutive cells with no gaps
        if sorted(rows) != list(range(min(rows), max(rows) + 1)) and sorted(
            cols
        ) != list(range(min(cols), max(cols) + 1)):
            return False, "Ship has gaps in its placement."

    # Check if ships touch or overlap
    if ships_touch_or_overlap(ships):
        return False, "Ships cannot touch or overlap."

    return True, None


def coord_to_human(coord: Coord) -> str:
    """Convert (row, col) coordinates to human-readable format like A1."""
    row, col = coord
    return f"{chr(col + ord('A'))}{row + 1}"


def log_turn_sequence(game_state, csv_path, player_moves, bot_moves):
    """
    Logs a sequence of moves that happened in a turn.
    player_moves: list of (coord, result) tuples
    bot_moves: list of (coord, result) tuples
    """
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Write to CSV
    with open(csv_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        if file.tell() == 0:  # If file is empty, write the header
            writer.writerow(
                [
                    "turn_number",
                    "player_move_coord",
                    "player_move_result",
                    "bot_move_coord",
                    "bot_move_result",
                    "player_board_serialized",
                    "bot_board_serialized",
                ]
            )

        # Log all moves in this turn
        max_moves = max(len(player_moves), len(bot_moves))
        for i in range(max_moves):
            player_move = player_moves[i] if i < len(player_moves) else (None, None)
            bot_move = bot_moves[i] if i < len(bot_moves) else (None, None)

            player_move_coord, player_move_result = player_move
            bot_move_coord, bot_move_result = bot_move

            player_board_serialized = game_state.serialize_board(
                game_state.player_board
            )
            bot_board_serialized = game_state.serialize_board(game_state.bot_board)

            writer.writerow(
                [
                    game_state.turn_number,
                    coords_to_str(player_move_coord) if player_move_coord else "",
                    player_move_result or "",
                    coords_to_str(bot_move_coord) if bot_move_coord else "",
                    bot_move_result or "",
                    player_board_serialized,
                    bot_board_serialized,
                ]
            )
