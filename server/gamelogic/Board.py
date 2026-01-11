import json
import math
import copy


class BoardC:
    """Holds the infomration of teh board for the game
    """
    def __init__(self,filename:str,map,regions:list[str]):
        """intialises the board class

        Args:
            filename (str): file path to the board json
            map (str): map identifier
            regions (list[str]): list of regions to include
        """
        try:
            file = open(filename,'r')
        except FileNotFoundError:
            pass
        map_string_to_index = {'G':0}

        self.__map_data = json.load(file)["maps"][map_string_to_index[map]]
        self._regions = regions

        self.LoadMap()

    def LoadMap(self):
        """Generates the map of cities from the board file
        """
        self.city_ids = [city["id"] for city in self.__map_data["cities"] if city["region"] in self._regions]
        self.city_to_indexes = {city_id:i for i,city_id in enumerate(self.city_ids)}
        self.indexes_to_cities = {i:city_id for i,city_id in enumerate(self.city_ids)}
        self.cityIds_to_CityClass = {city["id"]:City(city["id"],i,city["region"]) for i,city in enumerate(self.__map_data["cities"]) if city["region"] in self._regions}
        self.number_of_cities = len(self.city_ids)
        self.adjancency_matrix = [[math.inf for _ in range( self.number_of_cities) ] for _ in range(self.number_of_cities)]
        
        # Populate adjanceny matrix
        for city in self.__map_data["cities"]:
            if city["region"] not in self._regions:
                continue
            source_id = city["id"]
            source_index = self.city_to_indexes[source_id]

            for connection_id,cost in city["connections"].items():
                # Check if the connected city is actually on the board before proceeding
                if connection_id in self.city_to_indexes:
                    connection_index = self.city_to_indexes[connection_id]
                    
                    self.adjancency_matrix[source_index][connection_index] = cost
                    # Undirected so mirror
                    self.adjancency_matrix[connection_index][source_index] = cost


    def CheckConnectionCost(self,Source_id:str,Connection_id:str) -> int:
        """Calculates the connection cost between to cities to go directly between them

        Args:
            Source_id (str): City id of source city
            Connection_id (str): City id of connection city

        Returns:
            int: Connection cost between the two cities
        """
        Source_index = self.city_to_indexes[Source_id]
        Connection_index = self.city_to_indexes[Connection_id]
        return self.adjancency_matrix[Source_index][Connection_index]
    


    def DjkstrasSearch(self,Source_id:str, Connection_id:str,PlayerName:str)-> float:
        """Calculates the cheapest cost to connect two cities using Dijkstra's algorithm, taking into account owned cities and finding the cheapest path
        Args:
            Source_id (str): City id of source city
            Connection_id (str): City id of connection city
            PlayerName (str): Name of the player trying to connect the cities

        Returns:
            int: Cheapest connection cost between the two cities for the player
        """
        Source_index = self.city_to_indexes[Source_id]
        Connection_index = self.city_to_indexes[Connection_id]
        previous  = [None] * self.number_of_cities
        visited = [False] * self.number_of_cities
        distances = [math.inf] * self.number_of_cities
        distances[Source_index] = 0
        v = Source_index
        while not all(visited):
            for w in range(self.number_of_cities):
                if self.cityIds_to_CityClass[self.indexes_to_cities[v]].DoesPlayerOwnCity(PlayerName) and self.cityIds_to_CityClass[self.indexes_to_cities[w]].DoesPlayerOwnCity(PlayerName):
                    cost = 0
                else:
                    cost = self.adjancency_matrix[v][w]
                dist_to_w = distances[v] + cost
                if dist_to_w < distances[w]:
                    distances[w] = dist_to_w
                    previous[w] = v
            visited[v] = True
            min_d = math.inf
            for w in range(self.number_of_cities):
                if not visited[w] and distances[w] < min_d:
                    min_d = distances[w]
                    v = w
        return distances[Connection_index]
    
    def ChangeStage(self,stage:int) -> bool:
        """Updates the stage in all cities so that more players can buy into a city

        Args:
            stage (int): stage to update the cities to

        Returns:
            bool: True if stage updated successfully, False otherwise
        """
        if stage not in [1,2,3]:
            return False
        for cityid in self.city_ids:
            city = self.cityIds_to_CityClass[cityid]
            city.UpdateStage(stage)
        return True
    
    def DisplayBoardInfoBeforeGame(self):
        """Returns a JSON of the board to prevent external modification


        Returns:
            dict: board information before the game starts
        """
        info = {
            "regions": self._regions.copy(),
            "city_Indexes": self.indexes_to_cities,
            "cities": {
                cid: {
                    "region": city.Region,
                    "owners": city.GetPlayersInCity(),
                    "Available": city.CityIsAvailable(),
                    "cost": city.GetCostInCity(),
                    "connections": {i:cost for i,cost in enumerate(self.adjancency_matrix[self.city_to_indexes[cid]])}
                } for cid, city in self.cityIds_to_CityClass.items()
            },
        }
        return info

        

    def DisplayBoardInfo(self,playerstartingcity:str,playername:str)-> dict[str,list[str]|dict]:
        """Returns a dictionary of the board to send over a network

        Args:
            playerstartingcity (str): The starting city of the player
            playername (str):   Name of the player requesting the board info

        Returns:
            dict[str,list[str]|dict]: A dictionary representing the board information tailored for the requesting player.
        """
        info = {
            "regions": self._regions.copy(),
            "city_Indexes": self.indexes_to_cities,
            "cities":{
            cid: {
                    "region": city.Region,
                    "owners": city.GetPlayersInCity(),
                    "Available": city.CityIsAvailableToPlayer(playername),
                    "cost": city.GetCostInCity() + self.DjkstrasSearch(playerstartingcity,cid,playername),
                    "connections": {i:cost for i,cost in enumerate(self.adjancency_matrix[self.city_to_indexes[cid]])}
                } for cid, city in self.cityIds_to_CityClass.items()
            },

        }
        return info

        
        




class City:
    """city class 
    """
    def __init__(self,CityId:str,CityIndex:int,Region:str):
        """the city class intialiser

        Args:
            CityId (str): The unique identifier for the city.
            CityIndex (int): The index of the city in the board's city list.
            Region (str): The region to which the city belongs.
        """
        self.__CityId = CityId
        self.__PlayersOwn = []
        self.__Stage = 1
        self.Region = Region

    def PlayerBuyCity(self,PlayerName:str):
        """Player buy city

        Args:
            PlayerName (str): The name of the player buying the city

        Raises:
            Exception: If the city is not available to the player.
        """
        if self.CityIsAvailableToPlayer(PlayerName):
                self.__PlayersOwn.append(PlayerName)  
        else:
            raise Exception("City not available to player")

    def GetCostInCity(self) -> int:
        """Gives the cost to buy into this city

        Returns:
            int: The cost to buy into this city.
        """
        return (len(self.__PlayersOwn)+2) * 5
        
    def DoesPlayerOwnCity(self,PlayerName: str) -> bool:
        """Checks whether  player owns this city

        Args:
            PlayerName (str): the name of the player you would like to check

        Returns:
            bool: True if the player owns the city, False otherwise.
        """
        if PlayerName in self.__PlayersOwn:
            return True
        else:
            return False
        
    def GetPlayersInCity(self) -> list[str]:
        """Gives the names of the players in the city

        Returns:
            list[str]: List of player names in the city
        """
        return list(self.__PlayersOwn)
    
    def CityIsAvailableToPlayer(self,PlayerName: str) -> bool:
        """Checks if a player can buy into a city

        Args:
            PlayerName (str): The name of the player to check availability for

        Returns:
            bool: True if the city is available to the player, False otherwise.
        """
        if len(self.__PlayersOwn) != self.__Stage and PlayerName not in self.__PlayersOwn:
            return True 
        else:
            return False
        
    def CityIsAvailable(self) -> bool:
        """Checks if a city is available

        Returns:
            bool: True if the city is available, False otherwise.
        """
        if len(self.__PlayersOwn) != self.__Stage:
            return True
        else:
            return False
        
    def UpdateStage(self,stage:int):
        """updates the city stage

        Args:
            stage (int): the stage to update the city to
        """
        self.__Stage = stage

    
    
