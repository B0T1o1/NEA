from UI import UserInterface
from Player import PlayerC
import random
from Board import Board
from Resource_Market import R_Market

class Game:
    def __init__(self, UI:UserInterface,BoardFile = "board.JSON"):
        self.__UI = UI
        self.__STARTING_ELECTROS = 50
        self.__GameSetUp()
        self.__BoardFile = BoardFile

        


    def __GameSetUp(self):
        self.__NofPlayers = self.__UI.RequestPlayers()
        self.__Players = [PlayerC(self.__STARTING_ELECTROS,self.__UI) for i in range (0, self.__NofPlayers)]
        self.__Round = 0
        self.__stage = 1
        self.__Players = Phase1.Random_Assignment(self.__Players)
        self.__UI.DisplayPlayerOrder([player.GetName() for player in self.__Players])
        map = self.__UI.SelectMap()
        self.__Board = self.__HandleBoard(map)
        self.ChooseStart()


    def __HandleBoard(self,map):
        return Board(self.__BoardFile, map)

    def Phase2():
        pass
    def Phase3():
        pass
    def Phase4():
        pass
    def Phase5():
        pass


class Phase1:

    def Random_Assignment(players):
        random.shuffle(players)
        return players
    
    def Determine_Player_Order(players):
        players.sort()

class Phase2:
    def First_round(players):
        pass

    def Auction(players):
        pass


            

        

if __name__ == '__main__':
    G = Game(UserInterface)


