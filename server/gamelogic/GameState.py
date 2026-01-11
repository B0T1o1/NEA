from .Player import PlayerC
import random
from .Board import BoardC
from .Resource_Market import R_Market
from .PowerStationMarket import PS_Market
from .PowerStation import PowerStationC
from typing import List, Literal
import math

class GameStateC:
    """Creates an instance of a game
    """
    def __init__(self):
        """Sets starting attributes
        """
        self.__stage = 1
        self._Round = 0
        self.__Phase = 1
        self.__startingcites = []
        self.__UsedDiscount = False
        self.__Phase2:Phase2
        self.__Phase3:Phase3
        self.__Phase4:Phase4
        self.__Phase5:Phase5
        self.__Players: List[PlayerC]

    ### SET UP METHODS ###
    def Set_number_of_players(self, n: int) -> bool:
        """Records the number of players to setup the game=, ensuring it is between 3 and 6 inclusive

        Args:
            n (int): number of players between 3 and 6 inclusive 

        Raises:
            ValueError: if number of players not between 3 and 6

        Returns:
            bool: if setup works
        """
        if 3 <= n <= 6:
            self.__NofPlayers = n
            return True
        raise ValueError("Number of players must be between 3 and 6.")

    def Set_settings(self,BoardFile: str = "data/board.JSON",StationFile: str = "data/stations.JSON", starting_electros: int = 50,self_regions:List[str]= ["Brown","Yellow","Red","Purple"],map:str='G'):
        """Intialises the board and sets game settings

        Args:
            BoardFile (str): The board file path. Defaults to "data/board.JSON".
            StationFile (str): The station file path. Defaults to "data/stations.JSON".
            starting_electros (int): The starting electros for players. Defaults to 50.
            self_regions (List[str]): The regions for the game. Defaults to ["Brown","Yellow","Red","Purple"].
            map (str): The map identifier. Defaults to 'G'.
        """
        self.__PowerStationMarket: PS_Market = PS_Market(StationFile,self.__NofPlayers)
        self.__STARTING_ELECTROS = starting_electros
        self.__ResourceMarket: R_Market = R_Market()
        self.__regions = self_regions
        self.__Board = BoardC(BoardFile, map,self.__regions)
        
    
    def Set_player_names(self, names: list[str]):
        """Sets player names

        Args:
            names (list[str]): list of names to be used

        Returns:
            bool: if setup works
        """
        if len(names) == self.__NofPlayers:
            self.__Players = [PlayerC(self.__STARTING_ELECTROS, name) for name in names]
            self.__PName_to_PClass = {player.GetName(): player for player in self.__Players}
            random.shuffle(self.__Players)
            return True
        return False
    


    
    def Set_starting_city(self,player_name:str,city:str) -> bool:
        """Checks and sets starting city for a player

        Args:
            player_name (str): Name of player choosing
            city (str): city that player would like to start at, must be a valid city_id

        Returns:
            bool: if Starting city was set
        """
        player = self.__PName_to_PClass.get(player_name)
        if city in self.__startingcites or not self.__CheckIfCity(city) or not player:
            return False
        else:
            self.__startingcites.append(city)
            player.AddSourceCity(city)
            self.__Board.cityIds_to_CityClass[city].PlayerBuyCity(player_name)
            return True

    def __CheckIfCity(self,cityId:str) -> bool:
        """Checks if a cityid exists

        Args:
            cityId (str): The ID of the city to check.

        Returns:
            bool: True if the city ID exists, False otherwise.
        """
        if cityId in self.__Board.city_ids:
            return True
        else:
            return False

    ### Getters ###
    def Get_players(self) -> list[str]:
        """gives player names

        Returns:
            list[str]: list of player names
        """
        return [player.GetName() for player in self.__Players]
    
    def Get_board(self,playername:str) -> dict[str,list[str]|dict]:
        """Gets the board and returns in special dict format

        Args:
            playername (str): name of a player

        Returns:
            dict: the board in a special format
        """
        playerClass = self.__PName_to_PClass[playername]
        return self.__Board.DisplayBoardInfo(playerClass.GetSourceCity(),playername)

    def Get_whole_board_info(self) -> tuple[str, dict[str,List[int]], dict[str,int], dict[str,tuple[dict[str,int],List[str]]]]:
        """Gets all information of the game

        Returns:
            tuple[str, dict, dict, dict, dict]: powerstation market, resource market, electros dict, player resources and stations dict
        """
        powerstation_market = self.Get_Current_Market_String()
        resource_market =          {
            'C': self.__ResourceMarket.GetCostOfCoal(),
            'O': self.__ResourceMarket.GetCostOfOil(),
            'G': self.__ResourceMarket.GetCostOfGarbage(),
            'N': self.__ResourceMarket.GetCostOfNuclear()
        }
        electros = {player.GetName(): player.GetElectros() for player in self.__Players}
        player_resources_stations_dict = {player.GetName():(player.GetResources(), [station.station_to_str() for station in player.GetPowerStations()] ) for player in self.__Players}

        return powerstation_market, resource_market, electros, player_resources_stations_dict
    
    def Get_board_before_game(self) -> dict:
        """Gets the board information before the game starts

        Returns:
            dict: board information before the game
        """
        return self.__Board.DisplayBoardInfoBeforeGame()
    def Get_round(self) -> int:
        """Gets the current round number

        Returns:
            int: current round number 
        """
        return self._Round
    
    def Get_phase(self) -> int:
        """Gets the current phase number

        Returns:
            int: Current Phase number
        """
        return self.__Phase
    
    def Get_stage(self) -> int:
        """Gets the current stage number

        Returns:
            int: Current stage number
        """
        return self.__stage
    
    def Get_electros_of(self,player_name:str) -> int:
        """Gets the electros of the player specified

        Args:
            player_name (str): name of a player

        Raises:
            IndexError: if player name not in game

        Returns:
            int: number of electros of player
        """
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return player.GetElectros()
        else:
            raise IndexError(f'Player with name {player_name} not found.')



    #Game Logic Methods Below
    def Start_Game(self) -> bool:
        """Starts the game - completing phase 1 and sets to phase 2

        Returns:
            bool: True if the game started successfully, False otherwise.
        """
        if self.__Phase ==1 and len(self.__startingcites) == self.__NofPlayers:
            self.__Do_Phase_1_start()
            self.__Phase = 2
            return True
        else:
            return False
    ### Phase 1 Methods ###
    def __Do_Phase_1_start(self)-> bool:
        """Does phase 1 for the first round, randomly ordering players

        Raises:
            Exception: if not in phase 1

        Returns:
            bool: True if phase 1 started successfully, False otherwise.
        """
        if self.__Phase == 1:    
            Phase1.Random_Assignment(self.__Players)
            self.__Phase = 2
            return True
        raise Exception("Not in Phase 1")

    def Do_Phase_1_order(self) -> list[str]:
        """Determines player order for phase 1 based on number of cities and highest power station value

        Raises:
            Exception: if not in phase 1

        Returns:
            list[str]: list of player names in the new order
        """
        if self.__Phase == 1:
            self.__Players = Phase1.Determine_Player_Order(self.__Players)
            self.__Phase = 2
            return [player.GetName() for player in self.__Players]
        raise Exception("Not in Phase 1")
    
    ### Phase 2 Methods ###

    def Get_Current_Market_String(self) -> str:
        """Returns the powerstation market as a string

        Returns:
            str: powerstation market
        """
        return self.__PowerStationMarket.GetMarketString()
    
    def Get_Valid_station_values(self) -> list[int]:
        """Gives the Valid Values of the stations that can be bought in the powerstation market

        Returns:
            list[int]: list of valid powerstation values
        """
        current_market, future_market = self.__PowerStationMarket.GiveMarket()
        return [ps.GetValue() for ps in current_market]
    
    def Start_Auction(self) -> bool:
        """Intialises Phase 2 logic if the self.__Phase == 2

        Returns:
            bool: True if Phase 2 started successfully, False otherwise.
        """
        if self.__Phase == 2:
            if self._Round == 0:
                self.__Phase2 = Phase2StartingRound(self.__PowerStationMarket,self.__Players,self.__stage)
            else:
                self.__Phase2 = Phase2(self.__PowerStationMarket,self.__Players,self.__stage)
            return True
        return False
    
    def Convert_PS_value_to_class(self, ps_value:int) -> PowerStationC|Literal[False]:
        """Converts a Powerstation value into the powerstation class if it is in the powerstation market

        Args:
            ps_value (int): The value of the powerstation to convert.

        Returns:
            PowerStationC|Literal[False]: The PowerStation object if found, otherwise False.
        """
        if int(ps_value) not in self.Get_Valid_station_values():
            return False  # not a valid powerstation value

        powerstations = self.__PowerStationMarket.GiveMarket()[0]

        for ps in powerstations:
            if ps.GetValue() == int(ps_value):
                return ps  # this is the PowerStation object
        return False  # if not found


    def Starting_Bid_on_Power_Station(self, player_name: str, ps_value: int) -> bool:
        """Allows a player to create a starting bid on a powerstation if it is their turn

        Args:
            player_name (str): Player name making the bid
            ps_value (int): Value of powerstation to bid on

        Raises:
            Exception: if not in Phase 2

        Returns:
            bool: True if starting bid was successful, False otherwise.
        """
        if self.__Phase == 2:
            player = self.__PName_to_PClass.get(player_name)
            station = self.Convert_PS_value_to_class(ps_value)
            if station and player:
                return self.__Phase2.Select_Station_For_Auction(station, player)
            return False
        raise Exception("Not in Phase 2")
    
    def Place_Bid(self, player_name: str, bid: int) -> bool:
        """Places a bid for a player on the current power station if in bidding round

        Args:
            player_name (str): a player name in the game
            bid (int): the amount of the bid

        Raises:
            IndexError: if the player name is not found
            Exception: if not in Phase 2

        Returns:
            bool: True if the bid was successfully placed, False otherwise.
        """
        if self.__Phase ==2:
            player = self.__PName_to_PClass.get(player_name)
            if player:
                return self.__Phase2.Receive_Bid(player,bid)
            raise IndexError(f'Player with name {player_name} not found.')
        raise Exception("Not in Phase 2")
    
    def Resign_From_Bidding(self,player_name:str) -> tuple[str|Literal[False],int,str|Literal[False],bool]:
        """Resigns a player from bidding

        Args:
            player_name (str): A player name in the game

        Raises:
            IndexError: if the player name is not found
            Exception: if not in Phase 2
        Returns:
            tuple[str|Literal[False],int,str|Literal[False],bool]: Winner name or False, winning bid, station string or False, needs to discard bool
        """
        if self.__Phase == 2:
            player = self.__PName_to_PClass.get(player_name)
            if player:
                winner, winning_bid,station,needs_to_discard = self.__Phase2.Receive_Resign(player)
                if winner and station:
                    if self.__Phase2.Used_Discount():
                        self.__UsedDiscount = True
                    return winner.GetName(), winning_bid ,  station.station_to_str(), needs_to_discard
                return False, 0 ,False, False
            raise IndexError(f'Player with name {player_name} not found.')
        raise Exception("Not in Phase 2")
    
    def Resign_from_auction(self,player_name:str):
        """Resigns a player from the auction meaning they cannot buy a powerstation this round

        Args:
            player_name (str): a name of a player in the game

        Raises:
            IndexError: if the player name is not found
            Exception: if not in Phase 2
        """
        if self.__Phase == 2:
            player = self.__PName_to_PClass.get(player_name)
            if player:
                winner, winning_bid,station,needs_to_discard = self.__Phase2.Receive_Resign(player)
            else:
                raise IndexError(f'Player with name {player_name} not found.')
        else:
            raise Exception("Not in Phase 2")
    
    def Discard_PowerStation(self,player_name:str,ps_value:str) -> bool:
        """Discards the powerstation chosen by the player

        Args:
            player_name (str): a player name in the game
            ps_value (str): a powerstation value of a powerstation the player owns

        Raises:
            IndexError: if the player name is not found
            IndexError: if the powerstation value is not found
            Exception: if not in Phase 2

        Returns:
            bool: True if discard was successful, False otherwise.
        """
        if self.__Phase == 2:
            player = self.__PName_to_PClass.get(player_name)
            if not player:
                raise IndexError(f'Player with name {player_name} not found.')
            stations = player.GetPowerStations()
            for ps in stations:
                if ps.GetValue() == int(ps_value):
                    station = ps
            if player and station:
                self.__Phase2.Discard_PowerStation(player,station)
                return True
            else:
                raise IndexError(f'Player with name {player_name} not found.')
        else:
            raise Exception("Not in Phase 2")
    
    def Get_Waiting_Discard_Player(self) -> str|bool:
        """Gets whether the game state is waiting for a player to disard a powerstation

        Raises:
            Exception: if not in Phase 2

        Returns:
            str|bool: player name if waiting for discard, False otherwise
        """
        if self.__Phase == 2:
            player = self.__Phase2.Get_Waiting_Discard_Player()
            if player:
                return player.GetName()
            
            return False
        else:
            raise Exception("Not in Phase 2")
    
    def Get_Next_Bidder_in_Round(self) -> str:
        """Gets the next player to bid in a bidding round

        Raises:
            Exception: if not in Phase 2

        Returns:
            str: the name of the next player to bid in the round
        """
        if self.__Phase == 2:
            bidder = self.__Phase2.Get_Next_Bidder_in_Round()
            return bidder.GetName()
        raise Exception("Not in Phase 2")
    
    def Get_info_Bidding_Round(self) -> tuple[int, str, str]:
        """Get the information on a bidding round

        Raises:
            Exception: if not in phase 2

        Returns:
            tuple[int, str, str]: mininmum bid, station string , player name who holds the bid
        """
        if self.__Phase == 2:
            min_bid, station, player =  self.__Phase2.Get_info_on_BRound()
            return min_bid, station.station_to_str(),player.GetName()
        else:
            raise Exception("Not in Phase 2")


    def Get_Next_Bidder(self) -> str|Literal[False]:
        """Get the next bidder choose a station to bid on

        Raises:
            Exception: if not in phase 2

        Returns:
            str|Literal[False]: player name of next bidder if not in bidding round
        """
        if self.__Phase == 2:
            bidder = self.__Phase2.Get_Next_Bidder()
            if bidder:
                return bidder.GetName()
            return False
        else:
            raise Exception("Not in Phase 2")
    
    def Finish_Auction(self) -> bool:
        """Finishes Stage 3

        Raises:
            Exception: if not in phase 2

        Returns:
            bool: True if all players have skipped or bought power stations, False O|therwise
        """ 
        if self.__Phase == 2:
            if self.__Phase2.Finish_Auction():
                self.__Phase = 3
                return True
            else:
                return False
            
        else:
            raise Exception("Not in Phase 2")

    ### Phase 3 Methods ###
    def Do_Resource_Buying(self):
        """Starts the resource buying phase

        Raises:
            Exception: if not in phase 3
        """
        if self.__Phase == 3:
            self.__Phase3 = Phase3(self.__ResourceMarket,self.__Players[::-1])
        else:
            raise Exception("Not in Phase 3")
        
    def Get_Resource_Buyers(self) -> list[str]:
        """Gets the list of players who are currently buying resources

        Raises:
            Exception: if not in phase 3

        Returns:
            list[str]: list of player names left to buy resources in order from first to last
        """
        if self.__Phase != 3:
            raise Exception("Not in Phase 3")
        return [player.GetName() for player in self.__Phase3.Get_Players_to_buy()]
    
    def Get_Next_Resource_Buyer(self) -> str|Literal[False]:
        """Gets the next player to buy resources

        Raises:
            Exception: if not in phase 3

        Returns:
            str|Literal[False]: player name of next resource buyer if any left, False otherwise
        """
        if self.__Phase != 3:
            raise Exception("Not in Phase 3")
        buyers = self.__Phase3.Get_Players_to_buy()
        if buyers:
            return buyers[0].GetName()
        return False
    
    def Get_Resource_Costs(self) -> dict[str, list[int]]:
        """Gets the costs of resources in the market

        Raises:
            Exception: if not in phase 3

        Returns:
            dict[str, list[int]]: costs of resources in the market
        """
        if self.__Phase != 3:
            raise Exception("Not in Phase 3")
        return self.__Phase3.Get_Resource_Costs()

    def Buy_Resource(self,player_name:str,ResourceType:str,amount:int) -> bool:
        """Buys a specified amount of a resource for a player

        Args:
            player_name (str): name of the player buying the resource
            ResourceType (str): type of resource to buy
            amount (int): amount of the resource to buy

        Raises:
            Exception: if not in phase 3
            IndexError: if player not found
        Returns:
            bool: True if the resource was bought successfully, False otherwise
        """
        if self.__Phase != 3:
            raise Exception("Not in Phase 3")
        player = self.__PName_to_PClass.get(player_name)
        if amount == 0:
            return self.Player_Finished_Buying(player_name)
        elif player:
            return  self.__Phase3.Buy_Resources(player,ResourceType,amount)
        else:
            raise IndexError(f'Player with name {player_name} not found.')
    
    def Get_PowerStations_of(self,player_name:str) -> List[str]:
        """Gets the powerstations of a player

        Args:
            player_name (str): name of the player whose powerstations are being retrieved

        Raises:
            IndexError: if player not found

        Returns:
            List[str]: list of powerstations of the player
        """
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return [ps.station_to_str() for ps in player.GetPowerStations()]
        else:
            raise IndexError(f'Player with name {player_name} not found.')
        
    def Get_Resource_Space_of(self,player_name:str) -> dict[str,int]:
        """Gets the resource space of the specified player

        Args:
            player_name (str): name of the player whose resource space is being retrieved

        Raises:
            IndexError: if player not found

        Returns:
            dict[str,int]: resource space of the player
        """
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return player.GetResourceSpace()
        else:
            raise IndexError(f'Player with name {player_name} not found.')
        
    def Player_Finished_Buying(self,player_name:str) -> bool:
        """Retires a player from phase 3, meaning they cannot buy anymore resources

        Args:
            player_name (str): name of the player who has finished buying resources

        Raises:
            Exception: if not in phase 3
            IndexError: if player not found
        Returns:
            bool: True if the player was successfully retired from buying resources, False otherwise
        """
        if self.__Phase != 3:
            raise Exception("Not in Phase 3")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return self.__Phase3.Player_Finished_Buying(player)
        else:
            raise IndexError(f'Player with name {player_name} not found.')
    
    def Finish_Resource_Buying(self):
        """Ends phase 3

        Raises:
            Exception: if not in phase 3
            Exception: if not all players have finished buying resources

        Returns:
            bool: True if phase 3 ended successfully, otherwise raises an exception
        """
        if self.__Phase != 3:
            raise Exception("Not in Phase 3")
        if self.__Phase3.Finish_Resource_Buying():
            self.__Phase = 4
            return True
        raise Exception("Not all Players have finished buying resources yet.")

    ### Phase 4 Methdos ###
    def Do_City_Buying(self):
        """Starts phase 4

        Raises:
            Exception: if not in phase 4
        """
        if self.__Phase != 4:
            raise Exception("Not in Phase 4")
        self.__Phase4 = Phase4(self.__Players[::-1],self.__Board)
        
    def Get_Players_for_City_Buying(self) -> List[str]:
        """Gets the players left to complete city buying in order form first to last

        Raises:
            Exception: if not in phase 4

        Returns:
            List[str]: list of player names left to do city buying 
        """
        if self.__Phase != 4:
            raise Exception("Not in Phase 4")
        return [player.GetName() for player in self.__Phase4.Get_Players()]
    
    def Get_Next_City_Buyer(self) -> str|Literal[False]:
        """Gets the next player to do city buying

        Raises:
            Exception: if not in phase 4

        Returns:
            str|bool: next players name if there are buyers left
        """
        if self.__Phase != 4:
            raise Exception("Not in Phase 4")
        buyers = self.__Phase4.Get_Players()
        if buyers:
            return buyers[0].GetName()
        return False

    def Get_City_Costs(self,player_name:str) -> dict[str,int]:
        """Gets the costs to go to each city for a specfified player

        Args:
            player_name (str): player name to get the costs for 

        Raises:
            Exception: if not in phase 4
            IndexError: if player not in game

        Returns:
            dict[str,int]: dictionary with city id for keys and values are costs to get to city id
        """
        if self.__Phase != 4:
            raise Exception("Not in Phase 4")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return self.__Phase4.Get_Costs()
        else:
            raise IndexError(f'Player with name {player_name} not found.')
        
    def Player_Finished_city_buying(self,player_name:str) -> bool:
        """Retires a player from cuty buying meaning that they cannot buy any more cities in this round

        Args:
            player_name (str): player to retire

        Raises:
            Exception: if not in phase 4
            IndexError: if player not in the game

        Returns:
            bool: True if the player was successfully retired from city buying, False otherwise
        """
        if self.__Phase != 4:
            raise Exception("Not in Phase 4")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return self.__Phase4.Player_Finished_Buying(player)
        else:
            raise IndexError(f'Player with name {player_name} was not found')
        
    def Player_Buy_City(self,player_name:str,city_id:str) -> bool:
        """Checks player cna buy city and buys city if they can, also allows for retiring from city buying buy entering "FINISH"

        Args:
            player_name (str): name of player to buy the city
            city_id (str): city they would like to buy

        Raises:
            Exception: if not in phase 4
            IndexError: if player name not in game

        Returns:
            bool: True if city was bought successfully, False otherwise
        """
        if self.__Phase != 4:
            raise Exception("Not in Phase 4")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            if city_id == "FINISH":
                    return self.__Phase4.Player_Finished_Buying(player)
            else:
                if self.Get_Next_City_Buyer() != player_name:
                    return False
                return self.__Phase4.Player_Buy_City(city_id)
        else:
            raise IndexError(f'Player with name {player_name} was not found')

    def Finish_City_Buying(self) -> bool:
        """Ends phase 4 once all players have finished city buying

        Raises:
            Exception: if not in phase 4
        Returns:
            bool: True if phase 4 was successfully finished, False otherwise
        """
        if self.__Phase != 4:
            raise Exception("Not in Phase 4")
        
        if self.__Phase4.Finshed_city_buying():
            self.__Phase = 5
            return True
        return False
 
    ### Phase 5 Methods ###
    def Do_Bureaucracy(self):
        """Starts phase 5

        Raises:
            Exception: if not in phase 5
        """
        if self.__Phase != 5:
            raise Exception("Not in Phase 5")
        self.__Phase5 = Phase5(self.__Players,self.__ResourceMarket,self.__PowerStationMarket,self.__Board,self.__stage,self.__UsedDiscount)

    def Get_Info_For_Bureaucracy(self) -> tuple[str|Literal[False],int,int,List[str],dict[str,int]]:
        """Give information for bureacry 

        Raises:
            Exception: if not in phase 5

        Returns:
            tuple[str|Literal[False],int,int,List[str],dict[str,int]]: Information for bureaucracy, next player to do buracary, their electros, number of cities, list of powerstations as strings, resources dict
        """
        if self.__Phase != 5:
            raise Exception("Not in Phase 5")

        player,electros, number_of_cities, Powerstations,resources = self.__Phase5.GetInfoForBureaucracy()
        if not player:
            return False,0,0,[],{}
        power_stations_str = [ps.station_to_str() for ps in Powerstations]
        return player.GetName() ,electros, number_of_cities, power_stations_str,resources
    
    def Player_Do_Bureaucracy(self,player_name:str,Stations_Powered_resources_Dict:dict[str,dict[str,int]]):
        """Complete buracracy for a player

        Args:
            player_name (str): player name doing bureaucracy
            Stations_Powered_resources_Dict (dict[str,dict[str,int]]): dictionary mapping power station values as strings to resource dictionaries

        Raises:
            Exception: if not in phase 5
            IndexError: if player name not found
        Returns:
            bool: True if bureaucracy was successfully completed, False otherwise
        """
        if self.__Phase != 5:
            raise Exception("Not in Phase 5")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            # Convert string keys back to PowerStationC objects
            converted_dict:dict[PowerStationC, dict[str,int]] = {}
            for powerstation in player.GetPowerStations():
                for ps_val, res_dict in Stations_Powered_resources_Dict.items():
                    if powerstation.GetValue() == int(ps_val):
                        res_dict_converted = {res_type: int(amount) for res_type, amount in res_dict.items()}
                        converted_dict[powerstation] = res_dict_converted
                        
            return self.__Phase5.Player_Do_Bureaucracy(player,converted_dict)
        else:
            raise IndexError(f'Player with name {player_name} was not found')
    
    def Check_Stage_Change_And_Win(self):
        """Completes the rest of bureacracy that does not invlove player actions

        Raises:
            Exception: if not in phase 5

        Returns:
            str|None: Winner's name if there is a winner, None otherwise
        """
        if self.__Phase != 5:
            raise Exception("Not in Phase 5")
        winner,self.__stage = self.__Phase5.CheckStageChangeAndWin()
        if winner:
            return winner.GetName()
        self._Round += 1
        self.__Phase = 1
        self.Do_Phase_1_order()
        self.__Phase = 2
        self.__UsedDiscount = False
        return None
    



        

          




class Phase1:
    """Holds Phase 1 logic
    """
    @staticmethod
    def Random_Assignment(players:list[PlayerC]) -> list[PlayerC]:
        """Completes phase 1 for the first round, randomly shuffling players into an order

        Args:
            players (list[PlayerC]): list of PlayerC objects representing the players

        Returns:
            list[PlayerC]: list of PlayerC objects in randomized order
        """
        random.shuffle(players)
        return players
    @staticmethod

    def Determine_Player_Order(players:list[PlayerC]) -> list[PlayerC]:
        """Determines player order for phase 1 based on number of cities and highest power station value

        Args:
            players (list[PlayerC]): list of PlayerC objects representing the players
        Returns:
            list[PlayerC]: list of PlayerC objects in order
        """
        players.sort()
        return players
    

class Phase2:
    """Holds Phase 2 logic
    """
    def __init__(self,PS_Market:PS_Market,players:List[PlayerC],stage:int):
        """Intialses phase 2

        Args:
            PS_Market (PS_Market): the powerstation market
            players (List[PlayerC]): list of PlayerC objects representing the players in phase 2 order
            stage (int): the current stage of the game
        """
        self._PS_Market = PS_Market
        self._Players = players
        self._Players_to_buy = list(players)
        if stage <  3:
            self._Discount = True
        else:
            self._Discount = False
        self._In_BRound = False
        self._BRound: BiddingRound
        self._Waiting_for_discard_player: PlayerC|None = None
        
    def Get_Waiting_Discard_Player(self) -> PlayerC|Literal[False]:
        """Give the player that the game is waiting for to discard their excess powerstation, or false if no such player exists

        Returns:
            PlayerC|Literal[False]: player who needs to discard a station
        """
        if self._Waiting_for_discard_player:
            return self._Waiting_for_discard_player
        return False
    
    def Get_Next_Bidder_in_Round(self) -> PlayerC:
        """Gets the next player who should bid in the current bidding round

        Raises:
            Exception: if not currently in a bidding round

        Returns:
            PlayerC: the next player to bid
        """

        if self._In_BRound:
            return self._BRound.Get_Next_Bidder()
        else:
            raise Exception("Not in bidding round.")

    def Get_info_on_BRound(self) -> tuple[int,PowerStationC,PlayerC]:
        """gets the information for current bidding round

        Raises:
            Exception: if not in bidding round

        Returns:
            tuple[int,PowerStationC,PlayerC]: current minimum bid, powerstation being bid on, player who currently holds the bid
        """ 
        if self._In_BRound:
            current_bid,station,player = self._BRound.Get_Current_Bid() 
            min_bid = current_bid + 1
            return min_bid, station, player
        else:
            raise Exception("Not in bidding round.")

    def Get_Next_Bidder(self) -> PlayerC|Literal[False]:
        """Gets the next bidder to start a bidding round

        Raises:
            Exception: if in bidding round

        Returns:
            PlayerC|Literal[False]: The name of the next player to bid, or False if no players left to bid
        """
        if not self._In_BRound and not self._Waiting_for_discard_player:
            try:
                return self._Players_to_buy[0]
            except IndexError:
                return False
        raise Exception("In bidding round.")

    def Select_Station_For_Auction(self,station:PowerStationC,player:PlayerC) -> bool:
        """Starts a bidding round on the selected station

        Args:
            station (PowerStationC): Powerstation to bid on, must be in available market
            player (PlayerC): The player who is selecting the station for auction

        Returns:
            bool: True if the auction was successfully started, False otherwise
        """
        if player == self._Players_to_buy[0] and station in self._PS_Market.GiveMarket()[0] and not self._In_BRound and not self._Waiting_for_discard_player:
            
            if self._PS_Market.GiveMarket()[0][0] == station and self._Discount:
                bid = 1
                self._Discount = False
            else:
                bid = station.GetValue()
            if player.CheckEnoughElectros(bid):
                if self._Players_to_buy == [player]:
                    
                    #Only player left to buy station, buys at min price
                    self._PS_Market.BuyPowerStation(station)
                    player.BuyPowerstation(station,bid)
                    self._Players_to_buy.remove(player)
                    return True
                self._BRound = BiddingRound(station,self._Players_to_buy,player,bid)
                self._In_BRound = True
                return True
        
        return False



    def Receive_Bid(self,player:PlayerC,cost:int) -> bool:
        """Receives a bid from a player in the bidding round and processes it

        Args:
            player (PlayerC): The player who is placing the bid
            cost (int): The amount of the bid

        Raises:
            Exception: If not in bidding round
        Returns:
            bool: True if the bid was successfully placed, False otherwise
        """
        if self._In_BRound:
            return self._BRound.Place_Bid(player,cost)
        raise Exception("Not in bidding round.")

    def Receive_Resign(self,player:PlayerC) -> tuple[PlayerC|Literal[False],int,PowerStationC|Literal[False],bool]:
        """Removes a player from the bidding round if in a bidding round or removes a player from the auction, meaning they cannot buy a powerstation this round

        Args:
            player (PlayerC): player to resign

        Raises:
            Exception: if not in bidding round and the player is not the next to buy

        Returns:
            tuple[PlayerC|Literal[False],int,PowerStationC|Literal[False],bool]: Winner of bidding round or False, winning bid, powerstation won or False, needs to discard bool
        """
        if self._In_BRound:
            self._BRound.Resign_from_bidding(player)

            if self._BRound.Bidding_Over():
                winner = self._BRound.Get_Winner()
                station = self._BRound.GetStation()
                winning_bid = self._BRound.Get_Winning_Bid()
                self._In_BRound = False
                self._Players_to_buy.remove(winner)
                self._PS_Market.BuyPowerStation(station)

                needs_to_discard = winner.BuyPowerstation(station,winning_bid)
                if needs_to_discard:
                    self._In_BRound = True
                    self._Waiting_for_discard_player = winner
                    
                return winner, winning_bid, station, needs_to_discard
            return False,0, self._BRound.GetStation() ,False
        
        if not self._In_BRound and player == self._Players_to_buy[0]:
            self._Players_to_buy.remove(player)
            return False,0, False , False
        raise Exception("Not in bidding round.")
    
    def Discard_PowerStation(self,player:PlayerC,station:PowerStationC) -> bool:
        """Discards the selected power station for the player specified 

        Args:
            player (PlayerC): player who needs to dsicard power station
            station (PowerStationC): station they have chosen to discard

        Returns:
            bool: True if the power station was successfully discarded, False otherwise
        """
        player.RemovePowerStation(station)
        self._Waiting_for_discard_player = None
        self._In_BRound = False
        player.BuyPowerstation(self._BRound.GetStation(),self._BRound.Get_Winning_Bid())
        return True
    
    def Get_Players_to_buy(self) -> List[PlayerC]:
        """Returns a list of the players left to buy in auction

        Returns:
            List[PlayerC]: list of players left to buy in auction
        """
        return self._Players_to_buy
    
    def Used_Discount(self)-> bool:
        """returns true if discount has been used, false otherwise

        Returns:
            bool: true if discount has been used, false otherwise
        """
        return not self._Discount

    def Finish_Auction(self) -> bool:
        """Finishes the auction if no players left to buy, marks end of phase 2

        Returns:
            bool: true if auction is finished, false otherwise
        """
        if self._Players_to_buy == []:
            return True
        else:
            return False
        
class Phase2StartingRound(Phase2):
    """The starting auction of the game with specific requirements, such as player must buy a powerstation

    Args:
        Phase2 (class): holds phase 2 logic
    """
    def __init__(self,PS_Market:PS_Market,players:List[PlayerC],stage:int):
        """Initialises phase 2 starting round

        Args:
            PS_Market (PS_Market): power station market for the game
            players (List[PlayerC]): list of players in the game
            stage (int): current stage of the game
        """
        super().__init__(PS_Market,players,stage)

    def Receive_Resign(self,player:PlayerC) -> tuple[PlayerC|Literal[False],int,PowerStationC|Literal[False],bool]:
        """Removes a player fmor a bidding round, if not in bidding round raises error 

        Args:
            player (PlayerC): player to resign

        Raises:
            Exception: raised if not in bidding round
            Exception: raised if player tries to resign when not their turn

        Returns:
            tuple[PlayerC|Literal[False],int,PowerStationC|Literal[False],bool]: tuple containing the winner or False if no winner, winning bid, power station, and whether a discard is needed
        """
        if self._In_BRound:
            self._BRound.Resign_from_bidding(player)
            if self._BRound.Bidding_Over():
                winner = self._BRound.Get_Winner()
                station = self._BRound.GetStation()
                winning_bid = self._BRound.Get_Winning_Bid()
                self._In_BRound = False
                self._Players_to_buy.remove(winner)
                self._PS_Market.BuyPowerStation(station)
                winner.BuyPowerstation(station,winning_bid)
                return winner, winning_bid, station, False
            return False,0, self._BRound.GetStation(),False
        
        if not self._In_BRound and player == self._Players_to_buy[0]:
            raise Exception("In starting round,players must buy a power station.")
        raise Exception("Not in bidding round.")
    
    def Finish_Auction(self):
        """Marks the end of Phase 2, completes phase 1 sorting as this is required in first round.

        Returns:
            bool: true if auction is finished, false otherwise
        """
        if self._Players_to_buy:
            return False
        else:
            Phase1.Determine_Player_Order(self._Players)
            return True
    
class BiddingRound:
    def __init__(self,Station:PowerStationC,Players:List[PlayerC],StartingPLayer:PlayerC,starting_bid:int):
        """Initialises a bidding round

        Args:
            Station (PowerStationC): power station being bid on
            Players (List[PlayerC]): list of players participating in the bidding round
            StartingPLayer (PlayerC): player who starts the bidding
            starting_bid (int): starting bid for the power station
        """
        self.__station = Station
        self.__players = Players
        self.__starting_player = StartingPLayer
        self.__players_left = list(Players)
        self.__current_bidder_index = self.__players.index(StartingPLayer)
        self.__current_bid = starting_bid
        self.__next_bidder_index = (self.__current_bidder_index +1) % len(self.__players_left)
    
    def Get_Next_Bidder(self) -> PlayerC:
        """Give the next bidder in a bidding round

        Returns:
            PlayerC: the next bidder in the bidding round
        """
        return self.__players_left[self.__next_bidder_index]
        
    
    def Get_Current_Bid(self) -> tuple[int,PowerStationC,PlayerC]:
        """Get the current highest bid, the power station being bid on, and the current highest bidder

        Returns:
            tuple[int,PowerStationC,PlayerC]: current bid amount, power station, and player with the highest bid
        """
        return (self.__current_bid, self.__station, self.__players_left[self.__current_bidder_index])
    
    def Place_Bid(self,player:PlayerC,bid:int) -> bool:
        """Places a bid for the player specfied of amount specified, if player is next and bid amount is valid

        Args:
            player (PlayerC): player placing the bid
            bid (int): amount of the bid

        Raises:
            Exception: raised if bid is invalid or not player's turn to bid
        Returns:
            bool: true if bid is successfully placed, false otherwise
        """
        if player == self.Get_Next_Bidder() and bid > self.__current_bid and player.CheckEnoughElectros(bid):
            self.__current_bid = bid
            self.__current_bidder_index = self.__players_left.index(player)
            self.__next_bidder_index = (self.__current_bidder_index +1) % len(self.__players_left)
            return True
        raise Exception("Invalid bid or not this player's turn to bid.")
    
    def Resign_from_bidding(self,player:PlayerC):
        """Removes a player from the bidding round if they are the next bidder

        Args:
            player (PlayerC): 

        Raises:
            Exception: _description_
        """
        current_bidder = self.__players_left[self.__current_bidder_index]
        if player == self.Get_Next_Bidder():
            self.__players_left.remove(player)
            self.__current_bidder_index = self.__players_left.index(current_bidder)
            self.__next_bidder_index = (self.__current_bidder_index +1) % len(self.__players_left)
        else:
            raise Exception("It's not this player's turn to resign from bidding.")
    
    def Bidding_Over(self) -> bool:
        """Returns True if bidding is over otherwise false

        Returns:
            bool: True if bidding is over, False otherwise
        """
        if len(self.__players_left) == 1:
            return True
        return False
    
    def Get_Winner(self) -> PlayerC:
        """Gets the player class of the winning player if bidding is over=

        Raises:
            Exception: if bidding is not over yet

        Returns:
            PlayerC: the winning player
        """
        if self.Bidding_Over():
            return self.__players_left[0]
        raise Exception("Bidding is not over yet.")
    
    def Get_Winning_Bid(self) -> int:
        """Gives the winning bid

        Raises:
            Exception: if bidding is not over yet

        Returns:
            int: the winning bid
        """
        if self.Bidding_Over():
            return self.__current_bid
        raise Exception("Bidding is not over yet.")
    
    def Get_Starting_Player(self) -> PlayerC:
        """Gets the player who started the bidding round

        Returns:
            PlayerC: the starting player
        """
        return self.__starting_player
    
    def GetStation(self) -> PowerStationC:
        """Gives the station teh bidding round is on

        Returns:
            PowerStationC: the power station the bidding round is on
        """
        return self.__station
    

class Phase3:
    """Holds pahse 3 logic
    """

    def __init__(self,Resource_Market:R_Market,Players:List[PlayerC]):
        """Initialises phase 3

        Args:
            Resource_Market (R_Market): the resource market for phase 3
            Players (List[PlayerC]): the list of players in phase 3
        """
        self.__Resource_Market = Resource_Market
        self.__Players = Players
        self.__Players_to_buy = list(Players)

    def Get_Players_to_buy(self) -> list[PlayerC]:
        """Gives the players left to buy resources=

        Returns:
            list[PlayerC]: the players left to buy resources
        """
        return self.__Players_to_buy
    
    def Get_Resource_Costs(self) -> dict[str, list[int]]:
        """Gets the costs of resources in the market

        Returns:
            dict[str, list[int]]: the costs of resources in the market
        """
        return {
            'C': self.__Resource_Market.GetCostOfCoal(),
            'O': self.__Resource_Market.GetCostOfOil(),
            'G': self.__Resource_Market.GetCostOfGarbage(),
            'N': self.__Resource_Market.GetCostOfNuclear()
        }
    
    def Buy_Resources(self,player:PlayerC,ResourceType:str,amount:int) -> bool:
        """Allows a player to buy resources

        Args:
            player (PlayerC): the player buying resources
            ResourceType (str): the type of resource to buy
            amount (int): the amount of the resource to buy

        Returns:
            bool: True if the purchase was successful, False otherwise
        """
        if player == self.__Players_to_buy[0] and player.CheckEnoughElectros(self.Get_Resource_Costs()[ResourceType][amount-1]) and player.HasResourceSpace(ResourceType,amount):
            
            cost = self.__Resource_Market.Buy_Resource(ResourceType,amount)
            player.BuyResource(cost,ResourceType,amount)
            return True
        else:
            return False
        
    def Player_Finished_Buying(self,player:PlayerC) -> bool:
        """Allows a player to stop buying resources

        Args:
            player (PlayerC): the player who has finished buying resources

        Raises:
            Exception: if it's not the player's turn to finish buying

        Returns:
            bool: True if the player successfully finished buying, False otherwise
        """
        if player == self.__Players_to_buy[0]:
            self.__Players_to_buy.remove(player)
            return True
        else:
            raise Exception("It's not this player's turn to finish buying.")

    def Finish_Resource_Buying(self) -> bool:
        """Returns True if all players have finished buying resources

        Returns:
            bool: True if all players have finished buying resources, False otherwise
        """
        if self.__Players_to_buy:
            return False
        return True
    

class Phase4:
    """holds phase 4 logic 
    """
    def __init__(self,players:List[PlayerC],board:BoardC):
        """Initialises phase 4

        Args:
            players (List[PlayerC]): the list of players in phase 4
            board (BoardC): the game board
        """
        self.__players = list(players)
        self.__players_to_buy = list(players)
        self.__board = board

    def Get_Players(self) -> List[PlayerC]:
        """Gets the players left to buy cities in order

        Returns:
            List[PlayerC]: the players left to buy cities in order
        """
        return self.__players_to_buy
    
    def Get_Costs(self) -> dict[str,int|float]:
        """Gets the costs of cities for the current player to buy

        Returns:
            dict[str,int|float]: the costs of cities for the current player to buy
        """
        player = self.__players_to_buy[0]
        costs = {}
        for city_id in self.__board.city_ids:
            cost = self.__board.DjkstrasSearch(player.GetSourceCity(), city_id,player.GetName())
            if self.__board.cityIds_to_CityClass[city_id].CityIsAvailableToPlayer(player.GetName()):
                cost += self.__board.cityIds_to_CityClass[city_id].GetCostInCity()
                costs[city_id] = cost
            else:
                costs[city_id] = math.inf
        return costs
    
    def Player_Finished_Buying(self,player:PlayerC) -> bool:
        """Lets a player finish buying citie s

        Args:
            player (PlayerC): the player who has finished buying cities

        Raises:
            Exception: if it's not the player's turn to finish buying

        Returns:
            bool: True if the player successfully finished buying, False otherwise
        """
        if player == self.__players_to_buy[0]:
            self.__players_to_buy.remove(player)
            return True
        else:
            raise Exception("It's not this player's turn to finish buying.")
        
    def Player_Buy_City(self,city_id:str):
        """Buys a city a player if they can

        Args:
            city_id (str): the ID of the city to buy

        Returns:
            bool: True if the city was successfully bought, False otherwise
        """
        if city_id not in self.__board.city_ids:
            return False
        player = self.__players_to_buy[0]
        cost = self.__board.DjkstrasSearch(player.GetSourceCity(),city_id,player.GetName())
        if self.__board.cityIds_to_CityClass[city_id].CityIsAvailableToPlayer(player.GetName()):
            cost += self.__board.cityIds_to_CityClass[city_id].GetCostInCity()
            if player.CheckEnoughElectros(cost):
                self.__board.cityIds_to_CityClass[city_id].PlayerBuyCity(player.GetName())
                player.BuyCity(city_id,int(cost))
                return True
        return False

    def Finshed_city_buying(self) -> bool:
        """Marks the end of phase 4, returns true if all players have finished buying cities

        Returns:
            bool: True if all players have finished buying cities, False otherwise
        """
        if self.__players_to_buy:
            return False
        return True
    
                
                

class Phase5:
    """holds phase 5 logic
    """
    def __init__(self,Players:List[PlayerC],ResourceMarket:R_Market,PowerStationMarket:PS_Market,Board:BoardC,Stage:int,Used_Discount:bool):
        """Phase 5 initialisation

        Args:
            Players (List[PlayerC]): a list of players in the game
            ResourceMarket (R_Market): the resource market
            PowerStationMarket (PS_Market): the power station market
            Board (BoardC): the game board
            Stage (int): the current stage of the game
            Used_Discount (bool): whether a discount was used in phase 2
        """
        self.__Players = list(Players)
        self.__ResourceMarket = ResourceMarket
        self.__PowerStationMarket = PowerStationMarket
        self.__Board = Board
        self.__Stage = Stage
        self.__Players_left_to_do_bureaucracy: List[PlayerC] = list(Players)
        self.__Players_Powered_dict = {player:0 for player in Players}
        self.Restock_Resources()
        if not Used_Discount and self.__Stage < 3:
            # Removes the discounted powerstation from the market is not used
            self.__PowerStationMarket.RemoveDiscountedPowerStation()
            
        
        
    def Restock_Resources(self):
        """Restocks the resources market according to Power Grid rules
        """
        ResourceAmountResupply = {
            3: [{'C':4, 'O':2, 'G':1, 'N':1}, {'C':5, 'O':3, 'G':2, 'N':1}, {'C':3, 'O':4, 'G':3, 'N':1}],
            4: [{'C':5, 'O':3, 'G':2, 'N':1}, {'C':6, 'O':4, 'G':3, 'N':2}, {'C':4, 'O':5, 'G':4, 'N':2}],
            5: [{'C':5, 'O':4, 'G':3, 'N':2}, {'C':7, 'O':5, 'G':3, 'N':3}, {'C':5, 'O':6, 'G':5, 'N':2}],
            6: [{'C':7, 'O':5, 'G':3, 'N':2}, {'C':9, 'O':6, 'G':5, 'N':3}, {'C':6, 'O':7, 'G':6, 'N':3}]
        }
        self.__NofPlayers = len(self.__Players)
        for resource in ['C','O','G','N']:
            self.__ResourceMarket.Add_Resource(resource, ResourceAmountResupply[self.__NofPlayers][self.__Stage-1][resource])
        
    def GetInfoForBureaucracy(self) -> tuple[PlayerC|Literal[False],int,int,List[PowerStationC],dict[str,int]]:
        """Gives infomration for bureacary 

        Returns:
            tuple[PlayerC|Literal[False],int,int,List[PowerStationC],dict[str,int]]: player class of next player to do bureaucracy or False, their electros, number of cities, list of powerstations, resources dict
        """
        if not self.__Players_left_to_do_bureaucracy:
            return (False,0,0,[],{})
        else:
            player = self.__Players_left_to_do_bureaucracy[0]
            return (player, player.GetElectros(),len(player.GetCities() ),player.GetPowerStations(), player.GetResources())

    def Player_Do_Bureaucracy(self,player:PlayerC,Stations_Powered_resources_Dict:dict[PowerStationC,dict[str,int]]) -> int:
        """Completes bureaucracy for a player

        Args:
            player (PlayerC): the player doing bureaucracy
            Stations_Powered_resources_Dict (dict[PowerStationC,dict[str,int]]): the planned powering of stations with resources

        Raises:
            Exception: if the player tries to power a station they do not own
            Exception: if the player does not have enough resources for the plan
            Exception: if the plan does not work due to insufficient fuel
            Exception: if it is not the player's turn to do bureaucracy

        Returns:
            int: the total number of cities powered by the player
        """
        if player == self.__Players_left_to_do_bureaucracy[0]:
            stations = player.GetPowerStations()
            # 1. Validate Ownership
            if not set(Stations_Powered_resources_Dict.keys()).issubset(set(stations)):
                 raise Exception("Player tried to power a station they do not own.")

            # 2. Validate Resources
            if not self.Check_Player_has_resources_for_planned_powering(player, Stations_Powered_resources_Dict):
                 print(Stations_Powered_resources_Dict)
                 print(player.GetResources())
                 print(player.GetElectros())
                 raise Exception("Player does not have enough resources for this plan.")
            plan_works = True
            total_cities_powered = 0
            for station in Stations_Powered_resources_Dict.keys():
                if sum(Stations_Powered_resources_Dict[station].values()) == 0 and station.GetFuelAmount() > 0:
                    cities_powered = 0 # Chooses not to power this station
                elif station.CheckSuffficentFuel(Stations_Powered_resources_Dict[station]):
                    cities_powered = station.GetNumberOfCitiesPowered()
                else:
                    plan_works = False
                total_cities_powered += cities_powered
            if plan_works:
                self.Correct_resources_used_in_planned_powering(player,Stations_Powered_resources_Dict)
                total_cities_powered = min(total_cities_powered, len(player.GetCities()))
                player.Pay(self.Pay_formulae(total_cities_powered))
                self.__Players_left_to_do_bureaucracy.remove(player)
                self.__Players_Powered_dict[player] = total_cities_powered
                return total_cities_powered
            else:
                raise Exception("Player does not have enough resources to power the selected stations.")
        else:
            raise Exception("It's not this player's turn to do bureaucracy.")
    
    def Correct_resources_used_in_planned_powering(self,player:PlayerC,Stations_Powered_resources_Dict:dict[PowerStationC,dict[str,int]])-> bool:
        """Uses up the resources for the planned powering

        Args:
            player (PlayerC): the player doing bureaucracy
            Stations_Powered_resources_Dict (dict[PowerStationC,dict[str,int]]): the planned powering of stations with resources

        Returns:
            bool: True if resources were successfully used, False otherwise
        """
        players_resources = player.GetResources()
        for station, fuel_dict in Stations_Powered_resources_Dict.items():
            for fueltype, amount in fuel_dict.items():
                if fueltype in station.GetFuelOptions() and amount <= players_resources[fueltype]:
                    player.UseResources(fueltype, amount)
        return True
    
    def Check_Player_has_resources_for_planned_powering(self,player:PlayerC,Stations_Powered_resources_Dict:dict[PowerStationC,dict[str,int]])-> bool:
        """Check the player has the reosurces for what they planned

        Args:
            player (PlayerC): the player doing bureaucracy
            Stations_Powered_resources_Dict (dict[PowerStationC,dict[str,int]]): the planned powering of the powerstations

        Returns:
            bool: True if the player has enough resources for the planned powering, False otherwise
        """
        players_resources = player.GetResources()
        fuel_wanted = {'C':0,'O':0,'G':0,'N':0}
        for station, fuel_dict in Stations_Powered_resources_Dict.items():
            required_amount = station.GetFuelAmount()
            for fueltype, amount in fuel_dict.items():
                fuel_wanted[fueltype] += amount
        for fueltype, amount in fuel_wanted.items():
            if amount > players_resources[fueltype]:
                return False
        return True

    def Pay_formulae(self,number_of_cities:int) -> int:
        """Calculates the payment a player must make based on number of cities powered 
        uses the formula: 10 + 12 * number_of_cities - int(number_of_cities ** 2 / 4)

        Args:
            number_of_cities (int): the total number of cities powered by the player

        Returns:
            int: the payment amount the player must make
        """
        return 10 + 12 * number_of_cities - int(number_of_cities ** 2 / 4)



    def CheckStageChangeAndWin(self)->tuple[PlayerC|None, int]:
        """Check wheter there is a stage change or if someone has won

        Raises:
            Exception: Raised if not all players have completed bureaucracy.

        Returns:
            tuple[PlayerC|None, int]: The player who won and the current stage, or None and the current stage if no winner.
        """
        if self.__Players_left_to_do_bureaucracy:
            raise Exception("Not all players have completed bureaucracy.")
        
        stage2ReqsNoPlayers = {3:7,4:7,5:7,6:6}
        winCondition = {3:17,4:17,5:15,6:14}
        #stage 2 check
        if self.__Stage == 1:
            for player in self.__Players:
                if len(player.GetCities()) >= stage2ReqsNoPlayers[len(self.__Players)]:
                    self.__Stage = 2
                    self.__PowerStationMarket.Stage2()
                    self.__Board.ChangeStage(self.__Stage)
        #stage 3 check
        if self.__Stage != 3:
            if self.__PowerStationMarket.Stage3():
                self.__Stage = 3
                self.__Board.ChangeStage(self.__Stage)
        self.__Players.sort()
        #win check
        if len(self.__Players[0].GetCities()) >= winCondition[len(self.__Players)]:
            highest_score = 0
            highest_player:list[PlayerC] = []
            for player in self.__Players:
                if self.__Players_Powered_dict[player] > highest_score:
                    highest_score = self.__Players_Powered_dict[player]
                    highest_player = [player]
                elif self.__Players_Powered_dict[player] == highest_score:
                    highest_player.append(player)
            if len(highest_player) == 1:
                return highest_player[0],self.__Stage
            # If there's a tie, we need to check who has the most money
            if len(highest_player) > 1:
                Most_Money = 0
                Player_With_most_money:PlayerC
                for player in highest_player:
                    Electros = player.GetElectros()
                    if Electros > Most_Money:
                        Player_With_most_money = player
                        Most_Money = Electros
                        #player with most money win
                return Player_With_most_money,self.__Stage
        return None, self.__Stage


