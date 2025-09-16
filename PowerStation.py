
class PowerStationC:
    def __init__(self,Value:int,FuelType:chr,FuelAmount:int,NumberOfCitiesPowered:int):
        self.__Value = Value
        self.__Fuel_To_word = { 'C':'Coal', 'O':'Oil', 'H':'Hybrid', 'G': 'Garbage', 'N':'Nuclear', 'R':'Renewable'}
        self.__FuelType = FuelType
        self.__FuelAmount = FuelAmount
        self.__NumberOfCitiesPowered = NumberOfCitiesPowered

    def GetValue(self) -> int:
        return self.__Value
    
    def GetFuelWord(self) -> str:
        return self.__Fuel_To_word[self.__FuelType]
    
    def GetFuelType(self) -> str:
        return self.__FuelType
    
    def __repr__(self):
        return str(self.__Value) + self.__FuelType + str(self.__NumberOfCitiesPowered)
    
    def GetFuelAmount(self) -> int:
        return self.__FuelAmount
    def GetNumberOfCitiesPowered(self):
        return self.__NumberOfCitiesPowered

    def GetFuelOptions(self) -> list[str]:
        """
        Returns a list of valid fuel types this station can use.
        - Coal ('C'), Oil ('O'), Garbage ('G'), Nuclear ('N') are single-fuel stations.
        - Hybrid ('H') can use either Coal ('C') or Oil ('O').
        - Renewable ('R') requires no fuel (empty list).
        """
        if self.__FuelType == 'H':
            return ['C', 'O']
        elif self.__FuelType == 'R':
            return []
        else:
            return [self.__FuelType]
    def __lt__(self,other):
        if not isinstance(other, PowerStationC):
            raise TypeError('Can only compare PowerStation objects')
        return self.__Value < other.__Value