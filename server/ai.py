from shared import MESSAGES
import threading
from typing import List
import random
class AIPlayer:
    def __init__(self,name:str):
        self._Name = name
        self._latest_board_state = None
        self._invetories = {}
        self._electros:dict[str,int] = {}
        self._PowerStation_Market = None
        self._Resource_Market = None
        self._Receive_Message_Queue:List[tuple[str]] = []
        self._Send_Message_Queue:List[tuple[str]] = []



        threading.Thread(target=self.EnqueueMessage, args=(None,), daemon=True).start()
        threading.Thread(target=self.RecieveLoop, args=(None, None), daemon=True).start()

    
    def EnqueueMessage(self, message):
        # Process the incoming message for the AI player rather than send over network
        messageType = MESSAGES.Message.parse_payload(message)
        if messageType == 'BoardDisplay':
            board_state, powerstation_market, resource_market, electros, player_resources_stations_dict = MESSAGES.BoardDisplay.parse_payload(message)
            self._latest_board_state = board_state
            self._PowerStation_Market = powerstation_market
            self._Resource_Market = resource_market
            self._invetories = player_resources_stations_dict
            self._electros = electros
        elif messageType == 'StartBoardDisplay':
            board_state = MESSAGES.StartBoardDisplay.parse_payload(message)
        else:
            self._Receive_Message_Queue.append(message)
        

    def RecieveLoop(self, message_type, message):
        if message_type == 'BuyStartingCityRequest':
            current_player, electros = MESSAGES.BuyStartingCityRequest.parse_payload(message)
            if current_player == self._Name:
                city_id_to_buy = self._StartingCityPurchase()
                buy_city_message = MESSAGES.BuyStartingCityResponse.construct_payload(city_id_to_buy)
                self._Send_Message_Queue.append(buy_city_message)
        if message_type == 'BuyStartingStationRequest':
            market, player,values, electros = MESSAGES.BuyStartingStationRequest.parse_payload(message)
            if current_player == self._Name:
                    station_id_to_buy = self._StartingStationPurchase(values)
                    buy_station_message = MESSAGES.BuyStartingStationResponse.construct_payload(station_id_to_buy)
                    self._Send_Message_Queue.append(buy_station_message)
        if message_type == 'BidOnPowerStationRequest':
            powerstation, min_bid, current_player, held_by_player, electros = MESSAGES.BidOnPowerStationRequest.parse_payload(message)
            if current_player == self._Name:
                bid_amount = self._BidOnPowerStation(min_bid, electros,powerstation ,held_by_player)
                bid_message = MESSAGES.BidOnPowerStationResponse.construct_payload(bid_amount)
                self._Send_Message_Queue.append(bid_message)
        if message_type == 'BuyResourcesRequest':
            current_player,resource_costs, power_stations, resource_space = MESSAGES.BuyResourcesRequest.parse_payload(message)
            if current_player == self._Name:
                resources_to_buy = self._BuyResourcesDecision(resource_costs, power_stations, resource_space)
                buy_resources_message = MESSAGES.BuyResourcesResponse.construct_payload(resources_to_buy)
                self._Send_Message_Queue.append(buy_resources_message)
        if message_type == 'BuyCityRequest':
            current_player, electros,city_costs = MESSAGES.BuyCityRequest.parse_payload(message)
            if current_player == self._Name:
                city_id_to_buy = self._BuyCityDecision(city_costs, electros)
                buy_city_message = MESSAGES.BuyCityResponse.construct_payload(city_id_to_buy)
                self._Send_Message_Queue.append(buy_city_message)
        if message_type == 'BureaucracyUpdate':
            current_player, electros, number_of_cities, power_stations, resources = MESSAGES.BureaucracyUpdate.parse_payload(message)
            if current_player == self._Name:
                Choose_to_power_message = self._Choose_Stations_to_power(electros, number_of_cities, power_stations, resources)
                power_stations_message = MESSAGES.BureaucracyComplete.construct_payload(Choose_to_power_message)
                self._Send_Message_Queue.append(power_stations_message)
        if message_type == 'BuyPowerStationsRequest':
            market, current_player, electros, valid_values = MESSAGES.BuyPowerStationRequest.parse_payload(message)
            if current_player == self._Name:
                station_to_buy = self._BuyStationDecision( valid_values, electros, market)
                buy_stations_message = MESSAGES.BuyPowerStationResponse.construct_payload(station_to_buy)
                self._Send_Message_Queue.append(buy_stations_message)
        if message_type == 'DiscardPowerStationRequest':
            current_player,power_stations = MESSAGES.DiscardPowerStationRequest.parse_payload(message)
            if current_player == self._Name:
                station_to_discard = self._DiscardStationDecision(power_stations)
                discard_station_message = MESSAGES.DiscardPowerStationResponse.construct_payload(station_to_discard)
                self._Send_Message_Queue.append(discard_station_message)

                
    def _DiscardStationDecision(self, power_stations:List[str]):
        station_values = []
        for station in power_stations:
            station_data = str_to_station_dict(station)
            station_values.append(int(station_data.get("Value",0)))
        station_values.sort()  # Sort by value
        return station_values[0][0]  # Return the station with the lowest value

    def _BuyStationDecision(self, valid:List[str], electros:int,market):
        affordable_stations = []
        for station in valid:
            if int(valid) <= electros:
                affordable_stations.append(station)
        return affordable_stations[random.randrange(len(affordable_stations))] 
    
    def _Choose_Stations_to_power(self, electros:int, number_of_cities:int, power_stations:List[str], resources:dict):
        
        power_stations_dict = {}
        for power_station in power_stations:
            power_station_data = str_to_station_dict(power_station)
            fuel_type = power_station_data.get("FuelType")
            fuel_amount = power_station_data.get("FuelAmount", 0)
            if fuel_type == 'H':
                fuel_type = 'C'
            if fuel_type == 'R':
                power_stations_dict[power_station] = 0
                continue
            if fuel_type and fuel_type in resources:
                if resources[fuel_type] >= fuel_amount:
                    # Can power this station
                    resources[fuel_type] -= fuel_amount
                    power_stations_dict[power_station] = fuel_amount 
                    continue
        return power_stations_dict


    def _StartingCityPurchase(self):
        available_city_ids = []
        for city_id,city_data in self._latest_board_state['cities'].items(): # gives dict of city_id:city_data
            if bool(city_data['Available']) is True:
                # Buy the first unowned city we find
                available_city_ids.append(city_id)
        return available_city_ids[random.randrange(len(available_city_ids))]
    
    def _BuyCityDecision(self,city_costs:dict, electros:int):
        # Buy the first affordable city we find
        affordable_cities = []
        for city_id, cost in city_costs.items():
            if cost <= electros:
                affordable_cities.append(city_id)
        if affordable_cities:
            return affordable_cities[random.randrange(len(affordable_cities))]
        return 'FINISH'  # Indicate no purchase
    
    def _StartingStationPurchase(self,valid_values:List[int]):
        # Buy the cheapest valid station
        return valid_values[random.randrange(len(valid_values))]

    def _BidOnPowerStation(self, min_bid:int, electros:int,powerstation:str ,held_by_player:str):
        # Simple bidding strategy: if enough electros to meet min_bid, bid randomly between min_bid and passing
        if electros < min_bid:
            return False  # Cannot bid
        bid = random.choice([False,min_bid])
    
    def _BuyResourcesDecision(self,resource_costs:dict, power_stations:List[str], resource_space:int):
        # Simple strategy: buy one unit of each resource type if affordable and space allows
        for power_station in power_stations:
            if self._invetories.get(self._Name,{})[0]
            power_station_data = str_to_station_dict(power_station)
            fuel_type = power_station_data.get("FuelType")
            fuel_amount = power_station_data.get("FuelAmount", 0)
            if fuel_type == 'H':
                fuel_type = 'C'
            if fuel_type == 'R':
                None
            if fuel_type and fuel_type in resource_costs:
                cost = resource_costs[fuel_type][fuel_amount]
                if cost < self._electros.get(self._Name, 0) and resource_space >= fuel_amount:
                    return {fuel_type: fuel_amount}
        return {'X':0}
    
def str_to_station_dict(station_string: str) -> dict:
    data = {}
    # Handle empty or malformed strings gracefully
    if not station_string: return data
    
    parts = station_string.split(", ")
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            if key == "Value":
                data[key] = int(value)
            elif key == "FuelType":
                data[key] = value.split(" ")[0]
            elif key == "FuelAmount":
                data[key] = int(value)
            elif key == "CitiesPowered":
                data[key] = int(value)
    return data

    


    

    

    