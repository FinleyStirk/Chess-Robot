import chess

from chess_robot.utils.structs import PieceStorage, MoveInfo, Vector2

class BoardState:
    def __init__(self):
        self._board = chess.Board()
        self._storage = PieceStorage()

    def play_move(self, move: MoveInfo) -> None:
        self._board.push_uci(move.uci)
        if move.captured_piece is not None:
            self._storage.add(move.captured_piece)
    
    def undo_move(self) -> None:
        move = self._board.pop()
        move_info = self.parse_move(move.uci())
        if move_info.captured_piece is not None:
            self._storage.remove(move_info.captured_piece)

    def parse_move(self, move_uci: str) -> MoveInfo:
        move = self._board.parse_uci(move_uci)

        from_square = self.get_components(move.from_square)
        to_square = self.get_components(move.to_square)

        capture_destination = None
        captured_piece = None

        if self.is_capture(move):
            captured_piece = self.piece_at(to_square)
            capture_destination = self.get_next_free_storage(captured_piece)

        physical_move = MoveInfo(
            uci=move_uci, 
            from_square=from_square,
            to_square=to_square,
            moving_piece=self.piece_at(from_square),
            captured_piece=captured_piece,
            capture_destination=capture_destination,
            is_castling=self.is_castling(move),
            current_piece_positions=self.get_occupied_positions(),
        )
        return physical_move
    
    def piece_at(self, position: Vector2) -> chess.Piece:
        index = position.x + position.y * 8
        if position.x in range(8) and position.y in range(8):
            return self._board.piece_at(index)
        else:
            return self._storage.piece_at(position)
    
    def is_capture(self, move: chess.Move) -> bool:
        return self._board.is_capture(move)
    
    def is_castling(self, move: chess.Move) -> bool:
        return self._board.is_castling(move)
    
    def get_next_free_storage(self, piece: chess.Piece) -> Vector2:
        return self._storage.get_next_free(piece)
    
    def get_occupied_positions(self) -> frozenset[Vector2]:
        positions = set()
        for y in range(7, -1, -1):
            for x in range(-3, 11):
                position = Vector2(x, y)
                if self.piece_at(position):
                    positions.add(position)
        return frozenset(positions)
    
    @staticmethod
    def get_components(square: chess.Square) -> Vector2:
        x = square % 8
        y = square // 8
        return Vector2(x, y)
    
    def __repr__(self) -> str:
        rows = []
        for y in range(7, -1, -1):
            row = []
            for x in range(-3, 11):
                piece = self.piece_at(Vector2(x, y))
                row.append(piece.symbol() if piece else ".")
            rows.append(" ".join(row))
        return "\n".join(rows)

    