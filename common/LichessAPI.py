import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("LICHESS_API_TOKEN")
USER_NAME = "Auto_Mate"

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}
def get_ongoing_games():
    url = "https://lichess.org/api/account/playing"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Error {response.status_code}: {response.text}")
    
def get_current_gameid():
    games = get_ongoing_games()["nowPlaying"]
    if games:
        return games[0]["fullId"]
    return None

def make_move(game_id, move):
    url = f"https://lichess.org/api/board/game/{game_id}/move/{move}"
    response = requests.post(url, headers=HEADERS)
    
    if response.status_code == 200:
        return "Move successful!"
    raise Exception(f"Error {response.status_code}: {response.text}")
    
def get_moves(game_id):
    url = f"https://lichess.org/api/board/game/stream/{game_id}"
    with requests.get(url, headers=HEADERS, stream=True) as response:
        for line in response.iter_lines():
            if line:
                event = json.loads(line.decode("utf-8"))
                if event.get("type") == "gameFull":
                    return event.get("state", {}).get("moves", "").split()
                elif event.get("type") == "gameState":
                    return event.get("moves", "").split()

def create_ai_game(level=3):  
    url = "https://lichess.org/api/challenge/ai"
    data = {
        "level": level,
        "timeControl" : "unlimited",
        "rated": False,
        "color": "white",
    }
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        return response.json()['id']
    raise Exception(f"Error {response.status_code}: {response.text}")
