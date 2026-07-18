class TictactoeException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class Board:
    valid_moves = [
        "upper left",
        "upper center",
        "upper right",
        "middle left",
        "center",
        "middle right",
        "lower left",
        "lower center",
        "lower right",
    ]

    winning_lines = (
        ((0, 0), (0, 1), (0, 2)),
        ((1, 0), (1, 1), (1, 2)),
        ((2, 0), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 1), (1, 1), (2, 1)),
        ((0, 2), (1, 2), (2, 2)),
        ((0, 0), (1, 1), (2, 2)),
        ((0, 2), (1, 1), (2, 0)),
    )

    def __init__(self):
        self.board_array = [
            [" ", " ", " "],
            [" ", " ", " "],
            [" ", " ", " "],
        ]
        self.turn = "X"
        self.last_move = None

    def __str__(self):
        lines = []
        lines.append(f" {self.board_array[0][0]} | {self.board_array[0][1]} | {self.board_array[0][2]} \n")
        lines.append("-----------\n")
        lines.append(f" {self.board_array[1][0]} | {self.board_array[1][1]} | {self.board_array[1][2]} \n")
        lines.append("-----------\n")
        lines.append(f" {self.board_array[2][0]} | {self.board_array[2][1]} | {self.board_array[2][2]} \n")
        return "".join(lines)

    def move(self, move_string):
        if move_string not in Board.valid_moves:
            raise TictactoeException("That's not a valid move.")

        move_index = Board.valid_moves.index(move_string)
        row = move_index // 3
        column = move_index % 3

        if self.board_array[row][column] != " ":
            raise TictactoeException("That spot is taken.")

        self.board_array[row][column] = self.turn
        self.last_move = (row, column, self.turn)
        self.turn = "O" if self.turn == "X" else "X"

    def _winner(self):
        for line in Board.winning_lines:
            values = [
                self.board_array[row][column]
                for row, column in line
            ]

            if values[0] != " " and values[0] == values[1] == values[2]:
                return values[0]

        return None

    def _is_full(self):
        return all(
            cell != " "
            for row in self.board_array
            for cell in row
        )

    def whats_next(self):
        winner = self._winner()

        if winner is not None:
            return (True, f"{winner} has won")

        if self._is_full():
            return (True, "Cat's Game")

        return (False, f"{self.turn}'s turn")


def play_game():
    board = Board()
    game_over, message = board.whats_next()

    while not game_over:
        print(board)
        move_string = input(f"{message}. Enter move: ")

        try:
            board.move(move_string)
        except TictactoeException as error:
            print(error.message)

        game_over, message = board.whats_next()

    print(board)
    print(message)


if __name__ == "__main__":
    play_game()
