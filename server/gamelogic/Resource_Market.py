class R_Market:
    """Resource Market class
    """
    def __init__(self):
        """Initialses standard market amounts
        """
        self.Coal = 24
        self.Oil = 18
        self.Garbage = 9 
        self.Nuclear = 2

    def Buy_Resource(self,resource_type:str,quantity:int) -> int:
        """Removes a resource typoe from the resource market by a specified quantity

        Args:
            resource_type (str): resource type to buy
            quantity (int): quantity to buy

        Returns:
            int: total cost of the purchased resources
        """
        types_buy_function = {'C':self.BuyCoal, 'O':self.BuyOil, 'G':self.BuyGarbage, 'N':self.BuyNuclear}
        return types_buy_function[resource_type](quantity)

    def Add_Resource(self,resource_type:str,quantity:int):
        """Adds a specified quantity of a specified resource type to the resource market

        Args:
            resource_type (str): resource type to add
            quantity (int): quantity to add
        """
        types_add_function = {'C':self.AddCoal, 'O':self.AddOil, 'G':self.AddGarbage, 'N':self.AddNuclear}
        types_add_function[resource_type](quantity)

    def AddCoal(self,Quantity:int):
        """ Adds coal to the resource market

        Args:
            Quantity (int): quantity to add
        """
        self.Coal += Quantity
        if self.Coal > 24:
            self.Coal = 24

    def AddOil(self,Quantity:int):
        """ Adds oil to the resource market

        Args:
            Quantity (int): quantity to add
        """
        self.Oil += Quantity
        if self.Oil > 24:
            self.Oil = 24

    def AddGarbage(self,Quantity:int):
        """ Adds garbage to the resource market

        Args:
            Quantity (int): quantity to add
        """
        self.Garbage += Quantity
        if self.Garbage > 24:
            self.Garbage = 24

    def AddNuclear(self,Quantity:int):
        """ Adds nuclear to the resource market

        Args:
            Quantity (int): quantity to add
        """
        self.Nuclear += Quantity
        if self.Nuclear > 12:
            self.Nuclear = 12

    def GetCostOfCoal(self) -> list[int]:
        """Gives the cost of coal in list where index of amount - 1 gives the cost for that amount

        Returns:
            list[int]: List of costs for coal amounts
        """
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
        """Gives the cost of oil in list where index of amount - 1 gives the cost for that amount

        Returns:
            list[int]: List of costs for oil amounts
        """
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
        """Gives the cost of garbage in list where index of amount - 1 gives the cost for that amount

        Returns:
            list[int]: List of costs for garbage amounts
        """
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
        """Gives the cost of nuclear in list where index of amount - 1 gives the cost for that amount

        Returns:
            list[int]: List of costs for nuclear amounts
        """
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

    def BuyCoal(self,Quantity:int) -> int:
        """Buys quantitiy of coal from the resource market

        Args:
            Quantity (int): quantity to buy

        Raises:
            ValueError: not enough coal resources in market

        Returns:
            int: total cost of the purchase
        """
        Cost  = 0
        if self.Coal >= Quantity:
            while Quantity != 0:
                Cost += 8 - ((self.Coal - 1)// 3)
                self.Coal -= 1
                Quantity -= 1

            return Cost
        else:
            raise ValueError("Not enough coal resources in market")

    
    def BuyOil(self,Quantity:int) -> int:
        """Buys quantitiy of oil from the resource market

        Args:
            Quantity (int): quantity to buy

        Raises:
            ValueError: not enough oil resources in market

        Returns:
            int: total cost of the purchase
        """
        Cost  = 0
        if self.Oil >= Quantity:
            while Quantity != 0:
                Cost += 8 - ((self.Oil - 1)// 3)
                self.Oil -= 1
                Quantity -= 1

            return Cost
        else:
            raise ValueError("Not enough oil resources in market")

    def BuyGarbage(self,Quantity:int) -> int:
        """Buys quantitiy of garbage from the resource market

        Args:
            Quantity (int): quantity to buy

        Raises:
            ValueError: not enough garbage resources in market

        Returns:
            int: total cost of the purchase
        """
        Cost  = 0
        if self.Garbage >= Quantity:
            while Quantity != 0:
                Cost += 8 - ((self.Garbage - 1)// 3)
                self.Garbage -= 1
                Quantity -= 1

            return Cost
        else:
            raise ValueError("Not enough garbage resources in market")


    def BuyNuclear(self,Quantity:int) -> int:
        """Buys quantitiy of nuclear from the resource market

        Args:
            Quantity (int): quantity to buy

        Raises:
            ValueError: not enough nuclear resources in market
            
        Returns:
            int: total cost of the purchase
        """
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
            raise ValueError("Not enough nuclear resources in market")

            
