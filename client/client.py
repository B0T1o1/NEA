

from .ui.uis import UIC
import socket
import threading
import time

from shared import MESSAGES
from shared.encryption import RSA

class ClientC():
    def __init__(self,host = '127.0.0.1',port=65432):
        self.host = host
        self.port = port
        self.UI = UIC()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.kill = False

    def connect(self):
        try:
            self.client_socket.connect((self.host,self.port))
            print('Connected to server at {}:{}'.format(self.host,self.port))
        except ConnectionRefusedError:
            print('Connection refused by the server.')
            self.kill = True


    def sendMessage(self,message:str):
        self.client_socket.sendall(message.encode())


    def receiveMessage(self):
        while not self.kill:
            try:
                data = self.client_socket.recv(1024)
                if data:
                    message = eval(data.decode())
                    MessageType = message['MessageType']
                    print(f"Received message of type: {MessageType}")
                    if message['MessageType'] == 'LoginRequest':
                        server_public_key = MESSAGES.LoginRequest.parse_payload(message)
                        choice = self.UI.GetLogin_or_Register()
                        if choice == 'login':
                            username,password = self.UI.GetLoginDetails()
                            self.client_socket.sendall(str(RSA.encrypt(MESSAGES.LoginResponse.construct_payload(username,password),server_public_key)).encode())
                        if choice == 'register':
                            username,password = self.UI.GetRegisterDetails()
                            self.client_socket.sendall(str(RSA.encrypt(MESSAGES.RegisterRequest.construct_payload(username,password),server_public_key)).encode())
                    if message['MessageType'] == 'LoginConfirmation':
                        success = MESSAGES.LoginConfirmation.parse_payload(message)
                        if success:
                            self.UI.UI.DisplayMessage('Login successful!')
                        else:
                            self.UI.UI.DisplayMessage('Login failed. Please check your credentials.')
                    if message['MessageType'] == 'RegisterResponse':
                        success = MESSAGES.RegisterResponse.parse_payload(message)
                        if success:
                            self.UI.UI.DisplayMessage('Registration successful! You can now log in.')
                            
                        else:
                            self.UI.UI.DisplayMessage('Registration failed. Username may already be taken.')
                else:
                    print('Server closed the connection.')
                    self.kill = True
            except ConnectionResetError:
                print('Connection was reset by the server.')
                self.kill = True

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