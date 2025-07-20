from UI import UserInterfaceC
from PowerStation import PowerStationC

class PlayerC:
    def __init__(self,Electros:int,UI:UserInterfaceC):
        self.__Electros = Electros
        self.__PowerStations: list[PowerStationC] = []
        self.__cities: list[str] = []
        self.__UI = UI
        self.__name = self.__UI.GetName()


    def GetPowerStations(self) -> list:
        self.__PowerStations.sort()
        return self.__PowerStations
    
    def GetName(self) -> str:
        return self.__name

    def GetElectros(self) -> int:
        return self.__Electros
    
    def CheckEnoughElectros(self,Required:int) -> bool:
        return self.__Electros >= Required
    
    def GetCities(self) -> list:
        return self.__cities
    
    def AddPowerstation(self,PowerStation:PowerStationC):
        while len(self.__PowerStations) == 3:
            remove = self.__UI.RemovePowerStation(self.__PowerStations)
            for i,Station in enumerate(self.__PowerStations):
                if remove == Station.GetValue():
                    self.__PowerStations[i] = PowerStation
        if len(self.__PowerStations) != 3:
            self.__PowerStations.append(PowerStation)
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

            



    


        