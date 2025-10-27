from Player import PlayerC
import random
from Board import BoardC
from Resource_Market import R_Market
from PowerStationMarket import PS_Market
from PowerStation import PowerStationC
from typing import List
import math

class GameStateC:
    def __init__(self):
        self.__stage = 1
        self._Round = 0
        self.Phase = 1
        #         self.__players_to_regions = {3:["Brown","Yellow","Red","Purple"],4:["Brown","Green","Yellow","Red","Purple"],5:["Light Blue","Brown","Green","Yellow","Red","Purple"],6:["Light Blue","Brown","Green","Yellow","Red","Purple"]}

    def Set_number_of_players(self, n: int):
        if 3 <= n <= 6:
            self.__NofPlayers = n
            return True
        raise ValueError("Number of players must be between 3 and 6.")
    
    def Set_settings(self,BoardFile = "board.JSON",StationFile = "stations.JSON", starting_electros = 40,self_regions:List[str]= None):
        self.__Board = BoardC(BoardFile, map,self.__regions)
        self.__PowerStationMarket = PS_Market(StationFile,self.__NofPlayers)
        self.__STARTING_ELECTROS = 50
        self.__ResourceMarket = R_Market()
        #TODO REGIONS
    def Set_player_names(self, names: list[str]):
        if len(names) == self.__NofPlayers:
            self.__Players = [PlayerC(self.__STARTING_ELECTROS, name) for name in names]
            self.__PName_to_PClass = {player.GetName(): player for player in self.__Players}
            return True
        return False
    
    def Get_board(self) -> BoardC:
        #TODO return a copy / display version
        return self.__Board
    
    def Get_players(self) -> list[PlayerC]:
        return self.__Players
    
    def Set_starting_cities(self, starting_cities: dict[str, str]):
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
    
    def Do_Phase_1_start(self):
        if self.Phase != 1:
            raise Exception("Not in Phase 1")
        Phase1.Random_Assignment(self.__Players)
        return True
    
    def UpdatePhase_1_to_2(self):
        if self.Phase != 1:
            raise Exception("Not in Phase 1")
        self.Phase = 2
        return True

    def Do_Phase_1_order(self):
        self.__Players = Phase1.Determine_Player_Order(self.__Players)
        return [player.GetName() for player in self.__Players]
    
    def Get_Current_Market(self):
        current_market, future_market = self.__PowerStationMarket.GiveMarket()
        return current_market, future_market
    
    def Start_Auction(self):
        if self.__Round == 0:
            self.Phase2 = Phase2StartingRound(self.__PowerStationMarket,self.__Players)
        else:
            self.Phase2 = Phase2(self.__PowerStationMarket,self.__Players)
        return True
    
    def Buy_Power_Station(self, player_name: str, station: PowerStationC, cost:int) -> bool:
        player = self.__PName_to_PClass.get(player_name)
        if player:
            return self.Phase2.BuyPowerStation(player, station, cost)
        return False
    def Finish_Auction(self) -> bool:
        return self.Phase2.Finish_Auction()
    
    def Do_Resource_Buying(self):
        if self.Finish_Auction():
            self.Phase = 3
            self.Phase3 = Phase3(self.__ResourceMarket,self.__Players)
            self.Phase3.ResourceBuying(self.__ResourceMarket,[self.__Players][::-1])
           
        else:
            raise Exception("Auction not finished yet.")
        
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


    def BuyPowerStation(self,player:PlayerC,station:PowerStationC,cost:int):
        if player in self.__Players_to_buy and player.CheckEnoughElectros(cost):
            player.BuyPowerstation(self.__PS_Market.BuyPowerStation(station),cost)
            self.__Players_to_buy.remove(player)
            return True
        return False
    
    def Get_Players_to_buy(self) -> List[PlayerC]:
        return self.__Players_to_buy
    
    def Finish_Auction(self):
        self.__Players_to_buy = []
        return True
        

class Phase2StartingRound(Phase2):
    def __init__(self,PS_Market:PS_Market,players:List[PlayerC]):
        super().__init__(PS_Market,players)

    
    def Finish_Auction(self):
        if self.__Players_to_buy:
            return False
        else:
            Phase1.Determine_Player_Order(self.__Players)
            return True
    


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

    
                
                

class Phase5:
    @staticmethod
    def Bureaucracy(Players:list[PlayerC],UI:UserInterfaceC,ResourceMarket:R_Market,Stage:int,powerplantMarket:PS_Market,Board:BoardC)-> bool:
        Powered = Phase5.PowerStations(Players,UI)
        Phase5.RestockResources(ResourceMarket,Stage,len(Players))
        return Phase5.CheckStageChangeAndWin(Stage,Players,powerplantMarket,Powered,UI,Board)

    @staticmethod
    def PowerStations(Players:list[PlayerC],UI:UserInterfaceC) -> dict[PlayerC,int]:
        Powered = {}
        for player in Players:
            Correct = False
            while not Correct:
                Station_fuel =  UI.choose_power_stations_to_power(player)
                result,CitiesPowered = Phase5.CheckStationsFuel(Station_fuel,player)
                if result:
                    #TODO fix paydict with correct
                    payDict = {0: 10,1: 22, 2: 49,   3: 64,  4: 81,5: 97, 6: 128,    7: 134, 8: 139,    9: 142,10: 145,    11: 148,12: 149,    13: 150}
                    player.Pay(payDict[CitiesPowered])
                    Powered[player] = result
                    Correct = True
        return Powered
            
    @staticmethod
    def CheckStationsFuel(Station_fuel:dict[PowerStationC, dict[str, int]],player:PlayerC)-> (int,bool):
        
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



    @staticmethod
    def RestockResources(ResourceMarket:R_Market,Stage:int,NofPlayers:int):
        ResourceAmountResupply = {
            3: [{'C':4, 'O':2, 'G':1, 'N':1}, {'C':5, 'O':3, 'G':2, 'N':1}, {'C':3, 'O':4, 'G':3, 'N':1}],
            4: [{'C':5, 'O':3, 'G':2, 'N':1}, {'C':6, 'O':4, 'G':3, 'N':2}, {'C':4, 'O':5, 'G':4, 'N':2}],
            5: [{'C':5, 'O':4, 'G':3, 'N':2}, {'C':7, 'O':5, 'G':3, 'N':3}, {'C':5, 'O':6, 'G':5, 'N':2}],
            6: [{'C':7, 'O':5, 'G':3, 'N':2}, {'C':9, 'O':6, 'G':5, 'N':3}, {'C':6, 'O':7, 'G':6, 'N':3}]
        }
        for resource in ['C','O','G','N']:
            ResourceMarket.Add_Resource(resource, ResourceAmountResupply[NofPlayers][Stage][resource])
            
    @staticmethod
    def RestockStations():
        pass
    @staticmethod
    def CheckStageChangeAndWin(CurrentStage:int,players:list[PlayerC],PowerPlantMarket:PS_Market,Powered:dict[PlayerC,int],UI:UserInterfaceC,Board:BoardC)->bool:
        stage2ReqsNoPlayers = {3:7,4:7,5:7,6:6}
        winCondition = {3:17,4:17,5:15,6:14}
        #stage 2 check
        if CurrentStage == 1:
            for player in players:
                if len(player.GetCities()) >= stage2ReqsNoPlayers[len(players)]:
                    CurrentStage = 2
                    PowerPlantMarket.Stage2()
                    Board.ChangeStage(CurrentStage)
        if CurrentStage != 3:
            if PowerPlantMarket.Stage3():
                CurrentStage = 3
                Board.ChangeStage(CurrentStage)
        players.sort()
        if len(players[0].GetCities()) >= winCondition[len(players)]:
            highest_score = 0
            highest_player:list[PlayerC] = []
            for player in players:
                if Powered[player] > highest_score:
                    highest_score = Powered[player]
                    highest_player = [player]
                elif Powered[player] == highest_score:
                    highest_player.append(player)
            if len(highest_player) == 1:
                UI.DisplayMessage(f"{highest_player[0].GetName()} has won")
                exit()
            if len(highest_player) > 1:
                Most_Money = 0
                Player_With_most_money:PlayerC
                for player in highest_player:
                    Electros = player.GetElectros()
                    if Electros > Most_Money:
                        Player_With_most_money = player
                        Most_Money = Electros
            UI.DisplayMessage(UI.DisplayMessage(f"{Player_With_most_money.GetName()} has won"))
            return False
        return True


                    





                    
            
            



if __name__ == '__main__':
    def Phase3Test():
        plays = [PlayerC(50,"Jane"),PlayerC(50,"luca"),PlayerC(50,"Monty")]
        market = PS_Market("stations.JSON",3)
        for player in plays:

            station = market.GiveMarket()[0][0]
            cost = station.GetValue()
            player.BuyPowerstation(market.BuyPowerStation(station),cost)
        
        Phase3.ResourceBuying(R_Market(),plays,UserInterfaceC())
    
    def Phase4Test():
        plays = [PlayerC(50,"Jane"),PlayerC(50,"luca"),PlayerC(50,"Monty")]
        B = BoardC('board.JSON',0,["Brown","Yellow","Red","Purple"])
        Phase4.StartingRound(plays,dict(zip(plays,['mainz','ulm','berlin'])),B)
        Phase4.BuyCities(plays,B,UserInterfaceC())

    def WholeGameTest():
        GameC(UserInterfaceC())
    WholeGameTest()


