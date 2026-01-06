#Different types of messages over sockets can be defined here
import ast
from typing import List
class Message():
    @staticmethod
    def construct_payload():
        return str({'MessageType':'Message'})
    @staticmethod
    def parse_payload(payload):
        return payload['MessageType']


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
    def construct_payload(game_id:int, players:list[list[str,int,int,int]]):
        return str({'MessageType':'GameStartNotification','game_id':game_id,'players':players})
    @staticmethod
    def parse_payload(payload) -> tuple[int,list[list[str,int,int,int]]]:
        return (payload['game_id'], payload['players'])
class StartBoardDisplay(Message):
    @staticmethod
    def construct_payload(board_state:dict):
        return str({'MessageType':'StartBoardDisplay','board_state':board_state})
    @staticmethod
    def parse_payload(payload) -> dict:
        return payload['board_state']
    
class BoardDisplay(Message):
    @staticmethod
    def construct_payload(board_state:dict,powerstation_market, resource_market, electros, player_resources_stations_dict) -> str:
        return str({'MessageType':'BoardDisplay','board_state':board_state, 'powerstation_market': powerstation_market, 'resource_market': resource_market, 'electros': electros, 'player_resources_stations_dict': player_resources_stations_dict})
    @staticmethod
    def parse_payload(payload) -> tuple[dict,dict,dict,list[int],dict]:
        return payload['board_state'], payload['powerstation_market'], payload['resource_market'], payload['electros'], payload['player_resources_stations_dict']
    
class BuyStartingCityRequest(Message):
    @staticmethod
    def construct_payload(current_player,electros):
        return str({'MessageType':'BuyStartingCityRequest', 'current_player':current_player,'electros':electros})
    @staticmethod
    def parse_payload(payload) -> str:
        return payload['current_player'], payload['electros']
    
class BuyStartingCityResponse(Message):
    @staticmethod
    def construct_payload(city_id:str):
        return str({'MessageType':'BuyStartingCityResponse','city': city_id})
    @staticmethod
    def parse_payload(payload) -> str:
        return payload['city']
    
class BuyStartingStationRequest(Message):
    @staticmethod
    def construct_payload(current_market,current_player,values,electros):
        return str({'MessageType':'BuyStartingStationRequest','current_market':current_market, 'current_player':current_player,'valid_values':values,'electros':electros})
    @staticmethod
    def parse_payload(payload):
        return payload['current_market'],payload['current_player'],payload['valid_values'],payload['electros']
    
class BuyStartingStationResponse(Message):
    @staticmethod
    def construct_payload(power_station_value):
        return str({'MessageType':'BuyStartingStationResponse','power_station_value':power_station_value})
    @staticmethod
    def parse_payload(payload):
        return payload['power_station_value']


class BidOnPowerStation(Message):
    @staticmethod
    def construct_payload(powerstation,min_bid,current_player,held_by_player,electros):
        return str({'MessageType':'BidOnPowerStation','min_bid':min_bid, 'powerstation':powerstation,'current_player':current_player,'held_by_player':held_by_player,'electros': electros})
    @staticmethod
    def parse_payload(payload):
        return payload['powerstation'], int(payload['min_bid']), payload['current_player'], payload['held_by_player'], int(payload['electros'])

class BidOnPowerStationResponse(Message):
    @staticmethod
    def construct_payload(bid_amount:int|bool):
        return str({'MessageType':'BidOnPowerStationResponse','bid_amount':bid_amount})
    @staticmethod
    def parse_payload(payload) -> int|bool:
        return payload['bid_amount']

class PlayerBoughtPowerStation(Message):
    @staticmethod
    def construct_payload(player_name:str,power_station_value:str,winning_bid:int):
        return str({'MessageType':'PlayerBoughtPowerStation','player_name':player_name,'power_station_value':power_station_value,'winning_bid':winning_bid})
    @staticmethod
    def parse_payload(payload) -> tuple[str,str,int]:
        return payload['player_name'], payload['power_station_value'], payload['winning_bid']

class BuyResourcesRequest(Message):
    @staticmethod
    def construct_payload(current_player:str,resource_costs:dict,PowerStations:List[int],resource_space:dict):
        return str({'MessageType':'BuyResourcesRequest','current_player':current_player,'resource_costs':resource_costs,'PowerStations':PowerStations,'resource_space':resource_space})
    @staticmethod
    def parse_payload(payload) -> tuple[str,dict,List[int],dict]:
        return payload['current_player'], payload['resource_costs'], payload['PowerStations'], payload['resource_space']
class BuyResourcesResponse(Message):
    @staticmethod
    def construct_payload(resources_to_buy:dict):
        return str({'MessageType':'BuyResourcesResponse','resources_to_buy':resources_to_buy})
    @staticmethod
    def parse_payload(payload) -> dict:
        return payload['resources_to_buy']
    
class BuyCityRequest(Message):
    @staticmethod
    def construct_payload(current_player:str,electros:int,city_costs:dict):
        return str({'MessageType':'BuyCityRequest','current_player':current_player,'electros':electros,'city_costs':city_costs})
    @staticmethod
    def parse_payload(payload) -> tuple[str,int,dict]:
        return payload['current_player'], payload['electros'], payload['city_costs']
    
class BuyCityResponse(Message):
    @staticmethod
    def construct_payload(city_id:str):
        return str({'MessageType':'BuyCityResponse','city_id':city_id})
    @staticmethod
    def parse_payload(payload) -> str:
        return payload['city_id']

class BureaucracyUpdate(Message):
    @staticmethod
    def construct_payload(player_name:str,electros:int,number_of_cities:int,power_stations:List[str],resources:dict):
        return str({'MessageType':'BureaucracyUpdate','player_name':player_name,'electros':electros,'number_of_cities':number_of_cities,'power_stations':power_stations,'resources':resources})
    @staticmethod
    def parse_payload(payload) -> tuple[str,int,int,List[str],dict]:
        return payload['player_name'], payload['electros'], payload['number_of_cities'], payload['power_stations'], payload['resources']

class BureaucracyComplete(Message):
    @staticmethod
    def construct_payload(power_station_dict:dict):
        return str({'MessageType':'BureaucracyComplete','power_station_dict':str(power_station_dict)})
    @staticmethod
    def parse_payload(payload):
        return payload['power_station_dict']
    
class GameEndNotification(Message):
    @staticmethod
    def construct_payload(winner_name:str):
        return str({'MessageType':'GameEndNotification','winner_name':winner_name})
    @staticmethod
    def parse_payload(payload) -> str:
        return payload['winner_name']
    
class BuyPowerStationRequest(Message):
    @staticmethod
    def construct_payload(market:str,current_player:str,electros:int,valid_values:List[int]):
        return str({'MessageType':'BuyPowerStationRequest','market':market,'current_player':current_player,'electros':electros,'valid_values':valid_values})
    @staticmethod
    def parse_payload(payload) -> tuple[str,str,int,List[int]]:
        return payload['market'], payload['current_player'], payload['electros'], payload['valid_values']
    
class BuyPowerStationResponse(Message):
    @staticmethod
    def construct_payload(power_station_value:int|bool):
        return str({'MessageType':'BuyPowerStationResponse','power_station_value':power_station_value})
    @staticmethod
    def parse_payload(payload) -> int|bool:
        return payload['power_station_value']

class BureaucracyNotification(Message):
    @staticmethod
    def construct_payload(player,number_cities_powered:int):
        return str({'MessageType':'BureaucracyNotification','player':player,'number_cities_powered':str(number_cities_powered)})
    @staticmethod
    def parse_payload(payload) -> tuple[str,int]:
        return payload['player'], int(payload['number_cities_powered'])
    
class DiscardPowerStationRequest(Message):
    @staticmethod
    def construct_payload(current_player:str,power_stations:List[str]):
        return str({'MessageType':'DiscardPowerStationRequest','current_player':current_player,'power_stations':power_stations})
    @staticmethod
    def parse_payload(payload) -> tuple[str,List[str]]:
        return payload['current_player'], payload['power_stations']
    
class DiscardPowerStationResponse(Message):
    @staticmethod
    def construct_payload(power_station_value:str):
        return str({'MessageType':'DiscardPowerStationResponse','power_station_value':power_station_value})
    @staticmethod
    def parse_payload(payload) -> str:
        return payload['power_station_value']