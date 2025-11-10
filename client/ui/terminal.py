from server.gamelogic import PowerStation
from uis import UIC
class TerminalUIC(UIC):
    def __init__(self,player_num):
        self.__player_num = player_num
        self.__player_name = ''

    def mark_player_turn(self):
        if self.__player_name:
            print('#'*10 + self.__player_name + '#'*10)
        else:
            print('#'*10 + self.__player_num + '#'*10)

    def display_message(self, message: str):
        print(message)

    def get_user_input(self, prompt: str) -> str:
        while True:
            user_input = input(prompt).strip()
            if user_input.isalnum():
                return user_input
            print("Invalid input. Please enter alphanumeric characters only.")

    def get_number_input(self, prompt: str) -> int:
        while True:
            try:
                return int(input(prompt))
            except ValueError:
                print("Please enter a valid number.")

    def set_up_game(self) -> tuple[int, list[str]]:
        self.mark_player_turn()
        self.display_message("Setting up the game in terminal UI...")
        num_players = self.get_number_input("How many players? ")
        self.display_message(f"Number of players set to: {num_players}")
        players = []
        for i in range(num_players):
            player_name = self.get_user_input(f"Enter name for player {i + 1}: ")
            players.append(player_name)
            self.display_message(f"Player {i + 1} name set to: {player_name}")
        return (num_players, players)
    
    def display_PS_market(self, market):
        self.display_message("Current Power Station Market:")
        for ps in market:
            self.display_message(f"- {ps}")
