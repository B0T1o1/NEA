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
        self._resource_index = 0



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
            

            decoded_data = message.decode().replace("inf", "'inf'")
            message_dict = ast.literal_eval(decoded_data)
            
            messageType = MESSAGES.Message.parse_payload(message_dict)
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
                self._latest_board_state = board_state
            else:
                # Put other messages in the queue for RecieveLoop to process
                self._Receive_Message_Queue.append(message_dict) # Store as dict


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
        # treats like queue
        with self._lock:  # Use the threading lock
            if self._Send_Message_Queue:
                # Returns the message string 
                return self._Send_Message_Queue.pop(0)
        return None


    def _Process_Message(self, message:str):
        """Correctly Proccesses message and distrubutes logic and adds message to the send_message_queue

        Args:
            message (str): Message string in MESSAGES format
        """
        message_type = MESSAGES.Message.parse_payload(message)
        
        if message_type == 'BuyStartingCityRequest':
            # Handle starting city purchase 
            current_player, electros = MESSAGES.BuyStartingCityRequest.parse_payload(message)
            if current_player == self._Name:
                city_id_to_buy = self._StartingCityPurchase()
                buy_city_message = MESSAGES.BuyStartingCityResponse.construct_payload(city_id_to_buy)
                self._Send_Message_Queue.append(buy_city_message)

        if message_type == 'BuyStartingStationRequest':
            # Handle starting station purchase
            market, current_player,values, electros = MESSAGES.BuyStartingStationRequest.parse_payload(message)
            if current_player == self._Name:
                    station_id_to_buy = self._StartingStationPurchase(values)
                    buy_station_message = MESSAGES.BuyStartingStationResponse.construct_payload(station_id_to_buy)
                    self._Send_Message_Queue.append(buy_station_message)

        if message_type == 'BidOnPowerStation':
            # Handle bidding on powerstation
            powerstation, min_bid, current_player, held_by_player, electros = MESSAGES.BidOnPowerStation.parse_payload(message)
            if current_player == self._Name:
                bid_amount = self._BidOnPowerStation(min_bid, electros,powerstation ,held_by_player)
                bid_message = MESSAGES.BidOnPowerStationResponse.construct_payload(bid_amount)
                self._Send_Message_Queue.append(bid_message)

        if message_type == 'BuyResourcesRequest':
            # Handle resource buying
            current_player,resource_costs, power_stations, resource_space = MESSAGES.BuyResourcesRequest.parse_payload(message)
            if current_player == self._Name:
                resources_to_buy = self._BuyResourcesDecision(resource_costs, power_stations, resource_space)
                buy_resources_message = MESSAGES.BuyResourcesResponse.construct_payload(resources_to_buy)
                self._Send_Message_Queue.append(buy_resources_message)

        if message_type == 'BuyCityRequest':
            # Handle city buying
            current_player, electros,city_costs = MESSAGES.BuyCityRequest.parse_payload(message)
            if current_player == self._Name:
                city_id_to_buy = self._BuyCityDecision(city_costs, electros)
                buy_city_message = MESSAGES.BuyCityResponse.construct_payload(city_id_to_buy)
                self._Send_Message_Queue.append(buy_city_message)
                
        if message_type == 'BureaucracyUpdate':
            # Handle powering stations
            current_player, electros, number_of_cities, power_stations, resources = MESSAGES.BureaucracyUpdate.parse_payload(message)
            if current_player == self._Name:
                Choose_to_power_message = self._Choose_Stations_to_power(electros, number_of_cities, power_stations, resources)
                power_stations_message = MESSAGES.BureaucracyComplete.construct_payload(Choose_to_power_message)
                self._Send_Message_Queue.append(power_stations_message)

        if message_type == 'BuyPowerStationRequest':
            # Handle powerstation buying
            market, current_player, electros, valid_values = MESSAGES.BuyPowerStationRequest.parse_payload(message)
            if current_player == self._Name:
                station_to_buy = self._BuyStationDecision( valid_values, electros, market)
                buy_stations_message = MESSAGES.BuyPowerStationResponse.construct_payload(station_to_buy)
                self._Send_Message_Queue.append(buy_stations_message)

        if message_type == 'DiscardPowerStationRequest':
            # Handle powerstation discarding
            current_player,power_stations = MESSAGES.DiscardPowerStationRequest.parse_payload(message)
            if current_player == self._Name:
                station_to_discard = self._DiscardStationDecision(power_stations)
                discard_station_message = MESSAGES.DiscardPowerStationResponse.construct_payload(station_to_discard)
                self._Send_Message_Queue.append(discard_station_message)


    def _DiscardStationDecision(self, power_stations:List[str])-> int:
        """Discards a powerstation randomly

        Args:
            power_stations (List[str]): List of powerstations in specified string format 

        Returns:
            int: value of powerstation to discard
        """
        station_values = []
        for station in power_stations:
            station_data = str_to_station_dict(station)
            station_values.append(int(station_data.get("Value",0)))
        return random.choice(station_values) # Return random station value to discard

    def _BuyStationDecision(self, valid:List[int], electros:int,market:List[str]) -> int|bool:
        """Randomly buys and affordable powerstation if suich station exists

        Args:
            valid (List[int]): list of valid powerstation values
            electros (int): amount of electros available to the AI
            market (List[str]): List of powerstations in market in specified string format

        Returns:
            int or bool: value of powerstation to buy or False if none affordable
        """
        if random.random() > 0.5:
            return False  # 50% chance to not buy any station
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
        if random.random() > 0.7:
            return 'FINISH'  # 30% chance to not buy any city
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
        """Buys resources randomly if space and enough money

        Args:
            resource_costs (dict): cost of reosurces in market
            power_stations (List[str]): list of power stations owned by the AI
            resource_space (dict): available space for each resource type

        Returns:
            dict: resources to buy or {'X': 0} if finished buying
        """
        current_electros = self._electros.get(self._Name, 0)

        while True:
            if self._resource_index >= 4:
                self._resource_index = 0
                return {'X': 0}  # Finished Reosurce buying
            resource_type = ['C', 'O', 'G', 'N'][self._resource_index ]
            space = resource_space.get(resource_type, 0)
            if space == 0:
                if self._resource_index >= 4:
                    self._resource_index = 0
                    return {'X': 0}  # Finished Reosurce buying
                self._resource_index = (self._resource_index + 1)
                continue  # No space for this resource
            if resource_type == 'H' and space > 0:
                to_buy = random.randrange(0, space)
                if len(resource_costs.get('C', [])) > to_buy:
                    
                    if resource_costs['C'][to_buy] <= current_electros:
                        self._resource_index = (self._resource_index + 1)
                        return {'C': to_buy}  # Market is empty for this resource
            else:
                to_buy = random.randrange(0, space)
                if len(resource_costs.get(resource_type, [])) > to_buy:
                    
                    if resource_costs[resource_type][to_buy] <= current_electros:
                        self._resource_index = (self._resource_index + 1)
                        return {resource_type: to_buy}  # Market is empty for this resource
            self._resource_index = (self._resource_index + 1)
                    
    
def str_to_station_dict(station_string: str) -> dict[str, int|str]:
    """Turns the string of a station given over network into a dictionary

    Args:
        station_string (str): string of station

    Raises:
        ValueError: If any expected key is missing in the station string

    Returns:
        dict: Dictionary representation of the station
    """    
    data = {}
    # Handle empty or malformed strings 
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
    """ Hard AI player who makes strategic moves
    """
    def __init__(self,name:str, run_speed:float=0.1):
        """Intialiser for Hard ai player

        Args:
            name (str): Name of the AI player
            run_speed (float, optional): Speed at which the AI runs. Defaults to 0.1. (suggested 0.001 for ai only games)
        """
        super().__init__(name, run_speed)
        self._PowerStations_to_Buy_resources_for = []
        self._index_of_next_station_to_buy_resources_for = 0
        self._Hybrid_fuel_left_over_dict = {}  # Tracks leftover fuel from hybrids for resource buying phase
        self._PowerPlan = {}
        self._Number_of_cities_supported_in_power_plan = 0
        
    
    def _DiscardStationDecision(self, power_stations:List[str]) -> int:
        """Discards the station that powers the least cities, breaking ties by lowest value

        Args:
            power_stations (List[str]): list of power stations owned by the AI

        Returns:
            int: value of the station to discard
        """
        lowest_powering_station = str_to_station_dict(power_stations[0])
        station_tuples = [ (station_data.get('Value'), station_data.get('CitiesPowered',0),self._Get_cost_to_fuel(station_data)) for station_data in [str_to_station_dict(station) for station in power_stations]]
        loser_pair_1 = station_tuples[0]
        winner_pair_2,loser_pair_2 = self._which_station(station_tuples[1],station_tuples[2])
        middle,worst_station = self._which_station(loser_pair_1,loser_pair_2)
        return  worst_station[0] # Start with worst station so station we want to buy has to be better than it

    def _BuyStationDecision(self, valid:List[int], electros:int,market) -> int|bool:
        """Buys the station that helps reach the win condition the most, breaking ties by lowest cost of fuel and then lowest value

        Args:
            valid (List[int]): _description_
            electros (int): _description_
            market (_type_): _description_

        Returns:
            int|bool: The value of the station to buy or False if no station should be bought
        """


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
        
        # can we reach required power with a station from market, if so only consider those stations
        can_reach_required = False

        # Get Affordable stations from market
        affordable_stations = []
        for station_value in valid:
            if station_value <= electros:
                affordable_stations.append(station_value)

        
        power_stations = self._PowerStation_Market[0]
        for power_station in power_stations:
            station_data = str_to_station_dict(power_station)
            if station_data.get('Value') not in affordable_stations:
                continue
            # Evaluate station
            cost = self._Get_cost_to_fuel(station_data)
            station = (station_data.get('Value'), station_data.get('CitiesPowered'), cost)
            # Check if this station helps reach required power
            if station[1] >= Required_power:
                can_reach_required = True
            # If a station can reach required power and other can too, choose best among them
            if can_reach_required and station[1] >= Required_power:
                #choose lowest fuel cost
                if station[2] < best_station[2]:
                    best_station = station
                elif station[2] == best_station[2]:
                    # choose lowest value
                    if station[0] < best_station[0]:
                        best_station = station
            # If no station can reach required power, choose best overall
            elif station[1] > best_station[1] :
                # choose highest powering
                best_station = station
            elif station[1] == best_station[1]:
                # choose lowest fuel cost
                if station[2] < best_station[2]:
                    best_station = station
                elif station[2] == best_station[2]:
                    # choose lowest value
                    if station[0] < best_station[0]:
                        best_station = station
        if  best_station[0] == worst_station[0]:
            return False  # No station to buy
        return best_station[0]
    
    def _Get_cost_to_fuel(self,powerstation:dict) -> int:
        """Calculates the cost to fuel a powerstation given the current resource market

        Args:
            powerstation (dict): output of str_to_station_dict function representing the powerstation

        Returns:
            int: The cost to fuel the powerstation
        """
        fuel_type = powerstation.get('FuelType')
        fuel_amount = powerstation.get('FuelAmount')

        # Calculate fuel cost
        if fuel_type == 'H':
            used_dict = {'C':0,'O':0}
            cost_of_oil = 0
            cost_of_coal = 0
            # Buy the cheapest resources for hybrid
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
            # Total cost is sum of both fuels for hybrid
            cost = cost_of_coal + cost_of_oil

        elif fuel_type == 'R':
            # Free power
            cost = 0
        else:
            # Non-hybrid fuel type, buy from resource market, if enough resources exist
            if len(self._Resource_Market[fuel_type]) < fuel_amount:
                cost = float('inf')  # Not enough resources available
            else:
                cost = self._Resource_Market[fuel_type][fuel_amount - 1]


        return cost

    def _which_station(self,station1:tuple[int,int,int],station2:tuple[int,int,int]) -> tuple[tuple[int,int,int],tuple[int,int,int]]:
        """Check whether given the ranking system of highest powering, lowest fuel cost, lowest value which station is better

        Args:
            station1 (tuple[int,int,int]): a station tuple of (Value, CitiesPowered, FuelCost)
            station2 (tuple[int,int,int]): a station tuple of (Value, CitiesPowered, FuelCost)

        Returns:
            tuple[tuple[int,int,int],tuple[int,int,int]]: a tuple containing the better station first and the worse station second
        """
        if station1[1] > station2[1]:
            # station1 is better as it powers more cities
            return station1,station2
        elif station1[1] == station2[1]:
            if station1[2] < station2[2]:
                # station1 is better as it has lower fuel cost
                return station1,station2
            elif station1[2] == station2[2]:
                # tie breaker by value
                if station1[0] < station2[0]:
                    return station1,station2
        # station2 is better as it powers more cities or is better in tie breaker
        return station2,station1
    
    def _Choose_Stations_to_power(self, electros: int, number_of_cities: int, power_stations: List[str], resources: dict) -> dict[int, dict[str, int]]:
        """Chooses to power stations, priotising powering stations that can power more cities by considering them first
        First tries to use the precomputed power plan, calculated in the resource buying phase, if suffcient resources exist
        If not enough resources exist it creates a new power plan

        Args:
            electros (int): player's electros
            number_of_cities (int): number of cities the player currently owns
            power_stations (List[str]): list of power station strings owned by the player
            resources (dict): dictionary of available resources by type

        Returns:
            dict[int, dict[str, int]]: A dictionary mapping station values to resource usage dictionaries
        """
        
        real_power_plan: dict[int, dict[str, int]] = {}
        sorted_stations = sorted(power_stations, key=lambda x: -str_to_station_dict(x).get('CitiesPowered', 0))
        resource_check = {'C':0,'O':0,'G':0,'N':0}
        plan_works = True
        for station_val,resource_powering in self._PowerPlan.items():
            for r_type, r_amt in resource_powering.items():
                resource_check[r_type] += r_amt
        # Check if resources are suffcient for precomputed power plan
        for r_type, r_amt in resource_check.items():
            if resources.get(r_type,0) < r_amt:
                plan_works = False
        if plan_works:
            # Use precomputed power plan
            return self._PowerPlan
        
        # Create new power plan
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
                    # Use coal first for hybrid
                    resources['C'] -= f_amt
                    real_power_plan[val] = {'C': f_amt}
                elif resources.get('O', 0) >= f_amt:
                    # Use oil if no coal
                    resources['O'] -= f_amt
                    real_power_plan[val] = {'O': f_amt}
            elif f_type in resources:
                # Check resources
                if resources[f_type] >= f_amt:
                    resources[f_type] -= f_amt
                    real_power_plan[val] = {f_type: f_amt}
                    
        return real_power_plan
        
    
    def _StartingCityPurchase(self) -> str:
        """ Calculates the best city to buy 
        city_score is average connection cost divided by number of connections (cheaper and more connections is better)

        Returns:
            str: The ID of the best city to buy
        """
        best_city_id = []
        best_city_score = float('inf')
        for city_id,city_data in self._latest_board_state['cities'].items(): # gives dict of city_id:city_data
            if bool(city_data['Available']) is True:

                total_connection_cost = 0
                connection_count = 0
                for i,connection in city_data['connections'].items():
                    # Skip infinite connections
                    if connection == 'inf':
                        continue
                    connection_count += 1
                    total_connection_cost += int(connection)
                # Avoid division by zero
                if connection_count == 0:
                    continue
                # Calculate city score
                city_score = total_connection_cost / (connection_count)**2
                # Check if this city is better than the best found so far
                if city_score < best_city_score:
                    best_city_score = city_score
                    best_city_id = city_id
        return best_city_id
    
    def _BuyCityDecision(self,city_costs:dict, electros:int) -> str:
        """Buys the cheapest city available if one exists

        Args:
            city_costs (dict): A dictionary mapping city IDs to their costs
            electros (int): The amount of electros available for purchasing

        Returns:
            str: The ID of the city to buy or 'FINISH' if no purchase is made
        """
        
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
    
    def _StartingStationPurchase(self,valid_values:List[int] ) -> int:
        """Buy the station that powers the most cities, breaking ties by lowest cost of fuel and then lowestr value

        Args:
            valid_values (List[int]): a list of the values of stations that are available to be bought

        Returns:
            int: The value of the best station to buy
        """
        best_station = (0,0,float('inf'))  # (Value, CitiesPowered, FuelCost)
        power_stations = self._PowerStation_Market[0]

        for power_station in power_stations:
            station_data = str_to_station_dict(power_station)
            # calculate cost to fuel
            cost = self._Get_cost_to_fuel(station_data)
            station = (station_data.get('Value'), station_data.get('CitiesPowered'), cost)
            best_station,worst_station = self._which_station(station,best_station)
        return best_station[0]

    def _BidOnPowerStation(self, min_bid:int, electros:int,powerstation:str ,held_by_player:str):
        """Deciedes whether to bid on a poewrstaion by considering if it would have gone to buy that powerstation out of the top 5 (as if skip a new powerstation will exist) then using 1/(min_bid-value + 1) as probability of bidding

        Args:
            min_bid (int): minimum bid required
            electros (int): electros available to the AI
            powerstation (str): powerstation being bid on
            held_by_player (str): player currently holding the powerstation

        Returns:
            int|bool: amount to bid or False to skip
        """
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
    
    def _BuyResourcesDecision(self, resource_costs: dict, power_stations: List[str], resource_space: dict) -> dict[str, int]:
        """Deciedes to buy resources for all powerstations as cheaply as possible if affordable 

        Args:
            resource_costs (dict): dictionary mapping resource types to their costs
            power_stations (List[str]): list of power stations owned by the AI
            resource_space (dict): dictionary mapping resource types to available space

        Returns:
            dict[str, int]: dictionary mapping resource types to quantities to buy
        """
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
                    return self._Hybrid_fuel_left_over_dict.get(station_to_buy_for)
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
                                
                            if (resource_space['O'] < used_dict['O']) or (resource_space['C'] < used_dict['C']) or (self._electros.get(self._Name, 0) < (cost_of_oil + cost_of_coal)):
                                # Not enough money, skip it
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




