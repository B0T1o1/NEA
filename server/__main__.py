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
        self.clients = []
        self.queue = []
        self.ready_clients = []
        self.lobby_game_index = 0
        self.games = [[]]
        self.game_states: dict[int, GameStateC] = {}
        self.MAX_CLIENTS = 6
        self.MIN_CLIENTS = 3
        self.kill = False

    def connection_listen_loop(self):
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
            RSA_keypair = RSA.generate_keypair()
            private_key = RSA_keypair[1]
            message = MESSAGES.LoginRequest.construct_payload(public_key=RSA_keypair[0])
            client_socket.sendall(message.encode())
            print('Sent LoginRequest with public key to client.')

            while not self.kill:
                data = client_socket.recv(1024)
                if data:
                    message = eval(RSA.decrypt(int(data.decode()), private_key))
                    MessageType = message['MessageType']
                    print(f"Received message of type: {MessageType}")
                    if message['MessageType'] == 'LoginResponse':
                        username,password = MESSAGES.LoginResponse.parse_payload(message)
                        print(password)
                        conn = sqlite3.connect(db_path)
                        cur = conn.cursor()
                        cur.execute("SELECT * FROM usersdata WHERE username=? AND password_hash=?", (username,hashlib.sha256(password.encode()).hexdigest()))
                        if cur.fetchall():
                            print(f"User {username} logged in successfully.")
                            client_socket.sendall(MESSAGES.LoginConfirmation.construct_payload(True).encode())
                            self.ready_clients.append((username,client_socket))
                            self.queue.remove(client_socket)
                            break
                        else:
                            print(f"User {username} failed to log in.")
                            client_socket.sendall(MESSAGES.LoginConfirmation.construct_payload(False).encode())
                            client_socket.sendall(MESSAGES.LoginRequest.construct_payload(RSA_keypair[0]).encode())
                        conn.close()

                    elif message['MessageType'] == 'RegisterRequest':
                        username,password = MESSAGES.RegisterRequest.parse_payload(message)
                        if not username or not password:
                            client_socket.sendall(MESSAGES.RegisterResponse.construct_payload(False).encode())
                        else:
                            conn = sqlite3.connect(db_path)
                            cur = conn.cursor()
                            cur.execute("SELECT * FROM usersdata WHERE username=?", (username,))
                            if cur.fetchall():
                                print(f"Registration failed: Username {username} already exists.")
                                client_socket.sendall(MESSAGES.RegisterResponse.construct_payload(False).encode())
                            else:
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
            print("Client connection closed.")
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()


    def start_game(self, game_id):
        players:List[tuple[str, socket.socket]] = self.games[game_id]
        print(f"Starting game with players: {[p[0] for p in players]}")
        self.game_states[game_id] = GameStateC()
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
    
    def Handle_Player(self, game_id,client_socket:socket.socket,username:str):
        # Placeholder for handling player actions during the game
        pass
        

    


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
        connection_thread = threading.Thread(target=self.connection_listen_loop,daemon=True)
        connection_thread.start()
        try:
            connection_thread.join() # Wait for connection loop to finish
            
            # Keep main thread alive to allow other threads to run
            while not self.kill:
                #This loop is for keeping the server alive, can add monitoring or commands here
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