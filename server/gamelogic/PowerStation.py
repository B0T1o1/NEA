
class PowerStationC:
    """Class to represent powerstation=
    """
    def __init__(self,Value:int,FuelType:str,FuelAmount:int,NumberOfCitiesPowered:int):
        """Initalises the POwerstation class

        Args:
            Value (int): Value of powerstation
            FuelType (str): Fueltype of powerstation, must be in ['C','O','H','G','N','R']
            FuelAmount (int): Amount of fuel required to power the station
            NumberOfCitiesPowered (int): Number of cities powered by this station
        """
        self.__Value = Value
        self.__Fuel_To_word = { 'C':'Coal', 'O':'Oil', 'H':'Hybrid', 'G': 'Garbage', 'N':'Nuclear', 'R':'Renewable'}
        self.__FuelType = FuelType
        self.__FuelAmount = FuelAmount
        self.__NumberOfCitiesPowered = NumberOfCitiesPowered

    def GetValue(self) -> int:
        """Returns the value of the power station.

        Returns:
            int: Value of the power station
        """
        return self.__Value
    
    def GetFuelWord(self) -> str:
        """Returns the full name of the fuel type.

        Returns:
            str: Full name of the fuel type
        """
        return self.__Fuel_To_word.get(self.__FuelType)
    
    def GetFuelType(self) -> str:
        """Returns the fuel type abbreviation.

        Returns:
            str: Fuel type abbreviation
        """
        return self.__FuelType
    
    def __repr__(self):
        """Returns a string representation of the power station.

        Returns:
            str: String representation of the power station
        """
        return str(self.__Value) + self.__FuelType + str(self.__NumberOfCitiesPowered)
    
    def GetFuelAmount(self) -> int:
        """Returns the amount of fuel required to power the station.

        Returns:
            int: Amount of fuel required
        """
        return self.__FuelAmount
    def GetNumberOfCitiesPowered(self) -> int:
        """Returns the number of cities the powerstration can power

        Returns:
            int: Number of cities powered
        """
        return self.__NumberOfCitiesPowered

    def station_to_str(self) -> str:
        """Turns station into string format which can easily be sent over network, client and AI have the reverse function

        Returns:
            str: Stringfied dictionary of Value,Fueltype,FuelAmount,CitiesPowedered 
        """
        return (
            f"Value={self.GetValue()}, "
            f"FuelType={self.GetFuelType()} ({self.GetFuelWord()}), "
            f"FuelAmount={self.GetFuelAmount()}, "
            f"CitiesPowered={self.GetNumberOfCitiesPowered()}"
        )
    
    def GetFuelOptions(self) -> list[str]:
        """Returns a list of valid fuel types this station can use.
        - Coal ('C'), Oil ('O'), Garbage ('G'), Nuclear ('N') are single-fuel stations.
        - Hybrid ('H') can use either Coal ('C') or Oil ('O').
        - Renewable ('R') requires no fuel (empty list).

        Returns:
            list[str]: Valid fuel types this station can use
        """
        if self.__FuelType == 'H':
            return ['C', 'O']
        elif self.__FuelType == 'R':
            return []
        else:
            return [self.__FuelType]
        
    def __lt__(self,other) -> bool:
        """Less than comparison operator to allow sorting of stations in powerstation market

        Args:
            other (PowerStationC): Other powerstation to compare against

        Raises:
            TypeError: If the other object is not a PowerStationC instance

        Returns:
            bool: True if this power station's value is less than the other's value, False otherwise
        """
        if not isinstance(other, PowerStationC):
            raise TypeError('Can only compare PowerStation objects')
        return self.__Value < other.GetValue() 

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