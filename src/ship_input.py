import csv
import os
from typing import List

from src.utils import (BOARD_SIZE, SHIP_SIZES, Ship, coords_to_str,
                       get_adjacent_and_diagonal_cells, in_bounds,
                       str_to_coords, validate_ship_fleet)


def prompt_ship_input(size: int, ship_index: int = 1) -> Ship:
    """
    Prompts the user to input the coordinates for a ship of a given size.
    The input should be in the format "A1 A2 A3" for a size 3 ship, for example.
    Returns a list of coordinates representing the ship.
    """
    while True:
        prompt = f"Enter coordinates for ship of size {size} (ship {ship_index}): "
        user_input = input(prompt).strip()

        # Try to handle both space-separated and dash-separated input
        try:
            # Handle space-separated coordinates, e.g., 'A1 A2 A3'
            if " " in user_input:
                ship_coords = [str_to_coords(coord)[0] for coord in user_input.split()]

            # Handle range format input, e.g., 'B4-B6'
            elif "-" in user_input:
                start, end = user_input.split("-")
                start_row, start_col = str_to_coords(start)[0]
                end_row, end_col = str_to_coords(end)[0]

                # Ensure the ship is straight (horizontal or vertical)
                if start_row == end_row:
                    step = (
                        1 if end_col >= start_col else -1
                    )  # (optional: allow reverse ranges)
                    ship_coords = [
                        (start_row, col)
                        for col in range(start_col, end_col + step, step)
                    ]
                elif start_col == end_col:
                    step = (
                        1 if end_row >= start_row else -1
                    )  # (optional: allow reverse ranges)
                    ship_coords = [
                        (row, start_col)
                        for row in range(start_row, end_row + step, step)
                    ]
                else:
                    raise ValueError("Ship must be either horizontal or vertical.")

            # Handle single coordinate input (for size 1 ship), e.g., 'B4' or 'A10'
            elif user_input and user_input[0].isalpha() and user_input[1:].isdigit():
                ship_coords = [str_to_coords(user_input)[0]]

            else:
                raise ValueError(
                    "Invalid input format. Please use space-separated or range format."
                )
        except Exception as e:
            print(f"Error: {e}. Please try again.")
            continue

        if not all(in_bounds(c) for c in ship_coords):
            print(
                f"Error: One or more coordinates are out of bounds. Use A1–J{BOARD_SIZE}. Please try again."
            )
            continue

        # Ensure the coordinates list matches the ship size
        if len(ship_coords) != size:
            print(
                f"Error: Expected {size} coordinates, but got {len(ship_coords)}. Please try again."
            )
            continue

        return ship_coords


def are_ships_adjacent(ships: List[Ship]) -> bool:
    """
    Checks if any ships are adjacent to each other, including diagonally.
    """
    for i, ship in enumerate(ships):
        for coord in ship:
            adjacent_cells = get_adjacent_and_diagonal_cells(coord)
            for other_ship in ships:
                if coord in other_ship:
                    continue  # Skip checking the ship itself
                if any(cell in other_ship for cell in adjacent_cells):
                    return True  # Ships are adjacent
    return False


def get_and_save_player_ships(csv_path: str = "data/player_ships.csv") -> List[Ship]:
    """
    Prompts the user for ship coordinates, validates the fleet, and saves the layout to a CSV file.
    """
    print(
        """
    Welcome to Battleship!

    You will place your ships on a 10x10 grid (A1-J10). You need to place:
    - 1 ship of size 4
    - 2 ships of size 3
    - 3 ships of size 2
    - 4 ships of size 1

    Ships cannot touch each other, even diagonally.
    """
    )

    ships = []
    ship_index = 1

    # Prompt user for ships of each required size
    for size in SHIP_SIZES:
        ship_coords = prompt_ship_input(size, ship_index)
        ships.append(ship_coords)
        ship_index += 1

    # Validate the fleet
    valid, error_message = validate_ship_fleet(ships)
    if not valid:
        print(f"Error: {error_message}. Please enter the ship positions again.")
        return get_and_save_player_ships(csv_path)  # Restart the process if invalid

    # Check for adjacency between ships
    if are_ships_adjacent(ships):
        print(
            "Error: Ships cannot touch each other, even diagonally. Please adjust the placements."
        )
        return get_and_save_player_ships(
            csv_path
        )  # Restart the process if ships are adjacent

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Save to CSV
    with open(csv_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ship_id", "size", "coordinates"])
        for ship_id, ship in enumerate(ships, start=1):
            writer.writerow([ship_id, len(ship), coords_to_str(ship)])

    return ships
