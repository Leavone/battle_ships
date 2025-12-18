import csv
import os
import random
from typing import List

from src.utils import (BOARD_SIZE, SHIP_SIZES, Ship, coords_to_str, in_bounds,
                       ships_touch_or_overlap, validate_ship_fleet)


def get_random_orientation() -> str:
    """
    Randomly returns either 'horizontal' or 'vertical' as ship orientation.
    """
    return random.choice(["horizontal", "vertical"])


def generate_ship(size: int) -> Ship:
    """
    Randomly generates a single ship of a given size, either horizontal or vertical.
    The ship is placed randomly on the board ensuring it's fully in bounds.
    """
    while True:
        orientation = get_random_orientation()

        if orientation == "horizontal":
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - size)
            ship = [(row, col + i) for i in range(size)]
        else:
            row = random.randint(0, BOARD_SIZE - size)
            col = random.randint(0, BOARD_SIZE - 1)
            ship = [(row + i, col) for i in range(size)]

        # Check if the ship is placed within the board and is valid (no overlap or touching)
        if all(in_bounds(coord) for coord in ship) and not ships_touch_or_overlap(
            [ship]
        ):
            return ship


def generate_bot_ships() -> List[Ship]:
    """
    Randomly generates a valid fleet of ships based on the SHIP_SIZES configuration.
    It ensures that ships are not overlapping or touching.
    """
    ships = []

    # Keep generating ships until a valid configuration is found
    while True:
        ships.clear()  # Reset ships list

        # Generate ships for each size in SHIP_SIZES
        for size in SHIP_SIZES:
            ships.append(generate_ship(size))

        # Validate the generated fleet
        valid, _ = validate_ship_fleet(ships)
        if valid:
            break  # Valid fleet, stop generating

    return ships


def generate_and_save_bot_ships(csv_path: str = "data/bot_ships.csv") -> List[Ship]:
    """
    Generates a valid bot fleet, saves it to a CSV file, and returns the list of ships.
    """
    # Generate a valid bot fleet
    ships = generate_bot_ships()

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Save to CSV
    with open(csv_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ship_id", "size", "coordinates"])
        for ship_id, ship in enumerate(ships, start=1):
            writer.writerow([ship_id, len(ship), coords_to_str(ship)])

    return ships
