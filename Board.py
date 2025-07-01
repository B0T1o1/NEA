from UI import UserInterface
import json
class Board:
    def __init__(self,filename:str,UI):
        try:
            file = open(filename,'r')
        except FileNotFoundError:
            print('Sorry the board file was not found, ensure you have downloaded all files')
        self.map = json.load(file)['map_name']

Board('board.JSON',UserInterface)