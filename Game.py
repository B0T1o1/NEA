from UI import UserInterfaceC
from Player import PlayerC
import random
from Board import BoardC
from Resource_Market import R_Market

class GameC:
    def __init__(self, UI:UserInterfaceC,BoardFile = "board.JSON"):
        self.__UI = UI
        self.__STARTING_ELECTROS = 50
        self.__BoardFile = BoardFile

        self.__GameSetUp()

        


    def __GameSetUp(self):
        self.__NofPlayers = self.__UI.RequestPlayers()
        self.__Players = [PlayerC(self.__STARTING_ELECTROS,self.__UI) for i in range (0, self.__NofPlayers)]
        self.__Round = 0
        self.__stage = 1
        self.__Players = Phase1.Random_Assignment(self.__Players)
        self.__UI.DisplayPlayerOrder([player.GetName() for player in self.__Players])
        map = self.__UI.SelectMap()
        self.__Board = BoardC(self.__BoardFile, map)
        self.ChooseStart()



    def ChooseStart(self):
        for player in self.__Players:
            # Create a list of available cities for the current player
            available_cities = [city for city in self.__Board.city_ids if self.__Board.cityIds_to_CityClass[city].CityIsAvailable(player)]
            
            # Pass the list to the UI method
            self.__UI.GetStartingCity(available_cities,player.GetName())





class Phase1:

    def Random_Assignment(players):
        random.shuffle(players)
        return players
    
    def Determine_Player_Order(players):
        players.sort()
        return players

class Phase2:
    def First_round(players):
        for player in players:
            pass

    def Auction(players):
        pass


            

        

if __name__ == '__main__':
    G = GameC(UserInterfaceC())


