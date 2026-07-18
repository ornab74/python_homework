from collections.abc import Callable


def make_hangman(secret_word: str) -> Callable[[str], bool]:
    secret_word = secret_word.strip()

    if not secret_word:
        raise ValueError("Secret word cannot be blank.")

    guesses: list[str] = []

    def hangman_closure(letter: str) -> bool:
        letter = letter.strip().lower()

        if not letter:
            print("Guess cannot be blank.")
            return False

        guesses.append(letter[0])

        display = "".join(
            character if not character.isalpha() or character.lower() in guesses else "_"
            for character in secret_word
        )

        print(display)

        return all(
            not character.isalpha() or character.lower() in guesses
            for character in secret_word
        )

    return hangman_closure


def play_hangman():
    secret_word = input("Secret word: ").strip()

    try:
        game = make_hangman(secret_word)
    except ValueError as error:
        print(error)
        return

    solved = False

    while not solved:
        guess = input("Guess a letter: ")
        solved = game(guess)

    print("You guessed the word!")


if __name__ == "__main__":
    play_hangman()