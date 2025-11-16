import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import hashlib
import socket
import threading
import time
import datetime
from shared import MESSAGES
from shared.encryption import RSA
from .gamelogic.GameState import GameStateC
from typing import List

class Server:
    def __init__(self, host: str = '127.0.0.1', port: int = 65432):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
        self.server_socket.bind((self.host,self.port))
        self.clients: List[socket.socket] = []
        self.queue: List[socket.socket] = []
        self.ready_clients: List[tuple[str, socket.socket]] = []
        self.lobby_game_index = 0
        self.games: List[List[socket.socket]] = [[]]
        self.game_states: dict[int, GameStateC] = {} # stores the game state for each active game
        self.game_locks: dict[int, threading.Lock] = {}  # Stores a lock for each active game
        self.client_keys: dict[int, tuple[int,int]] = {} # Stores the private_key for each client socket
        self.MAX_CLIENTS = 6
        self.MIN_CLIENTS = 3
        self.kill = False

    def connection_listen_loop(self):
        # Listen for incoming connections and calls Set_up_client for each new connection
        Start_of_timer = None
        while len(self.clients) < self.MAX_CLIENTS and ((datetime.datetime.now() - Start_of_timer).total_seconds() < 60 if Start_of_timer else True): # Checks for max clients or timer expiry
            try: 
                print('Server listening for connections on {}:{}'.format(self.host,self.port))
                self.server_socket.settimeout(1.0)
                self.server_socket.listen()
                connn, addd = self.server_socket.accept()
                self.clients.append(connn)
                self.queue.append(connn)
                threading.Thread(target=self.Set_up_client,args=(connn,)).start()
            except socket.timeout:
                pass
            
    
    def Set_up_client(self,client_socket:socket.socket):
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'usersdata.db')
        try:
            login_successful = False
            # Generate RSA keypair for this session and sends to client
            RSA_keypair = RSA.generate_keypair()
            private_key = RSA_keypair[1]
            message = MESSAGES.LoginRequest.construct_payload(public_key=RSA_keypair[0])
            client_socket.sendall(message.encode())
            print('Sent LoginRequest with public key to client.')
            self.client_keys[client_socket.fileno()] = private_key
            while not self.kill:
                data = client_socket.recv(1024)
                if data:
                    # Decode and decrypt incoming message
                    message = eval(RSA.decrypt(int(data.decode()), private_key))
                    MessageType = message['MessageType']

                    # Handle different message types
                    if message['MessageType'] == 'LoginResponse':
                        # Handle login request
                        username,password = MESSAGES.LoginResponse.parse_payload(message)
                        conn = sqlite3.connect(db_path)
                        cur = conn.cursor()
                        # Check credentials
                        cur.execute("SELECT * FROM usersdata WHERE username=? AND password_hash=?", (username,hashlib.sha256(password.encode()).hexdigest()))
                        if cur.fetchall():
                            # Successful login
                            print(f"User {username} logged in successfully.")
                            client_socket.sendall(MESSAGES.LoginConfirmation.construct_payload(True).encode())
                            self.ready_clients.append((username,client_socket))
                            self.queue.remove(client_socket)
                            login_successful = True
                            conn.close()
                            break
                        else:
                            # Failed login
                            print(f"User {username} failed to log in.")
                            client_socket.sendall(MESSAGES.LoginConfirmation.construct_payload(False).encode())
                            client_socket.sendall(MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode())
                        conn.close()

                    elif message['MessageType'] == 'RegisterRequest':
                        # Handle registration request
                        username,password = MESSAGES.RegisterRequest.parse_payload(message)
                        if not username or not password:
                            client_socket.sendall(MESSAGES.RegisterResponse.construct_payload(False).encode())
                        else:
                            conn = sqlite3.connect(db_path)
                            cur = conn.cursor()
                            cur.execute("SELECT * FROM usersdata WHERE username=?", (username,))
                            if cur.fetchall():
                                # Username already exists
                                print(f"Registration failed: Username {username} already exists.")
                                client_socket.sendall(MESSAGES.RegisterResponse.construct_payload(False).encode())
                            else:
                                # Register new user
                                cur.execute("INSERT INTO usersdata (username, password_hash) VALUES (?, ?)", (username, hashlib.sha256(password.encode()).hexdigest()))
                                conn.commit()
                                print(f"User {username} registered successfully.")
                                client_socket.sendall(MESSAGES.RegisterResponse.construct_payload(True).encode())
                            client_socket.sendall(MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode())
                            conn.close()
                            

                if not data:
                    break # Client disconnected

        except ConnectionResetError:
            print('Client disconnected abruptly.')
        finally:
            if login_successful:
                print(f"User {username} setup completed and added to ready clients.")
                return
            print(f"User {username} connection failed to set up.")

            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()


    def start_game(self, game_id):
        players:List[tuple[str, socket.socket]] = self.games[game_id]
        print(f"Starting game with players: {[p[0] for p in players]}")
        self.game_states[game_id] = GameStateC()
        self.game_locks[game_id] = threading.Lock()
        self.game_states[game_id].Set_number_of_players(len(players))
        self.game_states[game_id].Set_player_names([p[0] for p in players])
        self.game_states[game_id].Set_settings() # default settings for now
        GameStartMessage = MESSAGES.GameStartNotification.construct_payload(game_id, self.game_states[game_id].Get_players())
        BoardMessage = MESSAGES.BoardMessage.construct_payload(self.game_states[game_id].Get_board())
        for player_index, (username, client_socket) in enumerate(players):
            try:
                
                client_socket.sendall(GameStartMessage.encode())
                client_socket.sendall(BoardMessage.encode())
                threading.Thread(target=self.Handle_Player,args=(game_id, client_socket, username)).start()
                
            except BrokenPipeError:
                print(f'Failed to send GameStartNotification to {username}.')
    
    def broadcast_to_game(self, game_id, message_payload: str):
            """Procedure to send a message to all clients in a specific game."""
            message = message_payload.encode()
            for _, client_socket in self.games[game_id]:
                try:
                    client_socket.sendall(message)
                except Exception as e:
                    print(f"Failed to broadcast to a client: {e}")

    def Handle_Player(self, game_id, client_socket: socket.socket, username: str):
        ##### INCOMPLETE - ADD LOGIC FOR ALL PHASES AND ACTIONS #####
        game_state = self.game_states[game_id]
        game_lock = self.game_locks[game_id]
        private_key = self.client_keys[client_socket] # Retrieve this client's key

        while not self.kill:
            try:
                data = client_socket.recv(1024)
                if not data:
                    print(f"Player {username} disconnected.")
                    # TODO: Add logic to handle player disconnection
                    # (e.g., remove from game, notify others)
                    break
                
                # 1. Decode the message
                message = eval(RSA.decrypt(int(data.decode()), private_key))
                MessageType = message['MessageType']

                response_payload = None # Message to send back ONLY to this player
                broadcast_payload = None # Message to send to EVERYONE in the game

                # 2. Acquire the lock to safely modify the game state
                with game_lock:
                    current_phase = game_state.Get_phase()

                    # --- PROCESS ALL GAME ACTIONS HERE ---
                    # This is a conceptual example for Phase 2 (Bidding)
                    
                    if MessageType == 'StartBid' and current_phase == 2:
                        # Assuming payload is (station_obj, starting_bid)
                        station, bid = MESSAGES.StartBid.parse_payload(message)
                        try:
                            if game_state.Starting_Bid_on_Power_Station(username, station):
                                # Tell everyone a bid has started
                                broadcast_payload = MESSAGES.AuctionStarted.construct_payload(username, station, bid)
                            else:
                                response_payload = MESSAGES.Error.construct_payload("Invalid action: Not your turn or invalid station.")
                        except Exception as e:
                            response_payload = MESSAGES.Error.construct_payload(f"Bid error: {e}")

                    elif MessageType == 'PlaceBid' and current_phase == 2:
                        station, bid = MESSAGES.PlaceBid.parse_payload(message)
                        try:
                            if game_state.Place_Bid(username, station, bid):
                                # Tell everyone the bid increased
                                broadcast_payload = MESSAGES.BidUpdate.construct_payload(username, station, bid)
                            else:
                                response_payload = MESSAGES.Error.construct_payload("Invalid bid: Too low or not your turn.")
                        except Exception as e:
                            response_payload = MESSAGES.Error.construct_payload(f"Bid error: {e}")

                    elif MessageType == 'ResignBid' and current_phase == 2:
                        try:
                            winner_name, winning_bid = game_state.Resign_From_Bidding(username)
                            if winner_name:
                                # Auction ended, tell everyone who won
                                broadcast_payload = MESSAGES.AuctionWon.construct_payload(winner_name, winning_bid)
                            else:
                                # Just this player resigned, tell everyone
                                broadcast_payload = MESSAGES.PlayerResigned.construct_payload(username)
                        except Exception as e:
                            response_payload = MESSAGES.Error.construct_payload(f"Resign error: {e}")

                    # --- ADD ELIF BLOCKS FOR OTHER PHASES ---
                    elif MessageType == 'BuyResource' and current_phase == 3:
                        # ... your logic for phase 3 ...
                        pass
                    
                    elif MessageType == 'BuyCity' and current_phase == 4:
                        # ... your logic for phase 4 ...
                        pass

                    # --- ADD LOGIC FOR PHASE TRANSITIONS ---
                    # (e.g., check if auction/buying is done and move to next phase)
                    if game_state.Phase2.Finish_Auction() and game_state.Get_phase() == 2:
                        game_state.Finish_Auction() # This advances phase to 3
                        game_state.Do_Resource_Buying()
                        broadcast_payload = MESSAGES.PhaseChange.construct_payload(3, game_state.Get_Resource_Buyers())


                # 3. Send responses *after* the lock is released
                if response_payload:
                    # You'd need to encrypt this response for the client
                    # For simplicity, we just send the encoded string
                    client_socket.sendall(response_payload.encode())
                
                if broadcast_payload:
                    self.broadcast_to_game(game_id, broadcast_payload)

            except ConnectionResetError:
                print(f"Player {username} disconnected abruptly.")
                break # Exit loop
            except Exception as e:
                print(f"Error in Handle_Player for {username}: {e}")
                # You might want to break or send an error to the client
        
        # --- CLEANUP ---
        print(f"Handle_Player thread for {username} stopping.")
        if client_socket in self.client_keys:
            del self.client_keys[client_socket]
        # Add logic to remove player from self.games[game_id]


    def check_and_start_games(self):
        while not self.kill:
            if len(self.ready_clients) >= self.MIN_CLIENTS:
                self.games.append([])
                self.lobby_game_index = len(self.games) - 1
                while len(self.games[self.lobby_game_index]) < self.MAX_CLIENTS:
                    self.games[self.lobby_game_index].append(self.ready_clients.pop(0))
                if len(self.games[self.lobby_game_index]) >= self.MIN_CLIENTS:
                    self.start_game(self.lobby_game_index)
                    self.lobby_game_index += 1

            time.sleep(5)  # Check every 5 seconds

        



    def run(self):
            # Start the thread that listens for new clients
            connection_thread = threading.Thread(target=self.connection_listen_loop, daemon=True)
            connection_thread.start()


            # Start the thread that groups clients into games
            game_starter_thread = threading.Thread(target=self.check_and_start_games, daemon=True)
            game_starter_thread.start()


            try:
                # Keep main thread alive to allow daemon threads to run
                while not self.kill:
                    time.sleep(1)
            
            except KeyboardInterrupt:
                print("\nShutting down server.")
                self.kill = True
                for client_socket in self.clients:
                    client_socket.close()
                self.server_socket.close()
                print("Server shut down.")
if __name__ == '__main__':
    server = Server()
    server.run()