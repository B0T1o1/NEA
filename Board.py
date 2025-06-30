
import json
class Board:
    def __init__(self,filename):
        file = open(filename,'r')
        self.map = json.load(file)
        print(din)
Board('board.JSON')