from .PowerStation import PowerStationC

class PlayerC:
    def __init__(self,Electros:int,name):
        self.__Electros = Electros
        self.__PowerStations: list[PowerStationC] = []
        self.__cities: list[str] = []
        self.__name = name
        self.__Resources =  { 'C':0, 'O':0, 'G':0, 'N':0}

    def Pay(self,Electros:int):
        self.__Electros += Electros
    def GetPowerStations(self) -> list[PowerStationC]:
        self.__PowerStations.sort()
        return self.__PowerStations
    
    def GetResourceSpace(self) -> dict:
            available = { 'C':0, 'O':0, 'H':0, 'G':0, 'N':0, 'R':0}
            
            # 1. Calculate total raw capacity based on stations
            for PowerStation in self.__PowerStations:
                available[PowerStation.GetFuelType()] += PowerStation.GetFuelAmount() * 2
                
            # 2. Subtract currently held resources
            for type in ['C','O','G','N']:
                available[type] -= self.__Resources[type]

            # 3. Handle Hybrid Overflow (Crucial Step)
            # If available['C'] is negative (e.g., -2), it means we have 2 extra Coal
            # that must be stored in Hybrid space. We subtract that from 'H'.
            if available['C'] < 0:
                available['H'] += available['C'] # Reduces H capacity by the overflow
                available['C'] = 0               # Resets C to 0 (no negative space)

            if available['O'] < 0:
                available['H'] += available['O'] # Reduces H capacity by the overflow
                available['O'] = 0               # Resets O to 0

            # 4. Final Safety Check
            # Ensure H (or G/N if there was an error) never returns a negative number
            for key in available:
                if available[key] < 0:
                    available[key] = 0
                    
            return available
    
    def HasResourceSpace(self, Type: str, amount: int) -> bool:
            # Get the currently available empty slots 
            # (This assumes GetResourceSpace correctly calculates remaining 'H' space)
            spaces = self.GetResourceSpace()
            
            # Start with the specific space for the requested type
            total_space = spaces.get(Type, 0)
            
            # If the requested type is Coal or Oil, they can also use the available Hybrid space
            if Type in ['C', 'O']:
                total_space += spaces.get('H', 0)
                
            # Check if the total available space is sufficient
            return total_space >= amount
        
    def GetResources(self):
        return dict(self.__Resources)

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
        self.__Electros -= 10 #TODO make global constant maybe
        self.__sourceCity = city
        self.__cities.append(city)
    def ChangeResources(self,NewResources:dict[str,int]):
        self.__Resources = NewResources
    
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

            



    


        