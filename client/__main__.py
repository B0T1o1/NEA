from .ui.uis import UIC
import socket
import threading
import time
import struct
from shared import MESSAGES
from shared.encryption import RSA 
from math import inf
import math
import ast
class ClientC():
    RECIEVE_LENGTH = 8
    def __init__(self,host = '127.0.0.1',port=65432):
        self.host = host
        self.port = port
        self.UI = UIC()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.kill = False
        self.username = ''

    def connect(self):
        try:
            self.client_socket.connect((self.host,self.port))
            print('Connected to server at {}:{}'.format(self.host,self.port))
        except ConnectionRefusedError:
            print('Connection refused by the server.')
            self.kill = True


    def send_message(self,client_socket:socket.socket,message:str):
        length_of_message = len(message)
        client_socket.sendall(struct.pack('Q',length_of_message))
        client_socket.sendall(message)

    def receiveMessage(self):
            # Ensure ast is imported at the top of your file: import ast
            while not self.kill:
                try:
                    # 1. Receive header
                    length_bytes = self.client_socket.recv(self.RECIEVE_LENGTH)
                    
                    if not length_bytes:
                        print("Disconnected from server.")
                        self.kill = True
                        break

                    # 2. Receive data based on header
                    msg_length = struct.unpack('Q', length_bytes)[0]
                    data = self.client_socket.recv(msg_length)
                    
                    if data:
                        # Use ast.literal_eval for safety
                        
                        message = ast.literal_eval(data.decode().replace("inf","'inf'"))
                        MessageType = MESSAGES.Message.parse_payload(message)
                        
                        print(f"Received message of type: {MessageType}")
                        
                        if MessageType == 'LoginRequest':
                            server_public_key = MESSAGES.LoginRequest.parse_payload(message)
                            choice = self.UI.GetLogin_or_Register()
                            
                            if choice == 'login':
                                username, password = self.UI.GetLoginDetails()
                                # Encrypt the payload
                                encrypted_payload = str(RSA.encrypt(
                                    MESSAGES.LoginResponse.construct_payload(username, password),
                                    server_public_key
                                ))
                                # FIX: Use send_message to attach the 8-byte header
                                self.send_message(self.client_socket, encrypted_payload.encode())
                                
                            elif choice == 'register':
                                username, password = self.UI.GetRegisterDetails()
                                encrypted_payload = str(RSA.encrypt(
                                    MESSAGES.RegisterRequest.construct_payload(username, password),
                                    server_public_key
                                ))
                                # FIX: Use send_message to attach the 8-byte header
                                self.send_message(self.client_socket, encrypted_payload.encode())

                        elif MessageType == 'LoginConfirmation':
                            success = MESSAGES.LoginConfirmation.parse_payload(message)
                            if success:
                                self.username = username # Save username locally
                                self.UI.UI.DisplayMessage('Login successful!')
                            else:
                                self.UI.UI.DisplayMessage('Login failed. Please check your credentials.')
                                
                        elif MessageType == 'RegisterResponse':
                            success = MESSAGES.RegisterResponse.parse_payload(message)
                            if success:
                                self.UI.UI.DisplayMessage('Registration successful! You can now log in.')
                            else:
                                self.UI.UI.DisplayMessage('Registration failed. Username may already be taken.')

                        elif MessageType == 'GameStartNotification':
                            game_id, players = MESSAGES.GameStartNotification.parse_payload(message)
                            self.UI.DisplayPlayerList(players)

                        elif MessageType == 'BoardDisplay':
                            board_info = MESSAGES.BoardDisplay.parse_payload(message)
                            self.UI.DisplayBoard(board_info)
                            
                        elif MessageType == 'BuyStartingCityRequest':
                            current_player,electros = MESSAGES.BuyStartingCityRequest.parse_payload(message)
                            
                            if current_player == self.username:
                                city = self.UI.GetStartingCity()
                                citymessage = MESSAGES.BuyStartingCityResponse.construct_payload(city)
                                # FIX: Use send_message to attach the 8-byte header
                                self.send_message(self.client_socket, citymessage.encode())
                            else:
                                self.UI.DisplayMessage(f'{current_player} is currently buying their first city.')
                                self.UI.DisplayElectros(current_player,electros)
                        elif MessageType == 'BuyStartingStationRequest':
                            market, current_player,valid_values,electros = MESSAGES.BuyStartingStationRequest.parse_payload(message)
                            self.UI.DisplayMarket(market)
                            if self.username == current_player:
                                station_value = self.UI.GetStartingBid(True,valid_values,electros)
                                message = MESSAGES.BuyStartingStationResponse.construct_payload(station_value)
                                self.send_message(self.client_socket,message.encode())
                            else:
                                self.UI.DisplayElectros(current_player,electros)
                                self.UI.DisplayMessage(f'Waiting for {current_player} to place their bid on a power station.')
                        elif MessageType == 'BidOnPowerStation':
                            powerstation, min_bid, current_player,held_by_player, electros = MESSAGES.BidOnPowerStation.parse_payload(message)
                            if self.username == current_player:
                                Bid = self.UI.GetBidOnPowerStation(held_by_player,electros,min_bid,powerstation)
                                BidOnPowerStationResponse = MESSAGES.BidOnPowerStationResponse.construct_payload(Bid)
                                self.send_message(self.client_socket,BidOnPowerStationResponse.encode())
                            else:
                                self.UI.DisplayElectros(current_player,electros)
                                self.UI.DisplayMessage(f'Waiting for {current_player} to place their bid on the power station worth {powerstation} with a minimum bid of {min_bid}.')

                        elif MessageType == 'PlayerBoughtPowerStation':
                            player_name, powerstation_value , winning_bid = MESSAGES.PlayerBoughtPowerStation.parse_payload(message)
                            self.UI.DisplayMessage(f'{player_name} has successfully bought the power station worth {powerstation_value} with a winning bid of {winning_bid}.')
                        elif MessageType == 'BuyResourcesRequest':
                            current_player,resource_costs,PowerStations,resource_space = MESSAGES.BuyResourcesRequest.parse_payload(message)
                            if current_player == self.username:
                                resources_to_buy = self.UI.GetResourcesToBuy(resource_costs,PowerStations,resource_space)
                                
                                buy_resources_message = MESSAGES.BuyResourcesResponse.construct_payload(resources_to_buy)
                                self.send_message(self.client_socket,buy_resources_message.encode())
                                
                            else:
                                self.UI.DisplayMessage(f'Waiting for {current_player} to buy resources.')
                        elif MessageType == 'BuyCityRequest':
                            current_player,electros,costs = MESSAGES.BuyCityRequest.parse_payload(message)
                            if current_player == self.username:
                                city = self.UI.Get_City_To_Buy(electros,costs)
                                citymessage = MESSAGES.BuyCityResponse.construct_payload(city)
                                self.send_message(self.client_socket, citymessage.encode())
                            else:
                                self.UI.DisplayMessage(f'Waiting for {current_player} to buy a city.')
                                self.UI.DisplayElectros(current_player,electros)
                        elif MessageType == 'BureaucracyUpdate':
                            player_name,electros,number_of_cities,power_stations,resources = MESSAGES.BureaucracyUpdate.parse_payload(message)
                            if player_name == self.username:
                                plan = self.UI.DisplayBureaucracyUpdate(number_of_cities,power_stations,resources)
                                BureacracyCompleteMessage = MESSAGES.BureaucracyComplete.construct_payload(plan)
                                self.send_message(self.client_socket,BureacracyCompleteMessage.encode())
                            else:
                                self.UI.DisplayMessage(f'Waiting for {player_name} to complete bureaucracy phase.')
                        elif MessageType == 'GameEndNotification':
                            winner_name = MESSAGES.GameEndNotification.parse_payload(message)
                            if winner_name == self.username:
                                self.UI.DisplayMessage('Congratulations! You have won the game!')
                            else:
                                self.UI.DisplayMessage(f'Game over! The winner is {winner_name}. Better luck next time!')
                        elif MessageType == 'BuyPowerStationRequest':
                            market, current_player,valid_values,electros = MESSAGES.BuyPowerStationRequest.parse_payload(message)
                            self.UI.DisplayMarket(market)
                            if self.username == current_player:
                                station_value = self.UI.GetStartingBid(False,valid_values,electros)
                                message = MESSAGES.BuyPowerStationResponse.construct_payload(station_value)
                                self.send_message(self.client_socket,message.encode())
                            else:
                                self.UI.DisplayElectros(current_player,electros)
                                self.UI.DisplayMessage(f'Waiting for {current_player} to place their bid on a power station.')
                                """
                                elif MessageType ==  'BidOnPowerStation':
                                    powerstation, min_bid, current_player,held_by_player, electros = MESSAGES.BidOnPowerStation.parse_payload(message)
                                    if self.username == current_player:
                                        Bid = self.UI.GetBidOnPowerStation(held_by_player,electros,min_bid,powerstation)
                                        BidOnPowerStationResponse = MESSAGES.BidOnPowerStationResponse.construct_payload(Bid)
                                        self.send_message(self.client_socket,BidOnPowerStationResponse.encode())
                                    else:
                                        self.UI.DisplayElectros(current_player,electros)
                                        self.UI.DisplayMessage(f'Waiting for {current_player} to place their bid on the power station worth {powerstation} with a minimum bid of {min_bid}.')
                                """
                        elif MessageType == 'BureaucracyNotification':
                            player, number_cities_powered = MESSAGES.BureaucracyNotification.parse_payload(message)
                            self.UI.DisplayMessage(f'{player} has powered {number_cities_powered} cities this turn.')
                        elif MessageType == 'DiscardPowerStationRequest':
                            player, power_stations = MESSAGES.DiscardPowerStationRequest.parse_payload(message)
                            if self.username == current_player:
                                station_value = self.UI.GetPowerStationToDiscard(power_stations)
                                message = MESSAGES.DiscardPowerStationResponse.construct_payload(station_value)
                                self.send_message(self.client_socket,message.encode())
                            else:
                                self.UI.DisplayMessage(f'Waiting for {player} to discard a power station.')
                    else:
                        print('Server closed the connection.')
                        self.kill = True
                
                except ConnectionResetError:
                    print('Connection was reset by the server.')
                    self.kill = True
                #add generic exception catch to prevent client crashing
                '''
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    self.kill = True
                '''
    def run(self):
        self.connect()
        if self.kill:
            return
        
        receiver_thread = threading.Thread(target=self.receiveMessage,daemon=True)
        receiver_thread.start()

        try:
            while not self.kill:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("Shutting down client.")
            self.kill = True
            self.client_socket.close()
        
        receiver_thread.join(timeout=2)


if __name__ == '__main__':
    client = ClientC()
    client.run()