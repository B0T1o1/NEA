from math import inf
import math
from typing import List
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
    def DisplayMarket(self,market):
        return self.UI.DisplayMarket(market)
    def GetStartingBid(self, Start_of_game: bool,valid_values,electros):
        return self.UI.GetStartingBid(Start_of_game,valid_values,electros)
    def DisplayElectros(self,player,electros):
        return self.UI.DisplayElectros(player,electros)
    def GetBidOnPowerStation(self,player,electros,minnum_bid,station_info):
        return self.UI.GetBidOnPowerStation(player,electros,  minnum_bid, station_info )
    def DisplayResourceCosts(self,resource_costs: dict[str, list[int]]):
        return self.UI.DisplayResourceCosts(resource_costs)
    def GetResourcesToBuy(self,resource_costs: dict[str, list[int]],PowerStations: List[int],resource_space: dict[str,int]) -> dict[str,int]:
        return self.UI.GetResourcesToBuy(resource_costs,PowerStations,resource_space)
    def Get_City_To_Buy(self, electros, costs):
        return self.UI.Get_City_To_Buy(electros, costs)
    def DisplayBureaucracyUpdate(self,number_of_cities:int,power_stations:List[str],resources:dict):
        return self.UI.DisplayBureaucracyUpdate(number_of_cities,power_stations,resources)
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
                
                # logic: Ensure cost is not Infinite (math.inf) and not a self-loop (0)
                if float(cost) != float('inf') and cost != 0: 
                    # Translate the index back to the city name
                    target_city = city_index_to_name.get(index, f"UNKNOWN INDEX {index}")
                    connections.append(f"{target_city} (${cost})")
            
            # Join connections with a nice arrow
            if connections:
                conn_str = "  <-->  ".join(connections)
                print(f"[{source_city.upper()}] connects to:  {conn_str}")
            else:
                print(f"[{source_city.upper()}] HAS NO EXTERNAL CONNECTIONS")
        
        print("\n" + "="*80 + "\n")

    def GetStartingCity(self):
        while True:
            city = input('Please enter the city id of the city you would like to buy:   ')
            if city.strip() == '':
                print('City id cannot be empty. Please try again.')
                continue
            else:
                break
        return city
    

    def DisplayMarket(self, market):
        print(market)

    def GetStartingBid(self, Start_of_game: bool,valid_values,electros):
        """
        Handles the starting bid selection for a player.

        Returns:
            PowerStationC if a station is selected
            None if the player skips (when allowed)
        """
        print(f'You have {electros} electros available for bidding.')

        while True:
            if Start_of_game:
                print("You must start a bid. You cannot skip.")
            else:
                print("Enter the value of the power station to bid on, or 's' to skip.")

            user_input = input("Your choice: ").strip().lower()

            # Skip logic (only allowed after start of game)
            if not Start_of_game and user_input == 's':
                print("You chose to skip bidding.")
                return None

            # Validate numeric input
            if not user_input.isdigit():
                print("Invalid input. Please enter a number.")
                continue
            if int(user_input) in valid_values:
                return int(user_input)
            else:
                print('enter a valid Station value')

    def GetBidOnPowerStation(self, player:str, electros:int, minnum_bid:int, station_info:str):
        print(f'{player} is currently bidding on the power station: {station_info}')
        print(f'Minimum bid required: {minnum_bid} electros')
        print(f'You have {electros} electros available for bidding.')

        while True:
            print("Enter your bid amount, or 's' to skip.")

            user_input = input("Your bid: ").strip().lower()

            # Skip logic
            if user_input == 's':
                print("You chose to skip bidding.")
                return False

            # Validate numeric input
            if not user_input.isdigit():
                print("Invalid input. Please enter a number.")
                continue
            bid_amount = int(user_input)
            if bid_amount >= minnum_bid and bid_amount <= electros:
                return bid_amount
            else:
                print(f'Please enter a bid between {minnum_bid} and {electros} electros.')

    def DisplayElectros(self, player, electros):
        print(f'{player} has {electros} electros')

    def DisplayResourceCosts(self,resource_costs: dict[str, list[int]]):
        """
        Takes the dictionary of costs and displays them in a formatted table.
        """
        # Mapping keys to friendly names
        names = {'C': 'Coal', 'O': 'Oil', 'G': 'Garbage', 'N': 'Nuclear'}
        
        # Determine the maximum number of items to ensure the table covers all rows
        max_len = max(len(costs) for costs in resource_costs.values())

        # Print Header
        print(f"{'Item #':<8} | {'Coal':<8} | {'Oil':<8} | {'Garbage':<8} | {'Nuclear':<8}")
        print("-" * 55)

        # Print Rows
        for i in range(max_len):
            row = f"{i + 1:<8} | "
            for key in ['C', 'O', 'G', 'N']:
                # Handle cases where one resource list might be shorter than others
                if i < len(resource_costs[key]):
                    row += f"{resource_costs[key][i]:<8} | "
                else:
                    row += f"{'-':<8} | "
            print(row)

    def GetResourcesToBuy(self, resource_costs: dict[str, list[int]], PowerStations: list[str], resource_space: dict[str, int]) -> dict[str, int]:
            print("\n" + "="*30)
            print("CURRENT RESOURCE MARKET")
            self.DisplayResourceCosts(resource_costs)
            
            print(f"\nYour Power Stations: {PowerStations}")
            print("Available Storage Space:")
            
            # Display logic helps user understand where H applies
            for res, space in resource_space.items():
                if res == 'H':
                    print(f" - {res} (Hybrid): {space} units max (Valid for Coal or Oil)")
                else:
                    print(f" - {res}: {space} units max")
            print("="*30 + "\n")

            names = {'C': 'Coal', 'O': 'Oil', 'G': 'Garbage', 'N': 'Nuclear'}
            
            # MAIN LOOP: Allows returning here if the user wants to "go back"
            while True:
                # Step 1: Select the Resource Type
                selected_resource = None
                while True:
                    user_choice = input("Which resource would you like to buy? (C/O/G/N) or 'X' to cancel: ").strip().upper()
                    
                    if user_choice == 'X':
                        return {'X': 0} 
                    
                    if user_choice in names:
                        selected_resource = user_choice
                        break
                    else:
                        print(">> Invalid selection. Please choose C, O, G, or N.")

                # Step 2: Select the Quantity
                # --- NEW LOGIC START ---
                # Base capacity for the specific resource
                max_allowed = resource_space.get(selected_resource, 0)

                # If the resource is Coal or Oil, add the Hybrid capacity
                if selected_resource in ['C', 'O']:
                    max_allowed += resource_space.get('H', 0)
                # --- NEW LOGIC END ---
                
                while True:
                    print(f"\n--- Purchasing {names[selected_resource]} ---")
                    prompt = f"Enter quantity (0-{max_allowed}) or 'B' to go back: "
                    user_input = input(prompt).strip().upper()

                    # Handle "Go Back" option
                    if user_input == 'B':
                        print(">> Returning to resource selection...")
                        break # This breaks the Quantity loop, but stays in the Main loop

                    if not user_input.isdigit():
                        print(">> Invalid input. Please enter a number or 'B'.")
                        continue
                    
                    quantity = int(user_input)

                    if quantity > max_allowed:
                        print(f">> Storage Limit Reached! You only have space for {max_allowed} units.")
                        # Optional: Explain why for Hybrid users
                        if selected_resource in ['C', 'O'] and 'H' in resource_space:
                            print(f"   (Includes {resource_space.get(selected_resource, 0)} standard + {resource_space.get('H', 0)} hybrid slots)")
                        continue
                    
                    # If everything is valid, return the result
                    return {selected_resource: quantity}

                # If the Quantity loop was "broken" by 'B', the code continues here.
                # Since it's inside the outer 'while True', it restarts Step 1.
                continue
            
    def Get_City_To_Buy(self, electros, costs):
        print(f'You have {electros} electros available to buy a city.')
        print('City Costs:')
        for city_id, cost in costs.items():
            print(f'- {city_id}: {cost} electros')
        
        while True:
            city_id = input("Enter the city ID you wish to buy, or 'FINISH' to end buying: ").strip()
            if city_id == 'FINISH':
                return 'FINISH'
            if city_id in costs:
                if costs[city_id] <= electros:
                    return city_id
                else:
                    print(f'You do not have enough electros to buy {city_id}. It costs {costs[city_id]} electros.')
            else:
                print('Invalid city ID. Please choose from the list above or enter FINISH to end buying.')

    def DisplayBureaucracyUpdate(self,number_of_cities:int,PowerStations:List[str],current_resources:dict):
        """
        Interactively asks the user which power stations to run.
        PowerStations argument is now a list of strings (e.g., "Value=10, FuelType=C...").
        Returns: { Station_Value_ID: { 'C': amount, 'O': amount ... } }
        """
        print(f'You have {number_of_cities} cities to power this turn.\n')
        plan = {}
        temp_resources = current_resources.copy()
        total_cities_powered = 0

        print("\n" + "="*45)
        print("PHASE 5: BUREAUCRACY - POWERING CITIES")
        print("="*45)
        print(f"Current Resources: {temp_resources}")
        
        # Optional: Print a quick reference guide for the user
        print("\nIncome Reference:")
        for i in range(1, 8): # Just showing first 7 as an example
            print(f" {i} Cities = {CalculateIncome(i)} Electros", end=" |")
        print(" ...\n")

        for station_str in PowerStations:
            # 1. Parse string to dict
            station_data = str_to_station_dict(station_str)
            
            p_id = station_data.get('Value')
            p_type = station_data.get('FuelType')
            cities_added = station_data.get('CitiesPowered', 1)
            fuel_needed = station_data.get('CitiesPowered', 1) # Assuming cost = cities count default

            # Calculate "What If" scenarios
            current_income = CalculateIncome(total_cities_powered)
            potential_cities = total_cities_powered + cities_added
            potential_income = CalculateIncome(potential_cities)
            income_gain = potential_income - current_income

            print("-" * 30)
            print(f"Power Station #{p_id} (Type: {p_type})")
            print(f" - Costs: {fuel_needed} Fuel")
            print(f" - Output: {cities_added} Cities")
            print(f" - Financial Impact: {current_income} -> {potential_income} Electros (+{income_gain})")

            # 2. Ask User
            while True:
                choice = input(f"Do you want to power this station? (Y/N): ").strip().upper()
                if choice in ['Y', 'N']:
                    break
                print("Invalid input.")

            if choice == 'N':
                continue

            # 3. Determine Fuel Mix
            consumption = {'C': 0, 'O': 0, 'G': 0, 'N': 0}
            
            # Helper boolean to check if we successfully powered it
            is_powered = False 

            if p_type == 'R':
                is_powered = True
                print(">> Station powered (Renewable).")

            elif p_type in ['C', 'O', 'G', 'N']:
                if temp_resources.get(p_type, 0) >= fuel_needed:
                    consumption[p_type] = fuel_needed
                    temp_resources[p_type] -= fuel_needed
                    is_powered = True
                    print(f">> Powered using {fuel_needed} {p_type}.")
                else:
                    print(f">> Not enough {p_type}!")
            
            elif p_type == 'H':
                print(f"   (Available: {temp_resources.get('C', 0)} Coal, {temp_resources.get('O', 0)} Oil)")
                while True:
                    try:
                        c_in = input(f"   Coal amount (0-{fuel_needed}): ").strip()
                        if not c_in.isdigit(): continue
                        c_amt = int(c_in)
                        o_amt = fuel_needed - c_amt
                        
                        if c_amt < 0 or c_amt > fuel_needed: 
                            print("   >> Invalid amount."); continue
                        if temp_resources.get('C', 0) < c_amt: 
                            print("   >> Not enough Coal."); continue
                        if temp_resources.get('O', 0) < o_amt: 
                            print("   >> Not enough Oil."); continue

                        consumption['C'] = c_amt
                        consumption['O'] = o_amt
                        temp_resources['C'] = temp_resources.get('C', 0) - c_amt
                        temp_resources['O'] = temp_resources.get('O', 0) - o_amt
                        is_powered = True
                        print(f">> Hybrid powered ({c_amt} C / {o_amt} O).")
                        break
                    except ValueError: pass

            # 4. Finalize
            if is_powered:
                plan[p_id] = consumption
                total_cities_powered += cities_added
                print(f">> Total Cities: {total_cities_powered} | Projected Income: {CalculateIncome(total_cities_powered)}")

        print("\n" + "="*45)
        print(f"FINAL PLAN: Power {total_cities_powered} Cities for {CalculateIncome(total_cities_powered)} Electros")
        return plan

class GUIC(UIC):
    pass

def str_to_station_dict(station_string: str) -> dict:
    """
    Unpacks a string formatted by station_to_str back into a dictionary.
    """
    data = {}
    
    # Split by the main delimiter ", "
    parts = station_string.split(", ")
    
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            
            # Clean and Convert Data Types
            if key == "Value":
                data[key] = int(value)
            elif key == "FuelType":
                # Removes the extra text in brackets, e.g. "C (Coal)" -> "C"
                data[key] = value.split(" ")[0]
            elif key == "FuelAmount":
                data[key] = int(value)
            elif key == "CitiesPowered":
                data[key] = int(value)
                
    return data
def CalculateIncome(self, number_of_cities: int) -> int:
        """
        Calculates income based on the number of cities a player powers.
        """
        # Formula: 10 + 12n - floor(n^2 / 4)
        return 10 + 12 * number_of_cities - int(number_of_cities ** 2 / 4)