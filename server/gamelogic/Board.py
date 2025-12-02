import json
import math
import copy


class BoardC:
    def __init__(self,filename:str,map,regions:list[str]):
        try:
            file = open(filename,'r')
        except FileNotFoundError:
            #TODO Ui errors
            pass
        map_string_to_index = {'G':0}

        self.__map_data = json.load(file)["maps"][map_string_to_index[map]]
        self._regions = regions

        self.LoadMap()

    def LoadMap(self):
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
        Source_index = self.city_to_indexes[Source_id]
        Connection_index = self.city_to_indexes[Connection_id]
        return self.adjancency_matrix[Source_index][Connection_index]
    


    def DjkstrasSearch(self,Source_id:str, Connection_id:str,PlayerName:str):
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
    
    def ChangeStage(self,stage:int):
        for cityid in self.city_ids:
            city = self.cityIds_to_CityClass[cityid]
            city.UpdateStage(stage)
        return
    
    def DisplayBoardInfoBeforeGame(self):
        # Return a JSON of the board to prevent external modification
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

        

    def DisplayBoardInfo(self,playerstartingcity,playername):
        # Return a JSON of the board to prevent external modification
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
    def __init__(self,CityId,CityIndex,Region):
        self.__CityId = CityId
        self.__PlayersOwn = []
        self.__Stage = 1
        self.Region = Region

    def PlayerBuyCity(self,PlayerName):
        if self.CityIsAvailableToPlayer(PlayerName):
                self.__PlayersOwn.append(PlayerName)  
        else:
            pass # TODO create an error

    def GetCostInCity(self):
        return (len(self.__PlayersOwn)+2) * 5
        
    def DoesPlayerOwnCity(self,PlayerName):
        if PlayerName in self.__PlayersOwn:
            return True
        else:
            return False
        
    def GetPlayersInCity(self):
        return list(self.__PlayersOwn)
    
    def CityIsAvailableToPlayer(self,PlayerName):
        if len(self.__PlayersOwn) != self.__Stage and PlayerName not in self.__PlayersOwn:
            return True 
        else:
            return False
    def CityIsAvailable(self):
        if len(self.__PlayersOwn) != self.__Stage:
            return True
        else:
            return False
        
    def UpdateStage(self,stage:int):
        self.__Stage = stage

    
    

if __name__ == '__main__':
    BoardC('Data/board.JSON','G',["Brown","Yellow","Red","Purple"])
