from PowerStation import PowerStationC
from Board import BoardC
from Player import PlayerC
import math
import networkx as nx
import matplotlib.pyplot as plt
TYPE_TO_WORD = { 'C':'Coal', 'O':'Oil', 'H':'Hybrid', 'G': 'Garbage', 'N':'Nuclear', 'R':'Renewable'}

class UserInterfaceC:

    def RequestPlayers(self) -> int:
        Valid = False
        while not Valid:
            try:
                Choice = int(input('Please enter the number of players playing:     '))
                Valid = True
            except ValueError:
                print('You didnt not enter an integer, please choose a whole positive number of players:    ')
        return Choice

    def SelectMap(self):
        map = input('Please type G for germany map or A for America Map:    ')
        if map == 'G': 
            return 0
        if map == 'A': 
            return 1
        else: 
            return 0

    def GetName(self) -> str:
        Name = input('Please enter the name of a player:    ')
        return Name
    
    def DisplayPlayerOrder(self,Player_names:list[str]):
        print('This is the Player order:    ')
        for place, name in enumerate(Player_names):
            print(f'{place+1}. {name}')

    def GetStartingCity(self,Cities:list[str],Player:str)-> str:
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
    
    def RemovePowerStation(self, PowerStations:list[PowerStationC],PlayerName):
        Valid = False
        while not Valid:
            try:
                print(f'{PlayerName} Please choose a Power station to remove:')
                for number, PStation in enumerate(PowerStations):
                    self.DisplayPowerStation(number +1,PStation)
                print('Please input the value of the powerstation you would like to remove:')
                choice = int(input(''))
            except ValueError:
                print('Not valid PowerStation, please try again')
                continue
            else:
                return choice
    
    def DisplayPowerStation(self,Position, PStation:PowerStationC):
        print(f'{Position}. \nValue:{PStation.GetValue()}\nType:{PStation.GetFuelWord()}\nNumber of Resource to Power:{PStation.GetFuelAmount()}\nNumber Of Cities Powered:{PStation.GetNumberOfCitiesPowered()}' )

    def DisplayCurrentMarket(self,discount:bool, Stations:list[PowerStationC]):
        print("This is the current market:")
        if discount: print("First Currently has discount")
        for i,station  in enumerate(Stations):
            self.DisplayPowerStation(i+1,station)

    def DisplayFutureMarket(self, Stations:list[PowerStationC]):
            print("This is the future market:")
            for i,station  in enumerate(Stations):
                self.DisplayPowerStation(i+5,station)
        

    def ChooseStationToAuctionFirst(self, market: list[PowerStationC], player_name: str) -> PowerStationC:
        print(f"\n{player_name}, choose a Power Station to auction.")
        valid_ids = [str(station.GetValue()) for station in market]
        
        while True:
            choice = input(f"Enter the Value of the station ({', '.join(valid_ids)}): ")
            if choice in valid_ids:
                for station in market:
                    if str(station.GetValue()) == choice:
                        return station
            print("Invalid ID. Please choose a station from the current market.")
    
    def ChooseStationToAuction(self, market: list[PowerStationC], player_name: str) :
        print(f"\n{player_name}, choose a Power Station to auction.")
        valid_ids = [str(station.GetValue()) for station in market]
        while True:
            choice = input(f"Enter the Value of the station ({', '.join(valid_ids)}) or type 'pass': ")
            if choice == 'pass':
                return -1
            if choice in valid_ids:
                for station in market:
                    if str(station.GetValue()) == choice:
                        return station
            print("Invalid ID. Please choose a station from the current market.")

    def GetAuctionBid(self, station: PowerStationC, current_bid: int, high_bidder_name: str, player: PlayerC) -> int | None:
        print(f"\n--- Bidding on Power Station #{station.GetValue()} ---")
        print(f"Current Bid: ${current_bid} (Held by: {high_bidder_name})")
        print(f"{player.GetName()}, you have ${player.GetElectros()}.")

        while True:
            response = input("Enter your bid, or type 'pass': ").lower()
            if response == 'pass':
                print(f"{player.GetName()} passes.")
                return None
            
            try:
                new_bid = int(response)
                if new_bid <= current_bid:
                    print(f"Your bid must be higher than the current bid of ${current_bid}.")
                elif new_bid > player.GetElectros():
                    print(f"You cannot afford this bid. You only have ${player.GetElectros()}.")
                else:
                    return new_bid
            except ValueError:
                print("Invalid input. Please enter a number or 'pass'.")

    def AnnounceAuctionWinner(self, winner_name: str, station_id: int, cost: int):
        print(f"\n🎉 {winner_name} wins Power Station #{station_id} for ${cost}! 🎉")

    def DisplayMessage(self, message: str):
        print(message)
    

    def DisplayFuelCosts(self,
        coal_costs: list[int],
        nuclear_costs: list[int],
        garbage_costs: list[int],
        oil_costs: list[int]
    ) -> None:
        """
        Displays the cumulative costs of different fuel types in a formatted table.

        This function takes four lists of integers, where each list represents the
        cumulative cost of purchasing 1, 2, 3, etc., units of a specific fuel.
        It then prints a formatted table to the console.

        Args:
            coal_costs: A list of cumulative costs for coal.
            nuclear_costs: A list of cumulative costs for nuclear fuel.
            garbage_costs: A list of cumulative costs for garbage.
            oil_costs: A list of cumulative costs for oil.
        """
        # Find the maximum quantity available across all fuel types to set the table height
        try:
            max_quantity = max(len(coal_costs), len(nuclear_costs), len(garbage_costs), len(oil_costs))
        except ValueError:
            print("All cost lists are empty. No data to display.")
            return

        print(f"{'Quantity':<10} | {'Coal':<8} | {'Nuclear':<8} | {'Garbage':<8} | {'Oil':<8}")
        print("-" * 62) # Separator line

        # Iterate through each quantity level up to the maximum
        for i in range(max_quantity):
            quantity = i + 1

            # Safely get the cost for each fuel type, or 'N/A' if that quantity is not available
            coal_cost = str(coal_costs[i]) if i < len(coal_costs) else 'N/A'
            nuclear_cost = str(nuclear_costs[i]) if i < len(nuclear_costs) else 'N/A'
            garbage_cost = str(garbage_costs[i]) if i < len(garbage_costs) else 'N/A'
            oil_cost = str(oil_costs[i]) if i < len(oil_costs) else 'N/A'

            # Print the formatted row with costs
            print(f"{quantity:<10} | {coal_cost:<8} | {nuclear_cost:<8} | {garbage_cost:<8} | {oil_cost:<8}")

    def PlayerHasBoughtFuel(self,name,amount,cost,Type,electros):
        print(f'{name} has bought {amount} of {TYPE_TO_WORD[Type]} for {cost}and now has ${electros}')
    def DisplayPlayerMoney(self,player:PlayerC):
        print(f'{player.GetName()} has ${player.GetElectros()}')

    def GetAmountOfFuelType(self) -> tuple[str | None, int]:
        """
        Prompts the player to enter the type and amount of fuel they wish to buy.

        Handles input validation and allows the player to pass their turn.

        Returns:
            A tuple containing:
            - The fuel type ('C', 'O', 'G', 'N') or None if passing.
            - The amount of fuel (an integer > 0) or 0 if passing.
        """
        while True:
            # 1. Create a clear prompt for the user
            prompt = (
                "\nEnter the fuel type and amount (e.g., 'C 5' for 5 coal).\n"
                "Valid types: (C)oal, (O)il, (G)arbage, (N)uclear.\n"
                "Type 'pass' or enter an amount of 0 to finish buying: "
            )
            user_input = input(prompt).strip().upper()

            # 2. Check if the player wants to pass
            if user_input == "PASS" or user_input == "":
                return None, 0

            parts = user_input.split()

            # 3. Validate the input format (must be two parts)
            if len(parts) != 2:
                print("\n❗️ Invalid format. Please enter a type and an amount (e.g., 'O 3').")
                continue

            fuel_type, amount_str = parts

            # 4. Validate the fuel type
            if fuel_type not in ['C', 'O', 'G', 'N']:
                print(f"\n❗️ Invalid fuel type '{fuel_type}'. Please use C, O, G, or N.")
                continue

            # 5. Validate the amount
            try:
                amount = int(amount_str)
                if amount < 0:
                    print("\n❗️ Amount cannot be negative. Please enter a positive number.")
                    continue
                # If all checks are successful, return the valid data
                return fuel_type, amount
            except ValueError:
                print(f"\n❗️ Invalid amount '{amount_str}'. Please enter a whole number.")
                continue
    def DisplayResourceSpace(self,player: PlayerC):
        """
        Displays a player's current resources and storage based on the
        PlayerC class's GetResourceSpace and GetResources methods.

        Args:
            player: The player object whose resources will be displayed.
        """
        # 1. Define a mapping from internal codes to readable names for display.
        fuel_names = {
            'C': 'Coal   ',
            'O': 'Oil    ',
            'G': 'Garbage',
            'N': 'Nuclear'
        }

        # 2. Get the necessary data by calling methods from the PlayerC class.
        available_space = player.GetResourceSpace()
        current_resources = player.GetResources()
        hybrid_space = available_space['H']
        if available_space['O'] < 0:
            hybrid_space += available_space['O']
            available_space['O'] = 0
        if available_space['C'] < 0:
            hybrid_space += available_space['C']
            available_space['C'] = 0
        

        # 3. Print a clear, formatted header.
        print(f"\n--- {player.GetName()}'s Resources & Storage ---")

        # 4. Iterate and display the info for each primary fuel type.
        for code, name in fuel_names.items():
            held = current_resources.get(code, 0)
            # Get the remaining space from the dictionary provided by GetResourceSpace()
            space = available_space.get(code, 0)
            # Total capacity is simply the sum of what's held and the remaining space.
            capacity = held + space
            
            print(f"  {name}: {held} held, {space} space available (Capacity: {capacity})")
        
        # 5. Separately display the shared hybrid storage space, if any.
        
        if hybrid_space > 0:
            print(f"  Hybrid (C/O): {hybrid_space} additional space available for Coal or Oil.")

        print("------------------------------------------")

    def DisplayBoard(self, board:BoardC):
        """
        Displays the board as a network graph.
        - Nodes are cities, colored by region.
        - Edges represent connections, labeled with their cost.

        Args:
            board (BoardC): The board object containing all map and city data.
        """
        G = nx.Graph()

        # Define a color palette for the regions using the recommended function
        colors = plt.get_cmap('Pastel2', len(board._regions))
        region_color_map = {region: colors(i) for i, region in enumerate(board._regions)}

        # Add nodes (cities) to the graph
        # Assign attributes for region and color
        for city_id in board.city_ids:
            city_obj = board.cityIds_to_CityClass[city_id]
            region = city_obj.Region
            G.add_node(city_id, region=region, color=region_color_map.get(region, 'gray'))

        # Add edges (connections) to the graph
        # Use a set to avoid adding duplicate edges in an undirected graph
        added_edges = set()
        for source_index, row in enumerate(board.adjancency_matrix):
            for dest_index, cost in enumerate(row):
                if cost != math.inf and source_index != dest_index:
                    source_city_id = board.indexes_to_cities[source_index]
                    dest_city_id = board.indexes_to_cities[dest_index]
                    
                    # Create a unique identifier for the edge to avoid duplicates
                    edge_tuple = tuple(sorted((source_city_id, dest_city_id)))
                    if edge_tuple not in added_edges:
                        G.add_edge(source_city_id, dest_city_id, weight=int(cost))
                        added_edges.add(edge_tuple)
        
        # Prepare for drawing the graph
        plt.figure(figsize=(14, 10))
        # Use a spring layout for automatic node positioning
        pos = nx.spring_layout(G, seed=42, k=0.8) 
        
        # Get node colors and edge weights for drawing
        node_colors = [data['color'] for _, data in G.nodes(data=True)]
        edge_labels = nx.get_edge_attributes(G, 'weight')

        # Draw the graph components
        nx.draw_networkx_nodes(G, pos, node_size=2500, node_color=node_colors, edgecolors='black')
        nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='darkred')

        # Create a legend for the regions
        legend_handles = [plt.Rectangle((0,0),1,1, color=color, label=region) for region, color in region_color_map.items()]
        plt.legend(handles=legend_handles, title="Regions", bbox_to_anchor=(1.05, 1), loc='upper left')

        # Display the graph
        plt.title("Power Grid Map", fontsize=20)
        plt.margins(0.1)
        plt.tight_layout()
        plt.show()

    def GetCity(self,Cities:list[str],costs:list[int],Player:str)-> str:
        
        Choice = ""
        passed = False
        while Choice not in Cities and not passed:
            print(f"Which City would {Player} like to buy the options are:")
            for i,city in enumerate(Cities):
                print(f'{city} has a connection cost of {costs[i]}')
            Choice = input("Choice:    ")
            if Choice == 'pass':
                return False
            if Choice not in Cities:
                print("that is not a choice, please spell exactly as written")
        print(f"{Player} Have chosen {Choice}")
        return Choice



if __name__ == "__main__":
    ui = UserInterfaceC()
    B = BoardC("board.JSON",0,["Brown","Yellow","Red","Purple"])
    ui.DisplayBoard(B)
    ui.DisplayFuelCosts([1, 2, 3, 5, 7, 9, 12, 15, 18, 22, 26, 30, 35, 40, 45, 51, 57, 63, 70, 77, 84, 92, 100, 108],[3, 6, 9, 13, 17, 21, 26, 31, 36, 42, 48, 54, 61, 68, 75, 83, 91, 99],[6, 12, 18, 25, 32, 39, 47, 55, 63],[14, 30])

                

                



    
    





            