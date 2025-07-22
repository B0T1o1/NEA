from PowerStation import PowerStationC

class PlayerC:
    def __init__(self,Electros:int,name):
        self.__Electros = Electros
        self.__PowerStations: list[PowerStationC] = []
        self.__cities: list[str] = []
        self.__name = name
        self.__Resources =  { 'C':0, 'O':0, 'H':0, 'G':0, 'N':0, 'R':0}


    def GetPowerStations(self) -> list:
        self.__PowerStations.sort()
        return self.__PowerStations
    
    def GetResourceSpace(self) -> dict:
        available =  { 'C':0, 'O':0, 'H':0, 'G':0, 'N':0, 'R':0}
        for PowerStation in self.__PowerStations:
            available[PowerStation.GetFuelType()] += PowerStation.GetFuelAmount() * 2
        for type in  ['C','O','H','G','N','R']:
            available[type] -=  self.__Resources[type]
        return available

    def addResource(self,cost):
        pass

    
    def GetName(self) -> str:
        return self.__name

    def GetElectros(self) -> int:
        return self.__Electros
    
    def CheckEnoughElectros(self,Required:int) -> bool:
        return self.__Electros >= Required
    
    def GetCities(self) -> list:
        return self.__cities
    
    def AddPowerstation(self,PowerStation:PowerStationC,cost):
        if len(self.__PowerStations) != 3:
            self.__PowerStations.append(PowerStation)
        self.__Electros -= cost
        return
    

    def __lt__(self,other):
        if not isinstance(other, PlayerC):
            raise TypeError('Can only compare Player objects')
        if len(self.GetCities()) > len(self.GetCities()):
            return False
        if len(self.GetCities()) < len(self.GetCities()):
            return True
        if self.GetPowerStations()[-1].GetValue() <  other.GetPowerStations()[-1].GetValue():
            return True
        if self.GetPowerStations()[-1].GetValue() >  other.GetPowerStations()[-1].GetValue():
            return False

            


if __name__ ==  "__main__":
    p = PowerStationC(3,'O',2,1)
    player = PlayerC(50,"jane")
    player.AddPowerstation(p,3)
    player.add
    print(player.GetResourceSpace())
    


        