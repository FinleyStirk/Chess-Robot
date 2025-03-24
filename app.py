from flask import render_template, request, jsonify, url_for, Blueprint, Flask
import chess
from common.game import board
from common.gantry import StartTransmitting, EndTransmitting, transmitting
import logging
from flask import Flask, jsonify
from common.game import PlayLastMove, board, reset
from common.LichessAPI import create_ai_game, get_moves, get_current_gameid, make_move
from time import sleep
import logging


app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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
        for file in "abcdefgh":
            square = file + str(rank)
            file_index = ord(file) - ord('a')
            rank_index = 8 - rank
            cell_color = "white" if ((file_index + rank_index) % 2 == 0) else "black"
            square_index = chess.parse_square(square)
            piece = board.piece_at(square_index)

            highlight = ""
            if len(board.move_stack) > 0:
                lastMove = board.peek()
                if chess.square_name(lastMove.from_square) == square or chess.square_name(lastMove.to_square) == square:
                    highlight = " highlight"
            
            if piece:
                piece_char = piece.symbol()
                if piece_char in piece_map:
                    img_url = url_for('static', filename=f"PieceImages/{piece_map[piece_char]}")
                    piece_html = f"<img src='{img_url}' class='piece' draggable='true' data-square='{square}'>"
                else:
                    piece_html = ""
            else:
                piece_html = ""
            board_html += f"<td class='{cell_color}{highlight}' data-square='{square}'>{piece_html}</td>"
        board_html += "</tr>"
    board_html += "</table>"
    return board_html

@app.route('/')
def index():
    board_html = render_chess_board()
    return render_template(html, board_html=board_html, transmitting=transmitting)

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
        StartTransmitting()
    else:
        EndTransmitting()
    return jsonify({'status': 'success', 'transmitting': transmitting})

def online_game():
    global move_count
    global html
    html = 'base.html'
    GAME_ID = get_current_gameid()
    if GAME_ID:
        moves = get_moves(GAME_ID)
        move_count = len(moves)
        for move in moves:
            board.push_uci(move)
    else:
        GAME_ID = create_ai_game()
        move_count = 0
    
    global process_move
    @app.route('/process_move', methods=['POST'])
    def process_move():
        global move_count
        try:
            make_move(GAME_ID, board.peek())
            PlayLastMove()

            moves = get_moves(GAME_ID)
            while move_count == len(moves) - 1:
                moves = get_moves(GAME_ID)
                sleep(1)
            board.push_uci(moves[-1])
            PlayLastMove()
            move_count = len(moves)

            new_board_html = render_chess_board()
            return jsonify({'status': 'success', 'board_html': new_board_html})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    app.run(debug=False)

def two_player_digital():
    global html
    html = 'twoPlayerDigital.html'

    global process_move
    @app.route('/process_move', methods=['POST'])
    def process_move():
        try:
            PlayLastMove()
            return jsonify({'status': 'success', 'board_html': render_chess_board()})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    global reset_board
    @app.route('/reset', methods=['POST'])
    def reset_board():
        try:
            reset()
            return jsonify({'status': 'success', 'board_html': render_chess_board()})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
        
    app.run(debug=False)