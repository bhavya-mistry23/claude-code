"""Demo of addition operations."""


def add_two_digits(a, b):
    """Return the sum of two numbers."""
    total = a + b
    return total


class Player:
    """Represents a player in a multiplayer math game."""

    def __init__(self, name, number1, number2):
        """Initialize player."""
        self.name = name
        self.number1 = number1
        self.number2 = number2
        self.results = {}

    def calculate(self):
        """Compute addition."""
        sum_result = add_two_digits(self.number1, self.number2)
        self.results["add"] = sum_result

    def display_results(self):
        """Show results."""
        print(f"\n{self.name}: {self.number1} + {self.number2} = {self.results['add']}")


def multiplayer_game(players):
    """
    Run a multiplayer math game where each player performs calculations.

    Args:
        players: A list of Player objects.
    """
    print("=" * 50)
    print("MULTIPLAYER MATH GAME (MODE 2)")
    print("=" * 50)

    for player in players:
        player.calculate()
        player.display_results()

    print("\n" + "=" * 50)
    print("Game Complete!")
    print("=" * 50)


def main():
    """Demo: add two numbers."""
    print("Single Player Mode:")
    digit1 = 10
    digit2 = 3
    add_result = add_two_digits(digit1, digit2)
    print(f"Result: {add_result}")

    # Multiplayer mode
    players = [
        Player("Player1", 10, 3),
        Player("Player2", 20, 5),
        Player("Player3", 15, 6),
    ]
    multiplayer_game(players)


if __name__ == "__main__":
    main()
