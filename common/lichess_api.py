import berserk
import os
import time
from dotenv import load_dotenv

class MoveTimeoutError(Exception):
    pass

class LichessAPIError(Exception):
    pass

class LichessAPI:
    def __init__(self):
        load_dotenv()
        API_TOKEN = os.getenv("LICHESS_API_TOKEN")

        session = berserk.TokenSession(API_TOKEN)
        self._client = berserk.Client(session=session)

    def start_ai_game(self, ai_strength: int):
        try:
            ai_game = self._client.challenges.create_ai(level=ai_strength)
        except Exception as e:
            raise LichessAPIError(f"Failed to start AI game: {e}")
        
        self._game_id = ai_game['id'],
        self._stream = self._client.bots.stream_game_state(ai_game['id'])

    def attach_to_game(self, game_id):
        self._game_id = game_id
        self._stream = self._client.bots.stream_game_state(game_id)
    
    def wait_for_opponent_move(self, max_wait_time: float = float('inf')) -> str:
        start_time = time.time()
        for event in self._stream:
            if event.get('type') == 'gameState':
                moves = event.get('moves').split()
                if len(moves) % 2 == 1:
                    continue
                return moves[-1]
            if time.time() - start_time > max_wait_time:
                raise MoveTimeoutError('No move was made in the maximum wait time')
            
    def get_move_stack(self):
        for event in self._stream:
            return event['state']['moves'].split()
                
    def make_move(self, move: str):
        self._client.bots.make_move(self._game_id, move)