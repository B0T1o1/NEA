
class PowerStationC:
    def __init__(self,Value:int,FuelType:chr,FuelAmount:int,NumberOfCitiesPowered:int):
        self.__Value = Value
        self.__Fuel_To_word = { 'C':'Coal', 'O':'Oil', 'H':'Hybrid', 'G': 'Garbadge', 'N':'Nuclear', 'R':'Renewable'}
        self.__FuelType = FuelType
        self.__FuelAmount = FuelAmount
        self.__NumberOfCitiesPowered = NumberOfCitiesPowered

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