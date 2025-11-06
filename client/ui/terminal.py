
class TerminalUIC:
    def __init__(self):
        pass

    def display_message(self, message: str):
        print(message)

    def get_user_input(self, prompt: str) -> str:
        return input(prompt)
    
    def get_number_input(self, prompt: str) -> int:
        while True:
            try:
                return int(input(prompt))
            except ValueError:
                print("Please enter a valid number.")
    
    
    
    def set_up_game(self):
        self.display_message("Setting up the game in terminal UI...")
        num_players = self.get_number_input("How many players? ")
        self.display_message(f"Number of players set to: {num_players}")
        for i in range(num_players):
            player_name = self.get_user_input(f"Enter name for player {i + 1}: ")
            self.display_message(f"Player {i + 1} name set to: {player_name}")
        