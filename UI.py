
class UserInterface:
    def __init__(self):
        pass

    def RequestPlayers(self) -> int:
        Valid = False
        while not Valid:
            try:
                Choice = int(input('Please enter the number of players playing: '))
                Valid = True
            except ValueError:
                print('You didnt not enter an integer, please choose a whole positive number of players:')
        return Choice
    
    def DisplayBoard(Board):
        pass


            