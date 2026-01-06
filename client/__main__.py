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
    RECEIVE_LENGTH = 8  # Fixed typo (EI -> IE)

    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.UI = UIC()  # This is your wrapper
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.kill = False
        self.username = ''

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print('Connected to server at {}:{}'.format(self.host, self.port))
        except ConnectionRefusedError:
            print('Connection refused by the server.')
            self.kill = True

    def send_message(self, client_socket: socket.socket, message: bytes):
        """Sends a message prefixed with an 8-byte length header."""
        length_of_message = len(message)
        # Pack length as unsigned long long (Q)
        header = struct.pack('Q', length_of_message)
        client_socket.sendall(header)
        client_socket.sendall(message)

    def receiveMessage(self):
        """Runs in a background thread to listen for server messages."""
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
                        server_public_key = MESSAGES.LoginRequest.parse_payload(message)
                        choice = self.UI.GetLogin_or_Register()

                        if choice == 'login':
                            username, password = self.UI.GetLoginDetails()
                            payload = MESSAGES.LoginResponse.construct_payload(username, password)
                            encrypted_payload = str(RSA.encrypt(payload, server_public_key))
                            self.send_message(self.client_socket, encrypted_payload.encode())

                        elif choice == 'register':
                            username, password = self.UI.GetRegisterDetails()
                            payload = MESSAGES.RegisterRequest.construct_payload(username, password)
                            encrypted_payload = str(RSA.encrypt(payload, server_public_key))
                            self.send_message(self.client_socket, encrypted_payload.encode())

                    elif MessageType == 'LoginConfirmation':
                        success = MESSAGES.LoginConfirmation.parse_payload(message)
                        if success:
                            self.username = username  # Save username locally
                            self.UI.DisplayMessage('Login successful!')
                        else:
                            self.UI.DisplayMessage('Login failed. Please check your credentials.')

                    elif MessageType == 'RegisterResponse':
                        success = MESSAGES.RegisterResponse.parse_payload(message)
                        if success:
                            self.UI.DisplayMessage('Registration successful! You can now log in.')
                        else:
                            self.UI.DisplayMessage('Registration failed. Username may already be taken.')

                    elif MessageType == 'GameStartNotification':
                        game_id, players = MESSAGES.GameStartNotification.parse_payload(message)
                        self.UI.DisplayPlayerList(players)

                    elif MessageType == 'BoardDisplay':
                        board_info = MESSAGES.BoardDisplay.parse_payload(message)
                        self.UI.DisplayFullBoard(board_info)

                    elif MessageType == 'StartBoardDisplay':
                        info = MESSAGES.StartBoardDisplay.parse_payload(message)
                        self.UI.DisplayStartingBoard(info)

                    elif MessageType == 'BuyStartingCityRequest':
                        current_player, electros = MESSAGES.BuyStartingCityRequest.parse_payload(message)
                        if current_player == self.username:
                            city = self.UI.GetStartingCity()
                            citymessage = MESSAGES.BuyStartingCityResponse.construct_payload(city)
                            self.send_message(self.client_socket, citymessage.encode())
                        else:
                            self.UI.DisplayMessage(f'{current_player} is buying their first city.')
                            self.UI.DisplayElectros(current_player, electros)

                    elif MessageType == 'BuyStartingStationRequest':
                        market, current_player, valid_values, electros = MESSAGES.BuyStartingStationRequest.parse_payload(message)
                        self.UI.DisplayMarket(market)
                        if self.username == current_player:
                            station_value = self.UI.GetStartingBid(True, valid_values, electros)
                            payload = MESSAGES.BuyStartingStationResponse.construct_payload(station_value)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            self.UI.DisplayElectros(current_player, electros)
                            self.UI.DisplayMessage(f'Waiting for {current_player} to place their bid.')

                    elif MessageType == 'BidOnPowerStation':
                        powerstation, min_bid, current_player, held_by_player, electros = MESSAGES.BidOnPowerStation.parse_payload(message)
                        if self.username == current_player:
                            Bid = self.UI.GetBidOnPowerStation(held_by_player, electros, min_bid, powerstation)
                            payload = MESSAGES.BidOnPowerStationResponse.construct_payload(Bid)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            self.UI.DisplayElectros(current_player, electros)
                            self.UI.DisplayMessage(f'Waiting for {current_player} to bid on station {powerstation} (Min: {min_bid}).')

                    elif MessageType == 'PlayerBoughtPowerStation':
                        player_name, powerstation_value, winning_bid = MESSAGES.PlayerBoughtPowerStation.parse_payload(message)
                        self.UI.DisplayMessage(f'{player_name} bought station {powerstation_value} for {winning_bid}.')

                    elif MessageType == 'BuyResourcesRequest':
                        current_player, resource_costs, PowerStations, resource_space = MESSAGES.BuyResourcesRequest.parse_payload(message)
                        if current_player == self.username:
                            resources_to_buy = self.UI.GetResourcesToBuy(resource_costs, PowerStations, resource_space)
                            payload = MESSAGES.BuyResourcesResponse.construct_payload(resources_to_buy)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            self.UI.DisplayMessage(f'Waiting for {current_player} to buy resources.')

                    elif MessageType == 'BuyCityRequest':
                        current_player, electros, costs = MESSAGES.BuyCityRequest.parse_payload(message)
                        if current_player == self.username:
                            city = self.UI.Get_City_To_Buy(electros, costs)
                            payload = MESSAGES.BuyCityResponse.construct_payload(city)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            self.UI.DisplayMessage(f'Waiting for {current_player} to buy a city.')
                            self.UI.DisplayElectros(current_player, electros)

                    elif MessageType == 'BureaucracyUpdate':
                        player_name, electros, number_of_cities, power_stations, resources = MESSAGES.BureaucracyUpdate.parse_payload(message)
                        if player_name == self.username:
                            plan = self.UI.DisplayBureaucracyUpdate(number_of_cities, power_stations, resources)
                            payload = MESSAGES.BureaucracyComplete.construct_payload(plan)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            self.UI.DisplayMessage(f'Waiting for {player_name} to complete bureaucracy.')

                    elif MessageType == 'GameEndNotification':
                        winner_name = MESSAGES.GameEndNotification.parse_payload(message)
                        if winner_name == self.username:
                            self.UI.DisplayMessage('Congratulations! You have won the game!')
                        else:
                            self.UI.DisplayMessage(f'Game over! The winner is {winner_name}.')

                    elif MessageType == 'BuyPowerStationRequest':
                        market, current_player, valid_values, electros = MESSAGES.BuyPowerStationRequest.parse_payload(message)
                        self.UI.DisplayMarket(market)
                        if self.username == current_player:
                            station_value = self.UI.GetStartingBid(False, valid_values, electros)
                            payload = MESSAGES.BuyPowerStationResponse.construct_payload(station_value)
                            self.send_message(self.client_socket, payload.encode())
                        else:
                            self.UI.DisplayElectros(current_player, electros)
                            self.UI.DisplayMessage(f'Waiting for {current_player} to start a bid.')

                    elif MessageType == 'BureaucracyNotification':
                        player, number_cities_powered = MESSAGES.BureaucracyNotification.parse_payload(message)
                        self.UI.DisplayMessage(f'{player} has powered {number_cities_powered} cities.')

                    elif MessageType == 'DiscardPowerStationRequest':
                        player, power_stations = MESSAGES.DiscardPowerStationRequest.parse_payload(message)
                        if self.username == player:
                            station_value = self.UI.GetPowerStationToDiscard(power_stations)
                            payload = MESSAGES.DiscardPowerStationResponse.construct_payload(station_value)
                            self.send_message(self.client_socket, payload.encode())
                        else:
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
        self.connect()
        if self.kill:
            return

        # 1. Start the Network Thread
        receiver_thread = threading.Thread(target=self.receiveMessage, daemon=True)
        receiver_thread.start()

        # 2. Start the UI Loop (This blocks the main thread if using GUI)
        # Note: We check self.UI.UI because self.UI is the wrapper, 
        # and self.UI.UI is the implementation (GUIC or TUIC).
        if hasattr(self.UI.UI, "Start"):
            self.UI.UI.Start()
        else:
            # Terminal UI fallback loop
            while not self.kill:
                time.sleep(1)

if __name__ == '__main__':
    client = ClientC()
    client.run()