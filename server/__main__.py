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
import queue  
import ast
import struct

class Server:
    RECIEVE_LENGTH = 8
    def __init__(self, host: str = '127.0.0.1', port: int = 65432):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
        self.server_socket.bind((self.host,self.port))
        self.clients: List[socket.socket] = []
        self.queue: List[socket.socket] = []
        self.ready_clients: List[tuple[str, socket.socket]] = []
        self.Client_sending_status: dict[int,bool] = {}
        self.Logged_in_clients: List[str]  = []
        self.lobby_game_index = 0
        self.games: List[dict[str,socket.socket]] = []
        self.game_states: dict[int, GameStateC] = {} # stores the game state for each active game
        self.game_locks: dict[int, threading.Lock] = {}  # Stores a lock for each active game
        self.client_keys: dict[int, tuple[int,int]] = {} # Stores the private_key for each client socket
        self.game_queues: dict[int,List[tuple[str, MESSAGES.Message]]] = {}
        self.MAX_CLIENTS = 3
        self.MIN_CLIENTS = 3
        self.kill = False

    def connection_listen_loop(self):
        # Listen for incoming connections and calls Set_up_client for each new connection
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
            
            db_path = os.path.join(os.path.dirname(__file__), 'data', 'usersdata.db')
            
            # 1. Initialize variables to prevent UnboundLocalError in 'finally' block
            username = None
            login_successful = False
            
            # Define a limit (e.g., 2MB). No login/register packet should exceed this.
            MAX_MESSAGE_SIZE = 2 * 1024 * 1024 

            try:
                # Generate RSA keypair for this session and sends to client
                RSA_keypair = RSA.generate_keypair()
                private_key = RSA_keypair[1]
                message = MESSAGES.LoginRequest.construct_payload(public_key=RSA_keypair[0])
                self.send_message(client_socket, message.encode())
                print('Sent LoginRequest with public key to client.')
                
                self.client_keys[client_socket.fileno()] = private_key
                
                while not self.kill:
                    length_bytes = client_socket.recv(self.RECIEVE_LENGTH)
                    
                    # Check for disconnection
                    if not length_bytes:
                        break 
                    
                    # Check for partial headers (garbage data)
                    if len(length_bytes) < 8:
                        break 

                    # Unpack the message length
                    msg_length = struct.unpack('Q', length_bytes)[0]

                    # ### SAFETY CHECK: Prevent MemoryError ###
                    if msg_length > MAX_MESSAGE_SIZE:
                        print(f"SECURITY ALERT: Client sent packet of size {msg_length}. Connection refused.")
                        break
                    # #########################################

                    # Receive the actual data
                    data = client_socket.recv(msg_length)
                    
                    if data:
                        # Decode and decrypt incoming message
                        # We use a try/except here in case decryption fails (wrong key/garbage data)
                        try:
                            decrypted_data = RSA.decrypt(int(data.decode()), private_key)
                            message_rec = ast.literal_eval(decrypted_data)
                        except Exception as e:
                            print(f"Decryption failed: {e}")
                            break

                        MessageType = MESSAGES.Message.parse_payload(message_rec)

                        # Handle different message types
                        if MessageType == 'LoginResponse':
                            # Handle login request
                            username, password = MESSAGES.LoginResponse.parse_payload(message_rec)
                            print(f"Login attempt: {username}")
                            
                            if username in self.Logged_in_clients: # Account is already logged in
                                message = MESSAGES.LoginConfirmation.construct_payload(False).encode()
                                self.send_message(client_socket, message)
                                message = MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode()
                                self.send_message(client_socket, message)
                            else:
                                conn = sqlite3.connect(db_path)
                                cur = conn.cursor()
                                # Check credentials
                                cur.execute("SELECT * FROM usersdata WHERE username=? AND password_hash=?", (username, hashlib.sha256(password.encode()).hexdigest()))
                                
                                if cur.fetchall():
                                    # Successful login
                                    print(f"User {username} logged in successfully.")
                                    message = MESSAGES.LoginConfirmation.construct_payload(True).encode()
                                    self.send_message(client_socket, message)
                                    self.ready_clients.append((username, client_socket))
                                    self.Logged_in_clients.append(username)
                                    self.queue.remove(client_socket)
                                    login_successful = True
                                    conn.close()
                                    break
                                else:
                                    # Failed login
                                    print(f"User {username} failed to log in.")
                                    message = MESSAGES.LoginConfirmation.construct_payload(False).encode()
                                    self.send_message(client_socket, message)
                                    message = MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode()
                                    self.send_message(client_socket, message)
                                conn.close()

                        elif MessageType == 'RegisterRequest':
                            # Handle registration request
                            username_reg, password_reg = MESSAGES.RegisterRequest.parse_payload(message_rec)
                            
                            # We don't set 'username' yet, because they aren't logged in.
                            # We just check the database.
                            if not username_reg or not password_reg:
                                message = MESSAGES.RegisterResponse.construct_payload(False).encode()
                                self.send_message(client_socket, message)
                            else:
                                conn = sqlite3.connect(db_path)
                                cur = conn.cursor()
                                cur.execute("SELECT * FROM usersdata WHERE username=?", (username_reg,))
                                if cur.fetchall():
                                    # Username already exists
                                    print(f"Registration failed: Username {username_reg} already exists.")
                                    message = MESSAGES.RegisterResponse.construct_payload(False).encode()
                                    self.send_message(client_socket, message)
                                    message = MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode()
                                    self.send_message(client_socket, message)
                                else:
                                    # Register new user
                                    cur.execute("INSERT INTO usersdata (username, password_hash) VALUES (?, ?)", (username_reg, hashlib.sha256(password_reg.encode()).hexdigest()))
                                    conn.commit()
                                    print(f"User {username_reg} registered successfully.")
                                    self.send_message(client_socket, MESSAGES.RegisterResponse.construct_payload(True).encode())
                                
                                message = MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode()
                                self.send_message(client_socket, message)
                                conn.close()

                    if not data:
                        break # Client disconnected

            except ConnectionResetError:
                print('Client disconnected abruptly.')
            except Exception as e:
                print(f"Unexpected error in Setup_client: {e}")
                
            finally:
                if login_successful:
                    print(f"User {username} setup completed and added to ready clients.")
                    return
                
                # Safe print using the variable initialized at the top
                user_display = username if username else "Unknown Client"
                print(f"User {user_display} connection failed to set up.")

                if client_socket in self.clients:
                    self.clients.remove(client_socket)
                
                try:
                    client_socket.close()
                except:
                    pass
    
    def start_game(self, game_id):
            """Initializes the game and starts the Game Loop Thread."""
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
            GameStartMessage = MESSAGES.GameStartNotification.construct_payload(game_id, self.game_states[game_id].Get_players())
            self.Broadcast_to_game(game_id,GameStartMessage)
            self.send_Starting_Board_to_everyone(game_id)

            for username, client_socket in players.items():
                try:
                    threading.Thread(target=self.Handle_Player, args=(game_id, client_socket, username), daemon=True).start()
                except Exception as e:
                    print(f'Failed to start player {username}: {e}')

            # Start the Main Game Loop in a separate thread so it doesn't block the server
            threading.Thread(target=self.game_logic_loop, args=(game_id,), daemon=True).start()

    def send_message(self,client_socket:socket.socket,message:str):
        length_of_message = len(message)
        sent = False
        while not sent:
            if self.Client_sending_status[client_socket.fileno()] == False:
                self.Client_sending_status[client_socket.fileno()] = True
                client_socket.sendall(struct.pack('Q',length_of_message))
                client_socket.sendall(message)
                self.Client_sending_status[client_socket.fileno()] = False 
                sent = True    
            else:
                time.sleep(0.01)


    def send_Board_to_everyone(self,game_id):
        with self.game_locks[game_id]:
            for player,socket in self.games[game_id].items():
                board = self.game_states[game_id].Get_board(player)
                BoardMessage = MESSAGES.BoardDisplay.construct_payload(board)
                self.send_message(socket,BoardMessage.encode())
    
    def send_Starting_Board_to_everyone(self,game_id):
        with self.game_locks[game_id]:
            for player,socket in self.games[game_id].items():
                board = self.game_states[game_id].Get_board_before_game()
                BoardMessage = MESSAGES.BoardDisplay.construct_payload(board)
                self.send_message(socket,BoardMessage.encode())

    def game_logic_loop(self, game_id):
        """The Central Brain of the specific game instance."""
        print(f"Game Loop started for Game ID {game_id}")
        players = self.game_states[game_id].Get_players()
        next_player_index = 0
        next_player = players[next_player_index]
        game_state = self.game_states[game_id]
        client_socket = self.games[game_id][next_player]
        BuyCityRequestMessage = MESSAGES.BuyStartingCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player))
        self.Broadcast_to_game(game_id,BuyCityRequestMessage)
        
        while not self.kill:
        #add try
            # Get message from queue (blocking with timeout to allow checking self.kill)
            # This consumes messages put here by Handle_Player threads
            try:
                username, message = self.game_queues[game_id].get(timeout=1) 
                    
                msg_type = message.get('MessageType')
                print(f"Game {game_id} received {msg_type} from {username}")
                # --- GAME LOGIC PROCESSING ---
                if msg_type == 'BuyStartingCityResponse':
                    if game_state.Get_phase() == 1 and game_state.Get_round() == 0:
                            
                        if username == next_player:
                            city = MESSAGES.BuyStartingCityResponse.parse_payload(message)
                            if game_state.Set_starting_city(username,city):
                                next_player_index += 1
                                if len(players) == next_player_index:
                                    #Startpowerstation bidding
                                    pass
                                
                                self.send_Starting_Board_to_everyone(game_id)

                                if not game_state.Start_Game():
                                    
                                    next_player = players[next_player_index]
                                    BuyCityRequestMessage = MESSAGES.BuyStartingCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player))
                                    self.Broadcast_to_game(game_id,BuyCityRequestMessage)
                                else:
                                    if game_state.Start_Auction():
                                        market  = game_state.Get_Current_Market_String()
                                        valid_values = game_state.Get_Valid_station_values()
                                        next_player  = game_state.Get_Next_Bidder()
                                        BuyStartingStationMessage = MESSAGES.BuyStartingStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                                        self.Broadcast_to_game(game_id,BuyStartingStationMessage)

                            else:
                                BuyCityRequestMessage = MESSAGES.BuyStartingCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BuyCityRequestMessage)

                if msg_type == 'BuyStartingStationResponse':
                    if username == game_state.Get_Next_Bidder():
                        power_station_value = MESSAGES.BuyStartingStationResponse.parse_payload(message)
                        
                        if game_state.Starting_Bid_on_Power_Station(username,power_station_value):
                            if game_state.Finish_Auction():
                                    game_state.Do_Resource_Buying()
                                    self.send_Board_to_everyone(game_id)
                                    costs = game_state.Get_Resource_Costs()
                                    next_player = game_state.Get_Next_Resource_Buyer()
                                    stations = game_state.Get_PowerStations_of(next_player)
                                    resource_space = game_state.Get_Resource_Space_of(next_player)
                                    BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                    self.Broadcast_to_game(game_id,BuyResourcesMessage)
                            else:
                                next_player = game_state.Get_Next_Bidder_in_Round()
                                min_bid, station_info, held_by_player = game_state.Get_info_Bidding_Round()
                                BidOnPowerStationMessage = MESSAGES.BidOnPowerStation.construct_payload(station_info,min_bid,next_player,held_by_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BidOnPowerStationMessage)


                        else:
                            print("Invalid starting station bid")
                            market  = game_state.Get_Current_Market_String()
                            valid_values = game_state.Get_Valid_station_values()
                            next_player  = game_state.Get_Next_Bidder()
                            BuyStartingStationMessage = MESSAGES.BuyStartingStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                            self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                    else:
                        pass
                if msg_type == 'BidOnPowerStationResponse':
                    if username == game_state.Get_Next_Bidder_in_Round():
                        bid_amount = MESSAGES.BidOnPowerStationResponse.parse_payload(message)
                        if bid_amount is False:
                            winning_player, winning_bid, station_info, needs_to_discard = game_state.Resign_From_Bidding(username)
                            if needs_to_discard:
                                    # Notify player to discard a power station
                                    DiscardPowerStationMessage = MESSAGES.DiscardPowerStationRequest.construct_payload(winning_player.GetName(), game_state.Get_PowerStations_of(winning_player.GetName()))
                                    self.Broadcast_to_game(game_id, DiscardPowerStationMessage)

                            if winning_player:
                                message = MESSAGES.PlayerBoughtPowerStation.construct_payload(winning_player,station_info,winning_bid)
                                self.Broadcast_to_game(game_id,message)
                                # Proceed to next power station or next phase

                                next_player = game_state.Get_Next_Bidder()
                                if next_player:
                                    market  = game_state.Get_Current_Market_String()
                                    valid_values = game_state.Get_Valid_station_values()
                                    BuyStartingStationMessage = MESSAGES.BuyStartingStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                                    self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                                else:
                                    game_state.Finish_Auction()
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
                            game_state.Place_Bid(username,bid_amount) 
                            next_player = game_state.Get_Next_Bidder_in_Round()
                            if next_player:
                                min_bid, station_info, held_by_player = game_state.Get_info_Bidding_Round()
                                BidOnPowerStationMessage = MESSAGES.BidOnPowerStation.construct_payload(station_info,min_bid,next_player,held_by_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BidOnPowerStationMessage)
                if msg_type == 'DiscardPowerStationResponse':
                    power_station_value = MESSAGES.DiscardPowerStationResponse.parse_payload(message)
                    if username == game_state.Get_Waiting_Discard_Player():
                        discarded = game_state.Discard_PowerStation(username,power_station_value)
                        next_player = game_state.Get_Next_Bidder()
                        if discarded:
                            if next_player:
                                market  = game_state.Get_Current_Market_String()
                                valid_values = game_state.Get_Valid_station_values()
                                BuyStartingStationMessage = MESSAGES.BuyStartingStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                            else:
                                game_state.Finish_Auction()
                                game_state.Do_Resource_Buying()
                                self.send_Board_to_everyone(game_id)
                                costs = game_state.Get_Resource_Costs()
                                next_player = game_state.Get_Next_Resource_Buyer()
                                stations = game_state.Get_PowerStations_of(next_player)
                                resource_space = game_state.Get_Resource_Space_of(next_player)
                                BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                self.Broadcast_to_game(game_id,BuyResourcesMessage)


                if msg_type == 'BuyResourcesResponse':
                    if username == game_state.Get_Next_Resource_Buyer():
                        resources_to_buy = MESSAGES.BuyResourcesResponse.parse_payload(message)
                        resource = list(resources_to_buy.keys())
                        amount = list(resources_to_buy.values())
                        if len(resource) == len(amount) == 1:
                            resource = resource[0]
                            amount = amount[0]
                            game_state.Buy_Resource(username,resource,amount)
                            next_player = game_state.Get_Next_Resource_Buyer()
                            if next_player:
                                costs = game_state.Get_Resource_Costs()
                                stations = game_state.Get_PowerStations_of(next_player)
                                resource_space = game_state.Get_Resource_Space_of(next_player)
                                BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                self.Broadcast_to_game(game_id,BuyResourcesMessage)
                            else:
                                game_state.Finish_Resource_Buying()
                                # Proceed to next phase/turn
                                self.send_Board_to_everyone(game_id)
                                game_state.Do_City_Buying()
                                next_player = game_state.Get_Next_City_Buyer()
                                costs = game_state.Get_City_Costs(next_player)
                                BuyCityRequestMessage = MESSAGES.BuyCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player),costs)
                                self.Broadcast_to_game(game_id,BuyCityRequestMessage)
                        else:
                            # Invalid response, ask again
                            costs = game_state.Get_Resource_Costs()
                            stations = game_state.Get_PowerStations_of(username)
                            resource_space = game_state.Get_Resource_Space_of(username)
                            BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(username,costs,stations,resource_space)
                            self.Broadcast_to_game(game_id,BuyResourcesMessage)

                if msg_type == 'BuyCityResponse':
                    if username == game_state.Get_Next_City_Buyer():
                        city_id = MESSAGES.BuyCityResponse.parse_payload(message)
                        bought = game_state.Player_Buy_City(username,city_id)
                        if bought == True:
                            next_player = game_state.Get_Next_City_Buyer()
                            if next_player:
                                costs = game_state.Get_City_Costs(next_player)
                                self.send_Board_to_everyone(game_id)
                                BuyCityRequestMessage = MESSAGES.BuyCityRequest.construct_payload(next_player,game_state.Get_electros_of(next_player),costs)
                                self.Broadcast_to_game(game_id,BuyCityRequestMessage)


                            elif game_state.Finish_City_Buying():
                                game_state.Do_Bureaucracy()
                                self.send_Board_to_everyone(game_id)
                                next_player, electros , number_of_cities, power_stations, resources = game_state.Get_Info_For_Bureaucracy()
                                BureaucracyUpdateMessage = MESSAGES.BureaucracyUpdate.construct_payload(next_player,electros,number_of_cities,power_stations,resources)
                                self.Broadcast_to_game(game_id,BureaucracyUpdateMessage)


                        else:
                            BuyCityRequestMessage = MESSAGES.BuyCityRequest.construct_payload(username,game_state.Get_electros_of(username),game_state.Get_City_Costs(username))
                            self.Broadcast_to_game(game_id,BuyCityRequestMessage)
                            costs = game_state.Get_City_Costs(username)

                if msg_type == 'BureaucracyComplete':
                    power_station_dict_str = MESSAGES.BureaucracyComplete.parse_payload(message)
                    power_station_dict = ast.literal_eval(power_station_dict_str)
                    cities = game_state.Player_Do_Bureaucracy(username,power_station_dict)

                    if cities is False:
                        # Invalid bureaucracy, ask again
                        next_player, electros , number_of_cities, power_stations, resources = game_state.Get_Info_For_Bureaucracy()
                        BureaucracyUpdateMessage = MESSAGES.BureaucracyUpdate.construct_payload(next_player,electros,number_of_cities,power_stations,resources)
                        self.Broadcast_to_game(game_id,BureaucracyUpdateMessage)
                        
                    BureaucracyNotificationMessage = MESSAGES.BureaucracyNotification.construct_payload(username, cities)
                    self.Broadcast_to_game(game_id,BureaucracyNotificationMessage)
                    self.send_Board_to_everyone(game_id)
                    next_player, electros , number_of_cities, power_stations, resources = game_state.Get_Info_For_Bureaucracy()
                    if next_player:
                        BureaucracyUpdateMessage = MESSAGES.BureaucracyUpdate.construct_payload(next_player,electros,number_of_cities,power_stations,resources)
                        self.Broadcast_to_game(game_id,BureaucracyUpdateMessage)
                    else:
                        winner = game_state.Check_Stage_Change_And_Win()
                        # Proceed to next turn
                        if winner:
                            # End Game
                            print(f"Game {game_id} ended. Winner: {winner}")
                            # Notify players about the winner
                            # (Implementation of GameEndNotification message is assumed)
                            GameEndMessage = MESSAGES.GameEndNotification.construct_payload(winner)
                            self.Broadcast_to_game(game_id, GameEndMessage)
                            return  # Exit the game loop
                        
                        self.send_Board_to_everyone(game_id)

                        if game_state.Start_Auction():
                            next_player = game_state.Get_Next_Bidder()
                            market  = game_state.Get_Current_Market_String()
                            valid_values = game_state.Get_Valid_station_values()
                            BuyStartingStationMessage = MESSAGES.BuyPowerStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                            self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                        else:
                            raise Exception("Failed to start auction after bureaucracy.")

                if msg_type == 'BuyPowerStationResponse':
                    if username == game_state.Get_Next_Bidder():
                        power_station_value = MESSAGES.BuyPowerStationResponse.parse_payload(message)
                        if power_station_value is False:
                            game_state.Resign_from_auction(username)
                            next_player = game_state.Get_Next_Bidder()
                            if next_player:
                                market  = game_state.Get_Current_Market_String()
                                valid_values = game_state.Get_Valid_station_values()
                                BuyStartingStationMessage = MESSAGES.BuyPowerStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BuyStartingStationMessage)

                            if game_state.Finish_Auction():
                                    game_state.Do_Resource_Buying()
                                    self.send_Board_to_everyone(game_id)
                                    costs = game_state.Get_Resource_Costs()
                                    next_player = game_state.Get_Next_Resource_Buyer()
                                    stations = game_state.Get_PowerStations_of(next_player)
                                    resource_space = game_state.Get_Resource_Space_of(next_player)
                                    BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                    self.Broadcast_to_game(game_id,BuyResourcesMessage)

                        if game_state.Starting_Bid_on_Power_Station(username,power_station_value):
                            if game_state.Finish_Auction():
                                    game_state.Do_Resource_Buying()
                                    self.send_Board_to_everyone(game_id)
                                    costs = game_state.Get_Resource_Costs()
                                    next_player = game_state.Get_Next_Resource_Buyer()
                                    stations = game_state.Get_PowerStations_of(next_player)
                                    resource_space = game_state.Get_Resource_Space_of(next_player)
                                    BuyResourcesMessage = MESSAGES.BuyResourcesRequest.construct_payload(next_player,costs,stations,resource_space)
                                    self.Broadcast_to_game(game_id,BuyResourcesMessage)
                            else:
                                next_player = game_state.Get_Next_Bidder_in_Round()
                                min_bid, station_info, held_by_player = game_state.Get_info_Bidding_Round()
                                BidOnPowerStationMessage = MESSAGES.BidOnPowerStation.construct_payload(station_info,min_bid,next_player,held_by_player,game_state.Get_electros_of(next_player))
                                self.Broadcast_to_game(game_id,BidOnPowerStationMessage)


                        else:
                            print("Invalid station bid")
                            market  = game_state.Get_Current_Market_String()
                            valid_values = game_state.Get_Valid_station_values()
                            next_player  = game_state.Get_Next_Bidder()
                            BuyStartingStationMessage = MESSAGES.BuyPowerStationRequest.construct_payload(market,next_player,valid_values,game_state.Get_electros_of(next_player))
                            self.Broadcast_to_game(game_id,BuyStartingStationMessage)
                    else:
                        pass


                        

                            


                # Add other game logic handling here...
            except queue.Empty:
                time.sleep(0.05)


            #add exception handling
    
    def Broadcast_to_game(self,game_id,message):
        for client_socket in self.games[game_id].values():
            self.send_message(client_socket,message.encode())
        return

                
    def Handle_Player(self, game_id, client_socket: socket.socket, username: str):
        MAX_MESSAGE_SIZE = 10 * 1024 * 1024 # 10 MB Limit

        while not self.kill:
            try:
                length_bytes = client_socket.recv(self.RECIEVE_LENGTH)
                
                if not length_bytes:
                    print(f"Player {username} disconnected.")
                    break
                
                # 1. Validation Checks
                if len(length_bytes) < 8:
                    break
                
                msg_length = struct.unpack('Q', length_bytes)[0]

                if msg_length > MAX_MESSAGE_SIZE:
                    print(f"Security: {username} sent too much data.")
                    break

                # 2. Receive Data
                data = client_socket.recv(msg_length)
                
                if not data:
                    break
                
                # 3. Decode
                # Note: ast.literal_eval is safer than eval, but still expects a string representation of a python object
                message = ast.literal_eval(data.decode())
                
                self.game_queues[game_id].put((username, message))
                
            except ConnectionResetError:
                print(f"Player {username} disconnected abruptly.")
                break 
            except Exception as e:
                print(f"Error in Handle_Player for {username}: {e}")
                break
        
        # --- CLEANUP ---
        print(f"Handle_Player thread for {username} stopping.")
        # Add code here to notify the GameLoop that a player has left!

    def check_and_start_games(self):
        while not self.kill:
            if len(self.ready_clients) >= self.MIN_CLIENTS:
                self.games.append({})
                self.lobby_game_index = len(self.games) - 1
                while len(self.games[self.lobby_game_index].keys()) < self.MAX_CLIENTS:
                    client = self.ready_clients.pop(0)
                    self.games[self.lobby_game_index][client[0]] = client[1]
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