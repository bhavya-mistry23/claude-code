"""Demo of addition, subtraction, multiplication, and division operations."""


def add_two_digits(a, b):
    """Return the sum of a and b."""
    return a + b


def subtract_two_digits(a, b):
    """Return the difference of a minus b."""
    return a - b


def multiply_two_digits(a, b):
    """Return the product of a and b."""
    return a * b


def divide_two_digits(a, b):
    """Return the quotient of a divided by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


class Player:
    """Represents a player in a multiplayer math game."""

    def __init__(self, name, number1, number2):
        """
        Initialize a player with a name and two numbers.

        Args:
            name: The player's name.
            number1: The player's first number.
            number2: The player's second number.
        """
        self.name = name
        self.number1 = number1
        self.number2 = number2
        self.results = {}

    def calculate(self):
        """
        Calculate addition, subtraction, multiplication, and division for this player's numbers.

        Stores results in the player's results dictionary.
        """
        self.results["add"] = add_two_digits(self.number1, self.number2)
        self.results["subtract"] = subtract_two_digits(self.number1, self.number2)
        self.results["multiply"] = multiply_two_digits(self.number1, self.number2)
        try:
            self.results["divide"] = divide_two_digits(self.number1, self.number2)
        except ValueError as e:
            self.results["divide"] = str(e)

    def display_results(self):
        """Display this player's calculation results."""
        print(f"\n--- {self.name}'s Results ---")
        print(
            f"Numbers: {self.number1} and {self.number2}"
        )
        print(f"Addition: {self.results['add']}")
        print(f"Subtraction: {self.results['subtract']}")
        print(f"Multiplication: {self.results['multiply']}")
        print(f"Division: {self.results['divide']}")


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
    Add, subtract, multiply, and divide two numbers in single and multiplayer modes.

    Runs both a single-player demo and a multiplayer game.
    """
    print("Single Player Mode:")
    digit1 = 5
    digit2 = 3
    add_result = add_two_digits(digit1, digit2)
    print(f"Addition of {digit1} and {digit2} is: {add_result}")
    sub_result = subtract_two_digits(digit1, digit2)
    print(f"Subtraction of {digit1} and {digit2} is: {sub_result}")
    multiply_result = multiply_two_digits(digit1, digit2)
    print(f"Multiplication of {digit1} and {digit2} is: {multiply_result}")
    divide_result = divide_two_digits(digit1, digit2)
    print(f"Division of {digit1} and {digit2} is: {divide_result}")

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
