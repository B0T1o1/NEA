from math import inf
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
    def GetStartingCity(self):
        return self.UI.GetStartingCity()
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
    
    def DisplayBoard(self, board_info: dict):

        """
        Takes the dictionary output from BoardC.DisplayBoardInfo
        and prints a formatted report to the terminal, using city_Indexes
        to translate connection keys.
        """
        
        cities_data = board_info["cities"]
        # New: Get the mapping from index to city name
        city_index_to_name = board_info["city_Indexes"]
        
        # --- SECTION 0: BOARD HEADER & REGIONS ---
        
        print("\n" + "="*80)
        print(f"{'⚡ POWER GRID BOARD STATUS ⚡':^80}")
        print("="*80)
        
        print("\n🌐 REGIONS AVAILABLE:")
        regions_str = ", ".join(board_info.get("regions", []))
        print(f"  {regions_str}")
        
        print("-" * 80 + "\n")

        # --- SECTION 1: CITY OVERVIEW ---
        
        print(f"{'CITY OVERVIEW':^80}")
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
            # 'cost' is the cost to build the first house, including connection cost from starting city.
            print(f"| {city_id:<15} | {data['region']:<10} | {data['cost']:<6} | {is_avail:<10} | {owners_str}")

        print("-" * len(header))
        print("\n")

        # --- SECTION 2: NETWORK CONNECTIONS ---
        
        print(f"{'🗺️ NETWORK CONNECTIONS':^80}")
        print("-" * 80)

        # Iterate through the city data where connections are stored
        for source_city, data in cities_data.items():
            connections = []
            
            # data["connections"] now uses integer indexes as keys.
            for index, cost in data["connections"].items():
                
                # Check for math.inf (representing no connection) and the self-loop (cost 0)
                # Since the DisplayBoardInfo function used enumerate(self.adjancency_matrix[...])
                # and the adjacency matrix typically has the city itself with cost 0, we filter that out.
                if cost != math.inf and cost != 0: 
                    # Translate the index back to the city name
                    target_city = city_index_to_name.get(index, f"UNKNOWN INDEX {index}")
                    connections.append(f"{target_city} (${cost})")
            
            # Join connections with a nice arrow
            if connections:
                conn_str = "  <-->  ".join(connections)
                print(f"[{source_city.upper()}] connects to:  {conn_str}")
            else:
                print(f"[{source_city.upper()}] HAS NO EXTERNAL CONNECTIONS")
        
        print("\n" + "="*80 + "\n")

    def GetStartingCity(self):
        city = input('Please enter the city id of the city you would like to buy')
        return city

class GUIC(UIC):
    pass
