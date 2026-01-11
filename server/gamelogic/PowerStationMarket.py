from .PowerStation import PowerStationC
import json
import random
import math
PLUGGED = 0
UNPLUGGED = 1
class PS_Market:
    """Class for powerstation market
    """
    def __init__(self,PowerStationsFile:str,NofPlayers:int):
        """The intialiser for the powerstation market

        Args:
            PowerStationsFile (str): file path for powerstations data
            NofPlayers (int): number of players in the game
        """
        # How many powerplants to remove: {players:(unplugged,plugged)}
        self.__RemovePowerPlants = {3:(2,6),4:(1,3),5:(0,0),6:(0,0)}
        self.__Deck: list[PowerStationC] = []
        self.__PluggedPowerStations,self.__UnpluggedPowerStations = self.ExtractStationsFromFile(PowerStationsFile)
        random.shuffle(self.__PluggedPowerStations)
        self.__PluggedPowerStations = self.RemovePowerStation(NofPlayers,PLUGGED)
        self.__Market:list[PowerStationC] = self.__PluggedPowerStations[:8]
        self.__Market.sort()
        self.__Deck = self.__PluggedPowerStations[8:-1]
        self.__Cover = self.__PluggedPowerStations[-1]
        self.__Deck += self.RemovePowerStation(NofPlayers,UNPLUGGED)
        random.shuffle(self.__Deck)
        self.__Deck.append(self.__Cover)
        self.__Deck.append(Stage3(0,'',0,0))
        self.__stage = 1
 
    def ExtractStationsFromFile(self,PowerStationsFile:str):
        """Extracts station from the powerstations file

        Args:
            PowerStationsFile (str): file path for powerstations data

        Returns:
            tuple: two lists containing plugged and unplugged power stations
        """
        with open(PowerStationsFile,"r") as file:
            JsonStations = json.load(file)
        plugged = []
        unplugged = []
        for station in JsonStations:
            if station["Value"] <= 15:
                plugged.append(PowerStationC(station["Value"],station["FuelType"],station["FuelAmount"],station["NumberOfCitiesPowered"]))
            else:
                unplugged.append(PowerStationC(station["Value"],station["FuelType"],station["FuelAmount"],station["NumberOfCitiesPowered"]))
        return plugged,unplugged
    
    def RemovePowerStation(self,NofPlayers:int,plugged:int) -> list[PowerStationC]:
        """Remove power stations based on the number of players and whether they are plugged or unplugged

        Args:
            NofPlayers (int): number of players in the game
            plugged (int): indicates whether the power stations are plugged (0) or unplugged (1)
        Returns:
            list[PowerStationC]: list of power stations after removal
        """
        if plugged == 0:
            StationList = self.__PluggedPowerStations
        else:
            StationList = self.__UnpluggedPowerStations

        for i in range(0,self.__RemovePowerPlants[NofPlayers][plugged]):
            StationList.pop(random.randrange(0,len(StationList)))

        return StationList
    
    def GiveMarket(self)-> tuple[list[PowerStationC],list[PowerStationC]]:
        """Gives the current market as an upper and a lower even if in stage 3, where the lower represents the whole market

        Returns:
            tuple: two lists representing the lower and upper market
        """
        if self.__stage != 3:
            return self.__Market[:4] , self.__Market[4:]
        else:
            return self.__Market , []
        
    def GetMarketString(self) -> str:
        """Returns a string with all market information


        Returns:
            str: Market information
        """
        lower, upper = self.GiveMarket()
        return str([[ps.station_to_str() for ps in lower],[ps.station_to_str() for ps in upper]])


    def BuyPowerStation(self,Station:PowerStationC)-> PowerStationC:
        """Removes a powersatation from the powerstation market, if a valid purchase

        Args:
            Station (PowerStationC): Powerstation to buy

        Raises:
            ValueError: PowerStation not in Market
                
        Returns:
            PowerStationC: The purchased power station
        """
        for index, station in enumerate(self.__Market):
            if station.GetValue() == Station.GetValue():
                if self.__stage != 3:
                    if 0 <= index < 4:
                        self.__Market.pop(index)
                        if self.__Deck:
                            self.__Market.append(self.__Deck.pop(0))
                        self.__Market.sort()
                else:
                    self.__Market.pop(index)
                    if self.__Deck:
                        self.__Market.append(self.__Deck.pop(0))
                    self.__Market.sort()                
                return Station
        raise ValueError("PowerStation not in Market")
            
    def GetDeck(self)-> list[PowerStationC]:
        """Getter for the deck

        Returns:
            list[PowerStationC]: The current deck of power stations
        """
        return self.__Deck

    def RemoveDiscountedPowerStation(self):
        """Removes the discounted powerstation in bureacarcy if it has not been bought

        Raises:
            ValueError: Cannot remove discounted powerstation in stage 3
        """
        if self.__stage != 3:
            self.__Market.pop(0)    
            if self.__Deck:
                self.__Market.append(self.__Deck.pop(0))
            self.__Market.sort()
        else:
            raise ValueError("Cannot remove discounted powerstation in stage 3")

    def Stage2(self):
        """Updates the powerstation market to pahse 2
        """
        self.BuyPowerStation(self.GiveMarket()[0][0])
        self.__stage = 2
        return

    def Stage3(self) -> bool:
        """Updates the powerstation market to phase 3

        Returns:
            bool: True if stage updated successfully, False otherwise
        """
        if self.__Market[-1].GetValue() == math.inf:
            self.__stage = 3
            self.__Market.pop(0)
            self.__Market.pop()

            return True
        else:
            self.RemoveTopPowerStation()
        return False

    def RemoveTopPowerStation(self):
        """Removes the top powerstation and puts at the bototm fo the deck
        """
        if self.__stage <=  2:
            self.__Deck.append(self.__Market.pop())
            self.__Market.append(self.__Deck.pop(0))
            self.__Market.sort()
            


class Stage3(PowerStationC):
    """Class for stage 3 card, inherits from PowerStationC
    """
    def __init__(self, Value:int, FuelType:str, FuelAmount:int, NumberOfCitiesPowered:int):
        """Intialiser for stage 3 card

        Args:
            Value (int): The value of the power station
            FuelType (str): The type of fuel used by the power station
            FuelAmount (int): The amount of fuel required by the power station
            NumberOfCitiesPowered (int): The number of cities powered by the power station
        """
        super().__init__(Value, FuelType, FuelAmount, NumberOfCitiesPowered)
        self.__Value: float = math.inf
        self.__Fuel_To_word = { 'C':'Coal', 'O':'Oil', 'H':'Hybrid', 'G': 'Garbadge', 'N':'Nuclear', 'R':'Renewable','S':'Stage3'}
        self.__FuelType = 'S'
        self.__FuelAmount: float = math.inf
        self.__NumberOfCitiesPowered = 0

    def GetValue(self) -> float:
        """Gives falue

        Returns:
            float: returns infinity
        """
        return self.__Value
    def GetFuelType(self) -> str:
        """Gives the fuel type

        Returns:
            str: The fuel type
        """
        return self.__FuelType
    
    def GetFuelWord(self) -> str:
        """Gives the fuel type in word form

        Returns:
            str: The fuel type in word form, Stage3
        """
        return 'Stage3'
    
    def GetFuelAmount(self) -> float:
        """_summary_

        Returns:
            float: returns infinity
        """
        return self.__FuelAmount
    
    def GetNumberOfCitiesPowered(self) -> int:
        """Returns 0

        Returns:
            int: returns 0
        """
        return self.__NumberOfCitiesPowered


    def __lt__(self,other) -> bool:
        """less than comparison for stage 3 card

        Args:
            other (PowerStationC): The other power station to compare with

        Raises:
            TypeError: If the other object is not a PowerStationC

        Returns:
            bool: True if this power station is less than the other, False otherwise
        """
        if not isinstance(other, PowerStationC):
            raise TypeError('Can only compare PowerStation objects')
        return self.__Value < other.GetValue()
    