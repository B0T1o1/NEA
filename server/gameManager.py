import gamelogic.GameState
import gamelogic.PowerStation
import client.ui
class GameManagerC:
    def __init__(self):
        self.__GameState = gamelogic.GameState.GameStateC()


class LocalGameManagerC(GameManagerC):
    def __init__(self):
        super().__init__()
        self.clientUI = client.ui.terminal.TerminalUIC()
        self.clientUI.set_up_game(self.__GameState.Get_board())
        


class RemoteGameManagerC(GameManagerC):
    def __init__(self, connection):
        super().__init__()
        self.__Connection = connection
        
    

