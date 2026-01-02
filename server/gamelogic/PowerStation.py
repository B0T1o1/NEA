
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

    def station_to_str(self) -> str:
        # Works for both PowerStationC and Stage3
        return (
            f"Value={self.GetValue()}, "
            f"FuelType={self.GetFuelType()} ({getattr(self, 'GetFuelWord', lambda: self.GetFuelType())()}), "
            f"FuelAmount={self.GetFuelAmount()}, "
            f"CitiesPowered={self.GetNumberOfCitiesPowered()}"
        )
    
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

    def CheckSuffficentFuel(self, fuel_dict:dict[str,int]) -> bool:
        """
        Checks if the provided fuel dictionary has sufficient fuel for this power station.
        Args:
            fuel_dict (dict[str, int]): A dictionary mapping fuel types ('C', 'O', 'G', 'N') to their available amounts.
        Returns:
            bool: True if there is sufficient fuel, False otherwise.
        """
        required_amount = self.GetFuelAmount()
        fuel_options = self.GetFuelOptions()
        
        if not fuel_options:  # Renewable station
            return True
        
        total_available = sum(fuel_dict.get(fuel_type, 0) for fuel_type in fuel_options)
        return total_available >= required_amount