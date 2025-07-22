from UI import UserInterfaceC
from Player import PlayerC
import random
from Board import BoardC
from Resource_Market import R_Market
from PowerStationMarket import PS_Market

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
        Phase2.First_round(self.__PowerStationMarket,self.__Players,self.__UI)
        self.__Players = Phase1.Determine_Player_Order(self.__Players)
        self.__UI.DisplayPlayerOrder([player.GetName() for player in self.__Players])
        
            





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
    def First_round(PS_Market: PS_Market, players: list[PlayerC], UI: UserInterfaceC):
        #create copy of list to ensure do not edit actual players list
        players_to_buy = list(players)
        discount_available = True

        for auction_starter in players:
            if auction_starter not in players_to_buy:
                continue

            UI.DisplayMessage(f"\n {auction_starter.GetName()}'s turn to start an auction\nThey have {auction_starter.GetElectros()} Electros.")
            current_market, future_market = PS_Market.GiveMarket()
            
            lowest_station = current_market[0]
            
            UI.DisplayCurrentMarket(discount_available, current_market)
            UI.DisplayFutureMarket(future_market)

            station_to_auction = UI.ChooseStationToAuctionFirst(current_market, auction_starter.GetName())

            if not station_to_auction:
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
                UI.RemovePowerStation(winner.GetPowerStations(),winner.GetName())
            winner.AddPowerstation(station_to_auction, current_bid)
            PS_Market.BuyPowerStation(station_to_auction)
            players_to_buy.remove(winner)
            
    @staticmethod
    def AuctionStage12(PS_Market: PS_Market, players: list[PlayerC], UI: UserInterfaceC):
        players_to_buy = list(players)
        discount_available = True

        for auction_starter in players:
            if auction_starter not in players_to_buy:
                continue

            UI.DisplayMessage(f"\n {auction_starter.GetName()}'s turn to start an auction\nThey have {auction_starter.GetElectros()} Electros.")
            current_market, future_market = PS_Market.GiveMarket()
            
            lowest_station = current_market[0]
            
            UI.DisplayCurrentMarket(discount_available, current_market)
            UI.DisplayFutureMarket(future_market)

            station_to_auction = UI.ChooseStationToAuction(current_market, auction_starter.GetName())

            if not station_to_auction:
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
                for bidder in potential_bidders:
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
                UI.RemovePowerStation(winner.GetPowerStations(),winner.GetName())
            winner.AddPowerstation(station_to_auction, current_bid)
            PS_Market.BuyPowerStation(station_to_auction)
            players_to_buy.remove(winner)

class Phase3:
    @staticmethod
    def ResourceBuying(ResourceMarket:R_Market,Players:list[PlayerC],UI:UserInterfaceC):
        UI.DisplayFuelCosts(ResourceMarket.GetCostOfCoal(),ResourceMarket.GetCostOfNuclear(),ResourceMarket.GetCostOfGarbage(),ResourceMarket.GetCostOfOil())
        for player in Players:
            pass
            
        

            

        

if __name__ == '__main__':
    plays = [PlayerC(50,"Jane"),PlayerC(50,"luca"),PlayerC(50,"Monty")]
    market = PS_Market("stations.JSON",3)
    for player in plays:

        station = market.GiveMarket()[0][0]
        cost = station.GetValue()
        player.AddPowerstation(market.BuyPowerStation(station),cost)
    
    Phase3.ResourceBuying(R_Market(),plays,UserInterfaceC())


