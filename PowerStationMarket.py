from PowerStation import PowerStationC
import json
import random
import math
PLUGGED = 0
UNPLUGGED = 1
class PS_Market:
    def __init__(self,PowerStationsFile,NofPlayers):
        # How many powerplants to remove: {players:(unplugged,unplugged)}
        self.__RemovePowerPlants = {3:(2,6),4:(1,3),5:(0,0),6:(0,0)}
        self.__deck: list[PowerStationC] = []
        self.__PluggedPowerStations,self.__UnpluggedPowerStations = self.ExtractStationsFromFile(PowerStationsFile)
        random.shuffle(self.__PluggedPowerStations)
        self.__deck = self.RemovePowerStation(NofPlayers,PLUGGED)
        




    def ExtractStationsFromFile(self,PowerStationsFile):
        JsonStations = json.load(PowerStationsFile)
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
    


