from PowerStation import PowerStationC

class PlayerC:
    def __init__(self,Electros:int,name):
        self.__Electros = Electros
        self.__PowerStations: list[PowerStationC] = []
        self.__cities: list[str] = []
        self.__name = name
        self.__Resources =  { 'C':0, 'O':0, 'G':0, 'N':0}


    def GetPowerStations(self) -> list:
        self.__PowerStations.sort()
        return self.__PowerStations
    
    def GetResourceSpace(self) -> dict:
        available =  { 'C':0, 'O':0, 'H':0, 'G':0, 'N':0, 'R':0}
        for PowerStation in self.__PowerStations:
            available[PowerStation.GetFuelType()] += PowerStation.GetFuelAmount() * 2
        for type in  ['C','O','G','N']:
            available[type] -=  self.__Resources[type]
        return available
    
    def HasResourceSpace(self,Type,amount:int)-> bool:
        spaces = self.GetResourceSpace()
        space = 0
        if Type == 'O' and self.__Resources['C'] <= spaces['C']:
            space += spaces['H']

        elif Type == 'O':
            space += spaces['H'] - - spaces['C']

        elif Type == 'C' and self.__Resources['O'] <= spaces['O']:
            space += spaces['H']
        elif Type == 'C':
            space += spaces['H']  - spaces['O']
        
        space += spaces[Type]

        if space >= amount:
            return True
        else:
            return False
        
    def GetResources(self):
        return self.__Resources

    def UseResources(self,type:str,amount:int):
        if self.__Resources[type] >= amount:
            self.__Resources[type] -= amount
        else:
            raise ValueError # TODO

    def BuyResource(self,cost:int,resourcetype,resourceamount:int):
        self.__Resources[resourcetype] += resourceamount
        self.__Electros -= cost

    
    def GetName(self) -> str:
        return self.__name

    def GetElectros(self) -> int:
        return self.__Electros
    
    def CheckEnoughElectros(self,Required:int) -> bool:
        return self.__Electros >= Required
    
    def GetCities(self) -> list:
        return self.__cities
    
    def GetSourceCity(self) -> str:
        return self.__sourceCity
    def BuyCity(self,city,cost):
        self.__cities.append(city)
        self.__Electros -=  cost

    def AddSourceCity(self,city):
        self.__sourceCity = city
        self.__cities.append(city)
    
    
    def RemovePowerStation(self,PowerStation:PowerStationC):
        self.__PowerStations.remove(PowerStation)
    
    def BuyPowerstation(self,PowerStation:PowerStationC,cost):
        if len(self.__PowerStations) != 3:
            self.__PowerStations.append(PowerStation)
            self.__Electros -= cost
        else:
            raise ValueError # TODO
    

    def __lt__(self,other):
        if not isinstance(other, PlayerC):
            raise TypeError('Can only compare Player objects')
        if len(self.GetCities()) < len(self.GetCities()):
            return False
        if len(self.GetCities()) > len(self.GetCities()):
            return True
        if self.GetPowerStations()[-1].GetValue() >  other.GetPowerStations()[-1].GetValue():
            return True
        if self.GetPowerStations()[-1].GetValue() <  other.GetPowerStations()[-1].GetValue():
            return False

            


if __name__ ==  "__main__":
    p = PowerStationC(3,'O',2,1)
    player = PlayerC(50,"jane")

    print(player.GetResourceSpace())
    


        