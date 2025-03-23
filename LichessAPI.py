import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("LICHESS_API_TOKEN")

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}
def get_ongoing_games():
    url = "https://lichess.org/api/account/playing"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error {response.status_code}: {response.text}"

def make_move(game_id, move):
    url = f"https://lichess.org/api/board/game/{game_id}/move/{move}"
    response = requests.post(url, headers=HEADERS)
    
    if response.status_code == 200:
        return "Move successful!"
    else:
        return f"Error {response.status_code}: {response.text}"
    
def get_moves(game_id):
    url = f"https://lichess.org/api/board/game/stream/{game_id}"
    with requests.get(url, headers=HEADERS, stream=True) as response:
        for line in response.iter_lines():
            if line:
                event = json.loads(line.decode("utf-8"))
                if event.get("type") == "gameFull":
                    moves = event.get("state", {}).get("moves", "")
                elif event.get("type") == "gameState":
                    moves = event.get("moves", "")
                else:
                    continue 
                if moves:
                    move_list = moves.split()
                    return move_list
                
def get_fen(game_id):
    url = f"https://lichess.org/api/board/game/stream/{game_id}"
    with requests.get(url, headers=HEADERS, stream=True) as response:
        for line in response.iter_lines():
            if line:
                event = json.loads(line.decode("utf-8"))
                if event.get("type") == "gameFull":
                    fen = event.get("state", {}).get("fen", "")
                elif event.get("type") == "gameState":
                    fen = event.get("fen", "")
                else:
                    continue
                if fen:
                    return fen

def create_ai_game(level=3):  
    url = "https://lichess.org/api/challenge/ai"
    data = {
        "level": level,
        "timeControl" : "unlimited",
        "rated": False
    }
    response = requests.post(url, headers=HEADERS, json=data)
    return response.json() if response.status_code == 200 else response.text




# games = get_ongoing_games()
# print(games)
# GAME_ID = games["nowPlaying"][0]["fullId"]
# make_move(GAME_ID, "e2e4")~
# print(get_moves(GAME_ID))
