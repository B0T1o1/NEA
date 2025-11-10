#Different types of messages over sockets can be defined here

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