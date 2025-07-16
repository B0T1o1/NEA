
class UserInterface:
    def __init__(self):
        pass

    def RequestPlayers() -> int:
        Valid = False
        while not Valid:
            try:
                Choice = int(input('Please enter the number of players playing:     '))
                Valid = True
            except ValueError:
                print('You didnt not enter an integer, please choose a whole positive number of players:    ')
        return Choice
    
    def DisplayBoard(Board):
        pass
    def SelectMap() -> int:
        map = input('Please type G for germany map or A for America Map')
        if map == 'G': return 0
        if map == 'A': return 1

    def GetName() -> str:
        Name = input('Please enter the name of a player')
        return Name
    
    def DisplayPlayerOrder(Player_names:list[str]):
        print('This is the Player order:    ')
        for place, name in enumerate(Player_names):
            print(f'{place+1}. {name}')
        return




            