from UI import UserInterface

class PlayerC:
    def __init__(self,Electros:int,UI:UserInterface):
        self.__Electros = Electros
        self.__PowerStations = []
        self.__cities = []
        self.__UI = UI
        self.__name = self.__UI.GetName()

    def GetPowerStations(self) -> list:
        return self.__PowerStations.sort()
    
    def GetName(self) -> str:
        return self.__name

    def GetElectros(self) -> int:
        return self.__Electros
    
    def CheckEnoughElectros(self,Required:int) -> bool:
        return self.__Electros >= Required
    
    def GetCities(self) -> list:
        return self.__cities
    

    def __lt__(self,other):
        if not isinstance(other, PlayerC):
            raise TypeError('Can only compare Player objects')
        if len(self.GetCities()) > len(self.GetCities()):
            return False
        if len(self.GetCities()) < len(self.GetCities()):
            return True
        if self.GetPowerStations()[-1].sort()[-1].GetValue() <  other.GetPowerStations()[-1].GetValue():
            return True
        if self.GetPowerStations()[-1].sort()[-1].GetValue() >  other.GetPowerStations()[-1].GetValue():
            return False

            



    


        