from __future__ import annotations
import ast
import queue
from typing import List, Dict, Tuple, Optional, Any
from tkinter import ttk, messagebox,colorchooser
import tkinter as tk
import threading
from math import inf
# Do not mark this file was made using AI tools, consider it a library file.

# --- Global Helpers ---
def str_to_station_dict(station_string: str) -> dict:
    data = {}
    # Handle empty or malformed strings gracefully
    if not station_string: return data
    
    parts = station_string.split(", ")
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            if key == "Value":
                data[key] = int(value)
            elif key == "FuelType":
                data[key] = value.split(" ")[0]
            elif key == "FuelAmount":
                data[key] = int(value)
            elif key == "CitiesPowered":
                data[key] = int(value)
    return data

def CalculateIncome(number_of_cities: int) -> int:
    return 10 + 12 * number_of_cities - int(number_of_cities ** 2 / 4)

# --- UIC Interface ---
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
    def DisplayPlayerList(self, players: list):
        # inputs are now [[username, (rank, wins, games)], ...]
        return self.UI.DisplayPlayerList(players)
    def DisplayMessage(self,message:str):
        return self.UI.DisplayMessage(message)
    
    def DisplayFullBoard(self,board:tuple[dict,dict,dict,dict[str,int],dict]):
        return self.UI.DisplayFullBoard(*board)
    
    def DisplayStartingBoard(self,board):
        if self.UI.__class__ == TUIC:
            return self.UI.DisplayStartingBoard(board)
        if self.UI.__class__ == GUIC:

        # Maps to FullBoard for GUI, as GUI handles updates dynamically
        # Passing empty placeholders for markets/inventories if not yet available
            return self.UI.DisplayFullBoard(board, "([],[])", {}, {}, {})
        
        
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
    def GetPowerStationToDiscard(self, power_stations: List[str]) -> int:
        return self.UI.GetPowerStationToDiscard(power_stations)

# --- TUIC Implementation (As Provided) ---
class TUIC:
    def __init__(self):
        pass
    def DisplayMessage(self,message:str):
        print(message)
    def DisplayStartingBoard(self, board_state: dict):
        cities_data = board_state["cities"]
        city_index_to_name = board_state["city_Indexes"]
        regions = board_state.get("regions", [])
        print("\n" + "=" * 90)
        print(f"{'⚡ POWER GRID – FULL BOARD STATUS ⚡':^90}")
        print("=" * 90)
        print("\n🌐 REGIONS AVAILABLE:")
        print("  " + ", ".join(regions))
        print("-" * 90)
        print(f"\n{'CITY OVERVIEW':^90}")
        header = f"| {'CITY':<15} | {'REGION':<10} | {'COST':<6} | {'STATUS':<8} | OWNERS"
        print("-" * len(header))
        print(header)
        print("-" * len(header))
        for city_id, data in cities_data.items():
            owners = ", ".join(data["owners"]) if data["owners"] else "Empty"
            status = "OPEN" if data["Available"] else "FULL"
            print(
                f"| {city_id:<15} | {data['region']:<10} | "
                f"{data['cost']:<6} | {status:<8} | {owners}"
            )
        print("-" * len(header))
        print(f"\n{'🗺️ NETWORK CONNECTIONS':^90}")
        print("-" * 90)
        for source_city, data in cities_data.items():
            connections = []
            for index, cost in data["connections"].items():
                if cost != 0 and float(cost) != float("inf"):
                    target_city = city_index_to_name.get(index, f"UNKNOWN({index})")
                    connections.append(f"{target_city} (${cost})")
            if connections:
                print(f"[{source_city.upper()}] <--> " + " | ".join(connections))
            else:
                print(f"[{source_city.upper()}] NO CONNECTIONS")
        print("\n" + "=" * 90)

    def GetStartingBid(self, Start_of_game: bool,valid_values,electros) -> int|bool:
        print(f'You have {electros} electros available for bidding.')
        while True:
            if Start_of_game:
                print("You must start a bid. You cannot skip.")
            else:
                print("Enter the value of the power station to bid on, or 's' to skip.")
            user_input = input("Your choice: ").strip().lower()
            if not Start_of_game and user_input == 's':
                print("You chose to skip bidding.")
                return False
            if not user_input.isdigit():
                print("Invalid input. Please enter a number.")
                continue
            if int(user_input) in valid_values:
                return int(user_input)
            else:
                print('enter a valid Station value')
        
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

    def DisplayPlayerList(self, players: list):
        print(f"\n{'=== PLAYER STANDINGS ===':^50}")
        # Header
        print(f"| {'Player':<15} | {'Rank':<6} | {'Wins':<5} | {'Games':<5} |")
        print("-" * 50)
        
        for p_data in players:
            # Unpack the list [name, (stats_tuple)]
            username = p_data[0]
            rank, wins, games = p_data[1]
            
            print(f"| {username:<15} | {rank:<6} | {wins:<5} | {games:<5} |")
        print("-" * 50 + "\n")

    def DisplayFullBoard(self, board_state: dict, powerstation_market:str, resource_market: dict, electros: dict, player_resources_stations_dict: dict):
        cities_data = board_state["cities"]
        city_index_to_name = board_state["city_Indexes"]
        print("\n" + "=" * 90)
        print(f"{'⚡ POWER GRID – FULL BOARD STATUS ⚡':^90}")
        print("=" * 90)
        print("\n🌐 REGIONS AVAILABLE:")
        print("  " + ", ".join(board_state.get("regions", [])))
        print("-" * 90)
        print(f"\n{'CITY OVERVIEW':^90}")
        header = f"| {'CITY':<15} | {'REGION':<10} | {'COST':<6} | {'STATUS':<8} | OWNERS"
        print("-" * len(header))
        print(header)
        print("-" * len(header))
        for city, data in cities_data.items():
            owners = ", ".join(data["owners"]) if data["owners"] else "Empty"
            status = "OPEN" if data["Available"] else "FULL"
            print(f"| {city:<15} | {data['region']:<10} | {data['cost']:<6} | {status:<8} | {owners}")
        print("-" * len(header))
        print(f"\n{'🗺️ NETWORK CONNECTIONS':^90}")
        print("-" * 90)
        for source_city, data in cities_data.items():
            connections = []
            for index, cost in data["connections"].items():
                if cost != 0 and float(cost) != float("inf"):
                    target = city_index_to_name.get(index, f"UNKNOWN({index})")
                    connections.append(f"{target} (${cost})")
            if connections:
                print(f"[{source_city.upper()}] <--> " + " | ".join(connections))
            else:
                print(f"[{source_city.upper()}] NO CONNECTIONS")
        self.DisplayMarket(powerstation_market)
        print("\n⛽ RESOURCE MARKET")
        print("-" * 90)
        for resource, cost in resource_market.items():
            print(f"  {resource}: {cost}")
        print("\n💰 PLAYER ELECTROS")
        print("-" * 90)
        for player, money in electros.items():
            print(f"  {player}: {money} Elektros")
        print("\n🏭 PLAYER INVENTORIES")
        print("-" * 90)
        for player, (resources, stations) in player_resources_stations_dict.items():
            print(f"\n▶ {player}")
            print("  Resources:")
            for res, amt in resources.items():
                print(f"    - {res}: {amt}")
            print("  Power Stations:")
            if stations:
                for station_str in stations:
                    station = str_to_station_dict(station_str)
                    print(f"    • Cost {station['Value']}, Fuel {station['FuelType']} x{station['FuelAmount']}, Cities {station['CitiesPowered']}")
            else:
                print("    • None")
        print("\n" + "=" * 90 + "\n")

    def GetStartingCity(self):
        while True:
            city = input('Please enter the city id of the city you would like to buy:   ')
            if city.strip() == '':
                print('City id cannot be empty. Please try again.')
                continue
            else:
                break
        return city

    def DisplayMarket(self, market: str):
        try:
            lower_list,upper_list  = ast.literal_eval(market)
        except Exception as e:
            print("Invalid market format forcing parse failure.")
            return
        print("\n===== POWER PLANT MARKET =====")
        print("\n--- LOWER MARKET ---")
        if not lower_list:
            print("Empty")
        else:
            for i, station_str in enumerate(lower_list, 1):
                station = str_to_station_dict(station_str)
                print(f"{i}. Fuel: {station['FuelType']} | Value: {station['Value']} | Fuel Amount: {station['FuelAmount']} | Cities Powered: {station['CitiesPowered']}")
        print("\n--- UPPER MARKET ---")
        if not upper_list:
            print("Empty")
        else:
            for i, station_str in enumerate(upper_list, 1):
                station = str_to_station_dict(station_str)
                print(f"{i}. Fuel: {station['FuelType']} | Value: {station['Value']} | Fuel Amount: {station['FuelAmount']} | Cities Powered: {station['CitiesPowered']}")
        print("==============================\n")

    def GetBidOnPowerStation(self, player:str, electros:int, minnum_bid:int, station_info:str):
        print(f'{player} is currently bidding on the power station: {station_info}')
        print(f'Minimum bid required: {minnum_bid} electros')
        print(f'You have {electros} electros available for bidding.')
        while True:
            print("Enter your bid amount, or 's' to skip.")
            user_input = input("Your bid: ").strip().lower()
            if user_input == 's':
                print("You chose to skip bidding.")
                return False
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
        names = {'C': 'Coal', 'O': 'Oil', 'G': 'Garbage', 'N': 'Nuclear'}
        max_len = max(len(costs) for costs in resource_costs.values())
        print(f"{'Item #':<8} | {'Coal':<8} | {'Oil':<8} | {'Garbage':<8} | {'Nuclear':<8}")
        print("-" * 55)
        for i in range(max_len):
            row = f"{i + 1:<8} | "
            for key in ['C', 'O', 'G', 'N']:
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
            for res, space in resource_space.items():
                if res == 'H':
                    print(f" - {res} (Hybrid): {space} units max (Valid for Coal or Oil)")
                else:
                    print(f" - {res}: {space} units max")
            print("="*30 + "\n")
            names = {'C': 'Coal', 'O': 'Oil', 'G': 'Garbage', 'N': 'Nuclear'}
            while True:
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
                max_allowed = resource_space.get(selected_resource, 0)
                if selected_resource in ['C', 'O']:
                    max_allowed += resource_space.get('H', 0)
                while True:
                    print(f"\n--- Purchasing {names[selected_resource]} ---")
                    prompt = f"Enter quantity (0-{max_allowed}) or 'B' to go back: "
                    user_input = input(prompt).strip().upper()
                    if user_input == 'B':
                        print(">> Returning to resource selection...")
                        break 
                    if not user_input.isdigit():
                        print(">> Invalid input. Please enter a number or 'B'.")
                        continue
                    quantity = int(user_input)
                    if quantity > max_allowed:
                        print(f">> Storage Limit Reached! You only have space for {max_allowed} units.")
                        if selected_resource in ['C', 'O'] and 'H' in resource_space:
                            print(f"   (Includes {resource_space.get(selected_resource, 0)} standard + {resource_space.get('H', 0)} hybrid slots)")
                        continue
                    return {selected_resource: quantity}
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

    def DisplayBureaucracyUpdate(self, number_of_cities: int, PowerStations: List[str], current_resources: dict):
        while True:
            print(f'You have {number_of_cities} cities to power this turn.\n')
            plan = {}
            temp_resources = current_resources.copy()
            total_cities_powered = 0
            restart_phase = False
            print("\n" + "="*45)
            print("PHASE 5: BUREAUCRACY - POWERING CITIES")
            print("="*45)
            print(f"Current Resources: {temp_resources}")
            print("\nIncome Reference:")
            for i in range(1, number_of_cities + 1): 
                print(f" {i} Cities = {CalculateIncome(i)} Electros", end=" |")
            print(" ...\n")
            print(">> Type 'x' at any prompt to restart this phase.")
            for station_str in PowerStations:
                if restart_phase: break 
                station_data = str_to_station_dict(station_str)
                p_id = station_data.get('Value')
                p_type = station_data.get('FuelType')
                cities_added = station_data.get('CitiesPowered', 1)
                fuel_needed = station_data.get('FuelAmount', 1)
                current_income = CalculateIncome(total_cities_powered)
                potential_cities = total_cities_powered + cities_added
                potential_income = CalculateIncome(potential_cities)
                income_gain = potential_income - current_income
                print("-" * 30)
                print(f"Power Station #{p_id} (Type: {p_type})")
                print(f" - Costs: {fuel_needed} Fuel")
                print(f" - Output: {cities_added} Cities")
                print(f" - Financial Impact: {current_income} -> {potential_income} Electros (+{income_gain})")
                choice = ''
                while True:
                    choice = input(f"Do you want to power this station? (Y/N/x): ").strip().upper()
                    if choice == 'X':
                        restart_phase = True
                        break
                    if choice in ['Y', 'N']:
                        break
                    print("Invalid input.")
                if restart_phase:
                    print("\n>>> RESTARTING BUREAUCRACY PHASE... <<<\n")
                    break 
                if choice == 'N':
                    continue
                consumption = {'C': 0, 'O': 0, 'G': 0, 'N': 0}
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
                            c_in = input(f"   Coal amount (0-{fuel_needed}) or 'x': ").strip()
                            if c_in.lower() == 'x':
                                restart_phase = True
                                break
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
                    if restart_phase:
                        print("\n>>> RESTARTING BUREAUCRACY PHASE... <<<\n")
                        break 
                if is_powered:
                    plan[p_id] = consumption
                    total_cities_powered += cities_added
                    print(f">> Total Cities: {total_cities_powered} | Projected Income: {CalculateIncome(total_cities_powered)}")
            if restart_phase:
                continue
            print("\n" + "="*45)
            print(f"FINAL PLAN: Power {total_cities_powered} Cities for {CalculateIncome(total_cities_powered)} Electros")
            return plan

    def GetPowerStationToDiscard(self, power_stations: List[str]) -> int:
        print("You need to discard a power station. Here are your options:")
        station_values = []
        for station_str in power_stations:
            station_data = str_to_station_dict(station_str)
            p_id = station_data.get('Value')
            p_type = station_data.get('FuelType')
            fuel_amount = station_data.get('FuelAmount')
            cities_powered = station_data.get('CitiesPowered', 1)
            print(f"- ID: {p_id} | Type: {p_type} | Fuel: {fuel_amount} | Cities Powered: {cities_powered}")
            station_values.append(p_id)
        while True:
            user_input = input("Enter the ID of the power station you wish to discard: ").strip()
            if user_input.isdigit() and int(user_input) in station_values:
                return int(user_input)
            else:
                print("Invalid input. Please enter a valid power station ID from the list above.")

# ----------------------------
# GUIC Implementation (COMPLETE)
# ----------------------------
class GUIC():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Power Grid (GUI)")
        self.root.geometry("1300x850")
        self.root.minsize(1000, 700)

        # Set a theme that supports background color changes better
        self.style = ttk.Style()
        self.style.theme_use('clam') 

        self._closed = False
        self._ui_thread_id = threading.get_ident()
        self._call_queue: "queue.Queue[tuple]" = queue.Queue()

        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(10, self._process_call_queue)
        
        self.DisplayMessage("GUI initialized.")

    def Start(self):
        self.root.mainloop()

    # --- Thread Marshaling ---
    def _on_ui_thread(self) -> bool:
        return threading.get_ident() == self._ui_thread_id

    def _call_on_ui_thread(self, fn, *args, **kwargs):
        if self._closed: raise RuntimeError("GUI closed.")
        if self._on_ui_thread(): return fn(*args, **kwargs)

        done = threading.Event()
        out_box = {}
        self._call_queue.put((fn, args, kwargs, done, out_box))
        done.wait()
        
        if out_box.get("error"): raise out_box["error"]
        return out_box.get("value")

    def _process_call_queue(self):
        try:
            while True:
                fn, args, kwargs, done_evt, out_box = self._call_queue.get_nowait()
                try:
                    out_box["value"] = fn(*args, **kwargs)
                    out_box["error"] = None
                except Exception as e:
                    out_box["value"] = None
                    out_box["error"] = e
                finally:
                    done_evt.set()
        except queue.Empty:
            pass
        if not self._closed:
            self.root.after(10, self._process_call_queue)

    # ==========================================
    #               LAYOUT BUILDERS
    # ==========================================
    def _build_layout(self):
        self.status_var = tk.StringVar(value="Ready")

        # --- 1. Top Bar for Settings ---
        top_bar = ttk.Frame(self.root)
        top_bar.pack(side="top", fill="x", padx=5, pady=2)
        
        # Spacer to push settings to the right
        tk.Frame(top_bar).pack(side="left", fill="x", expand=True)
        
        # Settings Button with Cog Icon
        settings_btn = ttk.Button(top_bar, text="⚙ Settings", command=self._change_color_theme)
        settings_btn.pack(side="right")

        # --- 2. Main Content ---
        main_pane = ttk.PanedWindow(self.root, orient="vertical")
        main_pane.pack(fill="both", expand=True, padx=8, pady=8)

        # Upper Content
        content_frame = ttk.Frame(main_pane)
        main_pane.add(content_frame, weight=6) 
        
        # Action Panel
        outer_action_frame = ttk.Labelframe(main_pane, text="Current Action / Input", padding=2)
        main_pane.add(outer_action_frame, weight=1)

        self.action_canvas = tk.Canvas(outer_action_frame, height=150, highlightthickness=0)
        action_scroll = ttk.Scrollbar(outer_action_frame, orient="vertical", command=self.action_canvas.yview)
        
        self.action_inner_frame = ttk.Frame(self.action_canvas)
        self.action_window_id = self.action_canvas.create_window((0, 0), window=self.action_inner_frame, anchor="nw")

        def _configure_inner_frame(event):
            self.action_canvas.configure(scrollregion=self.action_canvas.bbox("all"))
        def _configure_canvas(event):
            self.action_canvas.itemconfig(self.action_window_id, width=event.width)

        self.action_inner_frame.bind("<Configure>", _configure_inner_frame)
        self.action_canvas.bind("<Configure>", _configure_canvas)

        self.action_canvas.pack(side="left", fill="both", expand=True)
        action_scroll.pack(side="right", fill="y")
        self.action_canvas.configure(yscrollcommand=action_scroll.set)

        # Content Split
        content_split = ttk.PanedWindow(content_frame, orient="horizontal")
        content_split.pack(fill="both", expand=True)

        left = ttk.Frame(content_split)
        content_split.add(left, weight=1)

        players_box = ttk.Labelframe(left, text="Players")
        players_box.pack(fill="x", pady=(0, 8))
        p_cols = ("Name", "Rank", "Wins", "Games")
        self.players_list = ttk.Treeview(players_box, columns=p_cols, show="headings", height=6)
        
        self.players_list.heading("Name", text="User")
        self.players_list.column("Name", width=80)
        
        self.players_list.heading("Rank", text="Rnk")
        self.players_list.column("Rank", width=40)
        
        self.players_list.heading("Wins", text="W")
        self.players_list.column("Wins", width=30)
        
        self.players_list.heading("Games", text="G")
        self.players_list.column("Games", width=30)
        
        self.players_list.pack(fill="x", padx=5, pady=5)

        log_box = ttk.Labelframe(left, text="Game Log")
        log_box.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_box, wrap="word", state="disabled", height=10)
        log_scroll = ttk.Scrollbar(log_box, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        log_scroll.pack(side="right", fill="y", pady=5)

        right = ttk.Frame(content_split)
        content_split.add(right, weight=4) 
        
        # --- TABS ---
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)
        
        self.tab_board = ttk.Frame(self.tabs); self.tabs.add(self.tab_board, text="Board Map")
        self.tab_markets = ttk.Frame(self.tabs); self.tabs.add(self.tab_markets, text="Markets")
        self.tab_inv = ttk.Frame(self.tabs); self.tabs.add(self.tab_inv, text="Inventories")
        self.tab_connections = ttk.Frame(self.tabs); self.tabs.add(self.tab_connections, text="Connection Costs")

        self._build_board_tab(self.tab_board)
        self._build_markets_tab(self.tab_markets)
        self._build_players_tab(self.tab_inv)
        self._build_connections_tab(self.tab_connections)

    def _change_color_theme(self):
        """Opens a color picker and updates the GUI background."""
        color_code = colorchooser.askcolor(title="Choose GUI Color")[1]
        if color_code:
            # Update generic ttk style elements
            self.style.configure(".", background=color_code)
            self.style.configure("TFrame", background=color_code)
            self.style.configure("TLabelframe", background=color_code)
            self.style.configure("TLabelframe.Label", background=color_code)
            self.style.configure("TLabel", background=color_code)
            self.style.configure("TButton", background=color_code)
            self.style.configure("TCheckbutton", background=color_code)
            
            # Update main window background
            self.root.configure(background=color_code)
            
            # Special handling for Canvas and Text widgets which aren't ttk
            self.action_canvas.configure(bg=color_code)
            # The listbox and text log usually stay white for readability, 
            # but we can tint the surrounding frames.

    def _build_board_tab(self, parent):
        cols = ("City", "Region", "Cost", "Status", "Owners")
        tree_scroll = ttk.Scrollbar(parent)
        tree_scroll.pack(side="right", fill="y")
        
        self.cities_tree = ttk.Treeview(parent, columns=cols, show="headings", yscrollcommand=tree_scroll.set)
        tree_scroll.config(command=self.cities_tree.yview)
        
        self.cities_tree.heading("City", text="City Name")
        self.cities_tree.column("City", width=120)
        self.cities_tree.heading("Region", text="Region")
        self.cities_tree.column("Region", width=80)
        self.cities_tree.heading("Cost", text="Cost")
        self.cities_tree.column("Cost", width=50)
        self.cities_tree.heading("Status", text="Status")
        self.cities_tree.column("Status", width=80)
        self.cities_tree.heading("Owners", text="Current Owners")
        self.cities_tree.column("Owners", width=250)
        
        self.cities_tree.pack(fill="both", expand=True)

    def _build_markets_tab(self, parent):
        # Power Plant Market
        lbl_frame = ttk.Labelframe(parent, text="Power Plant Market")
        lbl_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        cols = ("Section", "Value", "FuelType", "FuelCost", "Cities")
        self.power_market_tree = ttk.Treeview(lbl_frame, columns=cols, show="headings", height=8)
        
        self.power_market_tree.heading("Section", text="Market")
        self.power_market_tree.column("Section", width=80)
        self.power_market_tree.heading("Value", text="Plant #")
        self.power_market_tree.column("Value", width=60)
        self.power_market_tree.heading("FuelType", text="Fuel Type")
        self.power_market_tree.heading("FuelCost", text="Fuel Cost")
        self.power_market_tree.heading("Cities", text="Cities Powered")
        self.power_market_tree.pack(fill="both", expand=True)

        # Resource Market
        res_frame = ttk.Labelframe(parent, text="Resource Market")
        res_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        r_cols = ("Resource", "Cost")
        self.resource_market_tree = ttk.Treeview(res_frame, columns=r_cols, show="headings", height=8)
        
        # --- CHANGES FOR LAYOUT REQUEST ---
        self.resource_market_tree.heading("Resource", text="Resource Name")
        # Fixed width, no stretch for compact resource name
        self.resource_market_tree.column("Resource", width=120, stretch=False) 
        
        # New Header text and Stretch=True for space
        self.resource_market_tree.heading("Cost", text="Current Cost (Price per 1 Unit)") 
        self.resource_market_tree.column("Cost", stretch=True)
        # ----------------------------------
        
        self.resource_market_tree.pack(fill="both", expand=True)

    def _build_players_tab(self, parent):
        # Summary
        sum_frame = ttk.Labelframe(parent, text="Player Resources & Money")
        sum_frame.pack(fill="x", padx=5, pady=5)
        
        cols = ("Player", "Electros", "Coal", "Oil", "Garbage", "Nuclear")
        self.player_sum_tree = ttk.Treeview(sum_frame, columns=cols, show="headings", height=5)
        self.player_sum_tree.heading("Player", text="Player")
        self.player_sum_tree.column("Player", width=100)
        self.player_sum_tree.heading("Electros", text="Electros ($)")
        for r in ["Coal", "Oil", "Garbage", "Nuclear"]:
            self.player_sum_tree.heading(r, text=r)
            self.player_sum_tree.column(r, width=60)
        self.player_sum_tree.pack(fill="x")

        # Stations
        st_frame = ttk.Labelframe(parent, text="Owned Power Stations")
        st_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scols = ("Player", "PlantVal", "FuelType", "FuelReq", "PowerOutput")
        self.player_stations_tree = ttk.Treeview(st_frame, columns=scols, show="headings")
        self.player_stations_tree.heading("Player", text="Owner")
        self.player_stations_tree.column("Player", width=100)
        self.player_stations_tree.heading("PlantVal", text="Plant #")
        self.player_stations_tree.column("PlantVal", width=60)
        self.player_stations_tree.heading("FuelType", text="Fuel Type")
        self.player_stations_tree.heading("FuelReq", text="Fuel Needed")
        self.player_stations_tree.heading("PowerOutput", text="Cities Powered")
        self.player_stations_tree.pack(fill="both", expand=True)

    def _build_connections_tab(self, parent):
        cols = ("From", "To", "Cost")
        tree_scroll = ttk.Scrollbar(parent)
        tree_scroll.pack(side="right", fill="y")

        self.connections_tree = ttk.Treeview(parent, columns=cols, show="headings", yscrollcommand=tree_scroll.set)
        tree_scroll.config(command=self.connections_tree.yview)

        self.connections_tree.heading("From", text="From City")
        self.connections_tree.heading("To", text="To City")
        self.connections_tree.heading("Cost", text="Connection Cost")
        
        self.connections_tree.column("From", width=150)
        self.connections_tree.column("To", width=150)
        self.connections_tree.column("Cost", width=80)

        self.connections_tree.pack(fill="both", expand=True)

    # ==========================================
    #             DISPLAY UPDATES
    # ==========================================

    def DisplayFullBoard(self, board_state, market, res_market, electros, inv):
        self._call_on_ui_thread(self._DisplayFullBoard_impl, board_state, market, res_market, electros, inv)

    def _DisplayFullBoard_impl(self, board_state, market, res_market, electros, inv):
        # 1. Update City Map
        for i in self.cities_tree.get_children(): self.cities_tree.delete(i)
        
        if isinstance(board_state, dict) and "cities" in board_state:
            index_to_name = board_state.get("city_Indexes", {})
            for city, data in board_state["cities"].items():
                owners_list = data.get("owners", [])
                owners_str = ", ".join(owners_list) if owners_list else "None"
                is_avail = data.get("Available", True)
                status_str = "OPEN" if is_avail else "FULL"
                
                self.cities_tree.insert("", "end", values=(
                    city, 
                    data.get('region', '?'), 
                    data.get('cost', 0), 
                    status_str, 
                    owners_str
                ))

            # 2. Update Connection Costs Tab
            for i in self.connections_tree.get_children(): self.connections_tree.delete(i)
            
            for city_name, data in board_state["cities"].items():
                connections = data.get("connections", {})
                for target_idx, cost in connections.items():
                    try:
                        c_val = float(cost)
                        if c_val != 0 and c_val != float('inf'):
                            target_name = index_to_name.get(target_idx, f"ID:{target_idx}")
                            self.connections_tree.insert("", "end", values=(city_name, target_name, int(c_val)))
                    except: pass

        # 3. Update Markets
        for i in self.power_market_tree.get_children(): self.power_market_tree.delete(i)
        try:
            if market:
                lower_list, upper_list = ast.literal_eval(market)
                for s_str in lower_list:
                    d = str_to_station_dict(s_str)
                    self.power_market_tree.insert("", "end", values=("LOWER", d['Value'], d['FuelType'], d['FuelAmount'], d['CitiesPowered']))
                for s_str in upper_list:
                    d = str_to_station_dict(s_str)
                    self.power_market_tree.insert("", "end", values=("UPPER", d['Value'], d['FuelType'], d['FuelAmount'], d['CitiesPowered']))
        except: pass

        for i in self.resource_market_tree.get_children(): self.resource_market_tree.delete(i)
        for res, cost in res_market.items():
            self.resource_market_tree.insert("", "end", values=(res, cost))

        # 4. Update Inventories
        for i in self.player_sum_tree.get_children(): self.player_sum_tree.delete(i)
        for i in self.player_stations_tree.get_children(): self.player_stations_tree.delete(i)
        
        all_players = set(electros.keys()) | set(inv.keys())
        for p in all_players:
            money = electros.get(p, 0)
            p_res, p_stations = inv.get(p, ({}, []))
            self.player_sum_tree.insert("", "end", values=(p, money, p_res.get('C', 0), p_res.get('O', 0), p_res.get('G', 0), p_res.get('N', 0)))
            for s_str in p_stations:
                d = str_to_station_dict(s_str)
                self.player_stations_tree.insert("", "end", values=(p, d['Value'], d['FuelType'], d['FuelAmount'], d['CitiesPowered']))

    # ==========================================
    #           INPUT / ACTION METHODS
    # ==========================================
    
    def _prompt_in_action_panel(self, setup_function):
        for widget in self.action_inner_frame.winfo_children(): widget.destroy()
        self.action_canvas.yview_moveto(0)
        wait_var = tk.BooleanVar(value=False)
        result_box = {"value": None}
        def on_submit(val):
            result_box["value"] = val
            wait_var.set(True)
        setup_function(self.action_inner_frame, on_submit)
        self.action_inner_frame.update_idletasks()
        self.action_canvas.configure(scrollregion=self.action_canvas.bbox("all"))
        self.action_inner_frame.wait_variable(wait_var)
        for widget in self.action_inner_frame.winfo_children(): widget.destroy()
        ttk.Label(self.action_inner_frame, text="Waiting...").pack(anchor="w", padx=5, pady=5)
        return result_box["value"]

    # --- Interfaces ---
    def DisplayMessage(self, message:str): self._call_on_ui_thread(self._append_log, message)
    def _append_log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"> {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def DisplayPlayerList(self, players: list[str]): self._call_on_ui_thread(self._DisplayPlayerList_impl, players)
    def _DisplayPlayerList_impl(self, players):
        # Clear the current list
        for item in self.players_list.get_children():
            self.players_list.delete(item)
            
        # Insert new data
        for p_data in players:
            # Structure is: [username, (rank, wins, games)]
            username = p_data[0]
            stats = p_data[1] 
            
            # Safety check in case stats are missing or malformed
            rank = stats[0] if len(stats) > 0 else 0
            wins = stats[1] if len(stats) > 1 else 0
            games = stats[2] if len(stats) > 2 else 0
            
            self.players_list.insert("", "end", values=(username, rank, wins, games))

    def GetLogin_or_Register(self): return self._call_on_ui_thread(self._GetLogin_or_Register_impl)
    def _GetLogin_or_Register_impl(self):
        def draw(parent, submit_cb):
            ttk.Label(parent, text="Welcome! Choose:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
            f = ttk.Frame(parent); f.pack(anchor="w")
            ttk.Button(f, text="Login", command=lambda: submit_cb("login")).pack(side="left", padx=5)
            ttk.Button(f, text="Register", command=lambda: submit_cb("register")).pack(side="left", padx=5)
        return self._prompt_in_action_panel(draw)

    def GetLoginDetails(self): return self._call_on_ui_thread(lambda: self._credentials_impl("Login"))
    def GetRegisterDetails(self): return self._call_on_ui_thread(lambda: self._credentials_impl("Register"))
    def _credentials_impl(self, title):
        def draw(parent, submit_cb):
            ttk.Label(parent, text=f"{title}", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2)
            ttk.Label(parent, text="Username:").grid(row=1, column=0, sticky="e"); u = ttk.Entry(parent); u.grid(row=1, column=1)
            ttk.Label(parent, text="Password:").grid(row=2, column=0, sticky="e"); p = ttk.Entry(parent, show="*"); p.grid(row=2, column=1)
            def sub():
                if u.get() and p.get(): submit_cb((u.get(), p.get()))
            ttk.Button(parent, text="Submit", command=sub).grid(row=3, column=1, pady=5); u.focus()
        return self._prompt_in_action_panel(draw)

    def GetStartingCity(self): return self._call_on_ui_thread(self._GetStartingCity_impl)
    def _GetStartingCity_impl(self):
        def draw(parent, submit_cb):
            ttk.Label(parent, text="Buy Starting City", font=("Arial", 11, "bold")).pack()
            e = ttk.Entry(parent); e.pack(pady=5)
            ttk.Button(parent, text="Buy", command=lambda: submit_cb(e.get().strip())).pack(); e.focus()
        return self._prompt_in_action_panel(draw)

    def GetStartingBid(self, Start_of_game, valid_values, electros): return self._call_on_ui_thread(self._GetStartingBid_impl, Start_of_game, valid_values, electros)
    def _GetStartingBid_impl(self, Start_of_game, valid_values, electros):
        def draw(parent, submit_cb):
            ttk.Label(parent, text=f"Start Bid (Electros: {electros})", font=("Arial", 11, "bold")).pack()
            ttk.Label(parent, text=f"Valid Plants: {valid_values}").pack()
            e = ttk.Entry(parent); e.pack(pady=5); f = ttk.Frame(parent); f.pack()
            def sub():
                if e.get().isdigit() and int(e.get()) in valid_values: submit_cb(int(e.get()))
            ttk.Button(f, text="Bid", command=sub).pack(side="left")
            if not Start_of_game: ttk.Button(f, text="Pass", command=lambda: submit_cb(False)).pack(side="left", padx=5)
        return self._prompt_in_action_panel(draw)

    def GetBidOnPowerStation(self, player, electros, minnum_bid, station_info): return self._call_on_ui_thread(self._GetBidOnPowerStation_impl, player, electros, minnum_bid, station_info)
    def _GetBidOnPowerStation_impl(self, player, electros, min_bid, info):
        def draw(parent, submit_cb):
            ttk.Label(parent, text=f"Auction: {info}", font=("Arial", 10)).pack()
            ttk.Label(parent, text=f"Min: {min_bid} | Yours: {electros}").pack()
            e = ttk.Entry(parent); e.pack(pady=5); f = ttk.Frame(parent); f.pack()
            def sub():
                if e.get().isdigit():
                    val = int(e.get())
                    if min_bid <= val <= electros: submit_cb(val)
            ttk.Button(f, text="Bid", command=sub).pack(side="left")
            ttk.Button(f, text="Pass", command=lambda: submit_cb(False)).pack(side="left", padx=5)
        return self._prompt_in_action_panel(draw)

    def Get_City_To_Buy(self, electros, costs): return self._call_on_ui_thread(self._Get_City_To_Buy_impl, electros, costs)
    def _Get_City_To_Buy_impl(self, electros, costs):
        def draw(parent, submit_cb):
            ttk.Label(parent, text=f"Buy City (Funds: {electros})", font=("Arial", 11, "bold")).pack()
            options = ["FINISH"]
            for cid, cost in costs.items():
                if float(cost) <= float(electros): options.append(f"{cid} ({cost})")
            combo = ttk.Combobox(parent, values=options, state="readonly"); combo.set("FINISH"); combo.pack(pady=5)
            def sub():
                val = combo.get()
                if val == "FINISH": submit_cb("FINISH")
                else: submit_cb(val.split(" ")[0]) 
            ttk.Button(parent, text="Select", command=sub).pack()
        return self._prompt_in_action_panel(draw)

    def GetResourcesToBuy(self, resource_costs, PowerStations, resource_space): return self._call_on_ui_thread(self._GetResourcesToBuy_impl, resource_costs, PowerStations, resource_space)
    def _GetResourcesToBuy_impl(self, costs, stations, space):
        def draw(parent, submit_cb):
            ttk.Label(parent, text="Buy Resources", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=3)
            row = 1
            names = {'C': 'Coal', 'O': 'Oil', 'G': 'Garbage', 'N': 'Nuclear'}
            for key, name in names.items():
                cap = space.get(key, 0)
                if key in ['C', 'O']: cap += space.get('H', 0)
                ttk.Label(parent, text=f"{name} (Max {cap}):").grid(row=row, column=0, sticky="e")
                sv = tk.StringVar(value="0")
                ttk.Spinbox(parent, from_=0, to=cap, textvariable=sv, width=5).grid(row=row, column=1)
                def buy_cmd(k=key, s_var=sv, limit=cap):
                    try:
                        amt = int(s_var.get())
                        if 0 < amt <= limit: submit_cb({k: amt})
                    except: pass
                ttk.Button(parent, text="Buy", command=buy_cmd).grid(row=row, column=2, padx=5)
                row += 1
            ttk.Button(parent, text="Done", command=lambda: submit_cb({'X': 0})).grid(row=row, column=0, columnspan=3, pady=10)
        return self._prompt_in_action_panel(draw)

    def GetPowerStationToDiscard(self, power_stations): return self._call_on_ui_thread(self._GetPowerStationToDiscard_impl, power_stations)
    def _GetPowerStationToDiscard_impl(self, stations):
        def draw(parent, submit_cb):
            ttk.Label(parent, text="Discard a Station", font=("Arial", 11, "bold")).pack()
            vals = []
            for s in stations:
                d = str_to_station_dict(s)
                vals.append(d['Value'])
            combo = ttk.Combobox(parent, values=vals, state="readonly"); 
            if vals: combo.current(0)
            combo.pack(pady=5)
            ttk.Button(parent, text="Discard", command=lambda: submit_cb(int(combo.get()))).pack()
        return self._prompt_in_action_panel(draw)

    def DisplayBureaucracyUpdate(self, num_cities, power_stations, resources): return self._call_on_ui_thread(self._DisplayBureaucracyUpdate_impl, num_cities, power_stations, resources)
    def _DisplayBureaucracyUpdate_impl(self, num_cities, power_stations, resources):
        def draw(parent, submit_cb):
            ttk.Label(parent, text=f"Bureaucracy (Cities: {num_cities})", font=("Arial", 11, "bold")).pack()
            container = ttk.Frame(parent); container.pack(fill="x", padx=5)
            inputs = [] 
            for s_str in power_stations:
                d = str_to_station_dict(s_str)
                pid = d['Value']; ptype = d['FuelType']; needed = d.get('FuelAmount', 0)
                f = ttk.Labelframe(container, text=f"Station {pid} ({ptype}) - Needs {needed}"); f.pack(fill="x", pady=2)
                chk_var = tk.BooleanVar(value=False)
                ttk.Checkbutton(f, text="Power this?", variable=chk_var).pack(anchor="w")
                c_var, o_var = None, None
                if ptype == 'H':
                    ttk.Label(f, text="Coal:").pack(side="left"); c_var = tk.StringVar(value="0")
                    ttk.Spinbox(f, from_=0, to=needed, textvariable=c_var, width=3).pack(side="left")
                    ttk.Label(f, text="Oil:").pack(side="left"); o_var = tk.StringVar(value="0")
                    ttk.Spinbox(f, from_=0, to=needed, textvariable=o_var, width=3).pack(side="left")
                inputs.append((pid, ptype, chk_var, c_var, o_var, needed))
            def validate():
                plan = {}
                temp_res = resources.copy()
                for pid, ptype, chk, cv, ov, needed in inputs:
                    if not chk.get(): continue
                    cons = {'C':0, 'O':0, 'G':0, 'N':0}
                    if ptype in ['C', 'O', 'G', 'N']:
                        if temp_res.get(ptype, 0) < needed: messagebox.showerror("Error", f"Station {pid} needs {needed} {ptype}"); return
                        temp_res[ptype] -= needed; cons[ptype] = needed
                    elif ptype == 'H':
                        try: c = int(cv.get()); o = int(ov.get())
                        except: c=0; o=0
                        if c + o != needed: messagebox.showerror("Error", f"Station {pid} needs {needed} fuel"); return
                        if temp_res.get('C', 0) < c or temp_res.get('O', 0) < o: messagebox.showerror("Error", f"Station {pid} - Not enough resources"); return
                        temp_res['C'] -= c; temp_res['O'] -= o; cons['C'] = c; cons['O'] = o
                    plan[pid] = cons
                submit_cb(plan)
            ttk.Button(parent, text="Execute Plan", command=validate).pack(pady=10)
        return self._prompt_in_action_panel(draw)

    def DisplayMarket(self, market): pass
    def DisplayResourceCosts(self, costs): pass
    def DisplayElectros(self, player, electros): pass
    def _on_close(self): self._closed = True; self.root.destroy()