from UI import UserInterfaceC
from Player import PlayerC
import random
from Board import BoardC
from Resource_Market import R_Market
from PowerStationMarket import PS_Market
from PowerStation import PowerStationC


class GameC:
    def __init__(self, UI:UserInterfaceC,BoardFile = "board.JSON",StationFile = "stations.JSON"):
        self.__UI = UI
        self.__STARTING_ELECTROS = 50
        self.__GameSetUp(BoardFile,StationFile)
        self.__StartingRound()



    def __GameSetUp(self,BoardFile,StationFile):
        self.__NofPlayers = self.__UI.RequestPlayers()
        self.__Players:list[PlayerC] = [PlayerC(self.__STARTING_ELECTROS,self.__UI.GetName()) for i in range (0, self.__NofPlayers)]
        self.__Round = 0
        self.__stage = 1
        self.__Players = Phase1.Random_Assignment(self.__Players)
        self.__UI.DisplayPlayerOrder([player.GetName() for player in self.__Players])
        map = self.__UI.SelectMap()


        self.__players_to_regions = {3:["Brown","Yellow","Red","Purple"],4:["Brown","Green","Yellow","Red","Purple"],5:["Light Blue","Brown","Green","Yellow","Red","Purple"],6:["Light Blue","Brown","Green","Yellow","Red","Purple"]}
        self.__regions = self.__players_to_regions[self.__NofPlayers]
        self.__Board = BoardC(BoardFile, map,self.__regions)
        self.__PowerStationMarket = PS_Market(StationFile,self.__NofPlayers)
        self.__ResourceMarket = R_Market()
        self.__UI.DisplayBoard(self.__Board)
        self.__starting_cities = self.ChooseStart()
        

    

    def ChooseStart(self):
        chosen_cities = []
        for player in self.__Players:

            # Create a list of available cities for the current player
            available_cities = [city for city in self.__Board.city_ids if self.__Board.cityIds_to_CityClass[city].CityIsAvailable(player) and city not in chosen_cities]
            
            # Pass the list to the UI method
            chosen_cities.append(self.__UI.GetStartingCity(available_cities,player.GetName()))

        return dict(zip(self.__Players, chosen_cities))
    
    def __StartingRound(self):
        Phase2.Auction(self.__PowerStationMarket,self.__Players,self.__UI,IsFirstRound=True)
        self.__Players = Phase1.Determine_Player_Order(self.__Players)
        self.__UI.DisplayPlayerOrder([player.GetName() for player in self.__Players])
        Phase3.ResourceBuying(self.__ResourceMarket,self.__Players,self.__UI)
        Phase4.StartingRound(self,self.__starting_cities,self.__Board)
        Phase4.BuyCities(self.__Players,self.__Board,self.__UI)
        
            





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
    @staticmethod
    def Auction(PS_Market: PS_Market, players: list[PlayerC], UI: UserInterfaceC,IsFirstRound:bool =False):
        players_to_buy = list(players)
        discount_available = True
        index = 0
        while len(players_to_buy) != 0:
            auction_starter = players[index]
            if auction_starter not in players_to_buy:
                continue

            UI.DisplayMessage(f"\n {auction_starter.GetName()}'s turn to start an auction")
            UI.DisplayPlayerMoney(auction_starter)
            current_market, future_market = PS_Market.GiveMarket()
            
            lowest_station = current_market[0]
            
            UI.DisplayCurrentMarket(discount_available, current_market)
            UI.DisplayFutureMarket(future_market)

            if IsFirstRound:
                station_to_auction = UI.ChooseStationToAuctionFirst(current_market, auction_starter.GetName())
            else:
                station_to_auction = UI.ChooseStationToAuction(current_market, auction_starter.GetName())

            if not IsFirstRound and station_to_auction == -1:
                players_to_buy.remove(auction_starter)
                UI.DisplayMessage(f"{auction_starter.GetName()} has passed and will not participate further in this phase's auctions.")
                continue
            
            will_consume_discount = False

            if discount_available and station_to_auction.GetValue() == lowest_station.GetValue():
                current_bid = 1
                will_consume_discount = True
                UI.DisplayMessage(f"The discount token is being used! The starting bid for Power Station #{station_to_auction.GetValue()} is $1.")
            else:
                current_bid = station_to_auction.GetValue()
                
            high_bidder = auction_starter
            if not will_consume_discount:
                UI.DisplayMessage(f"{auction_starter.GetName()} starts the bidding for Power Station #{station_to_auction.GetValue()} at ${current_bid}.")

            potential_bidders = [p for p in players_to_buy if p != auction_starter]
            potential_bidders.append(auction_starter)
            won = False
            while not won:
                for bidder in list(potential_bidders):
                    if bidder == high_bidder:
                        won = True
                    else:
                        if bidder.CheckEnoughElectros(current_bid):
                            new_bid = UI.GetAuctionBid(station_to_auction, current_bid, high_bidder.GetName(), bidder)

                            if new_bid and new_bid > current_bid:
                                current_bid = new_bid
                                high_bidder = bidder
                                UI.DisplayMessage(f"{bidder.GetName()} is the new high bidder with ${current_bid}!")
                            else:
                                potential_bidders.remove(bidder)

            winner = high_bidder

            UI.AnnounceAuctionWinner(winner.GetName(), station_to_auction.GetValue(), current_bid)
            
            if will_consume_discount:
                discount_available = False
            
            if len(winner.GetPowerStations()) == 3:
                choice = UI.RemovePowerStation(winner.GetPowerStations(),winner.GetName())
                winner.RemovePowerStation(choice)
                winner.BuyPowerstation(station_to_auction,current_bid)

            winner.BuyPowerstation(station_to_auction, current_bid)
            PS_Market.BuyPowerStation(station_to_auction)
            players_to_buy.remove(winner)
            if winner == auction_starter:
                index += 1



class Phase3:
    @staticmethod
    def ResourceBuying(ResourceMarket:R_Market,Players:list[PlayerC],UI:UserInterfaceC):
        for player in reversed(Players):
            passed = False
            while not passed:
                coal,nuclear,garbage,oil =ResourceMarket.GetCostOfCoal(),ResourceMarket.GetCostOfNuclear(),ResourceMarket.GetCostOfGarbage(),ResourceMarket.GetCostOfOil()
                UI.DisplayFuelCosts(coal,nuclear,garbage,oil)
                UI.DisplayPlayerMoney(player)
                UI.DisplayResourceSpace(player)
                cost_of_resources = { 'C':coal, 'O':oil, 'G':garbage, 'N':nuclear}
                Type,amount = UI.GetAmountOfFuelType()
                if amount == 0:
                    passed = True
                    continue
                if Type in ['C','O','G','N']:
                    
                    if player.CheckEnoughElectros(cost_of_resources[Type][amount-1]) and player.HasResourceSpace(Type,amount):
                        cost = ResourceMarket.Buy_Resource(Type,amount)
                        player.BuyResource(cost,Type,amount)
                        UI.PlayerHasBoughtFuel(player.GetName(),amount,cost,Type,player.GetElectros())
                else:
                    pass # TODO
                    
class Phase4:
    @staticmethod
    def StartingRound(players:list[PlayerC],startingCities,Board:BoardC):
        for player,city in startingCities.items():
            if player.CheckEnoughElectros(10):
                player.AddSourceCity(city)
                Board.cityIds_to_CityClass[city].PlayerBuyCity(player.GetName())
                
                
    @staticmethod
    def BuyCities(players:list[PlayerC],board:BoardC,UI:UserInterfaceC):
        for player in reversed(players):
            passed = False
            while not passed:
                UI.DisplayBoard(board)
                costs = [board.DjkstrasSearch(player.GetSourceCity(), city_id,player.GetName()) for city_id in board.city_ids]
                choice_city = UI.GetCity(board.city_ids,costs,player.GetName(),player.GetElectros())
                
                if choice_city:

                    cost_of_choice = board.CheckConnectionCost(player.GetSourceCity(), choice_city)



                    if board.cityIds_to_CityClass[choice_city].CityIsAvailable(player.GetName()):
                        cost_of_choice += board.cityIds_to_CityClass[choice_city].GetCostInCity()
                        if player.CheckEnoughElectros(cost_of_choice):
                            board.cityIds_to_CityClass[choice_city].PlayerBuyCity(player.GetName())
                            player.BuyCity(choice_city,cost_of_choice)
                else:
                    passed = True
                
                

class Phase5:
    @staticmethod
    def Bureaucracy(Players:list[PlayerC],UI:UserInterfaceC,ResourceMarket:R_Market,Stage:int):
        Powered = Phase5.PowerStations(Players,UI)
        Phase5.RestockResources(ResourceMarket,Stage,len(Players))

    @staticmethod
    def PowerStations(Players:list[PlayerC],UI:UserInterfaceC) -> dict[PlayerC,int]:
        Powered = {}
        for player in Players:
            Correct = False
            while not Correct:
                Station_fuel =  UI.choose_power_stations_to_power(player)
                result = Phase5.CheckStationsFuel(Station_fuel,player)
                if result:
                    for station,fuels in Station_fuel.items():
                        for fuel,amount in fuels.items():
                            player.UseResources(fuel,amount)
                    Powered[player] = result
                    Correct = True
        return Powered
            
    @staticmethod
    def CheckStationsFuel(Station_fuel:dict[PowerStationC, dict[str, int]],player:PlayerC)-> int|bool:
        citiesPowered = 0

        for station,fuels in Station_fuel.items():
            required_amount = station.GetFuelAmount()
            required_type = station.GetFuelType()
            if required_type == 'R':
                citiesPowered += station.GetNumberOfCitiesPowered()
            if required_type !=  'H':
                if fuels[required_type] == required_amount and required_amount <= player.GetResources()[required_type]:
                    citiesPowered += station.GetNumberOfCitiesPowered()
                else:
                    return False
            else:
                totalAmount= 0 
                for fuel,amount in fuels.items():
                    if player.GetResources()[fuel] >= amount:
                        totalAmount += amount
                if totalAmount == required_amount:
                    citiesPowered += station.GetNumberOfCitiesPowered()
                else:
                    return False
        return citiesPowered


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
    def CheckStageChangeAndWin():
        pass
            
            



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
    Phase4Test()


