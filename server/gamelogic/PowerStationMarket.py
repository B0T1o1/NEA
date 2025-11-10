from .PowerStation import PowerStationC
import json
import random
import math
PLUGGED = 0
UNPLUGGED = 1
class PS_Market:
    def __init__(self,PowerStationsFile,NofPlayers):
        # How many powerplants to remove: {players:(unplugged,plugged)}
        self.__RemovePowerPlants = {3:(2,6),4:(1,3),5:(0,0),6:(0,0)}
        self.__Deck: list[PowerStationC] = []
        self.__PluggedPowerStations,self.__UnpluggedPowerStations = self.ExtractStationsFromFile(PowerStationsFile)
        random.shuffle(self.__PluggedPowerStations)
        self.__PluggedPowerStations = self.RemovePowerStation(NofPlayers,PLUGGED)
        self.__Market:list[PowerStationC] = self.__PluggedPowerStations[:8]
        self.__Market.sort()
        self.__Deck = self.__PluggedPowerStations[8:-1]
        self.__Cover = self.__PluggedPowerStations[-1]
        self.__Deck += self.RemovePowerStation(NofPlayers,UNPLUGGED)
        random.shuffle(self.__Deck)
        self.__Deck.append(self.__Cover)
        self.__Deck.append(Stage3(0,'',0,0))
        self.__stage = 1
 
    def ExtractStationsFromFile(self,PowerStationsFile:str):
        with open(PowerStationsFile,"r") as file:
            JsonStations = json.load(file)
        plugged = []
        unplugged = []
        for station in JsonStations:
            if station["Value"] <= 15:
                plugged.append(PowerStationC(station["Value"],station["FuelType"],station["FuelAmount"],station["NumberOfCitiesPowered"]))
            else:
                unplugged.append(PowerStationC(station["Value"],station["FuelType"],station["FuelAmount"],station["NumberOfCitiesPowered"]))
        return plugged,unplugged
    
    def RemovePowerStation(self,NofPlayers,plugged:int):
            if plugged == 0:
                StationList = self.__PluggedPowerStations
            else:
                StationList = self.__UnpluggedPowerStations

            for i in range(0,self.__RemovePowerPlants[NofPlayers][plugged]):
                StationList.pop(random.randrange(0,len(StationList)))

            return StationList
    
    def GiveMarket(self):
        if self.__stage != 3:
            return self.__Market[:4] , self.__Market[4:]
        else:
            return self.__Market , []
        
    def BuyPowerStation(self,Station:PowerStationC):

        for index, station in enumerate(self.__Market):
            if station.GetValue() == Station.GetValue():
                if self.__stage != 3:
                    if 0 <= index < 4:
                        self.__Market.pop(index)
                        self.__Market.append(self.__Deck.pop(0))
                        self.__Market.sort()
                else:
                    self.__Market.pop(index)
                    self.__Market.append(self.__Deck.pop(0))
                    self.__Market.sort()                
                return Station
            
    def GetDeck(self):
        return self.__Deck

    def RemoveDiscountedPowerStation(self):
        if self.__stage != 3:
            self.__Market.pop(0)
            self.__Market.append(self.__Deck.pop(0))
            self.__Market.sort()
        else:
            raise ValueError("Cannot remove discounted powerstation in stage 3")

    def Stage2(self):
        self.BuyPowerStation(self.GiveMarket()[0][0].GetValue())
        self.__stage = 2
        return

    def Stage3(self) -> bool:
        if self.__Market[-1].GetValue() == math.inf:
            self.__stage = 3
            self.__Market.pop(0)
            self.__Market.pop()

            return True
        return False



class Stage3(PowerStationC):
    def __init__(self, Value, FuelType, FuelAmount, NumberOfCitiesPowered):
        super().__init__(Value, FuelType, FuelAmount, NumberOfCitiesPowered)
        self.__Value = math.inf
        self.__Fuel_To_word = { 'C':'Coal', 'O':'Oil', 'H':'Hybrid', 'G': 'Garbadge', 'N':'Nuclear', 'R':'Renewable','S':'Stage3'}
        self.__FuelType = 'S'
        self.__FuelAmount = math.inf
        self.__NumberOfCitiesPowered = 0

    def GetValue(self) -> int:
        return self.__Value
    def GetFuelType(self) -> str:
        return self.__Fuel_To_word[self.__FuelType]
    def GetFuelAmount(self) -> int:
        return self.__FuelAmount
    def GetNumberOfCitiesPowered(self):
        return self.__NumberOfCitiesPowered


    def __lt__(self,other):
        if not isinstance(other, PowerStationC):
            raise TypeError('Can only compare PowerStation objects')
        return self.__Value < other.__Value
    

if __name__ == "__main__":
    p = PS_Market("stations.JSON",3)
    print(p.GetDeck())