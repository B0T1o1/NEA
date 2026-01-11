from cv2 import phase
from shared import MESSAGES
import threading
from typing import List,Dict
import random
import ast
import time
import itertools
import math
import neat

class AIPlayer:
    """AI player who makes random valid moves
    """
    def __init__(self,name:str, run_speed:float=0.1):
        """Initialiases AI player

        Args:
            name (str): Name of Ai player
        """
        self._Name: str = name
        self._latest_board_state: dict[str, dict] 
        self._inventories: dict[str, tuple[dict[str,int],list[str]]]
        self._electros:dict[str,int] 
        self._PowerStation_Market: dict 
        self._Resource_Market: dict 
        self._Receive_Message_Queue:List[tuple[str]] = []
        self._Send_Message_Queue:List[tuple[str]] = []
        self._lock = threading.Lock()
        self.Kill = False
        self._run_speed = run_speed  # Time to sleep between processing loops



        threading.Thread(target=self.EnqueueMessage, args=(None,), daemon=True).start()
        threading.Thread(target=self.RecieveLoop, daemon=True).start()

    
    def EnqueueMessage(self, message: bytes):
        """Adds Message to be processed by AI player

        Args:
            message (bytes): Contains Message in format of from MESSAGES
        """
        # Use the context manager for thread-safe locking
        with self._lock:
            if message is None:
                return
            
        #try:
            decoded_data = message.decode().replace("inf", "'inf'")
            message_dict = ast.literal_eval(decoded_data)
            
            messageType = MESSAGES.Message.parse_payload(message_dict)
            #print(f"AI {self._Name} received message of type: {messageType}")
            # Logic to handle board state updates immediately
            if messageType == 'BoardDisplay':
                board_state, powerstation_market_str, resource_market, electros, player_resources_stations_dict = MESSAGES.BoardDisplay.parse_payload(message_dict)
                self._latest_board_state = board_state
                powerstation_market_str = powerstation_market_str.replace("inf", "'inf'")
                self._PowerStation_Market = ast.literal_eval(powerstation_market_str)
                self._Resource_Market = resource_market
                self._inventories = player_resources_stations_dict
                self._electros = electros
            elif messageType == 'StartBoardDisplay':
                board_state = MESSAGES.StartBoardDisplay.parse_payload(message_dict)
                # You likely want to save this state too
                self._latest_board_state = board_state
            else:
                # Put other messages in the queue for RecieveLoop to process
                self._Receive_Message_Queue.append(message_dict) # Store as dict, not string
        #except Exception as e:
            #print(f"AI Enqueue Error: {e}")

    def RecieveLoop(self):
        """Loops through messages queued by EnqueueMessage and sends them for processing
        """
        while not self.Kill:
            message_to_process = None
            
            # Lock only while popping from the list
            with self._lock:
                if self._Receive_Message_Queue:
                    message_to_process = self._Receive_Message_Queue.pop(0)
            
            # Process outside the lock so we don't block EnqueueMessage
            if message_to_process:
                # Pass the DICT to process message, not the string
                self._Process_Message(message_to_process) 
            else:
                time.sleep(self._run_speed)
    
    def GetNextMessage(self):
        """Gives the oldest message to the server for proccessing

        Returns:
            str: The next message string to be sent to the server
        """
        with self._lock:  # Use the threading lock
            if self._Send_Message_Queue:
                # Returns the message string (e.g., "{'MessageType': '...'}")
                return self._Send_Message_Queue.pop(0)
        return None


    def _Process_Message(self, message:str):
        """Correctly Proccesses message and distrubutes logic and adds message to the send_message_queue

        Args:
            message (str): Message string in MESSAGES format
        """
        message_type = MESSAGES.Message.parse_payload(message)

        if message_type == 'BuyStartingCityRequest':
            current_player, electros = MESSAGES.BuyStartingCityRequest.parse_payload(message)
            if current_player == self._Name:
                city_id_to_buy = self._StartingCityPurchase()
                buy_city_message = MESSAGES.BuyStartingCityResponse.construct_payload(city_id_to_buy)
                self._Send_Message_Queue.append(buy_city_message)

        if message_type == 'BuyStartingStationRequest':
            market, current_player,values, electros = MESSAGES.BuyStartingStationRequest.parse_payload(message)
            if current_player == self._Name:
                    station_id_to_buy = self._StartingStationPurchase(values)
                    buy_station_message = MESSAGES.BuyStartingStationResponse.construct_payload(station_id_to_buy)
                    self._Send_Message_Queue.append(buy_station_message)

        if message_type == 'BidOnPowerStation':
            powerstation, min_bid, current_player, held_by_player, electros = MESSAGES.BidOnPowerStation.parse_payload(message)
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

        if message_type == 'BuyPowerStationRequest':
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


    def _DiscardStationDecision(self, power_stations:List[str])-> int:
        """Discards the powerstation with the lowest value

        Args:
            power_stations (List[str]): List of powerstations in specified string format 

        Returns:
            int: value of powerstation to discard
        """
        station_values = []
        for station in power_stations:
            station_data = str_to_station_dict(station)
            station_values.append(int(station_data.get("Value",0)))
        station_values.sort()  # Sort by value
        return station_values[0]  # Return the station with the lowest value

    def _BuyStationDecision(self, valid:List[int], electros:int,market:List[str]) -> int|bool:
        """Randomly buys and affordable powerstation if suich station exists

        Args:
            valid (List[int]): list of valid powerstation values
            electros (int): amount of electros available to the AI
            market (List[str]): List of powerstations in market in specified string format

        Returns:
            int or bool: value of powerstation to buy or False if none affordable
        """
        affordable_stations = []
        for station_value in valid:
            if station_value <= electros:
                affordable_stations.append(station_value)
        if not affordable_stations:
            return False  # Cannot afford any station
        return affordable_stations[random.randrange(len(affordable_stations))] 
    
    def _Choose_Stations_to_power(self, electros:int, number_of_cities:int, power_stations:List[str], resources:dict) -> dict:
        """Chooses to power stations if suffcient resources exist, for hybrid stations it always chooses coal   

        Args:
            electros (int): amount of electros available to the AI
            number_of_cities (int): number of cities the AI owns
            power_stations (List[str]): List of powerstations in specified string format
            resources (dict): available resources for powering stations

        Returns:
            dict: mapping of powerstation values to resources used for powering
        """
        power_stations_dict: dict[int, dict[str, int]] = {}
        for power_station in power_stations:
            power_station_data = str_to_station_dict(power_station)
            fuel_type = power_station_data.get("FuelType")
            fuel_amount = power_station_data.get("FuelAmount", 0)
            if fuel_type == 'H':
                fuel_type = 'C'
            if fuel_type == 'R':
                power_stations_dict[power_station_data['Value']] = {}
                continue
            if fuel_type and fuel_type in resources:
                if resources[fuel_type] >= fuel_amount:
                    # Can power this station
                    resources[fuel_type] -= fuel_amount
                    power_stations_dict[power_station_data['Value']] = {fuel_type: fuel_amount}
                    continue
        return power_stations_dict

    def _StartingCityPurchase(self) -> str:
        """Chooses random city that is avaiable on the board

        Returns:
            str: a city_id 
        """
        available_city_ids = []
        for city_id,city_data in self._latest_board_state['cities'].items(): # gives dict of city_id:city_data
            if bool(city_data['Available']) is True:
                # Buy the first unowned city we find
                available_city_ids.append(city_id)
        return available_city_ids[random.randrange(len(available_city_ids))]
    
    def _BuyCityDecision(self,city_costs:dict, electros:int):
        """Chooses to buy a random affordable city

        Args:
            city_costs (dict): Costs of cities available to buy
            electros (int): amount of electros available to the AI

        Returns:
            str: city_id of the chosen city or 'FINISH' if no purchase
        """
        affordable_cities = []
        for city_id, cost in city_costs.items():
            if cost == 'inf':
                continue
            if int(cost) <= electros:
                affordable_cities.append(city_id)
        if affordable_cities:
            return affordable_cities[random.randrange(len(affordable_cities))]
        return 'FINISH'  # Indicate no purchase
    
    def _StartingStationPurchase(self,valid_values:List[int])-> int:
        """Chooses to buy a random station

        Args:
            valid_values (List[int]): A list of the values of stations that are available to be bought

        Returns:
            int: station value to buy
        """
        return valid_values[random.randrange(len(valid_values))]

    def _BidOnPowerStation(self, min_bid:int, electros:int,powerstation:str ,held_by_player:str) -> int|bool:
        """Deceides to bid the minmum 25% if AI has the electros otherwise skips 

        Args:
            min_bid (int): The minimum bid 
            electros (int): Electros available to the ai
            powerstation (str): The powerstation being bid on 
            held_by_player (str): Player currently holding the station in bidding

        Returns:
            int or bool: amount to bid or false to skip
        """
        if electros < min_bid:
            return False  # Cannot bid
        return random.choice([False,False,False,min_bid])
    
    def _BuyResourcesDecision(self, resource_costs: dict, power_stations: List[str], resource_space: dict):
        current_electros = self._electros.get(self._Name, 0)
        
        # Access nested inventory safely: List[Dict] -> Dict
        player_inventory_list = self._inventories.get(self._Name, [{}])
        current_inventory = player_inventory_list[0] if player_inventory_list else {}

        for resource_type, max_storage in resource_space.items():
            # Handle Hybrid logic (Hybrid usually buys Coal or Oil, but market lists them separately)
            # Assuming here we just look up the specific key passed in resource_space
            search_key = 'C' if resource_type == 'H' else resource_type
            
            # 1. Get the cost list safely. 
            costs_list = resource_costs.get(search_key, [])
            
            # If the market is empty for this resource, skip it
            if not costs_list:
                continue

            # 2. Determine how many we WANT to buy (half of capacity)
            target_amount = max_storage // 2
            if target_amount == 0:
                continue

            # 3. Determine how many we CAN buy (based on market availability)
            # We can't buy more than the list contains.
            amount_available = len(costs_list)
            actual_amount_to_buy = min(target_amount, amount_available)

            # 4. Get the cost
            # Assuming costs_list[i] represents the cost to buy i+1 items.
            # Example: buying 1 item -> index 0. Buying 3 items -> index 2.
            cost_index = actual_amount_to_buy - 1
            cost = costs_list[cost_index]

            # 5. Check Affordability and Inventory space
            current_held = current_inventory.get(search_key, 0)

            if current_electros >= cost and current_held < target_amount:
                return {search_key: actual_amount_to_buy}

        return {'X': 0}
    
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
    for key in ["Value", "FuelType", "FuelAmount", "CitiesPowered"]:
        if key not in data:
            data[key] = None  # or some default value
            raise ValueError(f"Missing key {key} in station string: {station_string}")
    return data

    


    
class HardAIPlayer(AIPlayer):
    def __init__(self,name:str, run_speed:float=0.1):
        super().__init__(name, run_speed)
        self._PowerStations_to_Buy_resources_for = []
        self._index_of_next_station_to_buy_resources_for = 0
        self._Hybrid_fuel_left_over_dict = {}  # Tracks leftover fuel from hybrids for resource buying phase
        self._PowerPlan = {}
        self._Number_of_cities_supported_in_power_plan = 0
        
    
    def _DiscardStationDecision(self, power_stations:List[str]):
        # Discards the station that powers the least cities, breaking ties by lowest value
        lowest_powering_station = str_to_station_dict(power_stations[0])
        station_tuples = [ (station_data.get('Value'), station_data.get('CitiesPowered',0),self._Get_cost_to_fuel(station_data)) for station_data in [str_to_station_dict(station) for station in power_stations]]
        loser_pair_1 = station_tuples[0]
        winner_pair_2,loser_pair_2 = self._which_station(station_tuples[1],station_tuples[2])
        middle,worst_station = self._which_station(loser_pair_1,loser_pair_2)
        return  worst_station[0] # Start with worst station so station we want to buy has to be better than it

    def _BuyStationDecision(self, valid:List[int], electros:int,market):
        # Buy the station that powers the most cities, or any station with suffcient power to win, breaking ties by lowest cost of fuel and then lowest value.
        # Lowest Value as this means we save more electros for resources and cities and we can be in last place in future auctions

        winCondition = {3:17,4:17,5:15,6:14}
        N_of_Players = len(self._inventories)
        Required_power = winCondition.get(N_of_Players,15)

        owned_power_stations = self._inventories.get(self._Name)[1]
        station_tuples = []
        for station in owned_power_stations:
            station_data = str_to_station_dict(station)
            Required_power -= station_data.get('CitiesPowered',0)
            station_tuples.append( (station_data.get('Value'), station_data.get('CitiesPowered'),self._Get_cost_to_fuel(station_data)) )
        if Required_power <=0:
            return False  # Don't buy any more stations if we can already power enough cities to win
        #find worst station owned
        if len(station_tuples) == 3:
            loser_pair_1 = station_tuples[0]
            winner_pair_2,loser_pair_2 = self._which_station(station_tuples[1],station_tuples[2])
            middle,worst_station = self._which_station(loser_pair_1,loser_pair_2)
            best_station = worst_station # Start with worst station so station we want to buy has to be better than it
            
        else:  
            worst_station = (0,0,float('inf'))  # (Value, CitiesPowered, FuelCost)
            best_station = (0,0,float('inf'))  # (Value, CitiesPowered, FuelCost)
        can_reach_required = False
        affordable_stations = []
        for station_value in valid:
            if station_value <= electros:
                affordable_stations.append(station_value)

        power_stations = self._PowerStation_Market[0]
        for power_station in power_stations:
            station_data = str_to_station_dict(power_station)
            if station_data.get('Value') not in affordable_stations:
                continue
            cost = self._Get_cost_to_fuel(station_data)
            station = (station_data.get('Value'), station_data.get('CitiesPowered'), cost)
            if station[1] >= Required_power:
                can_reach_required = True
            if can_reach_required and station[1] >= Required_power:
                if station[2] < best_station[2]:
                    best_station = station
                elif station[2] == best_station[2]:
                    if station[0] < best_station[0]:
                        best_station = station
            elif station[1] > best_station[1] :
                best_station = station
            elif station[1] == best_station[1]:
                if station[2] < best_station[2]:
                    best_station = station
                elif station[2] == best_station[2]:
                    if station[0] < best_station[0]:
                        best_station = station
        if  best_station[0] == worst_station[0]:
            return False  # No station to buy
        return best_station[0]
    
    def _Get_cost_to_fuel(self,powerstation:dict) -> int:
        fuel_type = powerstation.get('FuelType')
        fuel_amount = powerstation.get('FuelAmount')

        # Calculate fuel cost
        if fuel_type == 'H':
            used_dict = {'C':0,'O':0}
            cost_of_oil = 0
            cost_of_coal = 0
            for fuel_required in range(fuel_amount):
                if len(self._Resource_Market['O']) <= used_dict['O'] and len(self._Resource_Market['C']) <= used_dict['C']:
                    # No more resources available
                    cost_of_oil += float('inf')
                    cost_of_coal += float('inf')
                if len(self._Resource_Market['O']) <= used_dict['O'] and len(self._Resource_Market['C']) > used_dict['C']:
                    coal = self._Resource_Market['C'][used_dict['C']]
                    used_dict['C'] += 1
                    cost_of_coal += coal
                    continue
                if len(self._Resource_Market['C']) <= used_dict['C'] and len(self._Resource_Market['O']) > used_dict['O']:
                    oil = self._Resource_Market['O'][used_dict['O']]
                    used_dict['O'] += 1
                    cost_of_oil += oil
                    continue
                else:
                    oil = self._Resource_Market['O'][used_dict['O']]
                    coal = self._Resource_Market['C'][used_dict['C']]
                    if oil < coal:
                        used_dict['O'] += 1
                        cost_of_oil = oil
                    else:
                        used_dict['C'] += 1
                        cost_of_coal = coal

            cost = cost_of_coal + cost_of_oil
        elif fuel_type == 'R':
            cost = 0
        else:

            if len(self._Resource_Market[fuel_type]) < fuel_amount:
                cost = float('inf')  # Not enough resources available
            else:
                cost = self._Resource_Market[fuel_type][fuel_amount - 1]


        return cost

    def _which_station(self,station1,station2):
        if station1[1] > station2[1]:
            return station1,station2
        elif station1[1] == station2[1]:
            if station1[2] < station2[2]:
                return station1,station2
            elif station1[2] == station2[2]:
                if station1[0] < station2[0]:
                    return station1,station2
        return station2,station1
    
    def _Choose_Stations_to_power(self, electros: int, number_of_cities: int, power_stations: List[str], resources: dict):
        real_power_plan: dict[int, dict[str, int]] = {}
        sorted_stations = sorted(power_stations, key=lambda x: -str_to_station_dict(x).get('CitiesPowered', 0))
        resource_check = {'C':0,'O':0,'G':0,'N':0}
        plan_works = True
        for station_val,resource_powering in self._PowerPlan.items():
            for r_type, r_amt in resource_powering.items():
                resource_check[r_type] += r_amt

        for r_type, r_amt in resource_check.items():
            if resources.get(r_type,0) < r_amt:
                plan_works = False
        if plan_works:
            return self._PowerPlan
        

        for station in sorted_stations:
            data = str_to_station_dict(station)
            f_type = data['FuelType']
            f_amt = data['FuelAmount']
            val = data['Value']
            
            if f_type == 'R':
                real_power_plan[val] = {} # Free power
            elif f_type == 'H':
                # Check resources
                if resources.get('C', 0) >= f_amt:
                    resources['C'] -= f_amt
                    real_power_plan[val] = {'C': f_amt}
                elif resources.get('O', 0) >= f_amt:
                    resources['O'] -= f_amt
                    real_power_plan[val] = {'O': f_amt}
            elif f_type in resources:
                if resources[f_type] >= f_amt:
                    resources[f_type] -= f_amt
                    real_power_plan[val] = {f_type: f_amt}
                    
        return real_power_plan
        


    
    def _StartingCityPurchase(self):
        # city_score is average connection cost divided by number of connections (cheaper and more connections is better)
        best_city_id = []
        best_city_score = float('inf')
        for city_id,city_data in self._latest_board_state['cities'].items(): # gives dict of city_id:city_data
            if bool(city_data['Available']) is True:

                total_connection_cost = 0
                connection_count = 0
                for i,connection in city_data['connections'].items():
                    if connection == 'inf':
                        continue
                    connection_count += 1
                    total_connection_cost += int(connection)
                if connection_count == 0:
                    continue
                city_score = total_connection_cost / (connection_count)**2
                if city_score < best_city_score:
                    best_city_score = city_score
                    best_city_id = city_id
        return best_city_id
    
    def _BuyCityDecision(self,city_costs:dict, electros:int):

        
        cheapest_city = 'FINISH'
        cheapest_cost = float('inf')
        for city_id, cost in city_costs.items():
            if cost == 'inf':
                continue
            if int(cost) <= cheapest_cost:
                cheapest_cost = int(cost)
                cheapest_city = city_id
        if cheapest_city != 'FINISH' and cheapest_cost <= electros:
            return cheapest_city # Buy the cheapest city
        return 'FINISH'  # Indicate no purchase if no affordable cities
    
    def _StartingStationPurchase(self,valid_values:List[int]):
        # Buy the station that powers the most cities, breaking ties by lowest cost of fuel and then lowestr value
        best_station = (0,0,float('inf'))  # (Value, CitiesPowered, FuelCost)
        power_stations = self._PowerStation_Market[0]

        for power_station in power_stations:
            station_data = str_to_station_dict(power_station)
            fuel_type = station_data.get('FuelType')
            fuel_amount = station_data.get('FuelAmount')

            # Calculate fuel cost
            if fuel_type == 'H':
                used_dict = {'C':0,'O':0}
                cost_of_oil = 0
                cost_of_coal = 0
                for fuel_required in range(fuel_amount):
                    if len(self._Resource_Market['O']) <= used_dict['O'] and len(self._Resource_Market['C']) <= used_dict['C']:
                        # No more resources available
                        cost_of_oil += float('inf')
                        cost_of_coal += float('inf')
                    if len(self._Resource_Market['O']) <= used_dict['O'] and len(self._Resource_Market['C']) > used_dict['C']:
                        coal = self._Resource_Market['C'][used_dict['C']]
                        used_dict['C'] += 1
                        cost_of_coal += coal
                        continue
                    if len(self._Resource_Market['C']) <= used_dict['C'] and len(self._Resource_Market['O']) > used_dict['O']:
                        oil = self._Resource_Market['O'][used_dict['O']]
                        used_dict['O'] += 1
                        cost_of_oil += oil
                        continue
                    else:
                        oil = self._Resource_Market['O'][used_dict['O']]
                        coal = self._Resource_Market['C'][used_dict['C']]
                        if oil < coal:
                            used_dict['O'] += 1
                            cost_of_oil = oil
                        else:
                            used_dict['C'] += 1
                            cost_of_coal = coal

                cost = cost_of_coal + cost_of_oil
            elif fuel_type == 'R':
                cost = 0
            else:
                if len(self._Resource_Market[fuel_type]) < fuel_amount:
                    cost = float('inf')  # Not enough resources available
                else:
                    cost = self._Resource_Market[fuel_type][fuel_amount - 1]


            station = (station_data.get('Value'), station_data.get('CitiesPowered'), cost)
            if station[1] > best_station[1]:
                best_station = station
            elif station[1] == best_station[1]:
                if station[2] < best_station[2]:
                    best_station = station
                elif station[2] == best_station[2]:
                    if station[0] < best_station[0]:
                        best_station = station
        return best_station[0]

    def _BidOnPowerStation(self, min_bid:int, electros:int,powerstation:str ,held_by_player:str):
        # Check that we can afford it
        if electros < min_bid:
            return False  # Cannot bid
        valid = []
        # Check that we would currently Bid this station if we were buying it outright

        for station in self._PowerStation_Market[0]:
            station_data = str_to_station_dict(station)
            valid.append(station_data.get('Value'))
        # Also include the bottom of the upper marketr if it exists as this may be better and if we skip we may get it.
        if self._PowerStation_Market[1]:
            valid.append(str_to_station_dict(self._PowerStation_Market[1][0]).get('Value'))
        choosen_station = self._BuyStationDecision(valid, electros, self._PowerStation_Market)
        if choosen_station != str_to_station_dict(powerstation).get('Value'):
            return False  # Don't bid if we wouldn't buy it outright
        else:
            # If the min_bid is less than or equal to the station value, bid the minimum to try and win
            if min_bid <= str_to_station_dict(powerstation).get('Value'):
                return min_bid  # Bid the minimum to try and win
            else:
                # Otherwise, likely hood of bidding is given by inverse of how much over the station value the min bid is + 1 so that max prob is one.
                min_bid_chance =  1 / ( min_bid - str_to_station_dict(powerstation).get('Value') + 1)
                if random.random() < min_bid_chance:
                    return min_bid  # Bid the minimum to try and win
        return False  # Otherwise pass
    
    def _BuyResourcesDecision(self, resource_costs: dict, power_stations: List[str], resource_space: dict):
        
        if self._index_of_next_station_to_buy_resources_for == 0:
            self._PowerStations_to_Buy_resources_for = power_stations.copy()
            self._PowerPlan = {}
            self._Hybrid_fuel_left_over_dict = {}
            self._Number_of_cities_supported_in_power_plan = 0
            #sort stations by CitiesPowered descending, then by Value descending
            def station_sort_key(station_str):
                station_data = str_to_station_dict(station_str)
                return (-station_data.get('CitiesPowered', 0), -station_data.get('Value', float('inf')))
            self._PowerStations_to_Buy_resources_for.sort(key=station_sort_key)
        if self._electros.get(self._Name, 0) == 0:
            self._index_of_next_station_to_buy_resources_for = 0
            return {'X': 0}  # No electros to buy resources
        while self._index_of_next_station_to_buy_resources_for != len(self._PowerStations_to_Buy_resources_for):
            station_to_buy_for = self._PowerStations_to_Buy_resources_for[self._index_of_next_station_to_buy_resources_for]
            station_data = str_to_station_dict(station_to_buy_for)
            fuel_type = station_data.get('FuelType')
            fuel_amount = station_data.get('FuelAmount')
            # Special handling for Hybrid fuel type
            if fuel_type == 'H':
                if self._Hybrid_fuel_left_over_dict.get(station_to_buy_for):
                    self._index_of_next_station_to_buy_resources_for += 1
                    return self._Hybrid_fuel_left_over_dict
                else:

                    used_dict = {'C':0,'O':0}
                    cost_of_oil = 0
                    cost_of_coal = 0
                    for fuel_required in range(fuel_amount):
                        if len(self._Resource_Market['O']) <= used_dict['O'] and len(self._Resource_Market['C']) <= used_dict['C']:
                            # No more resources available
                            cost_of_oil += float('inf')
                            cost_of_coal += float('inf')
                        if len(self._Resource_Market['O']) <= used_dict['O'] and len(self._Resource_Market['C']) > used_dict['C']:
                            coal = self._Resource_Market['C'][used_dict['C']]
                            used_dict['C'] += 1
                            cost_of_coal = coal
                            continue
                        if len(self._Resource_Market['C']) <= used_dict['C'] and len(self._Resource_Market['O']) > used_dict['O']:
                            oil = self._Resource_Market['O'][used_dict['O']]
                            used_dict['O'] += 1
                            cost_of_oil = oil
                            continue
                        else:
                            oil = self._Resource_Market['O'][used_dict['O']]
                            coal = self._Resource_Market['C'][used_dict['C']]
                            if oil < coal:
                                used_dict['O'] += 1
                                cost_of_oil = oil
                            else:
                                used_dict['C'] += 1
                                cost_of_coal = coal
                    if used_dict['O'] !=0:
                        if used_dict['C'] !=0:
                                
                            if (resource_space.get('O', 0) < fuel_amount) or (resource_space.get('C', 0) < fuel_amount) or (self._electros.get(self._Name, 0) < (cost_of_oil + cost_of_coal)):
                                # Not enough space, skip it
                                self._index_of_next_station_to_buy_resources_for += 1
                                continue
                            if self._electros.get(self._Name, 0) >= (cost_of_oil + cost_of_coal):

                                self._Hybrid_fuel_left_over_dict[station_to_buy_for] = {'C': used_dict['C']}
                                self._PowerPlan[station_data.get('Value')] = {'O': used_dict['O'], 'C': used_dict['C']}
                                self._Number_of_cities_supported_in_power_plan += station_data.get('CitiesPowered',0)
                                return {'O': used_dict['O']}
                            else:
                                self._index_of_next_station_to_buy_resources_for += 1
                                continue
                    else:
                        if resource_space.get('C', 0) < fuel_amount or self._electros.get(self._Name, 0) < cost_of_coal:
                            # Not enough space, skip it
                            self._index_of_next_station_to_buy_resources_for += 1
                            continue
                        self._PowerPlan[station_data.get('Value')] = {'C': used_dict['C']}
                        self._Number_of_cities_supported_in_power_plan += station_data.get('CitiesPowered',0)
                        return {'C': used_dict['C']}
            if fuel_type == 'R':
                self._index_of_next_station_to_buy_resources_for += 1  # No resources needed for renewable
                continue

            else:
                search_key = fuel_type
            costs_list = resource_costs.get(search_key, [])
            if len(costs_list) < fuel_amount:
                # Can't afford to buy resources for this station, skip it
                self._index_of_next_station_to_buy_resources_for += 1
                continue

            cost_index = fuel_amount - 1
            cost = costs_list[cost_index]
            current_electros = self._electros.get(self._Name, 0)
            if int(current_electros) < int(cost):
                # Can't afford, skip it
                self._index_of_next_station_to_buy_resources_for += 1
                continue

            if resource_space.get(search_key, 0) < fuel_amount:
                # Not enough space, skip it
                self._index_of_next_station_to_buy_resources_for += 1
                continue

            self._index_of_next_station_to_buy_resources_for += 1

            self._PowerPlan[station_data.get('Value')] = {search_key: fuel_amount}
            self._Number_of_cities_supported_in_power_plan += station_data.get('CitiesPowered',0)
            return {search_key: fuel_amount}
        
        self._index_of_next_station_to_buy_resources_for = 0
        return {'X': 0}  # No stations to buy resources for

# --- helpers ---

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def argmax(xs: List[float]) -> int:
    best_i = 0
    best_v = xs[0]
    for i, v in enumerate(xs):
        if v > best_v:
            best_v = v
            best_i = i
    return best_i

def safe_int(x, default=0) -> int:
    try:
        return int(x)
    except Exception:
        return default

# --- your existing str_to_station_dict must NOT raise on missing keys during play ---
# Your current version raises ValueError for missing keys; that can crash training.
# Use this safer version during NEAT runs:
def str_to_station_dict_safe(station_string: str) -> dict:
    data = {"Value": 0, "FuelType": "", "FuelAmount": 0, "CitiesPowered": 0}
    if not station_string:
        return data
    parts = station_string.split(", ")
    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key == "Value":
            data[key] = safe_int(value, 0)
        elif key == "FuelType":
            data[key] = value.split(" ")[0].strip()
        elif key == "FuelAmount":
            data[key] = safe_int(value, 0)
        elif key == "CitiesPowered":
            data[key] = safe_int(value, 0)
    return data


class NeatAIPlayer(AIPlayer):
    """
    NEAT-controlled version of AIPlayer.
    Keeps your networking/message loop unchanged; only decisions are driven by the NN.
    """
    def __init__(self, name: str, genome, config, run_speed: float = 0.1):
        super().__init__(name, run_speed)
        self.genome = genome
        self.config = config
        self.net = neat.nn.FeedForwardNetwork.create(genome, config)
        self._Resource_buying_index = 0  # for tracking multi-step resource buying
        # optional: tracking for fitness shaping
        self.fitness = 0.0

    # -------------------------
    # Input building (99 floats)
    # -------------------------
    def _encode_fuel_type_1hot(self, fuel_type: str) -> List[float]:
        # C,O,G,N,H,R
        mapping = {"C": 0, "O": 1, "G": 2, "N": 3, "H": 4, "R": 5}
        v = [0.0] * 6
        idx = mapping.get(fuel_type, None)
        if idx is not None:
            v[idx] = 1.0
        return v

    def _normalize_station(self, value: float, fuel_amt: float, cities: float) -> List[float]:
        # Scales to roughly [0..1] ranges so sigmoid nets behave better.
        # You can tune these caps.
        return [
            clamp(value / 50.0, 0.0, 1.0),
            clamp(fuel_amt / 5.0, 0.0, 1.0),
            clamp(cities / 6.0, 0.0, 1.0),
        ]

    def _get_network_inputs(self, current_phase: int) -> List[float]:
        """
        Builds EXACTLY 99 floats.
        If anything is missing (early game / markets not loaded yet), pads with zeros.
        """
        inputs: List[float] = []

        # --- 1) Powerstation market snapshot ---
        # Your code assumes self._PowerStation_Market = {0:[...], 1:[...]}.
        lower = (self._PowerStation_Market or {}).get(0, []) if hasattr(self, "_PowerStation_Market") else []
        upper = (self._PowerStation_Market or {}).get(1, []) if hasattr(self, "_PowerStation_Market") else []

        # take up to 4 from lower + up to 2 from upper = 6 stations total (common power grid style)
        market_stations = list(lower[:4]) + list(upper[:2])

        # each station: (value,fuelamt,cities) + 6 fuel one-hot = 3+6=9
        # 6 stations -> 54 floats
        for i in range(6):
            if i < len(market_stations):
                sd = str_to_station_dict_safe(market_stations[i])
                inputs.extend(self._normalize_station(sd["Value"], sd["FuelAmount"], sd["CitiesPowered"]))
                inputs.extend(self._encode_fuel_type_1hot(sd["FuelType"]))
            else:
                inputs.extend([0.0, 0.0, 0.0])
                inputs.extend([0.0] * 6)

        # --- 2) Resource market counts (4) ---
        rm = self._Resource_Market if hasattr(self, "_Resource_Market") else {}
        inputs.extend([
            clamp(len(rm.get("C", [])) / 24.0, 0.0, 1.0),
            clamp(len(rm.get("O", [])) / 24.0, 0.0, 1.0),
            clamp(len(rm.get("G", [])) / 24.0, 0.0, 1.0),
            clamp(len(rm.get("N", [])) / 24.0, 0.0, 1.0),
        ])  # +4 => 58

        # --- 3) My electros (1) ---
        electros = (self._electros or {}).get(self._Name, 0) if hasattr(self, "_electros") else 0
        inputs.append(clamp(electros / 200.0, 0.0, 1.0))  # +1 => 59

        # --- 4) My cities count (1) ---
        cities_owned = 0
        if hasattr(self, "_latest_board_state") and self._latest_board_state:
            cities = self._latest_board_state.get("cities", {}).values()
            for c in cities:
                owners = c.get("owners", [])
                if self._Name in owners:
                    cities_owned += 1
        inputs.append(clamp(cities_owned / 20.0, 0.0, 1.0))  # +1 => 60

        # --- 5) My owned stations (up to 3) => 3 * 9 = 27 ---
        inv = self._inventories.get(self._Name, [{}, []]) if hasattr(self, "_inventories") else [{}, []]
        owned_stations = inv[1] if len(inv) > 1 else []
        for i in range(3):
            if i < len(owned_stations):
                sd = str_to_station_dict_safe(owned_stations[i])
                inputs.extend(self._normalize_station(sd["Value"], sd["FuelAmount"], sd["CitiesPowered"]))
                inputs.extend(self._encode_fuel_type_1hot(sd["FuelType"]))
            else:
                inputs.extend([0.0, 0.0, 0.0])
                inputs.extend([0.0] * 6)
        # +27 => 87

        # --- 6) My owned resources (4) ---
        owned_res = inv[0] if len(inv) > 0 and isinstance(inv[0], dict) else {}
        inputs.extend([
            clamp(owned_res.get("C", 0) / 24.0, 0.0, 1.0),
            clamp(owned_res.get("O", 0) / 24.0, 0.0, 1.0),
            clamp(owned_res.get("G", 0) / 24.0, 0.0, 1.0),
            clamp(owned_res.get("N", 0) / 24.0, 0.0, 1.0),
        ])  # +4 => 91

        # --- 7) Cheapest 5 available city costs (5) ---
        costs = []
        if hasattr(self, "_latest_board_state") and self._latest_board_state:
            for city_id, c in self._latest_board_state.get("cities", {}).items():
                if bool(c.get("Available")):
                    # if your city dict uses different cost field, change here
                    cost = c.get("Cost", 0)
                    if cost == "inf":
                        continue
                    costs.append(safe_int(cost, 0))
        costs.sort()
        while len(costs) < 5:
            costs.append(0)
        for i in range(5):
            inputs.append(clamp(costs[i] / 100.0, 0.0, 1.0))  # +5 => 96

        # --- 8) Number of players (1) ---
        n_players = len(self._inventories) if hasattr(self, "_inventories") and self._inventories else 0
        inputs.append(clamp(n_players / 6.0, 0.0, 1.0))  # +1 => 97

        # --- 9) Win condition (1) ---
        win_conditions = {3: 17, 4: 17, 5: 15, 6: 14}
        win = win_conditions.get(n_players, 15)
        inputs.append(clamp(win / 20.0, 0.0, 1.0))  # +1 => 98

        # --- 10) Phase (1) ---
        inputs.append(clamp(current_phase / 5.0, 0.0, 1.0))  # +1 => 99

        # Ensure exact length
        if len(inputs) != 99:
            # Hard guarantee: pad or trim if your upstream fields differ slightly.
            if len(inputs) < 99:
                inputs.extend([0.0] * (99 - len(inputs)))
            else:
                inputs = inputs[:99]
        return inputs

    # -------------------------
    # Output decoding (14 -> actions)
    # -------------------------
    def _activate(self, phase: int) -> List[float]:
        ins = self._get_network_inputs(phase)
        outs = self.net.activate(ins)
        # neat-python returns list[float] length 14
        if len(outs) != 14:
            # defensive: pad/trim
            outs = list(outs)[:14]
            while len(outs) < 14:
                outs.append(0.0)
        return outs

    def _combined_market_values(self) -> List[int]:
        lower = (self._PowerStation_Market or {}).get(0, []) if hasattr(self, "_PowerStation_Market") else []
        upper = (self._PowerStation_Market or {}).get(1, []) if hasattr(self, "_PowerStation_Market") else []
        if len(lower) == 4:
            stations = list(lower[:4]) + list(upper[:2])  
        else:
            stations = list(lower)
        values = []
        for s in stations:
            values.append(str_to_station_dict_safe(s)["Value"])
        return values

    # -------------------------
    # Decisions overridden
    # -------------------------

    def _StartingCityPurchase(self) -> str:
        # Use NN preference via "cheapest cities" implicitly; simplest: pick cheapest available.
        # (Starting city is critical; you can later evolve this by adding city features to inputs.)
        available = []
        for city_id, c in self._latest_board_state.get("cities", {}).items():
            if bool(c.get("Available")):
                available.append((safe_int(c.get("Cost", 0), 0), city_id))
        if not available:
            return super()._StartingCityPurchase()
        available.sort()
        return available[0][1]

    def _StartingStationPurchase(self, valid_values: List[int]) -> int:
        outs = self._activate(phase=1)
        prefs = outs[0:4]
        chosen_idx = argmax(prefs)
        market_vals = self._combined_market_values()[0:4]

        # Map idx -> station value
        while True:
            if market_vals[chosen_idx] in valid_values and self._electros.get(self._Name, 0) >= market_vals[chosen_idx]:
                return market_vals[chosen_idx]
            else:
                prefs[chosen_idx] = -float("inf")
                chosen_idx = argmax(prefs)


    def _BidOnPowerStation(self, min_bid: int, electros: int, powerstation: str, held_by_player: str):
        outs = self._activate(phase=2)
        if len(self._PowerStation_Market[0]) == 4:
            prefs = outs[0:5]
        else:
            prefs = outs[0:6]
        most_preferred_idx = argmax(prefs)
        market_vals = self._combined_market_values()
        target_val = str_to_station_dict_safe(powerstation)["Value"]

        # If not found, fall back to a cautious pass.
        want = False
        if target_val == market_vals[most_preferred_idx]:
            want = True

        if not want or electros < min_bid:
            return False

        if want:
            # Bid min to try and win
            if target_val * prefs[most_preferred_idx] >= min_bid:
                return min_bid
        return False

    def _BuyStationDecision(self, valid: List[int], electros: int, market) -> int | bool:
        outs = self._activate(phase=2)
        if len(self._PowerStation_Market[0]) == 4:
            prefs = outs[0:4]
        else:
            prefs = outs[0:6]
        chosen_idx = argmax(prefs)
        market_vals = self._combined_market_values()

        # pick the most preferred station that is valid & affordable
        while True:
            v = market_vals[chosen_idx]
            if v in valid and v <= electros:
                return v
            else:
                prefs[chosen_idx] = -float("inf")
                chosen_idx = argmax(prefs)
            # if all prefs exhausted, break
            if all(p == -float("inf") for p in prefs):
                return False


    def _BuyResourcesDecision(self, resource_costs: dict, power_stations: List[str], resource_space: dict):
        outs = self._activate(phase=3)
        
        if self._Resource_buying_index >= 4:
            self._Resource_buying_index = 0
            return {'X': 0}  # Finished buying resources
        desired = [
            {"C":max(0, min(resource_space.get("C", 0), int(round((outs[7]) * resource_space.get("C", 0)))))},
            {"O": max(0, min(resource_space.get("O", 0), int(round((outs[8]) * resource_space.get("O", 0)))))},
            {"G": max(0, min(resource_space.get("G", 0), int(round((outs[9]) * resource_space.get("G", 0)))))},
            {"N": max(0, min(resource_space.get("N", 0), int(round((outs[10]) * resource_space.get("N", 0)))))},
        ]

        current_electros = self._electros.get(self._Name, 0)
        for fuel, amount in desired[self._Resource_buying_index].items():
            if self._Resource_Market.get(fuel):
                costs_list = resource_costs.get(fuel, [])
                if len(costs_list) >= amount:
                    cost = costs_list[amount - 1]
                    if int(current_electros) >= int(cost) and amount > 0:
                        self._Resource_buying_index += 1
                        
                        return {fuel: amount}
         

    def _BuyCityDecision(self, city_costs: dict, electros: int):
        outs = self._activate(phase=4)
        buy_yes = sigmoid(outs[11]) > 0.5
        if not buy_yes:
            return "FINISH"

        # Pick cheapest affordable city (simple + stable).
        affordable = []
        for city_id, cost in city_costs.items():
            if cost == 'inf':
                continue
            
            if int(cost) <= electros:
                affordable.append((int(cost), city_id))
        if not affordable:
            return "FINISH"
        affordable.sort()
        return affordable[0][1]

    def _Choose_Stations_to_power(self, electros: int, number_of_cities: int, power_stations: List[str], resources: dict) -> dict:
        outs = self._activate(phase=5)

        # outputs 12..14 correspond to up to 3 owned stations
        flags = [sigmoid(outs[12]) > 0.5, sigmoid(outs[13]) > 0.5, sigmoid(outs[14]) > 0.5]

        # build a plan: {station_value: {fuel_type: amt}}
        plan: Dict[int, Dict[str, int]] = {}
        res = dict(resources)  # copy so we can decrement safely
        
        # stable order: most cities powered first (good heuristic), NN decides which to try enabling
        stations_sorted = sorted(power_stations, key=lambda s: -str_to_station_dict_safe(s)["CitiesPowered"])

        picked = 0
        for i, station_str in enumerate(stations_sorted):
            if picked >= 3:
                break
            if i >= len(flags):
                break
            if not flags[i]:
                continue

            sd = str_to_station_dict_safe(station_str)
            val = sd["Value"]
            ftype = sd["FuelType"]
            famt = sd["FuelAmount"]

            if ftype == "R":
                plan[val] = {}
                picked += 1
                continue

            if ftype == "H":
                # prefer coal if possible else oil
                if res.get("C", 0) >= famt:
                    res["C"] -= famt
                    plan[val] = {"C": famt}
                    picked += 1
                elif res.get("O", 0) >= famt:
                    res["O"] -= famt
                    plan[val] = {"O": famt}
                    picked += 1
                continue

            if res.get(ftype, 0) >= famt:
                res[ftype] -= famt
                plan[val] = {ftype: famt}
                picked += 1

        return plan

