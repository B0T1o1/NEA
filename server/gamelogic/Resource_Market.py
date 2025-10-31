class R_Market:
    def __init__(self):
        self.Coal = 24
        self.Oil = 18
        self.Garbage = 9 
        self.Nuclear = 2

    def Buy_Resource(self,resource_type,quantity):
        types_buy_function = {'C':self.BuyCoal, 'O':self.BuyOil, 'G':self.BuyGarbage, 'N':self.BuyNuclear}
        return types_buy_function[resource_type](quantity)

    def Add_Resource(self,resource_type,quantity):
        types_add_function = {'C':self.AddCoal, 'O':self.AddOil, 'G':self.AddGarbage, 'N':self.AddNuclear}
        types_add_function[resource_type](quantity)

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
        self.Nuclear += Quantity
        if self.Nuclear > 12:
            self.Nuclear = 12

    def GetCostOfCoal(self) -> list[int]:
        coal = self.Coal
        Quantity = coal
        costs:list[int] = []
        Cost = 0
        while Quantity != 0:
                Cost += 8 - ((coal - 1)// 3)
                coal -= 1
                Quantity -= 1
                costs.append(Cost)
        return costs
    
    def GetCostOfOil(self) -> list[int]:
        Oil = self.Oil
        Quantity = Oil
        costs:list[int] = []
        Cost = 0
        while Quantity != 0: 
                Cost += 8 - ((Oil - 1)// 3)
                Oil -= 1
                Quantity -= 1
                costs.append(Cost)
        return costs
    
    def GetCostOfGarbage(self) -> list[int]:
        Garbage = self.Garbage
        Quantity = Garbage
        costs:list[int] = []
        Cost = 0
        while Quantity != 0:
                Cost += 8 - ((Garbage - 1)// 3)
                Garbage -= 1
                Quantity -= 1
                costs.append(Cost)
        return costs
    
    def GetCostOfNuclear(self) -> list[int]:
        Nuclear = self.Nuclear
        Quantity = Nuclear
        costs:list[int] = []
        Cost = 0
        while Quantity != 0:
            if Nuclear > 4:
                Cost += 12 - Nuclear
            else:
                Cost += 10 + ((4 - Nuclear) * 2 )
            Nuclear -= 1
            Quantity -= 1
            costs.append(Cost)

        return costs

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
                self.Oil -= 1
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

    def BuyNuclear(self,Quantity):
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
            print('Not enough nuclear')

            

if __name__ == "__main__":
    r = R_Market()
    print(r.GetCostOfCoal())
    print(r.GetCostOfOil())
    print(r.GetCostOfGarbage())
    print(r.GetCostOfNuclear())