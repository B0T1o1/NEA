import copy
from .PowerStation import PowerStationC

class PlayerC:
    """ Class of a player in a game
    """
    INITIAL_COST_SOURCE_CITY = 10
    def __init__(self,Electros:int,name:str):
        """The intialiser for a player

        Args:
            Electros (int): the number of electros the player starts with
            name (str): the name of the player
        """
        self.__Electros = Electros
        self.__PowerStations: list[PowerStationC] = []
        self.__cities: list[str] = []
        self.__name = name
        self.__Resources =  { 'C':0, 'O':0, 'G':0, 'N':0}

    def Pay(self,Electros:int):
        """Pays a player a specified amount of electros

        Args:
            Electros (int): the number of eletros to pay the player
        """
        self.__Electros += Electros

    def GetPowerStations(self) -> list[PowerStationC]:
        """Gives the list of powerstations the player has

        Returns:
            list[PowerStationC]: the list of powerstations the player has
        """
        self.__PowerStations.sort()
        return self.__PowerStations
    
    def GetResourceSpace(self) -> dict[str,int]:
        """Gets the resource space of a player

        Returns:
            dict[str,int]: returns a dictionary of resource types to available space
        """
        available = { 'C':0, 'O':0, 'H':0, 'G':0, 'N':0, 'R':0}
        
        # 1. Calculate total raw capacity based on stations
        for PowerStation in self.__PowerStations:
            available[PowerStation.GetFuelType()] += PowerStation.GetFuelAmount() * 2
            
        # 2. Subtract currently held resources
        for type in ['C','O','G','N']:
            available[type] -= self.__Resources[type]

        # 3. Handle Hybrid Overflow 
        if available['C'] < 0:
            available['H'] += available['C'] 
            available['C'] = 0              

        if available['O'] < 0:
            available['H'] += available['O']
            available['O'] = 0             

        # Ensure H (or G/N if there was an error) never returns a negative number
        for key in available:
            if available[key] < 0:
                available[key] = 0
                
        return available

    def HasResourceSpace(self, Type: str, amount: int) -> bool:
        """Checks that a player has enough resource space for a specified type and amount

        Args:
            Type (str): the resource type
            amount (int): the amount of the resource

        Returns:
            bool: True if there is enough space, False otherwise
        """
        spaces = self.GetResourceSpace()
        
        total_space = spaces.get(Type, 0)
        
        if Type in ['C', 'O']:
            total_space += spaces.get('H', 0)
            
        return total_space >= amount
        
    def GetResources(self) -> dict[str,int]:
        """Returns a copy of the reosurce of a player

        Returns:
            dict[str,int]: a copy of the player's resources
        """
        return copy.deepcopy(self.__Resources)

    def UseResources(self,type:str,amount:int):
        """Uses the resources specified

        Args:
            type (str): the type of resource to use
            amount (int): the amount of the resource to use

        Raises:
            ValueError: if there are not enough resources of the specified type
        """
        if self.__Resources[type] >= amount:
            self.__Resources[type] -= amount
        else:
            raise ValueError ("Not enough resources to use")

    def BuyResource(self,cost:int,resourcetype:str,resourceamount:int):
        """Buys a resource for the player

        Args:
            cost (int): the cost of the resource
            resourcetype (str): the type of resource
            resourceamount (int): the amount of the resource
        """
        self.__Resources[resourcetype] += resourceamount
        self.__Electros -= cost

    
    def GetName(self) -> str:
        """Gives the name of the player

        Returns:
            str: the name of the player
        """
        return self.__name

    def GetElectros(self) -> int:
        """Gives the amount of electros the player has

        Returns:
            int: the amount of electros the player has
        """
        return self.__Electros
    
    def CheckEnoughElectros(self,Required:int|float) -> bool:
        """Checks if the player has enough electros

        Args:
            Required (int|float): the required amount of electros
        Returns:
            bool: True if the player has enough electros, False otherwise
        """
        return self.__Electros >= Required
    
    def GetCities(self) -> list:
        """Gives the list of cities the player has

        Returns:
            list: the list of cities the player has
        """
        return self.__cities
    
    def GetSourceCity(self) -> str:
        """Gives the source city of the player

        Returns:
            str: the source city of the player
        """
        return self.__sourceCity
    
    def BuyCity(self,city:str,cost:int):
        """Buys a city for the player

        Args:
            city (str): the city to buy
            cost (int): the cost of the city
        """
        self.__cities.append(city)
        self.__Electros -=  cost

    def AddSourceCity(self,city:str):
        """Adds the source city of a player

        Args:
            city (str): source city
        """
        self.__Electros -= self.INITIAL_COST_SOURCE_CITY # Initial cost of source city
        self.__sourceCity = city
        self.__cities.append(city)

    def ChangeResources(self,NewResources:dict[str,int]):
        """Changes the resources of the player

        Args:
            NewResources (dict[str,int]): the new resources to set
        """
        self.__Resources = NewResources
    
    def RemovePowerStation(self,PowerStation:PowerStationC):
        """Removes a powerstation from the player

        Args:
            PowerStation (PowerStationC): the powerstation to remove
        """
        self.__PowerStations.remove(PowerStation)
    
    def BuyPowerstation(self,PowerStation:PowerStationC,cost) -> bool:
        """Buys a powerstation for the player

        Args:
            PowerStation (PowerStationC): the powerstation to buy
            cost (int): the cost of the powerstation
        Returns:
            bool: True if the powerstation was bought, False otherwise
        """
        if len(self.__PowerStations) != 3:
            self.__PowerStations.append(PowerStation)
            self.__Electros -= cost
            return False
        else:
            return True
    

    def __lt__(self,other):
        """LEsst than comparison operator for players

        Args:
            other (_type_): player to compare to

        Raises:
            TypeError: if the other object is not a PlayerC instance

        Returns:
            bool: True if self is less than other, False otherwise. TThis is determined by number of cities, then by highest powerstation value.
        """
        if not isinstance(other, PlayerC):
            raise TypeError('Can only compare Player objects')
        if len(self.GetCities()) < len(other.GetCities()):
            return False
        if len(self.GetCities()) > len(other.GetCities()):
            return True
        if self.GetPowerStations()[-1].GetValue() >  other.GetPowerStations()[-1].GetValue():
            return True
        if self.GetPowerStations()[-1].GetValue() <  other.GetPowerStations()[-1].GetValue():
            return False

            



    


        