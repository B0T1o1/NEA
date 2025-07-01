from UI import UserInterface
from Player import PlayerC
class Game:
    def __init__(self, UI):
        self.__UI = UI
        self.__GameSetUp()


    def __GameSetUp(self):
        self.__NofPlayers = self.UI.RequestPlayers(self)
        self.__Players = [PlayerC for i in range (0, self.NofPlayers )]
        self.__Round = 0
    
    def Phase1(self):
        for player in self.__Players:
            player.

    def Phase2():
        pass
    def Phase3():
        pass
    def Phase4():
        pass
    def Phase5():
        pass

        

if __name__ == '__main__':
    G = Game(UserInterface)


