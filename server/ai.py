from shared import MESSAGES
import threading
from typing import List
import random
import ast
import time
import itertools
import math
class AIPlayer:
    """AI player who makes random valid moves
    """
    def __init__(self,name:str):
        """Initialiases AI player

        Args:
            name (str): Name of Ai player
        """
        self._Name = name
        self._latest_board_state = None
        self._inventories: dict[str, dict[str, int]] = {}
        self._electros:dict[str,int] = {}
        self._PowerStation_Market = None
        self._Resource_Market = None
        self._Receive_Message_Queue:List[tuple[str]] = []
        self._Send_Message_Queue:List[tuple[str]] = []
        self._lock = threading.Lock()
        self.Kill = False



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
            print(f"AI {self._Name} received message of type: {messageType}")
            # Logic to handle board state updates immediately
            if messageType == 'BoardDisplay':
                board_state, powerstation_market, resource_market, electros, player_resources_stations_dict = MESSAGES.BoardDisplay.parse_payload(message_dict)
                self._latest_board_state = board_state
                powerstation_market = powerstation_market.replace("inf", "'inf'")
                self._PowerStation_Market = ast.literal_eval(powerstation_market)
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
                time.sleep(0.1)
    
    def GetNextMessage(self):
        """Gets the next message the AI has prepared to send"""
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
    def __init__(self,name:str):
        super().__init__(name)
        self._PowerStations_to_Buy_resources_for = []
        self._index_of_next_station_to_buy_resources_for = 0
        self._Hybrid_fuel_left_over_dict = {}  # Tracks leftover fuel from hybrids for resource buying phase
    
    def _DiscardStationDecision(self, power_stations:List[str]):
        # Discards the station that powers the least cities, breaking ties by lowest value
        lowest_powering_station = str_to_station_dict(power_stations[0])
        for station in power_stations[1:]:
            station_data = str_to_station_dict(station)
            if lowest_powering_station.get('CitiesPowered') >= station_data.get('CitiesPowered'):
                if lowest_powering_station.get('Value') > station_data.get('Value'):
                    lowest_powering_station = station_data
        return lowest_powering_station.get('Value')

    def _BuyStationDecision(self, valid:List[int], electros:int,market):
        # Buy the station that powers the most cities, or any station with suffcient power to win, breaking ties by lowest cost of fuel and then lowest value.
        # Lowest Value as this means we save more electros for resources and cities and we can be in last place in future auctions

        winCondition = {3:17,4:17,5:15,6:14}
        N_of_Players = len(self._inventories)
        Required_power = winCondition.get(N_of_Players,15)

        owned_power_stations = self._inventories.get(self._Name)[1]
        for station in owned_power_stations:
            station_data = str_to_station_dict(station)
            Required_power -= station_data.get('CitiesPowered',0)
        if Required_power <=0:
            return False  # Don't buy any more stations if we can already power enough cities to win

        can_reach_required = False
        affordable_stations = []
        for station_value in valid:
            if station_value <= electros:
                affordable_stations.append(station_value)
        best_station = (0,0,float('inf'))  # (Value, CitiesPowered, FuelCost)
        power_stations = self._PowerStation_Market[0]

        for power_station in power_stations:
            station_data = str_to_station_dict(power_station)
            if station_data.get('Value') not in affordable_stations:
                continue
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
        if best_station[0] == 0:
            return False  # No station to buy
        return best_station[0]



    def _Choose_Stations_to_power(self, electros: int, number_of_cities: int, power_stations: List[str], resources: dict):
        available_stations = [str_to_station_dict(ps) for ps in power_stations]
        
        best_config = None
        max_cities_powered = -1
        min_cost = float('inf')

        # 1. Iterate through every possible subset of stations
        for r in range(len(available_stations) + 1):
            for station_combo in itertools.combinations(available_stations, r):
                
                # Identify which stations in this combo are hybrid ('H')
                hybrids = [s for s in station_combo if s.get("FuelType") == 'H']
                non_hybrids = [s for s in station_combo if s.get("FuelType") != 'H']
                
                # 2. Iterate through every combination of Coal ('C') or Oil ('O') for the hybrids
                # itertools.product generates all combinations like (C, C), (C, O), (O, C), (O, O)
                for hybrid_fuel_choices in itertools.product(['C', 'O'], repeat=len(hybrids)):
                    
                    temp_resources = resources.copy()
                    current_combo_cost = 0
                    possible_to_fuel = True
                    used_resources_mapping = {}
                    total_capacity = 0

                    # Process Non-Hybrids first
                    for s in non_hybrids:
                        f_type = s.get("FuelType")
                        f_amount = s.get("FuelAmount", 0)
                        val = s.get("Value")
                        
                        if f_type == 'R': # Renewable
                            used_resources_mapping[val] = {}
                            total_capacity += s.get("CitiesPowered", 0)
                        else:
                            if temp_resources.get(f_type, 0) >= f_amount:
                                current_combo_cost += self._Resource_Market[f_type][f_amount-1]
                                temp_resources[f_type] -= f_amount
                                used_resources_mapping[val] = {f_type: f_amount}
                                total_capacity += s.get("CitiesPowered", 0)
                            else:
                                possible_to_fuel = False
                                break
                    
                    if not possible_to_fuel: continue

                    # Process Hybrids based on the current product iteration
                    for i, s in enumerate(hybrids):
                        chosen_fuel = hybrid_fuel_choices[i]
                        f_amount = s.get("FuelAmount", 0)
                        val = s.get("Value")

                        if temp_resources.get(chosen_fuel, 0) >= f_amount:
                            current_combo_cost += self._Resource_Market[chosen_fuel][f_amount-1]
                            temp_resources[chosen_fuel] -= f_amount
                            used_resources_mapping[val] = {chosen_fuel: f_amount}
                            total_capacity += s.get("CitiesPowered", 0)
                        else:
                            possible_to_fuel = False
                            break
                    
                    # 3. Decision Logic: Maximize Cities (capped) > Minimize Cost
                    if possible_to_fuel:
                        effective_capacity = min(total_capacity, number_of_cities)
                        
                        if effective_capacity > max_cities_powered:
                            max_cities_powered = effective_capacity
                            min_cost = current_combo_cost
                            best_config = used_resources_mapping
                        
                        elif effective_capacity == max_cities_powered:
                            if current_combo_cost < min_cost:
                                min_cost = current_combo_cost
                                best_config = used_resources_mapping

        return best_config if best_config is not None else {}
    
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
        # Buy the cheapest affordable city if we can power it this turn
        powerable = 0
        for station in self._inventories.get(self._Name)[1]:
            station_data = str_to_station_dict(station)
            powerable += station_data.get('CitiesPowered',0)
        if powerable < len(self._inventories.get(self._Name)[0]) + 1:
            return 'FINISH'  # Can't power more cities this turn
        
        affordable_cities = []
        for city_id, cost in city_costs.items():
            if cost == 'inf':
                continue
            if int(cost) <= electros:
                affordable_cities.append(city_id)
        if len(affordable_cities) > 0:
            return sorted(affordable_cities)[0] # Buy the cheapest city
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
        while self._index_of_next_station_to_buy_resources_for != len(self._PowerStations_to_Buy_resources_for):
            station_to_buy_for = self._PowerStations_to_Buy_resources_for[self._index_of_next_station_to_buy_resources_for]
            station_data = str_to_station_dict(station_to_buy_for)
            fuel_type = station_data.get('FuelType')
            fuel_amount = station_data.get('FuelAmount')
            # Special handling for Hybrid fuel type
            if fuel_type == 'H':
                if self._Hybrid_fuel_left_over_dict.get(station_to_buy_for):
                    self._index_of_next_station_to_buy_resources_for += 1
                    if resource_space.get('C', 0) < fuel_amount:
                        # Not enough space, skip it
                        self._Hybrid_fuel_left_over_dict = {}
                        self._index_of_next_station_to_buy_resources_for += 1
                        continue
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
                    if used_dict['O'] !=0:
                        if used_dict['C'] !=0:
                            self._Hybrid_fuel_left_over_dict = {'C': used_dict['C']}
                        if resource_space.get('O', 0) < fuel_amount or resource_space.get('C', 0) < fuel_amount or self._electros.get(self._Name, 0) < (cost_of_oil + cost_of_coal):
                            # Not enough space, skip it
                            self._index_of_next_station_to_buy_resources_for += 1
                            continue
                        return {'O': used_dict['O']}
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
            if current_electros < cost:
                # Can't afford, skip it
                self._index_of_next_station_to_buy_resources_for += 1
                continue
            self._index_of_next_station_to_buy_resources_for += 1

            if resource_space.get(search_key, 0) < fuel_amount:
                # Not enough space, skip it
                continue
            return {search_key: fuel_amount}
        self._index_of_next_station_to_buy_resources_for = 0
        return {'X': 0}  # No stations to buy resources for