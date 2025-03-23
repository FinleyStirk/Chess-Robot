from common.utils import base_bp, render_chess_board
from flask import Flask, jsonify
from game import PlayLastMove, board
from LichessAPI import create_ai_game, get_moves, get_current_gameid, make_move
from time import sleep
import logging

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.register_blueprint(base_bp)

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


if __name__ == '__main__':
    GAME_ID = get_current_gameid()
    if GAME_ID:
        moves = get_moves(GAME_ID)
        move_count = len(moves)
        for move in moves:
            board.push_uci(move)
    else:
        GAME_ID = create_ai_game()
        move_count = 0
    app.run(debug=False)