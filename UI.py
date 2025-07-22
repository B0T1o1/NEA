from PowerStation import PowerStationC
from Board import BoardC
from Player import PlayerC

class UserInterfaceC:

    def RequestPlayers(self) -> int:
        Valid = False
        while not Valid:
            try:
                Choice = int(input('Please enter the number of players playing:     '))
                Valid = True
            except ValueError:
                print('You didnt not enter an integer, please choose a whole positive number of players:    ')
        return Choice
    
    def DisplayBoard(self,BoardMap:BoardC) -> int:
        return 0

    def SelectMap(self):
        map = input('Please type G for germany map or A for America Map:    ')
        if map == 'G': 
            return 0
        if map == 'A': 
            return 1
        else: 
            return 0

    def GetName(self) -> str:
        Name = input('Please enter the name of a player:    ')
        return Name
    
    def DisplayPlayerOrder(self,Player_names:list[str]):
        print('This is the Player order:    ')
        for place, name in enumerate(Player_names):
            print(f'{place+1}. {name}')

    def GetStartingCity(self,Cities:list[str],Player:str)-> str:
        Choice = ""
        while Choice not in Cities:
            print(f"Which City would {Player} like to start in, the options are:")
            for city in Cities:
                print(city)
            Choice = input("Choice:    ")
            if Choice not in Cities:
                print("that is not a choice, please spell exactly as written")
        print(f"{Player} Have chosen {Choice}")
        return Choice
    
    def RemovePowerStation(self, PowerStations:list[PowerStationC],PlayerName):
        Valid = False
        while not Valid:
            try:
                print(f'{PlayerName} Please choose a Power station to remove:')
                for number, PStation in enumerate(PowerStations):
                    self.DisplayPowerStation(number +1,PStation)
                print('Please input the value of the powerstation you would like to remove:')
                choice = int(input(''))
            except ValueError:
                print('Not valid PowerStation, please try again')
                continue
            else:
                return choice
    
    def DisplayPowerStation(self,Position, PStation:PowerStationC):
        print(f'{Position}. \nValue:{PStation.GetValue()}\nType:{PStation.GetFuelType()}\nNumber of Resource to Power:{PStation.GetFuelAmount()}\nNumber Of Cities Powered:{PStation.GetNumberOfCitiesPowered()}' )

    def DisplayCurrentMarket(self,discount:bool, Stations:list[PowerStationC]):
        print("This is the current market:")
        if discount: print("First Currently has discount")
        for i,station  in enumerate(Stations):
            self.DisplayPowerStation(i+1,station)

    def DisplayFutureMarket(self, Stations:list[PowerStationC]):
            print("This is the future market:")
            for i,station  in enumerate(Stations):
                self.DisplayPowerStation(i+5,station)
        

    def ChooseStationToAuctionFirst(self, market: list[PowerStationC], player_name: str) -> PowerStationC:
        print(f"\n{player_name}, choose a Power Station to auction.")
        valid_ids = [str(station.GetValue()) for station in market]
        
        while True:
            choice = input(f"Enter the Value of the station ({', '.join(valid_ids)}): ")
            if choice in valid_ids:
                for station in market:
                    if str(station.GetValue()) == choice:
                        return station
            print("Invalid ID. Please choose a station from the current market.")

    def GetAuctionBid(self, station: PowerStationC, current_bid: int, high_bidder_name: str, player: PlayerC) -> int | None:
        print(f"\n--- Bidding on Power Station #{station.GetValue()} ---")
        print(f"Current Bid: ${current_bid} (Held by: {high_bidder_name})")
        print(f"{player.GetName()}, you have ${player.GetElectros()}.")

        while True:
            response = input("Enter your bid, or type 'pass': ").lower()
            if response == 'pass':
                print(f"{player.GetName()} passes.")
                return None
            
            try:
                new_bid = int(response)
                if new_bid <= current_bid:
                    print(f"Your bid must be higher than the current bid of ${current_bid}.")
                elif new_bid > player.GetElectros():
                    print(f"You cannot afford this bid. You only have ${player.GetElectros()}.")
                else:
                    return new_bid
            except ValueError:
                print("Invalid input. Please enter a number or 'pass'.")

    def AnnounceAuctionWinner(self, winner_name: str, station_id: int, cost: int):
        print(f"\n🎉 {winner_name} wins Power Station #{station_id} for ${cost}! 🎉")

    def DisplayMessage(self, message: str):
        print(message)
            

            

            



    
    





            