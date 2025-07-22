class R_Market:
    def __init__(self):
        self.Coal = 24
        self.Oil = 18
        self.Garbage = 9 
        self.Nuclear = 2

    def AddCoal(self,Quantity):
        self.Coal += Quantity
        if self.Coal > 24:
            self.Coal = 24

    def AddOil(self,Quantity):
        self.Oil += Quantity
        if self.Oil > 24:
            self.Oil = 24

    def AddGarbage(self,Quantity):
        self.Garbage += Quantity
        if self.Garbage > 24:
            self.Garbage = 24

    def AddNuclear(self,Quantity):
        self.Garbage += Quantity
        if self.Garbage > 12:
            self.Garbage = 12

    def BuyCoal(self,Quantity):
        Cost  = 0
        if self.Coal >= Quantity:
            while Quantity != 0:
                Cost += 8 - ((self.Coal - 1)// 3)
                self.Coal -= 1
                Quantity -= 1

            return Cost
        else:
            # TODO raise ui error 
            print('Not enough coal')
    
    def BuyOil(self,Quantity):
        Cost  = 0
        if self.Oil >= Quantity:
            while Quantity != 0:
                Cost += 8 - ((self.Oil - 1)// 3)
                self.Coal -= 1
                Quantity -= 1

            return Cost
        else:
            # TODO raise ui error 
            print('Not enough Oil')

    def BuyGarbage(self,Quantity):
        Cost  = 0
        if self.Garbage >= Quantity:
            while Quantity != 0:
                Cost += 8 - ((self.Garbage - 1)// 3)
                self.Garbage -= 1
                Quantity -= 1

            return Cost
        else:
            # TODO raise ui error 
            print('Not enough Garbage')

    def BuyNuclear(self,Quanitity):
        Cost  = 0
        if self.Nuclear >= Quantity:
            while Quantity != 0:
                if self.Nuclear > 4:
                    Cost += 12 - self.Nuclear
                else:
                    Cost += 10 + ((4 - self.Nuclear) * 2 )
                self.Nuclear -= 1
                Quantity -= 1
            return Cost
        else:
            # TODO raise ui error 
            print('Not enough Garbage')

            

    