"""Demo of addition operations."""


def add_two_digits(a, b):
    """Return the sum of a and b."""
    result = a + b
    return result


class Player:
    """Represents a player in a multiplayer math game."""

    def __init__(self, name, number1, number2):
        """Initialize player with name and two numbers."""
        self.name = name
        self.number1 = number1
        self.number2 = number2
        self.results = {}

    def calculate(self):
        """Calculate addition for player's numbers."""
        self.results["add"] = add_two_digits(self.number1, self.number2)

    def display_results(self):
        """Display player's calculation results."""
        print(f"\n--- {self.name}'s Results ---")
        print(f"Numbers: {self.number1} and {self.number2}")
        print(f"Addition: {self.results['add']}")


def multiplayer_game(players):
    """
    Run a multiplayer math game where each player performs calculations.

    Args:
        players: A list of Player objects.
    """
    print("=" * 50)
    print("MULTIPLAYER MATH GAME")
    print("=" * 50)

    for player in players:
        player.calculate()
        player.display_results()

    print("\n" + "=" * 50)
    print("Game Complete!")
    print("=" * 50)


def main():
    """
    Add two numbers in single and multiplayer modes.

    Runs both a single-player demo and a multiplayer game.
    """
    print("Single Player Mode:")
    digit1 = 5
    digit2 = 3
    add_result = add_two_digits(digit1, digit2)
    print(f"Addition of {digit1} and {digit2} is: {add_result}")

    # Multiplayer mode
    players = [
        Player("Alice", 5, 3),
        Player("Bob", 10, 2),
        Player("Charlie", 8, 4),
    ]
    multiplayer_game(players)


# Check if this file is run directly
if __name__ == "__main__":
    main()
