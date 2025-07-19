
class UserInterface:

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
    def SelectMap():
        map = input('Please type G for germany map or A for America Map:    ')
        if map == 'G': 
            return 0
        if map == 'A': 
            return 1
        else: 
            return 0

    def GetName() :
        Name = input('Please enter the name of a player:    ')
        return Name
    
    def DisplayPlayerOrder(Player_names):
        print('This is the Player order:    ')
        for place, name in enumerate(Player_names):
            print(f'{place+1}. {name}')

    def GetStartingCity(Cities,Player):
        Choice = ""
        while Choice not in Cities:
            print(f"Which City would {Player} like to start in, the options are:")
            for city in Cities:
                print(city)
            Choice = input("Choice:    ")
            if Choice not in Cities:
                print("that is not a choice, please spell exactly as written")
        print(f"{Player} Have chosen {Choice}")
        return Choice
            



    
    





            