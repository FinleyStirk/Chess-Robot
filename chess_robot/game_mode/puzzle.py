import random
import json

from .base import GameMode
from chess_robot.board.robot_board import RobotBoard
from chess_robot.utils.structs import Puzzle, CommandType, RobotCommand
from chess_robot.input_method import Input


class PuzzleRush(GameMode):

    def __init__(self, board: RobotBoard, player_input: Input, puzzle_file_path: str, rating_lower_bound: float = 0, rating_upper_bound: float = float('inf')):
        super().__init__(board)
        self._player_input = player_input
        self._puzzle_file_path = puzzle_file_path
        self._lower_bound = rating_lower_bound
        self._upper_bound = rating_upper_bound

        self._is_player_turn = True

        self._start_new_puzzle()

    def player_move(self) -> None:
        move = self._player_input.get_command()
        correct_move = self._puzzle.solution[self._move_number]

        if move.command != CommandType.MOVE:
            raise Exception("Entry must be a move")
        self.execute_command(move)
        
        if move.data == correct_move:
            self._is_player_turn = False
            self._move_number += 1
            
            if self._move_number == self._puzzle.length:
                self._start_new_puzzle()
        else:
            self.execute_command(RobotCommand.undo())

    def opponent_move(self):
        if self._is_player_turn:
            return
        
        self._is_player_turn = True
        
        response = RobotCommand.move(self._puzzle.solution[self._move_number])
        self.execute_command(response)

        self._move_number += 1

    
    def _start_new_puzzle(self) -> None:
        self._puzzle = self._get_puzzle()
        self._move_number = 0
        self._is_player_turn = False
        print(self._puzzle)

        self._board.set_fen(self._puzzle.fen)
        self.opponent_move()
        


    def _get_puzzle(self) -> Puzzle:
        possible_puzzles = []
        with open(self._puzzle_file_path, "r") as puzzle_file:
            puzzles: list[dict] = json.load(puzzle_file)

            for puzzle_data in puzzles:
                fen: str = puzzle_data["FEN"]
                solution: tuple[str] = tuple(puzzle_data["Moves"])
                rating = puzzle_data["Rating"]
                next_puzzle = Puzzle(fen, solution, rating)

                if rating > self._lower_bound and rating < self._upper_bound:
                    possible_puzzles.append(next_puzzle)

        if possible_puzzles:
            return random.choice(possible_puzzles)
        else:
            raise Exception(f"No puzzle in range {self._lower_bound} - {self._upper_bound}")
        