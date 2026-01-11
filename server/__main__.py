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
from typing import List, Literal,Union
import queue  
import ast
import struct
from .Databasemanager import DataBaseManagerC
from .ai import AIPlayer,HardAIPlayer
import random
class Server:
    """Allows the clients to interact with the game server over sockets
    """
    RECIEVE_LENGTH = 8
    def __init__(self, host: str = '127.0.0.1', port: int = 65432):
        """Intialises server settings

        Args:
            host (str, optional): Ip. Defaults to '127.0.0.1'.
            port (int, optional): Port number. Defaults to 65432.
        """
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
        self.server_socket.bind((self.host,self.port))
        self.db_manager = DataBaseManagerC() 
        self.db_manager.setup_tables()
        self.clients: List[socket.socket] = []
        self.queue: List[socket.socket] = []
        self.ready_clients: List[tuple[str, socket.socket]] = []
        self.Client_sending_status: dict[int,bool] = {}
        self.Logged_in_clients: List[str]  = []
        self.lobby_game_index = 0
        self.games: List[dict[str,Union[socket.socket,AIPlayer]]] = []
        self.game_states: dict[int, GameStateC] = {} # stores the game state for each active game
        self.game_locks: dict[int, threading.Lock] = {}  # Stores a lock for each active game
        self.client_keys: dict[int, tuple[int,int]] = {} # Stores the private_key for each client socket
        self.game_queues: dict[int,queue.Queue[tuple[str, MESSAGES.Message]]] = {}
        self.MAX_CLIENTS = 6
        self.MIN_CLIENTS = 3
        self.kill = False
        self.Rankings_to_be_updated: List[tuple[str,dict[str,int]]] = [] # List of (winner,dict(username, electros)) to update rankings 
        self.ranking_lock = threading.Lock() # Lock to safely access the list
        self.last_broadcast: dict[int, str] = {} # Stores the last broadcast message for each game

    def connection_listen_loop(self):
        """Detects socket connections and sends them to setup
        """
        Start_of_timer = datetime.datetime.now()
        while len(self.clients) < self.MAX_CLIENTS and ((datetime.datetime.now() - Start_of_timer).total_seconds() < 60 if Start_of_timer else True): # Checks for max clients or timer expiry
            try: 
                print('Server listening for connections on {}:{}'.format(self.host,self.port))
                self.server_socket.settimeout(1.0)
                self.server_socket.listen()
                connn, addd = self.server_socket.accept()
                self.clients.append(connn)
                self.Client_sending_status[connn.fileno()] = False
                self.queue.append(connn)
                threading.Thread(target=self.Set_up_client,args=(connn,)).start()
            except socket.timeout:
                pass
    

    
    def Set_up_client(self, client_socket: socket.socket):
        """Handles client login/ registiering, ensuring unique username and that account is only logged once, ALL account details passed over network are encrypted with RSA

        Args:
            client_socket (socket.socket): The socket object representing the client connection.
        """
        # 1. Initialize variables 
        username = None
        login_successful = False

        try:
            # Generate RSA keypair and send public key to client
            RSA_keypair = RSA.generate_keypair()
            private_key = RSA_keypair[1]
            message = MESSAGES.LoginRequest.construct_payload(public_key=RSA_keypair[0])
            self.send_message(client_socket, message.encode())
            print('Sent LoginRequest with public key to client.')
            
            # Store private key for this client
            self.client_keys[client_socket.fileno()] = private_key
            
            while not self.kill:
                # Receive message length
                length_bytes = client_socket.recv(self.RECIEVE_LENGTH)
                if not length_bytes: break 
                if len(length_bytes) < 8: break 
                
                msg_length = struct.unpack('Q', length_bytes)[0]

                # Receive the actual message data
                data = client_socket.recv(msg_length)
                
                if data:
                    try:
                        # Decrypt the data using the stored private key
                        decrypted_data = RSA.decrypt(int(data.decode()), private_key)
                        message_rec = ast.literal_eval(decrypted_data)
                    except Exception as e:
                        print(f"Decryption failed: {e}")
                        break

                    MessageType = MESSAGES.Message.parse_payload(message_rec)

                    # --- LOGIN LOGIC ---
                    if MessageType == 'LoginResponse':
                        username_attempt, password = MESSAGES.LoginResponse.parse_payload(message_rec)
                        print(f"Login attempt: {username_attempt}")
                        # Check if already logged in
                        if username_attempt in self.Logged_in_clients: 
                            self.send_message(client_socket, MESSAGES.LoginConfirmation.construct_payload(False).encode())
                            self.send_message(client_socket, MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode())
                        else:
                            # Get ID first
                            player_id = self.db_manager.get_player_id(username_attempt)
                            # Hash the password provided by user
                            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
                            
                            # Verify ID exists AND hash matches
                            if player_id and self.db_manager.verify_hash_in_db(player_id, hashed_pw):
                                # Successful login
                                username = username_attempt # Set the session username
                                print(f"User {username} logged in successfully.")
                                # Send confirmation
                                self.send_message(client_socket, MESSAGES.LoginConfirmation.construct_payload(True).encode())
                                self.ready_clients.append((username, client_socket))
                                self.Logged_in_clients.append(username)
                                self.queue.remove(client_socket)
                                login_successful = True
                                break
                            else:
                                # Failed login
                                print(f"User {username_attempt} failed to log in.")
                                self.send_message(client_socket, MESSAGES.LoginConfirmation.construct_payload(False).encode())
                                self.send_message(client_socket, MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode())

                    # --- REGISTRATION LOGIC ---
                    elif MessageType == 'RegisterRequest':
                        username_reg, password_reg = MESSAGES.RegisterRequest.parse_payload(message_rec)
                        # Validate input
                        if not username_reg or not password_reg:
                            # Invalid input
                            self.send_message(client_socket, MESSAGES.RegisterResponse.construct_payload(False).encode())
                        else:
                            # Check if username already exists
                            if self.db_manager.username_exists(username_reg):
                                print(f"Registration failed: {username_reg} exists.")
                                self.send_message(client_socket, MESSAGES.RegisterResponse.construct_payload(False).encode())
                                self.send_message(client_socket, MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode())
                            else:
                                # Register new user
                                hashed_pw = hashlib.sha256(password_reg.encode()).hexdigest()
                                self.db_manager.create_player(username_reg, hashed_pw)
                                
                                print(f"User {username_reg} registered successfully.")
                                # Send success response
                                self.send_message(client_socket, MESSAGES.RegisterResponse.construct_payload(True).encode())
                                self.send_message(client_socket, MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode())

                if not data: break 

        except ConnectionResetError:
            print('Client disconnected abruptly.')
        except Exception as e:
            print(f"Unexpected error in Setup_client: {e}")
            
        finally:
            if login_successful:
                print(f"User {username} setup completed.")
                return
            
            user_display = username if username else "Unknown Client"
            print(f"User {user_display} connection failed/dropped.")
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass

    def start_game(self, game_id: int):
        """Starts a new game on the server

        Args:
            game_id (int): The ID of the game to start, corresponding to self.games index and other data structures
        """
        players = self.games[game_id]
        if len(players) < self.MAX_CLIENTS:
            for i in range(random.randint(1, self.MAX_CLIENTS - len(players))):
                chance = random.random()
                if chance < 0.01: # 1% chance to add an AI player, 99% for a hard AI player
                    #TODO
                    self.games[game_id][f'AI_player_{i+1}'] = AIPlayer(f'AI_player_{i+1}')
                else:
                    self.games[game_id][f'Hard_AI_player_{i+1}'] = HardAIPlayer(f'Hard_AI_player_{i+1}')
        players = self.games[game_id]
        print(f"Initializing game {game_id} with players: {[p for p in players.keys()]}")
        
        # Initialize State
        self.game_states[game_id] = GameStateC()
        self.game_states[game_id].Set_number_of_players(len(players.keys()))
        self.game_states[game_id].Set_settings()
        self.game_states[game_id].Set_player_names([p for p in players.keys()])

        
        # Initialize Message Queue for this game
        self.game_queues[game_id] = queue.Queue()
        self.game_locks[game_id] = threading.Lock()

        # Notify Players
        GameStartMessage = MESSAGES.GameStartNotification.construct_payload(game_id, [[player, self.db_manager.get_player_stats(player)] for player in self.game_states[game_id].Get_players()])
        self.Broadcast_to_game(game_id,GameStartMessage)
        self.send_Starting_Board_to_everyone(game_id)
        # Start Player Handler Threads
        for username, client_socket in players.items():
            try:
                if isinstance(client_socket, AIPlayer):
                    # Start AI handler thread (this thread will manage AI thinking and message sending, reducing network load)
                    threading.Thread(target=self.Handle_AI_Player, args=(game_id, client_socket, username), daemon=True).start()
                else:
                    threading.Thread(target=self.Handle_Player, args=(game_id, client_socket, username), daemon=True).start()
            except Exception as e:
                print(f'Failed to start player {username}: {e}')

        # Start the Main Game Loop in a separate thread so it doesn't block the server
        threading.Thread(target=self.game_logic_loop, args=(game_id,), daemon=True).start()

    def send_message(self,client_socket:AIPlayer|socket.socket,message:bytes):
        """Sends the message to the client, also checks if AI player, so that it can enqueue it for processing

        Args:
            client_socket (AIPlayer | socket.socket): socket of the client to send to or AI player instance
            message (bytes): message to send already encoded
        """
        length_of_message = len(message)
        sent = False
        if isinstance(client_socket, AIPlayer):
            # For AI players, enqueue the message directly
            client_socket.EnqueueMessage(message)
            return
        while not sent:
            if self.Client_sending_status[client_socket.fileno()] == False:
                # Mark as sending so that no other thread sends at the same time
                self.Client_sending_status[client_socket.fileno()] = True
                client_socket.sendall(struct.pack('Q',length_of_message))
                client_socket.sendall(message)
                self.Client_sending_status[client_socket.fileno()] = False 
                sent = True    
            else:
                # Wait a bit and try again
                time.sleep(0.01)

    def send_Board_to_everyone(self,game_id:int):
        """Sends the current Board state in dictionary format to all players in the game. Also sends market and inventories.

        Args:
            game_id (int): The ID of the game to send the board for.
        """
        with self.game_locks[game_id]:
            # Get the whole board info, with lock to prevent changes during retrieval
            powerstation_market, resource_market, electros, player_resources_stations_dict = self.game_states[game_id].Get_whole_board_info()
            for player,socket in self.games[game_id].items():
                board = self.game_states[game_id].Get_board(player)
                BoardMessage = MESSAGES.BoardDisplay.construct_payload(board,powerstation_market, resource_market, electros, player_resources_stations_dict)
                # send to each player, using their socket/AI instance
                self.send_message(socket,BoardMessage.encode())
    
    def send_Starting_Board_to_everyone(self,game_id:int):
        """Sends only the Board, without markets or inventories

        Args:
            game_id (int): The ID of the game to send the starting board for.
        """
        with self.game_locks[game_id]:
            for player,socket in self.games[game_id].items():
                board = self.game_states[game_id].Get_board_before_game()
                BoardMessage = MESSAGES.StartBoardDisplay.construct_payload(board)
                self.send_message(socket,BoardMessage.encode())

    def game_logic_loop(self, game_id:int):
        """The main logic loop for a game, which processes messages and runs a single game

        Args:
            game_id (int): The ID of the game to run the logic loop for.

        Raises:
            Exception: _generic exception for unexpected errors during game loop

        Returns:
            None: This function does not return a value.
        """
        print(f"Game Loop started for Game ID {game_id}")
        players = self.game_states[game_id].Get_players()
        next_player_index = 0 # Index to track whose turn it is just for starting city selection
        next_player:str|Literal[False] = players[next_player_index]
        game_state = self.game_states[game_id]
        client_socket = self.games[game_id][next_player]
        BuyCityRequestMessage = MESSAGES.BuyStartingCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player)) # Initial request for first player
        self.Broadcast_to_game(game_id,BuyCityRequestMessage) # Send to all players
        
        while not self.kill:
            # Get message from queue (blocking with timeout to allow checking self.kill)
            # This consumes messages put here by Handle_Player threads
            try:
                username, message = self.game_queues[game_id].get(timeout=1) 
                msg_type = MESSAGES.Message.parse_payload(message)

                print(f"Game {game_id} received {msg_type} from {username}")

                # --- GAME LOGIC PROCESSING ---
                if msg_type == 'BuyStartingCityResponse':
                    # Handle starting city purchase
                    if game_state.Get_phase() == 1 and game_state.Get_round() == 0: # Ensure in correct phase
                        if username == next_player: # Ensure correct player
                            city = MESSAGES.BuyStartingCityResponse.parse_payload(message) # Get city from message
                            if game_state.Set_starting_city(username,city): # Attempt to set starting city
                                next_player_index += 1
                                self.send_Starting_Board_to_everyone(game_id)
                                if not game_state.Start_Game(): # If game not started yet, request next player's city
                                    next_player = players[next_player_index]
                                    BuyCityRequestMessage = MESSAGES.BuyStartingCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player))
                                    self.Broadcast_to_game(game_id,BuyCityRequestMessage)
                                else:
                                    if game_state.Start_Auction(): # Start auction if all starting cities chosen
                                        market  = game_state.Get_Current_Market_String()
                                        valid_values = game_state.Get_Valid_station_values()
                                        next_player  = game_state.Get_Next_Bidder()
                                        if next_player:
                                            self.send_Board_to_everyone(game_id)
                                            BuyStartingStationMessage = MESSAGES.BuyStartingStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                                            self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                                    
                                    raise Exception("Failed to start auction after starting cities chosen")
                            else:
                                # Invalid city choice, re-request from same player
                                BuyCityRequestMessage = MESSAGES.BuyStartingCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BuyCityRequestMessage)

                # --- AUCTION LOGIC PROCESSING ---
                if msg_type == 'BuyStartingStationResponse':
                    if username == game_state.Get_Next_Bidder():
                        power_station_value = MESSAGES.BuyStartingStationResponse.parse_payload(message) # Get bid from message
                        
                        if game_state.Starting_Bid_on_Power_Station(username,power_station_value): # Attempt to place bid
                            # Successful bid
                            if game_state.Finish_Auction(): # Check if auction finished
                                    # Proceed to resource buying phase
                                    game_state.Do_Resource_Buying()
                                    self.send_Board_to_everyone(game_id)
                                    costs = game_state.Get_Resource_Costs()
                                    next_player = game_state.Get_Next_Resource_Buyer()
                                    stations = game_state.Get_PowerStations_of(next_player)
                                    resource_space = game_state.Get_Resource_Space_of(next_player)
                                    BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                    self.Broadcast_to_game(game_id,BuyResourcesMessage)
                            else:
                                # Proceed to next bidder
                                next_player = game_state.Get_Next_Bidder_in_Round()
                                min_bid, station_info, held_by_player = game_state.Get_info_Bidding_Round()
                                BidOnPowerStationMessage = MESSAGES.BidOnPowerStation.construct_payload(station_info,min_bid,next_player,held_by_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BidOnPowerStationMessage)


                        else:
                            # Failed to place bid (e.g., insufficient funds), re-request from same player
                            market  = game_state.Get_Current_Market_String()
                            valid_values = game_state.Get_Valid_station_values()
                            next_player  = game_state.Get_Next_Bidder()
                            BuyStartingStationMessage = MESSAGES.BuyStartingStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                            self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                    else:
                        # Not this player's turn, ignore message
                        pass


                if msg_type == 'BidOnPowerStationResponse':
                    # Handle bidding on power stations
                    if username == game_state.Get_Next_Bidder_in_Round(): # Ensure correct player
                        bid_amount = MESSAGES.BidOnPowerStationResponse.parse_payload(message) # Get bid from message
                        if bid_amount is False: # Player is resigning from bidding
                            winning_player, winning_bid, station_info, needs_to_discard = game_state.Resign_From_Bidding(username) # Process resignation

                            if needs_to_discard:
                                    # Notify player to discard a power station
                                    DiscardPowerStationMessage = MESSAGES.DiscardPowerStationRequest.construct_payload(winning_player, game_state.Get_PowerStations_of(winning_player))
                                    self.Broadcast_to_game(game_id, DiscardPowerStationMessage)
                                    

                            elif winning_player: # If there's a winning player for this station
                                # Notify all players of the winning bid
                                message = MESSAGES.PlayerBoughtPowerStation.construct_payload(winning_player,station_info,winning_bid)
                                self.Broadcast_to_game(game_id,message)
                                # Proceed to next power station or next phase
                                next_player = game_state.Get_Next_Bidder()

                                if next_player and not needs_to_discard:  # Wait for discard if needed, and ensure there's a next bidder
                                    market  = game_state.Get_Current_Market_String()
                                    valid_values = game_state.Get_Valid_station_values()
                                    self.send_Board_to_everyone(game_id)
                                    # Request next bidder to buy power station
                                    if game_state.Get_round() == 0:
                                        BuyStartingStationMessage = MESSAGES.BuyStartingStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                                        self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                                    else:
                                        BuyPowerStationMessage = MESSAGES.BuyPowerStationRequest.construct_payload(market,next_player,game_state.Get_electros_of(next_player),valid_values)
                                        self.Broadcast_to_game(game_id,BuyPowerStationMessage)
                                elif not next_player and not needs_to_discard: # No more bidders, finish auction
                                    # Proceed to resource buying phase
                                    game_state.Finish_Auction()
                                    game_state.Do_Resource_Buying()
                                    self.send_Board_to_everyone(game_id)
                                    costs = game_state.Get_Resource_Costs()
                                    next_player = game_state.Get_Next_Resource_Buyer()
                                    stations = game_state.Get_PowerStations_of(next_player)
                                    resource_space = game_state.Get_Resource_Space_of(next_player)
                                    # send buy resources request
                                    BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                    self.Broadcast_to_game(game_id,BuyResourcesMessage)
                            else:
                                # Proceed to next bidder if no winner yet
                                self.send_Board_to_everyone(game_id)
                                next_player = game_state.Get_Next_Bidder_in_Round()
                                min_bid, station_info, held_by_player = game_state.Get_info_Bidding_Round()
                                BidOnPowerStationMessage = MESSAGES.BidOnPowerStation.construct_payload(station_info,min_bid,next_player,held_by_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BidOnPowerStationMessage)
                        else:
                            # Player is placing a bid
                            game_state.Place_Bid(username,bid_amount) # Attempt to place bid
                            next_player = game_state.Get_Next_Bidder_in_Round()
                            if next_player: # More bidders remain
                                self.send_Board_to_everyone(game_id)
                                min_bid, station_info, held_by_player = game_state.Get_info_Bidding_Round()
                                # Send next bid request
                                BidOnPowerStationMessage = MESSAGES.BidOnPowerStation.construct_payload(station_info,min_bid,next_player,held_by_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BidOnPowerStationMessage)
                            else:
                                raise Exception("No next bidder found after placing bid")
                            

                if msg_type == 'DiscardPowerStationResponse':
                    # Handle discarding power stations
                    power_station_value = MESSAGES.DiscardPowerStationResponse.parse_payload(message) # Get station to discard
                    if username == game_state.Get_Waiting_Discard_Player(): # Ensure correct player
                        discarded = game_state.Discard_PowerStation(username,power_station_value) # Process discard
                        next_player = game_state.Get_Next_Bidder() # Check for next bidder
                        if discarded: # Discard successful
                            if next_player: # More bidders remain
                                self.send_Board_to_everyone(game_id)
                                market  = game_state.Get_Current_Market_String()
                                valid_values = game_state.Get_Valid_station_values()
                                # Request next bidder to buy power station
                                BuyPowerStationMessage = MESSAGES.BuyPowerStationRequest.construct_payload(market,next_player,game_state.Get_electros_of(next_player),valid_values)
                                self.Broadcast_to_game(game_id,BuyPowerStationMessage)
                            else:
                                # No more bidders, finish auction
                                game_state.Finish_Auction()
                                game_state.Do_Resource_Buying()
                                self.send_Board_to_everyone(game_id)
                                costs = game_state.Get_Resource_Costs()
                                next_player = game_state.Get_Next_Resource_Buyer()
                                stations = game_state.Get_PowerStations_of(next_player)
                                resource_space = game_state.Get_Resource_Space_of(next_player)
                                #  send buy resources request
                                BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                self.Broadcast_to_game(game_id,BuyResourcesMessage)

                # --- RESOURCE BUYING LOGIC PROCESSING ---
                if msg_type == 'BuyResourcesResponse':
                    if username == game_state.Get_Next_Resource_Buyer(): # Ensure correct player
                        resources_to_buy = MESSAGES.BuyResourcesResponse.parse_payload(message) # Get resources from message
                        resource = list(resources_to_buy.keys())
                        amount = list(resources_to_buy.values())
                        if len(resource) == len(amount) == 1: # Ensure only one resource type being bought at a time
                            resource = resource[0]
                            amount = amount[0]
                            if game_state.Buy_Resource(username,resource,amount): # Attempt to buy resource
                                next_player = game_state.Get_Next_Resource_Buyer() # Check for next resource buyer
                                if next_player: # More resource buyers remain
                                    self.send_Board_to_everyone(game_id)
                                    costs = game_state.Get_Resource_Costs()
                                    stations = game_state.Get_PowerStations_of(next_player)
                                    resource_space = game_state.Get_Resource_Space_of(next_player)
                                    #  send buy resources request
                                    BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                    self.Broadcast_to_game(game_id,BuyResourcesMessage)
                                else:
                                    # No more resource buyers, finish resource buying phase
                                    game_state.Finish_Resource_Buying()
                                    # Proceed to next phase
                                    self.send_Board_to_everyone(game_id)
                                    game_state.Do_City_Buying()
                                    next_player = game_state.Get_Next_City_Buyer()
                                    costs = game_state.Get_City_Costs(next_player)
                                    # send buy city request
                                    BuyCityRequestMessage = MESSAGES.BuyCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player),costs)
                                    self.Broadcast_to_game(game_id,BuyCityRequestMessage)
                            else:
                                # Invalid response, ask again
                                self.send_Board_to_everyone(game_id)
                                costs = game_state.Get_Resource_Costs()
                                stations = game_state.Get_PowerStations_of(username)
                                resource_space = game_state.Get_Resource_Space_of(username)
                                BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(username,costs,stations,resource_space)
                                self.Broadcast_to_game(game_id,BuyResourcesMessage)
                        else:
                            # Invalid response, ask again
                            self.send_Board_to_everyone(game_id)
                            costs = game_state.Get_Resource_Costs()
                            stations = game_state.Get_PowerStations_of(username)
                            resource_space = game_state.Get_Resource_Space_of(username)
                            BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(username,costs,stations,resource_space)
                            self.Broadcast_to_game(game_id,BuyResourcesMessage)

                if msg_type == 'BuyCityResponse':
                    # Handle city buying
                    if username == game_state.Get_Next_City_Buyer(): # Ensure correct player
                        city_id = MESSAGES.BuyCityResponse.parse_payload(message) # Get city from message
                        bought = game_state.Player_Buy_City(username,city_id) # Attempt to buy city
                        if bought == True:
                            next_player = game_state.Get_Next_City_Buyer() # Check for next city buyer
                            if next_player: # More city buyers remain
                                city_costs = game_state.Get_City_Costs(next_player) # Get costs for next player 
                                self.send_Board_to_everyone(game_id)
                                # send buy city request
                                BuyCityRequestMessage = MESSAGES.BuyCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player),city_costs)
                                self.Broadcast_to_game(game_id,BuyCityRequestMessage)


                            elif game_state.Finish_City_Buying():
                                # Finish city buying phase, proceed to bureaucracy
                                game_state.Do_Bureaucracy()
                                self.send_Board_to_everyone(game_id)
                                next_player, electros , number_of_cities, power_stations, resources = game_state.Get_Info_For_Bureaucracy()
                                # Send bureaucracy update
                                BureaucracyUpdateMessage = MESSAGES.BureaucracyUpdate.construct_payload(next_player,electros,number_of_cities,power_stations,resources)
                                self.Broadcast_to_game(game_id,BureaucracyUpdateMessage)


                        else:
                            # Invalid city choice, re-request from same player
                            self.send_Board_to_everyone(game_id)
                            BuyCityRequestMessage = MESSAGES.BuyCityRequest.construct_payload(username,game_state.Get_electros_of(username),game_state.Get_City_Costs(username))
                            self.Broadcast_to_game(game_id,BuyCityRequestMessage)
       
                # --- BUREAUCRACY LOGIC PROCESSING ---
                if msg_type == 'BureaucracyComplete':
                    # Handle bureaucracy completion
                    power_station_dict_str = MESSAGES.BureaucracyComplete.parse_payload(message) # Get power station dict from message
                    power_station_dict = ast.literal_eval(power_station_dict_str)
                    cities = game_state.Player_Do_Bureaucracy(username,power_station_dict) # Process bureaucracy

                    if cities is False:
                        # Invalid bureaucracy, ask again
                        next_player, electros , number_of_cities, power_stations, resources = game_state.Get_Info_For_Bureaucracy()
                        BureaucracyUpdateMessage = MESSAGES.BureaucracyUpdate.construct_payload(next_player,electros,number_of_cities,power_stations,resources)
                        self.Broadcast_to_game(game_id,BureaucracyUpdateMessage)
                        
                    BureaucracyNotificationMessage = MESSAGES.BureaucracyNotification.construct_payload(username, cities) # Notify all players of bureaucracy completion
                    self.Broadcast_to_game(game_id,BureaucracyNotificationMessage)
                    self.send_Board_to_everyone(game_id)
                    next_player, electros , number_of_cities, power_stations, resources = game_state.Get_Info_For_Bureaucracy() # Get next player for bureaucracy
                    if next_player:
                        # Send bureaucracy update for next player
                        BureaucracyUpdateMessage = MESSAGES.BureaucracyUpdate.construct_payload(next_player,electros,number_of_cities,power_stations,resources)
                        self.Broadcast_to_game(game_id,BureaucracyUpdateMessage)
                    else:
                        winner = game_state.Check_Stage_Change_And_Win() # Check if stage change or win condition met
                        # Proceed to next turn
                        if winner:
                            # End Game
                            print(f"Game {game_id} ended. Winner: {winner}")
                            # Notify players about the winner
                            GameEndMessage = MESSAGES.GameEndNotification.construct_payload(winner)
                            self.Broadcast_to_game(game_id, GameEndMessage)
                            # Update rankings in database
                            self.Rankings_to_be_updated.append((winner, {player: game_state.Get_electros_of(player) for player in game_state.Get_players()}))
                            return # Exit game loop
                        self.send_Board_to_everyone(game_id)
                        
                        if game_state.Start_Auction(): # Start next auction
                            next_player = game_state.Get_Next_Bidder()
                            market  = game_state.Get_Current_Market_String()
                            valid_values = game_state.Get_Valid_station_values()
                            # request next bidder to buy power station
                            BuyPowerStationMessage = MESSAGES.BuyPowerStationRequest.construct_payload(market,next_player,game_state.Get_electros_of(next_player),valid_values)
                            self.Broadcast_to_game(game_id,BuyPowerStationMessage)
                        else:
                            raise Exception("Failed to start auction after bureaucracy.")
                        
                # --- MORE AUCTION PROCESSING ---
                if msg_type == 'BuyPowerStationResponse':
                    # Handle power station purchase
                    if username == game_state.Get_Next_Bidder(): # Ensure correct player
                        power_station_value = MESSAGES.BuyPowerStationResponse.parse_payload(message) # Get bid from message
                        if power_station_value is False:
                            game_state.Resign_from_auction(username) # Process resignation
                            next_player = game_state.Get_Next_Bidder()
                            if next_player: # More bidders remain
                                self.send_Board_to_everyone(game_id)
                                market  = game_state.Get_Current_Market_String()
                                valid_values = game_state.Get_Valid_station_values()
                                # request next bidder to buy power station
                                BuyStartingStationMessage = MESSAGES.BuyPowerStationRequest.construct_payload(market,next_player,game_state.Get_electros_of(next_player),valid_values)
                                self.Broadcast_to_game(game_id,BuyStartingStationMessage)

                            if game_state.Finish_Auction(): # Check if auction finished
                                    # Proceed to resource buying phase
                                    game_state.Do_Resource_Buying()
                                    self.send_Board_to_everyone(game_id)
                                    costs = game_state.Get_Resource_Costs()
                                    next_player = game_state.Get_Next_Resource_Buyer()
                                    stations = game_state.Get_PowerStations_of(next_player)
                                    resource_space = game_state.Get_Resource_Space_of(next_player)
                                    #  send buy resources request
                                    BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                    self.Broadcast_to_game(game_id,BuyResourcesMessage)

                        elif game_state.Starting_Bid_on_Power_Station(username,power_station_value):
                            # Successful bid
                            if game_state.Finish_Auction(): # Check if auction finished
                                    # Proceed to resource buying phase
                                    game_state.Do_Resource_Buying()
                                    self.send_Board_to_everyone(game_id)
                                    costs = game_state.Get_Resource_Costs()
                                    next_player = game_state.Get_Next_Resource_Buyer()
                                    stations = game_state.Get_PowerStations_of(next_player)
                                    resource_space = game_state.Get_Resource_Space_of(next_player)
                                    #  send buy resources request
                                    BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                    self.Broadcast_to_game(game_id,BuyResourcesMessage)
                            else:
                                # Proceed to next bidder
                                self.send_Board_to_everyone(game_id)
                                next_player = game_state.Get_Next_Bidder_in_Round()
                                min_bid, station_info, held_by_player = game_state.Get_info_Bidding_Round()
                                # Send next bid request
                                BidOnPowerStationMessage = MESSAGES.BidOnPowerStation.construct_payload(station_info,min_bid,next_player,held_by_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BidOnPowerStationMessage)


                        else:
                            # Failed to place bid (e.g., insufficient funds), re-request from same player
                            self.send_Board_to_everyone(game_id)
                            market  = game_state.Get_Current_Market_String()
                            valid_values = game_state.Get_Valid_station_values()
                            next_player  = game_state.Get_Next_Bidder()
                            BuyStartingStationMessage = MESSAGES.BuyPowerStationRequest.construct_payload(market,next_player,game_state.Get_electros_of(next_player),valid_values)
                            self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                    else:
                        pass

            except queue.Empty:
                time.sleep(0.05)


            except Exception as e:
                print(f"Error in game_logic_loop for Game ID {game_id}: {e}")
                self.Broadcast_to_game(game_id,self.last_broadcast[game_id]) # Resend last broadcast to resync clients
    
    def Broadcast_to_game(self,game_id:int,message:str) -> None:
        """Sends a message to every player in a game, passes sending logic to send_message

        Args:
            game_id (int): The iD of the game to broadcast to.
            message (str): The message to send to all players.
        """
        for client_socket in self.games[game_id].values():
            self.send_message(client_socket,message.encode())
        self.last_broadcast[game_id] = message
        return

                
    def Handle_Player(self, game_id:int, client_socket: socket.socket, username: str):
        """Handles the player connection, recieving messages and putting them onto the Game queue to be processed by game logic loop

        Args:
            game_id (int): the ID of the game the player is in.
            client_socket (socket.socket): The socket object for the player's connection.
            username (str): The username of the player.
        """
        while not self.kill:
            try:
                # 0. Receive Length Prefix
                length_bytes = client_socket.recv(self.RECIEVE_LENGTH)
                

                if not length_bytes:
                    raise ConnectionResetError
                    
                
                # 1. Validation Checks
                if len(length_bytes) < 8:
                    break
                
                msg_length = struct.unpack('Q', length_bytes)[0]



                # 2. Receive Data
                data = client_socket.recv(msg_length)
                
                if not data:
                    break
                
                # 3. Decode
                
                message = ast.literal_eval(data.decode())
                
                # 4. Put message onto game queue
                self.game_queues[game_id].put((username, message))
                
            except ConnectionResetError:
                print(f"Player {username} disconnected abruptly.")
                break 
            except Exception as e:
                print(f"Error in Handle_Player for {username}: {e}")
            
        
        

    def Handle_AI_Player(self, game_id:int, ai_player: AIPlayer, username: str):
        """Handles Receiving messages from an AI player

        Args:
            game_id (int): the id of the game the AI is in.
            ai_player (AIPlayer): The AI player instance.
            username (str): The username of the AI player.
        """
        while not self.kill:
            try:
                # 1. Get the message from the AI Player
                message_str = ai_player.GetNextMessage()
                
                if message_str:
                    # 2. CONVERT String -> Dictionary
                    try:
                        message_dict = ast.literal_eval(message_str)
                        self.game_queues[game_id].put((username, message_dict))
                    except Exception as e:
                        print(f"Error parsing AI message from {username}: {e}")
                else:
                    time.sleep(ai_player._run_speed)  # Sleep briefly if no message, to avoid busy-waiting, default run speed is 0.1 seconds, unless sim server
            except Exception as e:
                print(f"Error in Handle_AI_Player for {username}: {e}")
                break

    def check_and_start_games(self):
        """Continuously checks for ready clients and starts new games when enough players are available.
        """
        while not self.kill:
            number_of_ready_clients = len(self.ready_clients)
            if number_of_ready_clients >= self.MIN_CLIENTS: # Check if enough players are ready to start a game
                self.games.append({})
                self.lobby_game_index = len(self.games) - 1
                # Fill the game with ready clients
                for i in range(min(number_of_ready_clients, self.MAX_CLIENTS)):
                    client = self.ready_clients.pop(0)
                    self.games[self.lobby_game_index][client[0]] = client[1]
                if len(self.games[self.lobby_game_index]) >= self.MIN_CLIENTS:
                    # Start the game in a new thread
                    threading.Thread(target=self.start_game, args=(self.lobby_game_index,), daemon=True).start()
                    self.lobby_game_index += 1

            time.sleep(5)  # Check every 5 seconds




    def Update_Player_Rankings_Loop(self):
            """
            Runs continuously in the background.
            Checks if there are game results in 'Rankings_to_be_updated'.
            Calculates N-Player Elo and updates the database.
            """
            while not self.kill:
                game_result = None
                
                # Thread-safe pop from list
                with self.ranking_lock:
                    if self.Rankings_to_be_updated:
                        game_result = self.Rankings_to_be_updated.pop(0)
                
                if not game_result:
                    time.sleep(5) # Sleep to save CPU if no games ended
                    continue

                try:
                    winner_name, player_electros = game_result
                    print(f"Processing rankings for game won by {winner_name}")

                    participants = []
                    
                    # 1. Fetch current stats for all players in this game
                    for username, electros in player_electros.items():
                        p_id = self.db_manager.get_player_id(username)
                        if p_id is None: continue 

                        # Requires get_player_stats() in DataBaseManagerC
                        current_rating, current_wins, total_games = self.db_manager.get_player_stats(p_id)
                        
                        participants.append({
                            "username": username,
                            "id": p_id,
                            "rating": current_rating,
                            "wins": current_wins,
                            "games_played": total_games,
                            "electros": electros,
                            "match_rank": 0
                        })

                    # 2. Sort by Electros (Descending) to determine rank
                    participants.sort(key=lambda x: x["electros"], reverse=True)
                    
                    # 3. Ensure Winner is Rank 1 (Handle ties favoring the declared winner)
                    for i, p in enumerate(participants):
                        if p["username"] == winner_name:
                            winner_data = participants.pop(i)
                            participants.insert(0, winner_data)
                            break
                    
                    # Assign 1-based ranks
                    for i, p in enumerate(participants):
                        p["match_rank"] = i + 1

                    # 4. Calculate Elo Deltas
                    N = len(participants)
                    if N >= 2:
                        for player in participants:
                            total_actual = 0
                            total_expected = 0
                            k_factor = 40 if player["games_played"] < 10 else 32
                            
                            for opponent in participants:
                                if player["id"] == opponent["id"]: continue
                                
                                # Expected Score
                                rating_diff = opponent["rating"] - player["rating"]
                                expected_score = 1 / (1 + 10 ** (rating_diff / 400))
                                total_expected += expected_score
                                
                                # Actual Score
                                if player["match_rank"] < opponent["match_rank"]:
                                    actual_score = 1.0
                                elif player["match_rank"] > opponent["match_rank"]:
                                    actual_score = 0.0
                                else:
                                    actual_score = 0.5
                                total_actual += actual_score

                            # Calculate Change
                            rating_change = (k_factor / (N - 1)) * (total_actual - total_expected)
                            new_rating = int(round(player["rating"] + rating_change))
                            
                            # Update DB
                            new_games = player["games_played"] + 1
                            new_wins = player["wins"] + (1 if player["match_rank"] == 1 else 0)
                            
                            self.db_manager.update_ranking(
                                player["id"], new_rating, new_wins, new_games
                            )
                            print(f"Updated {player['username']}: {player['rating']} -> {new_rating}")
                
                except Exception as e:
                    print(f"Error in Update_Player_Rankings_Loop: {e}")

    def run(self):
        """Starts server thread
        """
        # Start the thread that listens for new clients
        connection_thread = threading.Thread(target=self.connection_listen_loop, daemon=True)
        connection_thread.start()

        # Start the thread that groups clients into games
        game_starter_thread = threading.Thread(target=self.check_and_start_games, daemon=True)
        game_starter_thread.start()

        # Start the Ranking Updater Thread
        UpdateRankingsThread = threading.Thread(target=self.Update_Player_Rankings_Loop, daemon=True)
        UpdateRankingsThread.start()

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