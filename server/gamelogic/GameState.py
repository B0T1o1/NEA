from .Player import PlayerC
import random
from .Board import BoardC
from .Resource_Market import R_Market
from .PowerStationMarket import PS_Market
from .PowerStation import PowerStationC
from typing import List
import math

class GameStateC:
    def __init__(self):
        self.__stage = 1
        self._Round = 0
        self.Phase = 1
        self.__startingcites = []
        #         self.__players_to_regions = {3:["Brown","Yellow","Red","Purple"],4:["Brown","Green","Yellow","Red","Purple"],5:["Light Blue","Brown","Green","Yellow","Red","Purple"],6:["Light Blue","Brown","Green","Yellow","Red","Purple"]}

    ### SET UP METHODS ###
    def Set_number_of_players(self, n: int):
        if 3 <= n <= 6:
            self.__NofPlayers = n
            return True
        raise ValueError("Number of players must be between 3 and 6.")

    def Set_settings(self,BoardFile = "data/board.JSON",StationFile = "data/stations.JSON", starting_electros = 50,self_regions:List[str]= ["Brown","Yellow","Red","Purple"],map:str='G'):
        self.__PowerStationMarket = PS_Market(StationFile,self.__NofPlayers)
        self.__STARTING_ELECTROS = starting_electros
        self.__ResourceMarket = R_Market()
        self.__regions = self_regions
        self.__Board = BoardC(BoardFile, map,self.__regions)
        #TODO REGIONS
    
    def Set_player_names(self, names: list[str]):
        if len(names) == self.__NofPlayers:
            self.__Players = [PlayerC(self.__STARTING_ELECTROS, name) for name in names]
            self.__PName_to_PClass = {player.GetName(): player for player in self.__Players}
            random.shuffle(self.__Players)
            return True
        return False
    

    def __Set_starting_cities(self, starting_cities: dict[str, str]):
        #Check no two players start in the same city
        list_of_starting_cities = [city for city in starting_cities.values()]
        if len(list_of_starting_cities) != len(set(list_of_starting_cities)):
            raise ValueError("Two players cannot have the same starting city.")
        

        for player_name, city in starting_cities.items():
            player = self.__PName_to_PClass.get(player_name)
            if player:
                player.AddSourceCity(city)
                self.__Board.cityIds_to_CityClass[city].PlayerBuyCity(player_name)
                
            else:
                raise IndexError(f"Player with name {player_name} not found.")
        return True
    
    def Set_starting_cities(self,playername:str,city:str):
        if city in self.__startingcites:
            return False
        else:
            self.__startingcites

    ### Getters ###
    def Get_players(self) -> list[str]:
        return [player.GetName() for player in self.__Players]
    
    def Get_board(self) -> dict:
        return self.__Board.DisplayBoardInfo()
    
    def Get_round(self) -> int:
        return self._Round
    
    def Get_phase(self) -> int:
        return self.Phase
    
    def Get_stage(self) -> int:
        return self.__stage
    


    """Game Logic Methods Below"""
    def Start_Game(self):
        self.__Do_Phase_1_order()
        self.Phase = 2
        return True

    ### Phase 1 Methods ###
    def __Do_Phase_1_start(self):
        if self.Phase == 1:    
            Phase1.Random_Assignment(self.__Players)
            self.Phase = 2
            return True
        raise Exception("Not in Phase 1")

    def __Do_Phase_1_order(self):
        if self.Phase == 1:
            self.__Players = Phase1.Determine_Player_Order(self.__Players)
            self.Phase = 2
            return [player.GetName() for player in self.__Players]
        raise Exception("Not in Phase 1")
    
    ### Phase 2 Methods ###
    def Get_Current_Market(self):
        current_market, future_market = self.__PowerStationMarket.GiveMarket()
        return current_market, future_market
    
    def Start_Auction(self):
        if self.Phase == 2:
            if self.__Round == 0:
                self.Phase2 = Phase2StartingRound(self.__PowerStationMarket,self.__Players)
            else:
                self.Phase2 = Phase2(self.__PowerStationMarket,self.__Players)
            return True
        return False
    
    def Starting_Bid_on_Power_Station(self, player_name: str, station: PowerStationC) -> bool:
        if self.Phase == 2:
            player = self.__PName_to_PClass.get(player_name)
            if player:
                return self.Phase2.Select_Station_For_Auction(player, station)
            raise IndexError(f'Player with name {player_name} not found.')
        raise Exception("Not in Phase 2")
    
    def Place_Bid(self, player_name: str, station: PowerStationC, bid: int) -> bool:
        if self.Phase ==2:
            player = self.__PName_to_PClass.get(player_name)
            if player:
                return self.Phase2.Receive_Bid(player,station,bid)
            raise IndexError(f'Player with name {player_name} not found.')
        raise Exception("Not in Phase 2")
    
    def Resign_From_Bidding(self,player_name:str) -> tuple[str,int]:
        if self.Phase == 2:
            player = self.__PName_to_PClass.get(player_name)
            if player:
                winner, winning_bid = self.Phase2.Receive_Resign(player)
                if winner:
                    return winner.GetName(), winning_bid
                return None, 0
            raise IndexError(f'Player with name {player_name} not found.')
        raise Exception("Not in Phase 2")
    
    def Get_Next_Bidder_in_Round(self) -> str:
        if self.Phase == 2:
            bidder = self.Phase2.Get_Next_Bidder_in_Round()
            return bidder.GetName()
        raise Exception("Not in Phase 2")

    def Get_Next_Bidder(self) -> str:
        if self.Phase == 2:
            bidder = self.Phase2.Get_Next_Bidder()
            return bidder.GetName()
        raise Exception("Not in Phase 2")
    
    def Finish_Auction(self) -> bool:
        if self.Phase2.Finish_Auction() and self.Phase == 2:
            self.Phase = 3
            return True
        raise Exception("Auction not finished yet.")
    

    ### Phase 3 Methods ###
    def Do_Resource_Buying(self):
        if self.Phase == 3:
            self.Phase3 = Phase3(self.__ResourceMarket,self.__Players[::-1])
        raise Exception("Not in Phase 3")
        
    def Get_Resource_Buyers(self) -> list[str]:
        if self.Phase != 3:
            raise Exception("Not in Phase 3")
        return [player.GetName() for player in self.Phase3.Get_Players_to_buy()]
    
    def Buy_Resource(self,player_name:str,ResourceType:str,amount:int):
        if self.Phase != 3:
            raise Exception("Not in Phase 3")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            self.Phase3.Buy_Resources(player,ResourceType,amount)
        else:
            raise IndexError(f'Player with name {player_name} not found.')
        
    def Player_Finished_Buying(self,player_name:str):
        if self.Phase != 3:
            raise Exception("Not in Phase 3")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            self.Phase3.Player_Finished_Buying(player)
        else:
            raise IndexError(f'Player with name {player_name} not found.')
    
    def Finish_Resource_Buying(self):
        if self.Phase != 3:
            raise Exception("Not in Phase 3")
        if self.Phase3.Finish_Resource_Buying():
            self.Phase = 4
            return True
        raise Exception("Not all Players have finished buying resources yet.")

    ### Phase 4 Methdos ###
    def Do_City_Buying(self):
        if self.Phase != 4:
            raise Exception("Not in Phase 4")
        self.Phase4 = Phase4([self.__Players][::-1],self.__Board)
        
    def Get_Players_for_City_Buying(self) -> List[str]:
        if self.Phase != 4:
            raise Exception("Not in Phase 4")
        return [player.GetName() for player in self.Phase4.Get_Players()]

    def Get_City_Costs(self,player_name:str) -> dict[str,int]:
        if self.Phase != 4:
            raise Exception("Not in Phase 4")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return self.Phase4.Get_Costs()
        else:
            raise IndexError(f'Player with name {player_name} not found.')
        
    def Player_Finished_city_buying(self,player_name:str):
        if self.Phase != 4:
            raise Exception("Not in Phase 4")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return self.Phase4.Player_Finished_Buying(player)
        else:
            raise IndexError(f'Player with name {player_name} was not found')
        
    def Player_Buy_City(self,player_name:str,city_id:str):
        if self.Phase != 4:
            raise Exception("Not in Phase 4")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return self.Phase4.Player_Buy_City(city_id)
        else:
            raise IndexError(f'Player with name {player_name} was not found')

    def Finish_City_Buying(self):
        if self.Phase != 4:
            raise Exception("Not in Phase 4")
        return self.Phase4.Finshed_city_buying()
 
    ### Phase 5 Methods ###
    def Do_Bureaucracy(self):
        if self.Phase != 5:
            raise Exception("Not in Phase 5")
        self.Phase5 = Phase5(self.__Players,self.__ResourceMarket,self.__PowerStationMarket)

    def Get_Info_For_Bureaucracy(self):
        if self.Phase != 5:
            raise Exception("Not in Phase 5")

        player,electros, number_of_cities, Powerstations,resources = self.Phase5.GetInfoForBureaucracy()
        return player.GetName() ,electros, number_of_cities, Powerstations,resources
    
    def Player_Do_Bureaucracy(self,player_name:str,Stations_Powered_resources_Dict:dict[PowerStationC,dict[str,int]]):
        if self.Phase != 5:
            raise Exception("Not in Phase 5")
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return self.Phase5.Player_Do_Bureaucracy(player,Stations_Powered_resources_Dict)
        else:
            raise IndexError(f'Player with name {player_name} was not found')
    
    def Check_Stage_Change_And_Win(self):
        if self.Phase != 5:
            raise Exception("Not in Phase 5")
        winner = self.Phase5.CheckStageChangeAndWin()
        if winner:
            return winner.GetName()
        self._Round += 1
        self.Phase = 1
        self.__Do_Phase_1_order()
        self.Phase = 2
        return None
    



        

          




class Phase1:
    @staticmethod
    def Random_Assignment(players):
        random.shuffle(players)
        return players
    @staticmethod

    def Determine_Player_Order(players):
        players.sort()
        return players
    

class Phase2:
    def __init__(self,PS_Market:PS_Market,players:List[PlayerC]):
        self.__PS_Market = PS_Market
        self.__Players = players
        self.__Players_to_buy = list(players)
        self.__Discount = True
        self.__In_BRound = False
        self.__BRound: BiddingRound

    def Get_Next_Bidder_in_Round(self) -> PlayerC:
        if self.__In_BRound:
            return self.__BRound.Get_Next_Bidder()
        else:
            raise Exception("Not in bidding round.")

    def Get_Next_Bidder(self) -> int:
        if not self.__In_BRound:
            return self.__Players_to_buy[0]
        raise Exception("In bidding round.")

    def Select_Station_For_Auction(self,station:PowerStationC,player:PlayerC):
        if player == self.__Players_to_buy[0] and station in self.__PS_Market.GiveMarket()[0] and not self.__In_BRound:
            
            if self.__PS_Market.GiveMarket()[0][0] == station and self.__Discount:
                bid = 1
                self.__Discount = False
            else:
                bid = station.GetValue()
            self.__BRound = BiddingRound(self.__Current_Station,self.__Players_to_buy,player,bid)
            self.__In_BRound = True
            return True
        return False


    def Receive_Bid(self,player:PlayerC,station:PowerStationC,cost:int):
        if self.__In_BRound:
            return self.__BRound.Place_Bid(player,cost)
        raise Exception("Not in bidding round.")

    def Receive_Resign(self,player:PlayerC) -> tuple[PlayerC,int]:
        if self.__In_BRound:
            self.__BRound.Resign_from_bidding(player)

            if self.__BRound.Bidding_Over():
                winner = self.__BRound.Get_Winner()
                winning_bid = self.__BRound.Get_Winning_Bid()
                self.__In_BRound = False
                self.__Players_to_buy.remove(winner)


                self.BuyPowerStation(winner,self.__BRound.GetStation(),winning_bid)
                return winner, winning_bid
            return None,0
        
        if not self.__In_BRound and player == self.__Players_to_buy[0]:
            self.__Players_to_buy.remove(player)
            return None,0
        raise Exception("Not in bidding round.")
    

    
    #Returns list of players still to buy not in bidding round
    def Get_Players_to_buy(self) -> List[PlayerC]:
        return self.__Players_to_buy
    
    def Used_Discount(self)-> bool:
        return not self.__Discount

    def Finish_Auction(self):
        if self.__Players_to_buy == []:
            return True
        else:
            raise Exception("Not all players have resigned their right to buy.")
        
class Phase2StartingRound(Phase2):
    def __init__(self,PS_Market:PS_Market,players:List[PlayerC]):
        super().__init__(PS_Market,players)

    def Receive_Resign(self,player:PlayerC) -> tuple[PlayerC,int]:
        if self.__In_BRound:
            self.__BRound.Resign_from_bidding(player)
            if self.__BRound.Bidding_Over():
                winner = self.__BRound.Get_Winner()
                winning_bid = self.__BRound.Get_Winning_Bid()
                self.__In_BRound = False
                self.__Players_to_buy.remove(winner)


                self.BuyPowerStation(winner,self.__BRound.GetStation(),winning_bid)
                return winner, winning_bid
            return None,0
        
        if not self.__In_BRound and player == self.__Players_to_buy[0]:
            raise Exception("In starting round,players must buy a power station.")
        raise Exception("Not in bidding round.")
    
    def Finish_Auction(self):
        if self.__Players_to_buy:
            return False
        else:
            Phase1.Determine_Player_Order(self.__Players)
            return True
    
class BiddingRound:
    def __init__(self,Station:PowerStationC,Players:List[PlayerC],StartingPLayer:PlayerC,starting_bid:int):
        self.__station = Station
        self.__players = Players
        self.__starting_player = StartingPLayer
        self.__players_left = list(Players)
        self.__current_bidder_index = self.__players.index(StartingPLayer)
        self.__current_bid = starting_bid
    
    def Get_Next_Bidder(self) -> PlayerC:
        if self.__current_bidder_index +1 == len(self.__players_left):
            return self.__players_left[0]
        return self.__players_left[self.__current_bidder_index + 1]
    
    def Get_Current_Bid(self) -> tuple[int,PowerStationC,PlayerC]:
        return (self.__current_bid, self.__station, self.__players_left[self.__current_bidder_index])
    
    def Place_Bid(self,player:PlayerC,bid:int) -> bool:
        if player == self.Get_Next_Bidder() and bid > self.__current_bid and player.CheckEnoughElectros(bid):
            self.__current_bid = bid
            self.__current_bidder_index = self.__players_left.index(player)
            return True
        raise Exception("Invalid bid or not this player's turn to bid.")
    
    def Resign_from_bidding(self,player:PlayerC):
        current_bidder = self.__players_left[self.__current_bidder_index]
        if player == self.Get_Next_Bidder():
            self.__players_left.remove(player)
            self.__current_bidder_index = self.__players_left.index(current_bidder)
        else:
            raise Exception("It's not this player's turn to resign from bidding.")
    
    def Bidding_Over(self) -> bool:
        if len(self.__players_left) == 1:
            return True
        return False
    
    def Get_Winner(self) -> PlayerC:
        if self.Bidding_Over():
            return self.__players_left[0]
        raise Exception("Bidding is not over yet.")
    
    def Get_Winning_Bid(self) -> int:
        if self.Bidding_Over():
            return self.__current_bid
        raise Exception("Bidding is not over yet.")
    
    def Get_Starting_Player(self) -> PlayerC:
        return self.__starting_player
    
    def GetStation(self) -> PowerStationC:
        return self.__station
    

class Phase3:

    def __init__(self,Resource_Market:R_Market,Players:List[PlayerC]):
        self.__Resource_Market = Resource_Market
        self.__Players = Players
        self.__Players_to_buy = list(Players)

    def Get_Players_to_buy(self) -> list[PlayerC]:
        return self.__Players_to_buy
    
    def Get_Resource_Costs(self) -> dict[str, list[int]]:
        return {
            'C': self.__Resource_Market.GetCostOfCoal(),
            'O': self.__Resource_Market.GetCostOfOil(),
            'G': self.__Resource_Market.GetCostOfGarbage(),
            'N': self.__Resource_Market.GetCostOfNuclear()
        }
    
    def Buy_Resources(self,player:PlayerC,ResourceType:str,amount:int):
        if player == self.__Players_to_buy[0] and player.CheckEnoughElectros(self.Get_Resource_Costs()[ResourceType][amount-1]) and player.HasResourceSpace(ResourceType,amount):
            cost = self.__Resource_Market.Buy_Resource(ResourceType,amount)
            player.BuyResource(cost,ResourceType,amount)
        else:
            raise Exception("Player cannot buy resources at this time.")
        
    def Player_Finished_Buying(self,player:PlayerC):
        if player == self.__Players_to_buy[0]:
            self.__Players_to_buy.remove(player)
        else:
            raise Exception("It's not this player's turn to finish buying.")

    def Finish_Resource_Buying(self) -> bool:
        if self.__Players_to_buy:
            return False
        return True
    

class Phase4:
    def __init__(self,players:List[PlayerC],board:BoardC):
        self.__players = list(players)
        self.__players_to_buy = list(players)
        self.__board = board

    def Get_Players(self) -> List[PlayerC]:
        return self.__players_to_buy
    
    def Get_Costs(self) -> dict[str,int]:
        player = self.__players_to_buy[0]
        costs = {}
        for city_id in self.__board.city_ids:
            cost = self.__board.DjkstrasSearch(player.GetSourceCity(), city_id,player.GetName())
            if self.__board.cityIds_to_CityClass[city_id].CityIsAvailable(player.GetName()):
                cost += self.__board.cityIds_to_CityClass[city_id].GetCostInCity()
                costs[city_id] = cost
            else:
                costs[city_id] = math.inf
        return costs
    
    def Player_Finished_Buying(self,player:PlayerC):
        if player == self.__players_to_buy[0]:
            self.__players_to_buy.remove(player)
            return True
        else:
            raise Exception("It's not this player's turn to finish buying.")
        
    def Player_Buy_City(self,city_id:str):
        player = self.__players_to_buy[0]
        cost = self.__board.DjkstrasSearch(player.GetSourceCity(),city_id,player.GetName())
        if self.__board.cityIds_to_CityClass[city_id].CityIsAvailable(player.GetName()):
            cost += self.__board.cityIds_to_CityClass[city_id].GetCostInCity()
            if player.CheckEnoughElectros(cost):
                self.__board.cityIds_to_CityClass[city_id].PlayerBuyCity(player.GetName())
                player.BuyCity(city_id,cost)
                return True
        return False

    def Finshed_city_buying(self) -> bool:
        if self.__players_to_buy:
            return False
        return True
    
                
                

class Phase5:
    def __init__(self,Players:List[PlayerC],ResourceMarket:R_Market,PowerStationMarket:PS_Market,Board:BoardC,Stage:int,Used_Discount:bool):
        self.__Players = list(Players)
        self.__ResourceMarket = ResourceMarket
        self.__PowerStationMarket = PowerStationMarket
        self.__Board = Board
        self.__Stage = Stage
        self.__Players_left_to_do_bureaucracy = list(Players)
        self.__Players_Powered_dict = {player:0 for player in Players}
        self.Restock_Resources()
        if not Used_Discount:
            # Removes the discounted powerstation from the market is not used
            self.__PowerStationMarket.RemoveDiscountedPowerStation()
        
    def Restock_Resources(self):
        ResourceAmountResupply = {
            3: [{'C':4, 'O':2, 'G':1, 'N':1}, {'C':5, 'O':3, 'G':2, 'N':1}, {'C':3, 'O':4, 'G':3, 'N':1}],
            4: [{'C':5, 'O':3, 'G':2, 'N':1}, {'C':6, 'O':4, 'G':3, 'N':2}, {'C':4, 'O':5, 'G':4, 'N':2}],
            5: [{'C':5, 'O':4, 'G':3, 'N':2}, {'C':7, 'O':5, 'G':3, 'N':3}, {'C':5, 'O':6, 'G':5, 'N':2}],
            6: [{'C':7, 'O':5, 'G':3, 'N':2}, {'C':9, 'O':6, 'G':5, 'N':3}, {'C':6, 'O':7, 'G':6, 'N':3}]
        }
        self.__NofPlayers = len(self.__Players)
        for resource in ['C','O','G','N']:
            self.__ResourceMarket.Add_Resource(resource, ResourceAmountResupply[self.__NofPlayers][self.__Stage][resource])
        
    def GetInfoForBureaucracy(self) -> tuple[PlayerC,int,int,List[PowerStationC],dict[str,int]]:
        if not self.__Players_left_to_do_bureaucracy:
            raise Exception("All players have completed bureaucracy.")
        player = self.__Players_left_to_do_bureaucracy[0]
        return (player, player.GetElectros(),len(player.GetCities() ),player.GetPowerStations(), player.GetResources())

    def Player_Do_Bureaucracy(self,player:PlayerC,Stations_Powered_resources_Dict:dict[PowerStationC]):
        if player == self.__Players_left_to_do_bureaucracy[0]:
            stations = player.GetPowerStations()
            if set(Stations_Powered_resources_Dict.keys()).issubset(set(stations)):
                for station in Stations_Powered_resources_Dict.keys():
                    if sum(Stations_Powered_resources_Dict[station].values()) == 0 and station.GetFuelAmount() > 0:
                        result,cities_powered = True,0 # Chooses not to power this station
                    else:
                        result,cities_powered = Phase5.CheckStationsFuel({station:Stations_Powered_resources_Dict[station]},player)
                        if not result:
                            raise Exception("Player does not have enough resources to power the selected stations.")
                    total_cities_powered += cities_powered
                if result:
                    if total_cities_powered >= len(player.GetCities()):
                        total_cities_powered = len(player.GetCities())
                    player.Pay(player.Pay_formulae(total_cities_powered))
                    self.__Players_left_to_do_bureaucracy.remove(player)
                    self.__Players_Powered_dict[player] = total_cities_powered
                    return total_cities_powered
                else:
                    raise Exception("Player does not have enough resources to power the selected stations.")
        else:
            raise Exception("It's not this player's turn to do bureaucracy.")

    def Pay_formulae(self,number_of_cities:int) -> int:
        #Computes the nth term of the sequence:
        #y(n) = 10 + 12n - floor(n^2 / 4)
        return 10 + 12 * number_of_cities - int(number_of_cities ** 2 / 4)


    @staticmethod
    def CheckStationsFuel(Station_fuel:dict[PowerStationC, dict[str, int]],player:PlayerC)-> tuple[int,bool]:
        
        Players_resources = player.GetResources()
        citiesPowered = 0
        for station, fuel_dict in Station_fuel.items():
            required_amount = station.GetFuelAmount()
            for fueltype, amount in fuel_dict.items():
                if fueltype in station.GetFuelOptions() and amount <= Players_resources[fueltype] and required_amount >= amount:
                    Players_resources[fueltype] -= amount
                    required_amount -= amount
                else:
                    return False,0
            if required_amount == 0:
                citiesPowered += station.GetNumberOfCitiesPowered()
        if citiesPowered == 0:
            return True,0
        else:
            player.ChangeResources(Players_resources)
        return True,citiesPowered

    def CheckStageChangeAndWin(self)->PlayerC|None:
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
        if self.__Stage != 3:
            if self.__PowerStationMarket.Stage3():
                self.__Stage = 3
                self.__Board.ChangeStage(self.__Stage)
        self.__Players.sort()
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
                return highest_player[0]
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
                return Player_With_most_money
        return None




