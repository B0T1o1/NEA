from .ui.uis import GUIC, UIC
import socket
import threading
import time
import struct
import ast
import traceback  # Essential for debugging thread crashes
from shared import MESSAGES
from shared.encryption import RSA
from math import inf

class ClientC:
    """Main Client Class, handles network and UI interactions
    """
    RECEIVE_LENGTH = 8  

    def __init__(self, host:str='127.0.0.1', port:int=65432):
        """Initializes the client with the specified host and port.

        Args:
            host (str): IP address of server to connect to. Defaults to '127.0.0.1'.
            port (int): Port number of server to connect to. Defaults to 65432.
        """
        self.host = host
        self.port = port
        self.UI = UIC()     # This is a wrapper around the actual UI implementation to handle gui and tui
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.kill = False
        self.username = ''  # Will be set upon successful login

    def connect(self):
        """Attempts to connnect to the server
        """
        try:
            self.client_socket.connect((self.host, self.port))
            print('Connected to server at {}:{}'.format(self.host, self.port))
        except ConnectionRefusedError:
            print('Connection refused by the server.')
            self.kill = True

    def send_message(self, client_socket: socket.socket, message: bytes):
        """sends a message to ther server

        Args:
            client_socket (socket.socket):  client socket to send message
            message (bytes): message to send (already encoded)
        """
        length_of_message = len(message)
        # Pack length as unsigned long long (Q)
        header = struct.pack('Q', length_of_message)
        client_socket.sendall(header)
        client_socket.sendall(message)

    def receiveMessage(self):
        """Runs in background thread to receive messages from server, handles logic appropriately
        """
        while not self.kill:
            try:
                # 1. Receive header (8 bytes)
                length_bytes = self.client_socket.recv(self.RECEIVE_LENGTH)

                if not length_bytes:
                    print("Disconnected from server.")
                    self.kill = True
                    break

                # 2. Receive data based on header
                msg_length = struct.unpack('Q', length_bytes)[0]
                data = self.client_socket.recv(msg_length)

                if data:
                    # Parse data safely
                    decoded_data = data.decode().replace("inf", "'inf'")
                    message = ast.literal_eval(decoded_data)
                    MessageType = MESSAGES.Message.parse_payload(message)

                    print(f"Received message of type: {MessageType}")

                    # --- MESSAGE HANDLING ---
                    
                    if MessageType == 'LoginRequest':
                        # Get server public key and respond with login or registration
                        server_public_key = MESSAGES.LoginRequest.parse_payload(message)
                        choice = self.UI.GetLogin_or_Register()
                        
                        if choice == 'login':
                            # Prompt for login details
                            username, password = self.UI.GetLoginDetails()
                            # Construct and send encrypted login payload
                            payload = MESSAGES.LoginResponse.construct_payload(username, password)
                            encrypted_payload = str(RSA.encrypt(payload, server_public_key))
                            self.send_message(self.client_socket, encrypted_payload.encode())

                        elif choice == 'register':
                            # Prompt for registration details
                            username, password = self.UI.GetRegisterDetails()
                            # Construct and send encrypted registration payload
                            payload = MESSAGES.RegisterRequest.construct_payload(username, password)
                            encrypted_payload = str(RSA.encrypt(payload, server_public_key))
                            self.send_message(self.client_socket, encrypted_payload.encode())

                    elif MessageType == 'LoginConfirmation':
                        # Handle login confirmation
                        success = MESSAGES.LoginConfirmation.parse_payload(message)
                        if success:
                            self.username = username  # Save username locally
                            # Inform user of successful login
                            self.UI.DisplayMessage('Login successful!')
                        else:
                            # Inform user of failed login attempt
                            self.UI.DisplayMessage('Login failed. Please check your credentials.')

                    elif MessageType == 'RegisterResponse':
                        # Handle registration response
                        success = MESSAGES.RegisterResponse.parse_payload(message)
                        if success:
                            # Inform user of successful registration
                            self.UI.DisplayMessage('Registration successful! You can now log in.')
                        else:
                            # Inform user of failed registration attempt
                            self.UI.DisplayMessage('Registration failed. Username may already be taken.')

                    elif MessageType == 'GameStartNotification':
                        # Handle game start notification
                        game_id, players = MESSAGES.GameStartNotification.parse_payload(message)
                        # Display to user that game is starting
                        self.UI.DisplayPlayerList(players)

                    elif MessageType == 'BoardDisplay':
                        # Handle full board display
                        board_info = MESSAGES.BoardDisplay.parse_payload(message)
                        # Display the full board information
                        self.UI.DisplayFullBoard(board_info)

                    elif MessageType == 'StartBoardDisplay':
                        # Handle starting board display
                        info = MESSAGES.StartBoardDisplay.parse_payload(message)
                        # Display the starting board information
                        self.UI.DisplayStartingBoard(info)

                    elif MessageType == 'BuyStartingCityRequest':
                        # Handle request to buy starting city
                        current_player, electros = MESSAGES.BuyStartingCityRequest.parse_payload(message)
                        # Check if its this client's turn
                        if current_player == self.username: 
                            # Prompt user to select starting city
                            city = self.UI.GetStartingCity()
                            # Send selected city back to server
                            citymessage = MESSAGES.BuyStartingCityResponse.construct_payload(city)
                            self.send_message(self.client_socket, citymessage.encode())
                        else:
                            # Inform user to wait for their turn
                            self.UI.DisplayMessage(f'{current_player} is buying their first city.')
                            self.UI.DisplayElectros(current_player, electros)

                    elif MessageType == 'BuyStartingStationRequest':
                        # Handle request to buy starting power station
                        market, current_player, valid_values, electros = MESSAGES.BuyStartingStationRequest.parse_payload(message)
                        # Display market to user
                        self.UI.DisplayMarket(market)
                        # Check if its this client's turn
                        if self.username == current_player:
                            # Prompt user to select starting power station
                            station_value = self.UI.GetStartingBid(True, valid_values, electros)
                            # Send selected station back to server
                            payload = MESSAGES.BuyStartingStationResponse.construct_payload(station_value)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            # Inform user to wait for their turn
                            self.UI.DisplayElectros(current_player, electros)
                            self.UI.DisplayMessage(f'Waiting for {current_player} to place their bid.')

                    elif MessageType == 'BidOnPowerStation':
                        # Handle bidding on power station
                        powerstation, min_bid, current_player, held_by_player, electros = MESSAGES.BidOnPowerStation.parse_payload(message)
                        # Check if its this client's turn
                        if self.username == current_player:
                            # Prompt user to place a bid
                            Bid = self.UI.GetBidOnPowerStation(held_by_player, electros, min_bid, powerstation)
                            # Send bid back to server
                            payload = MESSAGES.BidOnPowerStationResponse.construct_payload(Bid)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            # Inform user to wait for their turn
                            self.UI.DisplayElectros(current_player, electros)
                            self.UI.DisplayMessage(f'Waiting for {current_player} to bid on station {powerstation} (Min: {min_bid}).')

                    elif MessageType == 'PlayerBoughtPowerStation':
                        # Handle notification of player buying power station
                        player_name, powerstation_value, winning_bid = MESSAGES.PlayerBoughtPowerStation.parse_payload(message)
                        # Displya to the user
                        self.UI.DisplayMessage(f'{player_name} bought station {powerstation_value} for {winning_bid}.')

                    elif MessageType == 'BuyResourcesRequest':
                        # Request to buy resources
                        current_player, resource_costs, PowerStations, resource_space = MESSAGES.BuyResourcesRequest.parse_payload(message)
                        # Check if its this client's turn
                        if current_player == self.username:
                            # Prompt user to select resources to buy
                            resources_to_buy = self.UI.GetResourcesToBuy(resource_costs, PowerStations, resource_space)
                            # Send selected resources back to server
                            payload = MESSAGES.BuyResourcesResponse.construct_payload(resources_to_buy)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            # Inform user to wait for their turn
                            self.UI.DisplayMessage(f'Waiting for {current_player} to buy resources.')

                    elif MessageType == 'BuyCityRequest':
                        # Request to buy a city
                        current_player, electros, costs = MESSAGES.BuyCityRequest.parse_payload(message)
                        # Check if its this client's turn
                        if current_player == self.username:
                            # Prompt user to select city to buy
                            city = self.UI.Get_City_To_Buy(electros, costs)
                            # Send selected city back to server
                            payload = MESSAGES.BuyCityResponse.construct_payload(city)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            # Inform user to wait for their turn
                            self.UI.DisplayMessage(f'Waiting for {current_player} to buy a city.')
                            self.UI.DisplayElectros(current_player, electros)

                    elif MessageType == 'BureaucracyUpdate':
                        # Handle bureaucracy update
                        player_name, electros, number_of_cities, power_stations, resources = MESSAGES.BureaucracyUpdate.parse_payload(message)
                        # Check if its this client's turn
                        if player_name == self.username:
                            # Prompt user to complete bureaucracy
                            plan = self.UI.DisplayBureaucracyUpdate(number_of_cities, power_stations, resources)
                            # Send completed plan back to server
                            payload = MESSAGES.BureaucracyComplete.construct_payload(plan)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            # Inform user to wait for their turn
                            self.UI.DisplayMessage(f'Waiting for {player_name} to complete bureaucracy.')

                    elif MessageType == 'GameEndNotification':
                        # Handle game end notification
                        winner_name = MESSAGES.GameEndNotification.parse_payload(message)
                        # Check if this client is the winner
                        if winner_name == self.username:
                            # Tell user they have won
                            self.UI.DisplayMessage('Congratulations! You have won the game!')
                        else:
                            # Inform user of the winner and end of game
                            self.UI.DisplayMessage(f'Game over! The winner is {winner_name}.')

                    elif MessageType == 'BuyPowerStationRequest':
                        # Handle request to buy power station
                        market, current_player, electros,valid_values = MESSAGES.BuyPowerStationRequest.parse_payload(message)
                        # Display market to user
                        self.UI.DisplayMarket(market)
                        # Check if its this client's turn
                        if self.username == current_player:
                            # Prompt user to select power station to buy
                            station_value = self.UI.GetStartingBid(False, valid_values, electros)
                            # Send selected station back to server
                            payload = MESSAGES.BuyPowerStationResponse.construct_payload(station_value)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            # Inform user to wait for their turn
                            self.UI.DisplayElectros(current_player, electros)
                            self.UI.DisplayMessage(f'Waiting for {current_player} to start a bid.')

                    elif MessageType == 'BureaucracyNotification':
                        # Handle bureaucracy notification
                        player, number_cities_powered = MESSAGES.BureaucracyNotification.parse_payload(message)
                        # Display to the user
                        self.UI.DisplayMessage(f'{player} has powered {number_cities_powered} cities.')

                    elif MessageType == 'DiscardPowerStationRequest':
                        # Handle request to discard power station
                        player, power_stations = MESSAGES.DiscardPowerStationRequest.parse_payload(message)
                        # Check if its this client's turn
                        if self.username == player:
                            # Prompt user to select power station to discard
                            station_value = self.UI.GetPowerStationToDiscard(power_stations)
                            # Send selected station back to server
                            payload = MESSAGES.DiscardPowerStationResponse.construct_payload(station_value)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            # Inform user to wait for their turn
                            self.UI.DisplayMessage(f'Waiting for {player} to discard a power station.')

                else:
                    print('Server closed the connection.')
                    self.kill = True

            except ConnectionResetError:
                print('Connection was reset by the server.')
                self.kill = True
            except Exception as e:
                print("\n!!! CRITICAL ERROR IN RECEIVE THREAD !!!")
                traceback.print_exc()
                self.kill = True

    def run(self):
        """Main run loop for the client
        """
        self.connect()
        if self.kill:
            return

        # 1. Start the Network Thread
        receiver_thread = threading.Thread(target=self.receiveMessage, daemon=True)
        receiver_thread.start()

        # 2. Start the UI Loop

        if hasattr(self.UI.UI, "Start"): # GUI loop
            self.UI.UI.Start()
        else:
            # Terminal UI fallback loop
            while not self.kill:
                time.sleep(1)

if __name__ == '__main__':
    client = ClientC()
    client.run()