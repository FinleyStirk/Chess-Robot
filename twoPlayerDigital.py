from common.ui_utils import base_bp
from flask import Flask, jsonify
from common.game import PlayLastMove, board
import logging

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.register_blueprint(base_bp)

@app.route('/process_move', methods=['POST'])
def process_move():
    try:
        PlayLastMove()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=False)