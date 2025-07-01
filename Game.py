from UI import UserInterface
from Player import PlayerC
import random
class Game:
    def __init__(self, UI:UserInterface):
        self.__UI = UI
        self.__STARTING_ELECTROS = 50
        self.__GameSetUp()

        


    def __GameSetUp(self):
        self.__NofPlayers = self.__UI.RequestPlayers()
        self.__Players = [PlayerC(self.__STARTING_ELECTROS,self.__UI) for i in range (0, self.__NofPlayers)]
        self.__Round = 0
        self.__stage = 1
        self.__Players = Phase1.Random_Assignment(self.__Players)
        self.__UI.DisplayPlayerOrder([player.GetName() for player in self.__Players])
        self.

    def Phase1(self):
        pass

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

            

        

if __name__ == '__main__':
    G = Game(UserInterface)


