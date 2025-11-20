#Different types of messages over sockets can be defined here
from typing import List
class Message():
    @staticmethod
    def construct_payload(self):
        pass
    @staticmethod
    def parse_payload(self,payload):
        pass


class LoginRequest(Message):
    @staticmethod
    def construct_payload(public_key:tuple[int,int]):
        return str({'MessageType':'LoginRequest','PublicKey':public_key})
    @staticmethod
    def parse_payload(payload) -> tuple[int,int]:
        return payload['PublicKey']
    
class LoginResponse(Message):
    @staticmethod
    def construct_payload(username:str,password:str):
        return str({'MessageType':'LoginResponse','username':username,'password':password})
    @staticmethod
    def parse_payload(payload) -> tuple[str,str]:
        return (payload['username'], payload['password'])
    
class RegisterRequest(Message):
    @staticmethod
    def construct_payload(username:str,password:str):
        return str({'MessageType':'RegisterRequest','username':username,'password':password})
    @staticmethod
    def parse_payload(payload) -> tuple[str,str]:
        return (payload['username'], payload['password'])

class RegisterResponse(Message):
    @staticmethod
    def construct_payload(success:bool):
        return str({'MessageType':'RegisterResponse','success':success})
    @staticmethod
    def parse_payload(payload) -> bool:
        return payload['success']
    
class LoginConfirmation(Message):
    @staticmethod
    def construct_payload(success:bool):
        return str({'MessageType':'LoginConfirmation','success':success})
    @staticmethod
    def parse_payload(payload) -> bool:
        return payload['success']

class GameStartNotification(Message):
    @staticmethod
    def construct_payload(game_id:int, players:list[str]):
        return str({'MessageType':'GameStartNotification','game_id':game_id,'players':players})
    @staticmethod
    def parse_payload(payload) -> tuple[int,list[str]]:
        return (payload['game_id'], payload['players'])
    
class BoardDisplay(Message):
    @staticmethod
    def construct_payload(board_state:dict) -> str:
        return str({'MessageType':'BoardDisplay','board_state':board_state})
    @staticmethod
    def parse_payload(payload) -> dict:
        return payload['board_state']
    
class BuyStartingCityRequest(Message):
    @staticmethod
    def construct_payload(current_player):
        return str({'MessageType':'BuyStartingCityRequest', 'current_player':current_player})
    @staticmethod
    def parse_payload(payload) -> str:
        return payload['current_player']
    
class BuyStartingCityResponse(Message):
    @staticmethod
    def construct_payload(self,city_id:str):
        return str({'MessageType':'BuyStartingCityResponse','city': city_id})
    def parse_payload(payload) -> str:
        return payload['city']

    