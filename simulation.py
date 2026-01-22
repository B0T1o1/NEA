import sys
import os
import threading
import queue
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server.__main__ import Server 
from server.ai import AIPlayer, HardAIPlayer
from server.gamelogic.GameState import GameStateC
from shared import MESSAGES

class SimulationServer(Server):
    """
    A special version of the Server that runs locally without network sockets.
    It manages the game loop for AI vs AI directly.
    """
    def __init__(self):
        # We do NOT call super().__init__() because we don't want to bind sockets
        # We manually initialize only what we need for the simulation logic
        self.games = []
        self.game_states = {}
        self.game_locks = {}
        self.game_queues = {}
        self.kill = False
        self.Rankings_to_be_updated = []
        self.ranking_lock = threading.Lock()
        self.last_broadcast:str = ""
        
        # We skip the real DB manager to avoid database conflicts during sims
        self.db_manager = None 

    def run_simulation(self, number_of_games:int=10):
        """Runs a series of game of ai vs ai

        Args:
            number_of_games (int): Number of games to simulate. Defaults to 10.
        """
        print(f"--- Starting Simulation: {number_of_games} Games ---")
        print("Setup: 2 Standard AI vs 2 Hard AI (Total 4 Players)")
        print("-" * 50)

        results = {
            "Standard AI": 0,
            "Hard AI": 0,
            "Best AI": 0,
            "Draw/Error": 0

        }
        
        for i in range(number_of_games):
            try:
                print(f"[Sim] Starting Game {i + 1}...")
                winner = self.play_single_match(game_id=i)
                
                if winner:
                    if "Hard" in winner:
                        results["Hard AI"] += 1
                        print(f"   -> Winner: Hard AI ({winner})")

                    else:
                        results["Standard AI"] += 1
                        print(f"   -> Winner: Standard AI ({winner})")

                else:
                    results["Draw/Error"] += 1
                    print("   -> Game terminated without clear winner.")
            except Exception as e:
                results["Draw/Error"] += 1
                print(f"   -> Error during Game {i + 1}: {e}")

        # --- Final Report ---
        total = number_of_games
        print("\n" + "="*30)
        print("FINAL RESULTS")
        print("="*30)
        print(f"Total Games: {total}")
        print(f"Standard AI Wins: {results['Standard AI']} ({results['Standard AI']/total*100:.1f}%)")
        print(f"Hard AI Wins:     {results['Hard AI']} ({results['Hard AI']/total*100:.1f}%)")
        print(f"Errors/Incomplete: {results['Draw/Error']}")
        print("="*30)

    def play_single_match(self, game_id:int):
        """Setups a Game of 2 standard ai players vs 2 hard ai players

        Args:
            game_id (int): Identifier for the game instance
        Returns:
            str: Name of the winning player or None if no winner
        """
        # 1. Initialize Game Container
        if len(self.games) <= game_id:
            self.games.append({})

        # 2. Create Players (2 Normal, 2 Hard)
        players = {}
        players['AI_Std_1'] = AIPlayer('AI_Std_1', run_speed=0.001)
        players['AI_Std_2'] = AIPlayer('AI_Std_2', run_speed=0.001)
        players['AI_Hard_1'] = HardAIPlayer('AI_Hard_1', run_speed=0.001)
        players['AI_Hard_2'] = HardAIPlayer('AI_Hard_2', run_speed=0.001)

        self.games[game_id] = players

        # 3. Initialize Game State
        self.game_states[game_id] = GameStateC()
        
        try:
            self.game_states[game_id].Set_number_of_players(4)
            self.game_states[game_id].Set_settings(map='A')
            self.game_states[game_id].Set_player_names(list(players.keys()))
        except ValueError as e:
            print(f"Setup Failed: {e}")
            return None

        # 4. Setup Queues
        self.game_queues[game_id] = queue.Queue()
        self.game_locks[game_id] = threading.Lock()

        # 5. Start AI Threads
        active_threads = []
        for username, ai_instance in players.items():
            t = threading.Thread(target=self.Handle_AI_Player, args=(game_id, ai_instance, username), daemon=True)
            t.start()
            active_threads.append(t)

        # 6. Start the Game (Send initial messages)
        # create dummy stats for start message
        dummy_stats = (1000, 0, 0) 
        
        # Create the start message
        start_payload = [[p, dummy_stats] for p in players.keys()]
        GameStartMessage = MESSAGES.GameStartNotification.construct_payload(game_id, start_payload)
        
        # Send to all AIs
        self.Broadcast_to_game(game_id, GameStartMessage)
        self.send_Starting_Board_to_everyone(game_id)

        # 7. Run the Game Logic Loop

        winner_name = None
        
        self.Rankings_to_be_updated = [] 
        # This calls the original game logic from your Server class
        self.game_logic_loop(game_id)
        
        # Check who won
        if self.Rankings_to_be_updated:
            # The logic loop puts (winner_name, stats) into this list on win
            winner_name = self.Rankings_to_be_updated[0][0]

        return winner_name

    # --- Overrides to disable Networking ---

    def Broadcast_to_game(self, game_id:int, message:str):
        """Overides parent class for speed - directly calls AI players instead of sending via sockets.

        Args:
            game_id (int): game identifier
            message (str): message to broadcast
        """
        if game_id < len(self.games):
            for client_socket in self.games[game_id].values():
                self.send_message(client_socket, message.encode())



if __name__ == '__main__':
    # Configuration
    NUMBER_OF_GAMES = 5 # Number of AI vs AI games to simulate

    sim_server = SimulationServer()
    sim_server.run_simulation(NUMBER_OF_GAMES)