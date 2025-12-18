import csv
import os
import random
from typing import List, Optional, Tuple

from src.utils import (BOARD_SIZE, Coord, Ship, coords_to_str,
                       get_adjacent_and_diagonal_cells, in_bounds)


class GameState:
    """
    Represents the current state of the game, including the player and bot fleets, boards, and turn number.
    Tracks hits, misses, and ship destruction status.
    """

    RANDOM = "random"
    HUNT = "hunt"
    LOCKED = "locked"

    def __init__(self, player_ships: List[Ship], bot_ships: List[Ship]):
        self.turn_number = 0
        self.player_ships = player_ships  # List[List[Coord]]
        self.bot_ships = bot_ships  # List[List[Coord]]

        # Initialize both boards with empty spaces
        self.player_board = [
            [" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
        ]
        self.bot_board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        # Create boards showing ship positions
        self.player_board_ships = self.create_ship_board(player_ships)
        self.bot_board_ships = self.create_ship_board(bot_ships)

        # Bot AI state
        self.bot_mode = GameState.RANDOM
        self.bot_hit_chain = []
        self.bot_last_hit: Optional[Coord] = None
        self.bot_orientation = None

        # Track whose turn it is and if they get another shot
        self.current_turn = "player"  # 'player' or 'bot'
        self.player_gets_extra_shot = False
        self.bot_gets_extra_shot = False

    @staticmethod
    def from_fleets(player_fleet: List[Ship], bot_fleet: List[Ship]) -> "GameState":
        """
        Creates a GameState instance from player and bot fleets.
        """
        return GameState(player_fleet, bot_fleet)

    def create_ship_board(self, ships: List[Ship]) -> List[List[str]]:
        """
        Creates a board with ships placed. This is used internally and does not affect game state board.
        The board will be filled with 'S' for ship positions.
        """
        board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for ship in ships:  # ship is List[Coord]
            for row, col in ship:  # Directly iterate over coordinates
                if in_bounds((row, col)):
                    board[row][col] = "S"
        return board

    def apply_move(
        self,
        board: List[List[str]],
        ship_board: List[List[str]],
        ships: List[Ship],
        coord: Coord,
    ) -> Tuple[str, bool]:
        """
        Applies a move to the given board, checking if it's a hit, miss, or sink.
        Returns a tuple: (result, ship_destroyed) where result is 'hit', 'miss', or 'sink',
        and ship_destroyed is a boolean indicating whether a ship was completely destroyed.
        """
        row, col = coord
        if not in_bounds(coord):
            return "invalid", False

        # Check if this cell has already been attacked
        if board[row][col] in ["M", "H"]:
            return "invalid", False

        if ship_board[row][col] == "S":
            board[row][col] = "H"  # Hit
            ship_destroyed = self.check_if_ship_sunk(coord, ships, board)
            if ship_destroyed:
                # Mark surrounding cells of the destroyed ship as misses
                self.mark_surrounding_cells_as_miss(coord, ships, board)
                return "sink", True
            return "hit", False
        board[row][col] = "M"  # Miss
        return "miss", False

    def apply_player_move(self, coord: Coord) -> Tuple[str, bool]:
        """
        Applies a move for the player on the bot's board and returns the result.
        """
        return self.apply_move(
            self.bot_board, self.bot_board_ships, self.bot_ships, coord
        )

    def apply_bot_move(self, coord: Coord) -> Tuple[str, bool]:
        """
        Applies a move for the bot on the player's board and returns the result.
        """
        return self.apply_move(
            self.player_board, self.player_board_ships, self.player_ships, coord
        )

    def check_if_ship_sunk(
        self, coord: Coord, ships: List[Ship], board: List[List[str]]
    ) -> bool:
        """
        Checks if a ship has been completely sunk (all parts of it hit).
        """
        for ship in ships:  # ship is List[Coord]
            # Check if this ship contains the hit coordinate
            if any((row, col) == coord for (row, col) in ship):
                # Check if all coordinates of this ship are hit
                if all(board[row][col] == "H" for (row, col) in ship):
                    return True
        return False

    def mark_surrounding_cells_as_miss(
        self, coord: Coord, ships: List[Ship], board: List[List[str]]
    ) -> None:
        """
        Marks the surrounding cells of a destroyed ship as miss.
        This includes all adjacent and diagonal cells of the ship's coordinates.
        """
        for ship in ships:  # ship is List[Coord]
            # Find the ship that contains the coordinate
            if any((row, col) == coord for (row, col) in ship):
                # Check if this entire ship is sunk
                if all(board[row][col] == "H" for (row, col) in ship):
                    # Mark all surrounding cells of this ship as misses
                    ship_cells = set()
                    for row, col in ship:
                        adjacent_cells = get_adjacent_and_diagonal_cells((row, col))
                        for r, c in adjacent_cells:
                            if in_bounds((r, c)):
                                ship_cells.add((r, c))

                    # Mark ship's own cells as 'H' and surrounding as 'M'
                    for r, c in ship_cells:
                        if board[r][c] == " ":
                            board[r][c] = "M"
                break

    def all_player_ships_sunk(self) -> bool:
        """
        Returns True if all player ships have been sunk.
        """
        for ship in self.player_ships:  # ship is List[Coord]
            if not all(self.player_board[row][col] == "H" for (row, col) in ship):
                return False
        return True

    def all_bot_ships_sunk(self) -> bool:
        """
        Returns True if all bot ships have been sunk.
        """
        for ship in self.bot_ships:  # ship is List[Coord]
            if not all(self.bot_board[row][col] == "H" for (row, col) in ship):
                return False
        return True

    def serialize_board(self, board: List[List[str]]) -> str:
        """
        Serializes a 10x10 game board into a string for storage in CSV.
        """
        return "".join(
            "".join(cell if cell != " " else "." for cell in row) for row in board
        )

    def log_turn(
        self,
        csv_path: str,
        player_move_info: Tuple[Coord, str],
        bot_move_info: Tuple[Coord, str],
    ) -> None:
        """
        Logs the current turn to a CSV file, including move details and serialized board states.
        """
        player_move_coord, player_move_result = player_move_info
        bot_move_coord, bot_move_result = bot_move_info

        player_board_serialized = self.serialize_board(self.player_board)
        bot_board_serialized = self.serialize_board(self.bot_board)

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
            writer.writerow(
                [
                    self.turn_number,
                    coords_to_str(player_move_coord),
                    player_move_result,
                    coords_to_str(bot_move_coord),
                    bot_move_result,
                    player_board_serialized,
                    bot_board_serialized,
                ]
            )

    def next_turn(self):
        """Increment the turn number and switch to the other player."""
        # Only increment turn number when switching between players
        if not (self.player_gets_extra_shot or self.bot_gets_extra_shot):
            self.turn_number += 1

        # Switch turns unless someone gets an extra shot
        if self.player_gets_extra_shot:
            self.current_turn = "player"
        elif self.bot_gets_extra_shot:
            self.current_turn = "bot"
        else:
            # Normal turn switching
            self.current_turn = "bot" if self.current_turn == "player" else "player"

    def print_boards(self) -> None:
        """
        Prints both the player and bot boards to the terminal.
        The player's board shows hits/misses/ships, while the bot's board shows hits/misses only.
        """
        print("\n" + "=" * 50)
        print(
            f"Turn: {self.turn_number + 1}"
        )  # Show human-friendly turn number (1-based)
        print(f"Current Player: {'Player' if self.current_turn == 'player' else 'Bot'}")
        print("=" * 50)

        print("\nPlayer's Board (Your ships):")
        self.print_board(self.player_board, is_player_board=True)

        print("\nBot's Board (Your attacks):")
        self.print_board(self.bot_board, is_player_board=False)

    def print_board(self, board: List[List[str]], is_player_board: bool = True) -> None:
        """
        Helper function to print a single board with labels.
        """
        print("   A B C D E F G H I J")
        for i in range(BOARD_SIZE):
            # Create a display row
            display_row = []
            for j in range(BOARD_SIZE):
                cell = board[i][j]
                if cell == " ":
                    if is_player_board:
                        # Check if there's a ship at this position on player's board
                        if self.player_board_ships[i][j] == "S":
                            display_row.append("S")
                        else:
                            display_row.append(".")
                    else:
                        display_row.append(".")
                else:
                    display_row.append(cell)
            print(f"{i+1:2} {' '.join(display_row)}")

    def choose_bot_move(self) -> Coord:
        """
        Determines the bot's next move based on its current strategy:
        random, hunt (after a hit), or locked (after consecutive hits).
        """
        if self.bot_mode == GameState.RANDOM:
            return self.choose_random_move()
        elif self.bot_mode == GameState.HUNT:
            return self.choose_hunt_move()
        elif self.bot_mode == GameState.LOCKED:
            return self.choose_locked_move()
        else:
            return self.choose_random_move()

    def choose_random_move(self) -> Coord:
        """
        Chooses a random untested coordinate.
        """
        available_moves = [
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if self.player_board[r][c] == " "
        ]
        if not available_moves:
            # If no available moves (shouldn't happen in valid game), return any coordinate
            return (
                random.randint(0, BOARD_SIZE - 1),
                random.randint(0, BOARD_SIZE - 1),
            )
        return random.choice(available_moves)

    def choose_hunt_move(self) -> Coord:
        """
        Chooses an adjacent untested cell after a successful hit.
        Prioritizes cells that could continue the ship based on orientation.
        """
        if not self.bot_last_hit:
            self.bot_mode = GameState.RANDOM
            return self.choose_random_move()

        row, col = self.bot_last_hit

        # If we have an orientation hint, prioritize that direction
        if self.bot_orientation == "horizontal":
            # Try left and right first
            directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # Left, Right, Up, Down
        elif self.bot_orientation == "vertical":
            # Try up and down first
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        else:
            # No orientation yet, try all 4 cardinal directions
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right

        # Try each direction
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if (
                in_bounds((new_row, new_col))
                and self.player_board[new_row][new_col] == " "
            ):
                return (new_row, new_col)

        # If no adjacent cells available, try hunting around other hits in the chain
        for hit in self.bot_hit_chain:
            if hit != self.bot_last_hit:
                row, col = hit
                for dr, dc in directions:
                    new_row, new_col = row + dr, col + dc
                    if (
                        in_bounds((new_row, new_col))
                        and self.player_board[new_row][new_col] == " "
                    ):
                        self.bot_last_hit = hit  # Update last hit
                        return (new_row, new_col)

        # If still nothing, go back to random
        self.bot_mode = GameState.RANDOM
        self.bot_hit_chain = []
        self.bot_last_hit = None
        self.bot_orientation = None
        return self.choose_random_move()

    def choose_locked_move(self) -> Coord:
        """
        Chooses a move based on the locked axis after two consecutive hits.
        When in LOCKED mode, systematically search along the determined orientation.
        """
        if not self.bot_hit_chain or len(self.bot_hit_chain) < 2:
            self.bot_mode = GameState.HUNT
            return self.choose_hunt_move()

        # Sort hits for consistent ordering
        sorted_hits = sorted(self.bot_hit_chain)

        if self.bot_orientation == "horizontal":
            return self.choose_locked_horizontal_move(sorted_hits)
        elif self.bot_orientation == "vertical":
            return self.choose_locked_vertical_move(sorted_hits)
        else:
            # Try to infer orientation
            self.infer_orientation()
            if self.bot_orientation:
                return self.choose_locked_move()
            else:
                self.bot_mode = GameState.HUNT
                return self.choose_hunt_move()

    def choose_locked_horizontal_move(self, sorted_hits: List[Coord]) -> Coord:
        """
        Chooses a move along the horizontal line where the bot got consecutive hits.
        """
        row = sorted_hits[0][0]
        left_col = min(hit[1] for hit in sorted_hits)
        right_col = max(hit[1] for hit in sorted_hits)

        # Try left side first (most natural progression)
        for offset in range(1, 5):  # Check up to 4 cells to the left
            col = left_col - offset
            if col >= 0 and self.player_board[row][col] == " ":
                return (row, col)
            elif col < 0:
                break

        # Try right side
        for offset in range(1, 5):  # Check up to 4 cells to the right
            col = right_col + offset
            if col < BOARD_SIZE and self.player_board[row][col] == " ":
                return (row, col)
            elif col >= BOARD_SIZE:
                break

        # Check for gaps between hits
        for i in range(len(sorted_hits) - 1):
            current = sorted_hits[i]
            next_hit = sorted_hits[i + 1]
            if next_hit[1] - current[1] > 1:
                # There's a gap between hits
                for col in range(current[1] + 1, next_hit[1]):
                    if self.player_board[row][col] == " ":
                        return (row, col)

        # If nothing found, go back to hunt mode
        self.bot_mode = GameState.HUNT
        return self.choose_hunt_move()

    def choose_locked_vertical_move(self, sorted_hits: List[Coord]) -> Coord:
        """
        Chooses a move along the vertical line where the bot got consecutive hits.
        """
        col = sorted_hits[0][1]
        top_row = min(hit[0] for hit in sorted_hits)
        bottom_row = max(hit[0] for hit in sorted_hits)

        # Try above first
        for offset in range(1, 5):  # Check up to 4 cells above
            row = top_row - offset
            if row >= 0 and self.player_board[row][col] == " ":
                return (row, col)
            elif row < 0:
                break

        # Try below
        for offset in range(1, 5):  # Check up to 4 cells below
            row = bottom_row + offset
            if row < BOARD_SIZE and self.player_board[row][col] == " ":
                return (row, col)
            elif row >= BOARD_SIZE:
                break

        # Check for gaps between hits
        for i in range(len(sorted_hits) - 1):
            current = sorted_hits[i]
            next_hit = sorted_hits[i + 1]
            if next_hit[0] - current[0] > 1:
                # There's a gap between hits
                for row in range(current[0] + 1, next_hit[0]):
                    if self.player_board[row][col] == " ":
                        return (row, col)

        # If nothing found, go back to hunt mode
        self.bot_mode = GameState.HUNT
        return self.choose_hunt_move()

    def bot_take_turn(self) -> Tuple[Coord, str]:
        """
        Makes the bot's move, applies it, updates the AI state, and returns the result.
        """
        bot_move = self.choose_bot_move()
        bot_result, ship_destroyed = self.apply_bot_move(bot_move)

        # Update bot state based on the result
        if bot_result == "hit" or bot_result == "sink":
            # Bot gets another shot next turn
            self.bot_gets_extra_shot = True

            if bot_result == "sink":
                # Ship sunk! Clear all tracking for this ship
                self.bot_hit_chain = []
                self.bot_last_hit = None
                self.bot_orientation = None
                # Even though ship is sunk, bot still gets another shot
        else:
            # Bot missed, no extra shot
            self.bot_gets_extra_shot = False

        # Update bot AI state (only for hits)
        if bot_result == "hit":
            if not self.bot_hit_chain:
                # First hit on a ship - enter HUNT mode
                self.bot_hit_chain = [bot_move]
                self.bot_last_hit = bot_move
                self.bot_mode = GameState.HUNT
            else:
                # Check if this hit is adjacent to our hit chain (same ship)
                is_same_ship = False
                for hit in self.bot_hit_chain:
                    if (abs(hit[0] - bot_move[0]) == 1 and hit[1] == bot_move[1]) or (
                        abs(hit[1] - bot_move[1]) == 1 and hit[0] == bot_move[0]
                    ):
                        is_same_ship = True
                        break

                if is_same_ship and bot_move not in self.bot_hit_chain:
                    # Additional hit on the same ship
                    self.bot_hit_chain.append(bot_move)
                    self.bot_last_hit = bot_move

                    # If we have at least 2 hits, try to determine orientation
                    if len(self.bot_hit_chain) >= 2:
                        self.infer_orientation()

                        if self.bot_orientation:
                            self.bot_mode = GameState.LOCKED
                else:
                    # This is likely a hit on a different ship
                    # Start fresh with this new hit
                    self.bot_hit_chain = [bot_move]
                    self.bot_last_hit = bot_move
                    self.bot_mode = GameState.HUNT
                    self.bot_orientation = None

        elif bot_result == "sink":
            # Already handled above, but clear tracking
            self.bot_hit_chain = []
            self.bot_last_hit = None
            self.bot_orientation = None
            self.bot_mode = GameState.RANDOM

        elif bot_result == "miss":
            # If we miss while hunting with multiple hits, check if we should switch to locked
            if self.bot_mode == GameState.HUNT and len(self.bot_hit_chain) >= 2:
                self.infer_orientation()
                if self.bot_orientation:
                    self.bot_mode = GameState.LOCKED

        return bot_move, bot_result

    def player_take_turn(self, coord: Coord) -> Tuple[Coord, str]:
        """
        Makes the player's move, applies it, and returns the result.
        Also sets whether the player gets an extra shot.
        """
        result, ship_destroyed = self.apply_player_move(coord)

        # Update extra shot status
        if result == "hit" or result == "sink":
            self.player_gets_extra_shot = True
        else:
            self.player_gets_extra_shot = False

        return coord, result

    def infer_orientation(self):
        """
        Infers the ship's orientation after at least two consecutive hits.
        """
        if len(self.bot_hit_chain) < 2:
            return

        # Sort hits
        sorted_hits = sorted(self.bot_hit_chain)

        # Check if all hits are in the same row (horizontal)
        if all(hit[0] == sorted_hits[0][0] for hit in sorted_hits):
            self.bot_orientation = "horizontal"
        # Check if all hits are in the same column (vertical)
        elif all(hit[1] == sorted_hits[0][1] for hit in sorted_hits):
            self.bot_orientation = "vertical"
        else:
            # Can't determine orientation
            self.bot_orientation = None


def ask_player_for_move(game_state: GameState) -> Coord:
    """
    Prompts the player for a move input, validates the input, and ensures the player doesn't shoot the same cell twice.
    Returns the valid move coordinate.
    """
    while True:
        move = input("Enter your move (e.g., A1, B2, etc.): ").strip().upper()

        if len(move) < 2 or len(move) > 3:
            print("Invalid input format. Please use coordinates like A1, B2, etc.")
            continue

        # Parse column (letter) and row (number)
        if move[0].isalpha() and move[1:].isdigit():
            col = ord(move[0]) - ord("A")
            row = int(move[1:]) - 1

            if 0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE:
                if game_state.bot_board[row][col] == " ":
                    return (row, col)
                else:
                    print("You've already attacked this spot. Try again.")
            else:
                print(
                    f"Out of bounds. Please choose coordinates within A1–J{BOARD_SIZE}."
                )
        else:
            print("Invalid format. Column should be A-J, row should be 1-10.")
