import os
import sys
import time

from src.bot_generation import generate_and_save_bot_ships
from src.gameplay import GameState, ask_player_for_move
from src.ship_input import get_and_save_player_ships
from src.utils import coord_to_human, log_turn_sequence


def main():
    # Ensure necessary directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    # Step 1: Get and save player ships
    print("Welcome to Battleship!")
    player_ships = get_and_save_player_ships(csv_path="data/player_ships.csv")

    # Step 2: Generate and save bot ships
    bot_ships = generate_and_save_bot_ships(csv_path="data/bot_ships.csv")

    # Step 3: Initialize the game state
    game_state = GameState.from_fleets(player_ships, bot_ships)

    # Step 4: Game loop
    try:
        while True:
            # Print the current boards
            game_state.print_boards()

            # Track moves for this turn sequence
            player_moves_in_turn = []
            bot_moves_in_turn = []

            if game_state.current_turn == "player":
                # Player's turn sequence
                print("\n=== Player's Turn ===")
                while game_state.current_turn == "player":
                    player_move = ask_player_for_move(game_state)
                    coord, result = game_state.player_take_turn(player_move)
                    player_moves_in_turn.append((coord, result))

                    print(f"Your move result: {result}")

                    # Check if the player wins
                    if game_state.all_bot_ships_sunk():
                        print("\n" + "=" * 50)
                        print("Congratulations! You sank all the bot's ships! You win!")
                        print("=" * 50)

                        # Log the turn sequence
                        log_turn_sequence(
                            game_state,
                            "data/game_state.csv",
                            player_moves_in_turn,
                            bot_moves_in_turn,
                        )
                        return

                    # Check if player gets another shot
                    if not game_state.player_gets_extra_shot:
                        game_state.next_turn()  # Switch to bot if no extra shot
                        break
                    print("You hit! You get another shot!")
                    time.sleep(0.5)  # Short pause between shots

            else:
                # Bot's turn sequence
                print("\n=== Bot's Turn ===")
                while game_state.current_turn == "bot":
                    bot_move, bot_result = game_state.bot_take_turn()
                    bot_moves_in_turn.append((bot_move, bot_result))
                    bot_move_human = coord_to_human(bot_move)
                    print(f"Bot's move: {bot_move_human} - Result: {bot_result}")

                    # Check if the bot wins
                    if game_state.all_player_ships_sunk():
                        print("\n" + "=" * 50)
                        print("Game Over. The bot sank all your ships. You lose!")
                        print("=" * 50)

                        # Log the turn sequence
                        log_turn_sequence(
                            game_state,
                            "data/game_state.csv",
                            player_moves_in_turn,
                            bot_moves_in_turn,
                        )
                        return

                    # Check if bot gets another shot
                    if not game_state.bot_gets_extra_shot:
                        game_state.next_turn()  # Switch to player if no extra shot
                        break
                    print("Bot hit! Bot gets another shot!")
                    time.sleep(1)  # Pause so player can see bot's moves

            # Log the turn sequence
            log_turn_sequence(
                game_state,
                "data/game_state.csv",
                player_moves_in_turn,
                bot_moves_in_turn,
            )

    except KeyboardInterrupt:
        print("\nGame interrupted. Exiting gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
