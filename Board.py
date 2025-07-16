from UI import UserInterface
import json
import math
class Board:
    def __init__(self,filename:str,map):
        try:
            file = open(filename,'r')
        except FileNotFoundError:
            #TODO Ui errors
            pass
        self.__map_data = json.load(file)["maps"][map]
        self.LoadMap()
        print(self.adjancency_matrix)



    def LoadMap(self):
        self.regions = self.__map_data["regions"]
        self.city_ids = [city["id"] for city in self.__map_data["cities"]]
        self.city_to_indexes = {city_id:i for i,city_id in enumerate(self.city_ids)}
        self.indexes_to_cities = {i:city_id for i,city_id in enumerate(self.city_ids)}
        self.number_of_cities = len(self.city_ids)
        self.adjancency_matrix = [[math.inf for _ in range( self.number_of_cities) ] for _ in range(self.number_of_cities)]
        
        # Populate adjanceny matrix
        for city in self.__map_data["cities"]:
            source_id = city["id"]
            source_index = self.city_to_indexes[source_id]
            for connection_id,cost in city["connections"].items():
                connection_index = self.city_to_indexes[connection_id]
                
                self.adjancency_matrix[source_index][connection_index] = cost
                # Undirected so mirror
                self.adjancency_matrix[connection_index][source_index] = cost


    def CheckConnectionCost(self,Source_id:str,Connection_id:str) -> int:
        Source_index = self.city_to_indexes[Source_id]
        Connection_index = self.city_to_indexes[Connection_id]
        return self.adjancency_matrix[Source_index][Connection_index]
    

    def Cheapest_Path(self,Source_id, Owned_id,Connection_id,cost = 0):
        # Essentially a recusive djkstra's
        # TODO
        Connection_Cost = self.CheckConnectionCost(Source_id,Connection_id)

        if Connection_Cost != math.inf:
            return cost
        
        else:
            pass





                




Board('board.JSON',0)
