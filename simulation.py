import sys
import os
import threading
import queue
import time

# --- 1. Fix Path to allow imports from 'server' folder ---
# This ensures we can see the 'server' package from the root directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- 2. Imports ---
# We try to import Server from server.__main__ based on your file structure image.
# If your Server class is in a different file (like server/server.py), change this line.

from server.__main__ import Server 
from server.ai import AIPlayer, HardAIPlayer
from server.gamelogic.GameState import GameStateC
from shared import MESSAGES

# --- 3. Simulation Class ---
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
        
        # We skip the real DB manager to avoid database conflicts during sims
        self.db_manager = None 

    def run_simulation(self, number_of_games=10):
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
            #try:
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
            #except Exception as e:
               # results["Draw/Error"] += 1
                #print(f"   -> Error during Game {i + 1}: {e}")

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

    def play_single_match(self, game_id):
        # 1. Initialize Game Container
        if len(self.games) <= game_id:
            self.games.append({})

        # 2. Create Players (2 Normal, 2 Hard)
        # We create exactly 4 players here to fix the "3-6 players" ValueError
        players = {}
        players['AI_Std_1'] = AIPlayer('AI_Std_1', run_speed=0.001)
        players['AI_Std_2'] = AIPlayer('AI_Std_2', run_speed=0.001)
        players['AI_Std_3'] = AIPlayer('AI_Std_3', run_speed=0.001)
        players['AI_Hard_1'] = HardAIPlayer('AI_Hard_1', run_speed=0.001)
        players['AI_Hard_2'] = HardAIPlayer('AI_Hard_2', run_speed=0.001)
        players['AI_Hard_3'] = HardAIPlayer('AI_Hard_3', run_speed=0.001)

        self.games[game_id] = players

        # 3. Initialize Game State
        self.game_states[game_id] = GameStateC()
        
        # CRITICAL FIX: We explicitly tell the Logic there are 6 players
        try:
            self.game_states[game_id].Set_number_of_players(6)
            self.game_states[game_id].Set_settings()
            self.game_states[game_id].Set_player_names(list(players.keys()))
        except ValueError as e:
            print(f"Setup Failed: {e}")
            return None

        # 4. Setup Queues
        self.game_queues[game_id] = queue.Queue()
        self.game_locks[game_id] = threading.Lock()

        # 5. Start AI Threads
        # These threads allow the AI to "think" and put messages into the queue
        active_threads = []
        for username, ai_instance in players.items():
            t = threading.Thread(target=self.Handle_AI_Player, args=(game_id, ai_instance, username), daemon=True)
            t.start()
            active_threads.append(t)

        # 6. Start the Game (Send initial messages)
        # We mock the stats (Rating, Wins, Games) since we aren't using the DB
        dummy_stats = (1000, 0, 0) 
        
        # Create the start message
        start_payload = [[p, dummy_stats] for p in players.keys()]
        GameStartMessage = MESSAGES.GameStartNotification.construct_payload(game_id, start_payload)
        
        # Send to all AIs
        self.Broadcast_to_game(game_id, GameStartMessage)
        self.send_Starting_Board_to_everyone(game_id)

        # 7. Run the Game Logic Loop
        # We use a trick: we clear the rankings list, run the loop, and wait for the loop to exit.
        # The loop exits when self.Rankings_to_be_updated is populated or error occurs.
        winner_name = None
        
        self.Rankings_to_be_updated = [] 
        # This calls the original game logic from your Server class
        self.game_logic_loop(game_id)
        
        # Check who won
        if self.Rankings_to_be_updated:
            # The logic loop puts (winner_name, stats) into this list on win
            winner_name = self.Rankings_to_be_updated[0][0]
                
        
        
        # 8. Cleanup
        # We don't actually kill the threads properly here for speed, 
        # but in a long-running app you would join() them.
        return winner_name

    # --- Overrides to disable Networking ---

    def Broadcast_to_game(self, game_id, message):
        """Overrides Server.Broadcast... to send directly to AI objects"""
        if game_id < len(self.games):
            for client_socket in self.games[game_id].values():
                self.send_message(client_socket, message.encode())

    # We reuse your existing send_message because it already handles AIPlayer checks:
    # if isinstance(client_socket, AIPlayer): ... EnqueueMessage ...

# --- Main Execution ---
if __name__ == '__main__':
    # Configuration
    NUMBER_OF_GAMES = 10 # Change this to run more or fewer games

    sim_server = SimulationServer()
    sim_server.run_simulation(NUMBER_OF_GAMES)