import math
class UIC():
    def __init__(self):
        self.UI = self.GetUserInterface()
    def GetUserInterface(self):
        print('Enter a t for a terminal interface or g for a graphical interface:')
        while True:
            choice = input().strip().lower()
            if choice == 't':
                return TUIC()
            elif choice == 'g':
                return GUIC()
            else:
                print('Invalid choice. Please enter "t" or "g":')
    def GetLoginDetails(self) -> tuple[str,str]:
        return self.UI.GetLoginDetails()
    def GetLogin_or_Register(self):
        return self.UI.GetLogin_or_Register()
    def GetRegisterDetails(self) -> tuple[str,str]:
        return self.UI.GetRegisterDetails()
    def DisplayPlayerList(self,players:list[str]):
        return self.UI.DisplayPlayerList(players)
    def DisplayMessage(self,message:str):
        return self.UI.DisplayMessage(message)
    def DisplayBoard(self,board):
        return self.UI.DisplayBoard(board)
class TUIC(UIC):
    def __init__(self):
        pass
    def DisplayMessage(self,message:str):
        print(message)
    
    def GetLogin_or_Register(self):
        print('Do you want to (l)ogin or (r)egister?')
        while True:
            choice = input().strip().lower()
            if choice == 'l':
                return 'login'
            elif choice == 'r':
                return 'register'
            else:
                print('Invalid choice. Please enter "l" or "r":')

    def GetLoginDetails(self) -> tuple[str,str]:
        username = input('Enter username: ')
        password = input('Enter password: ')
        return (username,password)
    
    def GetRegisterDetails(self) -> tuple[str,str]:
        username = input('Enter desired username: ')
        password = input('Enter desired password: ')
        return (username,password)
    
    def DisplayPlayerList(self,players:list[str]):
        print('Current players in the game:')
        for player in players:
            print(f'- {player}')
    
    def DisplayBoard(self, board_info:dict):
        """
        Takes the dictionary output from BoardC.DisplayBoardInfo
        and prints a formatted report to the terminal.
        """
        
        cities_data = board_info["cities"]
        matrix = board_info["connections"]
        
        # We need an ordered list of keys to match the matrix indices.
        # In Python 3.7+, dictionary insertion order is preserved, so this works 
        # assuming BoardC populated them in the same order as the matrix.
        city_names_ordered = list(cities_data.keys())

        print("\n" + "="*80)
        print(f"{'POWER GRID BOARD STATUS':^80}")
        print("="*80 + "\n")

        # --- SECTION 1: CITY OVERVIEW ---
        # Headers with fixed width formatting
        header = f"| {'CITY ID':<15} | {'REGION':<10} | {'COST':<6} | {'STATUS':<10} | {'OWNERS'}"
        print("-" * len(header))
        print(header)
        print("-" * len(header))

        for city_id, data in cities_data.items():
            # Format Owners List
            owners_list = data["owners"]
            owners_str = ", ".join(owners_list) if owners_list else "Empty"
            
            # Format Availability
            is_avail = "OPEN" if data["Available"] else "FULL"
            
            # Print Row
            print(f"| {city_id:<15} | {data['region']:<10} | {data['cost']:<6} | {is_avail:<10} | {owners_str}")

        print("-" * len(header))
        print("\n")

        # --- SECTION 2: CONNECTIONS (The Network) ---
        print(f"{'NETWORK CONNECTIONS':^80}")
        print("-" * 80)

        # We iterate through the matrix using the ordered city names
        for i, source_city in enumerate(city_names_ordered):
            connections = []
            row = matrix[i]
            
            for j, cost in enumerate(row):
                # Ignore self-loops (0) and non-connections (infinity)
                if cost != math.inf and i != j:
                    target_city = city_names_ordered[j]
                    connections.append(f"{target_city} (${cost})")
            
            # Join connections with a nice arrow
            if connections:
                conn_str = "  <-->  ".join(connections)
                print(f"[{source_city.upper()}] connects to:  {conn_str}")
            else:
                print(f"[{source_city.upper()}] IS ISOLATED")
        
        print("\n" + "="*80 + "\n")

class GUIC(UIC):
    pass
