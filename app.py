from flask import render_template, request, jsonify, url_for, Flask
import chess
from common.game import board
from common.gantry import start_transmitting, EndTransmitting, transmitting
from common.structs import Vector2
import logging
from flask import Flask, jsonify
import common.game as game
from common.LichessAPI import get_moves, make_move, get_current_game, await_opponent_move
from common.puzzle import get_puzzle
import logging


app = Flask(__name__)
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

piece_map = {
    'P': 'whitePawn.png', 'p': 'blackPawn.png',
    'N': 'whiteKnight.png', 'n': 'blackKnight.png',
    'B': 'whiteBishop.png', 'b': 'blackBishop.png',
    'R': 'whiteRook.png',   'r': 'blackRook.png',
    'Q': 'whiteQueen.png',  'q': 'blackQueen.png',
    'K': 'whiteKing.png',   'k': 'blackKing.png'
}

def render_chess_board():
    board_html = "<table class='chessboard'>"
    for rank in range(8, 0, -1):
        board_html += "<tr>"
        for file_index in range(-3, 11):
            rank_index = 8 - rank
            cell_color = "white" if ((file_index + rank_index) % 2 == 0) else "black"
            if 0 <= file_index < 8:
                file = chr(ord('a') + file_index)
                square = file + str(rank)
                square_index = chess.parse_square(square)
                piece = board.piece_at(square_index)
                highlight = ""
                if len(board.move_stack) > 0:
                    lastMove = board.peek()
                    if chess.square_name(lastMove.from_square) == square or chess.square_name(lastMove.to_square) == square:
                        highlight = "highlight"
                if piece:
                    piece_char = piece.symbol()
                    if piece_char in piece_map:
                        img_url = url_for('static', filename=f"PieceImages/{piece_map[piece_char]}")
                        piece_html = f"<img src='{img_url}' class='piece' draggable='true' data-square='{square}'>"
                    else:
                        piece_html = ""
                else:
                    piece_html = ""
                board_html += f"<td class='{cell_color} {highlight}' data-square='{square}'>{piece_html}</td>"
            elif file_index == -1 or file_index == 8:
                board_html += f"<td class='background'></td>"
            else:
                piece = game.get_offboard_piece(Vector2(file_index, rank - 1))
                if piece:
                    img_url = url_for('static', filename=f"PieceImages/{piece_map[piece]}")
                    piece_html = f"<img src='{img_url}' class='piece' draggable='false'>"
                else:
                    piece_html = ""
                board_html += f"<td class='{cell_color}'>{piece_html}</td>"
        board_html += "</tr>"
    board_html += "</table>"
    return board_html

@app.route('/')
def index():
    template = render_template(
        "base.html",
        board_html = render_chess_board(),
        transmitting = transmitting,
        reset_button = gamemode_settings['reset'],
        undo_button = gamemode_settings['undo'],
        difficulty_slider = gamemode_settings['puzzle_difficulty']
    )
    return template

@app.route('/get_board', methods=['POST'])
def get_board():
    board_html = render_chess_board()
    return jsonify({"status": "success", "board_html": board_html})

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    move_str = data.get('move')
    try:
        move = chess.Move.from_uci(move_str)
        if move in board.legal_moves:
            board.push(move)
            new_board_html = render_chess_board()
            return jsonify({'status': 'success', 'board_html': new_board_html})
        else:
            return jsonify({'status': 'invalid move'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/update_transmitting', methods=['POST'])
def update_transmitting():
    data = request.get_json()
    if data.get('transmitting', False):
        start_transmitting()
    else:
        EndTransmitting()
    return jsonify({'status': 'success', 'transmitting': transmitting})

@app.route('/reset', methods=['POST'])
def reset_board():
    try:
        game.reset()
        return jsonify({'status': 'success', 'board_html': render_chess_board()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    
@app.route('/undo', methods=['POST'])
def undo_move():
    try:
        game.UndoMove()
        return jsonify({'status': 'success', 'board_html': render_chess_board()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


def online_game():
    GAME_ID = get_current_game()
    initial_moves = get_moves(GAME_ID)
    for move in initial_moves:
        board.push_uci(move)
    
    global process_move
    @app.route('/process_move', methods=['POST'])
    def process_move():
        try:
            make_move(GAME_ID, board.peek())
            game.PlayLastMove()
            game.PlayMove(await_opponent_move(GAME_ID))
            
            new_board_html = render_chess_board()
            return jsonify({'status': 'success', 'board_html': new_board_html})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    app.run(debug=False)

def two_player_digital():
    global process_move
    @app.route('/process_move', methods=['POST'])
    def process_move():
        try:
            game.PlayLastMove()
            return jsonify({'status': 'success', 'board_html': render_chess_board()})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
        
    with app.app_context():
        gamemode_settings['reset'] = render_template('resetButton.html')
        gamemode_settings['undo'] = render_template('undoButton.html')
    
    app.run(debug=False)

gamemode_settings = {
    'reset' : '',
    'undo' : '',
    'puzzle_difficulty' : '',
}