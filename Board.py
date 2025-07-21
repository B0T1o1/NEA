import json
import math

class BoardC:
    def __init__(self,filename:str,map,regions:list[str]):
        try:
            file = open(filename,'r')
        except FileNotFoundError:
            #TODO Ui errors
            pass
        self.__map_data = json.load(file)["maps"][map]
        self.__regions = regions

        self.LoadMap()




    def LoadMap(self):
        self.city_ids = [city["id"] for city in self.__map_data["cities"] if city["region"] in self.__regions]
        self.city_to_indexes = {city_id:i for i,city_id in enumerate(self.city_ids)}
        self.indexes_to_cities = {i:city_id for i,city_id in enumerate(self.city_ids)}
        self.cityIds_to_CityClass = {city["id"]:City(city["id"],i,city["region"]) for i,city in enumerate(self.__map_data["cities"]) if city["region"] in self.__regions}
        self.number_of_cities = len(self.city_ids)
        self.adjancency_matrix = [[math.inf for _ in range( self.number_of_cities) ] for _ in range(self.number_of_cities)]
        
        # Populate adjanceny matrix
        for city in self.__map_data["cities"]:
            if city["region"] not in self.__regions:
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
    


    def DjkstrasSearch(self,Source_index, PlayerName, Connection_index,):
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

        

        
        




class City:
    def __init__(self,CityId,CityIndex,Region):
        self.__CityId = CityId
        self.__PlayersOwn = []
        self.__Stage = 1
        self.Region = Region
    def PlayerBuyCity(self,Electros,PlayerName):
        if self.CityIsAvailable(PlayerName):
            Cost = (len(self.__PlayersOwn)+2) * 5 
            if Cost > Electros:
                raise ValueError # TODO Create an insuffcient funds error
            else:
                Electros -= Cost
                self.__PlayersOwn.append(PlayerName)  
                return Electros
        else:
            pass # TODO create an error
        
    def DoesPlayerOwnCity(self,PlayerName):
        if PlayerName in self.__PlayersOwn:
            return True
        else:
            return False
    
    def CityIsAvailable(self,PlayerName):
        if len(self.__PlayersOwn) != self.__Stage and PlayerName not in self.__PlayersOwn:
            return True 
        else:
            return False

    
    



if __name__ == "__main__":   
    B = BoardC('board.JSON',0)
    B.cityIds_to_CityClass["emden"].PlayerBuyCity(20,"Luca")
    print(B.cityIds_to_CityClass["emden"].CityIsAvailable("maya"))